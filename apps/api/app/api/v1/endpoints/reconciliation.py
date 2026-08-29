from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import reconciliation_service

router = APIRouter()

@router.post("/reconciliation/run", tags=["Reconciliation"])
def trigger_reconciliation_run(db: Session = Depends(get_db)):
    """Triggers automated vectorized reconciliation engine over DB records and stores results."""
    return reconciliation_service.execute_reconciliation_run(db)

@router.get("/api/reconciliation/results", tags=["Reconciliation"])
@router.get("/reconciliation/results", tags=["Reconciliation"])
def get_reconciliation_results(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    exception_type: Optional[str] = Query(None, description="Filter by exception_type"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, RESOLVED, REJECTED"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Fetches reconciliation exception results with filtering and evidence breakdowns."""
    return reconciliation_service.query_reconciliation_results(
        db,
        severity=severity,
        exception_type=exception_type,
        status=status,
        limit=limit,
        offset=offset
    )
