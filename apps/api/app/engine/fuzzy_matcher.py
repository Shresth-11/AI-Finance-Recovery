import difflib
from datetime import datetime
from app.engine.data_normalizer import normalize_text, normalize_email, normalize_reference_id, normalize_amount

def string_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def fuzzy_match_order_invoice(order_dict: dict, invoice_dict: dict) -> dict:
    """
    Evaluates fuzzy match between an Order and an Invoice.
    Returns: {
        'is_match': bool,
        'confidence_score': float (0-100),
        'match_method': 'EXACT' | 'FUZZY' | 'NONE',
        'reasons': list
    }
    """
    raw_ord_id = str(order_dict.get("order_id", ""))
    raw_inv_ord_ref = str(invoice_dict.get("order_id", ""))

    norm_ord_id = normalize_reference_id(raw_ord_id)
    norm_inv_ord_ref = normalize_reference_id(raw_inv_ord_ref)

    # 1. Exact ID Match
    if norm_ord_id and norm_ord_id == norm_inv_ord_ref:
        return {
            "is_match": True,
            "confidence_score": 100.0,
            "match_method": "EXACT",
            "reasons": ["Exact Order ID match"]
        }

    # 2. Fuzzy Match Scoring
    score = 0.0
    reasons = []

    # Reference ID Similarity
    id_sim = string_similarity(norm_ord_id, norm_inv_ord_ref)
    if id_sim > 0.8:
        score += id_sim * 50.0
        reasons.append(f"High reference similarity ({id_sim*100:.1f}%)")
    elif id_sim > 0.5:
        score += id_sim * 25.0
        reasons.append(f"Moderate reference similarity ({id_sim*100:.1f}%)")

    # Amount Match
    ord_amt = normalize_amount(order_dict.get("order_amount", 0.0))
    inv_amt = normalize_amount(invoice_dict.get("invoice_amount", 0.0))
    if ord_amt == inv_amt:
        score += 30.0
        reasons.append("Exact invoice base amount match")
    elif abs(ord_amt - inv_amt) < (ord_amt * 0.05):
        score += 15.0
        reasons.append("Invoice amount within 5% tolerance")

    # Vendor Name similarity
    vendor = normalize_text(invoice_dict.get("vendor_name", ""))
    if "razorpay" in vendor or "paytm" in vendor or "phonepe" in vendor:
        score += 20.0
        reasons.append("Known payment gateway vendor match")

    confidence = round(min(100.0, score), 1)

    # Low-confidence threshold rule: Matches below 85.0 confidence are NOT silently merged!
    # They are flagged as manual review exceptions.
    is_match = confidence >= 85.0

    return {
        "is_match": is_match,
        "confidence_score": confidence,
        "match_method": "FUZZY" if confidence > 0 else "NONE",
        "reasons": reasons
    }
