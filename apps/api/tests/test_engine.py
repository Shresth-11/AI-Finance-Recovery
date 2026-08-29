import pytest
from app.engine.data_normalizer import normalize_text, normalize_email, normalize_reference_id, normalize_amount
from app.engine.severity_scorer import calculate_severity
from app.engine.priority_scorer import calculate_priority_score
from app.engine.fuzzy_matcher import fuzzy_match_order_invoice, string_similarity
from app.engine.anomaly_detector import detect_fee_anomalies
from app.engine.reconciliation_rules import run_reconciliation_rules

def test_data_normalizer():
    assert normalize_text("  Razorpay Softwares Pvt. Ltd. ") == "razorpay software private limited"
    assert normalize_email(" TEST.User@Example.IN ") == "test.user@example.in"
    assert normalize_reference_id("ord-live-1001") == "ORDLIVE1001"
    assert normalize_amount(1500.456) == 1500.46

def test_severity_scorer():
    assert calculate_severity("DUPLICATE_PAYMENT", 100.0) == "CRITICAL"
    assert calculate_severity("MISSING_SETTLEMENT", 1000.0) == "HIGH"
    assert calculate_severity("PARTIAL_PAYMENT", 4000.0) == "MEDIUM"
    assert calculate_severity("FEE_ANOMALY", 50.0) == "LOW"

def test_priority_scorer():
    crit_score = calculate_priority_score("CRITICAL", 60000.0, age_days=10)
    low_score = calculate_priority_score("LOW", 100.0, age_days=1)
    assert crit_score > low_score
    assert crit_score <= 100.0

def test_fuzzy_matcher_exact_and_fuzzy():
    order = {"order_id": "ord_live_1001", "order_amount": 2500.0}
    invoice_exact = {"order_id": "ORD-LIVE-1001", "invoice_amount": 2500.0, "vendor_name": "Razorpay Software Private Limited"}
    
    res_exact = fuzzy_match_order_invoice(order, invoice_exact)
    assert res_exact["is_match"] is True
    assert res_exact["confidence_score"] == 100.0
    assert res_exact["match_method"] == "EXACT"

    invoice_fuzzy_low = {"order_id": "ord_live_9999", "invoice_amount": 2500.0, "vendor_name": "Unknown Vendor"}
    res_low = fuzzy_match_order_invoice(order, invoice_fuzzy_low)
    # Low confidence match must NOT be silently merged
    assert res_low["is_match"] is False
    assert res_low["confidence_score"] < 85.0

def test_fee_anomaly_detector():
    payments = [
        {"payment_id": "p1", "payment_amount": 1000.0, "fee_amount": 0.0, "payment_method": "UPI"},
        {"payment_id": "p2", "payment_amount": 1000.0, "fee_amount": 70.0, "payment_method": "UPI"},  # 7% fee on UPI!
        {"payment_id": "p3", "payment_amount": 5000.0, "fee_amount": 100.0, "payment_method": "CARD"}
    ]
    anomalies = detect_fee_anomalies(payments)
    assert len(anomalies) >= 1
    assert anomalies[0]["payment"]["payment_id"] == "p2"

def test_all_12_reconciliation_rules():
    orders = [
        {"order_id": "ord_1", "order_amount": 1000.0, "created_at": "2026-07-01 10:00:00"}, # Normal
        {"order_id": "ord_2", "order_amount": 2000.0, "created_at": "2026-07-01 10:00:00"}, # Missing Payment
        {"order_id": "ord_3", "order_amount": 3000.0, "created_at": "2026-07-01 10:00:00"}, # Partial Payment
        {"order_id": "ord_4", "order_amount": 1000.0, "created_at": "2026-07-01 10:00:00"}, # Overpayment
    ]
    payments = [
        {"payment_id": "pay_1", "order_id": "ord_1", "payment_amount": 1000.0, "fee_amount": 20.0, "tax_amount": 3.6, "payment_method": "CARD", "status": "CAPTURED", "transaction_time": "2026-07-01 10:01:00"},
        {"payment_id": "pay_3", "order_id": "ord_3", "payment_amount": 1500.0, "fee_amount": 0.0, "tax_amount": 0.0, "payment_method": "UPI", "status": "CAPTURED", "transaction_time": "2026-07-01 10:01:00"},
        {"payment_id": "pay_4", "order_id": "ord_4", "payment_amount": 1500.0, "fee_amount": 0.0, "tax_amount": 0.0, "payment_method": "UPI", "status": "CAPTURED", "transaction_time": "2026-07-01 10:01:00"},
        {"payment_id": "pay_ghost", "order_id": "ord_ghost", "payment_amount": 500.0, "fee_amount": 0.0, "tax_amount": 0.0, "payment_method": "UPI", "status": "CAPTURED", "transaction_time": "2026-07-01 10:01:00"}, # Payment Without Order
    ]
    settlements = [
        {"settlement_id": "set_1", "utr": "UTR1001", "payment_id": "pay_1", "gross_amount": 1000.0, "fee_amount": 20.0, "tax_amount": 3.6, "net_amount": 976.4, "settlement_time": "2026-07-03 10:00:00", "status": "SETTLED"}
    ]
    invoices = [
        {"invoice_id": "inv_1", "order_id": "ord_1", "vendor_name": "Razorpay Software Private Limited", "invoice_amount": 1000.0, "tax_amount": 180.0, "net_total": 1180.0}
    ]

    res = run_reconciliation_rules(orders, payments, settlements, invoices)
    assert res["summary"]["total_orders"] == 4
    assert res["summary"]["total_exceptions"] > 0
