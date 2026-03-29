import structlog
from arq import create_pool
from arq.connections import RedisSettings
from typing import Optional

logger = structlog.get_logger(__name__)

class JobQueueService:
    """
    Servicio para interactuar con la cola de trabajos de ARQ (Redis).
    Permite encolar el procesamiento de documentos de forma asíncrona.
    """
    def __init__(self):
        from app.core.config import settings as _settings
        self.redis_settings = RedisSettings(
            host=_settings.redis_host,
            port=_settings.redis_port,
        )
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await create_pool(self.redis_settings)
            logger.info("job_queue_connected", host=self.redis_settings.host)

    async def enqueue_pipeline_job(self, session_id: str, file_path: str, filename: str, content_type: str) -> Optional[str]:
        """Encola un trabajo de procesamiento completo para una sesión."""
        if not self.pool:
            await self.connect()
        
        # Usamos el session_id como _job_id para evitar encolar el mismo trabajo dos veces
        job = await self.pool.enqueue_job(
            'run_pipeline_task',
            session_id,
            file_path,
            filename,
            content_type,
            _job_id=f"pipeline_{session_id}"
        )
        logger.info("job_enqueued", job_id=job.job_id if job else None, session_id=session_id)
        return job.job_id if job else None