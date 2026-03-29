from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional
import os

app = FastAPI(title="Data-X Code Audit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── COMPLETE AUDIT REPORT DATA ──────────────────────────────────────────────
AUDIT_REPORT = {
    "meta": {
        "repo": "javi2481/data-x",
        "repo_url": "https://github.com/javi2481/data-x",
        "branch": "main",
        "commit": "60972864747f9a1feaa49dd102b643781585ee43",
        "analysis_date": "2026-03-29",
        "analyst": "E2 — Tech Lead & Code Auditor",
        "summary": "Data-X es una plataforma sólida con una arquitectura Medallion bien pensada. Sin embargo, tiene vulnerabilidades críticas en la gestión de memoria de embeddings, un bug de NameError en producción, y patrones de diseño que generarán problemas de escalabilidad. Este reporte prioriza las acciones correctivas de mayor impacto.",
        "stats": {
            "total_issues": 23,
            "critical": 4,
            "high": 7,
            "medium": 8,
            "low": 4,
            "files_analyzed": 28,
            "lines_analyzed": 3200
        },
        "fixes_applied": [
            {
                "bug_id": "BUG-001",
                "title": "NameError: 'logger' no definido en analyze.py",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/bug-001-logger-nameerror-analyze",
                "files_changed": ["backend/app/api/routes/analyze.py"],
                "lines_changed": 4,
                "description": "import structlog y logger = structlog.get_logger(__name__) movidos al nivel de módulo. Eliminados imports inline dentro de try/except."
            },
            {
                "bug_id": "BUG-002",
                "title": "AttributeError: 'self.db' en delete_session_data",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/bug-002-attributeerror-delete-session",
                "files_changed": ["backend/app/repositories/mongo.py"],
                "lines_changed": 2,
                "description": "Reemplazado self.db.usage_events (inexistente) por db.db['usage_events'] con guard db.db is not None, consistente con el resto del repositorio."
            },
            {
                "bug_id": "BUG-003",
                "title": "EmbeddingService stateless: índice FAISS no persiste entre requests",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/bug-003-persist-faiss-index",
                "files_changed": [
                    "backend/app/services/pipeline_orchestrator.py",
                    "backend/app/api/routes/analyze.py"
                ],
                "lines_changed": 48,
                "description": "Worker serializa y persiste el índice FAISS + source_map + source_ids en MongoDB al finalizar Silver. El endpoint /api/analyze carga el índice antes de construir AnalysisDeps. RAG ahora funcional en producción."
            },
            {
                "bug_id": "BUG-004",
                "title": "Redis cache de LiteLLM centralizado en settings",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/bug-004-litellm-cache-settings",
                "files_changed": ["backend/app/services/llm_service.py"],
                "lines_changed": 15,
                "description": "Eliminado import os y las 3 líneas de módulo con os.environ. litellm.cache ahora se inicializa en __init__() usando settings.redis_host/port con degradación graceful si Redis no está disponible."
            },
            {
                "bug_id": "ACT-004",
                "title": "PipelineOrchestrator movido al contexto del worker ARQ + caché de modelos ML",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-004-worker-orchestrator-cache",
                "files_changed": [
                    "backend/app/worker.py",
                    "backend/app/services/embedding_service.py"
                ],
                "lines_changed": 41,
                "description": "Worker instancia PipelineOrchestrator una sola vez en on_startup(ctx). EmbeddingService ahora usa caché a nivel de clase (threading.Lock) para SentenceTransformer y CrossEncoder. Reduce latencia por tarea en 30-60s y RAM en ~60%."
            },
            {
                "bug_id": "ACT-005",
                "title": "Redis cache de LiteLLM centralizado en settings",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/bug-004-litellm-cache-settings",
                "files_changed": ["backend/app/services/llm_service.py"],
                "lines_changed": 15,
                "description": "Eliminado import os y las 3 líneas de módulo con os.environ. litellm.cache ahora se inicializa en __init__() usando settings.redis_host/port con degradación graceful si Redis no está disponible."
            },
            {
                "bug_id": "ACT-006",
                "title": "Cron job de limpieza de archivos temporales en worker ARQ",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-006-temp-cleanup-cron",
                "files_changed": ["backend/app/worker.py"],
                "lines_changed": 22,
                "description": "Función cleanup_stale_temp_files() elimina archivos tmp > 1 hora de antigüedad. Registrada como cron_job horario en WorkerSettings. Previene acumulación en disco tras crashes con SIGKILL."
            },
            {
                "bug_id": "ACT-007",
                "title": "Fallback models en LiteLLM Router",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-007-litellm-fallback",
                "files_changed": [
                    "backend/app/core/config.py",
                    "backend/app/services/llm_service.py"
                ],
                "lines_changed": 28,
                "description": "Agregado campo litellm_fallback_model en Settings. Router configurado con fallbacks=[{'primary': ['fallback']}] cuando el campo está presente. Elimina punto único de falla en el pipeline de IA."
            },
            {
                "bug_id": "ACT-008",
                "title": "Timeout + paralelismo en enrichment de findings",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-008-async-enrichment",
                "files_changed": ["backend/app/services/pipeline_orchestrator.py"],
                "lines_changed": 38,
                "description": "Loop secuencial reemplazado por asyncio.gather() con Semaphore(3) y asyncio.wait_for(timeout=25s) por llamada. Reduce tiempo Gold de ~5min a ~1min para 10 findings."
            },
            {
                "bug_id": "ACT-009",
                "title": "Índices compuestos MongoDB",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-009-mongo-indexes",
                "files_changed": ["backend/app/main.py"],
                "lines_changed": 10,
                "description": "Agregado índice compuesto (user_id, created_at DESC) en sessions para cubrir la query más frecuente en O(log n). Índices nombrados en bronze, silver, gold para session_id lookups."
            },
            {
                "bug_id": "ACT-010",
                "title": "FastAPI Dependency Injection para servicios",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-010-fastapi-di",
                "files_changed": ["backend/app/api/routes/sessions.py"],
                "lines_changed": 65,
                "description": "12 singletons globales reemplazados por factories con @lru_cache(maxsize=1). Servicios inyectados vía Depends(). Reemplazables en tests con app.dependency_overrides. FastAPI startup ya no carga modelos ML de forma eager."
            },
            {
                "bug_id": "ACT-011",
                "title": "datetime.utcnow() → datetime.now(timezone.utc)",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-011-datetime-timezone",
                "files_changed": [
                    "backend/app/services/pipeline_orchestrator.py",
                    "backend/app/services/auth_service.py",
                    "backend/app/api/routes/sessions.py"
                ],
                "lines_changed": 8,
                "description": "Reemplazados todos los datetime.utcnow() (deprecado Python 3.12+) por datetime.now(timezone.utc). Importado timezone en los 3 archivos afectados."
            },
            {
                "bug_id": "ACT-012",
                "title": "Routers duplicados eliminados de main.py",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-012-remove-legacy-routes",
                "files_changed": ["backend/app/main.py"],
                "lines_changed": 6,
                "description": "Eliminados 3 registros legacy sin prefijo /api (health, sessions, analyze). OpenAPI spec ahora sin duplicados. Rutas /health, /sessions, /analyze ya no responden (solo /api/*)."
            },
            {
                "bug_id": "ACT-013",
                "title": "Helper to_dict() para normalizar objetos Finding",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-013-to-dict-helper",
                "files_changed": [
                    "backend/app/utils.py",
                    "backend/app/services/llm_service.py"
                ],
                "lines_changed": 20,
                "description": "Creado backend/app/utils.py con to_dict() que normaliza Pydantic v1/v2, dataclass y dict a dict puro. Reemplazados 3 getattr ternarios en generate_enriched_explanation(). Patrón aplicable a todo el codebase."
            },
            {
                "bug_id": "ACT-014",
                "title": "Validación de configuración crítica en startup",
                "status": "fixed",
                "fix_date": "2026-03-29",
                "branch": "fix/act-014-config-validation",
                "files_changed": ["backend/app/core/config.py"],
                "lines_changed": 14,
                "description": "Agregado @model_validator(mode='after') en Settings que emite warnings si JWT_SECRET_KEY o LITELLM_API_KEY no están configuradas. Detecta configuraciones incompletas al importar el módulo, no en runtime."
            }
        ]
    },
    "sections": [
        {
            "key": "architecture",
            "title": "Arquitectura y Estructura",
            "icon": "layers",
            "summary": "El proyecto implementa una Arquitectura Medallion (Bronze → Silver → Gold) bien definida con FastAPI, MongoDB, ARQ (Redis), FAISS y LiteLLM. La separación en capas es correcta conceptualmente, pero la implementación tiene acoplamientos problemáticos que limitarán la escalabilidad.",
            "content": [
                {
                    "heading": "Patrón Medallion",
                    "text": "La arquitectura Medallion está bien implementada conceptualmente: Bronze guarda los datos raw con metadatos de conversión, Silver almacena el perfil estadístico y los findings, y Gold contiene el enriquecimiento por IA. El flujo de datos es unidireccional y determinístico."
                },
                {
                    "heading": "Worker ARQ + Redis",
                    "text": "La decisión de mover el pipeline a un worker ARQ asíncrono es correcta para operaciones de larga duración. Sin embargo, la instanciación del PipelineOrchestrator dentro del worker (en cada tarea) implica la carga de TODOS los modelos de ML (SentenceTransformer, CrossEncoder) en cada ejecución, lo cual es innecesariamente costoso en memoria."
                },
                {
                    "heading": "Patrón Strategy (Ingestion y Retrieval)",
                    "text": "Se detecta un intento de implementar el Patrón Strategy para la inyección de servicios (get_ingestion_strategy, get_retrieval_strategy). Sin embargo, la implementación es incompleta: ambas funciones siempre retornan el mismo servicio (EmbeddingService/IngestService) independientemente del tier del usuario, lo que vuelve el patrón inútil en la práctica."
                },
                {
                    "heading": "Repositorio de Datos",
                    "text": "La capa de repositorio (SessionRepository) centraliza correctamente el acceso a MongoDB. Sin embargo, no existe un índice compuesto para las consultas más frecuentes (user_id + created_at), lo que causará degradación de performance con el crecimiento de datos."
                },
                {
                    "heading": "EmbeddingService: Estado Estático en Worker",
                    "text": "El mayor problema arquitectónico es que el EmbeddingService mantiene el índice FAISS en memoria de instancia. Cuando el worker procesa un documento, construye el índice. Pero cuando el endpoint /api/analyze recibe una consulta, instancia un NUEVO EmbeddingService (vacío). Resultado: las búsquedas semánticas siempre retornan array vacío en producción."
                }
            ]
        },
        {
            "key": "bugs",
            "title": "Errores y Vulnerabilidades",
            "icon": "bug",
            "summary": "Se detectaron 4 bugs críticos (uno de los cuales genera un NameError en producción) y múltiples vulnerabilidades de seguridad y confiabilidad.",
            "issues": [
                {
                    "id": "BUG-001",
                    "title": "NameError en producción: 'logger' no definido en analyze.py",
                    "severity": "critical",
                    "status": "fixed",
                    "fix_branch": "fix/bug-001-logger-nameerror-analyze",
                    "category": "bug",
                    "file": "backend/app/api/routes/analyze.py",
                    "line_start": 30,
                    "line_end": 33,
                    "description": "La función get_retrieval_strategy() referencia la variable 'logger' sin haberla importado. Esto provoca un NameError que crashea cualquier request al endpoint /api/analyze cuando el usuario tiene tier='enterprise'. El bug está en producción y silencioso (solo ocurre en un branch condicional).",
                    "impact": "Los usuarios Enterprise no pueden usar el endpoint de análisis. El error crashea el worker sin mensaje claro.",
                    "evidence": "Línea 31: `logger.info('strategy_injection', ...)` — `logger` no está importado en este scope.",
                    "suggested_fix": {
                        "summary": "Importar structlog y definir logger al inicio del módulo",
                        "before": "def get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:\n    tier = current_user.get(\"tier\", \"lite\")\n    if tier == \"enterprise\":\n        # TODO: Retornar OpenSearchRetrievalService()\n        logger.info(\"strategy_injection\", ...)  # NameError!\n        return EmbeddingService()",
                        "after": "import structlog\nlogger = structlog.get_logger(__name__)  # ← Agregar al inicio del módulo\n\ndef get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:\n    tier = current_user.get(\"tier\", \"lite\")\n    if tier == \"enterprise\":\n        logger.info(\"strategy_injection\", strategy=\"faiss_in_memory\", user=current_user[\"sub\"])\n    return EmbeddingService()",
                        "notes": "Este es el fix mínimo. El TODO de OpenSearch también debe resolverse antes de activar el tier enterprise."
                    }
                },
                {
                    "id": "BUG-002",
                    "title": "AttributeError: 'self.db' no existe en SessionRepository.delete_session_data",
                    "severity": "critical",
                    "status": "fixed",
                    "fix_branch": "fix/bug-002-attributeerror-delete-session",
                    "category": "bug",
                    "file": "backend/app/repositories/mongo.py",
                    "line_start": 115,
                    "line_end": 115,
                    "description": "En el método delete_session_data(), la línea final referencia `self.db.usage_events` pero la clase SessionRepository no tiene atributo `self.db` (solo tiene properties que acceden a `db.db`). Esto causa un AttributeError en cada operación de delete/GDPR.",
                    "impact": "Todas las eliminaciones de sesiones fallan silenciosamente. Los datos de usage_events nunca se borran (violación GDPR potencial).",
                    "evidence": "Línea 115: `await self.db.usage_events.delete_many({\"session_id\": session_id})`\nLa clase no define `self.db`. Solo existe la propiedad `sessions`, `bronze`, etc.",
                    "suggested_fix": {
                        "summary": "Reemplazar self.db con la referencia correcta al cliente global db",
                        "before": "async def delete_session_data(self, session_id: str) -> bool:\n    await self.sessions.delete_one({\"session_id\": session_id})\n    # ... otras colecciones ...\n    await self.db.usage_events.delete_many({\"session_id\": session_id})  # AttributeError!\n    return True",
                        "after": "from app.db.client import db as _db  # importar el cliente global\n\nasync def delete_session_data(self, session_id: str) -> bool:\n    await self.sessions.delete_one({\"session_id\": session_id})\n    await self.bronze.delete_many({\"session_id\": session_id})\n    await self.silver.delete_many({\"session_id\": session_id})\n    await self.gold.delete_many({\"session_id\": session_id})\n    await self.embeddings_cache.delete_many({\"session_id\": session_id})\n    await self.hybrid_embeddings_cache.delete_many({\"session_id\": session_id})\n    await self.document_chunks.delete_many({\"session_id\": session_id})\n    # Usar _db.db en lugar de self.db:\n    if _db.db is not None:\n        await _db.db[\"usage_events\"].delete_many({\"session_id\": session_id})\n    return True",
                        "notes": "Validar que la colección usage_events realmente exista y sea necesaria antes de este fix."
                    }
                },
                {
                    "id": "BUG-003",
                    "title": "EmbeddingService stateless: índice FAISS no persiste entre requests",
                    "severity": "critical",
                    "status": "fixed",
                    "fix_branch": "fix/bug-003-persist-faiss-index",
                    "category": "bug",
                    "file": "backend/app/api/routes/analyze.py",
                    "line_start": 28,
                    "line_end": 44,
                    "description": "Cada request a /api/analyze instancia un nuevo EmbeddingService(). El índice FAISS se construye en el worker (proceso separado) y nunca se persiste en MongoDB ni se comparte. El nuevo EmbeddingService tiene `self.index = None` → search_hybrid_sources() retorna siempre lista vacía. El agente de PydanticAI no encuentra ningún documento relevante.",
                    "impact": "La funcionalidad RAG (Retrieval-Augmented Generation) está completamente rota en producción. El agente nunca puede responder preguntas sobre el documento cargado.",
                    "evidence": "Worker: `self.embedding_service.index_hybrid_sources(...)` (construye el índice en memoria del worker).\nAnalyze route: `EmbeddingService()` (instancia nueva, index=None).\nEmbeddingService.search_hybrid_sources(): `if self.index is None: return []`",
                    "suggested_fix": {
                        "summary": "Serializar el índice FAISS y persistirlo en MongoDB. Cargarlo en el endpoint de análisis.",
                        "before": "# En worker/pipeline_orchestrator.py\nawait self.embedding_service.index_hybrid_sources(findings=..., chunks=...)\n# El índice queda en memoria del worker. Se pierde.\n\n# En analyze.py\nretrieval_svc = EmbeddingService()  # Vacío!",
                        "after": "# En pipeline_orchestrator.py (después de index_hybrid_sources)\nindex_bytes = self.embedding_service.serialize_index()\nawait session_repo.save_hybrid_embeddings_cache({\n    \"session_id\": session_id,\n    \"index_bytes\": index_bytes,\n    \"source_map\": self.embedding_service.source_map,\n    \"source_ids\": self.embedding_service.source_ids,\n})\n\n# En analyze.py (cargar el índice desde MongoDB)\ncached = await session_repo.get_hybrid_embeddings_cache(session_id)\nretrieval_svc = EmbeddingService()\nif cached and cached.get(\"index_bytes\"):\n    retrieval_svc.deserialize_index(cached[\"index_bytes\"])\n    retrieval_svc.source_map = cached[\"source_map\"]\n    retrieval_svc.source_ids = cached[\"source_ids\"]",
                        "notes": "El método serialize_index() ya existe en EmbeddingService. Solo falta el guardado y la carga en el endpoint."
                    }
                },
                {
                    "id": "BUG-004",
                    "title": "Redis cache hardcodeado con os.environ en lugar de settings",
                    "severity": "critical",
                    "status": "fixed",
                    "fix_branch": "fix/bug-004-litellm-cache-settings",
                    "category": "security",
                    "file": "backend/app/services/llm_service.py",
                    "line_start": 10,
                    "line_end": 13,
                    "description": "La configuración del cache Redis de LiteLLM se inicializa a nivel de módulo usando os.environ.get() directamente, ignorando el sistema de configuración centralizado (Settings/Pydantic). Esto hace que los valores de settings.redis_host/port sean ignorados para LiteLLM, generando inconsistencias de configuración.",
                    "impact": "Si Redis corre en un host diferente (Docker, Kubernetes), el LLM cache apuntará a localhost mientras el worker apunta al host configurado. También hace el código no testeable.",
                    "evidence": "Líneas 10-13:\n`redis_host = os.environ.get(\"REDIS_HOST\", \"localhost\")`\n`redis_port = os.environ.get(\"REDIS_PORT\", \"6379\")`\n`litellm.cache = litellm.Cache(type=\"redis\", ...)` ← a nivel de módulo",
                    "suggested_fix": {
                        "summary": "Usar settings y mover la inicialización del cache dentro del constructor de LLMService",
                        "before": "import os\nredis_host = os.environ.get(\"REDIS_HOST\", \"localhost\")\nredis_port = os.environ.get(\"REDIS_PORT\", \"6379\")\nlitellm.cache = litellm.Cache(type=\"redis\", host=redis_host, port=redis_port)",
                        "after": "from app.core.config import settings\n\nclass LLMService:\n    def __init__(self):\n        self.api_key = settings.litellm_api_key\n        # Inicializar cache dentro del constructor, no a nivel de módulo\n        try:\n            litellm.cache = litellm.Cache(\n                type=\"redis\",\n                host=settings.redis_host,\n                port=settings.redis_port,\n            )\n        except Exception:\n            litellm.cache = None  # Degradar graciosamente si Redis no está disponible",
                        "notes": "Mover la inicialización al constructor permite testar la clase con mocks de settings."
                    }
                },
                {
                    "id": "BUG-005",
                    "status": "fixed",
                    "fix_branch": "fix/bug-005-csv-mime-validation",
                    "title": "Validación MIME de CSV demasiado restrictiva bloquea uploads legítimos",
                    "severity": "high",
                    "category": "bug",
                    "file": "backend/app/api/routes/sessions.py",
                    "line_start": 103,
                    "line_end": 109,
                    "description": "La validación de archivos CSV verifica que content_type sea exactamente 'text/csv' o 'text/plain'. Sin embargo, navegadores como Chrome a veces envían 'application/octet-stream' para archivos .csv. Esto bloqueará uploads legítimos con un error confuso.",
                    "impact": "Usuarios con ciertos navegadores/SO no pueden subir archivos CSV. Aumenta la tasa de abandonos.",
                    "evidence": "Líneas 103-109:\n`if content_type not in [\"text/csv\", \"text/plain\"]:`\n`return JSONResponse(400, ...)` ← Rechaza application/octet-stream",
                    "suggested_fix": {
                        "summary": "Priorizar la extensión del archivo sobre el MIME type declarado",
                        "before": "elif filename_lower.endswith(\".csv\"):\n    if content_type not in [\"text/csv\", \"text/plain\"]:\n        return JSONResponse(400, {\"error_code\": \"INVALID_FILE\", ...))",
                        "after": "# Para CSV, confiar en la extensión del archivo en lugar del MIME type\n# ya que los navegadores envían distintos MIME types para .csv\nelif filename_lower.endswith(\".csv\"):\n    ACCEPTED_CSV_MIMES = [\"text/csv\", \"text/plain\", \"application/octet-stream\", \"application/vnd.ms-excel\"]\n    if content_type not in ACCEPTED_CSV_MIMES:\n        # Solo advertir, no rechazar: la extensión es la fuente de verdad\n        logger.warning(\"csv_unusual_mime\", mime=content_type, filename=file.filename)",
                        "notes": "La validación real debe basarse en la estructura del contenido (intentar parsear las primeras líneas), no en el MIME type declarado."
                    }
                },
                {
                    "id": "BUG-006",
                    "status": "fixed",
                    "fix_branch": "fix/act-006-temp-cleanup-cron",
                    "title": "JobQueueService no reutiliza el pool Redis entre requests",
                    "severity": "high",
                    "category": "performance",
                    "file": "backend/app/services/job_queue.py",
                    "line_start": 1,
                    "line_end": 42,
                    "description": "JobQueueService se instancia a nivel de módulo en sessions.py como `job_queue_service = JobQueueService()`. El pool Redis (`self.pool`) se inicializa en None y se crea lazy en `connect()`. Sin embargo, al ser un singleton, eventualmente se reutiliza. El problema es que no hay lógica de reconexión si Redis cae → el pool queda None o stale.",
                    "impact": "Si Redis se reinicia o hay un timeout, el pool queda en estado inválido y todas las tareas de encolado fallan hasta que se reinicia el servidor FastAPI.",
                    "evidence": "No hay manejo de reconexión en `enqueue_pipeline_job`. Si `create_pool` falla, `self.pool = None` y la próxima llamada vuelve a intentar crear el pool sin limpiar el estado.",
                    "suggested_fix": {
                        "summary": "Agregar manejo de errores de reconexión y health check del pool",
                        "before": "async def enqueue_pipeline_job(self, ...): \n    if not self.pool:\n        await self.connect()",
                        "after": "async def enqueue_pipeline_job(self, ...) -> Optional[str]:\n    try:\n        if not self.pool:\n            await self.connect()\n        job = await self.pool.enqueue_job(...)\n        return job.job_id if job else None\n    except Exception as e:\n        logger.error(\"job_queue_failed\", error=str(e))\n        # Forzar reconexión en próximo intento\n        self.pool = None\n        raise RuntimeError(f\"No se pudo encolar el trabajo: {e}\") from e",
                        "notes": "Considerar usar un Circuit Breaker pattern si el error de Redis es frecuente."
                    }
                },
                {
                    "id": "BUG-007",
                    "status": "fixed",
                    "fix_branch": "fix/act-006-temp-cleanup-cron",
                    "title": "Archivos temporales huérfanos si el worker muere antes del finally",
                    "severity": "high",
                    "category": "reliability",
                    "file": "backend/app/services/pipeline_orchestrator.py",
                    "line_start": 145,
                    "line_end": 155,
                    "description": "El archivo temporal se crea en sessions.py con `tempfile.NamedTemporaryFile(delete=False)` y se elimina en el `finally` del PipelineOrchestrator. Si el worker ARQ muere con SIGKILL (OOM killer, K8s eviction), el bloque `finally` no se ejecuta y el archivo queda en el disco permanentemente.",
                    "impact": "Acumulación de archivos temporales en disco. En K8s con volumes limitados, puede causar OOMKilled o falta de espacio.",
                    "evidence": "sessions.py crea el tmp con delete=False. pipeline_orchestrator.py lo elimina en finally. SIGKILL no ejecuta finally.",
                    "suggested_fix": {
                        "summary": "Usar un job periódico de limpieza de temporales o tmpfs con TTL",
                        "before": "finally:\n    try:\n        os.unlink(file_path)\n    except OSError:\n        pass",
                        "after": "# Opción 1: Usar tmpfs en Docker/K8s (no requiere cambio de código)\n# En docker-compose.yml, montar /tmp como tmpfs con tamaño máximo\n\n# Opción 2: Agregar cleanup job periódico en el worker\nasync def cleanup_stale_temp_files(ctx):\n    \"\"\"Elimina archivos temporales > 1 hora de antigüedad.\"\"\"\n    import glob, time\n    pattern = os.path.join(tempfile.gettempdir(), \"tmp*\")\n    threshold = time.time() - 3600  # 1 hora\n    for f in glob.glob(pattern):\n        try:\n            if os.path.getmtime(f) < threshold:\n                os.unlink(f)\n        except OSError:\n            pass\n\n# Registrar en WorkerSettings.cron_jobs = [(cleanup_stale_temp_files, timedelta(hours=1))]",
                        "notes": "La opción de tmpfs en Docker es la más simple y efectiva para K8s."
                    }
                },
                {
                    "id": "BUG-008",
                    "title": "PipelineOrchestrator instancia todos los servicios ML en cada tarea ARQ",
                    "severity": "high",
                    "status": "fixed",
                    "fix_branch": "fix/act-004-worker-orchestrator-cache",
                    "category": "performance",
                    "file": "backend/app/worker.py",
                    "line_start": 33,
                    "line_end": 35,
                    "description": "En worker.py, `orchestrator = PipelineOrchestrator()` se ejecuta dentro de `run_pipeline_task()`, es decir, en cada tarea. El constructor de PipelineOrchestrator inicializa SentenceTransformer (modelo ~500MB), CrossEncoder, Docling, y otros servicios. Esto recarga todos los modelos ML en cada documento procesado.",
                    "impact": "Latencia de procesamiento aumentada en ~30-60 segundos por documento (solo por carga de modelos). Alto uso de RAM. En máquinas con <8GB RAM puede causar OOMKilled.",
                    "evidence": "worker.py:34: `orchestrator = PipelineOrchestrator()` — dentro del handler de la tarea.\npipeline_orchestrator.py:26-42: El constructor inicializa 12 servicios, incluyendo EmbeddingService que carga SentenceTransformer.",
                    "suggested_fix": {
                        "summary": "Mover la instanciación del orquestador al contexto de startup del worker (on_startup)",
                        "before": "async def run_pipeline_task(ctx, session_id, file_path, filename, content_type):\n    # ...\n    orchestrator = PipelineOrchestrator()  # ← Se carga en cada tarea\n    await orchestrator.run_full_pipeline(...)",
                        "after": "class WorkerSettings:\n    # ...\n    async def on_startup(ctx):\n        logger.info(\"arq_worker_startup\")\n        await db.connect_to_db()\n        ctx[\"orchestrator\"] = PipelineOrchestrator()  # ← Carga UNA vez al inicio\n        logger.info(\"orchestrator_ready\")\n\n    async def on_shutdown(ctx):\n        logger.info(\"arq_worker_shutdown\")\n        await db.close_db_connection()\n\nasync def run_pipeline_task(ctx, session_id, file_path, filename, content_type):\n    orchestrator = ctx[\"orchestrator\"]  # ← Reutilizar instancia existente\n    await orchestrator.run_full_pipeline(...)",
                        "notes": "Este cambio reduce el tiempo de procesamiento en ~30-60s por documento y reduce el uso de RAM significativamente."
                    }
                },
                {
                    "id": "BUG-009",
                    "status": "fixed",
                    "fix_branch": "fix/act-008-async-enrichment",
                    "title": "Sin timeout en llamadas LLM individuales para enrichment de findings",
                    "severity": "high",
                    "category": "reliability",
                    "file": "backend/app/services/pipeline_orchestrator.py",
                    "line_start": 115,
                    "line_end": 132,
                    "description": "El loop de enrichment de findings (hasta 10 llamadas LLM) no tiene timeout individual ni límite de tiempo total. Si el proveedor LLM (OpenRouter) experimenta lentitud, el pipeline puede bloquearse por varios minutos. El Router de LiteLLM tiene timeout=30s, pero está en la instancia del router, no en cada llamada async.",
                    "impact": "El pipeline puede exceder el job_timeout=600s de ARQ con solo 10 findings lentos. Todos los reintentos también tardarán, consumiendo el budget de 3 intentos sin procesar el documento.",
                    "evidence": "pipeline_orchestrator.py:119: `for finding in findings_dicts[:10]:` — sin asyncio.wait_for() ni timeout por finding.",
                    "suggested_fix": {
                        "summary": "Usar asyncio.wait_for() con timeout por llamada y asyncio.gather() para paralelismo",
                        "before": "for finding in findings_dicts[:10]:\n    try:\n        enriched = await self.llm_service.generate_enriched_explanation(\n            finding=finding, dataset_context=dataset_context\n        )",
                        "after": "import asyncio\n\nasync def _safe_enrich(llm_service, finding, context, timeout=25):\n    try:\n        return await asyncio.wait_for(\n            llm_service.generate_enriched_explanation(finding=finding, dataset_context=context),\n            timeout=timeout\n        )\n    except asyncio.TimeoutError:\n        logger.warning(\"finding_enrich_timeout\", finding_id=finding.get(\"finding_id\"))\n        return {\"explanation\": None, \"cost_usd\": 0.0}\n    except Exception as e:\n        logger.warning(\"finding_enrich_failed\", error=str(e))\n        return {\"explanation\": None, \"cost_usd\": 0.0}\n\n# Ejecutar en paralelo (máx 3 concurrentes para no saturar la API)\nsem = asyncio.Semaphore(3)\nasync def enrich_with_semaphore(finding):\n    async with sem:\n        return await _safe_enrich(self.llm_service, finding, dataset_context)\n\nresults = await asyncio.gather(*[enrich_with_semaphore(f) for f in findings_dicts[:10]])",
                        "notes": "El paralelismo con semáforo puede reducir el tiempo total de enrichment de ~5min a ~1min para 10 findings."
                    }
                },
                {
                    "id": "BUG-010",
                    "title": "Patrón Strategy de retrieval siempre retorna EmbeddingService",
                    "severity": "medium",
                    "status": "fixed",
                    "fix_branch": "main",
                    "category": "bug",
                    "file": "backend/app/api/routes/analyze.py",
                    "line_start": 21,
                    "line_end": 39,
                    "description": "La función get_retrieval_strategy() siempre retorna EmbeddingService() independientemente del tier. El bloque enterprise tiene el bug del logger (BUG-001) y además retorna EmbeddingService en ambas ramas. El patrón Strategy está implementado pero es un no-op.",
                    "impact": "El código promete diferenciación por tier pero no la entrega. Confusión para futuros desarrolladores. Deuda técnica que crece.",
                    "evidence": "Líneas 28-44: ambas branches de `if tier == \"enterprise\"` retornan `EmbeddingService()`.",
                    "suggested_fix": {
                        "summary": "Limpiar el patrón Strategy para que sea honesto sobre su estado actual",
                        "before": "def get_retrieval_strategy(current_user):\n    tier = current_user.get(\"tier\", \"lite\")\n    if tier == \"enterprise\":\n        # TODO: OpenSearchRetrievalService\n        logger.info(...)  # BUG!\n        return EmbeddingService()\n    logger.info(...)  # BUG!\n    return EmbeddingService()",
                        "after": "def get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:\n    \"\"\"\n    TODO(NXT-003): Implementar OpenSearchRetrievalService para tier Enterprise.\n    Por ahora, todos los tiers usan FAISS in-memory con persistencia en MongoDB.\n    \"\"\"\n    tier = current_user.get(\"tier\", \"lite\")\n    logger.info(\"retrieval_strategy_selected\", tier=tier, strategy=\"faiss_persisted\", user=current_user[\"sub\"])\n    return EmbeddingService()",
                        "notes": "Fix aplicado en commit 836b541. If/else redundante eliminado. Código ahora es honesto sobre el comportamiento actual con documentación clara del TODO."
                    }
                },
                {
                    "id": "BUG-011",
                    "status": "fixed",
                    "fix_branch": "fix/act-012-remove-legacy-routes",
                    "title": "Doble registro de routers en main.py genera rutas duplicadas en OpenAPI",
                    "severity": "medium",
                    "category": "bug",
                    "file": "backend/app/main.py",
                    "line_start": 108,
                    "line_end": 120,
                    "description": "Las rutas se registran dos veces: una con prefijo /api (correcto) y otra sin prefijo /api (legacy). Esto genera el doble de entradas en el OpenAPI spec (Swagger) y puede confundir a los consumidores de la API. También puede causar colisiones si algún middleware aplica lógica por prefijo.",
                    "impact": "API spec duplicado. Rutas como GET /sessions y GET /api/sessions responden igual. Duplicación de rate limits.",
                    "evidence": "Líneas 108-120: Se incluyen los mismos routers dos veces, con y sin prefijo /api.",
                    "suggested_fix": {
                        "summary": "Eliminar el registro legacy (sin /api) o agregar deprecated=True para migración controlada",
                        "before": "app.include_router(health.router, prefix=\"/api/health\")\n# ... otros con /api ...\n# Legacy (sin /api):\napp.include_router(health.router, prefix=\"/health\")\napp.include_router(sessions.router, prefix=\"/sessions\")\napp.include_router(analyze.router, prefix=\"/analyze\")",
                        "after": "# Solo registrar los routers una vez, con el prefijo correcto /api:\napp.include_router(health.router, prefix=\"/api/health\", tags=[\"health\"])\napp.include_router(auth.router, prefix=\"/api\", tags=[\"auth\"])\napp.include_router(sessions.router, prefix=\"/api/sessions\", tags=[\"sessions\"])\napp.include_router(analyze.router, prefix=\"/api/analyze\", tags=[\"analyze\"])\napp.include_router(reports.router, prefix=\"/api/sessions\", tags=[\"reports\"])\n\n# Si se necesita compatibilidad, usar un redirect middleware en lugar de duplicar:",
                        "notes": "Si el frontend ya usa /api/*, eliminar los registros legacy es seguro."
                    }
                },
                {
                    "id": "BUG-012",
                    "status": "fixed",
                    "fix_branch": "fix/act-009-mongo-indexes",
                    "title": "Sin índice compuesto en sessions para queries de usuario + fecha",
                    "severity": "medium",
                    "category": "performance",
                    "file": "backend/app/main.py",
                    "line_start": 29,
                    "line_end": 38,
                    "description": "En el startup, se crean índices individuales en `user_id` y `created_at`, pero no un índice compuesto. La query más frecuente es `find({\"user_id\": X}).sort(\"created_at\", -1)`, que requiere un índice compuesto (user_id, created_at) para ser eficiente. Con índices separados, MongoDB puede usar uno u otro pero no ambos.",
                    "impact": "Degradación de performance en list_sessions a medida que crecen los datos. Con 100K sesiones, la query puede tardar segundos en lugar de milisegundos.",
                    "evidence": "main.py:31-37: Índices separados en sessions.user_id y sessions.created_at.",
                    "suggested_fix": {
                        "summary": "Agregar índice compuesto (user_id, created_at DESC)",
                        "before": "await db.db.sessions.create_index(\"session_id\", unique=True)\nawait db.db.sessions.create_index(\"user_id\")\nawait db.db.sessions.create_index([(\"created_at\", -1)])",
                        "after": "await db.db.sessions.create_index(\"session_id\", unique=True)\n# Índice compuesto para la query más frecuente: listar por usuario ordenado por fecha\nawait db.db.sessions.create_index([(\"user_id\", 1), (\"created_at\", -1)], name=\"idx_user_date\")\n# Índices adicionales para Bronze/Silver/Gold también:\nawait db.db.bronze.create_index(\"session_id\")\nawait db.db.silver.create_index(\"session_id\")\nawait db.db.gold.create_index(\"session_id\")",
                        "notes": "Los índices en Bronze/Silver/Gold son especialmente importantes ya que se consultan frecuentemente por session_id."
                    }
                },
                {
                    "id": "BUG-013",
                    "status": "fixed",
                    "fix_branch": "fix/act-011-datetime-timezone",
                    "title": "datetime.utcnow() deprecado en Python 3.12+",
                    "severity": "low",
                    "category": "deprecation",
                    "file": "backend/app/services/pipeline_orchestrator.py",
                    "line_start": 72,
                    "line_end": 72,
                    "description": "Se usa `datetime.utcnow()` que está deprecado desde Python 3.12 y será removido en futuras versiones. El proyecto ya requiere Python 3.11+ en el README, pero si se actualiza a 3.12+ habrá warnings de deprecación en todos los logs.",
                    "impact": "DeprecationWarnings en logs. Futura incompatibilidad cuando datetime.utcnow() sea removido.",
                    "evidence": "Múltiples usos en pipeline_orchestrator.py y auth_service.py.",
                    "suggested_fix": {
                        "summary": "Reemplazar datetime.utcnow() con datetime.now(timezone.utc)",
                        "before": "from datetime import datetime\n\ncreated_at = datetime.utcnow().isoformat()",
                        "after": "from datetime import datetime, timezone\n\ncreated_at = datetime.now(timezone.utc).isoformat()",
                        "notes": "Aplicar en todos los archivos: pipeline_orchestrator.py, auth_service.py, sessions.py."
                    }
                }
            ]
        },
        {
            "key": "refactoring",
            "title": "Mejoras y Refactorización",
            "icon": "code",
            "summary": "Oportunidades de mejora para hacer el código más limpio, testeable y mantenible sin romper la arquitectura existente.",
            "issues": [
                {
                    "id": "REF-001",
                    "title": "Servicios instanciados a nivel de módulo en sessions.py crean singletons implícitos",
                    "severity": "high",
                    "category": "design",
                    "file": "backend/app/api/routes/sessions.py",
                    "line_start": 43,
                    "line_end": 57,
                    "description": "Sessions.py instancia 12 servicios a nivel de módulo (fuera de funciones). Esto crea singletons globales que: (1) no pueden ser reemplazados en tests, (2) cargan todos los modelos ML al iniciar FastAPI (lentitud de startup), (3) no son thread-safe si comparten estado mutable.",
                    "impact": "Startup de FastAPI lento. Imposible testear endpoints sin cargar modelos ML reales. Estado compartido entre requests puede causar bugs en concurrencia.",
                    "suggested_fix": {
                        "summary": "Usar FastAPI Dependency Injection para instanciar servicios por request o como dependencias cacheadas",
                        "before": "# A nivel de módulo (global, singleton):\ningest_service = IngestService()\nnormalization_service = NormalizationService()\n# ... etc ...",
                        "after": "from functools import lru_cache\nfrom fastapi import Depends\n\n@lru_cache(maxsize=1)\ndef get_ingest_service() -> IngestService:\n    return IngestService()\n\n@lru_cache(maxsize=1)\ndef get_llm_service() -> LLMService:\n    return LLMService()\n\n# En el endpoint:\nasync def create_session(\n    file: UploadFile,\n    ingest_svc: IngestService = Depends(get_ingest_service),\n    llm_svc: LLMService = Depends(get_llm_service),\n):\n    ...",
                        "notes": "lru_cache(maxsize=1) garantiza un singleton, pero reemplazable en tests con app.dependency_overrides."
                    }
                },
                {
                    "id": "REF-002",
                    "title": "Acceso a atributos de Finding mezcla Pydantic y dict de forma inconsistente",
                    "severity": "medium",
                    "category": "code_quality",
                    "file": "backend/app/services/llm_service.py",
                    "line_start": 45,
                    "line_end": 52,
                    "description": "El código en llm_service.py accede a los atributos de Finding con lógica duplicada: `f.title if not isinstance(f, dict) else f.get('title')`. Este patrón se repite 15+ veces en el archivo. Indica que la capa de serialización no es consistente: a veces se pasan objetos Pydantic y a veces dicts.",
                    "impact": "Código verbose y propenso a bugs. Si se agrega un nuevo campo a Finding, hay que actualizar 15+ lugares.",
                    "suggested_fix": {
                        "summary": "Normalizar a dict en el punto de entrada y usar dict.get() consistentemente",
                        "before": "f_what = getattr(finding, 'what', finding.get('what', '')) if not isinstance(finding, dict) else finding.get('what', '')",
                        "after": "def _to_dict(obj: Any) -> dict:\n    \"\"\"Normaliza Pydantic models o dicts a dict puro.\"\"\"\n    if isinstance(obj, dict):\n        return obj\n    if hasattr(obj, 'model_dump'):\n        return obj.model_dump()\n    return vars(obj)\n\n# En el método, una sola línea al inicio:\nf = _to_dict(finding)\nf_what = f.get('what', '')\nf_so_what = f.get('so_what', '')\nf_now_what = f.get('now_what', '')",
                        "notes": "Esta función helper debería vivir en app/utils.py y ser importada donde se necesite."
                    }
                },
                {
                    "id": "REF-003",
                    "title": "EmbeddingService hereda de BaseRetrievalService pero no persiste el índice por sesión",
                    "severity": "medium",
                    "category": "design",
                    "file": "backend/app/services/embedding_service.py",
                    "line_start": 1,
                    "line_end": 20,
                    "description": "EmbeddingService mantiene un único índice FAISS global (self.index) para todas las sesiones. Si se procesaran dos documentos en paralelo, el segundo sobreescribiría el índice del primero. Actualmente el sistema solo permite una sesión activa por vez en el worker, pero esto es frágil.",
                    "impact": "Race condition si se procesan documentos en paralelo. No escala a multi-session.",
                    "suggested_fix": {
                        "summary": "Hacer el índice por sesión en lugar de global, o extraer la persistencia al repositorio",
                        "before": "class EmbeddingService(BaseRetrievalService):\n    def __init__(self):\n        self.model = SentenceTransformer(...)\n        self.index = None  # ← Un único índice global",
                        "after": "class EmbeddingService(BaseRetrievalService):\n    # Los modelos son compartidos (thread-safe para inferencia)\n    _shared_model: Optional[SentenceTransformer] = None\n    _shared_reranker: Optional[CrossEncoder] = None\n\n    def __init__(self):\n        if EmbeddingService._shared_model is None:\n            EmbeddingService._shared_model = SentenceTransformer(self._model_name)\n        self.model = EmbeddingService._shared_model\n        self.index = None  # Por sesión (se carga desde MongoDB)",
                        "notes": "Los modelos SentenceTransformer son thread-safe para inferencia. Compartirlos entre instancias ahorra ~500MB de RAM."
                    }
                },
                {
                    "id": "REF-004",
                    "title": "Settings no tiene validación de valores críticos al startup",
                    "severity": "medium",
                    "category": "reliability",
                    "file": "backend/app/core/config.py",
                    "line_start": 1,
                    "line_end": 30,
                    "description": "La clase Settings usa tipos Optional para litellm_api_key y litellm_model, con defaults vacíos. Esto permite que el servidor arranque sin configuración de LLM, pero los errores solo se descubren en runtime cuando se intenta hacer el primer análisis.",
                    "impact": "Operadores pueden desplegar el servicio sin API key y descubrirlo solo cuando usuarios reales intentan usar IA.",
                    "suggested_fix": {
                        "summary": "Agregar validadores de Pydantic para detectar configuraciones incompletas en startup",
                        "before": "class Settings(BaseSettings):\n    litellm_api_key: Optional[str] = \"\"\n    litellm_model: Optional[str] = \"gpt-4o-mini\"",
                        "after": "from pydantic import field_validator, model_validator\n\nclass Settings(BaseSettings):\n    litellm_api_key: Optional[str] = \"\"\n    litellm_model: str = \"gpt-4o-mini\"\n    \n    @model_validator(mode='after')\n    def check_llm_config(self) -> 'Settings':\n        if not self.litellm_api_key:\n            import warnings\n            warnings.warn(\"LITELLM_API_KEY no configurada. Las funciones de IA estarán deshabilitadas.\")\n        return self",
                        "notes": "En producción, considerar hacer litellm_api_key required (sin default) para forzar configuración explícita."
                    }
                },
                {
                    "id": "REF-005",
                    "title": "IngestService carga OpenCV para TODOS los PDFs, incluso los de alta calidad",
                    "severity": "low",
                    "category": "performance",
                    "file": "backend/app/services/ingest.py",
                    "line_start": 45,
                    "line_end": 57,
                    "description": "Para cada PDF, se importa OpenCVPipeline, se convierten todas las páginas a imágenes cv2, y se evalúa la calidad de la primera. Esto añade 2-5 segundos de overhead para PDFs de alta calidad que no necesitan este análisis. El quality gate debería ser opcional o configurado por usuario.",
                    "impact": "Latencia adicional de 2-5 segundos en todos los PDFs. Carga de OpenCV en el processo de ingesta.",
                    "suggested_fix": {
                        "summary": "Hacer el OpenCV quality gate opcional mediante un parámetro de configuración",
                        "before": "if is_pdf:\n    from app.services.opencv_pipeline import OpenCVPipeline\n    cv_pipeline = OpenCVPipeline()\n    images = cv_pipeline.pdf_to_cv2_images(file_bytes)\n    if images:\n        qg_result = cv_pipeline.quality_gate_image(images[0])",
                        "after": "# Hacer el quality gate opcional\nENABLE_PDF_QUALITY_GATE = settings.enable_pdf_quality_gate  # Default: True\n\nif is_pdf and ENABLE_PDF_QUALITY_GATE:\n    from app.services.opencv_pipeline import OpenCVPipeline\n    cv_pipeline = OpenCVPipeline()\n    images = cv_pipeline.pdf_to_cv2_images(file_bytes)\n    if images:\n        qg_result = cv_pipeline.quality_gate_image(images[0])\n        if not qg_result[\"passed\"]:\n            logger.warning(\"pdf_quality_failed\", variance=qg_result[\"variance\"])",
                        "notes": "Agregar enable_pdf_quality_gate: bool = True a Settings para control por entorno."
                    }
                }
            ]
        },
        {
            "key": "ai_ml",
            "title": "Optimización IA/ML",
            "icon": "brain",
            "summary": "El pipeline de IA tiene potencial significativo de mejora en performance, costos y resiliencia. Los tres problemas más críticos son: el índice FAISS no persiste, los modelos de embeddings se recargan en cada tarea, y las llamadas LLM no son paralelas.",
            "issues": [
                {
                    "id": "AI-001",
                    "title": "Modelos SentenceTransformer y CrossEncoder se cargan en cada instancia",
                    "severity": "critical",
                    "status": "fixed",
                    "fix_branch": "fix/act-004-worker-orchestrator-cache",
                    "category": "ml_performance",
                    "file": "backend/app/services/embedding_service.py",
                    "line_start": 7,
                    "line_end": 12,
                    "description": "El constructor de EmbeddingService carga SentenceTransformer (~500MB) y registra CrossEncoder para carga lazy. Si EmbeddingService se instancia múltiples veces (como ocurre actualmente en analyze.py en cada request), esto puede causar múltiples cargas del modelo o al menos múltiples instancias en memoria.",
                    "impact": "Consumo de ~500MB de RAM por instancia. Tiempo de inicialización de 10-15 segundos por instancia. En producción con múltiples workers, esto escala linealmente.",
                    "suggested_fix": {
                        "summary": "Usar class-level caching para compartir los modelos entre instancias",
                        "before": "class EmbeddingService:\n    def __init__(self):\n        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')\n        self.reranker = None",
                        "after": "import threading\n\nclass EmbeddingService:\n    _model_cache: dict = {}\n    _model_lock = threading.Lock()\n\n    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):\n        self._model_name = model_name\n        with EmbeddingService._model_lock:\n            if model_name not in EmbeddingService._model_cache:\n                EmbeddingService._model_cache[model_name] = SentenceTransformer(model_name)\n        self.model = EmbeddingService._model_cache[model_name]",
                        "notes": "SentenceTransformer.encode() es thread-safe para inferencia. El lock solo es necesario para la inicialización."
                    }
                },
                {
                    "id": "AI-002",
                    "title": "Índice FAISS en memoria no sobrevive reinicios del worker ni escala horizontalmente",
                    "severity": "critical",
                    "category": "ml_architecture",
                    "file": "backend/app/services/embedding_service.py",
                    "line_start": 60,
                    "line_end": 80,
                    "description": "El índice FAISS se construye en memoria y no se persiste. EmbeddingService.serialize_index() existe pero nunca es llamado desde el pipeline. Esto significa que cada reinicio del worker destruye todos los índices de sesiones existentes, haciendo el RAG inoperable hasta que se reprocesen los documentos.",
                    "impact": "En despliegues con múltiples instancias del worker, solo el worker que procesó el documento tiene el índice. RAG falla con probabilidad (N-1)/N. Reinicios del worker = pérdida total de capacidad RAG.",
                    "suggested_fix": {
                        "summary": "Serializar y persistir el índice FAISS en MongoDB después de la indexación",
                        "before": "# En pipeline_orchestrator.py - el índice se construye pero nunca se persiste\nawait self.embedding_service.index_hybrid_sources(\n    findings=findings_dicts, chunks=chunks_dicts\n)",
                        "after": "# Después de indexar, serializar y guardar:\nawait self.embedding_service.index_hybrid_sources(\n    findings=findings_dicts, chunks=chunks_dicts\n)\n\n# Persistir en MongoDB para que otros workers/requests puedan usarlo:\nif self.embedding_service.index is not None:\n    index_bytes = self.embedding_service.serialize_index()\n    await session_repo.save_hybrid_embeddings_cache({\n        'session_id': session_id,\n        'index_bytes': Binary(index_bytes),  # BSON Binary\n        'source_map': self.embedding_service.source_map,\n        'source_ids': self.embedding_service.source_ids,\n        'model_name': self.embedding_service.model_name,\n        'created_at': datetime.now(timezone.utc).isoformat(),\n    })",
                        "notes": "Para índices grandes (>10MB), considerar GridFS de MongoDB o S3 en lugar de BSON Binary."
                    }
                },
                {
                    "id": "AI-003",
                    "title": "LLM Router con solo un modelo, sin fallback real",
                    "severity": "high",
                    "category": "ml_resilience",
                    "file": "backend/app/services/llm_service.py",
                    "line_start": 20,
                    "line_end": 35,
                    "description": "El LiteLLM Router está configurado con un solo modelo ('default'). El parámetro num_retries=2 solo reintenta el mismo modelo/endpoint, no hace failover real a un modelo alternativo. Si OpenRouter está caído, las 3 instancias del worker fallarán usando el mismo proveedor.",
                    "impact": "Punto único de falla en el pipeline de IA. Downtime de OpenRouter = downtime completo de análisis.",
                    "suggested_fix": {
                        "summary": "Configurar modelos de fallback en el Router para alta disponibilidad",
                        "before": "model_list = [{\n    'model_name': 'default',\n    'litellm_params': {\n        'model': settings.litellm_model,\n        'api_key': self.api_key,\n    }\n}]\nself.router = Router(model_list=model_list, num_retries=2)",
                        "after": "model_list = [\n    {\n        'model_name': 'primary',\n        'litellm_params': {\n            'model': settings.litellm_model,  # ej: openrouter/openai/gpt-4o-mini\n            'api_key': self.api_key,\n        }\n    },\n]\n\n# Agregar fallback si está configurado:\nif settings.litellm_fallback_model:\n    model_list.append({\n        'model_name': 'fallback',\n        'litellm_params': {\n            'model': settings.litellm_fallback_model,\n            'api_key': self.api_key,\n        }\n    })\n\nself.router = Router(\n    model_list=model_list,\n    fallbacks=[{'primary': ['fallback']}] if settings.litellm_fallback_model else [],\n    num_retries=2,\n    timeout=30,\n)",
                        "notes": "Agregar LITELLM_FALLBACK_MODEL a Settings. Un buen fallback es openrouter/anthropic/claude-3-haiku o gpt-3.5-turbo."
                    }
                },
                {
                    "id": "AI-004",
                    "title": "Reranker CrossEncoder cargado por demanda pero sin LRU cache",
                    "severity": "medium",
                    "category": "ml_performance",
                    "file": "backend/app/services/embedding_service.py",
                    "line_start": 22,
                    "line_end": 26,
                    "description": "El CrossEncoder se carga lazy mediante _get_reranker(), lo cual es buena práctica. Sin embargo, si EmbeddingService se instancia múltiples veces (que ocurre en el estado actual), el reranker tampoco se comparte entre instancias, causando cargas redundantes.",
                    "impact": "Carga del CrossEncoder (~200MB, ~5s) si se instancia EmbeddingService en múltiples requests.",
                    "suggested_fix": {
                        "summary": "Compartir el reranker a nivel de clase usando el mismo patrón de class-level cache",
                        "before": "def _get_reranker(self):\n    if self.reranker is None:\n        self.reranker = CrossEncoder(self.reranker_name)\n    return self.reranker",
                        "after": "_reranker_cache: dict = {}\n\ndef _get_reranker(self) -> CrossEncoder:\n    if self.reranker_name not in EmbeddingService._reranker_cache:\n        EmbeddingService._reranker_cache[self.reranker_name] = CrossEncoder(self.reranker_name)\n    return EmbeddingService._reranker_cache[self.reranker_name]",
                        "notes": "CrossEncoder también es thread-safe para inferencia."
                    }
                },
                {
                    "id": "AI-005",
                    "title": "Contexto narrativo truncado a 2000 caracteres en el prompt de LLM",
                    "severity": "medium",
                    "category": "ml_quality",
                    "file": "backend/app/services/llm_service.py",
                    "line_start": 56,
                    "line_end": 58,
                    "description": "El narrative_context (Markdown del documento completo) se trunca arbitrariamente a 2000 caracteres en el prompt. Para documentos de análisis financiero o informes extensos, esto puede cortar el contexto en medio de una oración, reduciendo la calidad de las explicaciones.",
                    "impact": "Menor calidad en las explicaciones de findings cuando el documento tiene más de ~2000 caracteres de contexto narrativo.",
                    "suggested_fix": {
                        "summary": "Usar los chunks del HybridChunker en lugar del narrativo completo, que ya están optimizados para el context window del LLM",
                        "before": "f\"Contexto del documento: {narrative[:2000]}\" if narrative else \"\"",
                        "after": "# En lugar de truncar el narrativo, usar los chunks relevantes al finding:\n# 1. Buscar los top-3 chunks más relevantes al finding específico\n# 2. Concatenar hasta 4000 tokens\n# Esto aprovecha el HybridChunker ya construido y mejora la calidad",
                        "notes": "Este cambio requiere pasar el retrieval_service al LLMService, o pre-recuperar los chunks relevantes en el orquestador."
                    }
                },
                {
                    "id": "AI-006",
                    "title": "Guardrail de análisis numérico puede generar falsos positivos con años y porcentajes",
                    "severity": "low",
                    "category": "ml_quality",
                    "file": "backend/app/services/analysis_agent.py",
                    "line_start": 57,
                    "line_end": 83,
                    "description": "El guardrail enforce_no_hallucinated_metrics extrae todos los números de la respuesta y verifica que existan en el contexto. El filtro excluye números ≤12 y años 1990-2100, pero no excluye porcentajes (ej: '85%') ni valores como '3.5' que el LLM podría calcular correctamente desde los datos. Esto puede generar ModelRetry innecesarios.",
                    "impact": "Falsos positivos que fuerzan al agente a regenerar respuestas válidas, aumentando latencia y costos.",
                    "suggested_fix": {
                        "summary": "Mejorar el regex de extracción de números para excluir porcentajes y decimales simples",
                        "before": "numbers = set(re.findall(r'\\b\\d+(?:[.,]\\d+)?\\b', response_text))",
                        "after": "# Excluir porcentajes (seguidos de %) y versiones (seguidos de .)\n# Solo verificar números \"suspechosos\": enteros grandes sin contexto obvio\nnumbers = set(re.findall(\n    r'(?<!\\.)\\b(\\d{3,}(?:[.,]\\d+)?)\\b(?!%|\\.|°)',\n    response_text\n))",
                        "notes": "El guardrail sigue siendo útil pero con menos agresividad para no interrumpir respuestas correctas."
                    }
                }
            ]
        },
        {
            "key": "action_plan",
            "title": "Plan de Acción Priorizado",
            "icon": "target",
            "summary": "Listado ordenado por impacto y urgencia. Los items Críticos deben resolverse antes de cualquier despliegue en producción.",
            "actions": {
                "critical": [
                    {
                        "id": "ACT-001",
                        "ref": "BUG-001",
                        "title": "Corregir NameError de 'logger' en analyze.py",
                        "effort": "30 minutos",
                        "impact": "Restaura funcionalidad para usuarios Enterprise",
                        "steps": ["Agregar `import structlog` y `logger = structlog.get_logger(__name__)` al inicio de analyze.py", "Ejecutar tests de regresión en el endpoint /api/analyze"]
                    },
                    {
                        "id": "ACT-002",
                        "ref": "BUG-002",
                        "title": "Corregir AttributeError en delete_session_data",
                        "effort": "1 hora",
                        "impact": "Habilita GDPR compliance y eliminación correcta de datos",
                        "steps": ["Reemplazar `self.db.usage_events` con referencia correcta al cliente db global", "Verificar si la colección usage_events realmente se usa en el sistema", "Agregar test unitario para delete_session_data"]
                    },
                    {
                        "id": "ACT-003",
                        "ref": "BUG-003",
                        "title": "Persistir índice FAISS en MongoDB para habilitar RAG",
                        "effort": "4 horas",
                        "impact": "Habilita la funcionalidad RAG que actualmente está rota en producción",
                        "steps": ["En pipeline_orchestrator.py: llamar serialize_index() después de index_hybrid_sources()", "Guardar bytes + source_map + source_ids en MongoDB via save_hybrid_embeddings_cache()", "En analyze.py: cargar el índice desde MongoDB antes de construir AnalysisDeps", "Test: verificar que search_hybrid_sources() retorna resultados después del ciclo completo"]
                    },
                    {
                        "id": "ACT-004",
                        "ref": "BUG-008 + AI-001",
                        "title": "Mover PipelineOrchestrator al contexto del worker ARQ",
                        "effort": "2 horas",
                        "impact": "Reduce tiempo de procesamiento por documento en 30-60 segundos, reduce RAM en ~60%",
                        "steps": ["Mover `orchestrator = PipelineOrchestrator()` a `on_startup(ctx)`", "Pasar `ctx['orchestrator']` al handler de la tarea", "Implementar class-level cache para SentenceTransformer (AI-001)", "Medir tiempo de procesamiento antes/después"]
                    }
                ],
                "medium": [
                    {
                        "id": "ACT-005",
                        "ref": "BUG-004",
                        "title": "Centralizar configuración Redis de LiteLLM en settings",
                        "effort": "1 hora",
                        "impact": "Consistencia de configuración entre ambientes (local/Docker/K8s)",
                        "steps": ["Mover inicialización litellm.cache dentro del constructor LLMService", "Usar settings.redis_host y settings.redis_port", "Agregar manejo de error si Redis no está disponible (degradar a no-cache)"]
                    },
                    {
                        "id": "ACT-006",
                        "ref": "BUG-007",
                        "title": "Agregar limpieza periódica de archivos temporales",
                        "effort": "2 horas",
                        "impact": "Previene acumulación de archivos en disco en producción",
                        "steps": ["Implementar cron job cleanup_stale_temp_files en WorkerSettings", "Configurar tmpfs en docker-compose.yml para /tmp", "Agregar alerta de monitoreo en uso de disco"]
                    },
                    {
                        "id": "ACT-007",
                        "ref": "AI-003",
                        "title": "Configurar modelos de fallback en LiteLLM Router",
                        "effort": "2 horas",
                        "impact": "Elimina punto único de falla en el pipeline de IA",
                        "steps": ["Agregar LITELLM_FALLBACK_MODEL a Settings", "Configurar fallbacks en el Router de LiteLLM", "Test: simular fallo del modelo primario y verificar fallback"]
                    },
                    {
                        "id": "ACT-008",
                        "ref": "BUG-009",
                        "title": "Agregar timeout y paralelismo en enrichment de findings",
                        "effort": "3 horas",
                        "impact": "Reduce tiempo de procesamiento Gold de ~5min a ~1min para 10 findings",
                        "steps": ["Implementar asyncio.wait_for() con timeout=25s por llamada", "Usar asyncio.gather() con Semaphore(3) para paralelismo", "Medir tiempo total antes/después"]
                    },
                    {
                        "id": "ACT-009",
                        "ref": "BUG-012",
                        "title": "Agregar índices compuestos en MongoDB",
                        "effort": "30 minutos",
                        "impact": "Mejora performance de list_sessions con escala de datos",
                        "steps": ["Agregar índice compuesto (user_id, created_at) en sessions", "Agregar índices en bronze, silver, gold para session_id", "Usar MongoDB Atlas Performance Advisor para detectar índices faltantes"]
                    },
                    {
                        "id": "ACT-010",
                        "ref": "REF-001",
                        "title": "Migrar servicios a FastAPI Dependency Injection",
                        "effort": "1 día",
                        "impact": "Hace el código testeable sin cargar modelos ML reales",
                        "steps": ["Crear factories con @lru_cache para servicios principales", "Reemplazar instancias globales en sessions.py", "Agregar tests con dependency_overrides"]
                    }
                ],
                "low": [
                    {
                        "id": "ACT-011",
                        "ref": "BUG-013",
                        "title": "Reemplazar datetime.utcnow() con datetime.now(timezone.utc)",
                        "effort": "30 minutos",
                        "impact": "Compatibilidad con Python 3.12+, elimina DeprecationWarnings",
                        "steps": ["Buscar y reemplazar en todo el proyecto", "Ejecutar tests de regresión"]
                    },
                    {
                        "id": "ACT-012",
                        "ref": "BUG-011",
                        "title": "Eliminar routers duplicados en main.py",
                        "effort": "30 minutos",
                        "impact": "Limpieza del OpenAPI spec, elimina confusión de rutas",
                        "steps": ["Confirmar que el frontend solo usa rutas /api/*", "Eliminar registros sin prefijo /api", "Verificar que la documentación Swagger no tiene duplicados"]
                    },
                    {
                        "id": "ACT-013",
                        "ref": "REF-002",
                        "title": "Crear helper _to_dict() para normalizar objetos Finding",
                        "effort": "1 hora",
                        "impact": "Reduce 15+ líneas de código duplicado en llm_service.py",
                        "steps": ["Crear app/utils.py con función _to_dict()", "Refactorizar llm_service.py para usar _to_dict()", "Aplicar en otras partes del código donde se accede a findings"]
                    },
                    {
                        "id": "ACT-014",
                        "ref": "REF-004",
                        "title": "Agregar validación de configuración en startup",
                        "effort": "1 hora",
                        "impact": "Detectar configuraciones incompletas al desplegar, no en runtime",
                        "steps": ["Agregar model_validator en Settings para validar LLM config", "Emitir warning si LITELLM_API_KEY no está configurada", "Documentar variables de entorno requeridas en README"]
                    }
                ]
            }
        },
        {
            "key": "next_steps",
            "title": "Próximos Pasos",
            "icon": "rocket",
            "summary": "Items estratégicos fuera del plan de corrección original. Representan la siguiente capa de madurez del proyecto: testabilidad, resiliencia de infraestructura, y evolución del pipeline de IA.",
            "issues": [
                {
                    "id": "NXT-001",
                    "title": "Tests unitarios del backend con dependency_overrides",
                    "severity": "high",
                    "category": "testing",
                    "file": "backend/tests/",
                    "line_start": None,
                    "line_end": None,
                    "description": "Con ACT-010 implementado, los servicios ahora son inyectables vía Depends(). Esto permite reemplazarlos en tests con mocks usando app.dependency_overrides sin cargar modelos ML reales. El primer candidato es delete_session_data() (BUG-002 fix) y el ciclo completo de FAISS persist/load (BUG-003 fix).",
                    "impact": "Sin tests, cada fix futuro puede romper silenciosamente los 14 fixes ya implementados. La deuda de testing es ahora el mayor riesgo de regresión.",
                    "evidence": "0 archivos en backend/tests/. pytest no figura en requirements.txt.",
                    "suggested_fix": {
                        "summary": "Crear test suite con pytest + pytest-asyncio cubriendo los fixes críticos",
                        "before": "# No existen tests. Cualquier cambio puede romper los fixes sin saberlo.",
                        "after": "# backend/tests/test_mongo_repo.py\nimport pytest\nfrom unittest.mock import AsyncMock, patch\nfrom app.repositories.mongo import SessionRepository\n\n@pytest.mark.asyncio\nasync def test_delete_session_data_cleans_all_collections():\n    repo = SessionRepository()\n    # Mockear todas las colecciones\n    repo.sessions = AsyncMock()\n    repo.bronze = AsyncMock()\n    repo.silver = AsyncMock()\n    repo.gold = AsyncMock()\n    repo.embeddings_cache = AsyncMock()\n    repo.hybrid_embeddings_cache = AsyncMock()\n    repo.document_chunks = AsyncMock()\n\n    with patch('app.repositories.mongo.db') as mock_db:\n        mock_db.db = AsyncMock()\n        mock_db.db.__getitem__ = lambda self, key: AsyncMock()\n        result = await repo.delete_session_data('test-session-id')\n\n    assert result is True\n    repo.sessions.delete_one.assert_called_once_with({'session_id': 'test-session-id'})\n    repo.bronze.delete_many.assert_called_once()\n    repo.silver.delete_many.assert_called_once()\n    repo.gold.delete_many.assert_called_once()\n\n# backend/tests/test_analyze_endpoint.py\nfrom fastapi.testclient import TestClient\nfrom unittest.mock import MagicMock, AsyncMock\nfrom app.main import app\nfrom app.api.routes.analyze import get_retrieval_strategy\n\ndef test_analyze_loads_faiss_index():\n    mock_retrieval = MagicMock()\n    mock_retrieval.index = None\n    app.dependency_overrides[get_retrieval_strategy] = lambda: mock_retrieval\n    # ... assert que deserialize_index es llamado si hay cache\n    app.dependency_overrides = {}",
                        "notes": "Instalar: pip install pytest pytest-asyncio httpx. Agregar a requirements.txt y al CI/CD pipeline."
                    }
                },
                {
                    "id": "NXT-002",
                    "title": "CI/CD pipeline con GitHub Actions",
                    "severity": "high",
                    "category": "devops",
                    "file": ".github/workflows/ci.yml",
                    "line_start": None,
                    "line_end": None,
                    "description": "El proyecto no tiene pipeline de CI/CD. Cada PR se mergea sin verificación automática. Con 14 fixes implementados y una arquitectura de pipeline compleja (ARQ + FAISS + MongoDB + LiteLLM), un regression en cualquier fix puede pasar desapercibido.",
                    "impact": "Un merge roto en producción puede deshabilitar el RAG (BUG-003) o crashear el worker (BUG-008) sin alertas automáticas.",
                    "evidence": "No existe directorio .github/. No hay badge de CI en el README.",
                    "suggested_fix": {
                        "summary": "Crear workflow de GitHub Actions con lint + tests en cada PR",
                        "before": "# No existe .github/workflows/ci.yml",
                        "after": "# .github/workflows/ci.yml\nname: CI\n\non:\n  push:\n    branches: [main, develop]\n  pull_request:\n    branches: [main]\n\njobs:\n  backend:\n    runs-on: ubuntu-latest\n    services:\n      mongodb:\n        image: mongo:7\n        ports: ['27017:27017']\n      redis:\n        image: redis:7\n        ports: ['6379:6379']\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - name: Install dependencies\n        run: pip install -r backend/requirements.txt\n      - name: Lint (ruff)\n        run: ruff check backend/\n      - name: Tests\n        run: pytest backend/tests/ -v\n        env:\n          MONGODB_URI: mongodb://localhost:27017\n          REDIS_HOST: localhost\n          JWT_SECRET_KEY: test-secret-key\n\n  frontend:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with:\n          node-version: '20'\n      - run: cd frontend && npm ci\n      - run: cd frontend && npm run build",
                        "notes": "Agregar LITELLM_API_KEY como GitHub Secret para tests de integración opcionales."
                    }
                },
                {
                    "id": "NXT-003",
                    "title": "Implementar OpenSearchRetrievalService para tier Enterprise",
                    "severity": "medium",
                    "category": "feature",
                    "file": "backend/app/api/routes/analyze.py",
                    "line_start": 28,
                    "line_end": 44,
                    "description": "El patrón Strategy en get_retrieval_strategy() tiene un TODO pendiente desde el inicio del proyecto: implementar OpenSearchRetrievalService para usuarios Enterprise. Con BUG-003 resuelto (FAISS persistido), el tier lite es funcional. El siguiente paso es implementar la alternativa escalable para Enterprise usando OpenSearch k-NN.",
                    "impact": "Usuarios Enterprise pagan por funcionalidad diferenciada que actualmente reciben el mismo servicio que lite. Bloquea la propuesta de valor del tier premium.",
                    "evidence": "analyze.py: TODO(sprint-X): Implementar OpenSearchRetrievalService para tier enterprise.",
                    "suggested_fix": {
                        "summary": "Crear OpenSearchRetrievalService implementando BaseRetrievalService",
                        "before": "# get_retrieval_strategy() siempre retorna EmbeddingService() para ambos tiers",
                        "after": "# backend/app/services/retrieval/opensearch_service.py\nfrom opensearchpy import AsyncOpenSearch\nfrom app.services.retrieval.base import BaseRetrievalService\nfrom app.core.config import settings\n\nclass OpenSearchRetrievalService(BaseRetrievalService):\n    def __init__(self):\n        self.client = AsyncOpenSearch(\n            hosts=[{'host': settings.opensearch_host, 'port': settings.opensearch_port}]\n        )\n        self.index_name = 'datax_embeddings'\n\n    async def search_hybrid_sources(self, query: str, session_id: str, top_k: int = 5):\n        # k-NN search con filtro por session_id\n        response = await self.client.search(\n            index=self.index_name,\n            body={\n                'query': {\n                    'bool': {\n                        'filter': [{'term': {'session_id': session_id}}],\n                        'must': [{'knn': {'embedding': {'vector': query_embedding, 'k': top_k}}}]\n                    }\n                }\n            }\n        )\n        return [hit['_source'] for hit in response['hits']['hits']]",
                        "notes": "Agregar opensearch-py a requirements.txt. Configurar OPENSEARCH_HOST/PORT en Settings."
                    }
                },
                {
                    "id": "NXT-004",
                    "title": "Mejorar guardrail anti-alucinaciones en analysis_agent.py",
                    "severity": "low",
                    "category": "ml_quality",
                    "file": "backend/app/services/analysis_agent.py",
                    "line_start": 57,
                    "line_end": 83,
                    "description": "El guardrail enforce_no_hallucinated_metrics extrae números con regex y verifica que existan en el contexto. El regex actual captura porcentajes (85%) y decimales simples (3.5) que el LLM puede calcular correctamente desde los datos. Esto genera ModelRetry innecesarios que aumentan latencia y costos.",
                    "impact": "Falsos positivos que fuerzan al agente a regenerar respuestas válidas. +1-3 llamadas LLM por respuesta con métricas derivadas.",
                    "evidence": "analysis_agent.py línea 63: `numbers = set(re.findall(r'\\b\\d+(?:[.,]\\d+)?\\b', response_text))` — captura todos los números incluyendo porcentajes.",
                    "suggested_fix": {
                        "summary": "Ajustar regex para excluir porcentajes, unidades y números pequeños del guardrail",
                        "before": "numbers = set(re.findall(r'\\b\\d+(?:[.,]\\d+)?\\b', response_text))\nskip = {str(n) for n in range(13)} | {str(y) for y in range(1990, 2101)}\nnumbers -= skip",
                        "after": "# Excluir: porcentajes (seguidos de %), unidades, años y números pequeños\n# Solo verificar enteros >= 100 sin contexto obvio de unidad\nnumbers = set(re.findall(\n    r'(?<!\\.)\\b(\\d{3,}(?:[.,]\\d+)?)\\b(?![%°\\'\"a-zA-Z])',\n    response_text\n))\nskip = {str(y) for y in range(1990, 2101)}  # Años\nnumbers -= skip",
                        "notes": "Test: respuesta con '85% de valores nulos' no debe triggear ModelRetry si '85' es un valor calculado correctamente del dataset."
                    }
                }
            ]
        },
        {
            "key": "frontend",
            "title": "Plan Frontend",
            "icon": "monitor",
            "summary": "Análisis del frontend Next.js 15 + TypeScript. Se identificaron issues de seguridad (token en localStorage), UX críticos (polling sin límite, historial de queries perdido) y deuda técnica de tipado. El frontend está bien estructurado pero tiene vulnerabilidades que afectan la experiencia en producción.",
            "issues": [
                {
                    "id": "FE-001",
                    "title": "JWT token almacenado en localStorage — vulnerable a XSS",
                    "severity": "high",
                    "category": "security",
                    "file": "frontend/src/lib/api.ts",
                    "line_start": 10,
                    "line_end": 18,
                    "description": "El token JWT se almacena en localStorage bajo la clave 'datax_token'. localStorage es accesible por cualquier script JavaScript en la página, incluyendo scripts de terceros inyectados (XSS). En una aplicación que maneja datasets potencialmente sensibles, un token robado permite acceso completo a todas las sesiones del usuario.",
                    "impact": "Si un atacante logra inyectar código JS (XSS en el contenido del dataset analizado, por ejemplo), puede exfiltrar el token y acceder a todas las sesiones del usuario.",
                    "evidence": "api.ts línea 13: `const TOKEN_KEY = 'datax_token'`\napi.ts línea 27: `localStorage.setItem(TOKEN_KEY, result.access_token)`",
                    "suggested_fix": {
                        "summary": "Migrar a httpOnly cookies gestionadas por el servidor Next.js o usar sessionStorage como mínimo",
                        "before": "// En api.ts — token expuesto a XSS\nlocalStorage.setItem(TOKEN_KEY, result.access_token);\nconst token = localStorage.getItem(TOKEN_KEY);",
                        "after": "// Opción 1 (recomendada): Route Handler de Next.js como proxy que setea httpOnly cookie\n// app/api/auth/login/route.ts\nexport async function POST(req: Request) {\n  const body = await req.json();\n  const res = await fetch(`${BACKEND_URL}/api/auth/login`, {\n    method: 'POST',\n    body: JSON.stringify(body),\n    headers: { 'Content-Type': 'application/json' },\n  });\n  const data = await res.json();\n  const response = NextResponse.json({ user: data.user });\n  response.cookies.set('datax_token', data.access_token, {\n    httpOnly: true,   // No accesible desde JS\n    secure: true,     // Solo HTTPS\n    sameSite: 'strict',\n    maxAge: 60 * 60 * 24, // 24 horas\n  });\n  return response;\n}",
                        "notes": "La Opción 1 requiere que todas las llamadas al backend pasen por Route Handlers de Next.js como proxy. La Opción 2 (sessionStorage) reduce el riesgo pero no lo elimina: el token sigue siendo accesible desde JS."
                    }
                },
                {
                    "id": "FE-002",
                    "title": "Polling de sesión sin límite de intentos ni backoff — loop infinito posible",
                    "severity": "high",
                    "category": "reliability",
                    "file": "frontend/src/app/workspace/page.tsx",
                    "line_start": 64,
                    "line_end": 85,
                    "description": "La función poll() dentro de loadSession() se llama recursivamente con setTimeout sin límite de intentos ni timeout total. Si el worker ARQ se cuelga o el documento queda en estado 'processing' indefinidamente, el polling corre para siempre consumiendo requests y memoria. No hay feedback al usuario tras N intentos fallidos.",
                    "impact": "Usuarios con documentos atascados ven el spinner eternamente sin poder reintentar. En producción con muchos usuarios, los requests infinitos pueden saturar el backend.",
                    "evidence": "workspace/page.tsx línea 69: `const poll = async () => {` llamada recursivamente con `setTimeout(poll, 2000)` sin contador de intentos.",
                    "suggested_fix": {
                        "summary": "Agregar máximo de intentos, backoff exponencial y timeout global",
                        "before": "const poll = async () => {\n  try {\n    const d = await api.getSession(sid);\n    if (d.status === 'ready') loadReport(sid);\n    else if (d.status === 'error') { ... }\n    else setTimeout(poll, 2000);  // Sin límite\n  } catch (e) {\n    console.error('Polling error', e);\n  }\n};\npoll();",
                        "after": "const MAX_POLLS = 150;  // 5 minutos máx (150 * 2s)\nlet attempts = 0;\n\nconst poll = async () => {\n  attempts++;\n  if (attempts > MAX_POLLS) {\n    setError({\n      title: 'Tiempo de procesamiento excedido',\n      desc: 'El análisis tardó más de lo esperado. Reintenta o contacta soporte.'\n    });\n    setState('error');\n    return;\n  }\n  try {\n    const d = await api.getSession(sid);\n    setSession(d);\n    if (d.status === 'ready') {\n      loadReport(sid);\n    } else if (d.status === 'error') {\n      setError({ title: 'Error en procesamiento', desc: 'El pipeline falló.' });\n      setState('error');\n    } else {\n      // Backoff suave: 2s primeros 30 intentos, luego 5s\n      const delay = attempts < 30 ? 2000 : 5000;\n      setTimeout(poll, delay);\n    }\n  } catch (e) {\n    console.error('Polling error', e);\n    setTimeout(poll, 5000);  // Reintento tras error de red\n  }\n};\npoll();",
                        "notes": "Con MAX_POLLS=150 y backoff, el timeout máximo es ~5min para documentos complejos, compatible con el job_timeout=600s del worker ARQ."
                    }
                },
                {
                    "id": "FE-003",
                    "title": "getReport() llamado antes de que el worker ARQ complete el pipeline",
                    "severity": "high",
                    "category": "bug",
                    "file": "frontend/src/app/workspace/page.tsx",
                    "line_start": 100,
                    "line_end": 108,
                    "description": "En handleUploadComplete(), se llama loadReport(sessionRes.session_id) inmediatamente después de crear la sesión. Pero la sesión recién creada tiene status='created' o 'processing' — el worker ARQ aún no terminó. getReport() falla porque Bronze/Silver/Gold no están disponibles, causando el error 'Error al generar reporte' para todos los uploads nuevos.",
                    "impact": "Todos los uploads nuevos muestran error inmediatamente, aunque el pipeline esté funcionando correctamente. El usuario ve un error falso y puede pensar que el sistema está roto.",
                    "evidence": "workspace/page.tsx línea 100: `loadReport(sessionRes.session_id)` llamado sin verificar `sessionRes.status === 'ready'`.",
                    "suggested_fix": {
                        "summary": "Redirigir al polling en lugar de llamar loadReport() directamente tras el upload",
                        "before": "const handleUploadComplete = (sessionRes: SessionResponse) => {\n  setSession(sessionRes);\n  router.push(`/workspace?session_id=${sessionRes.session_id}`);\n  loadReport(sessionRes.session_id);  // Error: pipeline aún no terminó\n};",
                        "after": "const handleUploadComplete = (sessionRes: SessionResponse) => {\n  setSession(sessionRes);\n  router.push(`/workspace?session_id=${sessionRes.session_id}`);\n  // Iniciar polling en lugar de cargar el reporte directo.\n  // El pipeline ARQ puede tardar 30-120s. loadReport() se llama\n  // automáticamente desde loadSession() cuando status === 'ready'.\n  loadSession(sessionRes.session_id);\n};",
                        "notes": "loadSession() ya maneja el flujo completo: polling → status=ready → loadReport(). Solo hay que reemplazar la llamada directa."
                    }
                },
                {
                    "id": "FE-004",
                    "title": "Requests en vuelo no se cancelan al desmontar el componente",
                    "severity": "medium",
                    "category": "reliability",
                    "file": "frontend/src/app/workspace/page.tsx",
                    "line_start": 30,
                    "line_end": 55,
                    "description": "Las llamadas a api.getReport(), api.getSession() y api.analyze() no usan AbortController. Si el usuario navega fuera de la página mientras una request está en vuelo, React muestra el warning 'setState on unmounted component' y puede causar comportamientos inesperados si el componente se remonta.",
                    "impact": "Memory leaks en navegación rápida. Posibles race conditions si el usuario vuelve a la página antes de que complete una request anterior.",
                    "evidence": "loadReport() y loadSession() no usan AbortController ni cleanup en el useEffect.",
                    "suggested_fix": {
                        "summary": "Usar AbortController en los useEffect y limpiar en el cleanup",
                        "before": "const loadReport = useCallback(async (sid: string) => {\n  setState('loading_report');\n  try {\n    const data = await api.getReport(sid);\n    setReport(data);\n  } catch (err) { ... }\n}, []);",
                        "after": "const loadReport = useCallback(async (sid: string, signal?: AbortSignal) => {\n  setState('loading_report');\n  try {\n    const data = await api.getReport(sid, signal);\n    if (!signal?.aborted) {\n      setReport(data);\n      setState('ready');\n    }\n  } catch (err) {\n    if ((err as Error).name !== 'AbortError') {\n      setError({ title: 'Error al generar reporte', desc: String(err) });\n      setState('error');\n    }\n  }\n}, []);\n\nuseEffect(() => {\n  const controller = new AbortController();\n  if (sessionIdParam) loadSession(sessionIdParam, controller.signal);\n  return () => controller.abort();  // Cleanup al desmontar\n}, [sessionIdParam]);",
                        "notes": "api.ts también debe aceptar signal?: AbortSignal y pasarlo al fetch()."
                    }
                },
                {
                    "id": "FE-005",
                    "title": "QueryPanel sin historial de conversación — respuestas previas se pierden",
                    "severity": "medium",
                    "category": "ux",
                    "file": "frontend/src/components/QueryPanel.tsx",
                    "line_start": 16,
                    "line_end": 45,
                    "description": "Cada nueva query sobreescribe el resultado anterior con setResult(response). El usuario no puede ver respuestas anteriores sin volver a preguntar. Para una herramienta de análisis de datos donde el usuario explora el dataset con múltiples preguntas, perder el historial degrada significativamente la UX.",
                    "impact": "El usuario tiene que recordar manualmente las respuestas anteriores. No puede comparar ni referenciar respuestas en la misma sesión.",
                    "evidence": "QueryPanel.tsx línea 32: `setResult(response)` reemplaza el estado anterior.",
                    "suggested_fix": {
                        "summary": "Cambiar result (objeto) a messages (array) para mantener historial de conversación",
                        "before": "const [result, setResult] = useState<AnalyzeResponse | null>(null);\n// ...\nsetResult(response);\n// ...\n{result && <div>Respuesta...</div>}",
                        "after": "interface Message {\n  query: string;\n  response: AnalyzeResponse;\n  timestamp: Date;\n}\n\nconst [messages, setMessages] = useState<Message[]>([]);\n// ...\nsetMessages(prev => [...prev, {\n  query: currentQuery,\n  response,\n  timestamp: new Date()\n}]);\n// ...\n<div className='messages-list'>\n  {messages.map((msg, i) => (\n    <div key={i} className='message-item'>\n      <div className='query-bubble'>{msg.query}</div>\n      <div className='response-bubble'>{msg.response.answer}</div>\n    </div>\n  ))}\n</div>\n<button onClick={() => setMessages([])}>Limpiar historial</button>",
                        "notes": "Limitar a los últimos 20 mensajes en memoria para evitar crecimiento infinito del estado."
                    }
                },
                {
                    "id": "FE-006",
                    "title": "Errores de red en polling no notifican al usuario",
                    "severity": "medium",
                    "category": "ux",
                    "file": "frontend/src/app/workspace/page.tsx",
                    "line_start": 75,
                    "line_end": 82,
                    "description": "Cuando el polling falla con un error de red (backend caído, timeout), el código solo hace console.error() y reintenta en 5s. El usuario sigue viendo el spinner sin saber que hay un problema de conectividad. No hay toast ni indicador visual de 'reconnecting...'.",
                    "impact": "En deployments con backend inestable, el usuario ve el spinner indefinidamente sin poder tomar acción (recargar, esperar, contactar soporte).",
                    "evidence": "workspace/page.tsx línea 79: `console.error('Polling error', e)` — sin actualización de UI.",
                    "suggested_fix": {
                        "summary": "Mostrar toast/banner de reconexión cuando el polling falla repetidamente",
                        "before": "} catch (e) {\n  console.error('Polling error', e);\n  // Silencioso para el usuario\n}",
                        "after": "} catch (e) {\n  networkErrors++;\n  if (networkErrors >= 3) {\n    // Mostrar banner de reconexión después de 3 fallos consecutivos\n    setConnectionWarning('Problemas de conexión. Reintentando...');\n  }\n  setTimeout(poll, 5000);\n}",
                        "notes": "Implementar un componente ConnectionBanner que aparezca/desaparezca automáticamente."
                    }
                },
                {
                    "id": "FE-007",
                    "title": "Tipos any/unknown en contracts.ts generan runtime errors silenciosos",
                    "severity": "medium",
                    "category": "code_quality",
                    "file": "frontend/src/types/contracts.ts",
                    "line_start": 1,
                    "line_end": 15,
                    "description": "Artifact.data: unknown y source_metadata: Record<string, unknown> son tipos que fuerzan casts implícitos en todos los componentes que los consumen. Cuando el backend cambia la estructura (por ejemplo, agrega un campo a source_metadata), el frontend no genera error en compilación — el bug aparece en runtime.",
                    "impact": "Cambios en el contrato del backend no son detectados por TypeScript. Los bugs de tipado solo aparecen en producción.",
                    "evidence": "contracts.ts línea 2: `data: unknown`. workspace/page.tsx: `session.source_metadata.filename as string` (cast forzado).",
                    "suggested_fix": {
                        "summary": "Tipar explícitamente source_metadata y usar Zod para validación en runtime",
                        "before": "export interface SessionResponse {\n  source_metadata: Record<string, unknown>;  // Tipo débil\n}\n// En workspace:\nconst filename = session.source_metadata.filename as string;  // Cast inseguro",
                        "after": "// contracts.ts — tipos explícitos\nexport interface SourceMetadata {\n  filename: string;\n  content_type: string;\n  file_size_bytes: number;\n  table_index?: number;\n}\n\nexport interface SessionResponse {\n  source_metadata: SourceMetadata;  // Tipo fuerte\n}\n\n// workspace.tsx — sin casts\nconst filename = session.source_metadata.filename;  // Type-safe",
                        "notes": "Para validación en runtime agregar: import { z } from 'zod' y crear schemas. Esto detecta cambios de API en tests de integración."
                    }
                },
                {
                    "id": "FE-008",
                    "title": "Tab activo no persiste en URL — se pierde al recargar",
                    "severity": "low",
                    "category": "ux",
                    "file": "frontend/src/app/workspace/page.tsx",
                    "line_start": 22,
                    "line_end": 24,
                    "description": "El tab activo se almacena solo en estado local (useState). Al recargar la página, siempre se vuelve al tab 'overview'. Tampoco es posible compartir un link directo a un tab específico (ej: '?tab=findings' para compartir con un colega).",
                    "impact": "Mala UX para usuarios que trabajan con reports grandes y necesitan recargar. No permite deep-linking a tabs específicos.",
                    "evidence": "workspace/page.tsx línea 22: `const [activeTab, setActiveTab] = useState('overview')` — sin sincronización con URL.",
                    "suggested_fix": {
                        "summary": "Sincronizar el tab activo con el query param ?tab= en la URL",
                        "before": "const [activeTab, setActiveTab] = useState('overview');",
                        "after": "const tabParam = searchParams.get('tab') || 'overview';\nconst [activeTab, setActiveTab] = useState(tabParam);\n\nconst handleTabChange = (tab: string) => {\n  setActiveTab(tab);\n  // Actualizar URL sin re-render completo\n  const params = new URLSearchParams(searchParams.toString());\n  params.set('tab', tab);\n  router.replace(`/workspace?${params.toString()}`, { scroll: false });\n};",
                        "notes": "Validar que tabParam sea un valor permitido antes de usarlo como estado inicial."
                    }
                },
                {
                    "id": "FE-009",
                    "title": "NEXT_PUBLIC_API_BASE_URL hardcodeado al puerto incorrecto (8000 vs 8001)",
                    "severity": "low",
                    "category": "bug",
                    "file": "frontend/src/lib/api.ts",
                    "line_start": 13,
                    "line_end": 13,
                    "description": "El fallback de NEXT_PUBLIC_API_BASE_URL está seteado a 'http://localhost:8000' pero el backend FastAPI corre en el puerto 8001 según la configuración del servidor. Esto causa errores de conexión silenciosos en desarrollo si la variable de entorno no está seteada.",
                    "impact": "Desarrolladores nuevos que clonan el repositorio sin configurar .env.local ven errores de conexión sin causa obvia.",
                    "evidence": "api.ts línea 13: `const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'` — el backend corre en 8001.",
                    "suggested_fix": {
                        "summary": "Corregir el puerto del fallback y agregar validación explícita",
                        "before": "const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';",
                        "after": "const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';\n\nif (process.env.NODE_ENV === 'development' && !process.env.NEXT_PUBLIC_API_BASE_URL) {\n  console.warn('[api.ts] NEXT_PUBLIC_API_BASE_URL no configurada. Usando fallback:', API_BASE_URL);\n}",
                        "notes": "Agregar NEXT_PUBLIC_API_BASE_URL=http://localhost:8001 al .env.example para guiar a nuevos developers."
                    }
                },
                {
                    "id": "FE-010",
                    "title": "Manipulación directa del DOM en QueryPanel — anti-pattern de React",
                    "severity": "low",
                    "category": "code_quality",
                    "file": "frontend/src/components/QueryPanel.tsx",
                    "line_start": 44,
                    "line_end": 52,
                    "description": "El scroll y highlight de fuentes usa document.getElementById() + classList.add/remove() directamente. Esto bypasea el sistema de renderizado de React y puede causar inconsistencias si el componente se re-renderiza entre la llamada al DOM y el timeout de limpieza.",
                    "impact": "Potential race condition: el elemento puede haberse desmontado antes de que el setTimeout limpie las clases CSS. No testeable con React Testing Library.",
                    "evidence": "QueryPanel.tsx línea 44: `const element = document.getElementById(sourceId)` + `element.classList.add('ring-2', 'ring-indigo-500')`.",
                    "suggested_fix": {
                        "summary": "Usar refs y estado de React en lugar de manipulación directa del DOM",
                        "before": "const element = document.getElementById(sourceId);\nif (element) {\n  element.scrollIntoView({ behavior: 'smooth', block: 'center' });\n  element.classList.add('ring-2', 'ring-indigo-500');\n  setTimeout(() => element.classList.remove('ring-2', 'ring-indigo-500'), 3000);\n}",
                        "after": "const [highlightedSource, setHighlightedSource] = useState<string | null>(null);\nconst sourceRefs = useRef<Record<string, HTMLElement | null>>({});\n\nconst handleSourceClick = (sourceId: string) => {\n  const el = sourceRefs.current[sourceId];\n  if (el) {\n    el.scrollIntoView({ behavior: 'smooth', block: 'center' });\n    setHighlightedSource(sourceId);\n    setTimeout(() => setHighlightedSource(null), 3000);\n  }\n};\n\n// En el JSX:\n<div\n  ref={el => { sourceRefs.current[sourceId] = el; }}\n  className={cn('source-item', highlightedSource === sourceId && 'ring-2 ring-indigo-500')}\n>",
                        "notes": "cn() de shadcn/ui maneja la condicionalidad de clases CSS de forma limpia."
                    }
                }
            ]
        }
    ]
}

@app.get("/api/report")
async def get_full_report():
    """Returns the complete audit report."""
    return AUDIT_REPORT

@app.get("/api/report/summary")
async def get_report_summary():
    """Returns just the summary stats."""
    return {
        "meta": AUDIT_REPORT["meta"],
        "sections": [
            {"key": s["key"], "title": s["title"], "icon": s["icon"]}
            for s in AUDIT_REPORT["sections"]
        ]
    }

@app.get("/api/report/issues")
async def get_issues(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    section: Optional[str] = Query(None)
):
    """Returns filtered issues from bugs, refactoring, and AI/ML sections."""
    all_issues = []
    for sec in AUDIT_REPORT["sections"]:
        if section and sec["key"] != section:
            continue
        for issue in sec.get("issues", []):
            issue_with_section = {**issue, "section": sec["key"]}
            all_issues.append(issue_with_section)
    
    if severity:
        all_issues = [i for i in all_issues if i.get("severity") == severity]
    if category:
        all_issues = [i for i in all_issues if i.get("category") == category]
    if q:
        q_lower = q.lower()
        all_issues = [i for i in all_issues if 
                     q_lower in i.get("title", "").lower() or 
                     q_lower in i.get("description", "").lower() or
                     q_lower in i.get("file", "").lower()]
    
    return {"issues": all_issues, "total": len(all_issues)}

@app.get("/api/report/export.md", response_class=PlainTextResponse)
async def export_markdown():
    """Exports the full report as Markdown."""
    report = AUDIT_REPORT
    meta = report["meta"]
    
    md = f"""# Reporte de Auditoría: {meta['repo']}

**Fecha:** {meta['analysis_date']}  
**Rama:** {meta['branch']}  
**Commit:** `{meta['commit'][:8]}`  
**Analista:** {meta['analyst']}

## Resumen Ejecutivo

{meta['summary']}

### Estadísticas

| Severidad | Cantidad |
|-----------|---------- |
| 🔴 Crítico | {meta['stats']['critical']} |
| 🟠 Alto | {meta['stats']['high']} |
| 🟡 Medio | {meta['stats']['medium']} |
| 🔵 Bajo | {meta['stats']['low']} |
| **Total** | **{meta['stats']['total_issues']}** |

"""
    
    # Add each section
    for section in report["sections"]:
        md += f"\n## {section['title']}\n\n{section.get('summary', '')}\n\n"
        
        for issue in section.get("issues", []):
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(issue["severity"], "⚪")
            md += f"### [{severity_emoji} {issue['id']}] {issue['title']}\n\n"
            md += f"**Archivo:** `{issue.get('file', 'N/A')}` (L{issue.get('line_start', '?')}-L{issue.get('line_end', '?')})\n\n"
            md += f"**Descripción:** {issue.get('description', '')}\n\n"
            md += f"**Impacto:** {issue.get('impact', '')}\n\n"
            
            fix = issue.get("suggested_fix", {})
            if fix:
                md += f"**Fix Sugerido:** {fix.get('summary', '')}\n\n"
                if fix.get("before"):
                    md += f"```python\n# ANTES\n{fix['before']}\n```\n\n"
                if fix.get("after"):
                    md += f"```python\n# DESPUÉS\n{fix['after']}\n```\n\n"
        
        # Action plan
        if "actions" in section:
            actions = section["actions"]
            for priority in ["critical", "medium", "low"]:
                for action in actions.get(priority, []):
                    emoji = {"critical": "🔴", "medium": "🟡", "low": "🔵"}.get(priority, "")
                    md += f"### [{emoji} {action['id']}] {action['title']}\n\n"
                    md += f"**Esfuerzo:** {action['effort']} | **Impacto:** {action['impact']}\n\n"
                    for step in action.get("steps", []):
                        md += f"- {step}\n"
                    md += "\n"
    
    return md

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "data-x-audit-api"}
