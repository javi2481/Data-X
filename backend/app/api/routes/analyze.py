from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.repositories.mongo import session_repo
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.suggested_questions_service import get_suggested_questions_service
from fastapi import Depends
from app.core.rate_limit import limiter
from app.api.dependencies import get_current_user
from datetime import datetime
from typing import Any, List

router = APIRouter()
llm_service = LLMService()
suggested_questions_service = get_suggested_questions_service()

def _build_typed_sources(llm_sources: list[Any], findings: list[dict[str, Any]]) -> list[dict[str, Any] | str]:
    if not llm_sources:
        return [
            {
                "source_type": "finding",
                "source_id": finding.get("finding_id", ""),
                "evidence_ref": finding.get("finding_id", ""),
                "snippet": finding.get("title") or finding.get("what"),
            }
            for finding in findings
            if finding.get("finding_id")
        ]

    typed_sources: list[dict[str, Any] | str] = []
    for source in llm_sources:
        if isinstance(source, dict) and source.get("source_type") and source.get("source_id"):
            typed_sources.append(source)
            continue
        if isinstance(source, str):
            typed_sources.append(
                {
                    "source_type": "finding",
                    "source_id": source,
                    "evidence_ref": source,
                }
            )
            continue
        typed_sources.append(str(source))
    return typed_sources

def _rank_hybrid_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(sources, key=lambda item: float(item.get("score", 0.0)), reverse=True)

@router.post("", 
    response_model=AnalyzeResponse, 
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Análisis interactivo con motor LLM",
    description="Permite realizar consultas inteligentes sobre el dataset usando procesamiento de lenguaje natural."
)
@limiter.limit("60/hour")
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ejecuta un análisis inteligente sobre el dataset de la sesión.
    1. Recuperar sesión y SilverRecord de MongoDB
    2. Intentar cargar caché de embeddings o indexar findings
    3. Buscar findings relevantes para la query del usuario
    4. Pasar SOLO los findings relevantes como contexto al LLM
    5. El LLM genera una respuesta contextualizada y anclada
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

    findings = silver.get("findings", [])
    if not findings:
        return AnalyzeResponse(
            session_id=session_id,
            query=body.query,
            answer="No se detectaron hallazgos específicos en el dataset para analizar.",
            relevant_findings=[],
            sources=[],
            confidence="low"
        )

    # 2. Cargar o construir índice híbrido findings + chunks
    embedding_service = EmbeddingService()
    hybrid_cache = await session_repo.get_hybrid_embeddings_cache(session_id)
    document_chunks = await session_repo.get_document_chunks(session_id)
    findings_by_id = {f.get("finding_id"): f for f in findings if f.get("finding_id")}

    if hybrid_cache and hybrid_cache.get("model_name") == embedding_service.model_name:
        embedding_service.source_map = hybrid_cache.get("source_map", {})
        embedding_service.source_ids = hybrid_cache.get("source_ids", [])
        embedding_service.deserialize_index(hybrid_cache.get("faiss_index", b""))
    else:
        embedding_service.index_hybrid_sources(findings=findings, chunks=document_chunks)
        await session_repo.save_hybrid_embeddings_cache(
            {
                "session_id": session_id,
                "faiss_index": embedding_service.serialize_index(),
                "source_map": embedding_service.source_map,
                "source_ids": embedding_service.source_ids,
                "model_name": embedding_service.model_name,
                "created_at": datetime.now(),
                "stats": {
                    "findings_indexed": len(findings),
                    "chunks_indexed": len(document_chunks),
                    "total_indexed": len(embedding_service.source_ids),
                },
            }
        )

    # 3. Retrieval híbrido
    hybrid_sources = _rank_hybrid_sources(embedding_service.search_hybrid_sources(body.query, top_k=10))
    top_finding_sources = [s for s in hybrid_sources if s.get("source_type") == "finding"][:5]
    top_chunk_sources = [s for s in hybrid_sources if s.get("source_type") == "chunk"][:5]

    relevant_findings: list[dict[str, Any]] = []
    for source in top_finding_sources:
        finding = findings_by_id.get(source.get("source_id"))
        if finding:
            finding_with_score = dict(finding)
            finding_with_score["relevance_score"] = source.get("score", 0.0)
            relevant_findings.append(finding_with_score)

    # Backward fallback si no se recuperaron findings en índice híbrido
    if not relevant_findings:
        legacy_cache = await session_repo.get_embeddings_cache(session_id)
        if legacy_cache and legacy_cache.get("model_name") == embedding_service.model_name:
            embedding_service.findings_map = legacy_cache.get("findings_map", {})
            embedding_service.deserialize_index(legacy_cache.get("faiss_index", b""))
            relevant_findings = embedding_service.search(body.query, top_k=5)
        else:
            embedding_service.index_findings(findings)
            relevant_findings = embedding_service.search(body.query, top_k=5)
            await session_repo.save_embeddings_cache(
                {
                    "session_id": session_id,
                    "faiss_index": embedding_service.serialize_index(),
                    "findings_map": embedding_service.findings_map,
                    "model_name": embedding_service.model_name,
                    "created_at": datetime.now(),
                }
            )

    # 4. Responder con contexto híbrido (findings + chunks)
    llm_result = await llm_service.answer_query(
        body.query,
        relevant_findings,
        context_sources=top_finding_sources + top_chunk_sources,
    )
    
    # 5. El LLM genera una respuesta contextualizada y anclada
    return AnalyzeResponse(
        session_id=session_id,
        query=body.query,
        answer=llm_result.get("answer", "No se pudo generar una respuesta inteligente."),
        relevant_findings=relevant_findings,
        sources=_build_typed_sources(
            llm_result.get("sources_used", []) or (top_finding_sources + top_chunk_sources),
            relevant_findings,
        ),
        confidence=llm_result.get("confidence", "high" if relevant_findings else "low"),
        contract_version="v1"
    )


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
