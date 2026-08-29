from typing import List, Optional
from pydantic import BaseModel, Field

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language question for copilot")
    context_exception_id: Optional[int] = Field(None, description="Optional exception ID context")

class CopilotQueryResponse(BaseModel):
    query: str
    answer: str
    cited_evidence_ids: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.95, ge=0.0, le=1.0)
    limitations: str
    fallback_mode: bool = True
    disclaimer: str = "AI-assisted analysis based on loaded synthetic data. Human review is required."
    suggested_actions: List[str] = Field(default_factory=list)
