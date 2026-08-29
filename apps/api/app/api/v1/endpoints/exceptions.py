from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.exceptions import ExceptionStatusUpdate, ExceptionDetailResponse, PaginatedExceptionsResponse
from app.services import exception_service

router = APIRouter()

@router.get("/exceptions", response_model=PaginatedExceptionsResponse, tags=["Exceptions"])
def list_exceptions(
    search: Optional[str] = Query(None, description="Search term for ID fields (exception/order/payment/settlement/invoice)"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, INVESTIGATING, RESOLVED, IGNORED, ESCALATED"),
    exception_type: Optional[str] = Query(None, description="Filter by exception_type"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Minimum discrepancy amount ₹"),
    max_amount: Optional[float] = Query(None, description="Maximum discrepancy amount ₹"),
    min_confidence: Optional[float] = Query(None, description="Minimum AI confidence score (0.0 to 1.0)"),
    max_confidence: Optional[float] = Query(None, description="Maximum AI confidence score (0.0 to 1.0)"),
    sort_by: str = Query("priority", description="Sort field: priority, amount, severity, confidence, created_at"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Lists exceptions with rich filtering, search, multi-field sorting, and pagination."""
    res = exception_service.query_exceptions_paginated(
        db, search=search, severity=severity, status=status, exception_type=exception_type,
        start_date=start_date, end_date=end_date, min_amount=min_amount, max_amount=max_amount,
        min_confidence=min_confidence, max_confidence=max_confidence,
        sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size
    )
    return PaginatedExceptionsResponse(**res)

@router.get("/exceptions/{exception_id}", response_model=ExceptionDetailResponse, tags=["Exceptions"])
def get_exception_detail(
    exception_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full exception detail including evidence card, related financial records, and audit history."""
    return exception_service.get_exception_detail(db, exception_id)

@router.patch("/exceptions/{exception_id}/status", response_model=ExceptionDetailResponse, tags=["Exceptions"])
def update_exception_status(
    exception_id: str,
    payload: ExceptionStatusUpdate,
    db: Session = Depends(get_db)
):
    """Human-in-the-Loop: Updates exception status and creates an immutable audit trail entry."""
    return exception_service.update_exception_status(db, exception_id, payload)

@router.get("/reports/exceptions.csv", tags=["Reports"])
def export_exceptions_csv(
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    min_confidence: Optional[float] = Query(None),
    max_confidence: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Exports exceptions as CSV report respecting all active search and query filters."""
    csv_str = exception_service.generate_exceptions_csv_report(
        db, search=search, severity=severity, status=status, exception_type=exception_type,
        start_date=start_date, end_date=end_date, min_amount=min_amount, max_amount=max_amount,
        min_confidence=min_confidence, max_confidence=max_confidence
    )
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ledgerguard_exceptions_report.csv"
        }
    )
