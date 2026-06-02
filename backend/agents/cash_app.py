"""
Cash Application Swarm - Orchestrator

Runs 5 specialized agents in sequence using Azure AI Foundry via AsyncAzureOpenAI.
Each agent is defined in its own module; this file handles routing, streaming, and retries.

Pipeline:
  BankStatementIntelligenceAgent  →  ARLedgerAgent  →  ReconciliationAgent
  →  MismatchReasoningAgent  →  CashPostingAgent
"""
import asyncio
import json
import os
import re
from typing import AsyncGenerator

from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from agents.bank_statement_agent import PROMPT as BANK_PROMPT, META as BANK_META, MODEL_ENV_KEY as BANK_MODEL_KEY, DEFAULT_MODEL as BANK_DEFAULT, MAX_TOKENS as BANK_MAX
from agents.ar_ledger_agent      import PROMPT as AR_PROMPT,   META as AR_META,   MODEL_ENV_KEY as AR_MODEL_KEY,   DEFAULT_MODEL as AR_DEFAULT,   MAX_TOKENS as AR_MAX
from agents.reconciliation_agent import PROMPT as RECON_PROMPT, META as RECON_META, MODEL_ENV_KEY as RECON_MODEL_KEY, DEFAULT_MODEL as RECON_DEFAULT, MAX_TOKENS as RECON_MAX
from agents.mismatch_agent       import PROMPT as MISMATCH_PROMPT, META as MISMATCH_META, MODEL_ENV_KEY as MISMATCH_MODEL_KEY, DEFAULT_MODEL as MISMATCH_DEFAULT, MAX_TOKENS as MISMATCH_MAX
from agents.posting_agent        import PROMPT as POSTING_PROMPT,  META as POSTING_META,  MODEL_ENV_KEY as POSTING_MODEL_KEY,  DEFAULT_MODEL as POSTING_DEFAULT,  MAX_TOKENS as POSTING_MAX


AGENT_ORDER = [
    "BankStatementIntelligenceAgent",
    "ARLedgerAgent",
    "ReconciliationAgent",
    "MismatchReasoningAgent",
    "CashPostingAgent",
]

AGENT_PROMPTS = {
    "BankStatementIntelligenceAgent": BANK_PROMPT,
    "ARLedgerAgent":                  AR_PROMPT,
    "ReconciliationAgent":            RECON_PROMPT,
    "MismatchReasoningAgent":         MISMATCH_PROMPT,
    "CashPostingAgent":               POSTING_PROMPT,
}

AGENT_META = {
    "BankStatementIntelligenceAgent": BANK_META,
    "ARLedgerAgent":                  AR_META,
    "ReconciliationAgent":            RECON_META,
    "MismatchReasoningAgent":         MISMATCH_META,
    "CashPostingAgent":               POSTING_META,
}

AGENT_MODEL_KEYS = {
    "BankStatementIntelligenceAgent": (BANK_MODEL_KEY,    BANK_DEFAULT),
    "ARLedgerAgent":                  (AR_MODEL_KEY,      AR_DEFAULT),
    "ReconciliationAgent":            (RECON_MODEL_KEY,   RECON_DEFAULT),
    "MismatchReasoningAgent":         (MISMATCH_MODEL_KEY, MISMATCH_DEFAULT),
    "CashPostingAgent":               (POSTING_MODEL_KEY, POSTING_DEFAULT),
}

AGENT_MAX_TOKENS = {
    "BankStatementIntelligenceAgent": BANK_MAX,
    "ARLedgerAgent":                  AR_MAX,
    "ReconciliationAgent":            RECON_MAX,
    "MismatchReasoningAgent":         MISMATCH_MAX,
    "CashPostingAgent":               POSTING_MAX,
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | None:
    """Extract the first valid JSON object from agent response text."""
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except Exception:
            pass

    # Find first { to last } - handles trailing "NEXT: AgentName" text
    try:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return None


def _build_openai_client() -> AsyncAzureOpenAI:
    """Build AsyncAzureOpenAI using API key or DefaultAzureCredential (Service Principal)."""
    endpoint = os.environ.get("AZURE_AI_ENDPOINT", "")
    api_key  = os.environ.get("AZURE_API_KEY", "")
    api_ver  = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not endpoint:
        raise EnvironmentError("Set AZURE_AI_ENDPOINT in backend/.env")

    if api_key:
        return AsyncAzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_ver)

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    return AsyncAzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider, api_version=api_ver)


# ── DEMO DATA SWARM ───────────────────────────────────────────────────────────

async def _run_demo_swarm(bank_data: dict, ar_data: dict) -> AsyncGenerator[dict, None]:
    """
    Stream pre-built demo results with realistic token animation.
    No Azure credentials needed - great for demos and development.
    """
    import pathlib

    demo_file = pathlib.Path(__file__).parent.parent / "data" / "cash_app_results.json"

    if not demo_file.exists():
        yield {"event": "error", "message": "Demo data file not found. Set USE_FIXTURES=false to use live Azure mode."}
        return

    results = json.loads(demo_file.read_text())

    for agent_name in AGENT_ORDER:
        meta        = AGENT_META[agent_name]
        agent_result = results.get(agent_name, {})
        response_text = json.dumps(agent_result, indent=2)

        yield {
            "event": "agent_start",
            "agent": agent_name,
            "label": meta["label"],
            "icon":  meta["icon"],
            "color": meta["color"],
            "tool":  "code_interpreter" if agent_name == "ReconciliationAgent" else None,
        }

        for i in range(0, len(response_text), 4):
            yield {"event": "agent_token", "agent": agent_name, "token": response_text[i:i + 4]}
            await asyncio.sleep(0.008)

        yield {
            "event":  "agent_complete",
            "agent":  agent_name,
            "label":  meta["label"],
            "icon":   meta["icon"],
            "color":  meta["color"],
            "output": agent_result,
        }
        await asyncio.sleep(0.1)

    yield {"event": "swarm_complete", "results": results, "final": results.get("CashPostingAgent", {})}


# ── LIVE AZURE SWARM ──────────────────────────────────────────────────────────

async def _run_recon_with_code_interpreter(
    client: AsyncAzureOpenAI,
    user_content: str,
    model: str,
) -> AsyncGenerator[dict, None]:
    """
    Run the Reconciliation Agent via the Azure OpenAI Assistants API with real
    Code Interpreter enabled. The model writes Python, Azure executes it in a
    sandboxed container, and the verified output is fed back to the model before
    it produces its final JSON. This is genuine code execution, not simulated.
    """
    assistant = None
    thread    = None
    try:
        assistant = await client.beta.assistants.create(
            name="ReconciliationAgent",
            instructions=RECON_PROMPT,
            model=model,
            tools=[{"type": "code_interpreter"}],
        )
        thread = await client.beta.threads.create()
        await client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_content,
        )

        response_text = ""

        async with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
        ) as stream:
            async for event in stream:
                evt = getattr(event, "event", "")

                # Text tokens being generated
                if evt == "thread.message.delta":
                    for block in (getattr(event.data.delta, "content", None) or []):
                        if getattr(block, "type", "") == "text":
                            chunk = getattr(block.text, "value", "") or ""
                            if chunk:
                                response_text += chunk
                                yield {"event": "agent_token", "agent": "ReconciliationAgent", "token": chunk}

                # Code Interpreter: Python being written + output returned
                elif evt == "thread.run.step.delta":
                    step = getattr(event.data.delta, "step_details", None)
                    if step and getattr(step, "type", "") == "tool_calls":
                        for tc in (getattr(step, "tool_calls", None) or []):
                            if getattr(tc, "type", "") == "code_interpreter":
                                ci = getattr(tc, "code_interpreter", None)
                                if ci:
                                    code_in = getattr(ci, "input", None)
                                    if code_in:
                                        yield {"event": "code_input", "agent": "ReconciliationAgent", "code": code_in}
                                    for out in (getattr(ci, "outputs", None) or []):
                                        if getattr(out, "type", "") == "logs":
                                            yield {"event": "code_output", "agent": "ReconciliationAgent", "output": out.logs}

        # Get the final complete message text
        msgs = await client.beta.threads.messages.list(thread_id=thread.id)
        for msg in msgs.data:
            if msg.role == "assistant":
                for block in msg.content:
                    if getattr(block, "type", "") == "text":
                        response_text = block.text.value
                        break
                break

        yield {"event": "agent_response", "agent": "ReconciliationAgent", "text": response_text}

    except Exception as e:
        yield {"event": "code_interpreter_unavailable", "agent": "ReconciliationAgent", "message": str(e)}
        yield {"event": "agent_response", "agent": "ReconciliationAgent", "text": ""}

    finally:
        if thread:
            try:
                await client.beta.threads.delete(thread.id)
            except Exception:
                pass
        if assistant:
            try:
                await client.beta.assistants.delete(assistant.id)
            except Exception:
                pass


async def _run_live_swarm(bank_data: dict, ar_data: dict) -> AsyncGenerator[dict, None]:
    """
    Live swarm using Azure AI Foundry.

    Agents 1, 2, 4, 5 use Chat Completions API.
    Agent 3 (Reconciliation) uses the Assistants API with real Code Interpreter
    so all arithmetic is executed in an Azure-hosted Python sandbox.
    """
    client      = _build_openai_client()
    all_results: dict[str, dict] = {}

    def _user_content(agent_name: str) -> str:
        """Build targeted input for each agent - only the fields it actually needs."""
        if agent_name == "BankStatementIntelligenceAgent":
            return json.dumps({
                "task": "Parse and normalize this bank statement. Extract all transactions with flags.",
                "bank_statement": bank_data,
            })

        if agent_name == "ARLedgerAgent":
            return json.dumps({
                "task": "Structure this open AR ledger. Build customer index, aging, alias registry.",
                "open_ar": ar_data,
            })

        if agent_name == "ReconciliationAgent":
            bank = all_results.get("BankStatementIntelligenceAgent", {})
            ar   = all_results.get("ARLedgerAgent", {})
            return json.dumps({
                "task": "Match every bank transaction to open AR invoices using the 8-tier hierarchy.",
                "normalized_transactions": bank.get("transactions", []),
                "bank_summary":            bank.get("summary", {}),
                "invoices":                ar.get("invoices", []),
                "customer_index":          ar.get("customer_index", {}),
                "legacy_invoice_map":      ar.get("legacy_invoice_map", {}),
                "compliance_flags":        ar.get("compliance_flags", {}),
                "intercompany_netting":    ar.get("intercompany_netting", []),
            })

        if agent_name == "MismatchReasoningAgent":
            recon   = all_results.get("ReconciliationAgent", {})
            exceptions = [m for m in recon.get("matches", []) if m.get("exception")]
            return json.dumps({
                "task": "Analyze each exception. Provide reasoning, risk tier, GL code, recommended action.",
                "exception_matches":      exceptions,
                "reconciliation_summary": recon.get("reconciliation_summary", {}),
            })

        if agent_name == "CashPostingAgent":
            recon    = all_results.get("ReconciliationAgent", {})
            mismatch = all_results.get("MismatchReasoningAgent", {})
            return json.dumps({
                "task": "Generate final GL posting instructions and workqueue items for every transaction.",
                "all_matches":            recon.get("matches", []),
                "reconciliation_summary": recon.get("reconciliation_summary", {}),
                "exception_analysis":     mismatch.get("exception_analysis", []),
                "exception_summary":      mismatch.get("exception_summary", {}),
            })

        return json.dumps({"task": "Continue."})

    for agent_name in AGENT_ORDER:
        meta       = AGENT_META[agent_name]
        env_key, default_model = AGENT_MODEL_KEYS[agent_name]
        model      = os.environ.get(env_key, default_model)
        max_tokens = AGENT_MAX_TOKENS[agent_name]

        yield {
            "event": "agent_start",
            "agent": agent_name,
            "label": meta["label"],
            "icon":  meta["icon"],
            "color": meta["color"],
            "model": model,
            "tool":  "code_interpreter" if agent_name == "ReconciliationAgent" else None,
        }

        messages = [
            {"role": "system", "content": AGENT_PROMPTS[agent_name]},
            {"role": "user",   "content": _user_content(agent_name)},
        ]

        response_text = ""
        finish_reason = None
        last_error    = None

        # Reconciliation Agent uses real Code Interpreter via Assistants API
        if agent_name == "ReconciliationAgent":
            async for ci_event in _run_recon_with_code_interpreter(client, _user_content(agent_name), model):
                if ci_event.get("event") == "agent_response":
                    response_text = ci_event.get("text", "")
                elif ci_event.get("event") == "code_interpreter_unavailable":
                    # Fall back to chat completions if Assistants API not available
                    last_error = ci_event.get("message")
                else:
                    yield ci_event
        else:
            for attempt in range(3):
                try:
                    response_text = ""
                    finish_reason = None
                    stream = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                        max_tokens=max_tokens,
                        temperature=0,
                        timeout=300,
                    )

                    async for chunk in stream:
                        if chunk.choices:
                            choice = chunk.choices[0]
                            if choice.delta.content:
                                token = choice.delta.content
                                response_text += token
                                yield {"event": "agent_token", "agent": agent_name, "token": token}
                            if choice.finish_reason:
                                finish_reason = choice.finish_reason

                    last_error = None
                    break

                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        await asyncio.sleep(2)

        # If Code Interpreter fell back and chat completions also failed, retry recon via chat
        if agent_name == "ReconciliationAgent" and (not response_text or last_error):
            for attempt in range(3):
                try:
                    response_text = ""
                    stream = await client.chat.completions.create(
                        model=model, messages=messages, stream=True,
                        max_tokens=max_tokens, temperature=0, timeout=300,
                    )
                    async for chunk in stream:
                        if chunk.choices:
                            choice = chunk.choices[0]
                            if choice.delta.content:
                                token = choice.delta.content
                                response_text += token
                                yield {"event": "agent_token", "agent": agent_name, "token": token}
                            if choice.finish_reason:
                                finish_reason = choice.finish_reason
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        await asyncio.sleep(2)

        if last_error and not response_text:
            yield {"event": "error", "agent": agent_name, "message": f"{agent_name} failed: {last_error}"}
            return

        parsed = _extract_json(response_text)
        if parsed:
            all_results[agent_name] = parsed

        yield {
            "event":          "agent_complete",
            "agent":          agent_name,
            "label":          meta["label"],
            "icon":           meta["icon"],
            "color":          meta["color"],
            "output":         parsed or {"raw": response_text[:800]},
            "response_chars": len(response_text),
            "finish_reason":  finish_reason,
            "parse_ok":       parsed is not None,
        }

        await asyncio.sleep(0.05)

    yield {"event": "swarm_complete", "results": all_results, "final": all_results.get("CashPostingAgent", {})}


# ── PUBLIC ENTRY POINT ────────────────────────────────────────────────────────

async def run_cash_application(bank_data: dict, ar_data: dict) -> AsyncGenerator[dict, None]:
    """Route to demo data swarm or live Azure AI Foundry swarm based on USE_FIXTURES env var."""
    use_demo = os.getenv("USE_FIXTURES", "true").lower() == "true"

    if use_demo:
        async for event in _run_demo_swarm(bank_data, ar_data):
            yield event
    else:
        async for event in _run_live_swarm(bank_data, ar_data):
            yield event
