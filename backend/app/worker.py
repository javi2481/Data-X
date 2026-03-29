import structlog
from arq.connections import RedisSettings
from arq import Worker
from app.repositories.mongo import session_repo
from app.db.client import db
# Importar las dependencias reales del pipeline
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

        # Instanciar el orquestador y ejecutar
        orchestrator = PipelineOrchestrator() 
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
    redis_settings = RedisSettings(host='localhost', port=6379)
    max_tries = 3  # Si falla (ej: error temporal de Docling), reintenta hasta 3 veces con backoff exponencial
    job_timeout = 600  # 10 minutos máximo por documento para evitar colgar el worker
    
    async def on_startup(ctx):
        logger.info("arq_worker_startup")
        await db.connect_to_db()

    async def on_shutdown(ctx):
        logger.info("arq_worker_shutdown")
        await db.close_db_connection()