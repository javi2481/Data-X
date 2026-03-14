from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class Evidence(BaseModel):
    metric: str
    value: float | int | str
    threshold: Optional[float | int] = None
    detail: Optional[str] = None

class Finding(BaseModel):
    finding_id: str
    category: Literal[
        "high_null_rate", "duplicate_rows", "constant_column",
        "high_cardinality", "low_cardinality", "type_mismatch",
        "column_stats", "data_quality_warning", "schema_warning",
        "strong_correlation", "outlier_detected", "skewed_distribution"
    ]
    severity: Literal["critical", "warning", "info"]
    title: str
    technical_summary: str
    explanation: str  # Generado por template estático en Corte 1
    impact: Optional[str] = None
    affected_columns: List[str] = []
    evidence: List[Evidence] = []
    recommendations: List[str] = []
