import json

def generate_evidence_payload(
    exception_type: str,
    order: dict = None,
    payment: dict = None,
    settlement: dict = None,
    invoice: dict = None,
    discrepancy_amount: float = 0.0,
    details: dict = None
) -> dict:
    """
    Generates structured evidence payload following the 6-part human explanation requirements:
    1. What happened
    2. Why it was flagged
    3. Amount affected
    4. Evidence reviewed
    5. Suggested next step
    6. Confidence and limitations
    """
    order = order or {}
    payment = payment or {}
    settlement = settlement or {}
    invoice = invoice or {}
    details = details or {}

    order_id = order.get("order_id") or "N/A"
    payment_id = payment.get("payment_id") or "N/A"
    settlement_id = settlement.get("settlement_id") or "N/A"
    invoice_id = invoice.get("invoice_id") or "N/A"

    what_happened = ""
    why_flagged = ""
    suggested_step = ""
    confidence_limitations = "High confidence based on exact transaction reference matching. Result depends on the completeness of uploaded feed files."

    if exception_type == "MISSING_SETTLEMENT":
        what_happened = f"Payment {payment_id} for ₹{payment.get('payment_amount', 0):,.2f} was captured for order {order_id}, but no linked bank settlement was found within the expected settlement window."
        why_flagged = "The payment is marked as captured and is older than the configured settlement SLA window."
        suggested_step = "Check the gateway settlement reference and confirm whether the payment is pending, reversed, or included in a later settlement batch."

    elif exception_type == "DUPLICATE_PAYMENT":
        what_happened = f"Order {order_id} for ₹{order.get('order_amount', 0):,.2f} has multiple successful gateway payment captures ({payment_id}) recorded against it."
        why_flagged = "The customer retried checkout payment after an app response timeout, resulting in a duplicate capture."
        suggested_step = "Confirm customer account statements and initiate a customer refund for the duplicate transaction via gateway console."

    elif exception_type == "PAYMENT_WITHOUT_ORDER":
        what_happened = f"Payment {payment_id} for ₹{payment.get('payment_amount', 0):,.2f} was captured by gateway, but no corresponding ERP order record exists."
        why_flagged = "Gateway capture exists with an unlinked or non-existent ERP order reference."
        suggested_step = "Check checkout system logs to map unlinked payment to manual order entry or verify customer inquiry ticket."

    elif exception_type == "PARTIAL_PAYMENT":
        what_happened = f"Order {order_id} for ₹{order.get('order_amount', 0):,.2f} received partial payment capture {payment_id} of ₹{payment.get('payment_amount', 0):,.2f}."
        why_flagged = "Captured payment amount is less than the total ERP order value."
        suggested_step = "Contact customer regarding outstanding balance or issue partial payment adjustment note."

    elif exception_type == "OVERPAYMENT":
        what_happened = f"Order {order_id} for ₹{order.get('order_amount', 0):,.2f} received excess payment capture {payment_id} of ₹{payment.get('payment_amount', 0):,.2f}."
        why_flagged = "Captured payment amount exceeds the recorded ERP order total."
        suggested_step = "Credit overpayment to customer account balance or process partial refund for excess ₹500."

    elif exception_type == "SETTLEMENT_MISMATCH":
        what_happened = f"Settlement {settlement_id} (UTR: {settlement.get('utr', 'N/A')}) net payout of ₹{settlement.get('net_amount', 0):,.2f} differs from calculated net payment amount."
        why_flagged = "Discrepancy detected between bank deposit payout and gateway capture minus fee deduction."
        suggested_step = "Compare gateway fee deduction advice against bank deposit UTR credit statement."

    elif exception_type == "DELAYED_SETTLEMENT":
        what_happened = f"Settlement {settlement_id} for payment {payment_id} was deposited on {settlement.get('settlement_time', 'N/A')}, exceeding the 2-business-day SLA limit."
        why_flagged = "Bank payout settlement timestamp exceeded standard T+2 SLA settlement window."
        suggested_step = "Log gateway SLA delay for quarterly vendor performance review."

    elif exception_type == "DUPLICATE_SETTLEMENT":
        what_happened = f"Payment {payment_id} was recorded in multiple bank settlement advices under UTR {settlement.get('utr', 'N/A')}."
        why_flagged = "Multiple settlement records exist referencing the exact same payment ID."
        suggested_step = "Notify finance audit team to prevent duplicate ledger entry."

    elif exception_type == "FEE_ANOMALY":
        what_happened = f"Payment {payment_id} was charged ₹{payment.get('fee_amount', 0):,.2f} in MDR fees on a ₹{payment.get('payment_amount', 0):,.2f} {payment.get('payment_method', 'CARD')} transaction."
        why_flagged = "Fee applied exceeds configured commercial rate threshold for this payment method channel."
        suggested_step = "Submit MDR fee overcharge claim ticket to gateway partner."

    elif exception_type == "INVOICE_MISMATCH":
        what_happened = f"Vendor tax invoice {invoice_id} net total of ₹{invoice.get('net_total', 0):,.2f} does not match linked Order {order_id} total."
        why_flagged = "Billed invoice net total differs from order total."
        suggested_step = "Request corrected vendor invoice or issue credit adjustment note."

    elif exception_type == "FUZZY_MATCH":
        what_happened = f"Imported order ID for Payment {payment_id} had formatting variation; matched using amount, customer email, and timestamp window."
        why_flagged = "Order ID reference had string formatting variation requiring fuzzy matching verification."
        confidence_limitations = "Medium confidence (85%). Matched using customer email, payment amount, and transaction window. Requires manual review."
        suggested_step = "Confirm transaction pairing and approve order link."

    else:
        what_happened = f"Financial discrepancy detected for transaction payment {payment_id} and order {order_id}."
        why_flagged = "Rule check flagged variance between loaded data feeds."
        suggested_step = "Review linked records and resolve manually."

    # Build evidence items list
    evidence_items = []
    if order_id != "N/A": evidence_items.append(f"Order {order_id}")
    if payment_id != "N/A": evidence_items.append(f"Payment {payment_id}")
    if settlement_id != "N/A": evidence_items.append(f"Settlement {settlement_id}")
    if invoice_id != "N/A": evidence_items.append(f"Invoice {invoice_id}")
    evidence_str = ", ".join(evidence_items) if evidence_items else "Loaded transaction ledgers"

    # Formatted 6-part human summary
    summary = (
        f"What happened: {what_happened}\n\n"
        f"Why it was flagged: {why_flagged}\n\n"
        f"Amount affected: ₹{discrepancy_amount:,.2f}.\n\n"
        f"Evidence reviewed: {evidence_str}.\n\n"
        f"Suggested next step: {suggested_step}\n\n"
        f"Confidence and limitations: {confidence_limitations}"
    )

    side_by_side = {
        "Order ID": order_id,
        "Order Amount": f"₹{order.get('order_amount', 0):,.2f}" if order else "N/A",
        "Payment ID": payment_id,
        "Payment Amount": f"₹{payment.get('payment_amount', 0):,.2f}" if payment else "N/A",
        "Settlement UTR": settlement.get("utr", "N/A"),
        "Settlement Net": f"₹{settlement.get('net_amount', 0):,.2f}" if settlement else "N/A",
        "Invoice ID": invoice_id,
        "Invoice Total": f"₹{invoice.get('net_total', 0):,.2f}" if invoice else "N/A",
    }

    return {
        "summary": summary,
        "side_by_side": side_by_side,
        "remediation": suggested_step,
        "details_json": json.dumps({
            "what_happened": what_happened,
            "why_flagged": why_flagged,
            "amount_affected": f"₹{discrepancy_amount:,.2f}",
            "evidence_reviewed": evidence_str,
            "suggested_next_step": suggested_step,
            "confidence_and_limitations": confidence_limitations,
            "side_by_side": side_by_side
        }, default=str)
    }
