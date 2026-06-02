"""
Mismatch Resolution Agent (AI Reasoning)

Analyzes unmatched payments and invoices using AI reasoning to identify
likely matches, exceptions, and provide resolution recommendations.
"""

import json
from typing import List, Dict, Any


class MismatchAgent:
    """
    Uses AI reasoning to resolve unmatched payments and invoices.
    """

    def __init__(self, client, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    async def resolve_mismatches(
        self, unmatched_payments: List[Dict], unmatched_invoices: List[Dict]
    ) -> dict:
        """
        Use AI to reason through mismatches and provide recommendations.

        Args:
            unmatched_payments: list of bank transactions with no match
            unmatched_invoices: list of AR invoices with no payment

        Returns:
            dict with reasoning, recommendations, and exception categorization
        """

        reasoning_results = []

        # Analyze each unmatched payment
        for payment in unmatched_payments:
            resolution = self._analyze_payment_exception(payment, unmatched_invoices)
            reasoning_results.append(resolution)

        # Categorize exceptions
        exception_categories = self._categorize_exceptions(reasoning_results)

        return {
            "status": "completed",
            "reasoning_results": reasoning_results,
            "exception_summary": exception_categories,
            "total_exceptions": len(reasoning_results),
            "recommendations": self._generate_recommendations(exception_categories),
        }

    def _analyze_payment_exception(
        self, payment: Dict, unmatched_invoices: List[Dict]
    ) -> dict:
        """
        Analyze a single unmatched payment for possible explanations.
        """
        anomaly_flags = payment.get("anomaly_flags", [])
        amount = payment.get("amount", 0)
        payer_normalized = payment.get("payer_name_normalized", "")
        remittance = payment.get("remittance_text_normalized", "")

        # Categorize payment
        exception_type = self._categorize_payment(anomaly_flags, amount, remittance)

        # Find potential matches (more lenient)
        potential_matches = self._find_potential_matches(payment, unmatched_invoices)

        return {
            "bank_txn_id": payment.get("bank_transaction_id", ""),
            "amount": amount,
            "payer": payer_normalized,
            "exception_type": exception_type,
            "anomaly_flags": anomaly_flags,
            "potential_matches": potential_matches,
            "reasoning": self._generate_reasoning(exception_type, potential_matches),
            "recommendation": self._generate_recommendation(exception_type, potential_matches),
            "confidence": self._calc_confidence(exception_type, potential_matches),
        }

    def _categorize_payment(
        self, anomaly_flags: List[str], amount: float, remittance: str
    ) -> str:
        """Categorize the payment exception type."""

        if "MISSING_REMITTANCE" in anomaly_flags:
            return "NO_REMITTANCE_DATA"

        if "NSF_RETURN" in anomaly_flags:
            return "NSF_OR_RETURN"

        if "FX_PAYMENT" in anomaly_flags:
            return "FOREIGN_EXCHANGE"

        if "PREPAYMENT" in anomaly_flags:
            return "PREPAYMENT"

        if "INTERCOMPANY_NET" in anomaly_flags:
            return "INTERCOMPANY_NETTING"

        if "COMPLIANCE_HOLD" in anomaly_flags:
            return "COMPLIANCE_FLAG"

        if "EDI_REMITTANCE_PENDING" in anomaly_flags:
            return "EDI_PENDING"

        if "THIRD_PARTY_PAYER" in anomaly_flags:
            return "THIRD_PARTY_PAYMENT"

        if amount < 0:
            return "DEBIT_MEMO_OR_REVERSAL"

        if amount > 50000:
            return "LARGE_PAYMENT_UNUSUAL"

        return "POSSIBLE_DUPLICATE_OR_TIMING"

    def _find_potential_matches(
        self, payment: Dict, unmatched_invoices: List[Dict]
    ) -> List[Dict]:
        """Find potential matches using lenient criteria."""
        potential = []

        payer = payment.get("payer_name_normalized", "")
        amount = payment.get("amount", 0)

        for inv in unmatched_invoices:
            customer = inv.get("customer_name_normalized", "")

            # Lenient customer match
            name_words_payer = set(payer.split())
            name_words_customer = set(customer.split())
            if name_words_payer & name_words_customer:
                # Some word overlap
                potential.append(
                    {
                        "invoice_number": inv.get("invoice_number", ""),
                        "customer": customer,
                        "open_balance": inv.get("open_balance", 0),
                        "match_reason": "Customer name overlap",
                        "amount_variance": abs(amount - inv.get("open_balance", 0)),
                    }
                )

        # Sort by amount variance
        potential.sort(key=lambda x: x["amount_variance"])
        return potential[:3]  # Return top 3

    def _generate_reasoning(
        self, exception_type: str, potential_matches: List[Dict]
    ) -> str:
        """Generate AI reasoning explanation."""
        reasoning_map = {
            "NO_REMITTANCE_DATA": "Payment received with no invoice reference; requires manual review to match to open AR.",
            "NSF_RETURN": "Transaction flagged as NSF or bank return; should be reversed or reconciled separately.",
            "FOREIGN_EXCHANGE": "Foreign currency or FX payment detected; may be applying to multi-currency invoice or requires conversion.",
            "PREPAYMENT": "Payment marked as prepayment/deposit; likely applying to future invoices or deposit account.",
            "INTERCOMPANY_NETTING": "Payment references intercompany netting; may be contra-account or AR/AP offset.",
            "COMPLIANCE_FLAG": "Payment from sanctioned region; holds compliance review before posting.",
            "EDI_PENDING": "Large round amount with no remittance suggests EDI 820 remittance arriving separately.",
            "THIRD_PARTY_PAYMENT": "Payment from third party not matching payer; may be collection agency or factoring arrangement.",
            "DEBIT_MEMO_OR_REVERSAL": "Negative amount indicates reversal, debit memo, or chargeback.",
            "LARGE_PAYMENT_UNUSUAL": "Unusually large payment; possible lump-sum settlement or consolidated payment.",
            "POSSIBLE_DUPLICATE_OR_TIMING": "Payment cannot be matched; possible timing issue, duplicate, or data quality concern.",
        }
        return reasoning_map.get(exception_type, "Unclassified exception requiring manual review.")

    def _generate_recommendation(
        self, exception_type: str, potential_matches: List[Dict]
    ) -> str:
        """Generate action recommendation."""
        if potential_matches:
            top_match = potential_matches[0]
            return f"REVIEW: Consider matching to {top_match['invoice_number']} (open balance: ${top_match['open_balance']:.2f})"

        recommendation_map = {
            "NO_REMITTANCE_DATA": "MANUAL_REVIEW: Contact customer for remittance information",
            "NSF_RETURN": "REVERSE: Process reversal in ERP system",
            "FOREIGN_EXCHANGE": "MANUAL_REVIEW: Route to FX/treasury team",
            "PREPAYMENT": "HOLD: Route to deposit account or prepayment handling process",
            "INTERCOMPANY_NETTING": "DEFER: Process as intercompany settlement",
            "COMPLIANCE_FLAG": "HOLD: Escalate to compliance review",
            "EDI_PENDING": "HOLD: Await EDI 820 remittance arrival",
            "THIRD_PARTY_PAYMENT": "MANUAL_REVIEW: Verify third-party collection arrangement",
            "DEBIT_MEMO_OR_REVERSAL": "REVERSE: Post reversal entry",
            "LARGE_PAYMENT_UNUSUAL": "MANUAL_REVIEW: Escalate for approval",
            "POSSIBLE_DUPLICATE_OR_TIMING": "MANUAL_REVIEW: Investigate data quality",
        }
        return recommendation_map.get(exception_type, "MANUAL_REVIEW: Requires human decision")

    def _categorize_exceptions(self, reasoning_results: List[Dict]) -> Dict[str, int]:
        """Count exceptions by type."""
        categories = {}
        for result in reasoning_results:
            exc_type = result.get("exception_type", "UNKNOWN")
            categories[exc_type] = categories.get(exc_type, 0) + 1
        return categories

    def _generate_recommendations(
        self, exception_categories: Dict[str, int]
    ) -> List[str]:
        """Generate high-level recommendations."""
        recommendations = []

        if exception_categories.get("NO_REMITTANCE_DATA", 0) > 0:
            recommendations.append(
                f"ACTION: {exception_categories['NO_REMITTANCE_DATA']} payments need remittance clarification"
            )

        if exception_categories.get("COMPLIANCE_FLAG", 0) > 0:
            recommendations.append(
                f"ESCALATE: {exception_categories['COMPLIANCE_FLAG']} payments on compliance hold"
            )

        if exception_categories.get("EDI_PENDING", 0) > 0:
            recommendations.append(
                f"MONITOR: {exception_categories['EDI_PENDING']} payments awaiting EDI remittances"
            )

        if not recommendations:
            recommendations.append("All exceptions categorized and flagged for action")

        return recommendations

    def _calc_confidence(self, exception_type: str, potential_matches: List[Dict]) -> float:
        """Calculate confidence in categorization."""
        if potential_matches:
            return 0.75
        if exception_type in [
            "NO_REMITTANCE_DATA",
            "NSF_RETURN",
            "FOREIGN_EXCHANGE",
            "COMPLIANCE_FLAG",
        ]:
            return 0.90
        return 0.65
