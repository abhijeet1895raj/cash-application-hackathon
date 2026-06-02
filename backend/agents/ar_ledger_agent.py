"""
AR Ledger Intelligence Agent

Analyzes open AR invoices and provides a searchable ledger for matching.
Extracts customer info, payment terms, aging, and flags collection risks.
"""

import json
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta


class ARLedgerAgent:
    """
    Analyzes open AR invoices and provides matching intelligence.
    """

    def __init__(self, client, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    async def process_ar_ledger(self, ar_data: dict) -> dict:
        """
        Process open AR invoices and return enriched ledger.

        Args:
            ar_data: dict with 'as_of_date' and 'invoices' list

        Returns:
            dict with status, invoices, summary stats, and aging buckets
        """

        as_of_date = ar_data.get("as_of_date", "")
        invoices = ar_data.get("invoices", [])

        enriched_invoices = []
        for inv in invoices:
            enriched = self._enrich_invoice(inv, as_of_date)
            enriched_invoices.append(enriched)

        # Calculate aging and risk
        aging_summary = self._calculate_aging(enriched_invoices, as_of_date)
        risk_summary = self._assess_credit_risk(enriched_invoices)

        return {
            "status": "completed",
            "as_of_date": as_of_date,
            "invoices": enriched_invoices,
            "invoice_count": len(enriched_invoices),
            "total_ar": sum(inv.get("open_balance", 0) for inv in enriched_invoices),
            "aging_summary": aging_summary,
            "risk_summary": risk_summary,
        }

    def _enrich_invoice(self, inv: dict, as_of_date: str) -> dict:
        """
        Enrich a single invoice with aging, normalization, and flags.
        """
        invoice_number = inv.get("invoice_number", "")
        customer_name = inv.get("customer_name", "").strip()
        invoice_date = inv.get("invoice_date", "")
        due_date = inv.get("due_date", "")
        open_balance = inv.get("open_balance", 0)
        invoice_amount = inv.get("invoice_amount", 0)

        # Normalize customer name
        customer_normalized = self._normalize_customer_name(customer_name)

        # Calculate aging
        days_outstanding = self._calculate_days_outstanding(invoice_date, as_of_date)

        # Determine bucket
        aging_bucket = self._get_aging_bucket(days_outstanding)

        # Flag collection risks
        risk_flags = self._assess_invoice_risk(
            inv, days_outstanding, open_balance, invoice_amount
        )

        # Extract payment terms
        payment_terms = inv.get("payment_terms", "NET30")
        terms_days = self._parse_terms(payment_terms)

        return {
            "invoice_number": invoice_number,
            "customer_name_raw": customer_name,
            "customer_name_normalized": customer_normalized,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "invoice_amount": invoice_amount,
            "open_balance": open_balance,
            "paid_amount": invoice_amount - open_balance,
            "payment_terms": payment_terms,
            "terms_days": terms_days,
            "days_outstanding": days_outstanding,
            "aging_bucket": aging_bucket,
            "as_of_date": as_of_date,
            "reference_po": inv.get("po_number", ""),
            "reference_contract": inv.get("contract_number", ""),
            "risk_flags": risk_flags,
            "is_partially_paid": inv.get("open_balance", 0) > 0
            and inv.get("open_balance", 0) < inv.get("invoice_amount", 0),
            "confidence_score": 0.95,
        }

    def _normalize_customer_name(self, name: str) -> str:
        """Normalize customer name."""
        if not name:
            return ""

        name = name.upper().strip()
        # Remove common suffixes
        name = re.sub(r"\s+(INC|LLC|LTD|CO|CORP|COMPANY)\s*$", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    def _calculate_days_outstanding(self, invoice_date: str, as_of_date: str) -> int:
        """Calculate days since invoice date."""
        try:
            inv_dt = datetime.strptime(invoice_date, "%Y-%m-%d")
            as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
            return (as_of_dt - inv_dt).days
        except:
            return 0

    def _get_aging_bucket(self, days: int) -> str:
        """Get aging bucket classification."""
        if days <= 30:
            return "CURRENT"
        elif days <= 60:
            return "31-60_DAYS"
        elif days <= 90:
            return "61-90_DAYS"
        else:
            return "90PLUS_DAYS"

    def _parse_terms(self, terms: str) -> int:
        """Parse payment terms into days."""
        if not terms:
            return 30

        terms_upper = terms.upper()

        # Common patterns: NET30, NET60, COD, 2/10 NET30, etc.
        match = re.search(r"NET(\d+)", terms_upper)
        if match:
            return int(match.group(1))

        if "COD" in terms_upper:
            return 0

        # Default
        return 30

    def _assess_invoice_risk(
        self, inv: dict, days_outstanding: int, open_balance: float, invoice_amount: float
    ) -> List[str]:
        """Assess invoice-level collection risks."""
        flags = []

        # PAST_DUE
        if days_outstanding > 30:
            flags.append("PAST_DUE")

        # SIGNIFICANTLY_OVERDUE
        if days_outstanding > 90:
            flags.append("SIGNIFICANTLY_OVERDUE")

        # PARTIAL_PAYMENT
        if open_balance > 0 and open_balance < invoice_amount:
            flags.append("PARTIAL_PAYMENT")

        # INVOICE_DISPUTE (if dispute_flag in data)
        if inv.get("dispute_flag", False):
            flags.append("INVOICE_DISPUTE")

        # CREDIT_HOLD (if customer on credit hold)
        if inv.get("customer_credit_hold", False):
            flags.append("CREDIT_HOLD")

        return flags

    def _calculate_aging(self, invoices: List[Dict], as_of_date: str) -> Dict[str, float]:
        """Calculate aging summary by bucket."""
        aging = {"CURRENT": 0, "31-60_DAYS": 0, "61-90_DAYS": 0, "90PLUS_DAYS": 0}

        for inv in invoices:
            bucket = inv.get("aging_bucket", "CURRENT")
            aging[bucket] = aging.get(bucket, 0) + inv.get("open_balance", 0)

        return aging

    def _assess_credit_risk(self, invoices: List[Dict]) -> Dict[str, Any]:
        """Assess overall AR portfolio risk."""
        high_risk_count = sum(
            1
            for inv in invoices
            if any(flag in inv.get("risk_flags", []) for flag in ["SIGNIFICANTLY_OVERDUE"])
        )
        disputed_count = sum(
            1 for inv in invoices if "INVOICE_DISPUTE" in inv.get("risk_flags", [])
        )
        on_hold_count = sum(
            1 for inv in invoices if "CREDIT_HOLD" in inv.get("risk_flags", [])
        )

        return {
            "high_risk_invoices": high_risk_count,
            "disputed_invoices": disputed_count,
            "on_credit_hold": on_hold_count,
            "overall_risk_level": "HIGH" if high_risk_count > 0 else "MEDIUM" if disputed_count > 0 else "LOW",
        }
