from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class ProvenanceInfo(BaseModel):
    source: str
    ingestion_method: str
    quality_decision: str
    processing_steps: List[str] = []
    affected_columns: List[str] = []
    schema_version: str = "legacy_v1"
    provenance_refs: List[Dict[str, Any]] = []

class AnalysisReport(BaseModel):
    session_id: str
    status: Literal["completed", "partial", "error"]
    dataset_overview: Dict[str, Any]
    column_profiles: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    chart_specs: List[Dict[str, Any]]
    data_preview: List[Dict[str, Any]] = []  # Primeras filas para previsualización
    executive_summary: Optional[str] = None
    explanations: Dict[str, str] = {}  # finding_id -> explanation text
    enriched_explanations: Dict[str, str] = {}  # finding_id -> LLM explanation (si disponible)
    provenance: ProvenanceInfo
    document_context: Optional[str] = None
    document_tables: List[Dict[str, Any]] = []
    document_metadata: Dict[str, Any] = {}
    selected_table_index: int = 0
    llm_cost_usd: float = 0.0
    llm_model_used: str = ""
    llm_calls_count: int = 0
    contract_version: str = "v1"
    generated_at: datetime
