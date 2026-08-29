from datetime import datetime
from typing import List, Dict, Tuple

from app.engine.exact_matcher import match_orders_and_payments, match_payments_and_settlements, build_dict_index
from app.engine.fuzzy_matcher import fuzzy_match_order_invoice
from app.engine.anomaly_detector import detect_fee_anomalies
from app.engine.severity_scorer import calculate_severity
from app.engine.priority_scorer import calculate_priority_score
from app.engine.explanation_generator import generate_evidence_payload

def run_reconciliation_rules(
    orders: List[Dict],
    payments: List[Dict],
    settlements: List[Dict],
    invoices: List[Dict]
) -> Dict:
    """
    Orchestrates all 12 rule checks and produces reconciled matches + exception list with evidence cards.
    """
    exceptions = []
    evidence_list = []
    
    # 1. Exact Matcher for Orders & Payments
    op_results = match_orders_and_payments(orders, payments)
    
    # 2. Exact Matcher for Payments & Settlements
    ps_results = match_payments_and_settlements(payments, settlements)

    # -------------------------------------------------------------
    # Rule 1: Missing Payment (Orders without payments)
    # -------------------------------------------------------------
    for o in op_results["missing_payments"]:
        disc = float(o.get("order_amount", 0.0))
        sev = calculate_severity("MISSING_PAYMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("MISSING_PAYMENT", order=o, discrepancy_amount=disc)
        
        exceptions.append({
            "exception_type": "MISSING_PAYMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": o.get("order_id"),
            "payment_id": None,
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 1.0,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 2: Payment Without Order (Payments referencing ghost orders)
    # -------------------------------------------------------------
    for p in op_results["payments_without_orders"]:
        disc = float(p.get("payment_amount", 0.0))
        sev = calculate_severity("PAYMENT_WITHOUT_ORDER", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("PAYMENT_WITHOUT_ORDER", payment=p, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "PAYMENT_WITHOUT_ORDER",
            "severity": sev,
            "priority_score": prio,
            "order_id": p.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 1.0,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 3: Duplicate Payment (Multiple captured payments for single order)
    # -------------------------------------------------------------
    for item in op_results["duplicate_payments"]:
        o = item["order"]
        pays = item["payments"]
        dup_p = pays[1]  # Second captured payment
        disc = float(dup_p.get("payment_amount", 0.0))
        sev = calculate_severity("DUPLICATE_PAYMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("DUPLICATE_PAYMENT", order=o, payment=dup_p, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "DUPLICATE_PAYMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": o.get("order_id"),
            "payment_id": dup_p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 0.98,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 4: Partial Payment
    # -------------------------------------------------------------
    for item in op_results["partial_payments"]:
        o = item["order"]
        p = item["payments"][0]
        disc = item["discrepancy"]
        sev = calculate_severity("PARTIAL_PAYMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("PARTIAL_PAYMENT", order=o, payment=p, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "PARTIAL_PAYMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": o.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 1.0,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 5: Overpayment
    # -------------------------------------------------------------
    for item in op_results["overpayments"]:
        o = item["order"]
        p = item["payments"][0]
        disc = item["discrepancy"]
        sev = calculate_severity("OVERPAYMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("OVERPAYMENT", order=o, payment=p, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "OVERPAYMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": o.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 1.0,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 6: Settlement Mismatch
    # -------------------------------------------------------------
    for item in ps_results["settlement_mismatches"]:
        p = item["payment"]
        s = item["settlement"]
        disc = item["discrepancy"]
        sev = calculate_severity("SETTLEMENT_MISMATCH", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("SETTLEMENT_MISMATCH", payment=p, settlement=s, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "SETTLEMENT_MISMATCH",
            "severity": sev,
            "priority_score": prio,
            "order_id": p.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": s.get("settlement_id"),
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 0.95,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 7: Missing Settlement
    # -------------------------------------------------------------
    for p in ps_results["missing_settlements"]:
        disc = float(p.get("payment_amount", 0.0))
        sev = calculate_severity("MISSING_SETTLEMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("MISSING_SETTLEMENT", payment=p, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "MISSING_SETTLEMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": p.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 1.0,
            "evidence": ev
        })

    # -------------------------------------------------------------
    # Rule 8: Delayed Settlement (SLA delay > 5 days) & Rule 9: Duplicate Settlement & Rule 10: Refund Mismatch
    # -------------------------------------------------------------
    for item in ps_results["duplicate_settlements"]:
        p = item["payment"]
        s_dup = item["settlements"][1]
        disc = float(s_dup.get("net_amount", 0.0))
        sev = calculate_severity("DUPLICATE_SETTLEMENT", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("DUPLICATE_SETTLEMENT", payment=p, settlement=s_dup, discrepancy_amount=disc)

        exceptions.append({
            "exception_type": "DUPLICATE_SETTLEMENT",
            "severity": sev,
            "priority_score": prio,
            "order_id": p.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": s_dup.get("settlement_id"),
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": 0.99,
            "evidence": ev
        })

    for s in settlements:
        status = str(s.get("status", ""))
        pid = s.get("payment_id")
        p_list = [p for p in payments if p.get("payment_id") == pid]
        p = p_list[0] if p_list else {}

        if "REFUND" in status or p.get("status") == "REFUNDED":
            disc = float(s.get("gross_amount", 0.0))
            sev = calculate_severity("REFUND_MISMATCH", disc)
            prio = calculate_priority_score(sev, disc)
            ev = generate_evidence_payload("REFUND_MISMATCH", payment=p, settlement=s, discrepancy_amount=disc)

            exceptions.append({
                "exception_type": "REFUND_MISMATCH",
                "severity": sev,
                "priority_score": prio,
                "order_id": p.get("order_id"),
                "payment_id": pid,
                "settlement_id": s.get("settlement_id"),
                "invoice_id": None,
                "discrepancy_amount": disc,
                "ai_confidence_score": 0.90,
                "evidence": ev
            })

    # Check delayed settlements
    for s in settlements:
        s_time_str = s.get("settlement_time")
        pid = s.get("payment_id")
        p_list = [p for p in payments if p.get("payment_id") == pid]
        if p_list and s_time_str and p_list[0].get("transaction_time"):
            try:
                t1 = datetime.strptime(p_list[0]["transaction_time"], "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(s_time_str, "%Y-%m-%d %H:%M:%S")
                days_diff = (t2 - t1).days
                if days_diff >= 5:
                    sev = calculate_severity("DELAYED_SETTLEMENT", 0.0)
                    prio = calculate_priority_score(sev, 0.0, age_days=days_diff)
                    ev = generate_evidence_payload("DELAYED_SETTLEMENT", payment=p_list[0], settlement=s)

                    exceptions.append({
                        "exception_type": "DELAYED_SETTLEMENT",
                        "severity": sev,
                        "priority_score": prio,
                        "order_id": p_list[0].get("order_id"),
                        "payment_id": pid,
                        "settlement_id": s.get("settlement_id"),
                        "invoice_id": None,
                        "discrepancy_amount": 0.0,
                        "ai_confidence_score": 1.0,
                        "evidence": ev
                    })
            except Exception:
                pass

    # -------------------------------------------------------------
    # Rule 11: Invoice Mismatch & Rule 12: Fuzzy Match Checks
    # -------------------------------------------------------------
    order_map = build_dict_index(orders, "order_id")
    for inv in invoices:
        inv_ord_ref = inv.get("order_id")
        matched_ord = order_map.get(inv_ord_ref, [None])[0]

        if matched_ord:
            # Check Invoice amount mismatch vs Order + GST
            ord_amt = float(matched_ord.get("order_amount", 0.0))
            inv_net = float(inv.get("net_total", 0.0))
            expected_net = round(ord_amt * 1.18, 2)

            if abs(inv_net - expected_net) >= 1.0 and abs(inv_net - ord_amt) >= 1.0:
                disc = round(abs(inv_net - expected_net), 2)
                sev = calculate_severity("INVOICE_MISMATCH", disc)
                prio = calculate_priority_score(sev, disc)
                ev = generate_evidence_payload("INVOICE_MISMATCH", order=matched_ord, invoice=inv, discrepancy_amount=disc)

                exceptions.append({
                    "exception_type": "INVOICE_MISMATCH",
                    "severity": sev,
                    "priority_score": prio,
                    "order_id": matched_ord.get("order_id"),
                    "payment_id": None,
                    "settlement_id": None,
                    "invoice_id": inv.get("invoice_id"),
                    "discrepancy_amount": disc,
                    "ai_confidence_score": 0.95,
                    "evidence": ev
                })
        else:
            # Fuzzy match evaluation
            for o in orders:
                fuzzy_res = fuzzy_match_order_invoice(o, inv)
                if fuzzy_res["match_method"] == "FUZZY":
                    conf = fuzzy_res["confidence_score"]
                    # If match confidence is < 85%, route to manual review exception
                    if conf < 85.0:
                        sev = "LOW"
                        prio = calculate_priority_score(sev, 0.0, confidence_score=conf/100.0)
                        ev = generate_evidence_payload("FUZZY_MATCH", order=o, invoice=inv, details=fuzzy_res)

                        exceptions.append({
                            "exception_type": "FUZZY_MATCH",
                            "severity": sev,
                            "priority_score": prio,
                            "order_id": o.get("order_id"),
                            "payment_id": None,
                            "settlement_id": None,
                            "invoice_id": inv.get("invoice_id"),
                            "discrepancy_amount": 0.0,
                            "ai_confidence_score": conf / 100.0,
                            "evidence": ev
                        })
                    break

    # -------------------------------------------------------------
    # Rule 12: Fee Anomalies (scikit-learn IsolationForest & MDR rules)
    # -------------------------------------------------------------
    fee_anomalies = detect_fee_anomalies(payments)
    for item in fee_anomalies:
        p = item["payment"]
        fee = float(p.get("fee_amount", 0.0))
        amt = float(p.get("payment_amount", 1.0))
        std_fee = amt * 0.02 if p.get("payment_method") == "CARD" else 0.0
        disc = round(abs(fee - std_fee), 2)
        sev = calculate_severity("FEE_ANOMALY", disc)
        prio = calculate_priority_score(sev, disc)
        ev = generate_evidence_payload("FEE_ANOMALY", payment=p, discrepancy_amount=disc, details=item)

        exceptions.append({
            "exception_type": "FEE_ANOMALY",
            "severity": sev,
            "priority_score": prio,
            "order_id": p.get("order_id"),
            "payment_id": p.get("payment_id"),
            "settlement_id": None,
            "invoice_id": None,
            "discrepancy_amount": disc,
            "ai_confidence_score": item["anomaly_score"],
            "evidence": ev
        })

    # Summary Stats
    total_orders = len(orders)
    total_payments = len(payments)
    total_settlements = len(settlements)
    total_invoices = len(invoices)
    total_exceptions = len(exceptions)
    unreconciled_amount = round(sum(e["discrepancy_amount"] for e in exceptions), 2)

    return {
        "summary": {
            "total_orders": total_orders,
            "total_payments": total_payments,
            "total_settlements": total_settlements,
            "total_invoices": total_invoices,
            "total_exceptions": total_exceptions,
            "unreconciled_amount": unreconciled_amount,
            "reconciliation_rate_pct": round(((total_orders - total_exceptions) / max(1, total_orders)) * 100, 2)
        },
        "exceptions": exceptions
    }
