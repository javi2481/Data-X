# Implementation Roadmap — Data-X
*Última actualización: 2026-03-24*
*Basado en auditoría completa del estado real del código*

---

## Estado Actual (Resumen Ejecutivo)

- Tests Fase 2: **PASSED** en cobertura focalizada (`test_profiler_l2.py`, `test_sessions.py`, `test_services.py`, `test_suggested_questions_service.py`)
- Pipeline L1→L2: **100% funcional** — ProfilingSummary, SensitiveDataGuard, ContextBuilder, DoclingRouter integrados y testeados
- Fase 2 backend: **COMPLETADA** — comparación entre sesiones, profiling temporal on-demand y SuggestedQuestions con trigger temporal implementados
- Fase 2.5: **COMPLETADA** — deuda técnica crítica resuelta (pingouin eliminado, dependencias sincronizadas, validación JWT en startup)
- Próximo hito: iniciar Fase 3 (ValidationRules + Drift Temporal)
- Deploy y producción: se abordan al final, solo después de implementar y validar localmente todas las features

---

## Fase 2 — L2 Profiling + DoclingRouter (COMPLETADA)

### Checklist de Aceptación Fase 2

- [x] `schemas/profiling.py` — ProfilingSummary, ColumnProfile, ColumnAlert, CorrelationPair, ProfilingComparison
- [x] `services/sensitive_data_guard.py` — detección por nombre y contenido, patrones LATAM
- [x] `services/profiler.py` refactorizado — ydata-profiling + fallback básico + SensitiveDataGuard integrado
- [x] `tests/test_profiler_l2.py` — 24 tests incluyendo Hypothesis (todos PASSED)
- [x] Profiler integrado en `pipeline_orchestrator.py` — ProfilingSummary persistido en sesión
- [x] FindingBuilder consume ProfilingSummary — método `_findings_from_profiling_summary()` implementado
- [x] `services/context_builder.py` — Markdown con budget de tokens ≤6K, 5 secciones priorizadas
- [x] ContextBuilder integrado en `llm_service.answer_query()`
- [x] `services/file_metadata.py` — FileMetadata, extract_metadata con PyMuPDF
- [x] `services/docling_router.py` — DoclingRouter singleton, modos embedded/serve/hybrid
- [x] `services/docling_backends/embedded.py` — DocumentConverter en ThreadPoolExecutor
- [x] `services/docling_backends/serve.py` — cliente httpx async con retry 3 intentos
- [x] `tests/test_docling_router.py` — 8 tests incluyendo Hypothesis (todos PASSED)
- [x] DoclingRouter integrado en `services/ingest.py`
- [x] `profiler.compare()` integrado en `pipeline_orchestrator.py` contra sesión previa (Paso 13)
- [x] `profile_timeseries()` on-demand (Paso 14)
- [x] TS profiling en SuggestedQuestions (Paso 15)

---

### Paso 13: Integrar `profiler.compare()` en el pipeline

**Estado**: COMPLETADO

**Archivos**:
- `backend/app/services/pipeline_orchestrator.py`
- `backend/app/repositories/mongo.py`
- `backend/app/schemas/session.py`

**Qué se hizo**:
- Se integró `ProfilerService.compare()` dentro del pipeline Silver después del profiling principal
- Se persiste `profiling_comparison` en `sessions`
- Se corrigió `get_latest_session_by_type()` para usar sesiones `completed` en lugar de `ready`
- `SessionResponse` ahora expone `profiling_comparison` como contrato tipado

**Verificación**:
- Test agregado en `backend/tests/test_services.py`
- La comparación queda persistida con `session_id_a`, `session_id_b` y `changes`

---

### Paso 14: `profile_timeseries()` on-demand

**Estado**: COMPLETADO

**Archivos**:
- `backend/app/services/profiler.py`
- `backend/app/api/routes/sessions.py`

**Qué se hizo**:
- Se agregó `profile_timeseries(df, date_column)` en `ProfilerService`
- Se valida que la columna exista, que pueda parsearse a datetime y que tenga suficientes fechas válidas
- Se agregó el endpoint `GET /api/sessions/{id}/timeseries-profile?date_column=...`
- El endpoint reconstruye el DataFrame desde Bronze `raw_data` y devuelve `ProfilingSummary`

**Verificación**:
- Tests agregados en `backend/tests/test_profiler_l2.py`
- Tests de API agregados en `backend/tests/test_sessions.py`

---

### Paso 15: TS profiling en SuggestedQuestions

**Estado**: COMPLETADO

**Archivos**:
- `backend/app/services/suggested_questions_service.py`
- `backend/app/api/routes/analyze.py`

**Qué se hizo**:
- `generate_questions()` ahora acepta `profiling_summary`
- Si el profiling detecta columnas `datetime`, se agrega la pregunta sugerida temporal correspondiente
- Todas las preguntas ahora incluyen `requires_timeseries`, con `false` por defecto y `true` en las temporales
- El endpoint de suggested questions reconstruye `ProfilingSummary` desde la sesión y lo pasa al servicio

**Verificación**:
- Tests agregados en `backend/tests/test_suggested_questions_service.py`
- Cobertura del endpoint en `backend/tests/test_sessions.py`

---

## Fase 2.5 — Deuda Técnica Crítica (COMPLETADA)

Esta fase ya fue resuelta. La deuda técnica crítica quedó cerrada antes de continuar con las siguientes features.

- [x] **Paso D1: Eliminar pingouin (GPL-3.0)** — reemplazado por `scipy/statsmodels`
- [x] **Paso D2: Sincronizar `pyproject.toml` con `requirements.txt`**
- [x] **Paso D3: Seguridad — JWT secret key validation** en startup

---

## Fase 3 — L3 ValidationRules + Drift Temporal (Semanas 7-8)

### Paso 1: ValidationRulesService (DSL JSON → Pandera)

**Archivos**:
- `backend/app/services/validation_rules_service.py` (NUEVO)
- `backend/app/schemas/validation_rules.py` (NUEVO)

**Qué hacer**:
- Schema Pydantic `ValidationRule`: columna, tipo, rango min/max, regex, required, etc.
- `ValidationRulesService.apply(df, rules: list[ValidationRule]) -> ValidationResult`
- `ValidationResult`: passed, failed_columns, error_details
- Almacenar reglas por `tenant_id + dataset_type` en MongoDB (colección `validation_rules`)
- Endpoint `POST /api/sessions/{id}/validation-rules` para definir reglas

**Verificación**:
```bash
python -c "from app.services.validation_rules_service import ValidationRulesService; print('OK')"
python -m pytest tests/test_validation_rules.py -v
```

---

### Paso 2: Baselines Evidently con thresholds por tenant

**Archivo**: `backend/app/services/profiler.py` y `backend/app/services/anomaly_service.py` (MODIFICAR)

**Qué hacer**:
- **Eliminar la dependencia externa y sobreingeniería de `Evidently AI`.**
- Usar la funcionalidad nativa de `ydata-profiling` (`profile_current.compare(profile_baseline)`) para calcular de forma 100% determinística el *Data Drift*.
- Extraer las métricas de distancia (PSI, Wasserstein) directamente del objeto de comparación generado por ydata.
- Modificar `anomaly_service.py` para que lea estos datos sin recalcular estadísticas.

**Verificación**: `python -m pytest tests/test_anomaly_drift.py -v`

---

### Paso 3: `usage_events` — tracking de tiempos por fase

**Archivo**: `backend/app/services/pipeline_orchestrator.py` (MODIFICAR)

**Qué hacer**:
Instrumentar cada fase del pipeline con tiempos:
```python
usage_event = {
    "session_id": session_id,
    "phase": "profiling_l2",
    "duration_ms": ...,
    "rows_processed": ...,
    "tokens_to_llm": ...,
    "llm_cost_usd": ..., # **Usar `litellm.completion_cost()` obligatoriamente**
    "faiss_hit": ...,
}
await repo.save_usage_event(usage_event)
```

**Verificación**: La sesión debe tener `usage_events` con tiempos por fase.

---

## Fase 4 — L5 Retrieval Determinista (Semanas 9-11)

### Paso 1: FAISS con filtros por metadatos

**Archivo**: `backend/app/services/retrieval/faiss_strategy.py` (MODIFICAR)

**Qué hacer**:
- Consolidar FAISS estrictamente para el Tier B2C/PyME (bajo costo, in-memory).
- Mantener filtrado post-retrieval (recuperar top-100, filtrar por metadatos, retornar top-k).
- Evitar sobreingeniería aquí, ya que los volúmenes B2C (pocos PDFs) no justifican una base vectorial pesada.

**Verificación**: `python -m pytest tests/test_faiss_filters.py -v`

---

### Paso 2: Reranker cross-encoder (liviano para B2C)

**Archivo**: `backend/app/services/embedding_service.py` (MODIFICAR)

**Qué hacer**:
- Agregar `rerank(query, candidates, top_k) -> list` usando `cross-encoder/ms-marco-MiniLM-L-6-v2` (MIT, ~66MB)
- Solo reranquear cuando hay más de 10 candidatos
- Registrar scores de reranking en el log para evaluación

**Dependencia nueva**: `sentence-transformers` ya incluida — los cross-encoders son parte del mismo paquete.

**Verificación**: `python -m pytest tests/test_reranker.py -v` — verificar que el reranker mejora el recall@5.

---

## Fase 5 — CI/CD + Job Queue (Semanas 12-13)

### Paso 1: Suite docling-eval con goldens

**Archivo**: `backend/tests/test_docling_eval.py` (NUEVO)

**Qué hacer**:
- Crear 20-50 pares (archivo, expected_tables) en `tests/fixtures/goldens/`
- Test que valida que Docling extrae las tablas correctas
- Threshold: si el accuracy baja más de 0.5pp respecto al baseline guardado, el test falla
- Integrar en CI como step separado (no en el run principal de 126 tests)

---

### Paso 2: Job Queue con ARQ + Redis

**Archivos**:
- `backend/app/services/job_queue.py` (NUEVO)
- `backend/app/worker.py` (NUEVO)

**Qué hacer**:
- Reemplazar `BackgroundTasks` por ARQ (AsyncIO task queue sobre Redis)
- Mantener el endpoint POST /api/sessions como 202 + polling
- Agregar estados: QUEUED → PROCESSING → COMPLETED/FAILED
- Agregar reintentos con backoff exponencial (3 intentos)
- Cancelación: `POST /api/sessions/{id}/cancel`

**Dependencia nueva**: `arq>=0.25` (MIT)

**Verificación**: `docker-compose up redis && python -m pytest tests/test_job_queue.py -v`

---

### Paso 3: Observabilidad Distribuida (OpenTelemetry)

**Archivo**: `backend/app/core/telemetry.py` (NUEVO)

**Qué hacer**:
- Integrar `opentelemetry-api` y `opentelemetry-sdk`.
- Configurar el *tracer* para correlacionar los requests de FastAPI con los jobs encolados en ARQ/Redis.
- Inyectar spans automáticos en las llamadas a `docling-serve` y LiteLLM para medir latencias exactas de red.

**Dependencias nuevas**: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`.

---

## Fase 6 — PydanticAI Agent para Queries Multi-paso (Semanas 14-16)

**Prerequisito**: Fases 3, 4 completadas (ValidationRules, baselines, FAISS con filtros).

### Paso 1: Schema `AnalysisResponse` como archivo separado

**Archivo**: `backend/app/schemas/analysis_response.py` (NUEVO)

**Qué hacer**:
Mover `AnalysisResponse` desde `schemas/analyze.py` a su propio archivo. Agregar campos:
```python
class AnalysisResponse(BaseModel):
    answer: str
    key_findings: list[str]
    data_quality_warnings: list[str]
    confidence: Literal["high", "medium", "low"]
    sources_used: list[SourceReference]
    tools_called: list[str] = []          # nuevo: qué tools usó el agente
    reasoning_steps: list[str] = []       # nuevo: pasos del razonamiento
```

**Verificación**: `python -c "from app.schemas.analysis_response import AnalysisResponse; print('OK')"`

---

### Paso 2: `AnalysisDeps` — contexto del agente

**Archivo**: `backend/app/services/analysis_agent.py` (NUEVO)

**Qué hacer**:
```python
from dataclasses import dataclass
from app.schemas.profiling import ProfilingSummary

@dataclass
class AnalysisDeps:
    session_id: str
    user_id: str
    profiling_summary: ProfilingSummary | None
    findings: list[dict]
    chunks: list[dict]
    dataset_meta: dict
```

---

### Paso 3: `analysis_agent.py` con 4 tools

**Archivo**: `backend/app/services/analysis_agent.py` (NUEVO)

**Qué hacer**:
```python
from pydantic_ai import Agent, RunContext
from app.services.embedding_service import EmbeddingService
from app.schemas.analysis_response import AnalysisResponse

analysis_agent = Agent(
    model,  # OpenAIModel desde settings
    output_type=AnalysisResponse,
    deps_type=AnalysisDeps,
    system_prompt="""Sos un analista de datos. Aplica la técnica CoD (Chain of Drafts). 
Antes de responder, genera un borrador lógico interno ultra-conciso. Basa tus conclusiones 
ESTRICTAMENTE en las tools proporcionadas. NUNCA computes datos directamente."""
)

@analysis_agent.tool
async def search_documents(ctx: RunContext[AnalysisDeps], query: str, top_k: int = 5) -> list[dict]:
    """Busca chunks documentales relevantes en FAISS."""
    svc = EmbeddingService()
    # cargar índice desde ctx.deps
    return svc.search_hybrid_sources(query, top_k=top_k)

@analysis_agent.tool
async def get_dataset_profile(ctx: RunContext[AnalysisDeps]) -> str:
    """Retorna ProfilingSummary como Markdown."""
    if ctx.deps.profiling_summary is None:
        return "No hay perfil de dataset disponible."
    from app.services.context_builder import ContextBuilder
    builder = ContextBuilder(max_tokens=2000)
    builder.add_dataset_summary(
        filename=ctx.deps.dataset_meta.get("filename", "dataset"),
        row_count=ctx.deps.dataset_meta.get("row_count", 0),
        col_count=ctx.deps.dataset_meta.get("column_count", 0),
        profiling_summary=ctx.deps.profiling_summary,
    )
    return builder.build()

@analysis_agent.tool
async def get_findings(ctx: RunContext[AnalysisDeps], category: str | None = None) -> list[dict]:
    """Retorna findings filtrados por categoría."""
    findings = ctx.deps.findings
    if category:
        findings = [f for f in findings if f.get("category") == category]
    return findings[:10]

@analysis_agent.tool
async def get_column_details(ctx: RunContext[AnalysisDeps], column_name: str) -> dict:
    """Retorna el perfil completo de una columna específica."""
    if ctx.deps.profiling_summary is None:
        return {}
    col = ctx.deps.profiling_summary.columns.get(column_name)
    if col is None:
        return {"error": f"Columna '{column_name}' no encontrada"}
    return col.model_dump()
```

**Verificación**:
```bash
python -c "from app.services.analysis_agent import analysis_agent; print('OK')"
python -m pytest tests/test_analysis_agent.py -v
```

---

### Paso 4: Tests del agente con TestModel (sin API calls)

**Archivo**: `backend/tests/test_analysis_agent.py` (NUEVO)

**Qué hacer**:
```python
from pydantic_ai.models.test import TestModel

async def test_analysis_agent_basic():
    from app.services.analysis_agent import analysis_agent, AnalysisDeps
    deps = AnalysisDeps(
        session_id="test",
        user_id="user1",
        profiling_summary=None,
        findings=[{"title": "Test", "category": "data_gap", "severity": "important"}],
        chunks=[],
        dataset_meta={"filename": "test.csv", "row_count": 100, "column_count": 5},
    )
    with analysis_agent.override(model=TestModel()):
        result = await analysis_agent.run("¿Cuántas filas tiene el dataset?", deps=deps)
    assert result.data.answer != ""
    assert result.data.confidence in ["high", "medium", "low"]
```

**Verificación**: `python -m pytest tests/test_analysis_agent.py -v` — debe pasar sin usar API key real.

---

### Paso 5: Modificar `/api/analyze` para usar el agente

**Archivo**: `backend/app/api/routes/analyze.py` (MODIFICAR)

**Qué hacer**:
- Mantener el path actual de RAG lineal como fallback
- Agregar `USE_AGENT_MODE = settings.environment == "production"` como feature flag
- Cuando USE_AGENT_MODE, construir `AnalysisDeps` y llamar `analysis_agent.run(query, deps=deps)`
- El resultado debe ser idéntico al contrato de `AnalyzeResponse`

**Verificación**: `python -m pytest tests/test_sessions.py tests/test_llm_pydantic_ai.py -v` — todos PASSED.

---

## Fase 7 — OpenCV: Capa Visual Complementaria a Docling (Semanas 17-20)

### Paso 1: Quality gate visual

**Archivo**: `backend/app/services/opencv_pipeline.py` (NUEVO)

**Qué hacer**:
- `quality_gate_image(image: np.ndarray) -> dict`: varianza Laplaciana + BRISQUE
- Si varianza < umbral: reject con reason="LOW_SHARPNESS"
- Integrar antes de Docling en `ingest.py` solo si el archivo es imagen

**Dependencia nueva**: `opencv-python-headless>=4.8.0` (Apache 2.0). NO usar `opencv-python` (incluye GUI, +200MB innecesarios).

---

### Paso 2: Deskew y preprocesamiento

**Archivo**: `backend/app/services/opencv_pipeline.py` (COMPLETADO)

**Qué hacer**:
- Deskew implementado puramente con `cv2.minAreaRect` y `cv2.warpAffine` (eliminando `jdeskew`).
- CLAHE y Denoising aplicados.
- Conversión de PDF a imagen con `pypdfium2` mitigando el riesgo AGPL.

**Dependencias nuevas**: `opencv-python-headless>=4.8.0`, `pypdfium2`.

---

### Paso 3: Validación de tablas post-Docling

**Archivo**: `backend/app/services/opencv_pipeline.py` (COMPLETADO)

**Qué hacer**:
- En lugar de librerías externas como `img2table`, auditar directamente el `confidence_score` del modelo TableFormer nativo de Docling.

**Dependencia nueva**: **Ninguna externa, 100% dependiente de Docling + OpenCV.**

---

## Fase 8 — FraudGuard (Semanas 21-26)

### Paso 1: Schema `FraudReport`

**Archivo**: `backend/app/schemas/fraud.py` (NUEVO)

**Qué hacer**:
```python
class FraudFinding(BaseModel):
    layer: Literal["pdf_forensics", "visual_forensics", "numeric_semantic", "fiscal_validation"]
    indicator: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    evidence: str
    page: Optional[int] = None
    confidence: float  # 0.0–1.0

class FraudReport(BaseModel):
    session_id: str
    risk_score: float  # 0.0–100.0 ponderado
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    findings: list[FraudFinding]
    disclaimer: str = "Estos son indicadores probabilísticos, no determinaciones legales."
    generated_at: datetime
```

---

### Paso 2: Layer 1 — PDF Forensics

**Archivo**: `backend/app/services/pdf_forensics.py` (COMPLETADO)

**Qué hacer**:
- Análisis de metadatos con `pikepdf` (detección de Photoshop, iLovePDF).
- Análisis Visual Forense Nativo con `cv2.absdiff` para Error Level Analysis (ELA) implementado en el pipeline visual.
- Verificación criptográfica de firmas con `pyhanko` para PAdES.

**Dependencias nuevas**:

| Paquete | Versión | Licencia |
|---|---|---|
| `pikepdf` | `>=8.0` | MPL-2.0 |
| `pdfminer.six` | `>=20221105` | MIT |
| `pyhanko` | `>=0.20` | MIT |

---

### Paso 3: Layer 3 — Validación Numérica (Benford)

**Archivo**: `backend/app/services/benford_service.py` (COMPLETADO)

**Qué hacer**:
- Servicio que aplica Chi-cuadrado y p-value sobre el primer dígito significativo de columnas financieras.
- Emite severidad basada en desviaciones estadísticas estándar.

**Dependencia nueva**: `benford-py>=0.2` (MIT)

---

### Paso 4: Layer 4 — Validación Fiscal LATAM

**Archivo**: `backend/app/services/fiscal_validator.py` (COMPLETADO)

**Qué hacer**:
- Validación CUIT Argentina (algoritmo módulo 11).
- Integración estructural lista para CFDI México vía `satcfdi`.

**Dependencia nueva**: `satcfdi>=1.0` (MIT). NO usar `cfdiclient` (GPLv3).

---

### Paso 5: Orquestador FraudGuard

**Archivo**: `backend/app/services/fraud_guard.py` (COMPLETADO)

**Qué hacer**:
- `FraudGuard.analyze()` ejecutando las 4 capas de forma asíncrona mediante `asyncio.gather()`.
- Ponderación dinámica de `risk_score` (0 a 100) y asignación de nivel de severidad.

**Verificación**: `python -m pytest tests/test_fraud_guard.py -v`

---

## Fase 9 — OpenCV + FraudGuard Avanzado (Semanas 27+)

Los detalles completos están en `docs/roadmap.md`. Los pasos de esta fase requieren GPU para TruFor y PhotoHolmes.

| Item | Paquete | Licencia | Nota |
|---|---|---|---|
| Firmas manuscritas | `transformers` (DETR/YOLOS) | Apache 2.0 | Reemplaza a Ultralytics (AGPL) para detección open-source segura. Hardening con **IBM/adversarial-robustness-toolbox**. |
| Validación DTE Chile | `cl-sii` o `apigateway.cl` | Evaluar licencia | — |
| Benchmark forense | `imdl-benco` | MIT | Para benchmarks internos |

---

## Fase 10 y 11 — Multi-Tier Strategy y Endpoints de Gestión (COMPLETADAS)

**Qué se hizo**:
- Implementación del **Patrón Strategy** para Búsqueda (FAISS vs OpenSearch) e Ingesta (Docling Local vs IBM Data Prep Kit).
- Creación de `BaseRetrievalService` y `BaseIngestionOrchestrator` con contratos estrictos.
- Actualización de `POST /api/sessions` para procesar asincrónicamente mediante ARQ y retornar HTTP 202.
- Implementación de endpoints de gestión: `GET /api/sessions/{id}/status` (Polling), `DELETE /api/sessions/{id}` (GDPR), `GET /api/sessions/{id}/export` (CSV) y `POST /api/sessions/{id}/compare` (Data Drift).
- Paginación enriquecida en `GET /api/sessions` con conteo total.
- Caché distribuido en Redis para respuestas del LLM (LiteLLM).
- Eliminación de deuda técnica: limpieza de `pingouin`, archivos mal ubicados (`docs/base.py`), y `asyncio.sleep` artificial.

---

## Fase 12 — Frontend y Experiencia de Usuario (PRÓXIMO PASO)

**Qué hacer**:
- Configurar **Zustand** para la gestión del estado global de la sesión.
- Migrar JWT de `localStorage` a cookies `httpOnly` mediante API Routes de Next.js (BFF).
- Construir UI para consumir reportes avanzados (FraudGuard, Data Drift, Costos).
- Integrar herramientas de generación de UI (Lovable/Emergent) basadas en los contratos de `types/contracts.ts`.

## Fase Final — Deploy y Producción

**Nota**: Esta fase no se toca hasta completar, integrar y testear localmente todas las features de las Fases 2 a 9.

### Paso 12: Deploy docling-serve en Railway

**Archivo**: `railway.toml` (MODIFICAR)

**Qué hacer**:
- Agregar tercer servicio `data-x-docling` usando imagen `quay.io/docling-project/docling-serve-cpu:latest`, puerto 5001
- En el servicio `data-x-backend`, agregar variables:
  - `DOCLING_MODE=hybrid`
  - `DOCLING_SERVE_URL=http://data-x-docling.railway.internal:5001`
  - `DOCLING_PAGES_THRESHOLD=15`
  - `DOCLING_SIZE_THRESHOLD_MB=10`
  - `DOCLING_SERVE_TIMEOUT=300`

**Verificación**: Subir un PDF de más de 15 páginas. En logs debe aparecer `docling_routing_decision` con `backend=serve`. El pipeline debe completar normalmente.

### Producción y hardening de entorno

**Qué incluir en esta fase**:
- Configuración de CORS para producción
- Variables de entorno definitivas de Railway
- Revisión y ajuste de `docker-compose.prod.yml`
- Despliegue de la arquitectura Multi-Tier (FAISS in-memory para B2C, OpenSearch Serverless / Contenedor para B2B).

---

## Dependencias Nuevas (Tabla Completa)

| Paquete | Versión mínima | Licencia | Fase que la necesita | Notas |
|---|---|---|---|---|
| `narwhals` | `>=1.20.0` | MIT | Ya en uso (falta en pyproject.toml) | Sincronizar |
| `polars` | `>=1.0.0` | MIT | Ya en uso | Sincronizar |
| `polars-ds` | `>=0.5.0` | MIT | Ya en uso | Sincronizar |
| `pypdfium2`| `>=4.0.0` | MIT | Fase 3 / 7 | Reemplazo directo de PyMuPDF (AGPL) |
| `pydantic-ai` | `>=1.0.0` | MIT | Ya en uso + Fase 6 | Sincronizar |
| `hypothesis` | `>=6.0.0` | MPL-2.0 | Ya en uso (dev) | Sincronizar |
| `rapidfuzz` | `>=3.0.0` | MIT | Ya en uso | Sincronizar |
| `arq` | `>=0.25` | MIT | Fase 5 — Job Queue | — |
| `opencv-python-headless` | `>=4.8.0` | Apache 2.0 | Fase 7 — OpenCV | NO usar opencv-python |
| `pikepdf` | `>=8.0` | MPL-2.0 | Fase 8 — PDF Forensics | — |
| `pdfminer.six` | `>=20221105` | MIT | Fase 8 — Font analysis | — |
| `pyhanko` | `>=0.20` | MIT | Fase 8 — Signature validation | — |
| `benford-py` | `>=0.2` | MIT | Fase 8 — Benford Law | — |
| `satcfdi` | `>=1.0` | MIT | Fase 8 — SAT México | NO usar cfdiclient (GPL) |

**Dependencias a ELIMINAR:**
| Paquete | Motivo |
|---|---|
| `pingouin` | **GPL-3.0** — incompatible con SaaS comercial. Reemplazado con scipy/statsmodels. |
| `pymupdf` | **AGPL-3.0** — riesgo comercial muy alto. Reemplazar con pypdfium2 (MIT). |

**Nota Estratégica Stack Clean:** Se ha decidido **descartar** `img2table`, `jdeskew`, `Evidently AI` y otras librerías externas de nicho. Todo el parseo estructural recae en `Docling`, la estadística en `ydata-profiling` y la manipulación visual en `OpenCV`.

---

## Orden Sugerido de Ejecución (Gantt Simplificado)

```
Completada: [Fase 2]   Paso 13 — profiler.compare() en pipeline
Completada: [Fase 2]   Paso 14 — profile_timeseries()
Completada: [Fase 2]   Paso 15 — TS profiling en SuggestedQuestions
Completada: [Fase 2.5] D1 pingouin → scipy/statsmodels
Completada: [Fase 2.5] D2 sincronizar pyproject.toml
Completada: [Fase 2.5] D3 JWT secret key validation
Semana 1:   [Fase 3]   Paso 1 — ValidationRulesService
Semana 2:   [Fase 3]   Paso 2 — Data Drift con ydata-profiling
Semana 3:   [Fase 3]   Paso 3 — usage_events tracking
Semana 4-5: [Fase 4]   FAISS filtros + reranker
Semana 6:   [Fase 5]   docling-eval goldens
Semana 7:   [Fase 5]   ARQ + Redis job queue
Semana 8+:  [Fase 6]   PydanticAI Agent con 4 tools
Semana 17+: [Fase 7]   OpenCV pipeline
Semana 21+: [Fase 8]   FraudGuard
Semana 27+: [Fase 9]   OpenCV + FraudGuard avanzado
Final:      [Fase Final] Deploy y Producción
```

---

## Reglas de Implementación (No Negociables)

1. **El LLM nunca computa** — solo narra resultados precalculados por el pipeline
2. **Correr `python -m pytest tests/ -v` después de CADA paso** — todos deben seguir pasando
3. **Type hints obligatorios** en todas las funciones nuevas
4. **structlog para logging** — nunca print()
5. **Pydantic v2 BaseModel** para todos los schemas nuevos
6. **Import condicional** para dependencias pesadas (opencv, etc.) con flag de disponibilidad
7. **No refactorear código fuera del scope del paso** — cada paso tiene un archivo objetivo
8. **Si algo falla después de 2 intentos, parar y preguntar**
9. **No GPL** — verificar licencia antes de agregar cualquier dependencia nueva
10. **No meters CrewAI, LangGraph, LlamaIndex, LangChain** en ningún archivo nuevo
11. **El pipeline de ingesta es 100% determinístico** — los agentes solo hacen lecturas sobre datos ya calculados
12. **Tests con Hypothesis** para servicios de parsing y validación (no para tests de integración)
