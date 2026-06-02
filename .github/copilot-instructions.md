# Cash Application Foundry - AI Agent Instructions

## Project Overview
A **5-agent orchestrated swarm** that automates cash application—matching bank transactions to open AR invoices and providing audit-ready GL posting instructions. Built for Microsoft Build AI Hackathon 2026.

**Core workflow:** Bank statement → normalized transactions → AR index → reconciliation matching → exception reasoning → final posting instructions (5 agents, sequential pipeline via Azure AI Foundry).

## Critical Architecture Patterns

### Sequential Agent Pipeline (not parallel swarm)
- Agents run **in strict order**: `BankStatementIntelligenceAgent` → `ARLedgerAgent` → `ReconciliationAgent` → `MismatchReasoningAgent` → `CashPostingAgent`
- **Hard dependencies exist:** Agent 3 (Reconciliation) cannot start until Agents 1 & 2 complete—it needs normalized transactions + invoice index
- **Each agent gets only what it needs**, not full history—keeps context windows lean and costs low
- Orchestration in [backend/agents/cash_app.py](backend/agents/cash_app.py): reads from `AGENT_ORDER`, routes models via environment variables (`MODEL_BANK_AGENT`, `MODEL_RECON_AGENT`, etc.)

### Agent Structure (One File = One Specialist)
Each agent module contains:
1. **System prompt** (`PROMPT` constant)—the detailed reasoning rules for that task
2. **Display metadata** (`META`)—name, icon, color for UI
3. **Model assignment** (`MODEL_ENV_KEY`, `DEFAULT_MODEL`)—per-agent model routing (e.g., Recon uses GPT-4o, Bank Parser uses GPT-4o-mini)
4. **Token budget** (`MAX_TOKENS`)—context window allocation

**Why:** Swap or tune any agent without touching the pipeline. Edit [backend/agents/reconciliation_agent.py](backend/agents/reconciliation_agent.py)'s prompt to change matching rules; update [backend/agents/mismatch_agent.py](backend/agents/mismatch_agent.py) to refine exception reasoning.

### Azure-Native, Not LangChain/CrewAI
Uses custom thin orchestration layer (`AsyncAzureOpenAI`) for three reasons:
1. **Real-time SSE streaming:** Every token from every agent streams to browser via Server-Sent Events—third-party frameworks add abstraction that breaks token-level forwarding
2. **Finance auditability:** Full control over what gets logged and when; immutable per-run audit trail
3. **Model routing per task:** Environment variables assign different models (`gpt-4o-mini` for parsing, `gpt-4o` for complex logic, `gpt-5` for reasoning)—no LLM can do all three equally well

### Streaming Architecture  
[backend/main.py](backend/main.py) `/analyze` endpoint:
- Yields `data: {JSON}` events for each token/event from swarm
- `asyncio.Queue` keepalive sends `: keepalive\n\n` every 10s (prevents Railway proxy timeout during agent gaps)
- Client receives `agent_start`, `token`, `agent_complete`, `swarm_complete` events
- Full run (`run_id`, inputs, all agent outputs) saved to Azure Blob Storage after completion

## Key Workflows

### Running Locally (Demo Mode)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Demo mode (no Azure account needed):
echo "USE_FIXTURES=true" > .env
uvicorn main:app --port 8001 --reload

# (separate terminal)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8001 npm run dev
```
Open `http://localhost:3000` → **Load Demo Data** → **Run Cash Application**

### Invoking the Pipeline Programmatically
```python
from agents.cash_app import run_cash_application

bank_statement = {...}  # dict with transactions
open_ar = {...}         # dict with invoices

async for event in run_cash_application(bank_statement, open_ar):
    print(event)  # yields: agent_start, token chunks, agent_complete, swarm_complete
```

### Adding a New Agent
1. Create [backend/agents/your_agent.py](backend/agents/) with `PROMPT`, `META`, `MODEL_ENV_KEY`, `DEFAULT_MODEL`, `MAX_TOKENS`
2. Import in [backend/agents/cash_app.py](backend/agents/cash_app.py): add to `AGENT_PROMPTS`, `AGENT_META`, `AGENT_MODEL_KEYS`, `AGENT_MAX_TOKENS`, `AGENT_ORDER`
3. Define the agent's input (output from previous agent) and output format (as JSON constant)
4. The orchestrator will automatically stream and route—no other changes needed

## Project-Specific Conventions

### 35 Edge Cases as Enum-Like Flags
Transactions are classified into **7 category groups**; UI badges map these flags (see [frontend/app/page.js](frontend/app/page.js) `FLAG_BADGE`):

| Category | Examples |
|----------|----------|
| **Amount mismatches** | EARLY_PAY_DISCOUNT, UNAUTHORIZED_DISCOUNT, FREIGHT_DEDUCTION, DAMAGE_CLAIM, BANK_WIRE_FEE |
| **Identity/names** | SWIFT_NAME_TRUNCATION, DBA_NAME_MISMATCH, POST_ACQUISITION_NAME |
| **Multi-entity** | PARENT_SUBSIDIARY, THIRD_PARTY_FACTORING, INTERCOMPANY_NET |
| **Timing** | DUPLICATE_PAYMENT, POST_DATED_CHECK, STALE_CHECK, NSF_RETURN |
| **Remittance** | MISSING_REMITTANCE, LEGACY_INVOICE_REF, EDI_PENDING |
| **FX** | FX_PAYMENT, FOREX_RATE_VARIANCE |
| **Compliance** | COMPLIANCE_HOLD, WRONG_LEGAL_ENTITY, DISPUTED_INVOICE |

Every exception must be assigned a **RISK_TIER** (CRITICAL/HIGH/MEDIUM/LOW) which determines SLA and routing priority.

### Configurable Thresholds (Reconciliation Agent)
Hardcoded defaults in [backend/agents/reconciliation_agent.py](backend/agents/reconciliation_agent.py) prompt:
- `AUTO_WRITEOFF_THRESHOLD = $25.00` (deltas ≤$25 are auto write-off to GL 6020)
- `FUZZY_NAME_MATCH_THRESHOLD = 0.75` (min similarity for alias/DBA matching)
- `DUPLICATE_WINDOW_DAYS = 30` (flag same payer+amount within window)
- `DISCOUNT_LATE_TOLERANCE_DAYS = 0` (no tolerance for late early-pay discounts)

### 8-Tier Matching Hierarchy (Reconciliation Agent)
Applied **after pre-checks** in this exact order (see [backend/agents/reconciliation_agent.py](backend/agents/reconciliation_agent.py)):
1. **EXACT** – amount == invoice.open_amount AND invoice_id in parsed_references
2. **LEGACY_REF** – parsed_references contains legacy_invoice_id (cross-reference lookup)
3. **ALIAS_MATCH** – payer matches customer alias table (fuzzy ≥75%) + amount match
4. **REMITTANCE_REF** – parsed reference matches invoice_id, amount within writeoff threshold
5. **DISCOUNT_EXACT** – amount == invoice.open_amount × (1 - discount%) AND date ≤ discount_deadline
6. **MULTI_INVOICE** – amount == exact sum of 2-4 open invoices (enumerate combinations precisely)
7. **CREDIT_NET** – amount == invoice.open_amount - credit_memo balance
8. **FIFO** – customer identified by alias/name → apply to oldest open invoice(s)

### Pre-Checks (Reconciliation Agent)
**Run before any matching tier.** These override/block transactions:
- COMPLIANCE_HOLD → status=COMPLIANCE_HOLD, freeze immediately
- WRONG_ENTITY → status=WRONG_ENTITY (cannot post to wrong entity)
- DISPUTED_INVOICE → status=DISPUTED_INVOICE_HOLD (escalate to legal)
- POST_DATED_CHECK → status=POST_DATED_HOLD (hold until check date)
- STALE_CHECK (>180 days) → status=STALE_CHECK_RETURN (void + reopen invoice)
- INTERCOMPANY_NET → match to intercompany_netting table (not invoices)
- PREPAYMENT → status=SUSPENSE_PREPAYMENT (no invoice match)
- EDI_PENDING → status=HOLD_EDI_PENDING (match after EDI arrives)

## Critical External Integrations

### Azure AI Foundry (Inference)
- Accessed via `AsyncAzureOpenAI` (standard OpenAI-compatible API, not proprietary SDK)
- Environment: `AZURE_AI_ENDPOINT`, `AZURE_API_KEY`, `AZURE_OPENAI_API_VERSION` (see `.env.example`)
- Uses DefaultAzureCredential in production (no API keys stored)
- Each agent receives environment variable for model: `MODEL_BANK_AGENT=gpt-4o-mini`, etc.

### Azure Blob Storage
- Stores per-run audit trail: bank_statement.json, open_ar.json, results.json, agent_events.json
- Keyed by `run_id` (UUID), uploaded in [backend/main.py](backend/main.py) `_upload_blob()` function
- Non-critical: silent fallback if storage not configured (see `_blob_service` init)

### Azure Application Insights (Telemetry)
- Auto-instrumented via OpenTelemetry
- Traces every agent run: latency, token counts, success/failure
- Controlled by `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable
- Non-critical: fails silently if not configured

## Sample Data & Testing

- Demo fixtures: [backend/data/bank_statement.json](backend/data/bank_statement.json), [backend/data/open_ar.json](backend/data/open_ar.json)
- 10 numbered samples: [backend/data/samples/sample_01/](backend/data/samples/sample_01/) through `sample_10/` (each has bank_statement.json, open_ar.json, meta.json)
- `/samples` endpoint lists available samples; `/demo-data?sample=01` loads a specific sample
- `USE_FIXTURES=true` .env setting loads sample data instead of running real agents

## Frontend Architecture (Streaming UI)

[frontend/app/page.js](frontend/app/page.js) receives SSE events and:
1. Displays 5 agent cards in order with streaming output
2. Shows token chunks in real-time as they arrive
3. Renders transaction details with exception badges (FLAG_BADGE map)
4. Shows agent timing + model used for each
5. Provides approve/reject UI for workqueue (UI-only for now; ERP connectors TBD)

**State flow:** `loading` (via SSE) → `complete` → user can review workqueue before approving

## Extending the System

### Adding a New Matching Strategy
1. Edit [backend/agents/reconciliation_agent.py](backend/agents/reconciliation_agent.py) PROMPT
2. Add tier description + logic to "8-TIER MATCHING HIERARCHY" section
3. Increment tier count in comments and test with [backend/data/samples/](backend/data/samples/) data

### Custom Thresholds per Deployment
1. Create `.env` with `AUTO_WRITEOFF_THRESHOLD=50.00`, etc.
2. Modify [backend/agents/reconciliation_agent.py](backend/agents/reconciliation_agent.py) to read from `os.getenv()` instead of hardcoded values
3. Pass to agent prompt template at runtime

### Production Deployment
- **Backend:** Docker Dockerfile in [backend/](backend/), deploy to Railway or similar
- **Frontend:** Next.js in [frontend/](frontend/), deploy to Vercel
- Set `NEXT_PUBLIC_API_URL=https://your-railway-api.up.railway.app` in Vercel environment
- Azure services must be configured with Service Principal + DefaultAzureCredential

