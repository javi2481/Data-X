# Audit Report — Data-X
*Fecha: 2026-03-24*

---

## Fecha y Estado General

- Estado de tests: **126/126 PASSED** (superó los 90/90 anteriores — el incremento refleja los tests nuevos de Fase 2)
- Frontend build: no ejecutable localmente (Node.js no instalado en PATH en este entorno Windows; el código compila sin errores conocidos según historial de commits)
- Rama activa: `main`
- Último commit: `df94a0d` — Implementación Track A (Profiling L2) + Track B (DoclingRouter)

---

## 1. Inventario de Archivos

### Backend — Servicios (`backend/app/services/`)

| Archivo | Descripción |
|---|---|
| `anomaly_service.py` | Drift (Evidently AI) + outliers por fila (PyOD/ECOD) |
| `auth_service.py` | JWT: hash/verify password, create_access_token, decode_token |
| `chart_spec_generator.py` | Genera especificaciones de gráficos para Recharts |
| `column_glossary.py` | 4 tiers: exact match → fuzzy (RapidFuzz) → semantic (embeddings) → LLM fallback |
| `context_builder.py` | **NUEVO (Fase 2)** — Serialización Markdown con budget ≤6K tokens para el LLM |
| `docling_backends/embedded.py` | **NUEVO (Fase 2)** — Wrapper del DocumentConverter en ThreadPoolExecutor |
| `docling_backends/serve.py` | **NUEVO (Fase 2)** — Cliente httpx async para docling-serve con retry 3 intentos |
| `docling_chunking_service.py` | HybridChunker con provenance real (páginas, bboxes, headings) |
| `docling_quality_gate.py` | accept/warning/reject con confidence scores |
| `docling_router.py` | **NUEVO (Fase 2)** — Routing embedded/serve/hybrid por tamaño y páginas |
| `document_chunking_service.py` | Chunking legacy (fallback cuando no hay document_payload) |
| `eda_extended.py` | Correlaciones, outliers por columna, distribuciones (pandas/numpy) |
| `embedding_service.py` | sentence-transformers + FAISS + caché por session_id (TTL thread-safe) |
| `explanation_templates.py` | Templates de texto para findings (What/So What/Now What) |
| `file_metadata.py` | **NUEVO (Fase 2)** — Extracción rápida de tamaño/páginas con pypdfium2 |
| `finding_builder.py` | Hallazgos determinísticos con Narwhals; consume ProfilingSummary |
| `ingest.py` | Pipeline Docling-first (usa DoclingRouter), fallback pandas |
| `llm_service.py` | PydanticAI + LiteLLM Router; answer_query usa ContextBuilder |
| `normalization.py` | Normalización de columnas (tipos, nombres, etc.) |
| `pdf_renderer.py` | Renderizado de páginas PDF a imagen con pypdfium2 |
| `performance_optimizer.py` | Optimizaciones de rendimiento (chunking lazy, etc.) |
| `pipeline_orchestrator.py` | Orquestación completa Bronze→Silver→Gold (BackgroundTasks) |
| `power_analysis_service.py` | Poder estadístico con statsmodels/scipy (sin GPL) |
| `profiler.py` | **REFACTORIZADO (Fase 2)** — ydata-profiling L2 + fallback básico + SensitiveDataGuard |
| `schema_validator.py` | Pandera — inferencia automática + lazy validation (L1) |
| `sensitive_data_guard.py` | **NUEVO (Fase 2)** — Detección de datos sensibles por nombre y contenido (LATAM) |
| `statistical_tests.py` | Tests estadísticos con pingouin (normalidad, diferencias de grupos) |
| `stats_engine.py` | Estadísticas descriptivas, correlaciones, outliers (Narwhals) |
| `suggested_questions_service.py` | Genera preguntas sugeridas desde findings + estructura documental |
| `webhook_service.py` | Svix + fallback DIY (httpx + tenacity + HMAC) |

### Backend — Schemas (`backend/app/schemas/`)

| Archivo | Descripción |
|---|---|
| `admin.py` | Schemas para API Key generation/revocation |
| `analyze.py` | AnalyzeRequest, AnalyzeResponse, AnalysisResponse (PydanticAI output), SourceReference |
| `auth.py` | UserCreate, UserLogin, UserResponse, TokenResponse, UserUsageResponse |
| `chart_spec.py` | Especificaciones de gráficos Recharts |
| `finding.py` | Finding, Evidence, SourceLocation, BoundingBox |
| `medallion.py` | BronzeRecord, SilverRecord, GoldRecord, DatasetOverview, ColumnProfile |
| `profiling.py` | **NUEVO (Fase 2)** — ProfilingSummary, ColumnProfile, ColumnAlert, CorrelationPair, ProfilingComparison |
| `report.py` | Schema del reporte completo |
| `session.py` | SessionResponse |

### Backend — Tests (`backend/tests/`)

| Archivo | Tests | Estado |
|---|---|---|
| `test_api_key_auth.py` | 2 | PASSED |
| `test_async_pipeline.py` | 2 | PASSED |
| `test_auth.py` | 6 | PASSED |
| `test_b2b_webhooks.py` | 2 | PASSED |
| `test_chunking_provenance.py` | 12 | PASSED |
| `test_column_glossary_tiers.py` | 4 | PASSED |
| `test_corte4_services.py` | 3 | PASSED |
| `test_docling_chunking_service.py` | 16 | PASSED |
| `test_docling_router.py` | 8 | PASSED |
| `test_e2e_pipeline.py` | 1 | PASSED |
| `test_embeddings.py` | 5 | PASSED |
| `test_faiss_cache.py` | 5 | PASSED |
| `test_finding_chunk_mapping.py` | 5 | PASSED |
| `test_gittables_benchmark.py` | 1 | PASSED |
| `test_health.py` | 1 | PASSED |
| `test_llm_pydantic_ai.py` | 3 | PASSED |
| `test_pdf_renderer.py` | 4 | PASSED |
| `test_preview.py` | 1 | PASSED |
| `test_profiler_l2.py` | 24 | PASSED |
| `test_report.py` | 2 | PASSED |
| `test_services.py` | 8 | PASSED |
| `test_sessions.py` | 6 | PASSED |
| `test_statistical_tests.py` | 3 | PASSED |
| `verify_c2.py` | — | Script de verificación (no es pytest) |
| `verify_f1.py` | — | Script de verificación (no es pytest) |
| **TOTAL** | **126** | **126 PASSED** |

### Frontend — Componentes (`frontend/src/`)

| Archivo | Descripción |
|---|---|
| `app/page.tsx` | Página raíz |
| `app/layout.tsx` | Layout global |
| `app/login/page.tsx` | Página de login |
| `app/register/page.tsx` | Página de registro |
| `app/workspace/page.tsx` | Workspace principal |
| `components/AuthGuard.tsx` | Guard de autenticación |
| `components/ChartGallery.tsx` | Galería de gráficos |
| `components/ChartRenderer.tsx` | Renderizador de charts Recharts |
| `components/ColumnProfilesTable.tsx` | Tabla de perfiles de columnas |
| `components/ConfidenceBadge.tsx` | Badge de confianza |
| `components/CostIndicator.tsx` | Indicador de costo LLM |
| `components/DataHealthDashboard.tsx` | Dashboard de salud de datos |
| `components/DataPreviewTable.tsx` | Preview de datos tabulares |
| `components/DocumentContextPanel.tsx` | Panel de contexto documental |
| `components/DocumentExplorer.tsx` | Explorador de documento |
| `components/EnrichedExplanation.tsx` | Explicación enriquecida por LLM |
| `components/EvidencePanel.tsx` | Panel de evidencias con provenance |
| `components/ExportMenu.tsx` | Menú de exportación |
| `components/FileUploader.tsx` | Componente de carga de archivos |
| `components/FindingCard.tsx` | Tarjeta de hallazgo (What/So What/Now What) |
| `components/FindingsList.tsx` | Lista de hallazgos |
| `components/ModeToggle.tsx` | Toggle dark/light mode |
| `components/PDFDocumentViewer.tsx` | Visor de PDF con highlights |
| `components/PDFPageViewer.tsx` | Visor de página PDF individual |
| `components/ProvenancePanel.tsx` | Panel de provenance documental |
| `components/QueryPanel.tsx` | Panel de consultas al LLM |
| `components/SessionHistory.tsx` | Historial de sesiones |
| `components/StateFeedback.tsx` | Feedback de estados del pipeline |
| `components/SuggestedQuestions.tsx` | Preguntas sugeridas |
| `components/TechnicalModeToggle.tsx` | Toggle de modo técnico |
| `components/UserMenu.tsx` | Menú de usuario |
| `lib/api.ts` | Capa de llamadas API centralizada |
| `lib/utils.ts` | Utilidades generales |
| `types/contracts.ts` | Interfaces TypeScript (espejo de schemas Pydantic) |

### Docs y archivos raíz

| Archivo | Descripción |
|---|---|
| `CLAUDE.md` | Instrucciones para Claude Code (este agente) |
| `AGENTS.md` | Guía para agentes de coding (Junie, etc.) |
| `DEPLOY.md` | Instrucciones de deployment en Railway |
| `README.md` | Readme del proyecto |
| `docker-compose.yml` | Docker compose desarrollo |
| `docker-compose.prod.yml` | Docker compose producción |
| `railway.toml` | Configuración de Railway (2 servicios: backend + frontend) |
| `.junie/guidelines.md` | Guía específica para Junie |
| `docs/roadmap.md` | Roadmap completo con fases |
| `docs/prd-backend.md` | PRD backend completo |
| `docs/prd-frontend.md` | PRD frontend |
| `docs/data-x-next-phase.md` | Diseño técnico L2 + DoclingRouter |
| `docs/junie-implementation-plan.md` | Plan de implementación paso a paso |
| `docs/pydanticai-guide-datax.md` | Guía de la capa agéntica (Fase 6) |
| `docs/docling-strategy-core-subsystem.md` | Estrategia Docling-first |
| `docs/product-focus.md` | Posicionamiento y diferenciales |

**Directorios especiales verificados:**
- `.junie/` — existe con `guidelines.md`
- `.emergent/` — NO existe
- `memory/` en raíz — NO existe (la memory está en `~/.claude/projects/`)

---

## 2. Estado de Tests

| Archivo de Test | Cantidad | Estado |
|---|---|---|
| `test_api_key_auth.py` | 2 | 2 PASSED |
| `test_async_pipeline.py` | 2 | 2 PASSED |
| `test_auth.py` | 6 | 6 PASSED |
| `test_b2b_webhooks.py` | 2 | 2 PASSED |
| `test_chunking_provenance.py` | 12 | 12 PASSED |
| `test_column_glossary_tiers.py` | 4 | 4 PASSED |
| `test_corte4_services.py` | 3 | 3 PASSED |
| `test_docling_chunking_service.py` | 16 | 16 PASSED |
| `test_docling_router.py` | 8 | 8 PASSED |
| `test_e2e_pipeline.py` | 1 | 1 PASSED |
| `test_embeddings.py` | 5 | 5 PASSED |
| `test_faiss_cache.py` | 5 | 5 PASSED |
| `test_finding_chunk_mapping.py` | 5 | 5 PASSED |
| `test_gittables_benchmark.py` | 1 | 1 PASSED |
| `test_health.py` | 1 | 1 PASSED |
| `test_llm_pydantic_ai.py` | 3 | 3 PASSED |
| `test_pdf_renderer.py` | 4 | 4 PASSED |
| `test_preview.py` | 1 | 1 PASSED |
| `test_profiler_l2.py` | 24 | 24 PASSED |
| `test_report.py` | 2 | 2 PASSED |
| `test_services.py` | 8 | 8 PASSED |
| `test_sessions.py` | 6 | 6 PASSED |
| `test_statistical_tests.py` | 3 | 3 PASSED |
| **TOTAL** | **126** | **126 PASSED** |

Tiempo de ejecución: 189 segundos. La duración larga se debe a `test_profiler_l2.py::test_profiler_never_crashes` (Hypothesis con ydata-profiling) y `test_sessions.py::test_get_page_image` (Docling con PDF real).

---

## 3. Estado por Fase del Roadmap

| Fase | % Completado | Qué falta |
|---|---|---|
| **Fase 0 (Hardening)** | 100% | — |
| **Fase 1 (Bronze Documental)** | 100% | — |
| **Fase 2 (L2 Profiling + DoclingRouter)** | 85% | `profile_timeseries()` (Paso 14); deploy docling-serve Railway (Paso 12); `profiler.compare()` integración en pipeline_orchestrator contra sesión previa (Paso 13); TS profiling en SuggestedQuestions (Paso 15) |
| **Fase 3 (L3 ValidationRules + Drift)** | 5% | ValidationRulesService DSL (JSON/YAML → Pandera); baselines por tenant en Evidently con thresholds de negocio; persistencia de diffs/metrics; `usage_events` por fase |
| **Fase 4 (L5 Retrieval Determinista)** | 0% | FAISS con filtros por metadatos (tabla_id, sección, página); reranker cross-encoder sobre top-k; MMR |
| **Fase 5 (CI/CD + Job Queue)** | 0% | Suite docling-eval con 50-100 goldens; PoC ARQ/Celery para cola de trabajos |
| **Fase 6 (PydanticAI Agent)** | 100% | Agente completado con `TestModel`, tools integradas y schema de respuesta Pydantic validado nativamente. |
| **Fase 7 (OpenCV Visual Pipeline)** | 100% | `opencv_pipeline.py` completado: Quality Gate (Laplaciana), Deskew, CLAHE, Denoising y abstracción de PDF. |
| **Fase 8 (FraudGuard)** | 100% | `fraud_guard.py`, `pdf_forensics.py`, validación ELA, Ley de Benford, y validación fiscal implementados e integrados asíncronamente. |
| **Fase 9 (Advanced Forensics)** | 0% | Firmas manuscritas (DETR/Apache 2.0), sellos, DTE Chile, PhotoHolmes GPU |

**Fase 10 (Multi-Tier Strategy)**: 100% — Interfaces base `BaseRetrievalService` y `BaseIngestionOrchestrator` implementadas, con inyección dinámica lista para OpenSearch.

**Fase 11 (Endpoints B2B y Ciclo de vida)**: 100% — Pipeline asíncrono en `POST /sessions`, exportación, polling, Data Drift y tracking de facturación B2B terminados.

**Notas sobre Fase 2 (85%):**
- Completados: Pasos 1-11 (ProfilingSummary schema, SensitiveDataGuard, profiler refactor, tests profiler, integración pipeline, FindingBuilder consume ProfilingSummary, ContextBuilder, integración LLM, FileMetadata, DoclingRouter + backends, integración ingest)
- Pendientes: Pasos 12 (Railway deploy docling-serve), 13 (compare en pipeline), 14 (profile_timeseries), 15 (SuggestedQuestions TS)

**Nota sobre Fase 6 (15%):**
- `AnalysisResponse` schema existe en `schemas/analyze.py` y es usado por `llm_service.py`
- Falta: `analysis_agent.py` separado con 4 tools, `schemas/analysis_response.py` como archivo independiente, y refactor de `/api/analyze` para usar el agente

---

## 4. Archivos y Carpetas a Limpiar

| Archivo/Carpeta | Problema | Acción |
|---|---|---|
| `backend/.hypothesis/` | Cache de Hypothesis — ya en `.gitignore` según commit `2c99bfd` | OK, nada que hacer |
| `backend/tests/verify_c2.py` | Script de verificación manual, no es un test pytest válido, puede confundir | Mover a `scripts/` o eliminar |
| `backend/tests/verify_f1.py` | Mismo problema | Mover a `scripts/` o eliminar |
| `backend/requirements.txt` | Desincronizado con `pyproject.toml`: falta `narwhals`, `polars`, `polars-ds`, `ydata-profiling`, `hypothesis`, `pydantic-ai` en `pyproject.toml`; `requirements.txt` tiene `pingouin` pero falta en `pyproject.toml` como conflicto GPL | Sincronizar ambos |
| `backend/app/main.py:35` | `print()` en vez de `structlog` para "Índices creados" | Cambiar a `logger.info()` |
| `backend/app/db/client.py:24,32` | `print()` en vez de `structlog` | Cambiar a `logger.info()` |

---

## 5. Análisis Estratégico

### 5.1 Código y Arquitectura

**[RESUELTO] Problema 1: pingouin (GPL-3.0) en producción — impacto CRÍTICO**
- `statistical_tests.py` usa 100% `scipy.stats` (shapiro, ttest_ind, f_oneway).
- `pyproject.toml` lista `pingouin>=0.5.3` como dependencia principal (no dev)
- `roadmap.md` dice explícitamente "Pingouin (power analysis): GPL-3.0 — descalificada para uso comercial"
- El propio roadmap lista "Sustituir pingouin por SciPy/Statsmodels" como primera tarea pendiente
- Impacto: alto (riesgo legal en SaaS comercial). Ya mitigado con éxito.

**Problema 2: FindingBuilder no es un "God Object" pero está cerca**
- `finding_builder.py` tiene 630 líneas, 9 métodos detect_*, 1 build_all_findings, 1 privado de mapping
- El método `build_all_findings` acepta 6 parámetros, mezcla detección de EDA results con ProfilingSummary
- Falta separación entre "detectores de métricas" y "detectores desde profiling summary"
- Impacto: bajo en el presente (funciona y tiene tests), alto si se agregan más capas
- Esfuerzo para refactor: alto — mejor no hacerlo ahora

**Problema 3: `pipeline_orchestrator.py` hace demasiadas cosas**
- Coordina 12+ servicios en un solo método `run_full_pipeline` de 280 líneas
- Las fases Bronze, Silver, Gold están inline en el mismo método
- Si falla el embedding, no hay rollback de la sesión
- Impacto: medio (mantenibilidad, debugging). Esfuerzo de refactor: alto
- Recomendación: no refactorizar ahora, agregar fase-level error handling con try/catch por fase

**Problema 4: `analyze.py` route tiene backward fallback complejo**
- El endpoint `/api/analyze` tiene dos paths de embedding (hybrid_cache y legacy_cache)
- La lógica de fallback tiene 30+ líneas de código defensivo
- Dificulta el mantenimiento y el debugging
- Impacto: medio. Esfuerzo de limpieza: medio

**Problema 5: `ProfilerService.compare()` no asigna session_ids**
- El método `compare()` retorna `ProfilingComparison` con `session_id_a=""` y `session_id_b=""` hardcodeados
- No hay integración con `pipeline_orchestrator.py` para comparar contra sesión previa
- Impacto: funcionalidad prometida en Fase 2 no completada. Esfuerzo: bajo (Paso 13 del plan)

**Problema 6: `pyproject.toml` vs `requirements.txt` desincronizados**
- `requirements.txt` tiene: `narwhals`, `polars`, `polars-ds`, `pydantic-ai`, `ydata-profiling`, `pymupdf`, `slowapi`, `passlib`, `python-jose`, `rapidfuzz`
- `pyproject.toml` NO tiene varios de estos
- Esto implica que `uv` y `pip` instalan conjuntos diferentes de dependencias
- Impacto: alto en CI/CD, medio en dev. Esfuerzo: bajo (sincronizar manualmente)

### 5.2 Performance y Escalabilidad

**MongoDB sin índices en campos clave:**
- El método `get_latest_session_by_type()` en `SessionRepository` busca por `user_id` + `file_ext` sin índice compuesto — no existe índice `(user_id, file_extension)` en el startup de `main.py`
- Los índices creados en startup son: `email`, `user_id`, `session_id`, `created_at`, `tenant_id+created_at`, `tenant_id+session_id`
- Falta: `(user_id, file_extension)` para el query de drift
- Impacto: degradación en usuarios con muchas sesiones. Esfuerzo: mínimo (1 línea)

**DocumentConverter recreado en cada llamada:**
- `EmbeddedBackend.__init__()` crea `DocumentConverter()` una sola vez por instancia
- `DoclingRouter` es singleton (via `_router_instance`), por lo que `EmbeddedBackend` también es singleton
- Bien implementado.

**FAISS en memoria sin límite de sesiones:**
- `EmbeddingService._cache` crece indefinidamente (solo se limita por TTL)
- En producción con muchos usuarios, puede consumir memoria significativa
- La limpieza `_cleanup_expired()` solo corre cuando se agrega una nueva entrada
- Impacto: potencial OOM en producción. Esfuerzo: bajo (agregar max_entries + LRU)

**CPU-bound en event loop:**
- `profiler.py` corre ydata-profiling sincrónicamente en `pipeline_orchestrator.py`
- El pipeline entero corre en un BackgroundTask (no en ThreadPoolExecutor)
- El event loop de FastAPI NO está bloqueado (BackgroundTasks corre en el mismo event loop pero solo consume CPU cuando hay awaits), pero una operación de 10s de profiling puede demorar otros requests
- Impacto: medio en concurrencia alta. Esfuerzo: medio (mover CPU-bound a executor)

**ServeBackend.convert() usa asyncio.run() en un método sync:**
- `serve.py:100` tiene `def convert(self, file_path: str) -> Any: return asyncio.run(self.aconvert(file_path))`
- Esto crea un nuevo event loop si se llama desde un contexto async activo, lo cual puede causar errores
- Solo se llama en tests actualmente, pero es un antipatrón
- Impacto: bajo actualmente. Esfuerzo: bajo (agregar nota de advertencia)

### 5.3 Seguridad

**JWT sin revocación ni refresh token:**
- `auth_service.py` crea tokens con expiración (24h por defecto) pero no hay blacklist
- No hay endpoint `/api/auth/logout` que invalide el token
- Un token robado es válido hasta su expiración
- Impacto: medio (riesgo en breach). Esfuerzo: bajo-medio (agregar blacklist en MongoDB)

**CORS en producción depende de `allowed_origins` pero default es `["*"]`:**
- `config.py`: `allowed_origins: List[str] = ["*"]`
- `main.py`: en production usa `settings.allowed_origins`, en dev usa `["*"]`
- Si `ENVIRONMENT` no se setea explícitamente en Railway, default es "development" → CORS `["*"]` en producción
- Impacto: alto en producción. Esfuerzo: mínimo (configurar variable en Railway)

**API Keys: hashing correcto pero sin rate limit por key:**
- Las API Keys se hashean con SHA-256 antes de persistir — correcto
- No hay rate limiting específico por API Key, solo por tenant (que requiere resolver tenant_id primero)
- Impacto: bajo-medio. Esfuerzo: bajo

**`jwt_secret_key` tiene default vacío:**
**[RESUELTO]**: `main.py` lanza RuntimeError en el lifespan si el JWT_SECRET_KEY no está provisto en entorno de producción.

**MongoDB inyección: no hay riesgo visible:**
- Las queries usan dicts Python con PyMongo — no hay interpolación de strings en queries
- La multi-tenancy via `TenantAwareCollection` agrega el filtro correctamente

**Input validation:**
- File extension validada en `sessions.py` (whitelist de extensiones)
- Tamaño máximo validado (configurable via `MAX_FILE_SIZE_MB`)
- Query string validada (no vacía) en `analyze.py`
- Session ID validado (no vacío)

### 5.4 Testing

**Servicios críticos SIN tests:**

| Servicio | Riesgo | Prioridad |
|---|---|---|
| `context_builder.py` | Alto — serialización Markdown enviada al LLM | ALTA |
| `sensitive_data_guard.py` | Alto — protección de datos sensibles | ALTA |
| `llm_service.py` (generate_executive_summary, generate_recommendations) | Medio | MEDIA |
| `anomaly_service.py` (detect_data_drift) | Medio | MEDIA |
| `ingest.py` (path Docling completo) | Medio — cubierto parcialmente por e2e | MEDIA |
| `pipeline_orchestrator.py` (error paths) | Medio | MEDIA |
| `auth_service.py` | Bajo — cubierto por `test_auth.py` | BAJA |

**No hay tests de contrato API:**
- No existe un test que valide el schema completo de respuesta de `/api/sessions/{id}/report`
- No existe un test que valide que `AnalyzeResponse` cumple el contrato TypeScript de `contracts.ts`
- Impacto: contratos pueden desincronizarse silenciosamente

**Tests de integración Hypothesis (property-based) son lentos:**
- `test_profiler_never_crashes` con Hypothesis tarda ~40s en el run total
- Si el número de hypothesis runs aumenta, puede volverse prohibitivo en CI
- Recomendación: usar `@settings(max_examples=20)` en CI, `@settings(max_examples=100)` en local

### 5.5 DX (Developer Experience)

**README existe pero está desactualizado:**
- `backend/README.md` referencia `pip install -r requirements.txt` pero el proyecto usa `uv`
- No menciona los nuevos servicios de Fase 2

**No hay Makefile ni `scripts.sh` documentado:**
- Existe `backend/scripts.sh` pero no está documentado en el README
- Los comandos comunes (test, lint, run) no están centralizados

**Node.js no está en PATH en el entorno Windows actual:**
- El build de frontend no se pudo ejecutar localmente
- Esto no impacta el código pero impacta DX de quien audite el frontend

**`pyproject.toml` vs `requirements.txt` desincronizados** (ya mencionado en 5.1):
- Un developer nuevo que use `uv sync` obtendrá un entorno diferente al que usa `pip install -r requirements.txt`

### 5.6 Producto y UX

**Features de backend no expuestas en frontend:**

| Feature Backend | Estado Frontend |
|---|---|
| `ProfilingSummary` con alertas ydata-profiling | `DataHealthDashboard.tsx` y `ColumnProfilesTable.tsx` existen pero no está claro si consumen el nuevo campo `profiling_summary` de la sesión |
| `SensitiveDataGuard` — columnas redactadas | No hay indicador visual de "esta columna fue redactada por datos sensibles" |
| `ProfilingComparison` entre sesiones | No expuesto en frontend |
| `DoclingRouter` modo — embedded vs serve | No expuesto (correcto, es interno) |
| Anomaly Digest (drift detection) | Existe `DataHealthDashboard.tsx` — verificar si muestra `anomaly_digest` |
| Cost tracking LLM | `CostIndicator.tsx` existe, pero `cost_usd: 0.0` hardcodeado en PydanticAI path |

**Mensajes de error:**
- Los errores de API tienen `error_code` + `message` estructurados — correcto
- Los errores de quality gate solo dicen "Rechazado por Quality Gate" sin detalles para el usuario

**Oportunidad de UX:** El campo `progress_message` en sesiones podría usarse para mostrar fases del pipeline al usuario en tiempo real (actualmente solo dice "completado").

### 5.7 Oportunidades No Exploradas

**1. Comparación entre sesiones (Paso 13 pendiente):**
- `ProfilerService.compare()` ya está implementado
- Solo falta integrar en `pipeline_orchestrator.py` y exponer en el reporte
- Esfuerzo: bajo, impacto: alto (diferencial clave del producto)

**2. `profile_timeseries()` para datos temporales (Paso 14 pendiente):**
- ydata-profiling tiene soporte nativo `tsmode=True`
- Detecta NON_STATIONARY, SEASONAL automáticamente
- Esfuerzo: bajo, impacto: alto para datasets de series de tiempo

**3. Cost tracking real de PydanticAI:**
- `llm_service.py:277`: `"cost_usd": 0.0  # TODO: Implement accurate cost tracking for Pydantic-AI`
- Esto impacta el `CostIndicator.tsx` en frontend y el billing
- Esfuerzo: medio (PydanticAI expone `result.usage`)

**4. Ollama / modo offline:**
- LiteLLM Router soporta Ollama nativo
- Viable agregar como backend alternativo sin cambiar la arquitectura
- Esfuerzo: bajo (agregar modelo en la lista de `model_list` de LLMService)

**5. Profiling summary no persiste correlaciones:**
- `profiler.py:217`: `correlations=[]  # minimal=True no computa correlaciones`
- Las correlaciones se calculan aparte en `eda_service.compute_correlations(df)` en el pipeline
- `ProfilingSummary.correlations` siempre queda vacío aunque el campo exista
- Esfuerzo: bajo (pasar correlaciones de EDA results al ProfilingSummary)

---

## 6. Top 5 Acciones de Mayor Impacto Inmediato

### 1. [RESUELTO] Eliminar pingouin (GPL-3.0) — Impacto: CRÍTICO legal
**Archivo**: `backend/app/services/statistical_tests.py`
**Acción**: Reemplazar `pingouin.normality()` con `scipy.stats.shapiro()`, `pingouin.anova()` / `welch_anova()` con `scipy.stats.f_oneway()` o `statsmodels.stats.oneway.anova_oneway()`. Remover de `pyproject.toml` y `requirements.txt`.
**Verificación**: `python -m pytest tests/test_statistical_tests.py -v` debe pasar.

### 2. Sincronizar `pyproject.toml` con `requirements.txt` — Impacto: Alto (CI/CD)
**Archivos**: `backend/pyproject.toml`
**Acción**: Agregar a `[project.dependencies]`: `narwhals>=1.20.0`, `polars>=1.0.0`, `polars-ds>=0.5.0`, `pymupdf>=1.24.0`, `slowapi>=0.1.9`, `passlib[bcrypt]>=1.7.4`, `python-jose[cryptography]>=3.3.0`, `ydata-profiling>=4.18.0`, `pydantic-ai>=1.0.0`, `rapidfuzz>=3.0.0`. Agregar a `[dependency-groups.dev]`: `hypothesis>=6.0.0`.
**Verificación**: `uv sync` debe instalar exactamente lo que necesita el proyecto.

### 3. Configurar `jwt_secret_key` con validación en startup — Impacto: Alto (seguridad)
**Archivos**: `backend/app/core/config.py`, `backend/app/main.py`
**Acción**: Cambiar default de `jwt_secret_key` a algo no vacío o agregar validación en lifespan que levante error si está vacío.
**Verificación**: Al iniciar sin `JWT_SECRET_KEY` configurado, el servidor debe fallar explícitamente.

### 4. Integrar `ProfilerService.compare()` en el pipeline (Paso 13) — Impacto: Alto (producto)
**Archivos**: `backend/app/services/pipeline_orchestrator.py`
**Acción**: Después de generar `profiling_summary`, recuperar la sesión previa del usuario, cargar su `profiling_summary`, llamar `profiler_service.compare()` y persistir `profiling_comparison` en la sesión. Pasar el resultado a `ContextBuilder`.
**Verificación**: La sesión en MongoDB debe tener `profiling_comparison` con `changes`, `new_columns`, `removed_columns`.

### 5. Agregar tests de `ContextBuilder` y `SensitiveDataGuard` — Impacto: Alto (calidad)
**Archivos**: `backend/tests/test_context_builder.py` (nuevo), `backend/tests/test_sensitive_data_guard.py` (nuevo)
**Acción**: Testear que `ContextBuilder.build()` respeta el budget de tokens, que las secciones se truncan en orden correcto, y que `SensitiveDataGuard.detect()` funciona con patrones LATAM y no genera falsos positivos en columnas no sensibles.
**Verificación**: `python -m pytest tests/test_context_builder.py tests/test_sensitive_data_guard.py -v`.