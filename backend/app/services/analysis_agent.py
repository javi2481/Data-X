from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings
from app.schemas.profiling import ProfilingSummary
from app.schemas.analysis_response import AnalysisResponse
from app.services.retrieval.base import BaseRetrievalService

# Para LiteLLM y OpenAI API (OpenRouter o compatible)
model = OpenAIModel(
    model_name=settings.litellm_model,
    provider=OpenAIProvider(api_key=settings.litellm_api_key or "dummy-key"),
)

@dataclass
class AnalysisDeps:
    """Contexto determinístico inyectado por request. Nada se guarda globalmente."""
    session_id: str
    user_id: str
    profiling_summary: Optional[ProfilingSummary]
    findings: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    dataset_meta: Dict[str, Any]
    retrieval_service: BaseRetrievalService
    drift_report: Optional[Dict[str, Any]] = None
    fraud_report: Optional[Dict[str, Any]] = None

# Definición central del Agente PydanticAI
analysis_agent = Agent(
    model,
    output_type=AnalysisResponse,
    deps_type=AnalysisDeps,
    system_prompt="""Sos un analista de datos experto.
Aplica la técnica CoD (Chain of Drafts) y AoT (Atom of Thoughts) para tu razonamiento:
1. ATOM: Descompón la pregunta compleja del usuario en múltiples "átomos" o pasos de investigación independientes.
2. TOOL: Por cada átomo lógico, determina qué herramienta necesitas y úsala para recuperar contexto.
3. DRAFT: Antes de emitir tu respuesta final, genera un borrador lógico interno ultra-conciso cruzando los hallazgos.
Basa tus conclusiones ESTRICTAMENTE en los resultados de las tools proporcionadas. 
NUNCA computes datos directamente (ni sumas, ni promedios), delega la búsqueda a tus tools."""
)

@analysis_agent.tool
async def search_documents(ctx: RunContext[AnalysisDeps], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca fragmentos (chunks) documentales relevantes.
    Útil para recuperar texto específico del PDF original (páginas, secciones).
    """
    # El agente ya no sabe (ni le importa) si está buscando en FAISS o en OpenSearch.
    # Solo consume el contrato de BaseRetrievalService.
    return await ctx.deps.retrieval_service.search_hybrid_sources(query, top_k=top_k)

@analysis_agent.tool
async def get_dataset_profile(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Retorna el resumen estadístico global del dataset (filas, nulos, métricas generales).
    Útil cuando se te piden visiones a alto nivel del archivo subido.
    """
    if ctx.deps.profiling_summary is None:
        return "No hay perfil de dataset disponible."
    
    meta = ctx.deps.dataset_meta
    return f"""Perfil del Dataset: {meta.get('filename', 'dataset')}
- Filas: {meta.get('row_count', 0)}, Columnas: {meta.get('column_count', 0)}"""

@analysis_agent.tool
async def get_findings(ctx: RunContext[AnalysisDeps], category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retorna las alertas (findings) calculadas previamente.
    Útil para conocer oportunidades de mejora, riesgos o problemas de calidad de datos.
    """
    findings = ctx.deps.findings
    if category:
        findings = [f for f in findings if f.get("category") == category]
    return findings[:10]

@analysis_agent.tool
async def get_column_details(ctx: RunContext[AnalysisDeps], column_name: str) -> Dict[str, Any]:
    """Retorna el perfil completo (estadísticas) de una sola columna específica."""
    if ctx.deps.profiling_summary is None or column_name not in ctx.deps.profiling_summary.columns:
        return {"error": f"Columna '{column_name}' no encontrada"}
    return ctx.deps.profiling_summary.columns[column_name].model_dump()

@analysis_agent.tool
async def get_data_drift_report(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Retorna las métricas y alertas de Data Drift (desviación de datos respecto a su versión histórica).
    Útil para analizar si el comportamiento o distribución de las columnas cambió significativamente con el tiempo.
    """
    if not ctx.deps.drift_report:
        return "No hay reporte de Data Drift disponible para este dataset (no se comparó contra un baseline)."
    
    import json
    return f"Reporte de Data Drift:\n{json.dumps(ctx.deps.drift_report, indent=2, ensure_ascii=False)}"

@analysis_agent.tool
async def get_fraud_report(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Retorna el reporte de fraude (FraudGuard) del documento actual.
    Útil para responder preguntas sobre la autenticidad, riesgo de falsificación, manipulación visual (ELA), 
    anomalías numéricas (Ley de Benford) o inconsistencias fiscales en el documento.
    """
    if not ctx.deps.fraud_report:
        return "No hay reporte de fraude disponible para este documento (posiblemente no se solicitó o no aplica)."
    
    import json
    return f"Reporte de Fraude (FraudGuard):\n{json.dumps(ctx.deps.fraud_report, indent=2, ensure_ascii=False)}"