# PRD Backend — Data-X
*Última actualización: 23 marzo 2026*

## Estado: PRODUCTION-READY ✅

## Stack técnico
Python 3.11+, FastAPI, Pydantic v2, Uvicorn
MongoDB (PyMongo Async), GridFS
Docling (DocumentConverter, HybridChunker, TableFormer)
Narwhals, Polars, polars-ds, Pandas, Pandera
statsmodels, scipy, Evidently AI (Apache-2.0), PyOD/ECOD (BSD-2)
ydata-profiling (MIT) — Profiling L2 determinístico
PydanticAI (reemplazó Instructor), LiteLLM Router
sentence-transformers, FAISS (caché en memoria thread-safe)
RapidFuzz (MIT), PyMuPDF, structlog
Hypothesis (testing property-based)
JWT, slowapi, uv, Svix

## Servicios (25)

| Servicio | Responsabilidad |
|---|---|
| ingest.py | Pipeline Docling-first, fallback pandas, multitabla |
| pipeline_orchestrator.py | Orquestación completa Bronze→Silver→Gold |
| docling_router.py | **NUEVO** — Routing embebido/serve por tamaño de archivo |
| docling_quality_gate.py | accept/warning/reject con confidence scores |
| schema_validator.py | Pandera — inferencia automática + lazy validation |
| finding_builder.py | Hallazgos determinísticos con Narwhals (consume ProfilingSummary) |
| stats_engine.py | Descriptive stats, correlations, outliers con Narwhals |
| profiler.py | **REFACTORIZADO** — ydata-profiling L2 con sampling + fallback básico |
| sensitive_data_guard.py | **NUEVO** — Detección de datos sensibles pre-profiling |
| context_builder.py | **NUEVO** — Budget de tokens, serialización Markdown para LLM |
| statistical_tests.py | Tests estadísticos (scipy, statsmodels) |
| power_analysis_service.py | Poder estadístico (statsmodels + scipy, sin GPL) |
| anomaly_service.py | Drift (Evidently) + outliers fila (PyOD/ECOD) |
| column_glossary.py | 4 tiers: exact → fuzzy → semantic → LLM fallback |
| llm_service.py | PydanticAI + LiteLLM Router — structured output |
| embedding_service.py | sentence-transformers + FAISS + caché por session_id |
| docling_chunking_service.py | HybridChunker con provenance real |
| chart_spec_generator.py | Especificaciones Recharts |
| suggested_questions_service.py | Preguntas sugeridas contextuales (+ trigger TS profiling) |
| webhook_service.py | Svix + fallback DIY (httpx + tenacity + HMAC) |
| tenant_db.py | TenantAwareCollection — aislamiento por tenant_id |
| api_key_auth.py | Auth por API Key con SHA-256 |
| file_metadata.py | **NUEVO** — Extracción de metadata rápida (tamaño, páginas) |
| normalization.py / serialization.py | Serialización de datos complejos |
| performance_optimizer.py | Optimizaciones de rendimiento |

## Endpoints

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | /api/health | — | Health check básico |
| GET | /api/health/detailed | — | Estado de todos los servicios |
| POST | /api/auth/register | — | Registro |
| POST | /api/auth/login | — | Login |
| GET | /api/auth/me | JWT | Perfil usuario |
| GET | /api/auth/me/usage | JWT | Consumo y límites del tier |
| POST | /api/sessions | JWT / API Key | Upload + pipeline (202 async) |
| GET | /api/sessions | JWT / API Key | Listar sesiones |
| GET | /api/sessions/{id}/status | JWT / API Key | Estado del pipeline |
| GET | /api/sessions/{id}/report | JWT / API Key | Reporte completo |
| GET | /api/sessions/{id}/pages/{n}/image | JWT | Imagen de página PDF |
| POST | /api/analyze | JWT / API Key | Query RAG |
| GET | /api/analyze/{id}/suggested-questions | JWT | Preguntas sugeridas |
| POST | /api/admin/keys/generate | JWT (admin) | Generar API Key B2B |
| POST | /api/admin/keys/revoke | JWT (admin) | Revocar API Key |
| GET | /api/admin/keys/{tenant_id} | JWT (admin) | Listar keys de tenant |
| POST | /api/webhooks/register | API Key | Registrar URL webhook |
| GET | /api/webhooks/logs | API Key | Historial de entregas |

## Reglas arquitectónicas (no negociables)
1. El LLM nunca computa — solo recibe JSON con resultados y los narra
2. Backend calcula, frontend renderiza
3. Findings como unidad de valor — estructura What/So What/Now What
4. Contratos Pydantic v2 son la fuente de verdad
5. Pandera siempre — ningún dato pasa al pipeline sin validación de schema
6. **NUEVO**: Datos sensibles nunca llegan al LLM — SensitiveDataGuard filtra antes del profiling
7. **NUEVO**: El contexto al LLM se serializa en Markdown con budget de tokens (≤6K tokens)

## Pipeline determinístico (L1→L5)

```
DoclingRouter (embebido/serve por tamaño)
  → Docling (DocumentConverter)
    → L1: Pandera (Quality Gate — pasa/no pasa)
      → L2: ydata-profiling → ProfilingSummary (Pydantic)
        → FindingBuilder (consume ProfilingSummary, no recomputa)
          → L3: scipy/statsmodels (tests de hipótesis, cuando se necesita)
            → L4: Evidently/PyOD (drift contra baseline, si existe)
              → ContextBuilder (Markdown con budget de tokens)
                → LLM (PydanticAI + LiteLLM — solo narra)
```

## Niveles de Determinismo (estado y próximos pasos)
- Nivel 1 (implementado): reglas fijas en FindingBuilder + Pandera + SciPy (el LLM no computa)
- Nivel 2 (en implementación): ydata‑profiling (minimal=True, sampling 10K) → `ProfilingSummary` (Pydantic)
  - Incluye: SensitiveDataGuard, ContextBuilder Markdown, comparación entre sesiones, TS profiling on-demand
- Nivel 3 (futuro): ValidationRulesService (DSL JSON/YAML → Pandera) binario pasa/no pasa
- Nivel 4 (futuro): Evidently con baselines por tenant y thresholds de negocio por columna
- Nivel 5 (futuro): Retrieval determinista (FAISS + filtros por metadatos + reranker) y, si escala, Qdrant

## DoclingRouter Híbrido
- Modos: embedded | serve | hybrid
- En hybrid: archivos chicos → embebido, archivos grandes → docling-serve
- Thresholds: >15 páginas O >10MB → serve
- Fallback automático a embedded si serve falla
- docling-serve como container separado en Railway
- Futuro: parámetro `accuracy=fast|high` para selección de motor OCR (Tesseract vs SuryaOCR)

## Queries Agénticas (evolución de /api/analyze)
- **Frontera clara**: El pipeline de ingesta es 100% determinístico. La capa agéntica solo opera en queries del usuario.
- PydanticAI Agent con tools para queries multi-paso:
  - `search_faiss(query)` → chunks relevantes
  - `get_profiling_summary(session_id)` → ProfilingSummary
  - `compare_tables(table_a, table_b)` → comparación
  - `get_findings(session_id, category)` → findings filtrados
- Structured output validado con Pydantic — el formato de respuesta es determinístico aunque el razonamiento sea agéntico
- No usar CrewAI, LangGraph, LlamaIndex ni n8n — PydanticAI ya está en el stack

## Evoluciones Docling futuras (activar por demanda)
- Docling PII nativo como complemento de SensitiveDataGuard (narrativa + columnas = dos capas)
- VLM Pipeline: gráficos embebidos → LiteLLM → VLM → descripción textual → FAISS
- XBRL support para balances financieros enterprise
- Information Extraction con templates Pydantic por vertical
- Plugin OCR por idioma (SuryaOCR para LATAM, autodetección con Tesseract)

## OpenCV: Capa Visual Complementaria a Docling (Fase 7)
- OpenCV NO reemplaza a Docling — actúa en 3 momentos: antes (preprocesamiento), después (validación), y en paralelo (enriquecimiento)
- Regla: todo lo que OpenCV produce son datos determinísticos con ProvenanceItem
- Servicios nuevos: `opencv_pipeline.py`, `opencv_enrichment_service.py`
- Patrón 1 (pre-Docling): quality gate (Laplaciano + BRISQUE), deskew (jdeskew), CLAHE, denoising, perspectiva
- Patrón 2 (post-Docling): validación geométrica de tablas (img2table), auditoría de confidence scores
- Patrón 3 (enriquecimiento): QR codes (pyzbar), firmas manuscritas (YOLO futuro), sellos (stamp2vec futuro)
- Conversión de coordenadas: pixel_x = bbox.l × (DPI/72), pixel_y = (page_height - bbox.t) × (DPI/72)
- Dependencias: opencv-python-headless (NO opencv-python), pyzbar, jdeskew, img2table, scikit-image
- Pipeline actualizado: upload → opencv quality gate → [preprocess si baja calidad] → DoclingRouter → Docling → opencv validate → opencv enrich → L1 Pandera → L2 profiling → ...

## FraudGuard: Detección de Fraude Documental (Fase 8)
- Subsistema paralelo al pipeline de análisis — produce FraudReport adjunto al AnalysisResult
- 4 Layers de detección, cada uno independiente y determinístico:
  - Layer 1 (PDF Forensics): pikepdf metadata + pdfminer.six fuentes + pyhanko firmas digitales
  - Layer 2 (Visual Forensics): ELA (OpenCV/PIL) + análisis de ruido + PhotoHolmes (opcional, métodos sin restricción comercial)
  - Layer 3 (Numérico/Semántico): benford_py (Chi², p-value) + validación matemática interna (IVA, balances) + Z-Score
  - Layer 4 (Cruzado/Fiscal): satcfdi SAT México + PyAfipWs AFIP Argentina + cross-document validation
- Schema: `FraudReport` (risk_score 0-1, risk_level, findings list) + `FraudFinding` (layer, type, severity, confidence, evidence, provenance)
- El LLM solo narra el FraudReport — nunca evalúa si algo "parece sospechoso"
- Disclaimer obligatorio: "indicadores probabilísticos, no determinaciones legales de fraude"
- Integración con provenance panel: zonas sospechosas en rojo/naranja sobre el PDF
- Dependencias: pikepdf, pdfminer.six, pyhanko, benford_py, satcfdi

## Pendiente post-deploy
### Plan de implementación (2026‑03‑23)
- Compliance y límites
  - Sustituir `pingouin` por SciPy/Statsmodels en producción (mismo contrato)
  - Due diligence/licencia PyMuPDF (AGPL upstream)
  - MAX_DOCLING_PAGES y política de muestreo para PDFs grandes
  - Rate limit distribuido (slowapi + store compartido o fastapi‑limiter)
- Observabilidad y performance
  - OpenTelemetry: FastAPI, httpx, PyMongo y fases Docling/EDA/Embeddings; exporter OTLP
  - structlog con `trace_id`/`span_id`
  - Pre‑parse con docling‑parse y preview < 2s para PDFs ≤ 150 páginas
  - EDA crítica con Narwhals→Polars (lazy, pushdown, streaming)
- Determinismo L2–L5
  - L2: ydata‑profiling (preset mínimo, muestreo) → `ProfilingSummary` (Pydantic)
  - L3: `ValidationRulesService` (JSON/YAML → Pandera) versionado por tenant/dataset
  - L4: Evidently (PSI/KS/Wasserstein) con thresholds; persistir diffs/metrics
  - L5: FAISS + filtros (tabla_id, sección, página) + reranker (cross‑encoder) y registro de scores/decisiones
- Calidad y operación
  - `usage_events`: tiempos por fase, páginas, tamaño DF, hits/miss FAISS, tokens/costo LLM; `GET /api/usage`
  - `docling‑eval/metrics` en CI con 50–100 goldens; bloquear degradaciones > 0.5 pp
  - PoC cola de trabajos (ARQ/Celery): estados, reintentos/backoff, cancelación, timeline/outbox

### KPIs objetivo
- p95 TTI preview < 2 s; −30–50% wall‑time EDA; −40% p95 memoria en transformaciones
- ≤ 5% alertas de drift revertidas; +10–15% precisión@k con reranker; p95 RAG ≤ 120 ms
- 0 regresiones Docling (CI bloqueando); rate limit coherente en ≥ 2 réplicas
- **NUEVO**: Profiling L2 < 3s para tablas Docling típicas; ≤ 6K tokens de contexto al LLM
- **NUEVO**: 0 data leaks de columnas sensibles en ProfilingSummary
