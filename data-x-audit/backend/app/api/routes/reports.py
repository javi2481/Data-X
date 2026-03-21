from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from app.schemas.report import AnalysisReport, ProvenanceInfo
from app.repositories.mongo import session_repo
from fastapi import Depends
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/{session_id}/report", 
    response_model=AnalysisReport,
    summary="Obtener reporte completo",
    description="Genera y retorna un AnalysisReport completo que incluye hallazgos, perfiles de columna y especificaciones de gráficos."
)
async def get_analysis_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Devuelve el AnalysisReport completo a partir de los datos Silver.
    """
    silver = await session_repo.get_silver(session_id)
    bronze = await session_repo.get_bronze(session_id)
    session = await session_repo.get_session(session_id)
    gold = await session_repo.get_gold(session_id)
    
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
        affected_columns=[p["name"] for p in silver.get("column_profiles", [])],
        schema_version=bronze.get("schema_version", "legacy_v1") if bronze else "legacy_v1",
        provenance_refs=bronze.get("provenance_refs", []) if bronze else [],
    )
    
    # Explicaciones (finding_id -> explanation/what)
    explanations = {f["finding_id"]: f.get("explanation", f.get("what", "")) for f in silver.get("findings", [])}
    
    # Resumen estático para el summary (en Corte 1)
    overview = silver.get("dataset_overview", {})
    finding_count = len(silver.get("findings", []))
    critical = len([f for f in silver.get("findings", []) if f["severity"] == "critical"])
    important = len([f for f in silver.get("findings", []) if f["severity"] == "important"])
    insight = len([f for f in silver.get("findings", []) if f["severity"] == "insight"])
    
    filename = bronze.get("original_filename", "dataset") if bronze else "dataset"
    summary = f"Dataset '{filename}' con {overview.get('row_count', 0)} filas y {overview.get('column_count', 0)} columnas. Se detectaron {finding_count} findings: {critical} críticos, {important} importantes, {insight} insights."

    executive_summary = gold.get("executive_summary") if gold else summary
    enriched_explanations = gold.get("enriched_explanations", {}) if gold else {}
    
    # Campos de costo LLM
    llm_cost_usd = gold.get("llm_cost_usd", 0.0) if gold else 0.0
    llm_model_used = gold.get("llm_model_used", "") if gold else ""
    llm_calls_count = gold.get("llm_calls_count", 0) if gold else 0

    return AnalysisReport(
        session_id=session_id,
        status="completed",
        dataset_overview=overview,
        column_profiles=silver.get("column_profiles", []),
        findings=silver.get("findings", []),
        chart_specs=silver.get("chart_specs", []),
        data_preview=silver.get("data_preview", []),
        executive_summary=executive_summary,
        explanations=explanations,
        enriched_explanations=enriched_explanations,
        provenance=provenance,
        document_context=bronze.get("narrative_context") if bronze else None,
        document_tables=bronze.get("tables", []) if bronze else [],
        document_metadata=bronze.get("document_metadata", {}) if bronze else {},
        selected_table_index=bronze.get("selected_table_index", 0) if bronze else 0,
        llm_cost_usd=llm_cost_usd,
        llm_model_used=llm_model_used,
        llm_calls_count=llm_calls_count,
        contract_version="v1",
        generated_at=datetime.utcnow()
    )
