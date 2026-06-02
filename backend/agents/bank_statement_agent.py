"""
Bank Statement Intelligence Agent

Parses and normalizes raw bank statement transactions for downstream matching.
Extracts remittance data, normalizes payer names, and flags anomalies.
"""

import json
import re
from typing import Any, Optional
from datetime import datetime, timedelta

PROMPT = """You are the Bank Statement Intelligence Agent in a Cash Application swarm.

Your role: Parse and normalize raw bank statement transactions for downstream matching.

For each transaction extract and flag ALL of the following:

NORMALIZATION:
- Normalize payer name: strip noise words (AP DEPT, CORP, LLC suffix variations), expand abbreviations
- SWIFT 35-char truncation: if payer name ends abruptly or looks abbreviated, flag SWIFT_NAME_TRUNCATION
- Parse remittance text for: invoice numbers (INV-xxxx), PO numbers (PO-xxxx), legacy refs (LEGACY-xxxx),
  contract numbers, check numbers, credit memo refs (CM-xxxx)

ANOMALY FLAGS (add all that apply):
  MISSING_REMITTANCE    - remittance_text is blank or contains no actionable reference
  POSSIBLE_DUPLICATE    - same payer + amount already seen within 30 days in this statement
  NSF_RETURN            - negative amount or "R01/R02" return codes in payer/remittance
  FX_PAYMENT            - currency != USD or "EUR/GBP/CHF" appears in remittance
  SWIFT_NAME_TRUNCATION - payer name appears cut off (likely 35-char SWIFT field limit)
  POST_DATED_CHECK      - check payment_type and check date in future vs statement date
  STALE_CHECK           - check payment_type and check date >180 days before statement date
  THIRD_PARTY_PAYER     - payer name does not match any known customer; remittance names a different company
  PARENT_ENTITY_PAYMENT - payer name contains "HOLDINGS", "GROUP", "GLOBAL" and references a known subsidiary
  EDI_REMITTANCE_PENDING - no remittance but amount is large and round (likely EDI 820 arriving separately)
  PREPAYMENT            - remittance mentions "advance", "deposit", "Q[1-4]", "prepay", no invoice ref
  INTERCOMPANY_NET      - remittance mentions "net", "interco", "netting", "AR/AP"
  COMPLIANCE_HOLD       - payer name contains "FZE", "FZCO", "LLC UAE", "Trading" with Gulf/sanctioned region markers
  WRONG_LEGAL_ENTITY    - transaction routed to subsidiary instead of parent

OUTPUT SCHEMA for each transaction:
{
  "bank_transaction_id": "unique id",
  "statement_date": "YYYY-MM-DD",
  "transaction_date": "YYYY-MM-DD",
  "amount": 1234.56,
  "currency": "USD",
  "payer_name_raw": "original name",
  "payer_name_normalized": "cleaned up name",
  "remittance_text_raw": "original remittance",
  "remittance_text_normalized": "cleaned remittance",
  "payment_type": "WIRE|ACH|CHECK|OTHER",
  "check_number": "optional check number",
  "reference_numbers": ["INV-1234", "PO-5678"],
  "anomaly_flags": ["MISSING_REMITTANCE", "SWIFT_NAME_TRUNCATION"],
  "confidence_score": 0.95,
  "notes": "human-readable explanation"
}

IMPORTANT:
- Never invent data; mark uncertainty in confidence_score
- Flag ambiguities for human review
- Normalize aggressively but preserve original for audit trail
"""


class BankStatementAgent:
    """
    Parses bank statements and normalizes transactions.
    """

    def __init__(self, client, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self.seen_transactions = {}  # For duplicate detection

    async def process_bank_statement(self, statement_data: dict) -> dict:
        """
        Process raw bank statement and return normalized transactions with flags.

        Args:
            statement_data: dict with 'statement_date' and 'transactions' list

        Returns:
            dict with 'status', 'statement_date', 'normalized_transactions', 'anomaly_summary'
        """

        statement_date = statement_data.get("statement_date", "")
        transactions = statement_data.get("transactions", [])

        normalized_transactions = []

        # If USE_FIXTURES, apply local parsing logic
        for txn in transactions:
            normalized = self._normalize_transaction(txn, statement_date)
            normalized_transactions.append(normalized)

        return {
            "status": "completed",
            "statement_date": statement_date,
            "normalized_transactions": normalized_transactions,
            "transaction_count": len(normalized_transactions),
            "anomaly_count": sum(
                len(txn.get("anomaly_flags", [])) for txn in normalized_transactions
            ),
        }

    def _normalize_transaction(self, txn: dict, statement_date: str) -> dict:
        """
        Normalize a single transaction.
        """
        payer_raw = txn.get("payer_name", "").strip()
        remittance_raw = txn.get("remittance_text", "").strip()
        amount = txn.get("amount", 0)
        payment_type = txn.get("payment_type", "OTHER").upper()
        check_number = txn.get("check_number", "")
        transaction_date = txn.get("transaction_date", statement_date)

        # Normalize payer name
        payer_normalized = self._normalize_payer_name(payer_raw)

        # Parse remittance for references
        reference_numbers = self._extract_references(remittance_raw)

        # Detect anomalies
        anomaly_flags = self._detect_anomalies(
            payer_raw,
            payer_normalized,
            remittance_raw,
            amount,
            payment_type,
            transaction_date,
            statement_date,
        )

        return {
            "bank_transaction_id": txn.get("id", ""),
            "statement_date": statement_date,
            "transaction_date": transaction_date,
            "amount": amount,
            "currency": txn.get("currency", "USD"),
            "payer_name_raw": payer_raw,
            "payer_name_normalized": payer_normalized,
            "remittance_text_raw": remittance_raw,
            "remittance_text_normalized": remittance_raw.lower(),
            "payment_type": payment_type,
            "check_number": check_number or None,
            "reference_numbers": reference_numbers,
            "anomaly_flags": anomaly_flags,
            "confidence_score": 0.92 if anomaly_flags else 0.98,
            "notes": self._generate_notes(anomaly_flags, reference_numbers),
        }

    def _normalize_payer_name(self, name: str) -> str:
        """Strip noise words and normalize."""
        if not name:
            return ""

        name = name.upper().strip()
        # Remove common suffixes
        name = re.sub(r"\s+(AP|DEPT|CORP|LLC|INC|LTD|CO|COMPANY)\s*$", "", name)
        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name)
        return name

    def _extract_references(self, remittance: str) -> list:
        """Extract invoice, PO, check, and other reference numbers."""
        references = []
        if not remittance:
            return references

        remittance_upper = remittance.upper()

        # Invoice numbers
        inv_matches = re.findall(r"INV[:\s]?(\d+)", remittance_upper)
        references.extend([f"INV-{m}" for m in inv_matches])

        # PO numbers
        po_matches = re.findall(r"PO[:\s]?(\d+)", remittance_upper)
        references.extend([f"PO-{m}" for m in po_matches])

        # Legacy references
        legacy_matches = re.findall(r"LEGACY[:\s]?(\w+)", remittance_upper)
        references.extend([f"LEGACY-{m}" for m in legacy_matches])

        # Credit memo
        cm_matches = re.findall(r"CM[:\s]?(\d+)", remittance_upper)
        references.extend([f"CM-{m}" for m in cm_matches])

        return list(set(references))  # Deduplicate

    def _detect_anomalies(
        self,
        payer_raw: str,
        payer_normalized: str,
        remittance_raw: str,
        amount: float,
        payment_type: str,
        transaction_date: str,
        statement_date: str,
    ) -> list:
        """Detect anomaly flags."""
        flags = []

        # MISSING_REMITTANCE
        if not remittance_raw or len(remittance_raw.strip()) < 3:
            flags.append("MISSING_REMITTANCE")

        # NSF_RETURN
        if amount < 0 or "R01" in remittance_raw or "R02" in remittance_raw:
            flags.append("NSF_RETURN")

        # FX_PAYMENT
        if "EUR" in remittance_raw or "GBP" in remittance_raw or "CHF" in remittance_raw:
            flags.append("FX_PAYMENT")

        # SWIFT_NAME_TRUNCATION
        if len(payer_raw) >= 35 or (payer_raw and payer_raw[-1] in [".", " "]):
            flags.append("SWIFT_NAME_TRUNCATION")

        # POST_DATED_CHECK or STALE_CHECK
        if payment_type == "CHECK":
            try:
                txn_dt = datetime.strptime(transaction_date, "%Y-%m-%d")
                stmt_dt = datetime.strptime(statement_date, "%Y-%m-%d")
                if txn_dt > stmt_dt:
                    flags.append("POST_DATED_CHECK")
                elif (stmt_dt - txn_dt).days > 180:
                    flags.append("STALE_CHECK")
            except:
                pass

        # PREPAYMENT
        if any(
            word in remittance_raw.lower()
            for word in ["advance", "deposit", "q1", "q2", "q3", "q4", "prepay"]
        ):
            flags.append("PREPAYMENT")

        # INTERCOMPANY_NET
        if any(
            word in remittance_raw.lower()
            for word in ["net", "interco", "netting", "ar/ap"]
        ):
            flags.append("INTERCOMPANY_NET")

        # COMPLIANCE_HOLD
        if any(
            word in payer_raw.upper()
            for word in ["FZE", "FZCO", "UAE", "TRADING"]
        ):
            flags.append("COMPLIANCE_HOLD")

        return flags

    def _generate_notes(self, anomaly_flags: list, reference_numbers: list) -> str:
        """Generate human-readable notes."""
        notes = []

        if not reference_numbers:
            notes.append("No invoice/PO references detected")
        else:
            notes.append(f"References: {', '.join(reference_numbers)}")

        if anomaly_flags:
            notes.append(f"Flags: {len(anomaly_flags)} anomalies detected")

        return "; ".join(notes) if notes else "Clean transaction"
