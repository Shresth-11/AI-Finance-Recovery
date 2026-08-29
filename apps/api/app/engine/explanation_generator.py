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
    Generates structured Evidence payload with human readable summary,
    side-by-side comparison JSON data, and actionable finance officer recommendations.
    """
    side_by_side = {}
    summary = ""
    remediation = ""

    if exception_type == "MISSING_SETTLEMENT":
        summary = f"Payment {payment.get('payment_id')} of ₹{payment.get('payment_amount')} captured on {payment.get('transaction_time')} has no corresponding bank settlement record after 48+ hours."
        side_by_side = {
            "Payment Status": payment.get("status"),
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Gateway Ref": payment.get("gateway_ref"),
            "Expected Settlement Net": f"₹{round(payment.get('payment_amount', 0) - payment.get('fee_amount', 0) - payment.get('tax_amount', 0), 2)}",
            "Actual Settlement Record": "NOT FOUND in Settlement Feeds"
        }
        remediation = "Raise ticket with Gateway Support citing Gateway Reference to confirm UTR payout status."

    elif exception_type == "DUPLICATE_PAYMENT":
        summary = f"Order {order.get('order_id')} of ₹{order.get('order_amount')} has multiple successful payment charges recorded."
        side_by_side = {
            "Order ID": order.get("order_id"),
            "Order Amount": f"₹{order.get('order_amount')}",
            "Duplicate Payment ID": payment.get("payment_id"),
            "Duplicate Payment Amount": f"₹{payment.get('payment_amount')}",
            "Gateway Ref": payment.get("gateway_ref")
        }
        remediation = f"Initiate customer refund for duplicate transaction {payment.get('payment_id')} via payment gateway console."

    elif exception_type == "PAYMENT_WITHOUT_ORDER":
        summary = f"Payment {payment.get('payment_id')} of ₹{payment.get('payment_amount')} captured with order ID '{payment.get('order_id')}' which does not exist in Orders DB."
        side_by_side = {
            "Payment ID": payment.get("payment_id"),
            "Captured Order ID": payment.get("order_id"),
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Orders Database Status": "Order Reference Missing"
        }
        remediation = "Verify customer order checkout logs or map unlinked payment to manual order entry."

    elif exception_type == "PARTIAL_PAYMENT":
        summary = f"Order {order.get('order_id')} of ₹{order.get('order_amount')} received partial payment of ₹{payment.get('payment_amount')} (Shortfall: ₹{discrepancy_amount})."
        side_by_side = {
            "Order ID": order.get("order_id"),
            "Order Amount": f"₹{order.get('order_amount')}",
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Unpaid Balance": f"₹{discrepancy_amount}"
        }
        remediation = "Notify customer of outstanding balance or issue partial payment invoice."

    elif exception_type == "OVERPAYMENT":
        summary = f"Order {order.get('order_id')} of ₹{order.get('order_amount')} received excess payment of ₹{payment.get('payment_amount')} (Excess: ₹{discrepancy_amount})."
        side_by_side = {
            "Order ID": order.get("order_id"),
            "Order Amount": f"₹{order.get('order_amount')}",
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Overpayment Credit": f"₹{discrepancy_amount}"
        }
        remediation = "Credit overpayment to customer account balance or process partial refund."

    elif exception_type == "SETTLEMENT_MISMATCH":
        summary = f"Settlement {settlement.get('settlement_id')} net payout ₹{settlement.get('net_amount')} does not match calculated payment net amount."
        side_by_side = {
            "Payment ID": payment.get("payment_id"),
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Fee & Tax Deducted": f"₹{round(payment.get('fee_amount', 0) + payment.get('tax_amount', 0), 2)}",
            "Expected Net Payout": f"₹{round(payment.get('payment_amount', 0) - payment.get('fee_amount', 0) - payment.get('tax_amount', 0), 2)}",
            "Actual Settlement Net Payout": f"₹{settlement.get('net_amount')}",
            "Variance": f"₹{discrepancy_amount}"
        }
        remediation = "Reconcile fee deduction statement with bank UTR credit history."

    elif exception_type == "DELAYED_SETTLEMENT":
        summary = f"Settlement {settlement.get('settlement_id')} (UTR: {settlement.get('utr')}) took extended time to settle (SLA SLA limit: 2 days)."
        side_by_side = {
            "Payment Time": payment.get("transaction_time"),
            "Settlement Time": settlement.get("settlement_time"),
            "UTR": settlement.get("utr"),
            "Status": "Settled with SLA Delay"
        }
        remediation = "Log gateway SLA breach for quarterly vendor performance review."

    elif exception_type == "DUPLICATE_SETTLEMENT":
        summary = f"Payment {payment.get('payment_id')} was settled in multiple settlement batches under duplicate UTRs."
        side_by_side = {
            "Payment ID": payment.get("payment_id"),
            "Duplicate Settlement ID": settlement.get("settlement_id"),
            "UTR": settlement.get("utr"),
            "Duplicate Net Payout": f"₹{settlement.get('net_amount')}"
        }
        remediation = "Notify finance audit team of duplicate gateway payout entry."

    elif exception_type == "REFUND_MISMATCH":
        summary = f"Payment {payment.get('payment_id')} status is REFUNDED, but settlement deduction variance detected."
        side_by_side = {
            "Payment ID": payment.get("payment_id"),
            "Payment Status": payment.get("status"),
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Settlement Status": settlement.get("status")
        }
        remediation = "Verify gateway refund credit note against monthly bank settlement ledger."

    elif exception_type == "INVOICE_MISMATCH":
        summary = f"Invoice {invoice.get('invoice_id')} net total ₹{invoice.get('net_total')} does not match Order {order.get('order_id')} total + tax."
        side_by_side = {
            "Invoice ID": invoice.get("invoice_id"),
            "Order ID": order.get("order_id"),
            "Billed Invoice Total": f"₹{invoice.get('net_total')}",
            "Order Amount + GST": f"₹{round(order.get('order_amount', 0) * 1.18, 2)}",
            "Discrepancy": f"₹{discrepancy_amount}"
        }
        remediation = "Request corrected vendor invoice or issue credit note."

    elif exception_type == "FEE_ANOMALY":
        summary = f"Payment {payment.get('payment_id')} charged abnormal fee of ₹{payment.get('fee_amount')} on {payment.get('payment_method')} transaction."
        side_by_side = {
            "Payment ID": payment.get("payment_id"),
            "Payment Method": payment.get("payment_method"),
            "Payment Amount": f"₹{payment.get('payment_amount')}",
            "Fee Charged": f"₹{payment.get('fee_amount')}",
            "Fee Percentage": f"{(payment.get('fee_amount', 0) / payment.get('payment_amount', 1)) * 100:.2f}%"
        }
        remediation = "Claim fee overcharge refund from payment gateway partner."

    elif exception_type == "FUZZY_MATCH":
        summary = f"Invoice {invoice.get('invoice_id')} reference fuzzy match requires human officer verification."
        side_by_side = {
            "Invoice ID": invoice.get("invoice_id"),
            "Invoice Order Ref": invoice.get("order_id"),
            "Matched Order ID": order.get("order_id"),
            "Vendor": invoice.get("vendor_name")
        }
        remediation = "Confirm match accuracy and approve invoice pairing."

    else:
        summary = f"Reconciliation exception detected for entity ID {order.get('order_id') if order else payment.get('payment_id')}."
        side_by_side = details if details else {}
        remediation = "Review exception details and resolve manually."

    return {
        "summary": summary,
        "side_by_side": side_by_side,
        "remediation": remediation,
        "details_json": json.dumps({"side_by_side": side_by_side, "remediation": remediation, "extra": details or {}}, default=str)
    }
