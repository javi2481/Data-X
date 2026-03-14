from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

class SessionResponse(BaseModel):
    session_id: str
    status: Literal["created", "processing", "ready", "error"]
    created_at: datetime
    source_metadata: dict
    schema_info: Optional[dict] = None
    profile: Optional[dict] = None
    quality_gate: Optional[dict] = None
    contract_version: str = "v1"
