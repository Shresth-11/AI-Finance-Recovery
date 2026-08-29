import csv
import json
import random
import os
from datetime import datetime, timedelta, timezone

# Fix seed for reproducibility
random.seed(42)

# Config & Paths
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ORDERS_FILE = os.path.join(OUTPUT_DIR, "orders.csv")
PAYMENTS_FILE = os.path.join(OUTPUT_DIR, "payments.csv")
SETTLEMENTS_FILE = os.path.join(OUTPUT_DIR, "settlements.csv")
INVOICES_FILE = os.path.join(OUTPUT_DIR, "invoices.csv")
GROUND_TRUTH_CSV = os.path.join(OUTPUT_DIR, "ground_truth.csv")
GROUND_TRUTH_JSON = os.path.join(OUTPUT_DIR, "ground_truth.json")

# Fictional Merchant Context
MERCHANT_NAME = "Northstar Retail Pvt. Ltd."
MERCHANT_ID = "mer_NSR_882910"
BANK_ACC = "HDFC0000123 / 50100293810291"
TIMEZONE = "Asia/Kolkata"
CURRENCY = "INR"

START_DATE = datetime(2026, 6, 30, 9, 0, 0)
VENDORS = [
    "Razorpay Software Private Limited",
    "Paytm Payments Bank Ltd",
    "PhonePe Merchant Services",
    "Cashfree Payments India Pvt Ltd",
    "BillDesk Technology Services"
]

FIRST_NAMES = ["Ananya", "Rohan", "Kavya", "Rahul", "Priya", "Vikram", "Neha", "Aditya", "Sneha", "Siddharth", "Ishita", "Amit", "Pooja", "Karan", "Riya", "Aarav"]
LAST_NAMES = ["Sharma", "Mehta", "Iyer", "Gupta", "Patel", "Singh", "Kumar", "Nair", "Reddy", "Deshmukh", "Joshi", "Agarwal"]

PAYMENT_METHODS = ["UPI", "CARD", "NET_BANKING", "WALLET"]
PAYMENT_METHOD_WEIGHTS = [0.55, 0.25, 0.12, 0.08]

def get_random_timestamp(days_offset_range=(0, 58)):
    days = random.randint(days_offset_range[0], days_offset_range[1])
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    return START_DATE + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

def calculate_standard_fee(amount, method):
    if method == "UPI":
        fee = 0.0  # Zero MDR on UPI
    elif method == "CARD":
        fee = round(amount * 0.02, 2)  # 2.0% MDR
    elif method == "NET_BANKING":
        fee = 15.0  # Flat ₹15
    elif method == "WALLET":
        fee = round(amount * 0.015, 2)  # 1.5% MDR
    else:
        fee = 0.0
    
    tax = round(fee * 0.18, 2)  # 18% GST on MDR fee
    return fee, tax

def generate_amount():
    r = random.random()
    if r < 0.45:
        return float(random.randint(99, 1999))
    elif r < 0.80:
        return float(random.randint(2000, 19999))
    elif r < 0.95:
        return float(random.randint(20000, 75000))
    else:
        return float(random.randint(75001, 150000))

def main():
    print(f"[LedgerGuard AI] Generating realistic synthetic financial dataset for {MERCHANT_NAME}...")

    orders = []
    payments = []
    settlements = []
    invoices = []
    ground_truth = []

    total_orders_count = 500
    total_payments_target = 540
    total_settlements_target = 470
    total_invoices_count = 500

    # 1. Create Base Orders (500)
    for i in range(1, total_orders_count + 1):
        order_id = f"ord_live_{1000 + i}"
        cust_first = random.choice(FIRST_NAMES)
        cust_last = random.choice(LAST_NAMES)
        cust_name = f"{cust_first} {cust_last}"
        cust_id = f"cust_{2000 + i}"
        cust_email = f"{cust_first.lower()}.{cust_last.lower()}{i}@example.test"
        cust_phone = f"+91-98XXXX{1000 + (i % 9000)}"
        amount = generate_amount()
        order_time = get_random_timestamp((0, 50))
        
        orders.append({
            "order_id": order_id,
            "merchant_id": MERCHANT_ID,
            "customer_id": cust_id,
            "customer_name": cust_name,
            "customer_email": cust_email,
            "customer_phone": cust_phone,
            "order_amount": amount,
            "currency": CURRENCY,
            "status": "PAID",
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    order_dict = {o["order_id"]: o for o in orders}

    # Anomaly assignments:
    duplicate_payment_order_ids = [f"ord_live_{1000 + i}" for i in range(1, 21)]
    ghost_payment_indices = list(range(1, 51))
    partial_payment_order_ids = [f"ord_live_{1000 + i}" for i in range(21, 36)]
    overpayment_order_ids = [f"ord_live_{1000 + i}" for i in range(36, 46)]
    missing_payment_order_ids = [f"ord_live_{1000 + i}" for i in range(46, 76)]
    missing_settlement_order_ids = [f"ord_live_{1000 + i}" for i in range(76, 106)]
    delayed_settlement_order_ids = [f"ord_live_{1000 + i}" for i in range(106, 126)]
    duplicate_settlement_order_ids = [f"ord_live_{1000 + i}" for i in range(126, 156)]
    fee_anomaly_order_ids = [f"ord_live_{1000 + i}" for i in range(136, 151)]
    invoice_mismatch_order_ids = [f"ord_live_{1000 + i}" for i in range(151, 166)]
    fuzzy_match_order_ids = [f"ord_live_{1000 + i}" for i in range(166, 176)]

    payment_seq = 1000
    settlement_seq = 1000
    invoice_seq = 1000

    # Process Payments & Settlements for Orders 1..500
    for o in orders:
        oid = o["order_id"]
        o_amount = o["order_amount"]
        o_time = datetime.strptime(o["created_at"], "%Y-%m-%d %H:%M:%S")
        method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]

        # Case 1: Missing Payment (Order exists in ERP, but 0 gateway capture)
        if oid in missing_payment_order_ids:
            ground_truth.append({
                "exception_type": "MISSING_PAYMENT",
                "entity_type": "ORDER",
                "entity_id": oid,
                "discrepancy_amount": o_amount,
                "severity": "HIGH" if o_amount < 50000 else "CRITICAL",
                "reason": "Order recorded as paid in ERP but 0 payment capture record exists in gateway ledger."
            })
            # Also create Tax Invoice
            invoice_seq += 1
            inv_id = f"INV-2026-{invoice_seq}"
            inv_tax = round(o_amount * 0.18, 2)
            invoices.append({
                "invoice_id": inv_id,
                "order_id": oid,
                "vendor_name": random.choice(VENDORS),
                "invoice_amount": o_amount,
                "tax_amount": inv_tax,
                "net_total": o_amount + inv_tax,
                "invoice_date": o["created_at"],
                "due_date": (o_time + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "ISSUED"
            })
            continue

        # Case 2: Duplicate Payment (Customer retried payment after app checkout response timeout)
        elif oid in duplicate_payment_order_ids:
            payment_seq += 1
            pay_id_1 = f"pay_NSR_{payment_seq}"
            pay_time_1 = o_time + timedelta(minutes=random.randint(1, 5))
            fee_1, tax_1 = calculate_standard_fee(o_amount, method)
            
            payments.append({
                "payment_id": pay_id_1,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee_1,
                "tax_amount": tax_1,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id_1}",
                "transaction_time": pay_time_1.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            # Second duplicate payment (5 mins later due to app timeout)
            payment_seq += 1
            pay_id_2 = f"pay_NSR_{payment_seq}"
            pay_time_2 = pay_time_1 + timedelta(minutes=random.randint(2, 10))
            fee_2, tax_2 = calculate_standard_fee(o_amount, method)

            payments.append({
                "payment_id": pay_id_2,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee_2,
                "tax_amount": tax_2,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id_2}",
                "transaction_time": pay_time_2.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            ground_truth.append({
                "exception_type": "DUPLICATE_PAYMENT",
                "entity_type": "PAYMENT",
                "entity_id": pay_id_2,
                "discrepancy_amount": o_amount,
                "severity": "CRITICAL",
                "reason": "Customer retried checkout payment after app response timeout, resulting in double capture."
            })

            # Create settlement for first payment
            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = o_amount - (fee_1 + tax_1)
            settle_time = pay_time_1 + timedelta(days=1 if method == "UPI" else 2)

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_AXIS_{random.randint(10000, 99999)}",
                "payment_id": pay_id_1,
                "gross_amount": o_amount,
                "fee_amount": fee_1,
                "tax_amount": tax_1,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

        # Case 3: Partial Payment
        elif oid in partial_payment_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            partial_amt = round(o_amount * 0.70, 2)  # 70% partial capture
            fee, tax = calculate_standard_fee(partial_amt, method)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": partial_amt,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            variance = round(o_amount - partial_amt, 2)
            ground_truth.append({
                "exception_type": "PARTIAL_PAYMENT",
                "entity_type": "PAYMENT",
                "entity_id": pay_id,
                "discrepancy_amount": variance,
                "severity": "HIGH" if variance < 50000 else "CRITICAL",
                "reason": "Partial capture recorded against full order amount."
            })

            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = partial_amt - (fee + tax)
            settle_time = pay_time + timedelta(days=1 if method == "UPI" else 2)

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_HDFC_{random.randint(10000, 99999)}",
                "payment_id": pay_id,
                "gross_amount": partial_amt,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

        # Case 4: Overpayment
        elif oid in overpayment_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            over_amt = round(o_amount + 500.0, 2)
            fee, tax = calculate_standard_fee(over_amt, method)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": over_amt,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            ground_truth.append({
                "exception_type": "OVERPAYMENT",
                "entity_type": "PAYMENT",
                "entity_id": pay_id,
                "discrepancy_amount": 500.0,
                "severity": "MEDIUM",
                "reason": "Captured payment amount exceeds ERP order total by ₹500."
            })

            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = over_amt - (fee + tax)
            settle_time = pay_time + timedelta(days=1 if method == "UPI" else 2)

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_ICICI_{random.randint(10000, 99999)}",
                "payment_id": pay_id,
                "gross_amount": over_amt,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

        # Case 5: Missing Settlement
        elif oid in missing_settlement_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            fee, tax = calculate_standard_fee(o_amount, method)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "PENDING"
            })

            ground_truth.append({
                "exception_type": "MISSING_SETTLEMENT",
                "entity_type": "PAYMENT",
                "entity_id": pay_id,
                "discrepancy_amount": o_amount,
                "severity": "HIGH" if o_amount < 50000 else "CRITICAL",
                "reason": "Settlement reference unavailable after expected T+2 window."
            })

        # Case 6: Delayed Settlement (Payout received past SLA)
        elif oid in delayed_settlement_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            fee, tax = calculate_standard_fee(o_amount, method)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = o_amount - (fee + tax)
            delayed_time = pay_time + timedelta(days=9)  # 9 days delay vs 2 days SLA limit

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_SBIN_{random.randint(10000, 99999)}",
                "payment_id": pay_id,
                "gross_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": delayed_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

            ground_truth.append({
                "exception_type": "DELAYED_SETTLEMENT",
                "entity_type": "SETTLEMENT",
                "entity_id": setl_id,
                "discrepancy_amount": o_amount,
                "severity": "MEDIUM",
                "reason": "Gateway settlement batch delayed due to bank clearing holiday."
            })

        # Case 6b: Duplicate Settlement (Multiple settlement advices referencing same UTR or payment ID)
        elif oid in duplicate_settlement_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            fee, tax = calculate_standard_fee(o_amount, method)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            settlement_seq += 1
            setl_id_1 = f"setl_2026_08_{settlement_seq}"
            net_amt = o_amount - (fee + tax)
            settle_time_1 = pay_time + timedelta(days=1)
            utr_shared = f"UTR_HDFC_{random.randint(10000, 99999)}"

            settlements.append({
                "settlement_id": setl_id_1,
                "utr": utr_shared,
                "payment_id": pay_id,
                "gross_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time_1.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

            # Duplicate settlement advice for same payment ID
            settlement_seq += 1
            setl_id_2 = f"setl_2026_08_{settlement_seq}"
            settlements.append({
                "settlement_id": setl_id_2,
                "utr": utr_shared,
                "payment_id": pay_id,
                "gross_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": (settle_time_1 + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

            ground_truth.append({
                "exception_type": "DUPLICATE_SETTLEMENT",
                "entity_type": "SETTLEMENT",
                "entity_id": setl_id_2,
                "discrepancy_amount": o_amount,
                "severity": "CRITICAL",
                "reason": "Duplicate bank payout advice recorded referencing same UTR and payment ID."
            })

        # Case 7: Fee Anomaly
        elif oid in fee_anomaly_order_ids:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            # Standard fee vs anomalous fee (e.g. 5% MDR instead of 2%)
            excess_fee = round(o_amount * 0.05, 2)
            tax = round(excess_fee * 0.18, 2)

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_method": "CARD",
                "payment_amount": o_amount,
                "fee_amount": excess_fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            std_fee, _ = calculate_standard_fee(o_amount, "CARD")
            fee_diff = round(excess_fee - std_fee, 2)

            ground_truth.append({
                "exception_type": "FEE_ANOMALY",
                "entity_type": "PAYMENT",
                "entity_id": pay_id,
                "discrepancy_amount": fee_diff,
                "severity": "HIGH",
                "reason": "MDR fee applied above configured commercial contract rate."
            })

            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = o_amount - (excess_fee + tax)
            settle_time = pay_time + timedelta(days=2)

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_KOTAK_{random.randint(10000, 99999)}",
                "payment_id": pay_id,
                "gross_amount": o_amount,
                "fee_amount": excess_fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

        # Standard clean matching order
        else:
            payment_seq += 1
            pay_id = f"pay_NSR_{payment_seq}"
            pay_time = o_time + timedelta(minutes=random.randint(1, 10))
            fee, tax = calculate_standard_fee(o_amount, method)

            # Check if fuzzy match formatting anomaly
            order_ref_for_payment = oid
            if oid in fuzzy_match_order_ids:
                order_ref_for_payment = f"ORD_{oid.split('_')[-1]}"  # Format variation: ORD_1166 vs ord_live_1166
                ground_truth.append({
                    "exception_type": "INVOICE_MISMATCH",
                    "entity_type": "PAYMENT",
                    "entity_id": pay_id,
                    "discrepancy_amount": 0.0,
                    "severity": "LOW",
                    "reason": "Imported order ID had formatting variation; matched using amount, customer email, and timestamp."
                })

            payments.append({
                "payment_id": pay_id,
                "order_id": order_ref_for_payment,
                "payment_method": method,
                "payment_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "status": "CAPTURED",
                "gateway_ref": f"gtw_ref_{pay_id}",
                "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "SETTLED"
            })

            settlement_seq += 1
            setl_id = f"setl_2026_08_{settlement_seq}"
            net_amt = o_amount - (fee + tax)
            settle_time = pay_time + timedelta(days=1 if method == "UPI" else 2)

            settlements.append({
                "settlement_id": setl_id,
                "utr": f"UTR_HDFC_{random.randint(10000, 99999)}",
                "payment_id": pay_id,
                "gross_amount": o_amount,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED"
            })

        # Generate Tax Invoice for Order
        invoice_seq += 1
        inv_id = f"INV-2026-{invoice_seq}"
        inv_amt = o_amount
        if oid in invoice_mismatch_order_ids:
            inv_amt = round(o_amount + 450.0, 2)
            ground_truth.append({
                "exception_type": "INVOICE_MISMATCH",
                "entity_type": "INVOICE",
                "entity_id": inv_id,
                "discrepancy_amount": 450.0,
                "severity": "MEDIUM",
                "reason": "Vendor tax invoice amount discrepancy vs linked order PO."
            })

        inv_tax = round(inv_amt * 0.18, 2)
        invoices.append({
            "invoice_id": inv_id,
            "order_id": oid,
            "vendor_name": random.choice(VENDORS),
            "invoice_amount": inv_amt,
            "tax_amount": inv_tax,
            "net_total": inv_amt + inv_tax,
            "invoice_date": o["created_at"],
            "due_date": (o_time + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "ISSUED"
        })

    # Add Payment Without Order (Ghost payments)
    for g_idx in ghost_payment_indices:
        payment_seq += 1
        pay_id = f"pay_NSR_{payment_seq}"
        ghost_oid = f"ord_ghost_{9000 + g_idx}"
        amount = generate_amount()
        pay_time = get_random_timestamp((0, 50))
        fee, tax = calculate_standard_fee(amount, "UPI")

        payments.append({
            "payment_id": pay_id,
            "order_id": ghost_oid,
            "payment_method": "UPI",
            "payment_amount": amount,
            "fee_amount": fee,
            "tax_amount": tax,
            "status": "CAPTURED",
            "gateway_ref": f"gtw_ref_{pay_id}",
            "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
            "settlement_status": "SETTLED"
        })

        ground_truth.append({
            "exception_type": "PAYMENT_WITHOUT_ORDER",
            "entity_type": "PAYMENT",
            "entity_id": pay_id,
            "discrepancy_amount": amount,
            "severity": "HIGH" if amount < 50000 else "CRITICAL",
            "reason": "Gateway capture exists with no corresponding ERP order record."
        })

    # Save to CSV files
    fieldnames_orders = ["order_id", "merchant_id", "customer_id", "customer_name", "customer_email", "customer_phone", "order_amount", "currency", "status", "created_at"]
    fieldnames_payments = ["payment_id", "order_id", "payment_method", "payment_amount", "fee_amount", "tax_amount", "status", "gateway_ref", "transaction_time", "settlement_status"]
    fieldnames_settlements = ["settlement_id", "utr", "payment_id", "gross_amount", "fee_amount", "tax_amount", "net_amount", "bank_account", "settlement_time", "status"]
    fieldnames_invoices = ["invoice_id", "order_id", "vendor_name", "invoice_amount", "tax_amount", "net_total", "invoice_date", "due_date", "status"]
    fieldnames_gt = ["exception_type", "entity_type", "entity_id", "discrepancy_amount", "severity", "reason"]

    def write_csv(filepath, fieldnames, data):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_csv(ORDERS_FILE, fieldnames_orders, orders)
    write_csv(PAYMENTS_FILE, fieldnames_payments, payments)
    write_csv(SETTLEMENTS_FILE, fieldnames_settlements, settlements)
    write_csv(INVOICES_FILE, fieldnames_invoices, invoices)
    write_csv(GROUND_TRUTH_CSV, fieldnames_gt, ground_truth)

    with open(GROUND_TRUTH_JSON, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"[LedgerGuard AI] Successfully generated datasets for {MERCHANT_NAME}:")
    print(f"  - Orders: {len(orders)} rows -> {ORDERS_FILE}")
    print(f"  - Payments: {len(payments)} rows -> {PAYMENTS_FILE}")
    print(f"  - Settlements: {len(settlements)} rows -> {SETTLEMENTS_FILE}")
    print(f"  - Invoices: {len(invoices)} rows -> {INVOICES_FILE}")
    print(f"  - Ground Truth: {len(ground_truth)} anomalies -> {GROUND_TRUTH_CSV}")

if __name__ == "__main__":
    main()
