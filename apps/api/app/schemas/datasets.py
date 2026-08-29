from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class DatasetSummaryResponse(BaseModel):
    orders_count: int
    payments_count: int
    settlements_count: int
    invoices_count: int
    total_records: int
    latest_load_batch: Optional[str] = None
    status: str = "success"

class LoadDemoResponse(BaseModel):
    message: str
    batch_id: str
    orders_loaded: int
    payments_loaded: int
    settlements_loaded: int
    invoices_loaded: int
    status: str = "success"

class UploadDatasetResponse(BaseModel):
    message: str
    dataset_type: str
    batch_id: str
    records_processed: int
    warnings: List[str] = []
    status: str = "success"

class ResetDemoResponse(BaseModel):
    message: str
    records_cleared: Dict[str, int]
    status: str = "success"

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "LedgerGuard AI API"
    version: str = "1.0.0"
    timestamp: str
