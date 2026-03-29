# Informe Completo — Data-X: Análisis Estratégico, Funcional y Técnico

> Fecha: 2026-03-28
> Modelo: Claude Sonnet 4.6
> Alcance: Backend, Frontend, Seguridad, Infraestructura, Estrategia de Producto

---

## 1. Visión General del Proyecto

Data-X es una plataforma SaaS de análisis documental inteligente que procesa archivos (CSV, PDF, XLSX) para extraer hallazgos de calidad de datos, perfiles estadísticos, detección de fraude y respuestas conversacionales mediante un agente RAG basado en LLM.

**Diferencial clave:** A diferencia de chatbots genéricos sobre documentos, Data-X provee **trazabilidad completa** (bounding boxes, número de página, sección) de cada hallazgo al documento original, combinando análisis determinístico (reglas, estadística) con análisis generativo (LLM).

---

## 2. Arquitectura

### 2.1 Pipeline Medallion (Bronze → Silver → Gold)

| Capa | Responsabilidad | Tecnología |
|------|----------------|------------|
| **Bronze** | Ingesta raw: extracción de texto, tablas, imágenes; quality gate | Docling + HybridChunker + OpenCV |
| **Silver** | Profiling estadístico + 9 detectores de findings + embeddings FAISS | pandas + sentence-transformers + FAISS |
| **Gold** | Enriquecimiento LLM, generación de narrativa, contexto semántico | LiteLLM + PydanticAI |

### 2.2 Multi-Tier Strategy Pattern

```
BaseRetrievalService (ABC)
├── EmbeddingService (Lite)     → FAISS en memoria, sin deps externas
└── OpenSearchService (Enterprise) → Cluster distribuido, producción
```

El agente PydanticAI consume únicamente el contrato abstracto, sin conocer el backend de recuperación. Esto permite escalar de Lite a Enterprise sin cambiar el agente.

### 2.3 Tecnologías Principales

- **Backend:** FastAPI, Python 3.13, PyMongo (MongoDB), ARQ (Redis jobs)
- **AI/LLM:** PydanticAI Agent, LiteLLM (router), OpenAI-compatible API
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`), FAISS
- **Documentos:** Docling (PDF/XLSX/CSV parsing), OpenCV (quality gates)
- **Validación:** Pandera v2 (DataFrame validation con reglas declarativas)
- **Observabilidad:** structlog + OpenTelemetry (OTLP trace export)
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind v4
- **Infraestructura:** Docker Compose, GitHub Actions CI

---

## 3. Endpoints de la API

### Autenticación (`/api/auth`)

| Método | Endpoint | Descripción | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/register` | Registro de usuario, devuelve JWT | 5/hora |
| POST | `/login` | Autenticación, devuelve JWT | 10/minuto |
| GET | `/me` | Perfil del usuario autenticado | — |

### Sesiones (`/api/sessions`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/` | Crea sesión + ejecuta pipeline completo (Bronze→Silver→Gold) |
| GET | `/` | Lista sesiones del usuario autenticado |
| GET | `/{session_id}` | Detalle de sesión con todos los findings |
| POST | `/{session_id}/chat` | Envía pregunta al agente RAG |
| GET | `/{session_id}/chat/history` | Historial de mensajes |
| GET | `/{session_id}/export` | Exporta resultados (endpoint incompleto) |

### Validación (`/api/validation`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/{session_id}/rules` | Aplica reglas de negocio declarativas al dataset |

---

## 4. Servicios e Inventario Funcional

### 4.1 Ingesta (Bronze Layer)
- **IngestService:** Orquesta Docling para extraer texto, tablas e imágenes
- **DocumentProcessingService:** Preprocesa documentos antes de la extracción
- **DistributedIngestionService:** Wrapper enterprise con latencia artificial (mock)

### 4.2 Análisis (Silver Layer)
- **ProfilerService:** Estadísticas descriptivas (media, mediana, percentiles, nulos, skewness)
- **FindingDetectorService:** 9 detectores: `data_gap`, `quality_issue`, `pattern`, `outlier`, `compliance`, `statistical_test`, `correlation`, `drift`, `fraud`
- **StatisticalTestsService:** Tests de hipótesis con pingouin (⚠️ GPL-3.0)
- **EmbeddingService:** Indexación FAISS + búsqueda semántica, hybrid sources
- **DocumentChunkingService:** Chunking semántico de narrativa y tablas
- **ValidationRulesService:** Validación declarativa con Pandera (Pydantic → pa.Check)

### 4.3 IA / LLM (Gold Layer)
- **LLMService:** Genera narrativa explicativa enriquecida por LiteLLM
- **ContextBuilderService:** Construye el prompt de contexto para el LLM
- **AnalysisAgent (PydanticAI):** Agente RAG con 6 tools:
  - `search_documents`: Búsqueda semántica en chunks del documento
  - `get_dataset_profile`: Resumen estadístico global
  - `get_findings`: Alertas/hallazgos por categoría
  - `get_column_details`: Perfil completo de una columna específica
  - `get_data_drift_report`: Métricas de data drift
  - `get_fraud_report`: Reporte FraudGuard

### 4.4 FraudGuard (4 capas)
- **Capa 1 — PDF Forensics:** Análisis de metadatos, historial de revisiones, fuentes tipográficas, fecha de modificación vs creación
- **Capa 2 — ELA (Error Level Analysis):** Detección visual de manipulaciones de imagen por análisis de niveles de compresión JPEG
- **Capa 3 — Ley de Benford:** Análisis estadístico de distribución de primeros dígitos para detectar datos numéricos fabricados
- **Capa 4 — LATAM Fiscal:** Validaciones específicas para RUC (Ecuador/Perú), CUIT/CUIL (Argentina), RFC (México), CNPJ (Brasil)

### 4.5 Autenticación y Seguridad
- **AuthService:** Registro/login con bcrypt (hashing) y JWT (python-jose, HS256)
- **SensitiveDataGuardService:** Detección y enmascaramiento de PII (emails, teléfonos, documentos de identidad)
- **Rate Limiting:** slowapi con MemoryStorage, por IP

### 4.6 Observabilidad
- structlog para logs estructurados JSON
- OpenTelemetry instrumentation: PyMongo, httpx, FastAPI
- OTLP trace export configurable (Jaeger, Grafana Tempo, etc.)

---

## 5. Base de Datos (MongoDB)

| Colección | Contenido |
|-----------|-----------|
| `users` | Credenciales, nombre, fecha de registro |
| `sessions` | Metadata de sesión, estado del pipeline |
| `bronze_documents` | Documento raw procesado por Docling |
| `silver_profiles` | Perfil estadístico + findings generados |
| `gold_narratives` | Narrativa LLM + contexto enriquecido |
| `embeddings_cache` | Índice FAISS serializado + findings_map |
| `hybrid_embeddings_cache` | Índice híbrido (findings + chunks) |
| `document_chunks` | Chunks semánticos del documento |

---

## 6. Frontend

### 6.1 Stack
- Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4
- shadcn/ui + Radix UI para componentes accesibles
- Recharts para visualizaciones

### 6.2 Workspace (7 pestañas)
1. **Overview** — Resumen ejecutivo + métricas clave del documento
2. **Data Profile** — Estadísticas por columna, distribuciones
3. **Findings** — Alertas detectadas con severidad y categoría
4. **Chat** — Interfaz conversacional con el agente RAG
5. **Validation** — Aplicación de reglas de negocio personalizadas
6. **FraudGuard** — ⚠️ Funcionalidad backend implementada, **UI no expuesta**
7. **History** — Sesiones anteriores del usuario

### 6.3 Estado actual
- JWT almacenado en `localStorage` (riesgo XSS)
- Sin gestión global de estado (Context API o Zustand)
- Datos hardcodeados en algunos componentes
- Sin lazy loading ni code splitting entre tabs
- FraudGuard y comparación de sesiones existen en el backend pero son invisibles en el frontend

---

## 7. Infraestructura y DevOps

### 7.1 Docker Compose
- Servicios: `backend` (FastAPI), `mongo` (MongoDB 7)
- ⚠️ **Redis ausente** del compose — ARQ job queue no puede funcionar
- ⚠️ **Corre como root** en el contenedor de backend

### 7.2 CI/CD (GitHub Actions)
- Pipeline: `setup-python` → `pip install` → `pytest`
- Sin caché de dependencias (lento)
- Sin linting (ruff/black) en CI
- Sin build/deploy de Docker en CI

### 7.3 Configuración
- `.env` con variables para MongoDB, Redis, JWT secret, LiteLLM
- `pyproject.toml` desincronizado con `requirements.txt` (dos fuentes de verdad)

---

## 8. Problemas Críticos Identificados

### 🔴 Seguridad

| # | Problema | Impacto | Solución |
|---|----------|---------|----------|
| 1 | **[RESUELTO] JWT_SECRET default vacío** | Crítico | Validado exitosamente en `lifespan` de `main.py`. Si falta, el servidor aborta el inicio. |
| 2 | **Sin revocación de tokens** — logout no invalida JWT | Alto | Blacklist en Redis o short-lived tokens + refresh |
| 3 | **JWT en localStorage** — vulnerable a XSS | Alto | Mover a `httpOnly` cookies |
| 4 | **Docker corre como root** — escalada de privilegios | Medio | Agregar `USER nobody` al Dockerfile |
| 5 | **[RESUELTO] Sin validación de magic bytes** | Medio | Validación binaria (`%PDF`, `PK`) implementada en `POST /sessions`. |
| 6 | **Sin CSP headers** en el frontend | Medio | Configurar Content-Security-Policy en `next.config.js` |

### 🔴 Confiabilidad

| # | Problema | Impacto | Solución |
|---|----------|---------|----------|
| 7 | **[RESUELTO] Pipeline síncrono en `POST /sessions`** | Crítico | Delegado a `JobQueueService` (ARQ). Ahora retorna HTTP 202 inmediato. |
| 8 | **[RESUELTO] Redis ausente en Docker Compose** | Crítico | `redis:7-alpine` agregado a los archivos Compose. |
| 9 | **[RESUELTO] Sin endpoint DELETE para sesiones** | Medio | Implementado borrado en cascada en MongoDB y caché FAISS (GDPR Compliant). |
| 10 | **Sin manejo de rollback en pipeline** — datos parciales en MongoDB si falla una capa | Medio | Implementar transacción o limpieza en caso de error |

### 🟡 Legal / Licenciamiento

| # | Problema | Impacto | Solución |
|---|----------|---------|----------|
| 11 | **[RESUELTO] pingouin usa GPL-3.0** | Alto | Eliminado y reemplazado 100% por `scipy.stats` y `statsmodels`. |

---

## 9. Mejoras Funcionales Prioritarias

### Sprint Inmediato (Crítico) - [COMPLETADO]
1. ~~Validar JWT_SECRET al startup~~ (Hecho)
2. ~~Reemplazar pingouin → scipy.stats~~ (Hecho)
3. ~~Agregar Redis a docker-compose + integrar ARQ~~ (Hecho)

### Sprint 1 (Alto Valor Backend) - [COMPLETADO]
4. ~~Polling de estado de sesión~~ (Implementado `GET /sessions/{id}/status`)
5. ~~DELETE /sessions/{id}~~ (Implementado)
6. ~~Export funcional CSV~~ (Implementado)
7. ~~Comparación de sesiones / Drift~~ (Implementado `POST /sessions/{id}/compare`)

### Sprint 1.5 (Alto Valor Frontend) - [PENDIENTE]
8. **Exponer FraudGuard en el frontend** — UI para las 4 capas forenses.
9. **Exponer UI de Data Drift** — Interfaz para la comparación de sesiones.

### Sprint 2 (diferenciación)
10. **Onboarding interactivo** — wizard de primera sesión con dataset de ejemplo
11. **Panel de costos LLM** — Mostrando los datos de telemetría devueltos por `GET /api/auth/me/usage`.
11. **Gestión de plantillas de reglas** — guardar/reutilizar conjuntos de reglas de negocio
12. **Dashboard de uso** — métricas por usuario: sesiones, tokens, tipos de documento

### Sprint 3 (enterprise)
13. **OpenSearch tier** — implementar `OpenSearchRetrievalService` (el contrato abstracto ya existe)
14. **Webhooks** — notificación a sistemas externos cuando una sesión completa el pipeline
15. **SSO/SAML** — para clientes enterprise con directorios corporativos
16. **Multi-tenancy** — aislamiento de datos por organización

---

## 10. Mejoras de Endpoints

| Endpoint actual | Problema | Mejora propuesta |
|-----------------|----------|-----------------|
| `POST /sessions` | **[RESUELTO]** | Retorna HTTP 202 asíncrono y encola en ARQ. |
| `GET /sessions/{id}/status` | **[RESUELTO]** | Endpoint ligero de polling implementado. |
| `DELETE /sessions/{id}` | **[RESUELTO]** | Implementado con borrado completo en DB. |
| `GET /sessions/{id}/export` | **[RESUELTO]** | Devuelve CSV vía `StreamingResponse`. |
| `POST /sessions/{id}/compare`| **[RESUELTO]** | Genera diferencias estadísticas (drift) entre 2 sesiones. |
| `GET /users/me/usage` | **[RESUELTO]** | Suma tokens, dólares y ms mediante MongoDB Aggregation. |
| `POST /sessions/{id}/fraud` | Pendiente | Trigger explícito de FraudGuard si es necesario invocarlo suelto. |

---

## 11. Mejoras de Frontend

| Área | Problema actual | Mejora |
|------|----------------|--------|
| **Estado global** | Sin Context/Zustand, prop drilling | Implementar Zustand store para sesión activa |
| **Auth storage** | JWT en localStorage | Mover a `httpOnly` cookie via BFF o API route |
| **FraudGuard tab** | Vacía/no conectada | Conectar con `GET /sessions/{id}/fraud` |
| **Carga de archivos** | Sin progreso visual | Barra de progreso + polling de estado del job |
| **Performance** | Sin lazy loading | `React.lazy()` por tab del workspace |
| **Errores** | Sin Error Boundary global | Agregar `ErrorBoundary` en la raíz del workspace |
| **Accesibilidad** | Sin verificar | Auditoría con axe-core + aria-labels en charts |
| **Mobile** | No verificado | Responsive breakpoints para workspace en tablet |

---

## 12. Estrategia de Producto y Monetización

### 12.1 Modelo de Pricing Sugerido (3 tiers)

| Tier | Precio | Límites | Retrieval |
|------|--------|---------|-----------|
| **Free** | $0/mes | 5 sesiones/mes, 10MB/doc, sin FraudGuard | FAISS Lite |
| **Pro** | $49/mes | 50 sesiones/mes, 50MB/doc, FraudGuard incluido | FAISS Lite |
| **Enterprise** | $299/mes | Ilimitado, 200MB/doc, FraudGuard + LATAM fiscal | OpenSearch |

### 12.2 FraudGuard como Producto Standalone
El módulo FraudGuard (4 capas: PDF forensics + ELA + Benford + LATAM fiscal) es una propuesta de valor diferencial en el mercado LATAM. Puede monetizarse:
- **API de verificación**: `POST /api/fraud/verify` con precio por documento
- **Integración con contadores/auditores**: flujo simplificado sin pipeline completo
- **White-label**: licenciar el módulo a plataformas de facturas electrónicas

### 12.3 Trazabilidad como Diferenciador
La proveniencia (bounding boxes + número de página) que Data-X genera es única frente a chatbots genéricos sobre PDF. Comunicar esto en el producto:
- Mostrar siempre el "fragmento de origen" en cada respuesta del chat
- Badge visual "Verificado en pág. X" en cada hallazgo
- Exportar informe con evidencia documental citada

### 12.4 Verticales con Mayor ROI
1. **Auditoría Contable LATAM** — validación CUIT/RUC/RFC + Benford + anomalías numéricas
2. **Compliance Financiero** — detección de PII, validación de formatos regulatorios
3. **Due Diligence** — análisis masivo de documentos con trazabilidad para M&A
4. **Recursos Humanos** — validación de legajos, detección de documentos adulterados

---

## 13. Observabilidad y Calidad

### 13.1 Estado actual
- structlog + OTLP configurado pero no hay dashboards definidos
- Tests: 64 pasando, 1 skipped (eval de Docling), 0 fallando
- Sin cobertura de código medida (no hay `pytest-cov` en CI)
- Gaps de cobertura: `llm_service.py`, `context_builder.py`, `sensitive_data_guard.py`, rutas de error del pipeline

### 13.2 Mejoras de observabilidad
- Agregar `pytest-cov` a CI y establecer umbral mínimo (80%)
- Definir alertas en Grafana/Jaeger para: latencia del pipeline > 30s, error rate > 5%, tokens LLM/sesión
- Dashboard de ARQ: jobs encolados, fallidos, tiempo de procesamiento por capa
- Logs de auditoría para acciones sensibles (registro, acceso a sesión de otro usuario)

---

## 14. Deuda Técnica

| Item | Severidad | Descripción |
|------|-----------|-------------|
| `pyproject.toml` vs `requirements.txt` | **[RESUELTO]** | Se consolidó el uso exclusivo de `pyproject.toml` y `uv`. |
| `distributed_strategy.py` mock | **[RESUELTO]** | Se eliminó el `asyncio.sleep(0.5)` artificial. |
| Sin caché de respuestas LLM | **[RESUELTO]** | Caché distribuido configurado en Redis para LiteLLM. |
| `base.py` en `/docs` | **[RESUELTO]** | Archivos huérfanos y duplicados eliminados. |
| Sin paginación en `GET /sessions` | **[RESUELTO]** | Endpoint retorna `PaginatedSessionList` con límite, offset y total. |
| `search_hybrid_sources` no implementado en `BaseRetrievalService` | **[RESUELTO]** | Firmas asíncronas agregadas al contrato base y respetadas en los tests. |

---

## 15. Resumen de Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| JWT secret vacío en producción | **RESUELTO** | Crítico | Validado en startup (`main.py`). Falla seguro si no existe. |
| Timeout en upload de PDF grande | **RESUELTO** | Alto | Pipeline migrado 100% a ARQ (Background jobs) + Polling endpoint. |
| GPL-3.0 (pingouin) en producto comercial | **RESUELTO** | Alto | Removido. Sustituido por `scipy.stats` puro. |
| Redis no disponible bloquea jobs async | **RESUELTO** | Alto | Contenedor agregado a los `docker-compose.yml`. |
| XSS roba JWT de localStorage | Media | Alto | **[PENDIENTE FRONTEND]** Migrar a httpOnly cookie. |
| OpenSearch Enterprise tier sin implementar | **RESUELTO** | Medio | Implementación asíncrona real inyectada con Patrón Strategy. |

---

*Informe generado el 2026-03-28. Para detalles de código, consultar la base de código o el historial de conversación en `.claude/projects/`.*
