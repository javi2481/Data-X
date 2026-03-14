from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.api.routes.sessions import SESSION_STORE
from app.services.artifact_builder import ArtifactBuilder

router = APIRouter()
artifact_builder = ArtifactBuilder()

@router.post("", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Ejecuta un análisis sobre el dataset de la sesión.
    En esta fase, genera artifacts estáticos basados en el dataset.
    """
    session_id = request.session_id
    
    if session_id not in SESSION_STORE:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session_data = SESSION_STORE[session_id]
    df = session_data["df"]
    schema_info = session_data["schema_info"]
    alerts = session_data.get("alerts", [])
    
    # Construir artifacts
    artifacts = []
    
    # 1. Alertas de calidad (si existen)
    if alerts:
        artifacts.append(artifact_builder.build_alerts(alerts))
    
    # 2. Métricas generales
    artifacts.append(artifact_builder.build_metric_set(schema_info))
    
    # 3. Vista previa de datos
    artifacts.append(artifact_builder.build_table_artifact(df, title="Vista previa de datos (top 50)"))
    
    # 4. Resumen (placeholder en esta fase)
    summary_text = (
        f"Análisis completado para el archivo '{session_data['source_metadata']['filename']}'. "
        f"Se procesaron {schema_info['row_count']} filas y {len(schema_info['columns'])} columnas. "
        "El sistema está listo para consultas avanzadas."
    )
    
    return AnalyzeResponse(
        session_id=session_id,
        artifacts=artifacts,
        summary=summary_text,
        provenance={
            "source": session_data['source_metadata']['filename'],
            "steps": ["ingest", "normalize", "validate", "artifact_generation"]
        }
    )
