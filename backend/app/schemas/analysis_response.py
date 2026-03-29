from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class SourceReference(BaseModel):
    """Referencia a la evidencia documental que respalda una afirmación."""
    text: str = Field(description="Fragmento de texto de la fuente")
    page: Optional[int] = Field(default=None, description="Número de página")
    section: Optional[str] = Field(default=None, description="Sección del documento")
    chunk_id: Optional[str] = Field(default=None, description="ID del chunk en FAISS")

class AnalysisResponse(BaseModel):
    """
    Respuesta estructurada del agente de análisis impulsado por PydanticAI.
    """
    answer: str = Field(description="Respuesta en lenguaje natural, clara y concisa orientada al negocio.")
    key_findings: List[str] = Field(description="Lista de los principales hallazgos resumidos.")
    data_quality_warnings: List[str] = Field(description="Advertencias sobre la calidad de los datos si aplican para la consulta.")
    
    confidence: Literal["high", "medium", "low"] = Field(description="Nivel de confianza en la respuesta basado en la evidencia recuperada.")
    sources_used: List[SourceReference] = Field(default_factory=list, description="Fuentes del documento original que respaldan la respuesta.")
    
    # NXT-004: Anti-hallucination guardrails
    hallucination_risk: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Score de 0-1 indicando probabilidad de alucinación. 0=confiable, 1=alta alucinación."
    )
    warning: Optional[str] = Field(
        default=None,
        description="Warning message si hallucination_risk >= 0.5"
    )
    
    # Telemetría interna del razonamiento (Chain of Drafts)
    tools_called: List[str] = Field(default_factory=list, description="Lista de herramientas internas invocadas.")
    reasoning_steps: List[str] = Field(default_factory=list, description="Pasos lógicos breves que llevaron a la conclusión.")