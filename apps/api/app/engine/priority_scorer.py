def calculate_priority_score(
    severity: str,
    discrepancy_amount: float,
    age_days: int = 0,
    confidence_score: float = 1.0,
    is_unresolved: bool = True
) -> float:
    """
    Computes a composite priority score (0.0 to 100.0).
    Higher scores indicate urgent finance officer action required.
    """
    # 1. Base Severity Points (max 40 pts)
    severity_weights = {
        "CRITICAL": 40.0,
        "HIGH": 30.0,
        "MEDIUM": 20.0,
        "LOW": 10.0
    }
    sev_score = severity_weights.get(severity.upper(), 10.0)

    # 2. Discrepancy Amount Points (max 30 pts)
    amt_abs = abs(float(discrepancy_amount or 0.0))
    amt_score = min(30.0, (amt_abs / 50000.0) * 30.0)

    # 3. Issue Age Points (max 20 pts)
    age_score = min(20.0, (max(0, age_days) / 30.0) * 20.0)

    # 4. Uncertainty Penalty/Boost (max 10 pts)
    # Lower matching confidence means human verification is urgent
    conf_score = (1.0 - max(0.0, min(1.0, confidence_score))) * 10.0

    total_priority = sev_score + amt_score + age_score + conf_score
    if not is_unresolved:
        total_priority *= 0.2  # De-prioritize resolved items

    return round(min(100.0, total_priority), 2)
