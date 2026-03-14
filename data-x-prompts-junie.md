# Data-X — Prompts para Junie (IntelliJ)

Guía operativa de prompts para delegar a Junie el bootstrap del monorepo Data-X.
Cada prompt es una tarea atómica. No le pidas todo junto.

---

## Cómo usar esta guía

1. Abrí IntelliJ IDEA con el proyecto Data-X (carpeta raíz).
2. Abrí Junie (AI Chat → seleccionar Junie como agente).
3. Copiá y pegá cada prompt en orden.
4. Esperá a que termine, revisá los cambios, aceptá o corregí.
5. Pasá al siguiente prompt.

**Regla importante:** Junie tiende a expandir el scope. Si ves que quiere tocar archivos que no le pediste, rechazá esos cambios y repetí el prompt con más restricciones.

---

## PROMPT 1 — Estructura de carpetas

```
## Tarea
Crear la estructura de carpetas del monorepo Data-X.

## Qué hacer
Crear exactamente estas carpetas y archivos __init__.py:

backend/app/__init__.py
backend/app/core/__init__.py
backend/app/schemas/__init__.py
backend/app/services/__init__.py
backend/app/api/__init__.py
backend/app/api/routes/__init__.py
backend/app/repositories/__init__.py
backend/app/db/__init__.py
backend/tests/fixtures/
frontend/src/app/workspace/
frontend/src/components/ui/
frontend/src/lib/
frontend/src/types/
frontend/public/
docs/reference/
.github/

## NO hacer
- No crear ningún archivo de código todavía (solo carpetas e __init__.py)
- No inicializar npm ni pip
- No crear README ni .gitignore todavía
- No instalar nada
```

---

## PROMPT 2 — Backend: main.py

```
## Tarea
Crear backend/app/main.py

## Archivo
backend/app/main.py

## Contenido exacto
FastAPI app con:
- título "Data-X API", versión "0.1.0"
- CORSMiddleware que lea origins desde config
- un endpoint GET /health que devuelva {"status": "ok"}
- import de settings desde app.core.config
- comentarios indicando dónde se registrarán routers después

## NO hacer
- No crear otros archivos
- No crear routers separados todavía
- No instalar dependencias
- No correr el servidor
```

---

## PROMPT 3 — Backend: config.py

```
## Tarea
Crear backend/app/core/config.py

## Archivo
backend/app/core/config.py

## Contenido exacto
Clase Settings usando pydantic_settings.BaseSettings con estos campos:
- host: str = "0.0.0.0"
- port: int = 8000
- env: str = "development"
- mongodb_uri: str = "mongodb://localhost:27017"
- mongodb_db: str = "datax"
- litellm_api_key: str = ""
- litellm_model: str = "gpt-4o-mini"
- cors_origins: list[str] = ["http://localhost:3000"]
- otel_service_name: str = "datax-backend"

Config inner class con env_file=".env" y env_file_encoding="utf-8"

Instanciar settings = Settings() al final del módulo.

## NO hacer
- No crear otros archivos
- No modificar main.py
- No instalar dependencias
```

---

## PROMPT 4 — Backend: logging.py

```
## Tarea
Crear backend/app/core/logging.py

## Archivo
backend/app/core/logging.py

## Contenido exacto
Configurar structlog con:
- merge_contextvars
- add_log_level
- StackInfoRenderer
- ConsoleRenderer (dev)
- PrintLoggerFactory
- cache_logger_on_first_use=True

Función get_logger(name) que devuelva structlog.get_logger(name)

## NO hacer
- No crear otros archivos
- No modificar main.py ni config.py
- No instalar dependencias
```

---

## PROMPT 5 — Backend: schemas canónicos

```
## Tarea
Crear los schemas Pydantic canónicos del backend.

## Archivos a crear (3 archivos)

### backend/app/schemas/session.py
SessionResponse(BaseModel):
- session_id: str
- status: Literal["created", "processing", "ready", "error"]
- created_at: datetime
- source_metadata: dict
- schema_info: dict | None = None
- profile: dict | None = None
- contract_version: str = "v1"

### backend/app/schemas/analyze.py
AnalyzeRequest(BaseModel):
- session_id: str
- query: str

AnalyzeResponse(BaseModel):
- session_id: str
- artifacts: list[dict]
- provenance: dict | None = None
- summary: str | None = None
- contract_version: str = "v1"

ErrorResponse(BaseModel):
- error_code: str
- message: str
- details: dict | None = None

### backend/app/schemas/artifacts.py
Archivo con comentario:
# Emergent implementará este módulo.
# Ver docs/prd-backend-emergent.md para especificación.

### backend/app/schemas/provenance.py
Archivo con comentario:
# Emergent implementará este módulo.
# Ver docs/prd-backend-emergent.md para especificación.

## NO hacer
- No crear otros archivos fuera de schemas/
- No modificar main.py
- No agregar validaciones extras
- No agregar tests
```

---

## PROMPT 6 — Backend: placeholders de servicios y routes

```
## Tarea
Crear archivos placeholder para los servicios y routes que Emergent implementará.

## Archivos a crear
Cada uno con este contenido exacto:
# Emergent implementará este módulo.
# Ver docs/prd-backend-emergent.md para especificación.

### Servicios (dentro de backend/app/services/)
- ingest.py
- normalization.py
- validation.py
- profiler.py
- stats_engine.py
- artifact_builder.py
- provenance.py
- llm_service.py

### Routes (dentro de backend/app/api/routes/)
- health.py
- sessions.py
- analyze.py

### Repositories y DB
- backend/app/repositories/mongo.py
- backend/app/db/client.py

## NO hacer
- No escribir lógica en ninguno de estos archivos
- No modificar archivos existentes
- No agregar imports en main.py
```

---

## PROMPT 7 — Backend: requirements.txt y .env.example

```
## Tarea
Crear requirements.txt y .env.example del backend.

## Archivos a crear

### backend/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
motor>=3.6.0
pymongo>=4.9.0
pandas>=2.2.0
pandera>=0.20.0
scipy>=1.14.0
statsmodels>=0.14.0
pingouin>=0.5.5
docling>=2.0.0
litellm>=1.50.0
opentelemetry-api>=1.27.0
opentelemetry-sdk>=1.27.0
opentelemetry-instrumentation-fastapi>=0.48b0
structlog>=24.4.0
python-multipart>=0.0.12
httpx>=0.27.0

### backend/.env.example
HOST=0.0.0.0
PORT=8000
ENV=development
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=datax
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
OTEL_SERVICE_NAME=datax-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

## NO hacer
- No instalar dependencias (solo crear los archivos)
- No crear virtualenv
- No modificar otros archivos
```

---

## PROMPT 8 — Backend: fixture de test y README

```
## Tarea
Crear fixture CSV de prueba y README del backend.

## Archivos a crear

### backend/tests/fixtures/ventas.csv
id,name,age,salary
1,Alice,28,75000
2,Bob,35,82000
3,Carol,41,91000

### backend/README.md
# Data-X Backend

Backend del producto Data-X. Python + FastAPI + Pydantic v2.

## Setup
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

## Health check
curl http://localhost:8000/health

## NO hacer
- No modificar otros archivos
- No crear tests Python
```

---

## PROMPT 9 — Frontend: inicializar Next.js

```
## Tarea
Inicializar el proyecto Next.js dentro de frontend/

## Qué hacer
Ejecutar en terminal, posicionado en la carpeta frontend/:

npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

Responder Yes a todas las opciones interactivas.

Después de que termine, ejecutar:

npx shadcn-ui@latest init

Y luego:

npm install recharts lucide-react

## NO hacer
- No modificar archivos del backend
- No crear componentes todavía
- No escribir páginas todavía
- Solo inicializar el proyecto y las dependencias
```

---

## PROMPT 10 — Frontend: tipos y cliente API

```
## Tarea
Crear los tipos TypeScript derivados del backend y el cliente HTTP.

## Archivos a crear

### frontend/src/types/contracts.ts
Interfaces TypeScript que reflejen exactamente los schemas Pydantic del backend:
- SessionResponse (session_id, status, created_at, source_metadata, schema_info, profile, contract_version)
- AnalyzeRequest (session_id, query)
- AnalyzeResponse (session_id, artifacts, provenance, summary, contract_version)
- ErrorResponse (error_code, message, details)
- Artifact (artifact_type, title, data)
- TableArtifact extends Artifact (artifact_type: 'table', data con columns y rows)
- MetricSetArtifact extends Artifact (artifact_type: 'metric_set', data con metrics array)
- ChartConfigArtifact extends Artifact (artifact_type: 'chart_config', data con chart_type, x_key, y_key, series)
- SummaryArtifact extends Artifact (artifact_type: 'summary', data con text)
- AlertsArtifact extends Artifact (artifact_type: 'alerts', data con items array)
- ProvenanceData (spans array con source, field, note)

Los tipos deben coincidir 1:1 con los schemas en backend/app/schemas/.
Leé esos archivos para asegurar consistencia.

### frontend/src/lib/api.ts
Cliente HTTP que:
- lea NEXT_PUBLIC_API_BASE_URL de env (default http://localhost:8000)
- tenga función request<T> genérica con fetch
- exporte objeto api con métodos:
  - health() → GET /health
  - createSession(file: File) → POST /sessions con FormData
  - analyze(sessionId, query) → POST /analyze con JSON

### frontend/.env.example
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

## NO hacer
- No modificar archivos del backend
- No crear componentes ni páginas
- No instalar dependencias nuevas
```

---

## PROMPT 11 — Archivos raíz del monorepo

```
## Tarea
Crear los archivos de configuración raíz del monorepo.

## Archivos a crear

### .gitignore (en la raíz del proyecto)
Ignorar:
- Python: __pycache__/, *.py[cod], .venv/, venv/, env/, *.egg-info/, dist/, build/
- Node: node_modules/, .next/, out/
- Env: .env, .env.local, .env.*.local
- IDE: .idea/, .vscode/, *.swp
- OS: .DS_Store, Thumbs.db
- Logs: *.log
- MongoDB: data/db/

### .github/CODEOWNERS
/backend/    @emergent-bot
/frontend/   @v0-bot
/docs/       @TU_USUARIO

(Reemplazá @TU_USUARIO con el username real de GitHub)

### README.md (raíz)
# Data-X

Plataforma de análisis de datos: ingestión unificada, análisis determinístico, artifacts reutilizables y provenance.

## Estructura
- backend/ — Python/FastAPI (ownership: Emergent)
- frontend/ — Next.js/React (ownership: v0)
- docs/ — Documentación del producto (read-only)

## Setup local

### Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

### Frontend
cd frontend
npm install
npm run dev

## NO hacer
- No modificar archivos del backend ni frontend
- No agregar configuraciones de CI/CD todavía
```

---

## PROMPT 12 — Copiar documentación a docs/

```
## Tarea
Necesito que copies los archivos de documentación del proyecto a la carpeta docs/.

## Qué hacer
Los archivos fuente están en la raíz del proyecto como:
- data-x-monorepo-setup.md
- data-x-plan-ejecucion.md

Pero además necesito que copies los documentos de producto.
Si existen en alguna parte del proyecto, copialos a docs/ con estos nombres:

docs/prd-maestro.md
docs/prd-backend-emergent.md
docs/prd-front-v0.md
docs/roadmap-2026.md
docs/technical-evolution.md
docs/docling-strategy.md
docs/reference/external-references.md

Si NO existen todavía como archivos (porque están solo como documentos externos), 
creá un placeholder en cada uno con:

# [Nombre del documento]
# TODO: pegar contenido del documento original aquí.

## NO hacer
- No modificar archivos del backend ni frontend
- No inventar contenido
- Solo crear la estructura de docs/
```

**Nota:** Después de este prompt, vos manualmente pegás el contenido de cada PRD en los archivos correspondientes dentro de `docs/`. Junie no tiene acceso a tus documentos originales salvo que ya estén en el repo.

---

## PROMPT 13 — Verificación final

```
## Tarea
Verificar que el proyecto está correctamente bootstrapeado.

## Qué hacer
1. Verificar que backend/app/main.py importa correctamente:
   python -c "from app.main import app; print('OK')"
   (ejecutar desde la carpeta backend/)

2. Verificar que los schemas importan:
   python -c "from app.schemas.session import SessionResponse; print('OK')"
   python -c "from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse; print('OK')"

3. Verificar que el frontend compila:
   cd frontend && npm run build
   (o al menos npm run dev sin errores)

4. Listar la estructura del proyecto y confirmar que coincide con 
   lo esperado en el documento data-x-monorepo-setup.md

## NO hacer
- No modificar ningún archivo
- No instalar nada nuevo
- No corregir errores automáticamente — solo reportarlos
- Si algo falla, decime qué falló y yo decido cómo corregirlo
```

---

## PROMPT 14 — Commit y push

```
## Tarea
Hacer commit y push del proyecto completo.

## Qué hacer
git add .
git commit -m "[bootstrap] estructura inicial del monorepo Data-X"
git push origin main

## NO hacer
- No modificar ningún archivo antes del commit
- No crear branches
- No agregar tags
```

---

## Después de Junie: Emergent y v0

Una vez que Junie terminó y el repo está en GitHub, seguí con los prompts de las Fases 2 y 3 del documento `data-x-plan-ejecucion.md`:

- **Emergent:** conectalo al repo → usá el prompt de contexto inicial → pedile plan de fases → aprobá → ejecutá fase por fase.
- **v0:** conectalo al repo → usá el prompt de contexto inicial → pedile plan de fases → aprobá → ejecutá feature por feature.

---

## Resumen de orden

| # | Prompt | Qué crea |
|---|--------|----------|
| 1 | Estructura de carpetas | Carpetas + __init__.py |
| 2 | main.py | FastAPI app + health |
| 3 | config.py | Pydantic Settings |
| 4 | logging.py | structlog |
| 5 | Schemas | session.py, analyze.py, placeholders |
| 6 | Placeholders | Servicios, routes, repo, db |
| 7 | requirements.txt + .env | Dependencias + env vars |
| 8 | Fixture + README backend | ventas.csv + README.md |
| 9 | Init Next.js | create-next-app + shadcn + recharts |
| 10 | Tipos + API client | contracts.ts + api.ts |
| 11 | Config raíz | .gitignore + CODEOWNERS + README |
| 12 | Documentación | docs/ con PRDs |
| 13 | Verificación | Confirmar que todo compila |
| 14 | Commit + push | Subir a GitHub |
