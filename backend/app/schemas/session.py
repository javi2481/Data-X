from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

class SessionResponse(BaseModel):
    session_id: str
    status: Literal["created", "processing", "ready", "error"]
    created_at: datetime
    source_metadata: dict
    quality_decision: Optional[str] = None
    dataset_overview: Optional[dict] = None
    finding_count: Optional[int] = None
    contract_version: str = "v1"
