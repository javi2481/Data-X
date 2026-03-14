from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from app.schemas.report import AnalysisReport, ProvenanceInfo
from app.repositories.mongo import session_repo

router = APIRouter()

@router.get("/{session_id}/report", 
    response_model=AnalysisReport,
    summary="Obtener reporte completo",
    description="Genera y retorna un AnalysisReport completo que incluye hallazgos, perfiles de columna y especificaciones de gráficos."
)
async def get_analysis_report(session_id: str):
    """
    Devuelve el AnalysisReport completo a partir de los datos Silver.
    """
    silver = await session_repo.get_silver(session_id)
    bronze = await session_repo.get_bronze(session_id)
    session = await session_repo.get_session(session_id)
    
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )
        
    if not silver:
        # Verificar si la sesión falló
        if session.get("status") == "error":
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "ANALYSIS_FAILED", 
                    "message": "El análisis de esta sesión falló durante el procesamiento",
                    "details": {"quality_decision": session.get("quality_decision")}
                }
            )
        
        return JSONResponse(
            status_code=404,
            content={"error_code": "REPORT_NOT_FOUND", "message": "No se encontró el reporte para esta sesión"}
        )
    
    # Construir provenance
    provenance = ProvenanceInfo(
        source=bronze.get("original_filename", "unknown") if bronze else "unknown",
        ingestion_method=bronze.get("ingestion_source", "unknown") if bronze else "unknown",
        quality_decision=bronze.get("quality_decision", "unknown") if bronze else "unknown",
        processing_steps=["ingest", "normalize", "profile", "finding_detection", "chart_generation"],
        affected_columns=[p["name"] for p in silver.get("column_profiles", [])]
    )
    
    # Explicaciones (finding_id -> explanation)
    explanations = {f["finding_id"]: f["explanation"] for f in silver.get("findings", [])}
    
    # Resumen estático para el summary (en Corte 1)
    overview = silver.get("dataset_overview", {})
    finding_count = len(silver.get("findings", []))
    critical = len([f for f in silver.get("findings", []) if f["severity"] == "critical"])
    warnings = len([f for f in silver.get("findings", []) if f["severity"] == "warning"])
    info = len([f for f in silver.get("findings", []) if f["severity"] == "info"])
    
    filename = bronze.get("original_filename", "dataset") if bronze else "dataset"
    summary = f"Dataset '{filename}' con {overview.get('row_count', 0)} filas y {overview.get('column_count', 0)} columnas. Se detectaron {finding_count} findings: {critical} críticos, {warnings} advertencias, {info} informativos."

    return AnalysisReport(
        session_id=session_id,
        status="completed",
        dataset_overview=overview,
        column_profiles=silver.get("column_profiles", []),
        findings=silver.get("findings", []),
        chart_specs=silver.get("chart_specs", []),
        data_preview=silver.get("data_preview", []),
        explanations=explanations,
        provenance=provenance,
        contract_version="v1",
        generated_at=datetime.utcnow()
    )
