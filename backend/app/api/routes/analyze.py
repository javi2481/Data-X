from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.repositories.mongo import session_repo

router = APIRouter()

@router.post("", 
    response_model=AnalyzeResponse, 
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Análisis interactivo (Legacy/Compat)",
    description="Permite realizar consultas sobre el dataset. En Corte 1 devuelve resultados estáticos o el reporte completo para mantener compatibilidad con el frontend."
)
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis sobre el dataset de la sesión.
    Adaptado para devolver el reporte completo si la query es genérica.
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
    
    # Buscar datos Silver en MongoDB
    silver = await session_repo.get_silver(session_id)
    session = await session_repo.get_session(session_id)
    
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )

    if not silver:
        return JSONResponse(
            status_code=404,
            content={"error_code": "ANALYSIS_NOT_FOUND", "message": "No se encontraron resultados de análisis para esta sesión"}
        )
    
    # Mantenemos compatibilidad con el frontend transformando Findings y ChartSpecs a Artifacts genéricos
    artifacts = []
    
    # Convertir Findings a Alertas/Texto
    findings = silver.get("findings", [])
    if findings:
        artifacts.append({
            "artifact_type": "alerts",
            "title": "Hallazgos detectados",
            "data": {
                "alerts": [
                    {"type": f["severity"], "message": f["title"], "details": f["explanation"]}
                    for f in findings
                ]
            }
        })
    
    # Convertir ChartSpecs a Artifacts de tipo chart_config
    chart_specs = silver.get("chart_specs", [])
    for spec in chart_specs:
        artifacts.append({
            "artifact_type": "chart_config",
            "title": spec["title"],
            "data": spec # El frontend deberá estar preparado para recibir ChartSpec o mapearlo
        })

    # Resumen estático (Corte 1)
    overview = silver.get("dataset_overview", {})
    filename = session.get("source_metadata", {}).get("filename", "dataset")
    summary_text = f"Análisis del dataset '{filename}'. Se encontraron {len(findings)} hallazgos relevantes."

    return AnalyzeResponse(
        session_id=session_id,
        artifacts=artifacts,
        summary=summary_text,
        contract_version="v1"
    )
