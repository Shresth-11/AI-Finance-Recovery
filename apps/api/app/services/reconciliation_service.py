import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.base import Order, Payment, Settlement, Invoice, ReconciliationRun, ExceptionRecord, Evidence
from app.engine.reconciliation_rules import run_reconciliation_rules
from app.services.audit_service import log_audit

def execute_reconciliation_run(db: Session) -> dict:
    orders = db.query(Order).all()
    payments = db.query(Payment).all()
    settlements = db.query(Settlement).all()
    invoices = db.query(Invoice).all()

    if not orders and not payments:
        raise HTTPException(status_code=400, detail="No financial records found in database. Load demo dataset or upload CSV files first.")

    run_code = f"RUN_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"
    started_at = datetime.now(timezone.utc)

    # Convert ORM objects to dict lists for pure engine processing
    orders_list = [{
        "id": o.id, "order_id": o.order_id, "merchant_id": o.merchant_id,
        "customer_id": o.customer_id, "customer_name": o.customer_name,
        "customer_email": o.customer_email, "order_amount": o.order_amount,
        "currency": o.currency, "status": o.status,
        "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else None
    } for o in orders]

    payments_list = [{
        "id": p.id, "payment_id": p.payment_id, "order_id": p.order_id,
        "payment_method": p.payment_method, "payment_amount": p.payment_amount,
        "fee_amount": p.fee_amount, "tax_amount": p.tax_amount,
        "status": p.status, "gateway_ref": p.gateway_ref,
        "transaction_time": p.transaction_time.strftime("%Y-%m-%d %H:%M:%S") if p.transaction_time else None
    } for p in payments]

    settlements_list = [{
        "id": s.id, "settlement_id": s.settlement_id, "utr": s.utr,
        "payment_id": s.payment_id, "gross_amount": s.gross_amount,
        "fee_amount": s.fee_amount, "tax_amount": s.tax_amount,
        "net_amount": s.net_amount, "status": s.status,
        "settlement_time": s.settlement_time.strftime("%Y-%m-%d %H:%M:%S") if s.settlement_time else None
    } for s in settlements]

    invoices_list = [{
        "id": i.id, "invoice_id": i.invoice_id, "order_id": i.order_id,
        "vendor_name": i.vendor_name, "invoice_amount": i.invoice_amount,
        "tax_amount": i.tax_amount, "net_total": i.net_total,
        "status": i.status
    } for i in invoices]

    # Execute rules engine
    recon_results = run_reconciliation_rules(orders_list, payments_list, settlements_list, invoices_list)
    summary = recon_results["summary"]
    exceptions_list = recon_results["exceptions"]

    # Clear previous exception runs if re-running
    db.query(ExceptionRecord).delete()
    db.query(Evidence).delete()
    db.commit()

    # Create Reconciliation Run Record
    recon_run = ReconciliationRun(
        run_code=run_code,
        status="COMPLETED",
        total_orders=summary["total_orders"],
        total_payments=summary["total_payments"],
        total_settlements=summary["total_settlements"],
        total_invoices=summary["total_invoices"],
        total_exceptions=summary["total_exceptions"],
        unreconciled_amount=summary["unreconciled_amount"],
        started_at=started_at,
        completed_at=datetime.now(timezone.utc)
    )
    db.add(recon_run)
    db.commit()
    db.refresh(recon_run)

    # Persist Exceptions and Evidence items to DB
    exc_counter = 1000
    for e_dict in exceptions_list:
        exc_counter += 1
        e_code = f"EXC_{exc_counter}"
        exc_record = ExceptionRecord(
            exception_code=e_code,
            run_id=recon_run.id,
            exception_type=e_dict["exception_type"],
            severity=e_dict["severity"],
            status="OPEN",
            order_id=e_dict.get("order_id"),
            payment_id=e_dict.get("payment_id"),
            settlement_id=e_dict.get("settlement_id"),
            invoice_id=e_dict.get("invoice_id"),
            discrepancy_amount=e_dict["discrepancy_amount"],
            ai_confidence_score=e_dict["ai_confidence_score"]
        )
        db.add(exc_record)
        db.commit()
        db.refresh(exc_record)

        # Store Evidence item
        ev_payload = e_dict["evidence"]
        ev_item = Evidence(
            exception_id=exc_record.id,
            evidence_type=e_dict["exception_type"],
            summary=ev_payload["summary"],
            details_json=ev_payload["details_json"]
        )
        db.add(ev_item)

    db.commit()

    log_audit(
        db,
        entity_type="ReconciliationRun",
        action="RUN_RECONCILIATION",
        entity_id=run_code,
        reason=f"Executed automated reconciliation engine over {summary['total_orders']} orders",
        metadata={
            "run_code": run_code,
            "total_exceptions": summary["total_exceptions"],
            "unreconciled_amount": summary["unreconciled_amount"]
        }
    )

    return {
        "message": f"Reconciliation run {run_code} completed successfully.",
        "run_code": run_code,
        "summary": summary
    }

def query_reconciliation_results(
    db: Session,
    severity: str = None,
    exception_type: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    query = db.query(ExceptionRecord)

    if severity:
        query = query.filter(ExceptionRecord.severity == severity.upper())
    if exception_type:
        query = query.filter(ExceptionRecord.exception_type == exception_type.upper())
    if status:
        query = query.filter(ExceptionRecord.status == status.upper())

    total_count = query.count()
    records = query.order_by(ExceptionRecord.id.asc()).offset(offset).limit(limit).all()

    items = []
    for r in records:
        ev = db.query(Evidence).filter(Evidence.exception_id == r.id).first()
        items.append({
            "id": r.id,
            "exception_code": r.exception_code,
            "run_id": r.run_id,
            "exception_type": r.exception_type,
            "severity": r.severity,
            "status": r.status,
            "order_id": r.order_id,
            "payment_id": r.payment_id,
            "settlement_id": r.settlement_id,
            "invoice_id": r.invoice_id,
            "discrepancy_amount": r.discrepancy_amount,
            "ai_confidence_score": r.ai_confidence_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "evidence": {
                "summary": ev.summary if ev else None,
                "details_json": ev.details_json if ev else None
            } if ev else None
        })

    return {
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "exceptions": items
    }
