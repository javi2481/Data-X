from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class ProvenanceInfo(BaseModel):
    source: str
    ingestion_method: str
    quality_decision: str
    processing_steps: List[str] = []
    affected_columns: List[str] = []

class AnalysisReport(BaseModel):
    session_id: str
    status: Literal["completed", "partial", "error"]
    dataset_overview: Dict[str, Any]
    column_profiles: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    chart_specs: List[Dict[str, Any]]
    data_preview: List[Dict[str, Any]] = []  # Primeras filas para previsualización
    explanations: Dict[str, str] = {}  # finding_id -> explanation text
    provenance: ProvenanceInfo
    contract_version: str = "v1"
    generated_at: datetime
