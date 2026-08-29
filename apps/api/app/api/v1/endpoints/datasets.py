from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.datasets import LoadDemoResponse, UploadDatasetResponse, DatasetSummaryResponse, ResetDemoResponse
from app.services import dataset_service

router = APIRouter()

@router.post("/datasets/load-demo", response_model=LoadDemoResponse, tags=["Datasets"])
def load_demo_dataset(db: Session = Depends(get_db)):
    """Loads pre-generated synthetic sample datasets from data/sample/ into SQLite DB."""
    return dataset_service.load_demo_data(db)

@router.post("/datasets/upload", response_model=UploadDatasetResponse, tags=["Datasets"])
async def upload_dataset_file(
    dataset_type: str = Form(..., description="Dataset type: 'orders', 'payments', 'settlements', or 'invoices'"),
    file: UploadFile = File(..., description="CSV file containing financial records"),
    db: Session = Depends(get_db)
):
    """Uploads a custom CSV dataset, validates headers/types/security rules, and stores in SQLite DB."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files (.csv) are accepted.")

    content = await file.read()
    return dataset_service.upload_dataset(db, dataset_type=dataset_type, content_bytes=content, filename=file.filename)

@router.get("/datasets/summary", response_model=DatasetSummaryResponse, tags=["Datasets"])
def get_datasets_summary(db: Session = Depends(get_db)):
    """Returns row counts and database statistics for financial records."""
    return dataset_service.get_datasets_summary(db)

@router.post("/demo/reset", response_model=ResetDemoResponse, tags=["Demo"])
def reset_demo_database(db: Session = Depends(get_db)):
    """Resets all database tables and clears all records."""
    return dataset_service.reset_demo_data(db)
