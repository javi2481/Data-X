from fastapi import APIRouter, HTTPException, Request
from typing import List
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.repositories.mongo import session_repo
from app.services.provenance import provenance_service
from app.services.stats_engine import StatsEngine
from app.services.llm_service import LLMService
from app.services.artifact_builder import ArtifactBuilder

router = APIRouter()
artifact_builder = ArtifactBuilder()
stats_engine = StatsEngine()
llm_service = LLMService()

@router.post("", response_model=AnalyzeResponse, responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis sobre el dataset de la sesión.
    Recupera los datos de MongoDB.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    session_id = request.session_id
    
    # Buscar en MongoDB
    session_data = await session_repo.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    schema_info = session_data["schema_info"]
    profile = session_data.get("profile", {})
    alerts = session_data.get("alerts", [])
    
    # Construir artifacts
    artifacts = []
    
    # 1. Alertas de calidad (si existen)
    if alerts:
        artifacts.append(artifact_builder.build_alerts(alerts))
    
    # 2. Métricas generales enriquecidas con Profile
    if profile:
        num_cols = len(schema_info["columns"])
        num_numeric = len([c for c, p in profile.items() if "mean" in p])
        num_text = len([c for c, p in profile.items() if "top_values" in p])
        
        metrics_artifact = artifact_builder.build_metric_set(schema_info)
        metrics_artifact["data"]["metrics"].extend([
            {"label": "Columnas numéricas", "value": num_numeric},
            {"label": "Columnas de texto", "value": num_text}
        ])
        artifacts.append(metrics_artifact)

        # 3. Gráficos automáticos (NUEVO Fase 6)
        # Tomar hasta 2 columnas numéricas para un bar chart de promedios
        numeric_cols = [c for c, p in profile.items() if "mean" in p]
        if numeric_cols:
            x_data = numeric_cols[:5] # Top 5 cols
            y_data = [profile[c]["mean"] for c in x_data]
            artifacts.append(artifact_builder.build_chart_config(
                title="Promedios por Columna",
                chart_type="bar",
                x_data=x_data,
                y_data=y_data,
                x_label="Columna",
                y_label="Promedio"
            ))
    else:
        artifacts.append(artifact_builder.build_metric_set(schema_info))

    # 4. Resumen inteligente con LiteLLM (con timeout y fallback)
    filename = session_data['source_metadata']['filename']
    try:
        if profile:
            # LLMService ya debería manejar el timeout internamente o lo manejamos aquí
            import asyncio
            summary_text = await asyncio.wait_for(
                llm_service.analyze_query(request.query, profile),
                timeout=30.0
            )
        else:
            summary_text = f"Análisis para '{filename}'. Sin perfil detallado."
    except Exception as e:
        summary_text = f"No se pudo generar el resumen inteligente: {str(e)}. Mostrando métricas base."
    
    # 5. Vista previa (Placeholder)
    artifacts.append({
        "artifact_type": "table",
        "title": "Vista previa de datos",
        "data": {
            "columns": schema_info["columns"],
            "rows": [] 
        }
    })
    
    # Registrar paso de análisis en provenance
    await provenance_service.add_step(session_id, "analyze", {"query": request.query})
    
    # Obtener provenance actualizado
    provenance_steps = await provenance_service.get_steps(session_id)
    
    return AnalyzeResponse(
        session_id=session_id,
        artifacts=artifacts,
        summary=summary_text,
        provenance={
            "source": filename,
            "steps": provenance_steps
        }
    )
