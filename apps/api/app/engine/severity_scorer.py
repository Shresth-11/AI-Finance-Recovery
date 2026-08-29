from typing import Dict, Any

DEFAULT_THRESHOLDS = {
    "CRITICAL_AMOUNT": 50000.0,
    "HIGH_AMOUNT": 10000.0,
    "LOW_AMOUNT": 500.0
}

def calculate_severity(
    exception_type: str,
    discrepancy_amount: float,
    thresholds: Dict[str, float] = None
) -> str:
    cfg = thresholds if thresholds else DEFAULT_THRESHOLDS
    disc_abs = abs(float(discrepancy_amount or 0.0))

    # Severe types always default to CRITICAL or HIGH
    critical_types = {"DUPLICATE_PAYMENT", "DUPLICATE_SETTLEMENT"}
    high_types = {"MISSING_SETTLEMENT", "PAYMENT_WITHOUT_ORDER", "MISSING_PAYMENT"}

    if exception_type in critical_types or disc_abs >= cfg["CRITICAL_AMOUNT"]:
        return "CRITICAL"
    elif exception_type in high_types or disc_abs >= cfg["HIGH_AMOUNT"]:
        return "HIGH"
    elif exception_type in {"PARTIAL_PAYMENT", "OVERPAYMENT", "INVOICE_MISMATCH", "DELAYED_SETTLEMENT", "REFUND_MISMATCH", "SETTLEMENT_MISMATCH"} or disc_abs >= cfg["LOW_AMOUNT"]:
        return "MEDIUM"
    else:
        return "LOW"
