from collections import Counter, defaultdict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.base import Order, Payment, Settlement, Invoice, ReconciliationRun, ExceptionRecord, AuditLog

def compute_dashboard_metrics(db: Session) -> dict:
    orders_cnt = db.query(Order).count()
    payments_cnt = db.query(Payment).count()
    settlements_cnt = db.query(Settlement).count()
    invoices_cnt = db.query(Invoice).count()

    latest_run = db.query(ReconciliationRun).order_by(ReconciliationRun.id.desc()).first()
    exceptions = db.query(ExceptionRecord).all()

    total_exceptions = len(exceptions)
    unreconciled_amt = sum(e.discrepancy_amount for e in exceptions if e.status == "OPEN")

    severity_counts = Counter(e.severity for e in exceptions)
    type_counts = Counter(e.exception_type for e in exceptions)
    status_counts = Counter(e.status for e in exceptions)

    # Reconciled percentage calculation
    total_volume = orders_cnt + payments_cnt + settlements_cnt
    reconciled_pct = round(((total_volume - total_exceptions) / max(1, total_volume)) * 100.0, 2)

    # Risk Score Index (0 to 100)
    critical_cnt = severity_counts.get("CRITICAL", 0)
    high_cnt = severity_counts.get("HIGH", 0)
    risk_score = round(min(100.0, (critical_cnt * 10 + high_cnt * 5 + total_exceptions * 0.5)), 1)

    return {
        "summary": {
            "total_orders": orders_cnt,
            "total_payments": payments_cnt,
            "total_settlements": settlements_cnt,
            "total_invoices": invoices_cnt,
            "total_exceptions": total_exceptions,
            "unreconciled_amount": round(unreconciled_amt, 2),
            "reconciled_percentage": reconciled_pct,
            "risk_score": risk_score,
            "latest_run_id": latest_run.run_code if latest_run else None,
            "latest_run_time": latest_run.started_at.isoformat() if latest_run and latest_run.started_at else None
        },
        "breakdown": {
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "by_status": dict(status_counts)
        }
    }

def compute_dashboard_trends(db: Session) -> dict:
    orders = db.query(Order).all()
    exceptions = db.query(ExceptionRecord).all()

    daily_orders = defaultdict(float)
    for o in orders:
        if o.created_at:
            day_str = o.created_at.strftime("%Y-%m-%d")
            daily_orders[day_str] += o.order_amount

    daily_exceptions = defaultdict(int)
    daily_discrepancy = defaultdict(float)
    for e in exceptions:
        if e.created_at:
            day_str = e.created_at.strftime("%Y-%m-%d")
            daily_exceptions[day_str] += 1
            daily_discrepancy[day_str] += e.discrepancy_amount

    all_days = sorted(list(set(daily_orders.keys()) | set(daily_exceptions.keys())))
    
    volume_trend = [{"date": d, "order_volume": round(daily_orders[d], 2)} for d in all_days]
    exception_trend = [{"date": d, "exception_count": daily_exceptions[d], "discrepancy_amount": round(daily_discrepancy[d], 2)} for d in all_days]

    return {
        "volume_trend": volume_trend[-30:],  # Last 30 active days
        "exception_trend": exception_trend[-30:]
    }
