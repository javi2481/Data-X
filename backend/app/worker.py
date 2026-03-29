import structlog
import glob
import os
import tempfile
import time
from datetime import timedelta
from arq.connections import RedisSettings
from arq import Worker
from app.core.config import settings as _cfg
from app.repositories.mongo import session_repo
from app.db.client import db
from app.services.pipeline_orchestrator import PipelineOrchestrator

# Intentar cargar OpenTelemetry si está disponible (Fase 5 - Paso 3)
try:
    from opentelemetry.instrumentation.arq import ARQInstrumentor
    from opentelemetry import trace
    ARQInstrumentor().instrument()
    tracer = trace.get_tracer(__name__)
except ImportError:
    tracer = None
    pass

logger = structlog.get_logger(__name__)

async def cleanup_stale_temp_files(ctx):
    """
    ACT-006: Cron job que elimina archivos temporales con más de 1 hora de antigüedad.
    Previene acumulación de archivos en disco cuando el worker muere con SIGKILL
    antes de ejecutar el bloque finally del pipeline.
    """
    threshold = time.time() - 3600  # 1 hora
    removed = 0
    pattern = os.path.join(tempfile.gettempdir(), "tmp*")
    for f in glob.glob(pattern):
        try:
            if os.path.isfile(f) and os.path.getmtime(f) < threshold:
                os.unlink(f)
                removed += 1
        except OSError:
            pass
    if removed:
        logger.info("stale_temp_cleanup", removed=removed)

async def run_pipeline_task(ctx, session_id: str, file_path: str, filename: str, content_type: str):
    """
    Tarea principal de ARQ. Ejecuta el pipeline con soporte para reintentos (backoff).
    """
    attempt = ctx.get('job_try', 1)
    logger.info("arq_task_started", job_id=ctx.get('job_id'), session_id=session_id, attempt=attempt)
    
    try:
        # Actualizamos el estado para que el frontend sepa que ya no está "En Cola" sino "Procesando"
        await session_repo.update_session(session_id, {"status": "processing"})
        
        # Enriquecer la traza actual si OpenTelemetry está activo
        if tracer:
            current_span = trace.get_current_span()
            current_span.set_attribute("session_id", session_id)
            current_span.set_attribute("filename", filename)
            current_span.set_attribute("attempt", attempt)

        # Reutilizar el orquestador precargado en on_startup (BUG-008 fix)
        orchestrator = ctx["orchestrator"]
        await orchestrator.run_full_pipeline(session_id, file_path, filename, content_type)
        
        logger.info("arq_task_finished", job_id=ctx.get('job_id'), session_id=session_id)
    except Exception as e:
        logger.error("arq_task_failed", error=str(e), session_id=session_id)
        if tracer:
            # Inyectar error en el Trace para dashboards como Jaeger o Datadog
            current_span = trace.get_current_span()
            current_span.record_exception(e)
            current_span.set_status(trace.Status(trace.StatusCode.ERROR, description=str(e)))
        raise e  # Lanzar la excepción le indica a ARQ que debe reintentar el trabajo

class WorkerSettings:
    """Configuración inyectada automáticamente cuando se corre el worker de ARQ."""
    functions = [run_pipeline_task]
    # ACT-006: cron job de limpieza de temporales cada hora
    cron_jobs = [
        {"coroutine": cleanup_stale_temp_files, "hour": {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}}
    ]
    redis_settings = RedisSettings(host=_cfg.redis_host, port=_cfg.redis_port)
    max_tries = 3
    job_timeout = 600
    
    async def on_startup(ctx):
        logger.info("arq_worker_startup")
        await db.connect_to_db()
        # ── BUG-008 fix: instanciar el orquestador UNA sola vez al arrancar ──
        # PipelineOrchestrator carga SentenceTransformer (~500MB) y 11 servicios
        # más en su __init__. Instanciarlo en cada tarea suma +30-60s de latencia
        # y eleva el consumo de RAM de forma innecesaria.
        ctx["orchestrator"] = PipelineOrchestrator()
        logger.info("arq_orchestrator_ready")

    async def on_shutdown(ctx):
        logger.info("arq_worker_shutdown")
        await db.close_db_connection()