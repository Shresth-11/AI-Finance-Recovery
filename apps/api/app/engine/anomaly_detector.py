import numpy as np
from typing import List, Dict
from sklearn.ensemble import IsolationForest

def detect_fee_anomalies(payments: List[Dict]) -> List[Dict]:
    """
    Uses scikit-learn IsolationForest & domain MDR rules to detect anomalous fee charges.
    Returns list of payments that exhibit abnormal fee charges.
    """
    if not payments:
        return []

    anomalous_payments = []
    
    # Feature preparation for ML model
    features = []
    valid_indices = []

    for idx, p in enumerate(payments):
        amt = float(p.get("payment_amount", 0.0))
        fee = float(p.get("fee_amount", 0.0))
        method = str(p.get("payment_method", "UPI")).upper()
        
        if amt <= 0:
            continue
            
        fee_rate = fee / amt
        features.append([amt, fee, fee_rate])
        valid_indices.append(idx)

    if len(features) >= 10:
        X = np.array(features)
        iso = IsolationForest(contamination=0.05, random_state=42)
        preds = iso.fit_predict(X)
    else:
        preds = [1] * len(features)

    for i, idx in enumerate(valid_indices):
        p = payments[idx]
        amt = float(p.get("payment_amount", 0.0))
        fee = float(p.get("fee_amount", 0.0))
        method = str(p.get("payment_method", "UPI")).upper()
        fee_rate = fee / amt if amt > 0 else 0.0

        # Domain MDR rules override
        is_rule_anomaly = False
        if method == "UPI" and fee > 1.0:
            is_rule_anomaly = True  # UPI should have zero/near-zero MDR
        elif method == "CARD" and fee_rate > 0.04:
            is_rule_anomaly = True  # >4% on credit card
        elif method == "WALLET" and fee_rate > 0.04:
            is_rule_anomaly = True  # >4% on wallet
        elif method == "NET_BANKING" and fee > 50.0:
            is_rule_anomaly = True  # Excessive net banking flat fee

        is_ml_anomaly = (preds[i] == -1) and (fee_rate > 0.03)

        if is_rule_anomaly or is_ml_anomaly:
            anomalous_payments.append({
                "payment": p,
                "fee_rate": float(fee_rate),
                "is_rule_anomaly": bool(is_rule_anomaly),
                "is_ml_anomaly": bool(is_ml_anomaly),
                "anomaly_score": 0.92 if is_rule_anomaly else 0.85
            })

    return anomalous_payments
