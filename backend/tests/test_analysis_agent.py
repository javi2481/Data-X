import pytest
from typing import List, Dict, Any
from pydantic_ai.models.test import TestModel
from pydantic_ai.exceptions import ModelRetry
from app.services.analysis_agent import analysis_agent, AnalysisDeps, enforce_no_hallucinated_metrics
from app.schemas.analysis_response import AnalysisResponse
from app.services.retrieval.base import BaseRetrievalService


class _MockRetrieval(BaseRetrievalService):
    @property
    def model_name(self) -> str:
        return "mock"

    def index_findings(self, findings: List[dict]) -> None:
        pass

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        return []

    async def search_hybrid_sources(self, query: str, top_k: int = 8, **filters) -> List[Dict[str, Any]]:
        return []

    async def index_hybrid_sources(self, findings: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> None:
        pass


@pytest.mark.asyncio
async def test_analysis_agent_returns_valid_schema():
    """
    Prueba que el agente PydanticAI devuelve correctamente el schema
    AnalysisResponse sin hacer llamadas reales al LLM (ahorrando tokens/costos).
    """
    # 1. Preparamos dependencias falsas para simular la sesión
    mock_deps = AnalysisDeps(
        session_id="test_sess_123",
        user_id="test_user",
        profiling_summary=None,
        findings=[{"category": "data_gap", "severity": "critical", "what": "Faltan valores"}],
        chunks=[],
        dataset_meta={"filename": "test_doc.pdf", "row_count": 500, "column_count": 10},
        retrieval_service=_MockRetrieval(),
        drift_report=None
    )
    
    # 2. Ejecutamos usando TestModel() para bypassear la API real
    with analysis_agent.override(model=TestModel()):
        result = await analysis_agent.run(
            "¿Qué problemas de calidad tiene el documento?", 
            deps=mock_deps
        )
        
        # 3. Verificamos que el resultado cumpla estrictamente con Pydantic
        assert isinstance(result.output, AnalysisResponse)
        assert result.output.confidence in ["high", "medium", "low"]
        assert isinstance(result.output.answer, str)
        assert isinstance(result.output.sources_used, list)


class _MockRunContext:
    """Mock simple para simular el RunContext inyectado por PydanticAI."""
    def __init__(self, deps):
        self.deps = deps

def test_validator_blocks_hallucinations():
    """
    Prueba el guardrail matemático: el agente NO puede devolver
    métricas numéricas que no existan en su contexto determinístico.
    """
    mock_deps = AnalysisDeps(
        session_id="test_sess",
        user_id="test_user",
        profiling_summary=None,
        findings=[{"what": "Los ingresos confirmados son de 5000 dólares.", "category": "pattern"}],
        chunks=[],
        dataset_meta={"filename": "test.csv", "row_count": 100, "column_count": 5},
        retrieval_service=_MockRetrieval(),
        drift_report=None,
        fraud_report=None
    )
    ctx = _MockRunContext(deps=mock_deps)
    
    # Escenario 1: Respuesta válida (5000 está en los findings, 100 en los metadatos)
    valid_result = AnalysisResponse(
        answer="Los ingresos fueron de 5000 dólares distribuidos en 100 filas.",
        key_findings=[], data_quality_warnings=[], confidence="high", sources_used=[], tools_called=[], reasoning_steps=[]
    )
    assert enforce_no_hallucinated_metrics(ctx, valid_result) == valid_result
    
    # Escenario 2: Respuesta con alucinación (9999 NO está en el contexto)
    invalid_result = AnalysisResponse(
        answer="Los ingresos proyectados alcanzan los 9999 dólares.",
        key_findings=[], data_quality_warnings=[], confidence="high", sources_used=[], tools_called=[], reasoning_steps=[]
    )
    with pytest.raises(ModelRetry, match="GUARDRAIL ERROR: Has incluido el número/métrica '9999'"):
        enforce_no_hallucinated_metrics(ctx, invalid_result)
        
    # Escenario 3: Respuesta con años y números pequeños permitidos (< 12 y años)
    ignored_numbers_result = AnalysisResponse(
        answer="En el año 2024, se encontraron 3 problemas principales.",
        key_findings=[], data_quality_warnings=[], confidence="high", sources_used=[], tools_called=[], reasoning_steps=[]
    )
    assert enforce_no_hallucinated_metrics(ctx, ignored_numbers_result) == ignored_numbers_result