import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas.analyze import AnalyzeRequest, ErrorResponse
from app.schemas.analysis_response import AnalysisResponse
from app.repositories.mongo import session_repo
from app.services.analysis_agent import analysis_agent, AnalysisDeps
from app.services.suggested_questions_service import get_suggested_questions_service
from app.services.retrieval.base import BaseRetrievalService
from app.services.embedding_service import EmbeddingService
from fastapi import Depends
from app.core.rate_limit import limiter
from app.api.dependencies import get_current_user
from typing import Any, List

logger = structlog.get_logger(__name__)

router = APIRouter()
suggested_questions_service = get_suggested_questions_service()

def get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:
    """
    Patrón Strategy: Decide dinámicamente qué motor vectorial usar según el tenant.
    
    Ref: NXT-003 - OpenSearch para tiers Professional y Enterprise.
    
    Fallback order:
    1. OpenSearch (if enabled + tier allows)
    2. FAISS in-memory (always available)
    """
    from app.core.config import settings
    
    tier = current_user.get("tier", "lite")
    session_id = current_user.get("current_session_id", "unknown")
    
    # Tier Lite: Always FAISS
    if tier == "lite":
        logger.info(
            "retrieval_strategy_selected",
            tier=tier,
            strategy="faiss",
            user=current_user["sub"]
        )
        return EmbeddingService()
    
    # Tier Professional/Enterprise: Try OpenSearch first
    if tier in ["professional", "enterprise"] and settings.opensearch_enabled:
        try:
            from app.services.retrieval.opensearch_service import OpenSearchRetrievalService
            service = OpenSearchRetrievalService(session_id=session_id, tier=tier)
            if service.client:  # Connection successful
                logger.info(
                    "retrieval_strategy_selected",
                    tier=tier,
                    strategy="opensearch",
                    session_id=session_id,
                    user=current_user["sub"]
                )
                return service
        except Exception as e:
            logger.error(
                "opensearch_fallback",
                tier=tier,
                error=str(e),
                msg="Falling back to FAISS"
            )
    
    # Fallback: FAISS
    logger.info(
        "retrieval_strategy_selected",
        tier=tier,
        strategy="faiss_fallback",
        user=current_user["sub"]
    )
    return EmbeddingService()

@router.post("", 
    response_model=AnalysisResponse, 
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Análisis interactivo con motor LLM",
    description="Permite realizar consultas inteligentes delegando a un agente PydanticAI."
)
@limiter.limit("60/hour")
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint RAG Agéntico. Reemplaza al RAG lineal viejo.
    Delega la decisión de búsqueda y síntesis al agente de PydanticAI.
    """
    if not body.session_id.strip():
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_SESSION_ID", "message": "El session_id no puede estar vacío"}
        )

    if not body.query.strip():
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_QUERY", "message": "La consulta no puede estar vacía"}
        )

    session_id = body.session_id
    
    # 1. Recuperar sesión y SilverRecord de MongoDB
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )

    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(
            status_code=403,
            content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso para acceder a esta sesión"}
        )

    silver = await session_repo.get_silver(session_id)
    if not silver:
        return JSONResponse(
            status_code=404,
            content={"error_code": "ANALYSIS_NOT_FOUND", "message": "No se encontraron resultados de análisis para esta sesión"}
        )

    bronze = await session_repo.get_bronze(session_id) or {}
    findings = silver.get("findings", [])
    overview = session.get("dataset_overview", {})
    
    # 2. Inyección de Dependencia Dinámica (Strategy)
    retrieval_svc = get_retrieval_strategy(current_user)

    # 3. Cargar el índice FAISS persistido desde MongoDB
    # El índice fue serializado por el worker al finalizar el pipeline Silver.
    # Sin esta carga, retrieval_svc.index = None y search_hybrid_sources()
    # retorna siempre lista vacía (RAG roto en producción).
    cached = await session_repo.get_hybrid_embeddings_cache(session_id)
    if cached:
        index_bytes = cached.get("index_bytes", b"")
        if index_bytes:
            retrieval_svc.deserialize_index(bytes(index_bytes))
            retrieval_svc.source_map = cached.get("source_map", {})
            retrieval_svc.source_ids = cached.get("source_ids", [])
            logger.info(
                "faiss_index_loaded",
                session_id=session_id,
                sources=len(retrieval_svc.source_ids),
            )
        else:
            logger.warning("faiss_index_empty_cache", session_id=session_id)
    else:
        logger.warning("faiss_index_not_found", session_id=session_id)

    deps = AnalysisDeps(
        session_id=session_id,
        user_id=current_user["sub"],
        profiling_summary=None,
        findings=findings,
        chunks=[],
        dataset_meta={
            "filename": bronze.get("original_filename", "archivo"),
            "row_count": overview.get("row_count", 0),
            "column_count": overview.get("column_count", 0)
        },
        drift_report=session.get("drift_report"),
        fraud_report=session.get("fraud_report"),
        retrieval_service=retrieval_svc
    )

    try:
        logger.info("agent_run_start", session_id=session_id, query=body.query)
        result = await analysis_agent.run(body.query, deps=deps)
        logger.info("agent_run_complete", session_id=session_id)
        return result.data
    except Exception as e:
        logger.error("agent_run_failed", error=str(e), session_id=session_id)
        return JSONResponse(status_code=500, content={"error_code": "AGENT_ERROR", "message": f"Error en el razonamiento del agente: {str(e)}"})


@router.get("/{session_id}/suggested-questions",
    summary="Obtener preguntas sugeridas",
    description="Genera preguntas contextuales basadas en la estructura del documento y hallazgos."
)
@limiter.limit("100/hour")
async def get_suggested_questions(
    request: Request,
    session_id: str,
    max_questions: int = 8,
    current_user: dict = Depends(get_current_user)
):
    """
    Genera preguntas sugeridas basadas en:
    - Hallazgos detectados (categoría, severidad, columnas afectadas)
    - Estructura del documento (headings, secciones)
    - Tablas disponibles
    """
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión no existe"}
        )

    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(
            status_code=403,
            content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso"}
        )

    # Obtener contexto
    silver = await session_repo.get_silver(session_id)
    bronze = await session_repo.get_bronze(session_id)
    chunks = await session_repo.get_document_chunks(session_id)

    findings = silver.get("findings", []) if silver else []
    tables = bronze.get("tables", []) if bronze else []
    document_metadata = bronze.get("document_metadata", {}) if bronze else {}

    # Generar preguntas
    questions = suggested_questions_service.generate_questions(
        findings=findings,
        chunks=chunks,
        document_metadata=document_metadata,
        tables=tables,
        max_questions=max_questions,
    )

    return {
        "session_id": session_id,
        "questions": questions,
        "total": len(questions),
        "context": {
            "findings_count": len(findings),
            "chunks_count": len(chunks),
            "tables_count": len(tables),
        }
    }
