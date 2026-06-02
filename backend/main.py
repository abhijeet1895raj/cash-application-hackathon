"""
FastAPI Cash Application Server

Serves the 5-agent pipeline via REST API with Server-Sent Events (SSE) streaming.
Loads demo data from fixtures and orchestrates the agent pipeline.
"""

import os
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from agents.cash_app import CashApplicationFoundry

# Load environment variables
load_dotenv()

# Configuration
USE_FIXTURES = os.getenv("USE_FIXTURES", "true").lower() == "true"
DATA_DIR = Path(__file__).parent / "data"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Initialize Azure OpenAI client
try:
    from openai import AsyncAzureOpenAI

    client = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
    )
except Exception as e:
    print(f"Warning: Could not initialize Azure OpenAI client: {e}")
    print("Running in fixture mode only")
    client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    print("🚀 Cash Application Foundry starting...")
    yield
    print("🛑 Cash Application Foundry shutting down...")


app = FastAPI(
    title="Cash Application Foundry",
    description="5-agent AI pipeline for bank reconciliation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files if they exist
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


def load_fixture(filename: str) -> dict:
    """Load JSON fixture file."""
    fixture_path = DATA_DIR / filename
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {filename}")

    with open(fixture_path, "r") as f:
        return json.load(f)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Cash Application Foundry",
        "version": "1.0.0",
        "fixtures_enabled": USE_FIXTURES,
    }


@app.post("/api/process")
async def process_statement():
    """
    Process bank statement and AR data through the 5-agent pipeline.
    Streams agent outputs as Server-Sent Events (SSE).
    """

    if not USE_FIXTURES:
        raise HTTPException(
            status_code=400,
            detail="Fixtures disabled. Please POST bank_statement and ar_ledger data.",
        )

    async def event_stream():
        """SSE event generator."""
        try:
            # Load fixtures
            bank_statement = load_fixture("bank_statement.json")
            ar_ledger = load_fixture("open_ar.json")

            # Initialize foundry
            foundry = CashApplicationFoundry(client, use_fixtures=USE_FIXTURES)

            # Run pipeline and stream events
            async for event in foundry.run_pipeline(bank_statement, ar_ledger):
                # Format as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"

                # Small delay to ensure client receives each event
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in event stream: {e}")
            yield f"data: {json.dumps({'agent': 'error', 'status': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/process-custom")
async def process_custom(bank_statement: dict, ar_ledger: dict):
    """
    Process custom bank statement and AR data.
    Accepts JSON payloads and streams agent outputs as SSE.
    """

    async def event_stream():
        """SSE event generator."""
        try:
            # Initialize foundry
            foundry = CashApplicationFoundry(client, use_fixtures=False)

            # Run pipeline and stream events
            async for event in foundry.run_pipeline(bank_statement, ar_ledger):
                # Format as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"

                # Small delay to ensure client receives each event
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error in event stream: {e}")
            yield f"data: {json.dumps({'agent': 'error', 'status': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/fixtures/bank-statement")
async def get_bank_statement_fixture():
    """Get bank statement fixture for reference."""
    return load_fixture("bank_statement.json")


@app.get("/api/fixtures/ar-ledger")
async def get_ar_ledger_fixture():
    """Get AR ledger fixture for reference."""
    return load_fixture("open_ar.json")


@app.get("/api/fixtures/demo-result")
async def get_demo_result():
    """Get pre-built demo result (if available)."""
    try:
        return load_fixture("cash_app_results.json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Demo result not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
