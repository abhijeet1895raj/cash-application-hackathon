import json
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── Azure Application Insights ────────────────────────────────────────────────
_conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
if _conn_str:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=_conn_str)
    except Exception:
        pass  # telemetry is non-critical

# ── Azure Blob Storage ────────────────────────────────────────────────────────
_storage_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
_blob_service = None
if _storage_url:
    try:
        from azure.storage.blob import BlobServiceClient
        from azure.identity import DefaultAzureCredential
        _blob_service = BlobServiceClient(
            account_url=_storage_url,
            credential=DefaultAzureCredential(),
        )
    except Exception:
        pass  # storage is non-critical

BLOB_CONTAINER = "cash-app-runs"


def _upload_blob(path: str, data: dict):
    """Upload JSON to Azure Blob Storage. Silently skips if storage not configured."""
    if not _blob_service:
        return
    try:
        client = _blob_service.get_blob_client(container=BLOB_CONTAINER, blob=path)
        client.upload_blob(json.dumps(data, indent=2), overwrite=True)
    except Exception:
        pass


from agents.cash_app import run_cash_application

app = FastAPI(title="Cash Application Foundry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FIXTURES_DIR = Path(__file__).parent / "data"
SAMPLES_DIR = FIXTURES_DIR / "samples"


class AnalyzeRequest(BaseModel):
    bank_data: dict
    ar_data: dict


def _load_sample(sample_id: str) -> tuple[dict, dict]:
    """Load bank_statement.json and open_ar.json for the given sample_id (e.g. '01')."""
    sample_dir = SAMPLES_DIR / f"sample_{sample_id.zfill(2)}"
    if sample_dir.exists():
        bank = json.loads((sample_dir / "bank_statement.json").read_text())
        ar = json.loads((sample_dir / "open_ar.json").read_text())
        return bank, ar
    # Fallback to legacy fixture files
    bank = json.loads((FIXTURES_DIR / "bank_statement.json").read_text())
    ar = json.loads((FIXTURES_DIR / "open_ar.json").read_text())
    return bank, ar


@app.get("/health")
async def health():
    storage_configured = _blob_service is not None
    telemetry_configured = bool(_conn_str)
    sample_count = len(list(SAMPLES_DIR.glob("sample_*"))) if SAMPLES_DIR.exists() else 0
    return {
        "status": "ok",
        "service": "cash-application-foundry",
        "azure_blob_storage": storage_configured,
        "azure_app_insights": telemetry_configured,
        "use_fixtures": os.getenv("USE_FIXTURES", "true"),
        "sample_count": sample_count,
    }


@app.get("/samples")
async def list_samples():
    """Return the list of available sample datasets."""
    samples = []
    if SAMPLES_DIR.exists():
        for d in sorted(SAMPLES_DIR.glob("sample_*")):
            meta_file = d / "meta.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
                samples.append(meta)
    return {"samples": samples}


@app.get("/demo-data")
async def demo_data(sample: str = "01"):
    bank_statement, open_ar = _load_sample(sample)
    return {"bank_statement": bank_statement, "open_ar": open_ar, "sample_id": sample}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # Save inputs to Azure Blob Storage immediately
    _upload_blob(f"{run_id}/bank_statement.json", {
        "run_id": run_id,
        "started_at": started_at,
        "data": request.bank_data,
    })
    _upload_blob(f"{run_id}/open_ar.json", {
        "run_id": run_id,
        "started_at": started_at,
        "data": request.ar_data,
    })

    agent_events = []
    all_results = {}

    async def event_stream():
        # Keepalive pump - sends SSE comment every 10s to prevent Railway proxy timeout
        keepalive_queue: asyncio.Queue = asyncio.Queue()

        async def _keepalive():
            while True:
                await asyncio.sleep(10)
                await keepalive_queue.put(": keepalive\n\n")

        ka_task = asyncio.create_task(_keepalive())

        async def _swarm():
            try:
                async for event in run_cash_application(request.bank_data, request.ar_data):
                    event["run_id"] = run_id

                    evt_type = event.get("event", "")
                    if evt_type in ("agent_start", "agent_complete"):
                        agent_events.append({
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "event": evt_type,
                            "agent": event.get("agent"),
                            "model": event.get("model"),
                        })

                    if evt_type == "agent_complete" and event.get("output"):
                        all_results[event["agent"]] = event["output"]

                    if evt_type == "swarm_complete":
                        _upload_blob(f"{run_id}/results.json", {
                            "run_id": run_id,
                            "started_at": started_at,
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                            "results": event.get("results", all_results),
                        })
                        _upload_blob(f"{run_id}/agent_events.json", {
                            "run_id": run_id,
                            "events": agent_events,
                        })

                    await keepalive_queue.put(f"data: {json.dumps(event)}\n\n")

            except Exception as e:
                await keepalive_queue.put(
                    f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                )
            finally:
                await keepalive_queue.put(None)  # sentinel - stream done

        asyncio.create_task(_swarm())

        try:
            while True:
                item = await keepalive_queue.get()
                if item is None:
                    break
                yield item
        finally:
            ka_task.cancel()
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
