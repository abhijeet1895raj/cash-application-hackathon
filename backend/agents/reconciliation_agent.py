"""
Reconciliation Agent

Matches bank transactions to AR invoices using fuzzy customer/amount logic,
produces a match report with confidence scores and unmatched items.
"""

import json
from typing import List, Dict, Tuple
from difflib import SequenceMatcher


class ReconciliationAgent:
    """
    Matches bank payments to open AR invoices.
    """

    def __init__(self, client, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    async def reconcile_payments_to_invoices(
        self, normalized_txns: List[Dict], ar_invoices: List[Dict]
    ) -> dict:
        """
        Match bank transactions to AR invoices.

        Args:
            normalized_txns: output from bank_statement_agent
            ar_invoices: output from ar_ledger_agent

        Returns:
            dict with matched_set, unmatched_payments, unmatched_invoices, summary
        """

        matched_set = []
        matched_txn_ids = set()
        matched_invoice_ids = set()

        # Exact matches (amount + reference)
        for txn in normalized_txns:
            if txn["bank_transaction_id"] in matched_txn_ids:
                continue

            for inv in ar_invoices:
                if inv["invoice_number"] in matched_invoice_ids:
                    continue

                # Check if reference matches
                if self._is_exact_reference_match(txn, inv):
                    matched_set.append(
                        {
                            "match_type": "EXACT_REFERENCE",
                            "confidence": 0.99,
                            "bank_txn_id": txn["bank_transaction_id"],
                            "invoice_number": inv["invoice_number"],
                            "amount": txn["amount"],
                            "customer_txn": txn.get("payer_name_normalized", ""),
                            "customer_inv": inv.get("customer_name_normalized", ""),
                            "notes": f"Invoice ref found in remittance",
                        }
                    )
                    matched_txn_ids.add(txn["bank_transaction_id"])
                    matched_invoice_ids.add(inv["invoice_number"])
                    break

        # Fuzzy matches (customer name + amount with tolerance)
        for txn in normalized_txns:
            if txn["bank_transaction_id"] in matched_txn_ids:
                continue

            for inv in ar_invoices:
                if inv["invoice_number"] in matched_invoice_ids:
                    continue

                # Fuzzy match on customer + amount
                match_score = self._fuzzy_match_score(txn, inv)
                if match_score > 0.75:
                    matched_set.append(
                        {
                            "match_type": "FUZZY_MATCH",
                            "confidence": match_score,
                            "bank_txn_id": txn["bank_transaction_id"],
                            "invoice_number": inv["invoice_number"],
                            "amount": txn["amount"],
                            "customer_txn": txn.get("payer_name_normalized", ""),
                            "customer_inv": inv.get("customer_name_normalized", ""),
                            "notes": f"Customer/amount similarity: {match_score:.2%}",
                        }
                    )
                    matched_txn_ids.add(txn["bank_transaction_id"])
                    matched_invoice_ids.add(inv["invoice_number"])
                    break

        # Partial payment matches (amount < invoice balance, within 5%)
        for txn in normalized_txns:
            if txn["bank_transaction_id"] in matched_txn_ids:
                continue

            for inv in ar_invoices:
                if inv["invoice_number"] in matched_invoice_ids:
                    continue

                if self._is_partial_payment_match(txn, inv):
                    matched_set.append(
                        {
                            "match_type": "PARTIAL_PAYMENT",
                            "confidence": 0.85,
                            "bank_txn_id": txn["bank_transaction_id"],
                            "invoice_number": inv["invoice_number"],
                            "amount": txn["amount"],
                            "customer_txn": txn.get("payer_name_normalized", ""),
                            "customer_inv": inv.get("customer_name_normalized", ""),
                            "notes": f"Partial payment of invoice balance",
                        }
                    )
                    matched_txn_ids.add(txn["bank_transaction_id"])
                    # Don't mark invoice as matched (can have multiple partial payments)
                    break

        # Unmatched items
        unmatched_payments = [
            txn
            for txn in normalized_txns
            if txn["bank_transaction_id"] not in matched_txn_ids
        ]
        unmatched_invoices = [
            inv for inv in ar_invoices if inv["invoice_number"] not in matched_invoice_ids
        ]

        return {
            "status": "completed",
            "matched_count": len(matched_set),
            "matched_set": matched_set,
            "unmatched_payments": unmatched_payments,
            "unmatched_invoice_count": len(unmatched_invoices),
            "unmatched_invoices": unmatched_invoices,
            "total_matched_amount": sum(m["amount"] for m in matched_set),
            "summary": {
                "total_payments": len(normalized_txns),
                "matched_payments": len(matched_txn_ids),
                "unmatched_payments": len(unmatched_payments),
                "match_rate": f"{len(matched_txn_ids) / len(normalized_txns) * 100:.1f}%"
                if normalized_txns
                else "0%",
            },
        }

    def _is_exact_reference_match(self, txn: Dict, inv: Dict) -> bool:
        """Check if invoice is referenced in transaction remittance."""
        invoice_number = inv.get("invoice_number", "")
        references = txn.get("reference_numbers", [])

        # Normalize invoice number for comparison
        inv_normalized = invoice_number.replace("-", "").upper()

        for ref in references:
            ref_normalized = ref.replace("-", "").upper()
            if inv_normalized in ref_normalized or ref_normalized in inv_normalized:
                return True

        return False

    def _fuzzy_match_score(self, txn: Dict, inv: Dict) -> float:
        """Calculate fuzzy match score based on customer and amount."""
        customer_score = self._name_similarity(
            txn.get("payer_name_normalized", ""),
            inv.get("customer_name_normalized", ""),
        )

        amount_score = self._amount_similarity(
            txn.get("amount", 0), inv.get("open_balance", 0)
        )

        # Weighted average: 60% customer, 40% amount
        return customer_score * 0.6 + amount_score * 0.4

    def _is_partial_payment_match(self, txn: Dict, inv: Dict) -> bool:
        """Check if transaction is a partial payment of invoice."""
        txn_amount = txn.get("amount", 0)
        inv_balance = inv.get("open_balance", 0)

        if txn_amount <= 0 or inv_balance <= 0:
            return False

        # Check if amount is between 70-100% of invoice balance
        ratio = txn_amount / inv_balance
        return 0.7 <= ratio <= 1.0 and self._name_similarity(
            txn.get("payer_name_normalized", ""),
            inv.get("customer_name_normalized", ""),
        ) > 0.6

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using SequenceMatcher."""
        if not name1 or not name2:
            return 0.0

        # Simple word-based similarity
        words1 = set(name1.split())
        words2 = set(name2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _amount_similarity(self, amount1: float, amount2: float) -> float:
        """Calculate similarity between two amounts (within 5% tolerance)."""
        if amount1 <= 0 or amount2 <= 0:
            return 0.0

        ratio = min(amount1, amount2) / max(amount1, amount2)
        # Perfect match = 1.0, within 5% = 0.95, etc.
        return max(0, ratio)
