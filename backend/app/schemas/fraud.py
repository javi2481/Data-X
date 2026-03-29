from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import datetime

class FraudFinding(BaseModel):
    """Un hallazgo o indicador de posible fraude o manipulación."""
    layer: Literal["pdf_forensics", "visual_forensics", "numeric_semantic", "fiscal_validation"]
    indicator: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    evidence: str
    page: Optional[int] = None
    confidence: float  # 0.0 a 1.0

class FraudReport(BaseModel):
    """Reporte final consolidado de la capa FraudGuard."""
    session_id: str
    risk_score: float  # Puntuación ponderada de 0 a 100
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    findings: List[FraudFinding]
    disclaimer: str = "Estos son indicadores probabilísticos, no determinaciones legales."
    generated_at: datetime