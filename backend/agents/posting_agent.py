"""
Posting Instructions Agent

Generates ERP-ready posting journal entries for matched payments,
partial payments, exceptions, and produces a standard GL posting format.
"""

import json
from typing import List, Dict, Any
from datetime import datetime


class PostingAgent:
    """
    Generates ERP-ready posting instructions from reconciliation results.
    """

    def __init__(self, client, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    async def generate_posting_instructions(
        self,
        matched_set: List[Dict],
        unmatched_payments: List[Dict],
        unmatched_invoices: List[Dict],
        reasoning_results: List[Dict],
        statement_date: str,
    ) -> dict:
        """
        Generate ERP-ready posting instructions.

        Args:
            matched_set: successful matches from reconciliation
            unmatched_payments: payments with no match
            unmatched_invoices: invoices with no payment
            reasoning_results: AI reasoning on mismatches
            statement_date: bank statement date

        Returns:
            dict with journal entries, GL posting format, and audit trail
        """

        journal_entries = []
        deferred_entries = []

        # Process matched payments
        for match in matched_set:
            entry = self._create_payment_entry(match, statement_date)
            if entry["status"] == "DEFERRED":
                deferred_entries.append(entry)
            else:
                journal_entries.append(entry)

        # Process exceptions
        for unmatched in unmatched_payments:
            exception_entry = self._create_exception_entry(unmatched, statement_date)
            if exception_entry:
                if exception_entry["status"] == "DEFERRED":
                    deferred_entries.append(exception_entry)
                else:
                    journal_entries.append(exception_entry)

        # Generate GL posting batch
        gl_batch = self._create_gl_batch(journal_entries, statement_date)

        return {
            "status": "completed",
            "statement_date": statement_date,
            "journal_entries": journal_entries,
            "deferred_entries": deferred_entries,
            "gl_posting_batch": gl_batch,
            "summary": {
                "ready_to_post": len(journal_entries),
                "deferred": len(deferred_entries),
                "total_cash_applied": sum(
                    e.get("amount", 0)
                    for e in journal_entries
                    if e.get("entry_type") == "PAYMENT"
                ),
            },
        }

    def _create_payment_entry(self, match: Dict, statement_date: str) -> dict:
        """Create GL entry for matched payment."""
        amount = match.get("amount", 0)
        invoice_number = match.get("invoice_number", "")
        match_confidence = match.get("confidence", 0)

        # Determine posting status
        status = "READY" if match_confidence > 0.90 else "REVIEW_REQUIRED"

        return {
            "entry_id": f"ENTRY_{statement_date}_{match['bank_txn_id'][:8]}",
            "entry_type": "PAYMENT",
            "status": status,
            "statement_date": statement_date,
            "description": f"Cash application to invoice {invoice_number}",
            "invoice_reference": invoice_number,
            "bank_txn_id": match.get("bank_txn_id", ""),
            "amount": amount,
            "currency": "USD",
            "match_type": match.get("match_type", ""),
            "confidence": match_confidence,
            "accounting_entries": [
                {
                    "line_number": 1,
                    "account": "1200",  # AR clearing/deposit account
                    "debit": amount,
                    "credit": 0,
                    "description": f"AR reduction - {invoice_number}",
                },
                {
                    "line_number": 2,
                    "account": "1010",  # Cash
                    "debit": 0,
                    "credit": amount,
                    "description": "Bank deposit applied",
                },
            ],
            "audit_trail": {
                "matched_to": invoice_number,
                "match_confidence": f"{match_confidence:.1%}",
            },
        }

    def _create_exception_entry(self, unmatched: Dict, statement_date: str) -> dict:
        """Create GL entry for unmatched payment exception."""
        amount = unmatched.get("amount", 0)
        anomaly_flags = unmatched.get("anomaly_flags", [])

        # Determine posting status based on flags
        if "COMPLIANCE_HOLD" in anomaly_flags:
            status = "DEFERRED"
            account = "1999"  # Suspense/clearance account
        elif "NSF_RETURN" in anomaly_flags:
            status = "READY"
            account = "1999"  # Suspense for reversal
        elif "MISSING_REMITTANCE" in anomaly_flags:
            status = "DEFERRED"
            account = "1900"  # Uncleared deposit
        else:
            status = "REVIEW_REQUIRED"
            account = "1900"  # Hold pending review

        return {
            "entry_id": f"EXCEPTION_{statement_date}_{unmatched['bank_transaction_id'][:8]}",
            "entry_type": "EXCEPTION",
            "status": status,
            "statement_date": statement_date,
            "description": f"Unmatched payment - {anomaly_flags[0] if anomaly_flags else 'UNKNOWN'}",
            "bank_txn_id": unmatched.get("bank_transaction_id", ""),
            "amount": amount,
            "currency": "USD",
            "anomaly_flags": anomaly_flags,
            "accounting_entries": [
                {
                    "line_number": 1,
                    "account": account,
                    "debit": amount,
                    "credit": 0,
                    "description": f"Unmatched deposit - {', '.join(anomaly_flags[:2])}",
                },
                {
                    "line_number": 2,
                    "account": "1010",
                    "debit": 0,
                    "credit": amount,
                    "description": "Bank deposit",
                },
            ],
            "audit_trail": {
                "anomalies": anomaly_flags,
                "action_required": status != "READY",
            },
        }

    def _create_gl_batch(self, journal_entries: List[Dict], statement_date: str) -> dict:
        """Create GL posting batch in standard format."""
        total_debits = 0
        total_credits = 0

        all_lines = []
        for entry_idx, entry in enumerate(journal_entries, 1):
            for line in entry.get("accounting_entries", []):
                all_lines.append(
                    {
                        "batch_line": len(all_lines) + 1,
                        "entry_sequence": entry_idx,
                        "entry_id": entry.get("entry_id", ""),
                        "account": line.get("account", ""),
                        "debit": line.get("debit", 0),
                        "credit": line.get("credit", 0),
                        "description": line.get("description", ""),
                    }
                )
                total_debits += line.get("debit", 0)
                total_credits += line.get("credit", 0)

        return {
            "batch_id": f"BATCH_{statement_date}",
            "batch_date": statement_date,
            "batch_status": "READY_TO_POST",
            "lines": all_lines,
            "batch_summary": {
                "entry_count": len(journal_entries),
                "line_count": len(all_lines),
                "total_debits": total_debits,
                "total_credits": total_credits,
                "is_balanced": abs(total_debits - total_credits) < 0.01,
            },
        }
