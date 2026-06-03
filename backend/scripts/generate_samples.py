#!/usr/bin/env python3
"""
Generate 10 focused sample datasets for Cash Application Foundry.
Each sample targets specific financial edge cases.
Run from repo root: python backend/scripts/generate_samples.py
"""

import json
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"

BASE_CONFIG = {
    "auto_writeoff_config": {
        "threshold": 25.00,
        "gl_account": "6020",
        "gl_description": "Bank Charges and Fees",
        "auto_approve": True,
        "max_per_transaction": 25.00
    }
}

def write_sample(n: int, label: str, bank: dict, ar: dict):
    d = SAMPLES_DIR / f"sample_{n:02d}"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "bank_statement.json", "w") as f:
        json.dump(bank, f, indent=2)
    with open(d / "open_ar.json", "w") as f:
        json.dump(ar, f, indent=2)
    meta = {"sample_id": f"{n:02d}", "label": label,
            "transactions": len(bank["transactions"]), "invoices": len(ar["invoices"])}
    with open(d / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Sample {n:02d} ({label}): {len(bank['transactions'])} txns, {len(ar['invoices'])} invoices")


# ─────────────────────────────────────────────────────────────
# SAMPLE 01: Clean Batch - All exact or near-exact matches
# ─────────────────────────────────────────────────────────────
write_sample(1, "Clean Batch - Exact and Near-Exact Matches",
bank={
    "statement_date": "2024-07-31",
    "bank": "Bank of America",
    "account": "****1234",
    "company": "Meridian Tech Solutions Inc.",
    "transactions": [
        {"txn_id":"TXN-01-001","date":"2024-07-05","amount":18500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"BRIGHTWAY SYSTEMS INC","bank_reference":"ACH20240705001",
         "remittance_text":"INV-01-001","note":"Exact match: correct amount, correct invoice reference"},
        {"txn_id":"TXN-01-002","date":"2024-07-08","amount":42000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"CASCADE INDUSTRIAL LLC","bank_reference":"WIRE20240708001",
         "remittance_text":"INV-01-002 INV-01-003","note":"Multi-invoice: $18,000 + $24,000 = $42,000 exact"},
        {"txn_id":"TXN-01-003","date":"2024-07-10","amount":31850.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"DELTA COMPONENTS CORP","bank_reference":"ACH20240710003",
         "remittance_text":"INV-01-004 2% early pay discount taken",
         "note":"Early pay discount: $32,500 * 0.98 = $31,850. Paid day 7, within 10-day window"},
        {"txn_id":"TXN-01-004","date":"2024-07-12","amount":9975.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"EASTERN SUPPLY GROUP","bank_reference":"WIRE20240712004",
         "remittance_text":"INV-01-005","note":"Bank wire fee: invoice $10,000, paid $9,975, delta $25 = auto write-off"},
        {"txn_id":"TXN-01-005","date":"2024-07-15","amount":55000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"FRONTIER LOGISTICS INC","bank_reference":"WIRE20240715005",
         "remittance_text":"","note":"No remittance: FIFO match to oldest open invoice for this customer"},
        {"txn_id":"TXN-01-006","date":"2024-07-18","amount":27300.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"GRANITE PRODUCTS CO","bank_reference":"ACH20240718006",
         "remittance_text":"PO-9901","note":"PO reference: customer pays by PO number, not invoice number"},
        {"txn_id":"TXN-01-007","date":"2024-07-22","amount":13400.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"HARBOR TECH SOLUTIONS","bank_reference":"ACH20240722007",
         "remittance_text":"INV-01-008 installment 2 of 3","note":"Installment: $40,200 / 3 = $13,400 each. First already applied."},
        {"txn_id":"TXN-01-008","date":"2024-07-25","amount":8750.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"INLAND DISTRIBUTORS LLC","bank_reference":"ACH20240725008",
         "remittance_text":"INV-01-009","note":"Exact match: small amount, clean payment"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Meridian Tech Solutions Inc.",
    "invoices":[
        {"invoice_id":"INV-01-001","customer_id":"CUST-01-001","customer_name":"Brightway Systems Inc.",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":18500.00,"open_amount":18500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Matches TXN-01-001"},
        {"invoice_id":"INV-01-002","customer_id":"CUST-01-002","customer_name":"Cascade Industrial LLC",
         "invoice_date":"2024-06-25","due_date":"2024-07-25","original_amount":18000.00,"open_amount":18000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":36,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Multi-bundle part 1"},
        {"invoice_id":"INV-01-003","customer_id":"CUST-01-002","customer_name":"Cascade Industrial LLC",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":24000.00,"open_amount":24000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Multi-bundle part 2"},
        {"invoice_id":"INV-01-004","customer_id":"CUST-01-003","customer_name":"Delta Components Corp",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":32500.00,"open_amount":32500.00,
         "currency":"USD","po_reference":None,"payment_terms":"2/10 NET 30","discount_pct":2.0,"discount_deadline":"2024-07-13",
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"2% discount if paid by 2024-07-13"},
        {"invoice_id":"INV-01-005","customer_id":"CUST-01-004","customer_name":"Eastern Supply Group",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":10000.00,"open_amount":10000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Delta $25 = bank wire fee auto write-off"},
        {"invoice_id":"INV-01-006","customer_id":"CUST-01-005","customer_name":"Frontier Logistics Inc.",
         "invoice_date":"2024-06-20","due_date":"2024-07-20","original_amount":55000.00,"open_amount":55000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":41,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Oldest open invoice. FIFO for TXN-01-005"},
        {"invoice_id":"INV-01-007","customer_id":"CUST-01-006","customer_name":"Granite Products Co.",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":27300.00,"open_amount":27300.00,
         "currency":"USD","po_reference":"PO-9901","payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"PO-9901 matches TXN-01-006 remittance"},
        {"invoice_id":"INV-01-008","customer_id":"CUST-01-007","customer_name":"Harbor Tech Solutions",
         "invoice_date":"2024-05-15","due_date":"2024-08-15","original_amount":40200.00,"open_amount":26800.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 90","discount_pct":0,"discount_deadline":None,
         "aging_days":77,"aging_bucket":"61-90","status":"PARTIAL","dispute_reason":None,"existing_credit_memo":0,"note":"Installment agreement. 1st of 3 already paid. Open = $26,800"},
        {"invoice_id":"INV-01-009","customer_id":"CUST-01-008","customer_name":"Inland Distributors LLC",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":8750.00,"open_amount":8750.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-01-008"}
    ],
    "credit_memos":[],"payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 02: Deductions Heavy - Freight, Damage, Promos
# ─────────────────────────────────────────────────────────────
write_sample(2, "Deductions Heavy - Freight, Damage, Unauthorized",
bank={
    "statement_date":"2024-07-31","bank":"Wells Fargo","account":"****5678",
    "company":"Retail Direct Group LLC",
    "transactions":[
        {"txn_id":"TXN-02-001","date":"2024-07-03","amount":39200.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"NORTHGATE RETAIL INC","bank_reference":"ACH20240703001",
         "remittance_text":"INV-02-001 2% early pay","note":"Valid early pay: $40,000 * 0.98 = $39,200. Paid day 9 within 10-day window"},
        {"txn_id":"TXN-02-002","date":"2024-07-05","amount":47500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"SUMMIT RETAIL CORP","bank_reference":"WIRE20240705002",
         "remittance_text":"INV-02-002 less freight $2,500","note":"Freight deduction: $50,000 invoice less $2,500 freight allowance per distribution agreement"},
        {"txn_id":"TXN-02-003","date":"2024-07-08","amount":28750.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"VALLEY STORES LLC","bank_reference":"ACH20240708003",
         "remittance_text":"INV-02-003 damage claim deduction $1,250","note":"Damage claim: customer deducting $1,250 for goods damaged in transit. Claim filed 2024-06-28"},
        {"txn_id":"TXN-02-004","date":"2024-07-10","amount":62000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"COASTAL CHAIN STORES","bank_reference":"WIRE20240710004",
         "remittance_text":"INV-02-004 Q2 trade promo allowance $3,000","note":"Trade promo deduction: $3,000 promotional allowance per Q2 trade deal signed 2024-05-01"},
        {"txn_id":"TXN-02-005","date":"2024-07-12","amount":33500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"MIDWEST GROCERS CO","bank_reference":"ACH20240712005",
         "remittance_text":"INV-02-005","note":"Unauthorized deduction: $35,000 invoice, paid $33,500. No discount terms. $1,500 unexplained deduction"},
        {"txn_id":"TXN-02-006","date":"2024-07-15","amount":19800.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"EASTERN MART GROUP","bank_reference":"ACH20240715006",
         "remittance_text":"INV-02-006 short ship deduction 200 units","note":"Short ship: customer deducting for 200 undelivered units at $10 each = $2,000 deduction from $21,800 invoice"},
        {"txn_id":"TXN-02-007","date":"2024-07-18","amount":25840.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"PACIFIC SUPERSTORE INC","bank_reference":"ACH20240718007",
         "remittance_text":"INV-02-007 2% discount","note":"Late discount: $26,000 * 0.98 = $25,480. But discount deadline was 2024-07-10 and payment is 2024-07-18. UNAUTHORIZED."},
        {"txn_id":"TXN-02-008","date":"2024-07-22","amount":44000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"HIGHLAND RETAIL INC","bank_reference":"WIRE20240722008",
         "remittance_text":"INV-02-008 pricing dispute line 3","note":"Pricing dispute: customer claims line item 3 was billed at $12/unit, contract says $10/unit. Disputing $2,000"},
        {"txn_id":"TXN-02-009","date":"2024-07-25","amount":15000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"SUNRISE DISTRIBUTORS","bank_reference":"ACH20240725009",
         "remittance_text":"INV-02-009","note":"Exact match: clean payment, no deductions"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Retail Direct Group LLC",
    "invoices":[
        {"invoice_id":"INV-02-001","customer_id":"CUST-02-001","customer_name":"Northgate Retail Inc.",
         "invoice_date":"2024-06-24","due_date":"2024-07-24","original_amount":40000.00,"open_amount":40000.00,
         "currency":"USD","po_reference":"PO-4401","payment_terms":"2/10 NET 30","discount_pct":2.0,"discount_deadline":"2024-07-04",
         "aging_days":37,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"2% discount if paid by 2024-07-04"},
        {"invoice_id":"INV-02-002","customer_id":"CUST-02-002","customer_name":"Summit Retail Corp",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":50000.00,"open_amount":50000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Freight allowance $2,500 per distribution agreement"},
        {"invoice_id":"INV-02-003","customer_id":"CUST-02-003","customer_name":"Valley Stores LLC",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":30000.00,"open_amount":30000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Damage claim filed 2024-06-28 for $1,250"},
        {"invoice_id":"INV-02-004","customer_id":"CUST-02-004","customer_name":"Coastal Chain Stores",
         "invoice_date":"2024-07-02","due_date":"2024-08-01","original_amount":65000.00,"open_amount":65000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":29,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Q2 trade promo $3,000 per signed deal 2024-05-01"},
        {"invoice_id":"INV-02-005","customer_id":"CUST-02-005","customer_name":"Midwest Grocers Co.",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":35000.00,"open_amount":35000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"No discount terms. Unauthorized $1,500 deduction"},
        {"invoice_id":"INV-02-006","customer_id":"CUST-02-006","customer_name":"Eastern Mart Group",
         "invoice_date":"2024-07-06","due_date":"2024-08-05","original_amount":21800.00,"open_amount":21800.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":25,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Short ship: 200 units at $10 = $2,000 deduction"},
        {"invoice_id":"INV-02-007","customer_id":"CUST-02-007","customer_name":"Pacific Superstore Inc.",
         "invoice_date":"2024-06-30","due_date":"2024-07-30","original_amount":26000.00,"open_amount":26000.00,
         "currency":"USD","po_reference":None,"payment_terms":"2/10 NET 30","discount_pct":2.0,"discount_deadline":"2024-07-10",
         "aging_days":31,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Discount deadline was 2024-07-10. Payment on 2024-07-18 = LATE DISCOUNT"},
        {"invoice_id":"INV-02-008","customer_id":"CUST-02-008","customer_name":"Highland Retail Inc.",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":46000.00,"open_amount":46000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Pricing dispute: line 3 rate $12 vs contract $10"},
        {"invoice_id":"INV-02-009","customer_id":"CUST-02-009","customer_name":"Sunrise Distributors",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":15000.00,"open_amount":15000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Clean exact match"}
    ],
    "credit_memos":[],"payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 03: Compliance and Legal Risk
# ─────────────────────────────────────────────────────────────
write_sample(3, "Compliance and Legal Risk - OFAC, Disputes, Wrong Entity",
bank={
    "statement_date":"2024-07-31","bank":"Citibank","account":"****9012",
    "company":"Global Imports Corp",
    "transactions":[
        {"txn_id":"TXN-03-001","date":"2024-07-07","amount":125000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"ZARKON TRADING FZE","bank_reference":"WIRE20240707001",
         "remittance_text":"INV-03-001","note":"COMPLIANCE HOLD: Payer name matches OFAC SDN watchlist. DO NOT POST. Escalate to Compliance Officer immediately."},
        {"txn_id":"TXN-03-002","date":"2024-07-09","amount":48000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"REDSTONE MATERIALS LLC","bank_reference":"ACH20240709002",
         "remittance_text":"INV-03-002","note":"DISPUTED INVOICE: INV-03-002 is under active dispute filed 2024-06-15. Do not auto-post. Route to Credit Manager."},
        {"txn_id":"TXN-03-003","date":"2024-07-11","amount":72000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"BLUEROCK ENTERPRISES INC","bank_reference":"WIRE20240711003",
         "remittance_text":"INV-03-003 Global Imports North","note":"WRONG ENTITY: Remittance references Global Imports North LLC (separate legal entity). Payment cannot be posted here. Return to sender or redirect."},
        {"txn_id":"TXN-03-004","date":"2024-07-14","amount":33500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"IRONCLAD SUPPLY CO","bank_reference":"ACH20240714004",
         "remittance_text":"INV-03-004","note":"LEGAL HOLD: INV-03-004 is under court freeze pending litigation. Hold payment in suspense GL 2099."},
        {"txn_id":"TXN-03-005","date":"2024-07-16","amount":22000.00,"currency":"USD",
         "payment_type":"ACH_RETURN","payer_raw":"NSF RETURN - MERIDIAN SUPPLY","bank_reference":"RETURN20240716005",
         "remittance_text":"Return of ACH20240620001 - NSF","note":"NSF RETURN: Prior ACH of $22,000 on 2024-06-20 for INV-03-005 bounced. Reverse prior application, reopen invoice, notify customer."},
        {"txn_id":"TXN-03-006","date":"2024-07-22","amount":29750.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"CLEARBROOK SOLUTIONS","bank_reference":"ACH20240722006",
         "remittance_text":"INV-03-006","note":"Clean payment: exact match, no issues"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Global Imports Corp",
    "invoices":[
        {"invoice_id":"INV-03-001","customer_id":"CUST-03-001","customer_name":"Zarkon Trading FZE",
         "invoice_date":"2024-06-15","due_date":"2024-07-15","original_amount":125000.00,"open_amount":125000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":46,"aging_bucket":"31-60","status":"ON_HOLD","dispute_reason":"OFAC screening - do not post pending compliance review",
         "existing_credit_memo":0,"note":"COMPLIANCE_HOLD flag. Matches TXN-03-001"},
        {"invoice_id":"INV-03-002","customer_id":"CUST-03-002","customer_name":"Redstone Materials LLC",
         "invoice_date":"2024-06-20","due_date":"2024-07-20","original_amount":48000.00,"open_amount":48000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":41,"aging_bucket":"31-60","status":"DISPUTED",
         "dispute_reason":"Customer claims short delivery of 40 units. Dispute filed 2024-06-15.",
         "existing_credit_memo":0,"note":"do_not_auto_apply = true. Matches TXN-03-002"},
        {"invoice_id":"INV-03-003","customer_id":"CUST-03-003","customer_name":"Bluerock Enterprises Inc.",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":72000.00,"open_amount":72000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,
         "existing_credit_memo":0,"note":"Invoice is for Global Imports Corp. Payment remittance says Global Imports North LLC (different entity)"},
        {"invoice_id":"INV-03-004","customer_id":"CUST-03-004","customer_name":"Ironclad Supply Co.",
         "invoice_date":"2024-06-28","due_date":"2024-07-28","original_amount":33500.00,"open_amount":33500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":33,"aging_bucket":"31-60","status":"LEGAL_HOLD",
         "dispute_reason":"Court freeze order 2024-06-10. Case No. CV-2024-4471.",
         "existing_credit_memo":0,"note":"do_not_auto_apply = true. Hold in suspense GL 2099"},
        {"invoice_id":"INV-03-005","customer_id":"CUST-03-005","customer_name":"Meridian Supply Group",
         "invoice_date":"2024-06-01","due_date":"2024-07-01","original_amount":22000.00,"open_amount":0.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":60,"aging_bucket":"61-90","status":"CLOSED","dispute_reason":None,
         "existing_credit_memo":0,"note":"Was marked closed after ACH20240620001 payment which has now returned NSF. Must be reopened."},
        {"invoice_id":"INV-03-006","customer_id":"CUST-03-006","customer_name":"Clearbrook Solutions",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":29750.00,"open_amount":29750.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,
         "existing_credit_memo":0,"note":"Clean. Matches TXN-03-006"}
    ],
    "credit_memos":[],"payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":["INV-03-002"],"legal_hold_invoice_ids":["INV-03-004"],"do_not_auto_apply_customer_ids":["CUST-03-001","CUST-03-002","CUST-03-004"]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 04: Multi-Entity Relationships
# ─────────────────────────────────────────────────────────────
write_sample(4, "Multi-Entity - Parent/Subsidiary, Factoring, Intercompany",
bank={
    "statement_date":"2024-07-31","bank":"JPMorgan Chase","account":"****3456",
    "company":"Enterprise Holdings Group Inc.",
    "transactions":[
        {"txn_id":"TXN-04-001","date":"2024-07-04","amount":85000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"OMEGA GLOBAL HOLDINGS LLC","bank_reference":"WIRE20240704001",
         "remittance_text":"INV-04-001 payment on behalf of Omega West Division",
         "note":"Parent paying for subsidiary: Omega Global Holdings (CUST-04-P01) paying for Omega West Division (CUST-04-001). Post to subsidiary AR."},
        {"txn_id":"TXN-04-002","date":"2024-07-07","amount":56000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"CAPITAL RECEIVABLES CORP","bank_reference":"WIRE20240707002",
         "remittance_text":"INV-04-002 INV-04-003 - factoring payment","note":"Third-party factoring: Capital Receivables Corp paying on behalf of Lakeview Supplies Inc. Post to customer AR, note factor."},
        {"txn_id":"TXN-04-003","date":"2024-07-10","amount":41200.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"BRIGHTON INDUSTRIES GROUP","bank_reference":"ACH20240710003",
         "remittance_text":"INV-04-004 intercompany net settlement July",
         "note":"Intercompany netting: our AR $68,000 minus our AP $26,800 = net payment $41,200. Requires DR to AR and CR to AP."},
        {"txn_id":"TXN-04-004","date":"2024-07-14","amount":32500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"NEXUS PARENT CORP","bank_reference":"ACH20240714004",
         "remittance_text":"INV-04-005","note":"Parent paying for subsidiary: Nexus Parent Corp (CUST-04-P02) paying for Nexus Midwest LLC (CUST-04-005). Post to subsidiary."},
        {"txn_id":"TXN-04-005","date":"2024-07-17","amount":19800.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"T&R TRADING CO","bank_reference":"ACH20240717005",
         "remittance_text":"INV-04-006","note":"DBA name mismatch: T&R Trading Co is the registered DBA of Thornton and Reed Enterprises (CUST-04-006). Alias resolved."},
        {"txn_id":"TXN-04-006","date":"2024-07-21","amount":47250.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"MOMENTUM GLOBAL INC","bank_reference":"WIRE20240721006",
         "remittance_text":"INV-04-007","note":"Post-acquisition name: Momentum Global Inc. is the former name of Crestview Solutions Corp (CUST-04-007) prior to 2024-03 acquisition."},
        {"txn_id":"TXN-04-007","date":"2024-07-24","amount":28000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"CLEARFIELD TRADING LTD","bank_reference":"ACH20240724007",
         "remittance_text":"INV-04-008","note":"Exact match: clean payment"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Enterprise Holdings Group Inc.",
    "invoices":[
        {"invoice_id":"INV-04-001","customer_id":"CUST-04-001","customer_name":"Omega West Division",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":85000.00,"open_amount":85000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"Parent Omega Global Holdings (CUST-04-P01) will pay on behalf of this subsidiary"},
        {"invoice_id":"INV-04-002","customer_id":"CUST-04-002","customer_name":"Lakeview Supplies Inc.",
         "invoice_date":"2024-06-25","due_date":"2024-07-25","original_amount":31000.00,"open_amount":31000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":36,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Factoring: Capital Receivables Corp pays on behalf of this customer"},
        {"invoice_id":"INV-04-003","customer_id":"CUST-04-002","customer_name":"Lakeview Supplies Inc.",
         "invoice_date":"2024-07-02","due_date":"2024-08-01","original_amount":25000.00,"open_amount":25000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":29,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Part of factoring bundle with INV-04-002"},
        {"invoice_id":"INV-04-004","customer_id":"CUST-04-003","customer_name":"Brighton Industries Group",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":68000.00,"open_amount":68000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"Intercompany net: our AR $68,000, our AP to Brighton $26,800. Net payment = $41,200"},
        {"invoice_id":"INV-04-005","customer_id":"CUST-04-005","customer_name":"Nexus Midwest LLC",
         "invoice_date":"2024-07-07","due_date":"2024-08-06","original_amount":32500.00,"open_amount":32500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":24,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Parent Nexus Parent Corp (CUST-04-P02) will pay on behalf"},
        {"invoice_id":"INV-04-006","customer_id":"CUST-04-006","customer_name":"Thornton and Reed Enterprises",
         "invoice_date":"2024-07-09","due_date":"2024-08-08","original_amount":19800.00,"open_amount":19800.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":22,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"DBA registered as T&R Trading Co"},
        {"invoice_id":"INV-04-007","customer_id":"CUST-04-007","customer_name":"Crestview Solutions Corp",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":47250.00,"open_amount":47250.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Formerly Momentum Global Inc. before 2024-03 acquisition"},
        {"invoice_id":"INV-04-008","customer_id":"CUST-04-008","customer_name":"Clearfield Trading Ltd.",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":28000.00,"open_amount":28000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Clean exact match TXN-04-007"}
    ],
    "credit_memos":[],
    "payer_alias_registry":[
        {"payer_alias":"T&R TRADING CO","canonical_customer_id":"CUST-04-006","canonical_name":"Thornton and Reed Enterprises","match_type":"DBA"},
        {"payer_alias":"MOMENTUM GLOBAL INC","canonical_customer_id":"CUST-04-007","canonical_name":"Crestview Solutions Corp","match_type":"POST_ACQUISITION"},
        {"payer_alias":"CAPITAL RECEIVABLES CORP","canonical_customer_id":"CUST-04-002","canonical_name":"Lakeview Supplies Inc.","match_type":"FACTORING_AGENT"}
    ],
    "parent_child_hierarchy":[
        {"parent_customer_id":"CUST-04-P01","parent_name":"Omega Global Holdings LLC","children":["CUST-04-001"]},
        {"parent_customer_id":"CUST-04-P02","parent_name":"Nexus Parent Corp","children":["CUST-04-005"]}
    ],
    "intercompany_netting":[
        {"customer_id":"CUST-04-003","customer_name":"Brighton Industries Group",
         "our_receivable":68000.00,"our_payable":26800.00,"expected_net_payment":41200.00,"net_agreement_active":True}
    ],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 05: International FX Payments
# ─────────────────────────────────────────────────────────────
write_sample(5, "International FX - EUR, GBP, CAD Payments",
bank={
    "statement_date":"2024-07-31","bank":"HSBC USA","account":"****7890",
    "company":"Atlantic Export Services Inc.",
    "transactions":[
        {"txn_id":"TXN-05-001","date":"2024-07-04","amount":54000.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"BERLIN COMPONENTS GMBH","bank_reference":"SWIFT20240704001",
         "remittance_text":"INV-05-001 EUR 50000 @ 1.08","note":"EUR SWIFT: 50,000 EUR at 1.08 USD/EUR = $54,000 USD. Exact match after FX conversion."},
        {"txn_id":"TXN-05-002","date":"2024-07-07","amount":38145.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"LONDON TRADING CO LTD","bank_reference":"SWIFT20240707002",
         "remittance_text":"INV-05-002 GBP 30000 @ 1.2715","note":"GBP SWIFT: 30,000 GBP at 1.2715 USD/GBP = $38,145 USD. Verify FX rate."},
        {"txn_id":"TXN-05-003","date":"2024-07-09","amount":29600.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"AMSTERDAM SUPPLY BV","bank_reference":"SWIFT20240709003",
         "remittance_text":"INV-05-003 EUR 27500 @ 1.0764","note":"FX RATE MISMATCH: 27,500 EUR converted at 1.0764 = $29,601. Invoice expected $29,700 (based on deal rate 1.08). Delta $100 - FX rate difference."},
        {"txn_id":"TXN-05-004","date":"2024-07-12","amount":22200.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"TORONTO DISTRIBUTORS INC","bank_reference":"ACH20240712004",
         "remittance_text":"INV-05-004 CAD 30000 @ 0.74","note":"CAD ACH: 30,000 CAD at 0.74 USD/CAD = $22,200 USD. Exact match after FX conversion."},
        {"txn_id":"TXN-05-005","date":"2024-07-15","amount":86400.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"MUNICH INDUSTRIAL AG","bank_reference":"SWIFT20240715005",
         "remittance_text":"INV-05-005 INV-05-006 EUR 80000 @ 1.08","note":"EUR multi-invoice: 80,000 EUR at 1.08 = $86,400. Covers two invoices: EUR 45,000 + EUR 35,000."},
        {"txn_id":"TXN-05-006","date":"2024-07-19","amount":25405.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"MANCHESTER GOODS PLC","bank_reference":"SWIFT20240719006",
         "remittance_text":"INV-05-007 GBP 20000 @ 1.2715 less GBP15 bank fee","note":"GBP with bank fee: 20,000 GBP at 1.2715 = $25,430. Less GBP 15 bank fee = $25,411. Actual received $25,405 - delta within auto write-off threshold."},
        {"txn_id":"TXN-05-007","date":"2024-07-23","amount":67500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"CONTINENTAL EXPORTS LLC","bank_reference":"WIRE20240723007",
         "remittance_text":"INV-05-008","note":"USD clean payment from international customer billed in USD"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Atlantic Export Services Inc.",
    "invoices":[
        {"invoice_id":"INV-05-001","customer_id":"CUST-05-001","customer_name":"Berlin Components GmbH",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":54000.00,"open_amount":54000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"Billed in USD equiv. EUR 50,000 @ 1.08. Matches TXN-05-001"},
        {"invoice_id":"INV-05-002","customer_id":"CUST-05-002","customer_name":"London Trading Co Ltd",
         "invoice_date":"2024-07-02","due_date":"2024-08-01","original_amount":38145.00,"open_amount":38145.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":29,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"GBP 30,000 @ 1.2715 = $38,145 USD"},
        {"invoice_id":"INV-05-003","customer_id":"CUST-05-003","customer_name":"Amsterdam Supply BV",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":29700.00,"open_amount":29700.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"Invoice at EUR 27,500 @ deal rate 1.08 = $29,700. Customer used market rate 1.0764 - $100 FX rate difference"},
        {"invoice_id":"INV-05-004","customer_id":"CUST-05-004","customer_name":"Toronto Distributors Inc.",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":22200.00,"open_amount":22200.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"CAD 30,000 @ 0.74 = $22,200 USD"},
        {"invoice_id":"INV-05-005","customer_id":"CUST-05-005","customer_name":"Munich Industrial AG",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":48600.00,"open_amount":48600.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"EUR 45,000 @ 1.08 = $48,600. Part of multi-invoice bundle with INV-05-006"},
        {"invoice_id":"INV-05-006","customer_id":"CUST-05-005","customer_name":"Munich Industrial AG",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":37800.00,"open_amount":37800.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"EUR 35,000 @ 1.08 = $37,800. Part of multi-invoice bundle with INV-05-005"},
        {"invoice_id":"INV-05-007","customer_id":"CUST-05-006","customer_name":"Manchester Goods PLC",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":25430.00,"open_amount":25430.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"GBP 20,000 @ 1.2715 = $25,430. Delta $25 or less = auto write-off"},
        {"invoice_id":"INV-05-008","customer_id":"CUST-05-007","customer_name":"Continental Exports LLC",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":67500.00,"open_amount":67500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"USD invoice. Clean exact match"}
    ],
    "credit_memos":[],"payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 06: Timing and Sequence Issues
# ─────────────────────────────────────────────────────────────
write_sample(6, "Timing Issues - Post-Dated, Stale Check, NSF, Duplicates",
bank={
    "statement_date":"2024-07-31","bank":"US Bank","account":"****2345",
    "company":"Midwest Wholesale Corp",
    "transactions":[
        {"txn_id":"TXN-06-001","date":"2024-08-15","amount":41000.00,"currency":"USD",
         "payment_type":"CHECK","payer_raw":"RIDGELINE MATERIALS INC","bank_reference":"CHECK-004821",
         "remittance_text":"INV-06-001","note":"POST-DATED CHECK: Check date is 2024-08-15, which is after statement date 2024-07-31. Hold file. Re-process on check date."},
        {"txn_id":"TXN-06-002","date":"2024-01-10","amount":18750.00,"currency":"USD",
         "payment_type":"CHECK","payer_raw":"OAKDALE HARDWARE LLC","bank_reference":"CHECK-003317",
         "remittance_text":"INV-06-002","note":"STALE CHECK: Check date 2024-01-10 is 202 days before statement date 2024-07-31 (over 180 days). Cannot negotiate. Return to issuer."},
        {"txn_id":"TXN-06-003","date":"2024-07-02","amount":22000.00,"currency":"USD",
         "payment_type":"ACH_RETURN","payer_raw":"NSF RETURN - PINECREST SUPPLY","bank_reference":"RETURN20240702003",
         "remittance_text":"Return of ACH20240605003 NSF - insufficient funds","note":"NSF RETURN: Prior ACH of $22,000 on 2024-06-05 bounced. Reverse previous application of INV-06-003 and reopen invoice."},
        {"txn_id":"TXN-06-004","date":"2024-07-08","amount":34500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"SUMMIT WHOLESALE INC","bank_reference":"ACH20240708004",
         "remittance_text":"INV-06-004","note":"First occurrence of payment. VALID."},
        {"txn_id":"TXN-06-005","date":"2024-07-15","amount":34500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"SUMMIT WHOLESALE INC","bank_reference":"ACH20240715005",
         "remittance_text":"INV-06-004","note":"DUPLICATE PAYMENT: Same payer Summit Wholesale, same amount $34,500, same invoice INV-06-004, within 30-day window. Hold second occurrence. Notify customer."},
        {"txn_id":"TXN-06-006","date":"2024-07-11","amount":15600.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"VALLEY DISTRIBUTION LLC","bank_reference":"ACH20240711006",
         "remittance_text":"INV-06-005 installment 1 of 4","note":"Installment payment: $62,400 total / 4 installments = $15,600. First installment."},
        {"txn_id":"TXN-06-007","date":"2024-07-19","amount":50000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"CENTRAL COMMERCE GROUP","bank_reference":"WIRE20240719007",
         "remittance_text":"PREPAYMENT order PO-7751 expected August","note":"PREPAYMENT ADVANCE: No invoice exists. Customer paying ahead of order PO-7751. Post to GL 2050 Unearned Revenue."},
        {"txn_id":"TXN-06-008","date":"2024-07-24","amount":29000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"NORTHERN PARTS CO","bank_reference":"ACH20240724008",
         "remittance_text":"INV-06-006","note":"Clean exact match payment"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Midwest Wholesale Corp",
    "invoices":[
        {"invoice_id":"INV-06-001","customer_id":"CUST-06-001","customer_name":"Ridgeline Materials Inc.",
         "invoice_date":"2024-07-15","due_date":"2024-08-14","original_amount":41000.00,"open_amount":41000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":16,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Post-dated check received. Hold until 2024-08-15."},
        {"invoice_id":"INV-06-002","customer_id":"CUST-06-002","customer_name":"Oakdale Hardware LLC",
         "invoice_date":"2023-12-15","due_date":"2024-01-14","original_amount":18750.00,"open_amount":18750.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":198,"aging_bucket":"90+","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Stale check (>180 days). Cannot negotiate."},
        {"invoice_id":"INV-06-003","customer_id":"CUST-06-003","customer_name":"Pinecrest Supply Corp",
         "invoice_date":"2024-05-15","due_date":"2024-06-14","original_amount":22000.00,"open_amount":0.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":77,"aging_bucket":"61-90","status":"CLOSED","dispute_reason":None,"existing_credit_memo":0,"note":"Was closed - prior ACH bounced NSF. Must be reopened to $22,000."},
        {"invoice_id":"INV-06-004","customer_id":"CUST-06-004","customer_name":"Summit Wholesale Inc.",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":34500.00,"open_amount":34500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Two payments received for same invoice. First (TXN-06-004) valid. Second (TXN-06-005) is duplicate - hold."},
        {"invoice_id":"INV-06-005","customer_id":"CUST-06-005","customer_name":"Valley Distribution LLC",
         "invoice_date":"2024-05-01","due_date":"2024-07-30","original_amount":62400.00,"open_amount":62400.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 90","discount_pct":0,"discount_deadline":None,
         "aging_days":91,"aging_bucket":"90+","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Installment agreement: 4 x $15,600"},
        {"invoice_id":"INV-06-006","customer_id":"CUST-06-006","customer_name":"Northern Parts Co.",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":29000.00,"open_amount":29000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Clean exact match TXN-06-008"}
    ],
    "credit_memos":[],"payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 07: Remittance Problems
# ─────────────────────────────────────────────────────────────
write_sample(7, "Remittance Problems - Missing, Vague, Legacy, EDI",
bank={
    "statement_date":"2024-07-31","bank":"PNC Bank","account":"****6789",
    "company":"Summit Distribution LLC",
    "transactions":[
        {"txn_id":"TXN-07-001","date":"2024-07-03","amount":23500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"GREENFIELD PARTS INC","bank_reference":"WIRE20240703001",
         "remittance_text":"","note":"NO REMITTANCE: Empty reference. Match by customer name + FIFO to oldest open invoice."},
        {"txn_id":"TXN-07-002","date":"2024-07-06","amount":41000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"LAKEWOOD SUPPLY CO","bank_reference":"ACH20240706002",
         "remittance_text":"June invoices","note":"VAGUE REMITTANCE: 'June invoices' has no specific invoice numbers. Match by amount to open June invoices."},
        {"txn_id":"TXN-07-003","date":"2024-07-09","amount":28750.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"IRONBRIDGE ENTERPRISES","bank_reference":"WIRE20240709003",
         "remittance_text":"LEGACY-INV-2024-0087","note":"LEGACY INVOICE REF: Customer used old ERP invoice number LEGACY-INV-2024-0087. Cross-reference to current INV-07-003."},
        {"txn_id":"TXN-07-004","date":"2024-07-12","amount":55000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"COASTAL TRADE CORP","bank_reference":"ACH20240712004",
         "remittance_text":"EDI 820 pending","note":"EDI PENDING: Customer sends EDI 820 remittance file separately. Do not FIFO match. Hold for EDI file expected within 2 business days."},
        {"txn_id":"TXN-07-005","date":"2024-07-15","amount":19200.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"HILLSIDE PRODUCTS LLC","bank_reference":"ACH20240715005",
         "remittance_text":"PO-5533 PO-5541","note":"PO REFERENCE: Customer pays by PO numbers. Match to invoices with po_reference PO-5533 and PO-5541."},
        {"txn_id":"TXN-07-006","date":"2024-07-18","amount":38400.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"MERIDIAN HARDWARE GROUP","bank_reference":"WIRE20240718006",
         "remittance_text":"See attached remittance advice","note":"VAGUE: 'See attached' with no specifics. Amount-based match to open invoices for this customer."},
        {"txn_id":"TXN-07-007","date":"2024-07-21","amount":31500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"PINNACLE SUPPLY INC","bank_reference":"ACH20240721007",
         "remittance_text":"Old ref: SAP-2024-112-A","note":"OLD ERP REF: Customer using SAP legacy numbering. Cross-reference via legacy map to INV-07-007."},
        {"txn_id":"TXN-07-008","date":"2024-07-25","amount":44500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"TRIDENT MATERIALS CORP","bank_reference":"WIRE20240725008",
         "remittance_text":"INV-07-008","note":"Clean exact match: invoice number provided, exact amount"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Summit Distribution LLC",
    "invoices":[
        {"invoice_id":"INV-07-001","customer_id":"CUST-07-001","customer_name":"Greenfield Parts Inc.",
         "invoice_date":"2024-06-18","due_date":"2024-07-18","original_amount":23500.00,"open_amount":23500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":43,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Oldest open invoice for customer. FIFO target for TXN-07-001"},
        {"invoice_id":"INV-07-002","customer_id":"CUST-07-002","customer_name":"Lakewood Supply Co.",
         "invoice_date":"2024-06-20","due_date":"2024-07-20","original_amount":41000.00,"open_amount":41000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":41,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"June invoice. Amount matches TXN-07-002 vague remittance."},
        {"invoice_id":"INV-07-003","customer_id":"CUST-07-003","customer_name":"Ironbridge Enterprises",
         "invoice_date":"2024-07-02","due_date":"2024-08-01","original_amount":28750.00,"open_amount":28750.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":29,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"Current invoice. Legacy ID = LEGACY-INV-2024-0087. TXN-07-003 uses old ref."},
        {"invoice_id":"INV-07-004","customer_id":"CUST-07-004","customer_name":"Coastal Trade Corp",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":55000.00,"open_amount":55000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"ON_HOLD","dispute_reason":"EDI 820 remittance pending",
         "existing_credit_memo":0,"note":"EDI_REMITTANCE_PENDING flag. Do not FIFO. Hold for EDI file."},
        {"invoice_id":"INV-07-005","customer_id":"CUST-07-005","customer_name":"Hillside Products LLC",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":9800.00,"open_amount":9800.00,
         "currency":"USD","po_reference":"PO-5533","payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"PO-5533 matches TXN-07-005 remittance"},
        {"invoice_id":"INV-07-006","customer_id":"CUST-07-005","customer_name":"Hillside Products LLC",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":9400.00,"open_amount":9400.00,
         "currency":"USD","po_reference":"PO-5541","payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"PO-5541 matches TXN-07-005. Bundle: $9,800 + $9,400 = $19,200"},
        {"invoice_id":"INV-07-007-A","customer_id":"CUST-07-006","customer_name":"Meridian Hardware Group",
         "invoice_date":"2024-07-06","due_date":"2024-08-05","original_amount":38400.00,"open_amount":38400.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":25,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Amount $38,400 matches TXN-07-006 exactly. Vague remittance match."},
        {"invoice_id":"INV-07-007","customer_id":"CUST-07-007","customer_name":"Pinnacle Supply Inc.",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":31500.00,"open_amount":31500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Legacy SAP ref = SAP-2024-112-A. TXN-07-007 uses old ref."},
        {"invoice_id":"INV-07-008","customer_id":"CUST-07-008","customer_name":"Trident Materials Corp",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":44500.00,"open_amount":44500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-07-008"}
    ],
    "credit_memos":[],
    "payer_alias_registry":[],
    "parent_child_hierarchy":[],
    "intercompany_netting":[],
    "legacy_invoice_map":{"LEGACY-INV-2024-0087":"INV-07-003","SAP-2024-112-A":"INV-07-007"},
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 08: Overpayments and Credit Memos
# ─────────────────────────────────────────────────────────────
write_sample(8, "Overpayments and Credit Memos",
bank={
    "statement_date":"2024-07-31","bank":"TD Bank","account":"****4567",
    "company":"Harbor Logistics Corp",
    "transactions":[
        {"txn_id":"TXN-08-001","date":"2024-07-04","amount":52000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"BAYSHORE FREIGHT LLC","bank_reference":"WIRE20240704001",
         "remittance_text":"INV-08-001","note":"OVERPAYMENT: Invoice is $48,000. Payment is $52,000. $4,000 excess becomes credit on account for future invoices."},
        {"txn_id":"TXN-08-002","date":"2024-07-07","amount":35500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"PORTSIDE TRADING CO","bank_reference":"ACH20240707002",
         "remittance_text":"INV-08-002 less CM-08-001 credit memo","note":"CREDIT NET: Invoice $38,000 minus existing credit memo $2,500 = net payment $35,500. Customer netting credit memo against invoice."},
        {"txn_id":"TXN-08-003","date":"2024-07-10","amount":75000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"ANCHOR INDUSTRIES INC","bank_reference":"WIRE20240710003",
         "remittance_text":"PREPAYMENT for order PO-8850 Q3 production run","note":"PREPAYMENT ADVANCE: No invoice yet. Customer prepaying for Q3 production. Post to GL 2050 Unearned Revenue. Create advance record."},
        {"txn_id":"TXN-08-004","date":"2024-07-13","amount":91500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"COASTAL CARGO GROUP","bank_reference":"WIRE20240713004",
         "remittance_text":"INV-08-003","note":"LARGE OVERPAYMENT: Invoice is $85,000. Payment is $91,500. $6,500 excess. Notify customer. High risk tier for treasury review."},
        {"txn_id":"TXN-08-005","date":"2024-07-17","amount":27300.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"DOCKSIDE MATERIALS LLC","bank_reference":"ACH20240717005",
         "remittance_text":"INV-08-004 less CM-08-002","note":"CREDIT NET: Invoice $31,000 minus credit memo $3,700 = net $27,300. Exact credit-net match."},
        {"txn_id":"TXN-08-006","date":"2024-07-21","amount":22000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"INLET SUPPLY GROUP","bank_reference":"ACH20240721006",
         "remittance_text":"INV-08-005","note":"Exact match: clean payment"},
        {"txn_id":"TXN-08-007","date":"2024-07-24","amount":44000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"TIDEWATER CORP","bank_reference":"WIRE20240724007",
         "remittance_text":"INV-08-006","note":"Exact match: clean payment"},
        {"txn_id":"TXN-08-008","date":"2024-07-27","amount":16800.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"SHORELINE PRODUCTS INC","bank_reference":"ACH20240727008",
         "remittance_text":"INV-08-007","note":"SMALL OVERPAYMENT: Invoice $16,500. Paid $16,800. Delta $300. Above auto write-off threshold. Post invoice, carry $300 as credit on account."}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Harbor Logistics Corp",
    "invoices":[
        {"invoice_id":"INV-08-001","customer_id":"CUST-08-001","customer_name":"Bayshore Freight LLC",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":48000.00,"open_amount":48000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Overpayment: paid $52,000, $4,000 goes to credit"},
        {"invoice_id":"INV-08-002","customer_id":"CUST-08-002","customer_name":"Portside Trading Co.",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":38000.00,"open_amount":38000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":2500.00,"note":"Existing credit memo CM-08-001 = $2,500. Net amount due = $35,500"},
        {"invoice_id":"INV-08-003","customer_id":"CUST-08-003","customer_name":"Coastal Cargo Group",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":85000.00,"open_amount":85000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Large overpayment: paid $91,500, $6,500 excess. High risk."},
        {"invoice_id":"INV-08-004","customer_id":"CUST-08-004","customer_name":"Dockside Materials LLC",
         "invoice_date":"2024-07-07","due_date":"2024-08-06","original_amount":31000.00,"open_amount":31000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":24,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":3700.00,"note":"Credit memo CM-08-002 = $3,700. Net = $27,300"},
        {"invoice_id":"INV-08-005","customer_id":"CUST-08-005","customer_name":"Inlet Supply Group",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":22000.00,"open_amount":22000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-08-006"},
        {"invoice_id":"INV-08-006","customer_id":"CUST-08-006","customer_name":"Tidewater Corp",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":44000.00,"open_amount":44000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-08-007"},
        {"invoice_id":"INV-08-007","customer_id":"CUST-08-007","customer_name":"Shoreline Products Inc.",
         "invoice_date":"2024-07-14","due_date":"2024-08-13","original_amount":16500.00,"open_amount":16500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":17,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Small overpayment: paid $16,800, delta $300 goes to credit"}
    ],
    "credit_memos":[
        {"cm_id":"CM-08-001","customer_id":"CUST-08-002","amount":2500.00,"reason":"Return allowance for damaged goods","date":"2024-06-20","applied_to_invoice":"INV-08-002"},
        {"cm_id":"CM-08-002","customer_id":"CUST-08-004","amount":3700.00,"reason":"Pricing correction on prior invoice","date":"2024-06-28","applied_to_invoice":"INV-08-004"}
    ],
    "payer_alias_registry":[],"parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 09: Identity and Name Resolution Issues
# ─────────────────────────────────────────────────────────────
write_sample(9, "Identity and Name Issues - SWIFT Truncation, DBA, Alias",
bank={
    "statement_date":"2024-07-31","bank":"KeyBank","account":"****8901",
    "company":"TechMerge Industries Inc.",
    "transactions":[
        {"txn_id":"TXN-09-001","date":"2024-07-04","amount":36500.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"BLACKSTONE MANUFACTURING","bank_reference":"SWIFT20240704001",
         "remittance_text":"INV-09-001","note":"SWIFT 35-CHAR TRUNCATION: Actual customer name is Blackstone Manufacturing Solutions Corp (38 chars). SWIFT cut it at 35 to BLACKSTONE MANUFACTURING. Match via alias table."},
        {"txn_id":"TXN-09-002","date":"2024-07-07","amount":24800.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"RJ BUILDING SUPPLIES","bank_reference":"ACH20240707002",
         "remittance_text":"INV-09-002","note":"DBA NAME: RJ Building Supplies is the registered DBA of Robertson-Jenkins Construction Materials Inc. Alias registry match."},
        {"txn_id":"TXN-09-003","date":"2024-07-10","amount":58000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"AXIOM TECHNOLOGIES INC","bank_reference":"WIRE20240710003",
         "remittance_text":"INV-09-003","note":"POST-ACQUISITION: Axiom Technologies Inc. was acquired by NovaTech Solutions in March 2024. Still paying under old name. Alias registry maps to CUST-09-003."},
        {"txn_id":"TXN-09-004","date":"2024-07-12","amount":19200.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"CONTINENTAL WIRE & CABLE","bank_reference":"ACH20240712004",
         "remittance_text":"INV-09-004","note":"ALIAS MATCH: Continental Wire & Cable is a known alias for Global Cable Systems LLC in our alias registry. High-confidence match."},
        {"txn_id":"TXN-09-005","date":"2024-07-15","amount":43700.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"EUROTECH COMPONENTS","bank_reference":"SWIFT20240715005",
         "remittance_text":"INV-09-005","note":"SWIFT 35-CHAR TRUNCATION: Full name is EuroTech Components and Assemblies GmbH (42 chars). SWIFT truncated to EUROTECH COMPONENTS. Match via alias."},
        {"txn_id":"TXN-09-006","date":"2024-07-18","amount":31100.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"METRO FASTENERS LLC","bank_reference":"ACH20240718006",
         "remittance_text":"INV-09-006","note":"DBA NAME: Metro Fasteners LLC is the DBA of Metropolitan Industrial Fasteners Corporation. Alias match with >75% fuzzy similarity."},
        {"txn_id":"TXN-09-007","date":"2024-07-22","amount":27500.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"HIGHLAND ELEC SUPPLY CO","bank_reference":"ACH20240722007",
         "remittance_text":"INV-09-007","note":"FUZZY MATCH: 'HIGHLAND ELEC SUPPLY CO' matches 'Highland Electrical Supply Company' at 87% similarity. Alias resolve with high confidence."},
        {"txn_id":"TXN-09-008","date":"2024-07-26","amount":51000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"MERIDIAN GLASS PRODUCTS","bank_reference":"WIRE20240726008",
         "remittance_text":"INV-09-008","note":"Exact name match: clean payment"}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"TechMerge Industries Inc.",
    "invoices":[
        {"invoice_id":"INV-09-001","customer_id":"CUST-09-001","customer_name":"Blackstone Manufacturing Solutions Corp",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":36500.00,"open_amount":36500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,
         "note":"SWIFT truncates to BLACKSTONE MANUFACTURING (35 chars)"},
        {"invoice_id":"INV-09-002","customer_id":"CUST-09-002","customer_name":"Robertson-Jenkins Construction Materials Inc.",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":24800.00,"open_amount":24800.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"DBA = RJ Building Supplies"},
        {"invoice_id":"INV-09-003","customer_id":"CUST-09-003","customer_name":"NovaTech Solutions (formerly Axiom Technologies)",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":58000.00,"open_amount":58000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Post-acquisition. Former name Axiom Technologies Inc. still used by payer"},
        {"invoice_id":"INV-09-004","customer_id":"CUST-09-004","customer_name":"Global Cable Systems LLC",
         "invoice_date":"2024-07-06","due_date":"2024-08-05","original_amount":19200.00,"open_amount":19200.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":25,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Known alias: Continental Wire & Cable"},
        {"invoice_id":"INV-09-005","customer_id":"CUST-09-005","customer_name":"EuroTech Components and Assemblies GmbH",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":43700.00,"open_amount":43700.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"SWIFT truncates to EUROTECH COMPONENTS (35 chars from 42)"},
        {"invoice_id":"INV-09-006","customer_id":"CUST-09-006","customer_name":"Metropolitan Industrial Fasteners Corporation",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":31100.00,"open_amount":31100.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"DBA = Metro Fasteners LLC"},
        {"invoice_id":"INV-09-007","customer_id":"CUST-09-007","customer_name":"Highland Electrical Supply Company",
         "invoice_date":"2024-07-12","due_date":"2024-08-11","original_amount":27500.00,"open_amount":27500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":19,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Fuzzy match: HIGHLAND ELEC SUPPLY CO at 87% similarity"},
        {"invoice_id":"INV-09-008","customer_id":"CUST-09-008","customer_name":"Meridian Glass Products",
         "invoice_date":"2024-07-14","due_date":"2024-08-13","original_amount":51000.00,"open_amount":51000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":17,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-09-008"}
    ],
    "credit_memos":[],
    "payer_alias_registry":[
        {"payer_alias":"BLACKSTONE MANUFACTURING","canonical_customer_id":"CUST-09-001","canonical_name":"Blackstone Manufacturing Solutions Corp","match_type":"SWIFT_TRUNCATION"},
        {"payer_alias":"RJ BUILDING SUPPLIES","canonical_customer_id":"CUST-09-002","canonical_name":"Robertson-Jenkins Construction Materials Inc.","match_type":"DBA"},
        {"payer_alias":"AXIOM TECHNOLOGIES INC","canonical_customer_id":"CUST-09-003","canonical_name":"NovaTech Solutions","match_type":"POST_ACQUISITION"},
        {"payer_alias":"CONTINENTAL WIRE & CABLE","canonical_customer_id":"CUST-09-004","canonical_name":"Global Cable Systems LLC","match_type":"ALIAS"},
        {"payer_alias":"EUROTECH COMPONENTS","canonical_customer_id":"CUST-09-005","canonical_name":"EuroTech Components and Assemblies GmbH","match_type":"SWIFT_TRUNCATION"},
        {"payer_alias":"METRO FASTENERS LLC","canonical_customer_id":"CUST-09-006","canonical_name":"Metropolitan Industrial Fasteners Corporation","match_type":"DBA"},
        {"payer_alias":"HIGHLAND ELEC SUPPLY CO","canonical_customer_id":"CUST-09-007","canonical_name":"Highland Electrical Supply Company","match_type":"FUZZY"}
    ],
    "parent_child_hierarchy":[],"intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":[]}
})


# ─────────────────────────────────────────────────────────────
# SAMPLE 10: Enterprise Mixed Batch - Large Amounts, All Types
# ─────────────────────────────────────────────────────────────
write_sample(10, "Enterprise Mixed Batch - All Exception Types",
bank={
    "statement_date":"2024-07-31","bank":"Goldman Sachs","account":"****1122",
    "company":"Consolidated Global Corp",
    "transactions":[
        {"txn_id":"TXN-10-001","date":"2024-07-02","amount":250000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"ATLAS MANUFACTURING GROUP","bank_reference":"WIRE20240702001",
         "remittance_text":"INV-10-001","note":"Clean exact match: large amount, exact invoice reference"},
        {"txn_id":"TXN-10-002","date":"2024-07-04","amount":487500.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"TITAN INDUSTRIAL CORP","bank_reference":"WIRE20240704002",
         "remittance_text":"INV-10-002 INV-10-003 INV-10-004","note":"Multi-invoice: $175,000 + $212,500 + $100,000 = $487,500 exact"},
        {"txn_id":"TXN-10-003","date":"2024-07-07","amount":162000.00,"currency":"USD",
         "payment_type":"SWIFT","payer_raw":"FRANKFURT LOGISTICS GMBH","bank_reference":"SWIFT20240707003",
         "remittance_text":"INV-10-005 EUR 150000 @ 1.08","note":"EUR SWIFT: 150,000 EUR at 1.08 USD/EUR = $162,000. FX payment."},
        {"txn_id":"TXN-10-004","date":"2024-07-09","amount":320000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"ZENITH HOLDINGS INC","bank_reference":"WIRE20240709004",
         "remittance_text":"INV-10-006 payment on behalf of Zenith Southeast LLC",
         "note":"Parent/subsidiary: Zenith Holdings (CUST-10-P01) paying for Zenith Southeast LLC (CUST-10-006). Post to subsidiary."},
        {"txn_id":"TXN-10-005","date":"2024-07-11","amount":890000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"MIRAN INTERNATIONAL FZCO","bank_reference":"WIRE20240711005",
         "remittance_text":"INV-10-007","note":"COMPLIANCE HOLD: MIRAN INTERNATIONAL FZCO triggers OFAC sanctions screening. DO NOT POST. Escalate to Compliance Officer within 4 hours."},
        {"txn_id":"TXN-10-006","date":"2024-07-14","amount":138000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"SUMMIT ENTERPRISE GROUP","bank_reference":"ACH20240714006",
         "remittance_text":"INV-10-008 less freight $7,000 less damage claim $5,000",
         "note":"Multiple deductions: $150,000 invoice less $7,000 freight allowance less $5,000 damage claim = $138,000. Both deductions require workitems."},
        {"txn_id":"TXN-10-007","date":"2024-07-17","amount":225000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"HORIZON GLOBAL LLC","bank_reference":"WIRE20240717007",
         "remittance_text":"INV-10-009","note":"OVERPAYMENT: Invoice $200,000. Payment $225,000. $25,000 excess. High-risk. Route to treasury."},
        {"txn_id":"TXN-10-008","date":"2024-07-20","amount":293600.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"CRESTLINE SUPPLIES INC","bank_reference":"ACH20240720008",
         "remittance_text":"INV-10-010 2% early pay discount","note":"LATE DISCOUNT: Invoice $300,000 * 0.98 = $294,000. But discount deadline was 2024-07-15. Payment on 2024-07-20 is 5 days late. Unauthorized $6,000 discount."},
        {"txn_id":"TXN-10-009","date":"2024-07-22","amount":410000.00,"currency":"USD",
         "payment_type":"ACH","payer_raw":"NOVA DISTRIBUTION CORP","bank_reference":"ACH20240722009",
         "remittance_text":"EDI 820 file pending batch ref 2024-07-22","note":"EDI PENDING: Do not FIFO match. EDI 820 file expected within 24 hours with full remittance detail."},
        {"txn_id":"TXN-10-010","date":"2024-08-20","amount":175000.00,"currency":"USD",
         "payment_type":"CHECK","payer_raw":"RIDGEWAY CAPITAL GROUP","bank_reference":"CHECK-018834",
         "remittance_text":"INV-10-012","note":"POST-DATED CHECK: Check date 2024-08-20 is future-dated. Hold until check date."},
        {"txn_id":"TXN-10-011","date":"2024-07-25","amount":84000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"KEYSTONE MATERIALS CORP","bank_reference":"WIRE20240725011",
         "remittance_text":"INV-10-013 less CM-10-001 credit $16,000","note":"CREDIT NET: Invoice $100,000 minus credit memo $16,000 = net $84,000. Exact credit-net match."},
        {"txn_id":"TXN-10-012","date":"2024-07-28","amount":195000.00,"currency":"USD",
         "payment_type":"WIRE","payer_raw":"EASTGATE SOLUTIONS GROUP","bank_reference":"WIRE20240728012",
         "remittance_text":"","note":"NO REMITTANCE: Large wire with no reference. FIFO match to oldest open invoice for this customer."}
    ]
},
ar={
    "as_of_date":"2024-07-31","company":"Consolidated Global Corp",
    "invoices":[
        {"invoice_id":"INV-10-001","customer_id":"CUST-10-001","customer_name":"Atlas Manufacturing Group",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":250000.00,"open_amount":250000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Exact match TXN-10-001"},
        {"invoice_id":"INV-10-002","customer_id":"CUST-10-002","customer_name":"Titan Industrial Corp",
         "invoice_date":"2024-06-28","due_date":"2024-07-28","original_amount":175000.00,"open_amount":175000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":33,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Multi-bundle part 1"},
        {"invoice_id":"INV-10-003","customer_id":"CUST-10-002","customer_name":"Titan Industrial Corp",
         "invoice_date":"2024-07-02","due_date":"2024-08-01","original_amount":212500.00,"open_amount":212500.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":29,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Multi-bundle part 2"},
        {"invoice_id":"INV-10-004","customer_id":"CUST-10-002","customer_name":"Titan Industrial Corp",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":100000.00,"open_amount":100000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Multi-bundle part 3"},
        {"invoice_id":"INV-10-005","customer_id":"CUST-10-003","customer_name":"Frankfurt Logistics GmbH",
         "invoice_date":"2024-07-03","due_date":"2024-08-02","original_amount":162000.00,"open_amount":162000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":28,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"EUR 150,000 @ 1.08 = $162,000"},
        {"invoice_id":"INV-10-006","customer_id":"CUST-10-006","customer_name":"Zenith Southeast LLC",
         "invoice_date":"2024-07-04","due_date":"2024-08-03","original_amount":320000.00,"open_amount":320000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":27,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Parent Zenith Holdings (CUST-10-P01) pays on behalf"},
        {"invoice_id":"INV-10-007","customer_id":"CUST-10-007","customer_name":"Miran International FZCO",
         "invoice_date":"2024-07-05","due_date":"2024-08-04","original_amount":890000.00,"open_amount":890000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":26,"aging_bucket":"1-30","status":"ON_HOLD","dispute_reason":"OFAC sanctions screening - do not post",
         "existing_credit_memo":0,"note":"COMPLIANCE_HOLD. TXN-10-005 must not be posted."},
        {"invoice_id":"INV-10-008","customer_id":"CUST-10-008","customer_name":"Summit Enterprise Group",
         "invoice_date":"2024-07-06","due_date":"2024-08-05","original_amount":150000.00,"open_amount":150000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":25,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Freight $7,000 + damage claim $5,000 = $12,000 total deductions"},
        {"invoice_id":"INV-10-009","customer_id":"CUST-10-009","customer_name":"Horizon Global LLC",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":200000.00,"open_amount":200000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Overpayment: paid $225,000, excess $25,000 to credit"},
        {"invoice_id":"INV-10-010","customer_id":"CUST-10-010","customer_name":"Crestline Supplies Inc.",
         "invoice_date":"2024-07-01","due_date":"2024-07-31","original_amount":300000.00,"open_amount":300000.00,
         "currency":"USD","po_reference":None,"payment_terms":"2/10 NET 30","discount_pct":2.0,"discount_deadline":"2024-07-11",
         "aging_days":30,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Discount deadline was 2024-07-11. Payment on 2024-07-20 is late."},
        {"invoice_id":"INV-10-011","customer_id":"CUST-10-011","customer_name":"Nova Distribution Corp",
         "invoice_date":"2024-07-08","due_date":"2024-08-07","original_amount":410000.00,"open_amount":410000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":23,"aging_bucket":"1-30","status":"ON_HOLD","dispute_reason":"EDI_REMITTANCE_PENDING",
         "existing_credit_memo":0,"note":"Hold for EDI 820 file before matching"},
        {"invoice_id":"INV-10-012","customer_id":"CUST-10-012","customer_name":"Ridgeway Capital Group",
         "invoice_date":"2024-07-15","due_date":"2024-08-14","original_amount":175000.00,"open_amount":175000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":16,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Post-dated check. Hold until 2024-08-20."},
        {"invoice_id":"INV-10-013","customer_id":"CUST-10-013","customer_name":"Keystone Materials Corp",
         "invoice_date":"2024-07-10","due_date":"2024-08-09","original_amount":100000.00,"open_amount":100000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":21,"aging_bucket":"1-30","status":"OPEN","dispute_reason":None,"existing_credit_memo":16000.00,"note":"Credit memo $16,000. Net due = $84,000"},
        {"invoice_id":"INV-10-014","customer_id":"CUST-10-014","customer_name":"Eastgate Solutions Group",
         "invoice_date":"2024-06-22","due_date":"2024-07-22","original_amount":195000.00,"open_amount":195000.00,
         "currency":"USD","po_reference":None,"payment_terms":"NET 30","discount_pct":0,"discount_deadline":None,
         "aging_days":39,"aging_bucket":"31-60","status":"OPEN","dispute_reason":None,"existing_credit_memo":0,"note":"Oldest open invoice for customer. FIFO target for TXN-10-012"}
    ],
    "credit_memos":[
        {"cm_id":"CM-10-001","customer_id":"CUST-10-013","amount":16000.00,"reason":"Volume rebate Q2 2024","date":"2024-07-01","applied_to_invoice":"INV-10-013"}
    ],
    "payer_alias_registry":[],
    "parent_child_hierarchy":[
        {"parent_customer_id":"CUST-10-P01","parent_name":"Zenith Holdings Inc.","children":["CUST-10-006"]}
    ],
    "intercompany_netting":[],
    **BASE_CONFIG,
    "compliance_config":{"ofac_screening":True,"disputed_invoice_ids":[],"legal_hold_invoice_ids":[],"do_not_auto_apply_customer_ids":["CUST-10-007"]}
})

print("\nAll 10 samples generated successfully.")
print(f"Output directory: {SAMPLES_DIR.resolve()}")
