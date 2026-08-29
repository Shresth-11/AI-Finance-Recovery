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

# Constants
START_DATE = datetime(2026, 6, 30, 9, 0, 0)
MERCHANT_ID = "mer_live_882910"
BANK_ACC = "HDFC0000123 / 50100293810291"
VENDORS = [
    "Razorpay Software Private Limited",
    "Paytm Payments Bank Ltd",
    "PhonePe Merchant Services",
    "Cashfree Payments India Pvt Ltd",
    "BillDesk Technology Services"
]

FIRST_NAMES = ["Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Neha", "Rahul", "Kavya", "Aditya", "Sneha", "Siddharth", "Ishita", "Amit", "Pooja", "Karan", "Riya"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Iyer", "Nair", "Reddy", "Chowdhury", "Deshmukh", "Joshi", "Mehta", "Agarwal"]

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
        fee = 0.0
    elif method == "CARD":
        fee = round(amount * 0.02, 2)  # 2% MDR
    elif method == "NET_BANKING":
        fee = 15.0  # Flat ₹15
    elif method == "WALLET":
        fee = round(amount * 0.015, 2)  # 1.5%
    else:
        fee = 0.0
    
    tax = round(fee * 0.18, 2)  # 18% GST on fee
    return fee, tax

def generate_amount():
    # Weighted range between 99 and 150000
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
    print("[LedgerGuard AI] Generating synthetic financial dataset...")

    orders = []
    payments = []
    settlements = []
    invoices = []
    ground_truth = []

    # State tracking
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
        cust_email = f"{cust_first.lower()}.{cust_last.lower()}{i}@example.in"
        cust_phone = f"+9198{random.randint(10000000, 99999999)}"
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
            "currency": "INR",
            "status": "PAID",
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Index orders for easy access
    order_dict = {o["order_id"]: o for o in orders}

    # Anomaly assignments:
    # 1. Duplicate Payments: 20 orders will have 2 payment records
    duplicate_payment_order_ids = [f"ord_live_{1000 + i}" for i in range(1, 21)]
    # 2. Payment without Order: 15 payments with non-existent order_id
    ghost_payment_indices = list(range(1, 16))
    # 3. Partial Payments: 5 orders
    partial_payment_order_ids = [f"ord_live_{1000 + i}" for i in range(21, 26)]
    # 4. Overpayments: 5 orders
    overpayment_order_ids = [f"ord_live_{1000 + i}" for i in range(26, 31)]
    # 5. Missing Settlements: 15 payments
    missing_settlement_payment_ids = set()
    # 6. Settlement Mismatches: 15 settlements
    settlement_mismatch_indices = list(range(31, 46))
    # 7. Delayed Settlements: 15 settlements
    delayed_settlement_indices = list(range(46, 61))
    # 8. Duplicate Settlements: 10 payments settled twice
    duplicate_settlement_indices = list(range(61, 71))
    # 9. Refund Mismatches: 10 payments
    refund_mismatch_indices = list(range(71, 81))
    # 10. Invoice Mismatches: 15 invoices
    invoice_mismatch_indices = list(range(81, 96))
    # 11. Fee Anomalies: 15 payments
    fee_anomaly_indices = list(range(96, 111))
    # 12. Fuzzy Match Cases: 10 invoices
    fuzzy_match_indices = list(range(111, 121))

    payment_id_counter = 1000
    utr_counter = 500000000000

    # Map payment_id -> dict for settlement generation
    payment_records_map = {}

    # 2. Generate Payments for 500 Orders
    for i, ord_obj in enumerate(orders, start=1):
        order_id = ord_obj["order_id"]
        order_amt = ord_obj["order_amount"]
        order_time = datetime.strptime(ord_obj["created_at"], "%Y-%m-%d %H:%M:%S")

        method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
        pay_time = order_time + timedelta(seconds=random.randint(10, 300))
        
        # Anomaly checks
        if order_id in partial_payment_order_ids:
            pay_amt = round(order_amt * 0.6, 2)
            gt_type = "PARTIAL_PAYMENT"
        elif order_id in overpayment_order_ids:
            pay_amt = round(order_amt * 1.2, 2)
            gt_type = "OVERPAYMENT"
        else:
            pay_amt = order_amt
            gt_type = None

        payment_id_counter += 1
        pay_id = f"pay_live_{payment_id_counter}"
        
        # Fee anomaly check
        if i in fee_anomaly_indices:
            fee_amount = round(pay_amt * 0.07, 2)  # 7% abnormal fee!
            tax_amount = round(fee_amount * 0.18, 2)
            gt_type = "FEE_ANOMALY"
        else:
            fee_amount, tax_amount = calculate_standard_fee(pay_amt, method)

        pay_status = "CAPTURED"
        if i in refund_mismatch_indices:
            pay_status = "REFUNDED"
            gt_type = "REFUND_MISMATCH"

        p_entry = {
            "payment_id": pay_id,
            "order_id": order_id,
            "payment_method": method,
            "payment_amount": pay_amt,
            "fee_amount": fee_amount,
            "tax_amount": tax_amount,
            "status": pay_status,
            "gateway_ref": f"gw_ref_{random.randint(100000, 999999)}",
            "transaction_time": pay_time.strftime("%Y-%m-%d %H:%M:%S"),
            "settlement_status": "PENDING"
        }
        payments.append(p_entry)
        payment_records_map[pay_id] = p_entry

        if gt_type == "PARTIAL_PAYMENT":
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "PARTIAL_PAYMENT",
                "severity": "HIGH",
                "order_id": order_id,
                "payment_id": pay_id,
                "settlement_id": None,
                "invoice_id": None,
                "discrepancy_amount": round(order_amt - pay_amt, 2),
                "description": f"Order {order_id} of ₹{order_amt} received only partial payment ₹{pay_amt}."
            })
        elif gt_type == "OVERPAYMENT":
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "OVERPAYMENT",
                "severity": "MEDIUM",
                "order_id": order_id,
                "payment_id": pay_id,
                "settlement_id": None,
                "invoice_id": None,
                "discrepancy_amount": round(pay_amt - order_amt, 2),
                "description": f"Order {order_id} of ₹{order_amt} received excess payment ₹{pay_amt}."
            })
        elif gt_type == "FEE_ANOMALY":
            std_fee, _ = calculate_standard_fee(pay_amt, method)
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "FEE_ANOMALY",
                "severity": "HIGH",
                "order_id": order_id,
                "payment_id": pay_id,
                "settlement_id": None,
                "invoice_id": None,
                "discrepancy_amount": round(fee_amount - std_fee, 2),
                "description": f"Excessive fee charged on {method} payment {pay_id}: expected ₹{std_fee}, actual charged ₹{fee_amount} (7% rate)."
            })

        # Inject Duplicate Payments
        if order_id in duplicate_payment_order_ids:
            payment_id_counter += 1
            dup_pay_id = f"pay_live_{payment_id_counter}"
            dup_p_entry = {
                "payment_id": dup_pay_id,
                "order_id": order_id,
                "payment_method": method,
                "payment_amount": pay_amt,
                "fee_amount": fee_amount,
                "tax_amount": tax_amount,
                "status": "CAPTURED",
                "gateway_ref": f"gw_ref_dup_{random.randint(100000, 999999)}",
                "transaction_time": (pay_time + timedelta(seconds=120)).strftime("%Y-%m-%d %H:%M:%S"),
                "settlement_status": "PENDING"
            }
            payments.append(dup_p_entry)
            payment_records_map[dup_pay_id] = dup_p_entry
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "DUPLICATE_PAYMENT",
                "severity": "CRITICAL",
                "order_id": order_id,
                "payment_id": dup_pay_id,
                "settlement_id": None,
                "invoice_id": None,
                "discrepancy_amount": pay_amt,
                "description": f"Order {order_id} has duplicate captured payment {dup_pay_id} alongside {pay_id}."
            })

    # Inject 15 Payments Without Order (Ghost payments) to bring payment count to exact 540!
    # Currently payments count = 500 + 20 (duplicates) = 520.
    # 520 + 20 ghost payments = 540 payments total.
    for g_idx in range(1, 21):
        payment_id_counter += 1
        ghost_pay_id = f"pay_ghost_{payment_id_counter}"
        ghost_order_id = f"ord_ghost_{9000 + g_idx}"
        ghost_amt = float(random.randint(500, 5000))
        g_method = random.choice(PAYMENT_METHODS)
        g_fee, g_tax = calculate_standard_fee(ghost_amt, g_method)
        g_time = get_random_timestamp((5, 45))

        p_entry = {
            "payment_id": ghost_pay_id,
            "order_id": ghost_order_id,
            "payment_method": g_method,
            "payment_amount": ghost_amt,
            "fee_amount": g_fee,
            "tax_amount": g_tax,
            "status": "CAPTURED",
            "gateway_ref": f"gw_ref_ghost_{random.randint(100000, 999999)}",
            "transaction_time": g_time.strftime("%Y-%m-%d %H:%M:%S"),
            "settlement_status": "PENDING"
        }
        payments.append(p_entry)
        payment_records_map[ghost_pay_id] = p_entry

        if g_idx <= 15:
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "PAYMENT_WITHOUT_ORDER",
                "severity": "HIGH",
                "order_id": ghost_order_id,
                "payment_id": ghost_pay_id,
                "settlement_id": None,
                "invoice_id": None,
                "discrepancy_amount": ghost_amt,
                "description": f"Payment {ghost_pay_id} captured for non-existent order {ghost_order_id}."
            })

    # Select 15 payments for Missing Settlements
    all_payment_ids = [p["payment_id"] for p in payments]
    missing_settlement_payment_ids = set(all_payment_ids[150:165])

    for pid in missing_settlement_payment_ids:
        p_obj = payment_records_map[pid]
        ground_truth.append({
            "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
            "exception_type": "MISSING_SETTLEMENT",
            "severity": "CRITICAL",
            "order_id": p_obj["order_id"],
            "payment_id": pid,
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": p_obj["payment_amount"],
            "description": f"Payment {pid} of ₹{p_obj['payment_amount']} captured on {p_obj['transaction_time']} has no corresponding bank settlement record."
        })

    # 3. Generate Settlements
    # Target settlements: 470 records
    # Payments eligible for settlement = 540 total - 15 missing = 525 payments.
    # 10 payments will have duplicate settlement (+10 settlement records).
    # To hit 470 settlements from eligible payments, we group some normal payments or adjust 1-to-1 matching.
    
    settlement_id_counter = 1000
    settled_payment_count = 0

    for i, p_obj in enumerate(payments, start=1):
        pid = p_obj["payment_id"]
        if pid in missing_settlement_payment_ids:
            continue

        p_amt = p_obj["payment_amount"]
        fee = p_obj["fee_amount"]
        tax = p_obj["tax_amount"]
        trans_time = datetime.strptime(p_obj["transaction_time"], "%Y-%m-%d %H:%M:%S")

        settlement_id_counter += 1
        set_id = f"set_live_{settlement_id_counter}"
        utr_counter += 1
        utr = f"RATN000{utr_counter}"

        # Default normal settlement time: T+2 days
        settle_time = trans_time + timedelta(days=2, hours=random.randint(1, 5))
        net_amt = round(p_amt - fee - tax, 2)
        set_status = "SETTLED"

        # Check anomalies
        if i in settlement_mismatch_indices:
            # Gateway under-settled by ₹350
            net_amt = round(net_amt - 350.0, 2)
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "SETTLEMENT_MISMATCH",
                "severity": "HIGH",
                "order_id": p_obj["order_id"],
                "payment_id": pid,
                "settlement_id": set_id,
                "invoice_id": None,
                "discrepancy_amount": 350.0,
                "description": f"Settlement {set_id} net payout ₹{net_amt} does not equal payment net calculation ₹{round(p_amt - fee - tax, 2)} (Shortage ₹350)."
            })
        elif i in delayed_settlement_indices:
            settle_time = trans_time + timedelta(days=12, hours=4)
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "DELAYED_SETTLEMENT",
                "severity": "MEDIUM",
                "order_id": p_obj["order_id"],
                "payment_id": pid,
                "settlement_id": set_id,
                "invoice_id": None,
                "discrepancy_amount": 0.0,
                "description": f"Settlement {set_id} took 12 days to settle (SLA limit 2 days)."
            })
        elif i in refund_mismatch_indices:
            # Payment refunded, but settlement deducted full payment without refund credit reversal
            net_amt = 0.0
            set_status = "REFUND_DEDUCTED_FLAT"
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "REFUND_MISMATCH",
                "severity": "HIGH",
                "order_id": p_obj["order_id"],
                "payment_id": pid,
                "settlement_id": set_id,
                "invoice_id": None,
                "discrepancy_amount": p_amt,
                "description": f"Refund mismatch on payment {pid}: full refund issued but settlement deduction mismatch."
            })

        s_entry = {
            "settlement_id": set_id,
            "utr": utr,
            "payment_id": pid,
            "gross_amount": p_amt,
            "fee_amount": fee,
            "tax_amount": tax,
            "net_amount": net_amt,
            "bank_account": BANK_ACC,
            "settlement_time": settle_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": set_status
        }
        settlements.append(s_entry)
        p_obj["settlement_status"] = "SETTLED"
        settled_payment_count += 1

        # Duplicate settlement injection (10 cases)
        if i in duplicate_settlement_indices:
            settlement_id_counter += 1
            dup_set_id = f"set_live_dup_{settlement_id_counter}"
            utr_counter += 1
            dup_utr = f"RATN000{utr_counter}"
            dup_s_entry = {
                "settlement_id": dup_set_id,
                "utr": dup_utr,
                "payment_id": pid,
                "gross_amount": p_amt,
                "fee_amount": fee,
                "tax_amount": tax,
                "net_amount": net_amt,
                "bank_account": BANK_ACC,
                "settlement_time": (settle_time + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SETTLED_DUPLICATE"
            }
            settlements.append(dup_s_entry)
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "DUPLICATE_SETTLEMENT",
                "severity": "CRITICAL",
                "order_id": p_obj["order_id"],
                "payment_id": pid,
                "settlement_id": dup_set_id,
                "invoice_id": None,
                "discrepancy_amount": net_amt,
                "description": f"Payment {pid} settled twice under settlement {set_id} (UTR {utr}) and duplicate {dup_set_id} (UTR {dup_utr})."
            })

    # To trim total settlements to EXACTLY 470:
    # Right now we generated settlements for all non-missing payments + duplicate settlements.
    # Let's slice/adjust settlements list to exactly 470 records while keeping all anomalies!
    if len(settlements) > 470:
        # Group some normal non-anomaly settlements or trim excess normal ones
        # Find indices of normal settlements
        normal_settlement_indices = [idx for idx, s in enumerate(settlements) if "dup" not in s["settlement_id"] and s["status"] == "SETTLED" and not any(gt.get("settlement_id") == s["settlement_id"] for gt in ground_truth)]
        excess = len(settlements) - 470
        remove_set_ids = set(settlements[i]["settlement_id"] for i in normal_settlement_indices[:excess])
        settlements = [s for s in settlements if s["settlement_id"] not in remove_set_ids]
    elif len(settlements) < 470:
        # Top up with extra normal settlement entries if needed
        pass

    # 4. Generate Invoices for 500 Orders
    for i, ord_obj in enumerate(orders, start=1):
        order_id = ord_obj["order_id"]
        order_amt = ord_obj["order_amount"]
        order_time = datetime.strptime(ord_obj["created_at"], "%Y-%m-%d %H:%M:%S")

        inv_id = f"inv_2026_{1000 + i}"
        vendor = VENDORS[i % len(VENDORS)]
        
        # Base tax and amounts
        tax_amt = round(order_amt * 0.18, 2)
        net_total = round(order_amt + tax_amt, 2)
        
        ref_order_id = order_id
        inv_status = "ISSUED"

        # Check anomalies
        if i in invoice_mismatch_indices:
            # Invoice amount inflated by ₹1,200
            net_total = round(net_total + 1200.0, 2)
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "INVOICE_MISMATCH",
                "severity": "HIGH",
                "order_id": order_id,
                "payment_id": None,
                "settlement_id": None,
                "invoice_id": inv_id,
                "discrepancy_amount": 1200.0,
                "description": f"Invoice {inv_id} total ₹{net_total} does not match Order {order_id} total + GST ₹{round(order_amt + tax_amt, 2)} (Mismatch ₹1,200)."
            })
        elif i in fuzzy_match_indices:
            # Fuzzy match cases: typo in vendor name or formatting difference in order_id
            if i % 2 == 0:
                vendor = "Razorpay Softwares Private Limited"  # "Softwares" vs "Software"
            else:
                ref_order_id = order_id.replace("ord_live_", "ORD-LIVE-")  # ORD-LIVE-1111 vs ord_live_1111
            ground_truth.append({
                "anomaly_id": f"ANO_{len(ground_truth)+1:03d}",
                "exception_type": "FUZZY_MATCH",
                "severity": "LOW",
                "order_id": order_id,
                "payment_id": None,
                "settlement_id": None,
                "invoice_id": inv_id,
                "discrepancy_amount": 0.0,
                "description": f"Invoice {inv_id} contains fuzzy string mismatch: vendor '{vendor}' or order ref '{ref_order_id}' vs canonical '{order_id}'."
            })

        invoices.append({
            "invoice_id": inv_id,
            "order_id": ref_order_id,
            "vendor_name": vendor,
            "invoice_amount": order_amt,
            "tax_amount": tax_amt,
            "net_total": net_total,
            "invoice_date": order_time.strftime("%Y-%m-%d"),
            "due_date": (order_time + timedelta(days=30)).strftime("%Y-%m-%d"),
            "status": inv_status
        })

    # Save to CSV files
    print(f"[LedgerGuard AI] Writing output files to {OUTPUT_DIR}...")

    # Write orders.csv
    with open(ORDERS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "merchant_id", "customer_id", "customer_name", "customer_email", "customer_phone", "order_amount", "currency", "status", "created_at"])
        writer.writeheader()
        writer.writerows(orders)

    # Write payments.csv
    with open(PAYMENTS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["payment_id", "order_id", "payment_method", "payment_amount", "fee_amount", "tax_amount", "status", "gateway_ref", "transaction_time", "settlement_status"])
        writer.writeheader()
        writer.writerows(payments)

    # Write settlements.csv
    with open(SETTLEMENTS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["settlement_id", "utr", "payment_id", "gross_amount", "fee_amount", "tax_amount", "net_amount", "bank_account", "settlement_time", "status"])
        writer.writeheader()
        writer.writerows(settlements)

    # Write invoices.csv
    with open(INVOICES_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_id", "order_id", "vendor_name", "invoice_amount", "tax_amount", "net_total", "invoice_date", "due_date", "status"])
        writer.writeheader()
        writer.writerows(invoices)

    # Write ground_truth.csv
    with open(GROUND_TRUTH_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["anomaly_id", "exception_type", "severity", "order_id", "payment_id", "settlement_id", "invoice_id", "discrepancy_amount", "description"])
        writer.writeheader()
        writer.writerows(ground_truth)

    # Write ground_truth.json
    with open(GROUND_TRUTH_JSON, mode="w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print("\n[SUCCESS] Synthetic dataset generated successfully!")
    print(f"  - Orders count: {len(orders)}")
    print(f"  - Payments count: {len(payments)}")
    print(f"  - Settlements count: {len(settlements)}")
    print(f"  - Invoices count: {len(invoices)}")
    print(f"  - Injected Ground-Truth Anomalies: {len(ground_truth)}")

if __name__ == "__main__":
    main()
