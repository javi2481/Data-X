from pydantic import BaseModel
from typing import Optional, List, Literal, Union, Tuple

from app.schemas.finding import SourceLocation, BoundingBox


class SourceReference(BaseModel):
    """Referencia a una fuente de evidencia con provenance completo"""
    source_type: Literal["finding", "chunk", "table", "section", "page_reference", "heading"]
    source_id: str
    evidence_ref: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None
    
    # Provenance detallado (Sprint 0 - Docling-first)
    location: Optional[SourceLocation] = None
    chunk_id: Optional[str] = None  # ID del chunk asociado


class AnalyzeRequest(BaseModel):
    session_id: str
    query: str


class AnalyzeResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    relevant_findings: List[dict]  # findings usados como contexto
    sources: List[Union[str, SourceReference]] = []  # Legacy IDs o referencias tipadas
    confidence: str  # "high" si hay findings relevantes, "low" si no
    contract_version: str = "v1"


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
