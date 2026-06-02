# Cash Application Foundry

A team of 5 AI agents that takes your bank statement and open invoices, figures out what matches what, and tells your finance team exactly what to post, including the hard cases that used to take hours to sort out manually.

> Built for Microsoft Build AI Hackathon 2026 · Theme 05: Agent Swarms

**Live Demo:** [cash-app-hackathon.vercel.app](https://cash-app-hackathon.vercel.app) · **Architecture Docs:** [vinaygangidi.github.io/cash-application-foundry/architecture.html](https://vinaygangidi.github.io/cash-application-foundry/architecture.html)


## What problem does this solve?

Every company that sells on credit (net 30, net 60, etc.) has an Accounts Receivable team. Their job is to match the money coming into the bank account to the invoices that are still open. Sounds simple. It isn't.

Here's what actually happens:

- A customer sends $29,250 but the invoice is for $29,500. Did they take a freight deduction? A damaged goods claim? An unauthorized short pay? The AR analyst has to figure that out manually.
- The bank shows the payer as "GREENFIELD TECH SOLUT" because SWIFT wire transfers cut off names at 35 characters. The actual customer is "Greenfield Technology Solutions LLC." Someone has to look that up.
- A payment comes in from "ACE Capital Partners" but your customer is "Riverside Manufacturing." Turns out ACE is a factoring company that bought the invoice. The payment is legitimate but needs to be posted to the right customer.
- A payment arrives for an invoice that the customer is actively disputing in court. Posting it would be a compliance problem. It has to be flagged and held.

An experienced AR analyst handles maybe 8 to 10 of these edge cases per hour. Our system handles 35 of them in under 60 seconds and shows its reasoning for every single one.

**The scale of the problem:** US companies process $2.3 trillion in AR annually. Each day a payment sits unposted is one more day of working capital tied up. For a $500M revenue company, that's roughly $1.4M per DSO day.


## How it works: the 5-agent pipeline

Instead of one big AI trying to do everything at once, we split the work across 5 specialists. Each one does one job well and hands structured output to the next.

```
Your bank statement JSON
        │
        ▼
Agent 1: Bank Statement Parser          (GPT-4o-mini, fast + cheap)
  Reads every transaction, normalizes payer names,
  parses remittance text for invoice/PO references,
  and flags anything unusual (truncated names, foreign currency,
  stale checks, compliance red flags, etc.)
        │
        ▼
Agent 2: AR Ledger Builder              (GPT-4o-mini, fast + cheap)
  Takes your open invoices and builds every lookup table
  Reconciliation will need: customer aliases, aging buckets,
  legacy invoice cross-references, dispute/hold flags,
  intercompany netting agreements, credit memo balances.
        │
        ▼
Agent 3: Reconciliation Engine          (GPT-4o + Python code execution)
  Runs pre-checks first (compliance holds, disputed invoices,
  stale checks, etc.), then tries 8 matching strategies in order
  from most confident to least. Runs actual Python to verify
  every dollar. No mental arithmetic, no hallucination on math.
        │
        ▼
Agent 4: Mismatch Reasoning             (GPT-5, deep reasoning model)
  For every transaction that didn't match cleanly, this agent
  figures out WHY. Is the $250 delta a legitimate freight
  deduction or an unauthorized short pay? Should this be
  routed to the deductions team or escalated to legal?
  Assigns a risk tier and SLA to every exception.
        │
        ▼
Agent 5: Cash Posting                   (GPT-4o)
  Turns all the analysis into specific ERP instructions.
  Which GL account? Which invoice gets closed? Who on the
  AR team needs to handle which item, and by when?
  Produces workqueue items sorted by urgency.
```

The whole thing streams in real time. You watch each agent work as it happens.


## Why we built it this way: the multi-agent framework

### Custom sequential pipeline on Azure AI Foundry

We use **Azure AI Foundry** as the inference platform, accessed through the standard OpenAI-compatible API (`AsyncAzureOpenAI`). The agents run sequentially. Each one waits for the previous one to finish, takes its structured JSON output, and continues.

This is a hand-off pattern, not a parallel swarm. Here's why that fits cash application specifically:

- Agent 3 (Reconciliation) literally cannot start until Agents 1 and 2 have built the normalized transaction list and invoice lookup tables. The dependency is hard, not a design choice.
- Agents don't need to coordinate or negotiate. Each one has one job. A parallel swarm with shared memory would add complexity without adding value here.
- The sequential pattern makes the audit trail clean: Agent 1 output goes to Agent 2, Agent 3 uses both, and so on. Every step is traceable.

Each agent gets **only the data it needs**, not the full conversation history. Agent 3 gets Agent 1's normalized transactions and Agent 2's invoice index. Agent 4 gets only the exceptions from Agent 3, not all 35 match records. This keeps context windows lean, costs low, and responses focused.

### Why not LangChain, AutoGen, or CrewAI?

Those frameworks are excellent for building agent systems quickly. We chose to build our own thin orchestration layer for three reasons:

1. **Azure-native streaming:** We stream every token from every agent directly to the browser via Server-Sent Events. Third-party frameworks add abstraction layers that make it harder to intercept and forward individual tokens cleanly.

2. **Auditability:** For finance, every agent input and output needs to be loggable and immutable. Owning the orchestration layer means we control exactly what gets saved and when. No hidden buffering or intermediate state.

3. **Model routing per agent:** We need to assign a different model to each agent based on task complexity. Our orchestrator reads `MODEL_BANK_AGENT`, `MODEL_RECON_AGENT`, etc. from environment variables, configurable per deployment without touching code.

### Why does each agent live in its own file?

Each agent module (`bank_statement_agent.py`, `ar_ledger_agent.py`, etc.) contains:
- The full system prompt for that agent
- Its display metadata (name, icon, color)
- The model it should use and its max token budget

This means you can tune, test, or replace any single agent without touching the others. Want to upgrade only the Reconciliation Agent to a newer model? Change one line in `reconciliation_agent.py`. Want to try a different prompt for exception reasoning? Edit `mismatch_agent.py`. The orchestrator (`cash_app.py`) just imports them all and runs the pipeline.


## How we're using Microsoft's tech stack

This isn't a wrapper around ChatGPT. Every inference call goes through **Azure AI Foundry**, Microsoft's enterprise AI platform. Here's what that means in practice:

**Azure OpenAI Service:** The models (GPT-4o-mini, GPT-4o, GPT-5) run entirely within the Azure tenant. Your financial data never leaves your subscription. Microsoft doesn't use it to train future models. For a finance application processing real bank data, that's not optional. It's a hard requirement.

**Right model for each task:** We route each agent to the model that matches its cognitive complexity:

| Agent | Model | Why |
|---|---|---|
| Bank Statement Parser | GPT-4o-mini | Text normalization and flag detection. Fast, cheap, accurate. No deep reasoning needed. |
| AR Ledger Builder | GPT-4o-mini | Building lookup tables from structured JSON. Deterministic, no business judgment required. |
| Reconciliation Engine | GPT-4o | Complex matching logic with 8 tiers and 8 pre-checks. Precise arithmetic applied directly from the structured input data. |
| Mismatch Reasoning | GPT-5 | Business judgment: "Is this a legitimate freight deduction?" This is where a reasoning model pays off. |
| Cash Posting | GPT-4o | Generating complex structured output: GL entries, workqueue routing, compliance actions. |

Running everything on GPT-4o would cost about 4x more per batch. Running everything on GPT-4o-mini would miss the nuance in exception reasoning. Routing by task saves cost where it doesn't matter and spends it where it does.

**Azure Application Insights:** Auto-instrumented via OpenTelemetry. Every agent run is traced end-to-end: how long each agent took, which model ran, whether parsing succeeded. When something breaks, we know exactly where.

**Azure Blob Storage:** Every batch run is saved: the raw inputs, each agent's output, and the final results, keyed by a unique `run_id`. This is the foundation of the audit trail.

**DefaultAzureCredential / Service Principal:** In production on Railway, we authenticate to all Azure services using a Service Principal with exactly the roles it needs (Cognitive Services OpenAI User + Storage Blob Data Contributor). No API keys stored. No manual rotation. This is the Azure-recommended approach for workload identity.

**Real-time SSE streaming:** The frontend connects to a single `/analyze` endpoint that streams every token from every agent as it's generated. An `asyncio.Queue` keepalive sends a heartbeat every 10 seconds so the Railway proxy doesn't drop the connection during the gaps between agents.


## The 35 edge cases we handle

| Category | What it covers |
|---|---|
| **Amount mismatches** (10) | Exact match, multi-invoice bundle, early-pay discount (valid), unauthorized short pay, freight deduction, damage claim, overpayment to credit, credit memo netting, wire fee write-off (up to $25 auto), late discount |
| **Identity and name issues** (4) | SWIFT 35-char truncation, DBA/trade name, post-acquisition name change, fuzzy alias matching |
| **Multi-entity payments** (4) | Parent paying for subsidiary, factoring agent payment, intercompany AP/AR netting, wrong legal entity |
| **Timing problems** (6) | Duplicate payment, installment/partial, NSF return + reversal, post-dated check hold, stale check (over 180 days), prepayment to unearned revenue |
| **Remittance issues** (5) | No remittance (FIFO match), vague remittance (amount match), PO number only, legacy ERP invoice number, EDI 820 pending |
| **FX and international** (2) | EUR SWIFT payment with FX conversion, FX rate verification via Python |
| **Compliance and legal** (3) | OFAC/sanctions hold (same-day escalation), disputed invoice block, legal hold escalation |


## Code structure

```
cash-application-foundry/
├── backend/
│   ├── agents/
│   │   ├── cash_app.py              # Orchestrator: runs the 5-agent pipeline
│   │   ├── bank_statement_agent.py  # Agent 1: prompt, model config, metadata
│   │   ├── ar_ledger_agent.py       # Agent 2: prompt, model config, metadata
│   │   ├── reconciliation_agent.py  # Agent 3: prompt, model config, metadata
│   │   ├── mismatch_agent.py        # Agent 4: prompt, model config, metadata
│   │   └── posting_agent.py         # Agent 5: prompt, model config, metadata
│   ├── data/
│   │   ├── bank_statement.json      # 35-transaction demo bank statement
│   │   ├── open_ar.json             # 38-invoice demo AR ledger
│   │   └── cash_app_results.json    # Pre-built demo data results
│   ├── main.py                      # FastAPI app: SSE streaming, Blob Storage, App Insights
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── app/
│       └── page.js                  # Next.js: real-time pipeline UI, approve/reject workqueue
├── docs/
│   └── architecture.html            # Full architecture documentation (GitHub Pages)
└── README.md
```


## Running it locally

You need: **Python 3.11+**, **Node.js 18+**, and **Git**. That is it for demo mode. For live Azure mode you also need an Azure AI Foundry project.

### Step 1: Clone the repo

```bash
git clone https://github.com/vinaygangidi/cash-application-foundry.git
cd cash-application-foundry
```

### Step 2: Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Step 3: Configure environment variables

Copy the example file and fill it in:

```bash
cp .env.example .env
```

**Demo mode** (runs on built-in sample data, no Azure account needed):

```
USE_FIXTURES=true
```

That is the only line you need for demo mode. Leave everything else blank.

**Live Azure mode** (runs the real agents against your Azure AI Foundry project):

```
AZURE_AI_ENDPOINT=https://your-resource-name.services.ai.azure.com
AZURE_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
USE_FIXTURES=false
```

Where to find these values: go to [ai.azure.com](https://ai.azure.com), open your project, click Overview. The endpoint and key are listed there.

### Step 4: Start the backend

```bash
uvicorn main:app --port 8001 --reload
```

You should see: `Uvicorn running on http://0.0.0.0:8001`

### Step 5: Frontend setup (separate terminal)

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8001 npm run dev
```

Open `http://localhost:3000` in your browser. Click **Load Demo Data**, then **Run Cash Application**.

### Verify it is working

The UI shows 5 agents running one after another with streaming output. The full pipeline takes about 30-60 seconds in demo mode and 2-4 minutes in live Azure mode depending on the model.


## Deploying to Railway + Vercel

### Backend to Railway

1. Connect GitHub repo, set root to `/backend`
2. Railway detects the Dockerfile automatically
3. Add your environment variables in the Railway dashboard
4. Railway gives you a public HTTPS URL

### Frontend to Vercel

1. Connect GitHub repo, set root to `/frontend`
2. Add `NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app`
3. Every push to `main` deploys automatically


## MVP vs where this goes in production

The current build is optimized for the hackathon with a reliable demo, real Azure inference, and real streaming. Here's the gap between what we built and what a production deployment looks like:

| What | Today | Production | Azure service |
|---|---|---|---|
| Input format | JSON payload | PDF bank statements + ERP exports | Azure Document Intelligence |
| Storage | Per-run Blob files | Immutable 7-year archive with lifecycle tiers | Azure Blob Storage (WORM policy) |
| Job processing | One at a time, synchronous | Async queue, 100+ batches/hour | Azure Service Bus + Container Apps |
| History | Ephemeral | Full run history, searchable, exportable | Azure PostgreSQL Flexible Server |
| Login | None | Microsoft SSO with role-based access | Microsoft Entra ID |
| Secrets | .env file | Centralized, auto-rotating | Azure Key Vault |
| Scaling | 1 Railway container | Auto-scale 1 to 20 workers on queue depth | Azure Container Apps + KEDA |
| ERP write-back | UI only | Auto-post to SAP / Oracle / NetSuite | Azure Logic Apps |


## Audit trail: every AI decision is traceable

Finance teams need to answer questions like: "Why did the system post TXN-007 to GL 6020?" or "Who approved the compliance hold on this payment?" The full production schema captures everything:

```sql
-- Every batch run
CREATE TABLE runs (
  id            UUID PRIMARY KEY,
  company_id    UUID NOT NULL,         -- which tenant
  submitted_by  TEXT NOT NULL,         -- who triggered the run (Entra ID UPN)
  blob_path_bank TEXT,                 -- link to original bank statement PDF in Blob Storage
  result_json   JSONB,                 -- full swarm output
  status        TEXT                   -- pending | running | complete | failed
);

-- Every agent's input and output, immutable
CREATE TABLE agent_events (
  run_id     UUID REFERENCES runs(id),
  agent      TEXT,                     -- which agent
  model      TEXT,                     -- which model actually ran
  tokens_in  INT,
  tokens_out INT,
  payload    JSONB                     -- full input + output
);

-- The workqueue with human decisions recorded
CREATE TABLE work_queue (
  run_id          UUID REFERENCES runs(id),
  txn_id          TEXT,
  status          TEXT DEFAULT 'pending',  -- pending | approved | rejected
  actioned_by     TEXT,                    -- analyst UPN
  override_note   TEXT                     -- why they disagreed with the AI
);
```

This gives auditors a complete chain from source document to AI reasoning to human decision to GL posting. SOX compliant, 7-year retention.


## Security

- **No data leaves your Azure tenant.** Azure OpenAI processes everything in-region.
- **No API keys in production code.** Service Principal + Managed Identity for all Azure service auth.
- **OFAC screening happens before any LLM processing.** A compliance hold means zero AI analysis. The transaction is frozen immediately.
- **Segregation of duties.** The agent that generates a GL posting cannot approve it. Human sign-off required above $10K.
- **All data encrypted at rest** (AES-256) and in transit (TLS 1.3). Private Endpoints for backend services in production. Nothing exposed to the public internet.


## The compounding advantage

Every batch the system processes generates labeled training data. After enough runs, the Mismatch Reasoning Agent can be fine-tuned on your company's specific deduction patterns: your freight allowance rates, your top customers' payment habits, your contract terms. A fine-tuned smaller model outperforms a generic large one on domain-specific tasks and costs less to run. After 12 months of production use, this system would be significantly more accurate than anything a competitor could deploy on day one.


## Scale roadmap

**Phase 1: Now** (hackathon MVP): 1 company, 35 transactions, demo data + live Azure inference, SSE streaming UI

**Phase 2: 3 months** (production beta): PDF ingestion via Document Intelligence, async queue via Service Bus, PostgreSQL audit trail, Entra ID login, 3 pilot companies, 500 txns/day

**Phase 3: 12 months** (enterprise platform): 50+ companies, 1M+ txns/month, SAP/Oracle/NetSuite connectors, multi-region, auto-scaling, fine-tuned models, Azure Marketplace listing


## Team

**Vinay Gangidi** | [vinay.gangidi@gmail.com](mailto:vinay.gangidi@gmail.com)


*Microsoft Build AI Hackathon 2026 · Theme 05: Agent Swarms · [github.com/vinaygangidi/cash-application-foundry](https://github.com/vinaygangidi/cash-application-foundry)*
