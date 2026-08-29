import time
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.copilot import CopilotQueryRequest, CopilotQueryResponse
from app.services.copilot_service import CopilotService

router = APIRouter()

# Simple in-memory rate limiting store (max 20 requests per minute per IP)
RATE_LIMIT_STORE: Dict[str, list] = {}

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    timestamps = RATE_LIMIT_STORE.get(client_ip, [])
    # Filter timestamps within last 60 seconds
    valid_timestamps = [t for t in timestamps if now - t < 60]

    if len(valid_timestamps) >= 30: # 30 requests per minute limit
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a minute before making more copilot queries.",
        )

    valid_timestamps.append(now)
    RATE_LIMIT_STORE[client_ip] = valid_timestamps

@router.post("/query", response_model=CopilotQueryResponse)
def query_copilot(
    req: CopilotQueryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    check_rate_limit(request)
    service = CopilotService(db)
    return service.query(req)
