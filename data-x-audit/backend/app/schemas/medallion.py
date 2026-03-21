from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class DocumentTableRef(BaseModel):
    table_id: str
    index: int
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    headers: List[str] = []
    confidence: Optional[float] = None

class DocumentProvenanceRef(BaseModel):
    source_type: Literal["table", "section", "page_reference", "chunk", "finding"] = "table"
    ref_id: str
    page: Optional[int] = None
    section: Optional[str] = None
    table_id: Optional[str] = None
    chunk_id: Optional[str] = None
    snippet: Optional[str] = None

class BronzeRecord(BaseModel):
    """Raw ingestion data"""
    session_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    ingestion_source: Literal["docling", "pandas_fallback"]
    quality_decision: Literal["accept", "warning", "reject"]
    quality_scores: Dict[str, Any] = {}
    source_metadata: Dict[str, Any] = {}
    schema_version: str = "legacy_v1"
    quality_baseline: Dict[str, Any] = {}
    tables_found: int = 1
    selected_table_index: int = 0
    narrative_context: Optional[str] = None  # Markdown del documento
    table_confidence: Optional[float] = None
    document_payload: Optional[Dict[str, Any]] = None
    document_metadata: Dict[str, Any] = {}
    tables: List[DocumentTableRef] = []
    provenance_refs: List[DocumentProvenanceRef] = []
    ingested_at: datetime

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    count: int
    null_count: int
    null_percent: float
    unique_count: int
    cardinality: float
    # Numéricas
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    # Strings
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None

class DatasetOverview(BaseModel):
    row_count: int
    column_count: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    total_nulls: int
    total_null_percent: float
    duplicate_rows: int
    duplicate_percent: float

class SilverRecord(BaseModel):
    """Processed + EDA results"""
    session_id: str
    dataset_overview: DatasetOverview
    column_profiles: List[ColumnProfile]
    findings: List[Dict[str, Any]]  # List of Finding dicts
    chart_specs: List[Dict[str, Any]]  # List of ChartSpec dicts
    data_preview: List[Dict[str, Any]] = []  # Primeras N filas del dataset
    processed_at: datetime

class GoldRecord(BaseModel):
    """Enriched insights using LLM"""
    session_id: str
    executive_summary: str
    enriched_explanations: Dict[str, str]  # finding_id -> LLM explanation
    recommendations: List[str]
    llm_cost_usd: float = 0.0
    llm_model_used: str = ""
    llm_calls_count: int = 0
    generated_at: datetime
