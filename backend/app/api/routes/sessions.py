from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime, timezone
from functools import lru_cache
import uuid
import io
import csv
from typing import Any, List
from pydantic import BaseModel

from app.schemas.session import SessionResponse
from app.schemas.analyze import ErrorResponse
from app.schemas.medallion import BronzeRecord, SilverRecord, GoldRecord, DatasetOverview, ColumnProfile
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.profiler import ProfilerService
from app.services.docling_quality_gate import DoclingQualityGate
from app.services.finding_builder import FindingBuilder
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.eda_extended import EDAExtendedService
from app.services.llm_service import LLMService
from app.services.schema_validator import SchemaValidator
from app.services.statistical_tests import StatisticalTestsService
from app.services.document_chunking_service import DocumentChunkingService
from app.services.docling_chunking_service import get_docling_chunking_service
from app.services.ingestion.distributed_strategy import DistributedIngestionService
from app.services.embedding_service import EmbeddingService
from app.repositories.mongo import session_repo
from app.api.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.services.job_queue import JobQueueService
import tempfile
import os

router = APIRouter()

class CompareRequest(BaseModel):
    target_session_id: str

class PaginatedSessionList(BaseModel):
    items: List[SessionResponse]
    total: int
    limit: int
    offset: int

# ── ACT-010: FastAPI Dependency Injection con @lru_cache ─────────────────────
# Antes: 12 singletons globales a nivel de módulo, imposibles de reemplazar en
# tests y que cargan todos los modelos ML al iniciar FastAPI.
# Después: factories con lru_cache(maxsize=1) — singleton reemplazable via
# app.dependency_overrides en tests, y lazy-loaded en el primer request.

@lru_cache(maxsize=1)
def get_ingest_service() -> IngestService:
    return IngestService()

@lru_cache(maxsize=1)
def get_normalization_service() -> NormalizationService:
    return NormalizationService()

@lru_cache(maxsize=1)
def get_profiler_service() -> ProfilerService:
    return ProfilerService()

@lru_cache(maxsize=1)
def get_quality_gate() -> DoclingQualityGate:
    return DoclingQualityGate()

@lru_cache(maxsize=1)
def get_finding_builder() -> FindingBuilder:
    return FindingBuilder()

@lru_cache(maxsize=1)
def get_chart_spec_generator() -> ChartSpecGenerator:
    return ChartSpecGenerator()

@lru_cache(maxsize=1)
def get_eda_service() -> EDAExtendedService:
    return EDAExtendedService()

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService()

@lru_cache(maxsize=1)
def get_schema_validator() -> SchemaValidator:
    return SchemaValidator()

@lru_cache(maxsize=1)
def get_stat_tests_service() -> StatisticalTestsService:
    return StatisticalTestsService()

@lru_cache(maxsize=1)
def get_chunking_service() -> DocumentChunkingService:
    return DocumentChunkingService()

@lru_cache(maxsize=1)
def get_job_queue_service() -> JobQueueService:
    return JobQueueService()
# ─────────────────────────────────────────────────────────────────────────────

def get_ingestion_strategy(current_user: dict) -> Any:
    tier = current_user.get("tier", "lite")
    if tier == "enterprise":
        import structlog
        structlog.get_logger(__name__).info("strategy_injection", strategy="distributed_ingestion", user=current_user["sub"])
        return DistributedIngestionService()
    return get_ingest_service()

@router.post("",
    response_model=SessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Crear nueva sesión de análisis",
    description="Carga un archivo CSV, ejecuta el pipeline Medallion (Bronze/Silver) y genera los hallazgos iniciales."
)
@limiter.limit("20/hour")
async def create_session(
    request: Request,
    file: UploadFile = File(...),
    table_index: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    job_queue: JobQueueService = Depends(get_job_queue_service),
):
    """
    Crea una sesión a partir de un archivo subido.
    Pipeline Medallion: Bronze -> Silver.
    """
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_FILE", "message": "No se proporcionó un nombre de archivo"}
        )
    
    # Soporte para CSV, XLSX, XLS, PDF y DOCX
    allowed_extensions = [".csv", ".xlsx", ".xls", ".pdf", ".docx"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "UNSUPPORTED_FORMAT", 
                "message": f"Formato de archivo no soportado. Formatos aceptados: {', '.join(allowed_extensions)}"
            }
        )

    MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB
    
    try:
        content = await file.read()
        
        # Validar tamaño máximo
        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={"error_code": "FILE_TOO_LARGE", "message": "El archivo es demasiado grande (máx 50MB)"}
            )
            
        # Validar MIME type real y Magic Numbers
        filename_lower = file.filename.lower()
        content_type = file.content_type
        
        if filename_lower.endswith(".pdf"):
            if not content.startswith(b"%PDF"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo PDF no tiene una firma válida (%PDF)"}
                )
        elif filename_lower.endswith(".xlsx"):
            if not content.startswith(b"PK\x03\x04"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo XLSX no tiene una firma válida (PK header)"}
                )
        elif filename_lower.endswith(".docx"):
            if not content.startswith(b"PK\x03\x04"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo DOCX no tiene una firma válida (PK header)"}
                )
        elif filename_lower.endswith(".csv"):
            if content_type not in ["text/csv", "text/plain"]:
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo CSV debe ser text/csv o text/plain"}
                )
        
        if len(content) == 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_FILE", "message": "El archivo está vacío (0 bytes)"}
            )

        # Guardar archivo en disco temporal para que el worker de ARQ lo levante en background
        ext = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        session_id = f"sess_{uuid.uuid4()}"
        ingested_at = datetime.now(timezone.utc)

        # Crear la sesión inicial en estado "queued"
        session_data = {
            "session_id": session_id,
            "user_id": current_user["sub"],
            "status": "queued",
            "created_at": ingested_at.isoformat(),
            "source_metadata": {
                "filename": file.filename,
                "content_type": content_type,
                "size_bytes": len(content)
            },
            "contract_version": "v1"
        }
        await session_repo.create_session(session_data.copy())
        
        # Encolar el trabajo en Redis vía ARQ
        await job_queue.enqueue_pipeline_job(
            session_id=session_id,
            file_path=tmp_path,
            filename=file.filename,
            content_type=content_type
        )

        session_data.pop("_id", None)
        return JSONResponse(status_code=202, content=session_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("", 
    response_model=PaginatedSessionList,
    summary="Listar historial de sesiones",
    description="Devuelve una lista paginada enriquecida de todas las sesiones realizadas ordenadas por fecha."
)
@limiter.limit("100/minute")
async def list_sessions(
    request: Request,
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["sub"]
    total = await session_repo.count_sessions_by_user(user_id)
    sessions = await session_repo.list_sessions_by_user(
        user_id=user_id,
        limit=limit, 
        offset=offset
    )
    return {
        "items": [SessionResponse(**s) for s in sessions],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{session_id}", 
    response_model=SessionResponse,
    summary="Obtener información de sesión",
    description="Recupera los metadatos y el resumen del estado actual de una sesión específica."
)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
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
        
    return SessionResponse(**session)

@router.get("/{session_id}/status",
    summary="Obtener el estado de procesamiento",
    description="Endpoint ligero diseñado específicamente para hacer polling desde el frontend mientras la sesión se procesa en background."
)
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
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
        
    return {
        "session_id": session.get("session_id"),
        "status": session.get("status", "unknown"),
        "progress_message": session.get("progress_message", ""),
        "quality_decision": session.get("quality_decision")
    }

@router.delete("/{session_id}",
    summary="Eliminar sesión y sus datos (GDPR)",
    description="Borra permanentemente la sesión, el documento original, metadatos, hallazgos y vectores asociados."
)
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )
    
    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(
            status_code=403,
            content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso para eliminar esta sesión"}
        )
        
    await session_repo.delete_session_data(session_id)
    
    import structlog
    structlog.get_logger(__name__).info("session_deleted", session_id=session_id, user_id=current_user["sub"])
    
    return JSONResponse(
        status_code=200,
        content={"message": "Sesión y datos asociados eliminados correctamente"}
    )

@router.get("/{session_id}/export",
    summary="Exportar resultados del análisis",
    description="Descarga los hallazgos (findings) de la sesión en un archivo estructurado CSV."
)
async def export_session_results(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión no existe"})
        
    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(status_code=403, content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso"})
        
    silver = await session_repo.get_silver(session_id)
    if not silver:
        return JSONResponse(status_code=400, content={"error_code": "NO_DATA", "message": "El análisis aún no ha terminado o no hay datos."})
        
    findings = silver.get("findings", [])
    
    # Generar CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir Headers
    writer.writerow(["ID", "Categoria", "Severidad", "Titulo", "Que encontramos", "Por que importa", "Recomendacion", "Columnas Afectadas"])
    
    # Escribir Filas
    for f in findings:
        writer.writerow([
            f.get("finding_id", ""),
            f.get("category", ""),
            f.get("severity", ""),
            f.get("title", ""),
            f.get("what", ""),
            f.get("so_what", ""),
            f.get("now_what", ""),
            ", ".join(f.get("affected_columns", []))
        ])
        
    output.seek(0)
    filename = session.get("source_metadata", {}).get("filename", "analisis").replace(" ", "_")
    safe_filename = f"data_x_export_{filename}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
    )

@router.post("/{session_id}/compare",
    summary="Comparar sesiones (Data Drift)",
    description="Compara el perfil estadístico y los hallazgos de la sesión actual contra una sesión base histórica."
)
async def compare_sessions(
    session_id: str,
    body: CompareRequest,
    current_user: dict = Depends(get_current_user)
):
    session_a = await session_repo.get_session(session_id)
    session_b = await session_repo.get_session(body.target_session_id)
    
    if not session_a or not session_b:
        return JSONResponse(status_code=404, content={"error_code": "SESSION_NOT_FOUND", "message": "Una o ambas sesiones no existen"})
        
    if session_a.get("user_id") != current_user["sub"] or session_b.get("user_id") != current_user["sub"]:
        return JSONResponse(status_code=403, content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso"})
        
    silver_a = await session_repo.get_silver(session_id) or {}
    silver_b = await session_repo.get_silver(body.target_session_id) or {}
    
    overview_a = silver_a.get("dataset_overview", {})
    overview_b = silver_b.get("dataset_overview", {})
    
    findings_a = {f["finding_id"]: f for f in silver_a.get("findings", [])}
    findings_b = {f["finding_id"]: f for f in silver_b.get("findings", [])}
    
    # Extraer diferencias clave (Nuevos riesgos vs riesgos resueltos)
    new_findings = [f for fid, f in findings_a.items() if fid not in findings_b]
    resolved_findings = [f for fid, f in findings_b.items() if fid not in findings_a]
    
    return {
        "session_current": session_id,
        "session_baseline": body.target_session_id,
        "overview_diff": {
            "row_count_change": overview_a.get("row_count", 0) - overview_b.get("row_count", 0),
            "null_percent_change": round(overview_a.get("total_null_percent", 0.0) - overview_b.get("total_null_percent", 0.0), 4),
        },
        "findings_diff": {
            "new_findings_count": len(new_findings),
            "resolved_findings_count": len(resolved_findings),
            "new_findings": new_findings,
            "resolved_findings": resolved_findings
        }
    }
