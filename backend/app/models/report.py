from typing import Optional
from pydantic import BaseModel, Field


class DecisionAnalyzeRequest(BaseModel):
    """Request for single-event analysis by normalized anomaly or known event ID."""
    event_id: Optional[str] = Field(default=None)
    anomaly: Optional[dict] = Field(default=None)


class ReportMetadata(BaseModel):
    event_id: str
    firms_id: Optional[str] = None
    generated_at: str
    format: str = "html"
    source: str = "THERMOSENTRY AI"