import os
import csv
import io
import re
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger
from app.models.base import Base, Order, Payment, Settlement, Invoice, ReconciliationRun, ExceptionRecord, Evidence, AuditLog
from app.services.audit_service import log_audit

SENSITIVE_KEYWORDS = {"cvv", "cvc", "card_number", "pan", "pin", "password", "secret_key", "auth_token", "private_key"}

REQUIRED_HEADERS = {
    "orders": {"order_id", "order_amount", "currency", "status", "created_at"},
    "payments": {"payment_id", "order_id", "payment_method", "payment_amount", "status", "transaction_time"},
    "settlements": {"settlement_id", "utr", "payment_id", "gross_amount", "fee_amount", "tax_amount", "net_amount", "settlement_time"},
    "invoices": {"invoice_id", "order_id", "vendor_name", "invoice_amount", "net_total", "invoice_date"}
}

def check_sensitive_credentials(headers: list, rows: list):
    # Check headers
    for h in headers:
        clean_h = h.strip().lower()
        if clean_h in SENSITIVE_KEYWORDS or any(kw in clean_h for kw in SENSITIVE_KEYWORDS):
            raise HTTPException(
                status_code=400,
                detail=f"Security Violation: CSV header '{h}' contains prohibited sensitive payment credentials."
            )
    
    # Check sample row values for 16-digit raw credit card or explicit CVV patterns
    card_pattern = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    for row_idx, row in enumerate(rows[:50], start=1):
        for col_name, val in row.items():
            if val and card_pattern.search(str(val)) and "phone" not in str(col_name).lower() and "utr" not in str(col_name).lower():
                # Allow standard phone/UTR strings, block raw card numbers
                if len(re.sub(r"\D", "", str(val))) == 16 and not str(val).startswith("+91"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Security Violation: Prohibited raw card credential detected in row {row_idx}, column '{col_name}'."
                    )

def parse_datetime(dt_str: str) -> datetime:
    if not dt_str:
        return datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid timestamp format: '{dt_str}'. Expected format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD")

def load_demo_data(db: Session) -> dict:
    Base.metadata.create_all(bind=db.get_bind())

    sample_dir = settings.SAMPLE_DATA_DIR
    if not os.path.exists(sample_dir):
        raise HTTPException(status_code=404, detail=f"Sample data directory not found at '{sample_dir}'. Run generator first.")

    batch_id = f"demo_{uuid.uuid4().hex[:8]}"
    
    # Files
    orders_path = os.path.join(sample_dir, "orders.csv")
    payments_path = os.path.join(sample_dir, "payments.csv")
    settlements_path = os.path.join(sample_dir, "settlements.csv")
    invoices_path = os.path.join(sample_dir, "invoices.csv")

    for path, name in [(orders_path, "orders"), (payments_path, "payments"), (settlements_path, "settlements"), (invoices_path, "invoices")]:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Sample file '{name}.csv' missing in {sample_dir}.")

    # Reset current table data before loading fresh demo set
    db.query(Order).delete()
    db.query(Payment).delete()
    db.query(Settlement).delete()
    db.query(Invoice).delete()
    db.query(ExceptionRecord).delete()
    db.query(Evidence).delete()
    db.query(ReconciliationRun).delete()
    db.commit()

    orders_count = 0
    payments_count = 0
    settlements_count = 0
    invoices_count = 0

    # 1. Load Orders
    with open(orders_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            o_item = Order(
                order_id=row["order_id"],
                merchant_id=row.get("merchant_id"),
                customer_id=row.get("customer_id"),
                customer_name=row.get("customer_name"),
                customer_email=row.get("customer_email"),
                customer_phone=row.get("customer_phone"),
                order_amount=float(row["order_amount"]),
                currency=row.get("currency", "INR"),
                status=row.get("status", "PAID"),
                created_at=parse_datetime(row["created_at"]),
                dataset_batch=batch_id
            )
            db.add(o_item)
            orders_count += 1

    # 2. Load Payments
    with open(payments_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_item = Payment(
                payment_id=row["payment_id"],
                order_id=row["order_id"],
                payment_method=row["payment_method"],
                payment_amount=float(row["payment_amount"]),
                fee_amount=float(row.get("fee_amount", 0.0)),
                tax_amount=float(row.get("tax_amount", 0.0)),
                status=row.get("status", "CAPTURED"),
                gateway_ref=row.get("gateway_ref"),
                transaction_time=parse_datetime(row["transaction_time"]),
                settlement_status=row.get("settlement_status", "PENDING"),
                dataset_batch=batch_id
            )
            db.add(p_item)
            payments_count += 1

    # 3. Load Settlements
    with open(settlements_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_item = Settlement(
                settlement_id=row["settlement_id"],
                utr=row["utr"],
                payment_id=row["payment_id"],
                gross_amount=float(row["gross_amount"]),
                fee_amount=float(row.get("fee_amount", 0.0)),
                tax_amount=float(row.get("tax_amount", 0.0)),
                net_amount=float(row["net_amount"]),
                bank_account=row.get("bank_account"),
                settlement_time=parse_datetime(row["settlement_time"]),
                status=row.get("status", "SETTLED"),
                dataset_batch=batch_id
            )
            db.add(s_item)
            settlements_count += 1

    # 4. Load Invoices
    with open(invoices_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            i_item = Invoice(
                invoice_id=row["invoice_id"],
                order_id=row["order_id"],
                vendor_name=row["vendor_name"],
                invoice_amount=float(row["invoice_amount"]),
                tax_amount=float(row.get("tax_amount", 0.0)),
                net_total=float(row["net_total"]),
                invoice_date=parse_datetime(row["invoice_date"]),
                due_date=parse_datetime(row["due_date"]) if row.get("due_date") else None,
                status=row.get("status", "ISSUED"),
                dataset_batch=batch_id
            )
            db.add(i_item)
            invoices_count += 1

    db.commit()

    log_audit(
        db,
        entity_type="Dataset",
        action="LOAD_DEMO_DATA",
        reason=f"Seeded demo dataset batch {batch_id}",
        metadata={
            "batch_id": batch_id,
            "orders": orders_count,
            "payments": payments_count,
            "settlements": settlements_count,
            "invoices": invoices_count
        }
    )

    return {
        "message": f"Successfully loaded demo dataset (Batch: {batch_id})",
        "batch_id": batch_id,
        "orders_loaded": orders_count,
        "payments_loaded": payments_count,
        "settlements_loaded": settlements_count,
        "invoices_loaded": invoices_count
    }

def upload_dataset(db: Session, dataset_type: str, content_bytes: bytes, filename: str) -> dict:
    Base.metadata.create_all(bind=db.get_bind())
    dataset_type = dataset_type.lower().strip()
    if dataset_type not in REQUIRED_HEADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dataset_type '{dataset_type}'. Must be one of: {list(REQUIRED_HEADERS.keys())}"
        )

    if len(content_bytes) > settings.MAX_CSV_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_CSV_SIZE_BYTES // (1024*1024)}MB."
        )

    try:
        content_str = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File decoding failed. CSV file must be UTF-8 encoded.")

    stream = io.StringIO(content_str)
    reader = csv.DictReader(stream)

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Malformed CSV file: Header row missing or empty.")

    headers = [h.strip() for h in reader.fieldnames]
    missing_headers = REQUIRED_HEADERS[dataset_type] - set(headers)
    if missing_headers:
        raise HTTPException(
            status_code=400,
            detail=f"CSV Validation Error for '{dataset_type}': Missing required headers: {list(missing_headers)}"
        )

    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV Validation Error: File contains no data rows.")

    # Security check
    check_sensitive_credentials(headers, rows)

    batch_id = f"upload_{uuid.uuid4().hex[:8]}"
    processed_count = 0
    warnings = []

    try:
        if dataset_type == "orders":
            for idx, r in enumerate(rows, start=1):
                try:
                    db.add(Order(
                        order_id=r["order_id"],
                        merchant_id=r.get("merchant_id"),
                        customer_id=r.get("customer_id"),
                        customer_name=r.get("customer_name"),
                        customer_email=r.get("customer_email"),
                        customer_phone=r.get("customer_phone"),
                        order_amount=float(r["order_amount"]),
                        currency=r.get("currency", "INR"),
                        status=r.get("status", "PAID"),
                        created_at=parse_datetime(r["created_at"]),
                        dataset_batch=batch_id
                    ))
                    processed_count += 1
                except Exception as e:
                    warnings.append(f"Row {idx} skipped: {str(e)}")

        elif dataset_type == "payments":
            for idx, r in enumerate(rows, start=1):
                try:
                    db.add(Payment(
                        payment_id=r["payment_id"],
                        order_id=r["order_id"],
                        payment_method=r["payment_method"],
                        payment_amount=float(r["payment_amount"]),
                        fee_amount=float(r.get("fee_amount", 0.0)),
                        tax_amount=float(r.get("tax_amount", 0.0)),
                        status=r.get("status", "CAPTURED"),
                        gateway_ref=r.get("gateway_ref"),
                        transaction_time=parse_datetime(r["transaction_time"]),
                        settlement_status=r.get("settlement_status", "PENDING"),
                        dataset_batch=batch_id
                    ))
                    processed_count += 1
                except Exception as e:
                    warnings.append(f"Row {idx} skipped: {str(e)}")

        elif dataset_type == "settlements":
            for idx, r in enumerate(rows, start=1):
                try:
                    db.add(Settlement(
                        settlement_id=r["settlement_id"],
                        utr=r["utr"],
                        payment_id=r["payment_id"],
                        gross_amount=float(r["gross_amount"]),
                        fee_amount=float(r.get("fee_amount", 0.0)),
                        tax_amount=float(r.get("tax_amount", 0.0)),
                        net_amount=float(r["net_amount"]),
                        bank_account=r.get("bank_account"),
                        settlement_time=parse_datetime(r["settlement_time"]),
                        status=r.get("status", "SETTLED"),
                        dataset_batch=batch_id
                    ))
                    processed_count += 1
                except Exception as e:
                    warnings.append(f"Row {idx} skipped: {str(e)}")

        elif dataset_type == "invoices":
            for idx, r in enumerate(rows, start=1):
                try:
                    db.add(Invoice(
                        invoice_id=r["invoice_id"],
                        order_id=r["order_id"],
                        vendor_name=r["vendor_name"],
                        invoice_amount=float(r["invoice_amount"]),
                        tax_amount=float(r.get("tax_amount", 0.0)),
                        net_total=float(r["net_total"]),
                        invoice_date=parse_datetime(r["invoice_date"]),
                        due_date=parse_datetime(r["due_date"]) if r.get("due_date") else None,
                        status=r.get("status", "ISSUED"),
                        dataset_batch=batch_id
                    ))
                    processed_count += 1
                except Exception as e:
                    warnings.append(f"Row {idx} skipped: {str(e)}")

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error during dataset upload: {str(exc)}")

    log_audit(
        db,
        entity_type="Dataset",
        action="UPLOAD_CSV",
        reason=f"Uploaded CSV dataset '{dataset_type}' from file {filename}",
        metadata={
            "dataset_type": dataset_type,
            "filename": filename,
            "batch_id": batch_id,
            "records_processed": processed_count,
            "warnings_count": len(warnings)
        }
    )

    return {
        "message": f"Successfully uploaded {processed_count} {dataset_type} records.",
        "dataset_type": dataset_type,
        "batch_id": batch_id,
        "records_processed": processed_count,
        "warnings": warnings[:10]  # Return up to 10 warnings
    }

def get_datasets_summary(db: Session) -> dict:
    Base.metadata.create_all(bind=db.get_bind())
    orders_cnt = db.query(Order).count()
    payments_cnt = db.query(Payment).count()
    settlements_cnt = db.query(Settlement).count()
    invoices_cnt = db.query(Invoice).count()

    latest_audit = db.query(AuditLog).filter(AuditLog.entity_type == "Dataset").order_by(AuditLog.id.desc()).first()
    latest_batch = None
    if latest_audit and latest_audit.metadata_json:
        try:
            meta = json.loads(latest_audit.metadata_json)
            latest_batch = meta.get("batch_id")
        except Exception:
            pass

    return {
        "orders_count": orders_cnt,
        "payments_count": payments_cnt,
        "settlements_count": settlements_cnt,
        "invoices_count": invoices_cnt,
        "total_records": orders_cnt + payments_cnt + settlements_cnt + invoices_cnt,
        "latest_load_batch": latest_batch,
        "status": "success"
    }

def reset_demo_data(db: Session) -> dict:
    Base.metadata.create_all(bind=db.get_bind())
    cleared = {
        "orders": db.query(Order).count(),
        "payments": db.query(Payment).count(),
        "settlements": db.query(Settlement).count(),
        "invoices": db.query(Invoice).count(),
        "reconciliation_runs": db.query(ReconciliationRun).count(),
        "exceptions": db.query(ExceptionRecord).count(),
        "evidence": db.query(Evidence).count()
    }

    db.query(Order).delete()
    db.query(Payment).delete()
    db.query(Settlement).delete()
    db.query(Invoice).delete()
    db.query(ExceptionRecord).delete()
    db.query(Evidence).delete()
    db.query(ReconciliationRun).delete()
    db.commit()

    log_audit(
        db,
        entity_type="System",
        action="RESET_DEMO_DATABASE",
        reason="Reset all dataset and reconciliation state",
        metadata={"cleared": cleared}
    )

    return {
        "message": "Successfully cleared all database tables and reset system state.",
        "records_cleared": cleared,
        "status": "success"
    }
