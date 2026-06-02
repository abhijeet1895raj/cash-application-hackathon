# 💰 Cash Application Foundry

A **5-Agent AI Pipeline** for automated bank statement reconciliation with real-time streaming to the browser.

## Overview

The Cash Application Foundry orchestrates a sophisticated multi-agent workflow to:

1. **Parse Bank Statements** - Normalize transactions, extract remittance data, flag anomalies
2. **Analyze AR Ledger** - Enrich invoices with aging, risk flags, and collection intelligence
3. **Match Payments** - Reconcile transactions to invoices using fuzzy matching and reference detection
4. **Resolve Mismatches** - Use AI reasoning to categorize exceptions and recommend actions
5. **Generate Posting** - Produce ERP-ready GL journal entries and posting batches

**All agent outputs stream to the browser in real-time via Server-Sent Events (SSE).**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                     │
│         Real-time SSE streaming + interactive UI            │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP EventStream
┌────────────────────▼────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  /api/process  →  Agent Pipeline  →  SSE Response           │
└───────────────────────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────┐
    │  1. Bank Statement Agent (Parsing & Normalization)      │
    │     ↓ normalized_transactions                           │
    ├─────────────────────────────────────────────────┤
    │  2. AR Ledger Agent (Invoice Enrichment)               │
    │     ↓ enriched_invoices + aging                        │
    ├─────────────────────────────────────────────────┤
    │  3. Reconciliation Agent (Matching)                     │
    │     ↓ matched_set + unmatched                          │
    ├─────────────────────────────────────────────────┤
    │  4. Mismatch Agent (AI Reasoning)                       │
    │     ↓ reasoning_results + recommendations              │
    ├─────────────────────────────────────────────────┤
    │  5. Posting Agent (GL Batch Generation)                │
    │     ↓ journal_entries + posting_batch                  │
    └─────────────────────────────────────────────────┘
```

---

## Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+ |
| **API Framework** | FastAPI 0.115.5 |
| **Streaming** | Server-Sent Events (SSE) |
| **AI/LLM** | Azure OpenAI (AsyncAzureOpenAI) |
| **Frontend** | Next.js 14 (App Router) |
| **Styling** | Tailwind CSS 3.3 |
| **HTTP Client** | Browser Fetch API |

---

## Folder Structure

```
cash-application-foundry/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── bank_statement_agent.py    (Agent 1)
│   │   ├── ar_ledger_agent.py         (Agent 2)
│   │   ├── reconciliation_agent.py    (Agent 3)
│   │   ├── mismatch_agent.py          (Agent 4)
│   │   ├── posting_agent.py           (Agent 5)
│   │   └── cash_app.py                (Orchestrator)
│   ├── data/
│   │   ├── bank_statement.json        (35 transactions)
│   │   └── open_ar.json               (38 invoices)
│   ├── main.py                        (FastAPI server)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.js                    (Main streaming UI)
│   │   └── globals.css
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Azure OpenAI API key & endpoint (optional; demo runs on fixtures)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials (optional for demo)

# Run server
python main.py
```

Server runs on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on `http://localhost:3000`

### 3. Access the UI

1. Open [http://localhost:3000](http://localhost:3000) in your browser
2. Click **"▶ Start Pipeline"**
3. Watch agents execute in real-time with streaming output

---

## API Endpoints

### `POST /api/process`
Process demo bank statement and AR ledger (fixture-based).

**Response**: Server-Sent Events stream

**Example event**:
```json
{
  "agent": "bank_statement_agent",
  "status": "completed",
  "output": {
    "status": "completed",
    "statement_date": "2025-06-30",
    "normalized_transactions": [...],
    "transaction_count": 35,
    "anomaly_count": 8
  },
  "timestamp": "2025-06-30T15:30:45.123Z"
}
```

### `GET /health`
Health check endpoint.

```json
{
  "status": "healthy",
  "service": "Cash Application Foundry",
  "version": "1.0.0",
  "fixtures_enabled": true
}
```

### `GET /api/fixtures/bank-statement`
Get bank statement fixture for reference.

### `GET /api/fixtures/ar-ledger`
Get AR ledger fixture for reference.

---

## Agent Details

### 1. Bank Statement Agent 🏦

**Input**: Raw bank statement transactions  
**Output**: Normalized transactions with anomaly flags

**Capabilities**:
- Payer name normalization (strip noise, expand abbreviations)
- SWIFT 35-char truncation detection
- Remittance parsing for invoice/PO/legacy refs
- Anomaly detection: NSF, FX, compliance holds, duplicates, post-dated checks, etc.
- Confidence scoring

**Anomaly Flags**:
- `MISSING_REMITTANCE` - No invoice reference
- `NSF_RETURN` - Return code detected
- `FX_PAYMENT` - Foreign currency
- `SWIFT_NAME_TRUNCATION` - Name appears cut off
- `POST_DATED_CHECK` / `STALE_CHECK` - Timing issues
- `PREPAYMENT` - Advance/deposit language detected
- `INTERCOMPANY_NET` - Netting/interco language
- `COMPLIANCE_HOLD` - Sanctioned region markers
- And more...

### 2. AR Ledger Agent 📋

**Input**: Open AR invoices  
**Output**: Enriched ledger with aging and risk assessment

**Capabilities**:
- Customer name normalization
- Days outstanding calculation
- Aging bucket classification (Current, 31-60, 61-90, 90+)
- Payment terms parsing (NET30, NET60, etc.)
- Invoice-level risk flagging
- AR portfolio aging summary

**Risk Flags**:
- `PAST_DUE` - Days outstanding > 30
- `SIGNIFICANTLY_OVERDUE` - Days outstanding > 90
- `PARTIAL_PAYMENT` - Partially paid invoice
- `INVOICE_DISPUTE` - Under dispute
- `CREDIT_HOLD` - Customer credit hold

### 3. Reconciliation Agent 🔗

**Input**: Normalized transactions + enriched invoices  
**Output**: Matched payment set + unmatched items

**Matching Strategy**:
1. **Exact Reference Match** (99% confidence) - Invoice referenced in remittance
2. **Fuzzy Match** (60-99%) - Customer name + amount similarity
3. **Partial Payment Match** (85%) - Amount is 70-100% of invoice balance

### 4. Mismatch Agent 🤔 (AI Reasoning)

**Input**: Unmatched payments + unmatched invoices  
**Output**: Exception categorization + recommendations

**Exception Categories**:
- `NO_REMITTANCE_DATA` → MANUAL_REVIEW
- `NSF_RETURN` → REVERSE
- `FOREIGN_EXCHANGE` → Route to treasury
- `COMPLIANCE_FLAG` → Escalate to compliance
- And more...

### 5. Posting Agent 📝

**Input**: Matched payments + exceptions + reasoning results  
**Output**: ERP-ready GL posting batch

**GL Entry Format** includes:
- Entry type (PAYMENT, EXCEPTION)
- Posting status (READY, REVIEW_REQUIRED, DEFERRED)
- Accounting entries (debits/credits)
- Audit trail

---

## Demo Data

### Bank Statement (35 transactions)
- Date: 2025-06-15 to 2025-06-30
- Amount range: $5K - $75K
- Payment types: WIRE, ACH, CHECK
- Scenarios: exact matches, partial payments, mismatches, NSF, FX, compliance flags, etc.

### AR Ledger (38 invoices)
- Date range: 2025-03-15 to 2025-06-30
- Invoices vary from CURRENT to 90+ DAYS overdue
- Partially paid invoices
- Credit-hold and disputed invoices
- Total AR: ~$1.2M

---

## Real-Time Streaming

The frontend uses **Server-Sent Events (SSE)** to receive agent outputs in real-time. Each agent's JSON output feeds to the next, and all progress is streamed to the browser for live tracking.

---

## Environment Configuration

Create `.env` in `backend/` folder:

```env
AZURE_AI_ENDPOINT=https://your-resource-name.services.ai.azure.com/
AZURE_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
USE_FIXTURES=true
```

---

## Development

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Build for Production
```bash
# Backend: Create requirements.txt
pip freeze > backend/requirements.txt

# Frontend: Build static
cd frontend
npm run build
npm start
```

---

## Key Features

✅ **5-Agent Sequential Pipeline** - Each agent's output feeds the next  
✅ **Real-time SSE Streaming** - Live browser updates as agents execute  
✅ **Anomaly Detection** - 14+ bank transaction anomaly flags  
✅ **Fuzzy Matching** - Customer name + amount reconciliation  
✅ **AI Reasoning** - Exception categorization with recommendations  
✅ **ERP-Ready Output** - Standard GL posting format  
✅ **Demo Data** - 35 transactions + 38 invoices pre-built  
✅ **Responsive UI** - Tailwind CSS + Next.js 14  

---

## Support & Contributions

For issues or contributions, please refer to the development team.

Built with ❤️ using FastAPI, Next.js, and Azure OpenAI