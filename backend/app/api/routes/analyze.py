from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.repositories.mongo import session_repo
from app.services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

@router.post("", 
    response_model=AnalyzeResponse, 
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Análisis interactivo con motor LLM",
    description="Permite realizar consultas inteligentes sobre el dataset usando procesamiento de lenguaje natural."
)
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis inteligente sobre el dataset de la sesión.
    Llama al LLMService para procesar la consulta con el contexto completo.
    """
    if not request.session_id.strip():
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_SESSION_ID", "message": "El session_id no puede estar vacío"}
        )

    if not request.query.strip():
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_QUERY", "message": "La consulta no puede estar vacía"}
        )

    session_id = request.session_id
    
    # 1. Recuperar sesión y datos Silver
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )

    silver = await session_repo.get_silver(session_id)
    if not silver:
        return JSONResponse(
            status_code=404,
            content={"error_code": "ANALYSIS_NOT_FOUND", "message": "No se encontraron resultados de análisis para esta sesión"}
        )

    # 2. Recuperar Gold Record si existe
    gold = await session_repo.get_gold(session_id)
    
    # 3. Construir contexto para el LLM
    context = {
        "dataset_overview": silver.get("dataset_overview", {}),
        "column_profiles": silver.get("column_profiles", []),
        "findings": silver.get("findings", []),
        "executive_summary": gold.get("executive_summary") if gold else None,
        "filename": session.get("source_metadata", {}).get("filename", "dataset")
    }
    
    # 4. Llamar al motor LLM
    llm_result = await llm_service.answer_query(request.query, context)
    
    # 5. Filtrar findings y charts relevantes
    all_findings = silver.get("findings", [])
    relevant_finding_ids = llm_result.get("relevant_findings", [])
    relevant_findings = [f for f in all_findings if f["finding_id"] in relevant_finding_ids]
    
    all_charts = silver.get("chart_specs", [])
    # Por ahora incluimos un par de charts relevantes o los primeros por defecto
    relevant_charts = all_charts[:2] 
    
    # Si no hay findings filtrados pero el LLM no dio nada, mostrar algunos si la query parece pedir hallazgos
    if not relevant_findings and len(all_findings) > 0 and any(kw in request.query.lower() for kw in ["problema", "hallazgo", "alerta", "finding"]):
        relevant_findings = [f for f in all_findings if f["severity"] in ["critical", "warning"]][:5]

    return AnalyzeResponse(
        session_id=session_id,
        query=request.query,
        answer=llm_result.get("answer", "No se pudo generar una respuesta inteligente."),
        relevant_findings=relevant_findings,
        relevant_charts=relevant_charts,
        confidence=llm_result.get("confidence", "low"),
        contract_version="v1"
    )
