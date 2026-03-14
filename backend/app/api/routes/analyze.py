from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.repositories.mongo import session_repo
from app.services.provenance import provenance_service
from app.services.stats_engine import StatsEngine
from app.services.llm_service import LLMService
from app.services.artifact_builder import ArtifactBuilder

router = APIRouter()
artifact_builder = ArtifactBuilder()
stats_engine = StatsEngine()
llm_service = LLMService()

@router.post("", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis sobre el dataset de la sesión.
    Recupera los datos de MongoDB.
    """
    session_id = request.session_id
    
    # Buscar en MongoDB
    session_data = await session_repo.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    # En esta fase, como el DF no se guarda en Mongo, 
    # los artifacts se generan basándose en el schema_info persistido
    # o tendríamos que re-leer el archivo.
    # Dado que el objetivo de Emergent es mejorar esto, por ahora
    # generamos lo que podemos con la info que hay en session_data.
    
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
    else:
        artifacts.append(artifact_builder.build_metric_set(schema_info))

    # 3. Stats avanzadas (si hay perfil)
    # Por ahora enviamos un artifact de tipo summary con algunas stats
    if profile:
        stats_text = "Estadísticas por columna:\n"
        for col, p in profile.items():
            if "mean" in p:
                stats_text += f"- {col}: media={p['mean']:.2f}, med={p['median']:.2f}, std={p['std']:.2f}\n"
            elif "top_values" in p:
                top = list(p['top_values'].keys())[:2]
                stats_text += f"- {col}: únicos={p['unique_count']}, top={top}\n"
        
        artifacts.append(artifact_builder.build_summary(stats_text))
    
    # 3. Vista previa (Simulada si no hay DF en memoria)
    # TODO: Implementar persistencia de DF (Parquet/S3) para recuperación real
    artifacts.append({
        "artifact_type": "table",
        "title": "Vista previa (persistida)",
        "data": {
            "columns": schema_info["columns"],
            "rows": [] # Placeholder hasta implementar persistencia de DF
        }
    })
    
    # 4. Resumen inteligente con LiteLLM
    filename = session_data['source_metadata']['filename']
    if profile:
        summary_text = await llm_service.analyze_query(request.query, profile)
    else:
        summary_text = (
            f"Análisis para '{filename}'. "
            f"Datos persistidos en MongoDB. {schema_info['row_count']} filas detectadas."
        )
    
    # Registrar paso de análisis en provenance
    await provenance_service.add_step(session_id, "analyze", {"query": request.query})
    
    # Obtener provenance actualizado
    provenance_steps = await provenance_service.get_steps(session_id)
    
    return AnalyzeResponse(
        session_id=session_id,
        artifacts=artifacts,
        summary=summary_text,
        provenance={
            "source": session_data['source_metadata']['filename'],
            "steps": provenance_steps
        }
    )
