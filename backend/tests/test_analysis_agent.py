import pytest
from typing import List
from pydantic_ai.models.test import TestModel
from app.services.analysis_agent import analysis_agent, AnalysisDeps
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

    async def search_hybrid_sources(self, query: str, top_k: int = 5) -> List[dict]:
        return []


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