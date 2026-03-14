from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

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
