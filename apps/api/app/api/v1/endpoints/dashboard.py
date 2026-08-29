from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.engine.metrics_calculator import compute_dashboard_metrics, compute_dashboard_trends

router = APIRouter()

@router.get("/dashboard/metrics", tags=["Dashboard"])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Computes executive financial dashboard metrics (Reconciled %, Unreconciled amount, risk score)."""
    return compute_dashboard_metrics(db)

@router.get("/dashboard/trends", tags=["Dashboard"])
def get_dashboard_trends(db: Session = Depends(get_db)):
    """Returns daily order volume trends and discrepancy trends over active time windows."""
    return compute_dashboard_trends(db)
