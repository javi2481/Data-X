from fastapi import APIRouter, HTTPException, Request
from typing import List
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.repositories.mongo import session_repo

router = APIRouter()

@router.post("", response_model=AnalyzeResponse, responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis sobre el dataset de la sesión.
    Adaptado para devolver el reporte completo si la query es genérica.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    session_id = request.session_id
    
    # Buscar datos Silver en MongoDB
    silver = await session_repo.get_silver(session_id)
    session = await session_repo.get_session(session_id)
    
    if not silver or not session:
        raise HTTPException(status_code=404, detail="Sesión o análisis no encontrado")
    
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
