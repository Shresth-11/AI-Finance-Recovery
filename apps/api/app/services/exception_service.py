import csv
import io
import json
import math
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.base import Order, Payment, Settlement, Invoice, ExceptionRecord, Evidence, AuditLog
from app.engine.priority_scorer import calculate_priority_score
from app.services.dataset_service import parse_datetime
from app.services.audit_service import log_audit
from app.schemas.exceptions import ExceptionStatusUpdate, VALID_STATUSES

def _build_exception_detail_dict(db: Session, exc: ExceptionRecord) -> dict:
    ev = db.query(Evidence).filter(Evidence.exception_id == exc.id).first()
    
    side_by_side = None
    remediation = None
    if ev and ev.details_json:
        try:
            parsed = json.loads(ev.details_json)
            side_by_side = parsed.get("side_by_side")
            remediation = parsed.get("remediation")
        except Exception:
            pass

    # Fetch related records
    rel_order = None
    if exc.order_id:
        o = db.query(Order).filter(Order.order_id == exc.order_id).first()
        if o:
            rel_order = {
                "order_id": o.order_id, "amount": o.order_amount, "currency": o.currency,
                "status": o.status, "customer_name": o.customer_name, "customer_email": o.customer_email,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }

    rel_payment = None
    if exc.payment_id:
        p = db.query(Payment).filter(Payment.payment_id == exc.payment_id).first()
        if p:
            rel_payment = {
                "payment_id": p.payment_id, "order_id": p.order_id, "method": p.payment_method,
                "amount": p.payment_amount, "fee": p.fee_amount, "tax": p.tax_amount,
                "status": p.status, "gateway_ref": p.gateway_ref,
                "transaction_time": p.transaction_time.isoformat() if p.transaction_time else None
            }

    rel_settlement = None
    if exc.settlement_id:
        s = db.query(Settlement).filter(Settlement.settlement_id == exc.settlement_id).first()
        if s:
            rel_settlement = {
                "settlement_id": s.settlement_id, "utr": s.utr, "payment_id": s.payment_id,
                "gross_amount": s.gross_amount, "fee": s.fee_amount, "net_amount": s.net_amount,
                "status": s.status, "settlement_time": s.settlement_time.isoformat() if s.settlement_time else None
            }

    rel_invoice = None
    if exc.invoice_id:
        inv = db.query(Invoice).filter(Invoice.invoice_id == exc.invoice_id).first()
        if inv:
            rel_invoice = {
                "invoice_id": inv.invoice_id, "order_id": inv.order_id, "vendor_name": inv.vendor_name,
                "amount": inv.invoice_amount, "tax": inv.tax_amount, "net_total": inv.net_total,
                "status": inv.status
            }

    # Fetch audit logs for this exception
    audits = db.query(AuditLog).filter(
        AuditLog.entity_type == "ExceptionRecord",
        AuditLog.entity_id == str(exc.id)
    ).order_by(AuditLog.id.desc()).all()

    audit_history = []
    for a in audits:
        meta = json.loads(a.metadata_json) if a.metadata_json else {}
        audit_history.append({
            "action": a.action,
            "performed_by": a.performed_by,
            "reason": a.reason,
            "metadata": meta,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        })

    # Age in days
    age_days = 0
    if exc.created_at:
        age_days = (datetime.now() - exc.created_at).days

    priority = calculate_priority_score(
        severity=exc.severity,
        discrepancy_amount=exc.discrepancy_amount,
        age_days=age_days,
        confidence_score=exc.ai_confidence_score,
        is_unresolved=(exc.status == "OPEN")
    )

    return {
        "id": exc.id,
        "exception_code": exc.exception_code,
        "run_id": exc.run_id,
        "exception_type": exc.exception_type,
        "severity": exc.severity,
        "status": exc.status,
        "priority_score": priority,
        "order_id": exc.order_id,
        "payment_id": exc.payment_id,
        "settlement_id": exc.settlement_id,
        "invoice_id": exc.invoice_id,
        "discrepancy_amount": exc.discrepancy_amount,
        "ai_confidence_score": exc.ai_confidence_score,
        "created_at": exc.created_at.isoformat() if exc.created_at else None,
        "evidence": {
            "evidence_type": ev.evidence_type if ev else exc.exception_type,
            "summary": ev.summary if ev else "",
            "side_by_side": side_by_side,
            "remediation": remediation,
            "details_json": ev.details_json if ev else None
        } if ev else None,
        "related_order": rel_order,
        "related_payment": rel_payment,
        "related_settlement": rel_settlement,
        "related_invoice": rel_invoice,
        "audit_history": audit_history
    }

def filter_exceptions_query(
    db: Session,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    exception_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None
):
    query = db.query(ExceptionRecord)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            ExceptionRecord.exception_code.ilike(term),
            ExceptionRecord.order_id.ilike(term),
            ExceptionRecord.payment_id.ilike(term),
            ExceptionRecord.settlement_id.ilike(term),
            ExceptionRecord.invoice_id.ilike(term)
        ))

    if severity and severity.strip():
        query = query.filter(ExceptionRecord.severity == severity.strip().upper())

    if status and status.strip():
        query = query.filter(ExceptionRecord.status == status.strip().upper())

    if exception_type and exception_type.strip():
        query = query.filter(ExceptionRecord.exception_type == exception_type.strip().upper())

    if start_date:
        try:
            dt_start = parse_datetime(start_date)
            query = query.filter(ExceptionRecord.created_at >= dt_start)
        except Exception:
            pass

    if end_date:
        try:
            dt_end = parse_datetime(end_date)
            query = query.filter(ExceptionRecord.created_at <= dt_end)
        except Exception:
            pass

    if min_amount is not None:
        query = query.filter(ExceptionRecord.discrepancy_amount >= float(min_amount))

    if max_amount is not None:
        query = query.filter(ExceptionRecord.discrepancy_amount <= float(max_amount))

    if min_confidence is not None:
        query = query.filter(ExceptionRecord.ai_confidence_score >= float(min_confidence))

    if max_confidence is not None:
        query = query.filter(ExceptionRecord.ai_confidence_score <= float(max_confidence))

    return query

def query_exceptions_paginated(
    db: Session,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    exception_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    sort_by: str = "priority",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20
) -> dict:
    query = filter_exceptions_query(
        db, search, severity, status, exception_type, start_date, end_date,
        min_amount, max_amount, min_confidence, max_confidence
    )

    total_count = query.count()
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1

    records = query.all()

    # Build detail dicts & attach computed priority_score
    items = [_build_exception_detail_dict(db, r) for r in records]

    # In-memory sorting for priority_score, amount, severity, confidence, created_at
    is_desc = (sort_order.lower() == "desc")
    sort_key_lower = sort_by.lower()

    if sort_key_lower == "priority":
        items.sort(key=lambda x: x["priority_score"], reverse=is_desc)
    elif sort_key_lower == "amount":
        items.sort(key=lambda x: x["discrepancy_amount"], reverse=is_desc)
    elif sort_key_lower == "severity":
        sev_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        items.sort(key=lambda x: sev_rank.get(x["severity"], 0), reverse=is_desc)
    elif sort_key_lower == "confidence":
        items.sort(key=lambda x: x["ai_confidence_score"], reverse=is_desc)
    elif sort_key_lower == "created_at":
        items.sort(key=lambda x: x["created_at"] or "", reverse=is_desc)
    else:
        items.sort(key=lambda x: x["priority_score"], reverse=is_desc)

    # Slice for pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": paginated_items
    }

def get_exception_detail(db: Session, exception_id_str: str) -> dict:
    exc = None
    if exception_id_str.isdigit():
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.id == int(exception_id_str)).first()
    
    if not exc:
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.exception_code == exception_id_str).first()

    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception with identifier '{exception_id_str}' not found.")

    return _build_exception_detail_dict(db, exc)

def update_exception_status(db: Session, exception_id_str: str, update_payload: ExceptionStatusUpdate) -> dict:
    exc = None
    if exception_id_str.isdigit():
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.id == int(exception_id_str)).first()
    
    if not exc:
        exc = db.query(ExceptionRecord).filter(ExceptionRecord.exception_code == exception_id_str).first()

    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception with identifier '{exception_id_str}' not found.")

    prev_status = exc.status
    new_status = update_payload.status

    exc.status = new_status
    db.commit()
    db.refresh(exc)

    # Mandatory Audit Log creation
    log_audit(
        db,
        entity_type="ExceptionRecord",
        entity_id=str(exc.id),
        action=f"STATUS_UPDATED_{new_status}",
        performed_by=update_payload.performed_by or "Finance Officer",
        reason=update_payload.note or f"Status changed from {prev_status} to {new_status}",
        metadata={
            "exception_code": exc.exception_code,
            "previous_status": prev_status,
            "new_status": new_status,
            "resolution_code": update_payload.resolution_code,
            "note": update_payload.note
        }
    )

    return _build_exception_detail_dict(db, exc)

def generate_exceptions_csv_report(
    db: Session,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    exception_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None
) -> str:
    res = query_exceptions_paginated(
        db, search=search, severity=severity, status=status, exception_type=exception_type,
        start_date=start_date, end_date=end_date, min_amount=min_amount, max_amount=max_amount,
        min_confidence=min_confidence, max_confidence=max_confidence,
        page=1, page_size=10000
    )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "exception_id", "exception_code", "exception_type", "severity", "status",
        "priority_score", "order_id", "payment_id", "settlement_id", "invoice_id",
        "discrepancy_amount", "ai_confidence_score", "created_at", "evidence_summary"
    ])
    writer.writeheader()

    for item in res["items"]:
        ev_summary = item["evidence"]["summary"] if item.get("evidence") else ""
        writer.writerow({
            "exception_id": item["id"],
            "exception_code": item["exception_code"],
            "exception_type": item["exception_type"],
            "severity": item["severity"],
            "status": item["status"],
            "priority_score": item["priority_score"],
            "order_id": item["order_id"] or "",
            "payment_id": item["payment_id"] or "",
            "settlement_id": item["settlement_id"] or "",
            "invoice_id": item["invoice_id"] or "",
            "discrepancy_amount": item["discrepancy_amount"],
            "ai_confidence_score": item["ai_confidence_score"],
            "created_at": item["created_at"] or "",
            "evidence_summary": ev_summary
        })

    return output.getvalue()
