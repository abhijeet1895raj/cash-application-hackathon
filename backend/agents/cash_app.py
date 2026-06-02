"""
Cash Application Orchestrator

Coordinates the 5-agent pipeline sequentially, passing output from each
agent to the next, and handling streaming to the browser via SSE.
"""

import json
import os
from typing import AsyncGenerator, Dict, Any, List

from agents.bank_statement_agent import BankStatementAgent
from agents.ar_ledger_agent import ARLedgerAgent
from agents.reconciliation_agent import ReconciliationAgent
from agents.mismatch_agent import MismatchAgent
from agents.posting_agent import PostingAgent


class CashApplicationFoundry:
    """
    Orchestrates the 5-agent pipeline for cash application reconciliation.
    """

    def __init__(self, client, use_fixtures: bool = True):
        self.client = client
        self.use_fixtures = use_fixtures

        # Initialize agents
        self.bank_agent = BankStatementAgent(client)
        self.ar_agent = ARLedgerAgent(client)
        self.recon_agent = ReconciliationAgent(client)
        self.mismatch_agent = MismatchAgent(client)
        self.posting_agent = PostingAgent(client)

    async def run_pipeline(
        self, bank_statement_data: dict, ar_data: dict
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the 5-agent pipeline and yield output from each agent as it completes.

        Args:
            bank_statement_data: raw bank statement with transactions
            ar_data: open AR invoices

        Yields:
            dict with agent_name, status, output, timestamp
        """

        # Agent 1: Bank Statement Parsing
        yield {
            "agent": "bank_statement_agent",
            "status": "starting",
            "timestamp": self._get_timestamp(),
        }

        bank_result = await self.bank_agent.process_bank_statement(bank_statement_data)

        yield {
            "agent": "bank_statement_agent",
            "status": "completed",
            "output": bank_result,
            "timestamp": self._get_timestamp(),
        }

        normalized_txns = bank_result.get("normalized_transactions", [])

        # Agent 2: AR Ledger Analysis
        yield {
            "agent": "ar_ledger_agent",
            "status": "starting",
            "timestamp": self._get_timestamp(),
        }

        ar_result = await self.ar_agent.process_ar_ledger(ar_data)

        yield {
            "agent": "ar_ledger_agent",
            "status": "completed",
            "output": ar_result,
            "timestamp": self._get_timestamp(),
        }

        ar_invoices = ar_result.get("invoices", [])

        # Agent 3: Reconciliation Matching
        yield {
            "agent": "reconciliation_agent",
            "status": "starting",
            "timestamp": self._get_timestamp(),
        }

        recon_result = await self.recon_agent.reconcile_payments_to_invoices(
            normalized_txns, ar_invoices
        )

        yield {
            "agent": "reconciliation_agent",
            "status": "completed",
            "output": recon_result,
            "timestamp": self._get_timestamp(),
        }

        matched_set = recon_result.get("matched_set", [])
        unmatched_payments = recon_result.get("unmatched_payments", [])
        unmatched_invoices = recon_result.get("unmatched_invoices", [])

        # Agent 4: Mismatch Resolution (AI Reasoning)
        yield {
            "agent": "mismatch_agent",
            "status": "starting",
            "timestamp": self._get_timestamp(),
        }

        mismatch_result = await self.mismatch_agent.resolve_mismatches(
            unmatched_payments, unmatched_invoices
        )

        yield {
            "agent": "mismatch_agent",
            "status": "completed",
            "output": mismatch_result,
            "timestamp": self._get_timestamp(),
        }

        # Agent 5: Posting Instructions
        yield {
            "agent": "posting_agent",
            "status": "starting",
            "timestamp": self._get_timestamp(),
        }

        posting_result = await self.posting_agent.generate_posting_instructions(
            matched_set,
            unmatched_payments,
            unmatched_invoices,
            mismatch_result.get("reasoning_results", []),
            bank_statement_data.get("statement_date", ""),
        )

        yield {
            "agent": "posting_agent",
            "status": "completed",
            "output": posting_result,
            "timestamp": self._get_timestamp(),
        }

        # Final pipeline result
        yield {
            "agent": "pipeline",
            "status": "completed",
            "summary": {
                "total_transactions": len(normalized_txns),
                "total_invoices": len(ar_invoices),
                "matched_payments": recon_result.get("summary", {}).get("matched_payments", 0),
                "unmatched_payments": len(unmatched_payments),
                "exceptions_identified": len(mismatch_result.get("reasoning_results", [])),
                "ready_to_post": posting_result.get("summary", {}).get("ready_to_post", 0),
            },
            "timestamp": self._get_timestamp(),
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"
