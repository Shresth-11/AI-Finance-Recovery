from typing import List, Dict

def build_dict_index(records: List[Dict], key_field: str) -> Dict[str, List[Dict]]:
    index = {}
    for r in records:
        val = str(r.get(key_field, "")).strip()
        if not val:
            continue
        if val not in index:
            index[val] = []
        index[val].append(r)
    return index

def match_orders_and_payments(orders: List[Dict], payments: List[Dict]) -> Dict:
    order_map = build_dict_index(orders, "order_id")
    payment_map = build_dict_index(payments, "order_id")

    matched_orders = {}
    missing_payments = []
    duplicate_payments = []
    payments_without_orders = []
    partial_payments = []
    overpayments = []

    # Process payments for known orders
    for order_id, o_list in order_map.items():
        order = o_list[0]
        p_list = payment_map.get(order_id, [])

        if not p_list:
            missing_payments.append(order)
            continue

        # Check multiple payments (duplicates)
        if len(p_list) > 1:
            duplicate_payments.append({
                "order": order,
                "payments": p_list
            })

        # Calculate total captured payment amount
        tot_pay_amt = sum(float(p.get("payment_amount", 0.0)) for p in p_list if p.get("status") in ["CAPTURED", "SETTLED", "PAID"])
        ord_amt = float(order.get("order_amount", 0.0))

        if abs(tot_pay_amt - ord_amt) < 0.01:
            matched_orders[order_id] = {
                "order": order,
                "payments": p_list,
                "match_type": "EXACT"
            }
        elif tot_pay_amt < ord_amt and tot_pay_amt > 0:
            partial_payments.append({
                "order": order,
                "payments": p_list,
                "discrepancy": round(ord_amt - tot_pay_amt, 2)
            })
        elif tot_pay_amt > ord_amt:
            overpayments.append({
                "order": order,
                "payments": p_list,
                "discrepancy": round(tot_pay_amt - ord_amt, 2)
            })

    # Check payments referencing missing/non-existent orders
    for order_id, p_list in payment_map.items():
        if order_id not in order_map:
            for p in p_list:
                payments_without_orders.append(p)

    return {
        "matched_orders": matched_orders,
        "missing_payments": missing_payments,
        "duplicate_payments": duplicate_payments,
        "payments_without_orders": payments_without_orders,
        "partial_payments": partial_payments,
        "overpayments": overpayments
    }

def match_payments_and_settlements(payments: List[Dict], settlements: List[Dict]) -> Dict:
    settlement_map = build_dict_index(settlements, "payment_id")
    
    matched_settlements = {}
    missing_settlements = []
    duplicate_settlements = []
    settlement_mismatches = []
    delayed_settlements = []

    for p in payments:
        pid = str(p.get("payment_id", "")).strip()
        s_list = settlement_map.get(pid, [])

        if not s_list:
            missing_settlements.append(p)
            continue

        if len(s_list) > 1:
            duplicate_settlements.append({
                "payment": p,
                "settlements": s_list
            })

        s = s_list[0]
        p_amt = float(p.get("payment_amount", 0.0))
        fee = float(p.get("fee_amount", 0.0))
        tax = float(p.get("tax_amount", 0.0))
        expected_net = round(p_amt - fee - tax, 2)
        actual_net = round(float(s.get("net_amount", 0.0)), 2)

        if abs(expected_net - actual_net) >= 0.01:
            settlement_mismatches.append({
                "payment": p,
                "settlement": s,
                "expected_net": expected_net,
                "actual_net": actual_net,
                "discrepancy": round(abs(expected_net - actual_net), 2)
            })
        else:
            matched_settlements[pid] = {
                "payment": p,
                "settlement": s
            }

    return {
        "matched_settlements": matched_settlements,
        "missing_settlements": missing_settlements,
        "duplicate_settlements": duplicate_settlements,
        "settlement_mismatches": settlement_mismatches
    }
