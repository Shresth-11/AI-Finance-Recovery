from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    merchant_id = Column(String(100), nullable=True)
    customer_id = Column(String(100), nullable=True)
    customer_name = Column(String(200), nullable=True)
    customer_email = Column(String(200), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    order_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="PAID", nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    dataset_batch = Column(String(100), nullable=True, default="default")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_amount = Column(Float, nullable=False)
    fee_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="CAPTURED", nullable=False)
    gateway_ref = Column(String(100), nullable=True)
    transaction_time = Column(DateTime, nullable=False, index=True)
    settlement_status = Column(String(50), default="PENDING", nullable=False)
    dataset_batch = Column(String(100), nullable=True, default="default")

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    settlement_id = Column(String(100), index=True, nullable=False)
    utr = Column(String(100), index=True, nullable=False)
    payment_id = Column(String(100), index=True, nullable=False)
    gross_amount = Column(Float, nullable=False)
    fee_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    net_amount = Column(Float, nullable=False)
    bank_account = Column(String(100), nullable=True)
    settlement_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="SETTLED", nullable=False)
    dataset_batch = Column(String(100), nullable=True, default="default")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=False)
    vendor_name = Column(String(200), nullable=False)
    invoice_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    net_total = Column(Float, nullable=False)
    invoice_date = Column(DateTime, nullable=False, index=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="ISSUED", nullable=False)
    dataset_batch = Column(String(100), nullable=True, default="default")

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_code = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)
    total_orders = Column(Integer, default=0)
    total_payments = Column(Integer, default=0)
    total_settlements = Column(Integer, default=0)
    total_invoices = Column(Integer, default=0)
    total_exceptions = Column(Integer, default=0)
    unreconciled_amount = Column(Float, default=0.0)
    started_at = Column(DateTime, default=utc_now, index=True)
    completed_at = Column(DateTime, nullable=True)

    exceptions = relationship("ExceptionRecord", back_populates="run", cascade="all, delete-orphan")

class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_code = Column(String(100), unique=True, index=True, nullable=False)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id"), nullable=True)
    exception_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), default="MEDIUM", nullable=False, index=True)
    status = Column(String(50), default="OPEN", nullable=False, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    payment_id = Column(String(100), nullable=True, index=True)
    settlement_id = Column(String(100), nullable=True, index=True)
    invoice_id = Column(String(100), nullable=True, index=True)
    discrepancy_amount = Column(Float, default=0.0, index=True)
    ai_confidence_score = Column(Float, default=0.95)
    created_at = Column(DateTime, default=utc_now, index=True)

    run = relationship("ReconciliationRun", back_populates="exceptions")
    evidence_items = relationship("Evidence", back_populates="exception_record", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exceptions.id"), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    exception_record = relationship("ExceptionRecord", back_populates="evidence_items")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    performed_by = Column(String(100), default="System", nullable=False)
    reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
