from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

VALID_STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED", "IGNORED", "ESCALATED"}

class ExceptionStatusUpdate(BaseModel):
    status: str = Field(..., description="New status: OPEN, INVESTIGATING, RESOLVED, IGNORED, ESCALATED")
    resolution_code: Optional[str] = Field(None, description="Optional resolution code e.g. REFUND_ISSUED, GATEWAY_CLAIM_FILED")
    note: Optional[str] = Field(None, description="Mandatory/optional finance officer note")
    performed_by: Optional[str] = Field("Finance Officer", description="Name/ID of officer taking action")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        clean_v = str(v).strip().upper()
        if clean_v not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed statuses: {sorted(list(VALID_STATUSES))}")
        return clean_v

class EvidenceSchema(BaseModel):
    evidence_type: str
    summary: str
    side_by_side: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None
    details_json: Optional[str] = None

class ExceptionDetailResponse(BaseModel):
    id: int
    exception_code: str
    run_id: Optional[int] = None
    exception_type: str
    severity: str
    status: str
    priority_score: float
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    settlement_id: Optional[str] = None
    invoice_id: Optional[str] = None
    discrepancy_amount: float
    ai_confidence_score: float
    created_at: str
    evidence: Optional[EvidenceSchema] = None
    related_order: Optional[Dict[str, Any]] = None
    related_payment: Optional[Dict[str, Any]] = None
    related_settlement: Optional[Dict[str, Any]] = None
    related_invoice: Optional[Dict[str, Any]] = None
    audit_history: List[Dict[str, Any]] = []

class PaginatedExceptionsResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    items: List[ExceptionDetailResponse]
    status: str = "success"
