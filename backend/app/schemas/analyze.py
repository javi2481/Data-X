from pydantic import BaseModel
from typing import Optional, List

class AnalyzeRequest(BaseModel):
    session_id: str
    query: str

class AnalyzeResponse(BaseModel):
    session_id: str
    artifacts: List[dict]
    provenance: Optional[dict] = None
    summary: Optional[str] = None
    contract_version: str = "v1"

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
