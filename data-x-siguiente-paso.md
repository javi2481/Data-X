# Data-X — Siguiente paso: Junie (críticos) → Emergent → v0

---

## PARTE 1: Junie completa los servicios críticos

Estos prompts completan lo mínimo para que el flujo end-to-end funcione.
Después Emergent enriquece todo.

---

### PROMPT J1 — Servicio de ingestión + normalización básica

```
## Tarea
Crear el servicio de ingestión de archivos y normalización básica.

## Archivos a crear

### backend/app/services/ingest.py
Clase IngestService con método async:
- ingest_file(file_bytes: bytes, filename: str, content_type: str) -> dict

Debe hacer:
- Si el archivo es CSV (por content_type o extensión), leerlo con pandas
- Detectar schema: columnas, tipos (dtypes como strings), cantidad de filas, nulls por columna
- Devolver dict con:
  {
    "dataframe": df,  (el DataFrame en memoria, para uso interno)
    "schema_info": {
      "columns": ["col1", "col2"],
      "dtypes": {"col1": "int64", "col2": "object"},
      "row_count": 100,
      "null_counts": {"col1": 0, "col2": 3}
    },
    "source_metadata": {
      "filename": "ventas.csv",
      "content_type": "text/csv",
      "size_bytes": 1234
    }
  }
- Si el formato no es CSV, lanzar ValueError("Formato no soportado. Solo CSV por ahora.")
- Si el CSV está mal formado, lanzar ValueError con mensaje descriptivo
- Agregar comentario TODO donde Docling entraría después

### backend/app/services/normalization.py
Clase NormalizationService con método:
- normalize(df: DataFrame) -> DataFrame

Debe hacer:
- Limpiar nombres de columnas: lowercase, reemplazar espacios por _, quitar caracteres especiales
- Intentar convertir columnas que parezcan numéricas (coerce errors)
- Eliminar filas completamente vacías
- Devolver DataFrame limpio

## NO hacer
- No crear routes todavía (eso viene después)
- No tocar schemas
- No tocar el frontend
- No agregar Docling todavía
- No agregar tests
- No instalar dependencias nuevas (pandas ya está en requirements.txt)
```

---

### PROMPT J2 — Validación básica + artifact builder mínimo

```
## Tarea
Crear validación básica y un artifact builder mínimo.

## Archivos a crear

### backend/app/services/validation.py
Clase ValidationService con método:
- validate(df: DataFrame, schema_info: dict) -> list[dict]

Debe hacer:
- Verificar que el DataFrame tiene al menos 1 columna y 1 fila
- Detectar columnas con más del 50% de nulls → warning
- Detectar si hay 0 columnas numéricas → info "No se detectaron columnas numéricas"
- Devolver lista de alertas: [{"level": "warning"|"error"|"info", "message": "...", "field": "col_name"|None}]
- Si el DataFrame es vacío, devolver [{"level": "error", "message": "El dataset está vacío", "field": None}]

### backend/app/services/artifact_builder.py
Clase ArtifactBuilder con métodos:
- build_table_artifact(df: DataFrame, title: str, max_rows: int = 50) -> dict
  Devuelve: {"artifact_type": "table", "title": title, "data": {"columns": [...], "rows": [...]}}
  Los rows son dicts. Limitar a max_rows.

- build_metric_set(schema_info: dict) -> dict
  Devuelve: {"artifact_type": "metric_set", "title": "Resumen del dataset", "data": {"metrics": [
    {"label": "Filas", "value": row_count},
    {"label": "Columnas", "value": len(columns)},
    {"label": "Columnas numéricas", "value": count_numeric},
    {"label": "Valores nulos totales", "value": total_nulls}
  ]}}

- build_alerts(alerts: list[dict]) -> dict
  Devuelve: {"artifact_type": "alerts", "title": "Alertas", "data": {"items": alerts}}

- build_summary(text: str) -> dict
  Devuelve: {"artifact_type": "summary", "title": "Resumen", "data": {"text": text}}

## NO hacer
- No crear profiler completo (Emergent lo hará)
- No crear stats engine (Emergent lo hará)
- No crear charts (Emergent lo hará)
- No tocar el frontend
- No crear routes todavía
```

---

### PROMPT J3 — Routes funcionales + main.py conectado

```
## Tarea
Crear las routes de la API y conectar todo en main.py para que el flujo funcione end-to-end.

## Archivos a crear/modificar

### backend/app/api/routes/health.py
Router FastAPI con:
- GET /health → {"status": "ok"}

### backend/app/api/routes/sessions.py
Router FastAPI con:
- POST /sessions
  - Recibe archivo via UploadFile de FastAPI
  - Lee los bytes del archivo
  - Llama a IngestService().ingest_file(bytes, filename, content_type)
  - Llama a NormalizationService().normalize(df)
  - Llama a ValidationService().validate(df, schema_info)
  - Genera session_id con uuid4 (prefijo "sess_")
  - Guarda la sesión en memoria (usar un dict global por ahora, 
    como SESSION_STORE = {}). Emergent migrará esto a MongoDB después.
  - Devuelve SessionResponse con status="created", schema_info, profile=None
  - Si hay error, devuelve ErrorResponse con error_code apropiado

### backend/app/api/routes/analyze.py
Router FastAPI con:
- POST /analyze
  - Recibe AnalyzeRequest (session_id, query) como JSON body
  - Busca la sesión en SESSION_STORE
  - Si no existe, devuelve error SESSION_NOT_FOUND
  - Recupera el DataFrame de la sesión
  - Llama a ArtifactBuilder para generar:
    - table artifact (preview del dataset)
    - metric_set artifact (resumen de métricas)
    - alerts artifact (si hay alertas de validación)
    - summary artifact (texto básico describiendo el dataset, 
      por ahora generado con lógica simple sin LLM)
  - Devuelve AnalyzeResponse con la lista de artifacts
  
  Para el summary sin LLM, generar algo como:
  "Dataset '{filename}' con {rows} filas y {cols} columnas. 
   Columnas: {col1}, {col2}, ... Tipos detectados: {n} numéricas, {m} texto."

### backend/app/main.py (MODIFICAR el existente)
- Importar y registrar los 3 routers (health, sessions, analyze)
- CORS configurado desde settings
- Manejo de errores global: si un endpoint lanza ValueError,
  devolver ErrorResponse con status 400
- NO agregar startup/shutdown de MongoDB todavía (usa SESSION_STORE en memoria)

## Almacenamiento temporal
Usar un dict global en sessions.py:

SESSION_STORE: dict[str, dict] = {}

Cada sesión guarda:
{
  "session_id": "sess_...",
  "dataframe": df,
  "schema_info": {...},
  "source_metadata": {...},
  "alerts": [...],
  "created_at": datetime
}

Emergent migrará esto a MongoDB después. Dejá un comentario:
# TODO: Emergent migrará SESSION_STORE a MongoDB

## NO hacer
- No agregar MongoDB (Emergent lo hará)
- No agregar LLM (Emergent lo hará)
- No agregar auth
- No agregar WebSockets
- No tocar el frontend
- No crear tests
- No instalar dependencias nuevas
```

---

### PROMPT J4 — Verificación del flujo end-to-end

```
## Tarea
Verificar que el backend funciona end-to-end.

## Qué hacer

1. Instalar dependencias (si no están instaladas):
   cd backend
   pip install -r requirements.txt

2. Verificar imports:
   python -c "from app.main import app; print('OK')"

3. Arrancar el servidor:
   uvicorn app.main:app --reload --port 8000

4. Probar health:
   curl http://localhost:8000/health
   → Debe devolver {"status":"ok"}

5. Probar crear sesión:
   curl -X POST http://localhost:8000/sessions \
     -F "file=@tests/fixtures/ventas.csv"
   → Debe devolver SessionResponse con session_id y schema_info

6. Probar analyze (reemplazar SESSION_ID con el valor real):
   curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"session_id":"SESSION_ID","query":"Analiza los datos"}'
   → Debe devolver AnalyzeResponse con artifacts (table, metric_set, alerts, summary)

## Si algo falla
Corregí el error específico. Máximo 3 intentos por error.
Si no se resuelve, PARA y dame opciones.

## NO hacer
- No agregar features nuevas
- No refactorizar lo que ya funciona
- No tocar el frontend
```

---

### PROMPT J5 — Commit del backend funcional

```
## Tarea
Hacer commit de los servicios y routes del backend.

## Qué hacer
git add .
git commit -m "[backend] servicios críticos + routes funcionales — flujo end-to-end operativo"
git push origin main

## NO hacer
- No modificar nada antes del commit
```

---

## PARTE 2: Emergent mejora el backend

Una vez que Junie terminó y el repo está en GitHub, conectá Emergent.

---

### Primer prompt para Emergent

```
## Contexto
Este es el monorepo de Data-X. El backend ya tiene una versión funcional mínima
construida con Junie/IntelliJ. Tu rol es mejorarlo, completarlo y evolucionarlo.

## Estado actual del backend
Lo que YA existe y funciona:
- Estructura de carpetas completa en backend/
- Config con Pydantic Settings (backend/app/core/config.py)
- Logging con structlog (backend/app/core/logging.py)
- Schemas Pydantic: SessionResponse, AnalyzeRequest, AnalyzeResponse, ErrorResponse, ArtifactResult
- IngestService: lee CSV con pandas, detecta schema
- NormalizationService: limpia columnas, convierte tipos, elimina filas vacías
- ValidationService: detecta nulls y problemas básicos
- ArtifactBuilder: genera table, metric_set, alerts y summary artifacts
- Routes: GET /health, POST /sessions, POST /analyze
- main.py con CORS y routers registrados
- Almacenamiento temporal en memoria (SESSION_STORE dict)
- Flujo end-to-end funcional: upload CSV → sesión → analyze → artifacts

Lo que FALTA y es tu responsabilidad:
- Persistencia MongoDB (reemplazar SESSION_STORE en memoria)
- ProfilerService completo (descripción detallada de cada columna)
- StatsEngine (descriptive stats, correlaciones, outliers)
- ProvenanceService (trazabilidad de datos)
- LLMService con LiteLLM (interpretación y summary inteligente)
- ChartConfig artifacts (gráficos)
- Observabilidad con OpenTelemetry
- Docling como pipeline de ingesta (reemplazar pandas directo)
- Manejo de errores más robusto
- Mejoras generales de calidad y robustez

## Documentación
Leé estos archivos en el repo:
- docs/ (toda la documentación disponible)
- backend/ (todo el código existente)
- frontend/src/types/contracts.ts (para entender qué consume el frontend)

## Scope
- Escribir solo en: backend/
- Puede leer: frontend/, docs/
- No tocar: frontend/, docs/

## Tarea
Revisá todo el backend existente y producí un informe con:
1. Estado actual: qué existe, qué funciona, qué calidad tiene
2. Gaps: qué falta según el PRD backend
3. Mejoras prioritarias: qué conviene hacer primero
4. Plan de fases: cómo organizar el trabajo

NO implementes nada todavía. Solo el informe y el plan.

## NO hacer
- No tocar frontend/
- No tocar docs/
- No implementar código todavía
- NO testing agent

## Si falla 2 veces
PARA y dame opciones
```

---

### Prompts sugeridos para Emergent (después del informe)

Una vez que Emergent te da el plan y vos aprobás, estos son los bloques típicos de trabajo:

**Bloque 1 — MongoDB:**
```
## Tarea
Migrar el almacenamiento de sesiones de SESSION_STORE (dict en memoria) a MongoDB.

## Scope
- Escribir solo en: backend/
- No tocar: frontend/, docs/

## Archivos a tocar
- backend/app/db/client.py (crear MongoClient con Motor async)
- backend/app/repositories/mongo.py (crear SessionRepository)
- backend/app/api/routes/sessions.py (reemplazar SESSION_STORE por repository)
- backend/app/api/routes/analyze.py (leer sesión desde MongoDB)
- backend/app/main.py (agregar startup/shutdown de MongoDB)

## Debe hacer
- Conexión async a MongoDB usando Motor
- CRUD de sesiones en colección "sessions"
- El DataFrame NO se guarda en MongoDB (es demasiado grande).
  Guardar schema_info, source_metadata, alerts, status, timestamps.
  El DataFrame se reconstruye del archivo original si es necesario,
  o se guarda serializado en una colección separada.

## NO hacer
- No tocar el frontend
- No refactorizar servicios que ya funcionan
- NO testing agent

## Verificación
curl -X POST http://localhost:8000/sessions -F "file=@tests/fixtures/ventas.csv"
(debe funcionar igual que antes pero persistiendo en MongoDB)

## Si falla 2 veces
PARA y dame opciones
```

**Bloque 2 — Profiler + Stats:**
```
## Tarea
Crear ProfilerService y StatsEngine completos.

## Scope
- Escribir solo en: backend/

## Archivos
- backend/app/services/profiler.py
- backend/app/services/stats_engine.py

## ProfilerService.profile(df) debe generar por columna:
- name, dtype, count, null_count, null_percent, unique_count, cardinality
- Para numéricas: min, max, mean, median, std
- Para strings: min_length, max_length, top_values (top 5)

## StatsEngine debe tener:
- descriptive_stats(df) → dict con describe() serializable
- correlation_matrix(df) → dict con correlaciones numéricas
- detect_outliers(df, column) → dict con count, bounds (IQR)

## NO hacer
- No agregar ML ni LLM
- No tocar routes (la integración en routes viene después)
- NO testing agent

## Verificación
python -c "from app.services.profiler import ProfilerService; print('OK')"
python -c "from app.services.stats_engine import StatsEngine; print('OK')"

## Si falla 2 veces
PARA y dame opciones
```

**Bloque 3 — LLM + Provenance + Charts:**
(Seguir el mismo formato, un servicio por prompt)

---

## PARTE 3: v0 mejora el frontend

Conectá v0 al repo después de que Emergent tenga al menos MongoDB y los endpoints estables.

---

### Primer prompt para v0

```
## Contexto
- Proyecto: Data-X, plataforma de análisis de datos
- Stack: Next.js 14 + TypeScript + shadcn/ui + Recharts + Tailwind
- Backend externo: FastAPI en NEXT_PUBLIC_API_BASE_URL
- El frontend ya tiene una versión funcional mínima construida con Junie/IntelliJ

## Estado actual del frontend
Lo que YA existe:
- Landing page profesional con CTA
- Workspace con FileUploader (subida de archivos)
- Visualización de resultados (gráficos y tablas)
- Componentes de UI con shadcn
- Contratos TypeScript sincronizados con backend
- Cliente API base en src/lib/api.ts
- Navegación básica

Lo que probablemente FALTA o NECESITA MEJORA:
- Diseño y UX más pulido
- Estados loading/error/empty más consistentes
- ArtifactRenderer completo (switch por artifact_type)
- MetricCard, ProvenancePanel
- Workspace más robusto (manejo de errores de API, retry)
- Historial de sesiones
- Responsive design
- Accesibilidad
- Mejor tipado en consumo de API

## Scope
- Escribir solo en: frontend/
- Puede leer: backend/, docs/
- No tocar: backend/, docs/

## Documentación
Leé estos archivos:
- docs/ (especialmente prd-front-v0.md si existe)
- frontend/ (todo el código existente)
- backend/app/schemas/ (para verificar que contracts.ts está sincronizado)
- backend/app/api/routes/ (para entender qué endpoints existen)

## Tarea
Revisá todo el frontend existente y producí un informe con:
1. Estado actual: qué existe, qué calidad tiene, qué se ve bien
2. Gaps: qué falta según el PRD frontend
3. Mejoras prioritarias: qué conviene hacer primero
4. Plan de fases: cómo organizar el trabajo

NO implementes nada todavía. Solo el informe y el plan.

## Restricciones
- NO modificar: backend/, docs/
- SI usar: shadcn/ui, Recharts, Tailwind, tipos de contracts.ts
- No agregar Supabase todavía
- No recalcular lógica analítica en frontend
```

---

## Resumen de la secuencia completa

```
JUNIE (IntelliJ)
  ✅ Ya hecho: estructura, config, schemas, frontend visual
  → J1: IngestService + NormalizationService
  → J2: ValidationService + ArtifactBuilder
  → J3: Routes (health, sessions, analyze) + main.py conectado
  → J4: Verificación end-to-end
  → J5: Commit y push

EMERGENT (después)
  → Lee repo, produce informe de gaps
  → Bloque 1: MongoDB (reemplaza SESSION_STORE)
  → Bloque 2: Profiler + StatsEngine
  → Bloque 3: LLM + Provenance + Charts
  → Bloque 4: Docling, observabilidad, hardening

V0 (después o en paralelo con Emergent)
  → Lee repo, produce informe de gaps
  → Mejora UX/diseño
  → Completa componentes faltantes
  → Conecta con endpoints nuevos de Emergent
  → Historial, estados, responsive
```
