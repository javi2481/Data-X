# Data-X — Guía de Setup del Monorepo

## 1. Contexto y modelo de trabajo

Data-X se organiza como un monorepo en GitHub con tres actores que operan sobre el mismo repositorio:

| Actor | Responsabilidad | Puede escribir en | Puede leer |
|-------|----------------|-------------------|------------|
| **IntelliJ** (tú) | Bootstrap, scaffolding, configuración inicial, coordinación | `backend/`, `frontend/`, `docs/` | Todo |
| **Emergent.sh** | Desarrollo e iteración del backend | Solo `backend/` | Todo |
| **v0 (Vercel)** | Desarrollo e iteración del frontend | Solo `frontend/` | Todo |

La regla fundamental es: **lectura cruzada permitida, escritura cruzada prohibida**. Emergent nunca toca `frontend/`. v0 nunca toca `backend/`. Ninguno toca `docs/` salvo instrucción explícita tuya.

---

## 2. Estructura raíz del monorepo

```
data-x/
├── backend/                  # Python — ownership de Emergent
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── analyze.py
│   │   │   ├── artifacts.py
│   │   │   └── provenance.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py
│   │   │   ├── normalization.py
│   │   │   ├── validation.py
│   │   │   ├── profiler.py
│   │   │   ├── stats_engine.py
│   │   │   ├── artifact_builder.py
│   │   │   ├── provenance.py
│   │   │   └── llm_service.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── sessions.py
│   │   │       ├── analyze.py
│   │   │       └── health.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── mongo.py
│   │   └── db/
│   │       ├── __init__.py
│   │       └── client.py
│   ├── tests/
│   │   └── fixtures/
│   │       └── ventas.csv
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/                 # TypeScript/Next.js — ownership de v0
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── workspace/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── FileUploader.tsx
│   │   │   ├── ArtifactRenderer.tsx
│   │   │   ├── TableView.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ChartContainer.tsx
│   │   │   ├── ProvenancePanel.tsx
│   │   │   ├── LoadingState.tsx
│   │   │   └── ErrorBanner.tsx
│   │   ├── lib/
│   │   │   └── api.ts           # client HTTP al backend
│   │   └── types/
│   │       └── contracts.ts     # tipos derivados del backend
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── components.json          # config shadcn/ui
│   ├── .env.example
│   └── README.md
│
├── docs/                        # Documentación — read-only para Emergent y v0
│   ├── prd-maestro.md
│   ├── prd-backend-emergent.md
│   ├── prd-front-v0.md
│   ├── roadmap-2026.md
│   ├── technical-evolution.md
│   ├── docling-strategy.md
│   └── reference/
│       └── external-references.md
│
├── .gitignore
├── .github/
│   └── CODEOWNERS
└── README.md                    # Este README raíz
```

---

## 3. Stack tecnológico exacto

### 3.1 Backend (Python)

Este es el stack que Emergent usará. IntelliJ debe generar el scaffolding con las mismas dependencias.

**Framework y core:**
- Python 3.11+
- FastAPI (async handlers)
- Pydantic v2 (schemas y validación)
- Uvicorn (server ASGI)

**Datos y análisis:**
- Pandas
- Pandera (validación de DataFrames)
- SciPy
- statsmodels
- pingouin

**Ingestión:**
- Docling (pipeline unificado, Docling-first)

**LLM:**
- LiteLLM (gateway multi-provider)

**Persistencia:**
- MongoDB (Motor como async driver)

**Observabilidad:**
- OpenTelemetry
- structlog

**`requirements.txt` de referencia:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
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
```

### 3.2 Frontend (TypeScript/Next.js)

Este es el stack que v0 usará. IntelliJ debe generar el scaffolding con las mismas dependencias.

**Framework:**
- Next.js 14+ (App Router)
- React 18+
- TypeScript

**UI:**
- shadcn/ui
- Tailwind CSS
- Lucide React (iconos)

**Visualización:**
- Recharts

**`package.json` dependencias clave:**
```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "recharts": "^2.12.0",
    "lucide-react": "^0.440.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "@types/react": "^18.3.0",
    "@types/node": "^22.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 4. Archivos de configuración clave

### 4.1 `.gitignore` (raíz)

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
*.egg
.venv/
venv/
env/

# Node
node_modules/
.next/
out/

# Env
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# MongoDB
data/db/
```

### 4.2 `.github/CODEOWNERS`

```
# Backend — Emergent ownership
/backend/    @emergent-bot

# Frontend — v0 ownership
/frontend/   @v0-bot

# Docs — solo el owner del repo
/docs/       @tu-usuario-github
```

### 4.3 `backend/.env.example`

```env
# Server
HOST=0.0.0.0
PORT=8000
ENV=development

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=datax

# LLM
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o-mini

# CORS
CORS_ORIGINS=http://localhost:3000

# OpenTelemetry
OTEL_SERVICE_NAME=datax-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 4.4 `frontend/.env.example`

```env
# API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 5. Archivos de bootstrap que IntelliJ debe crear

### 5.1 Backend — `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Data-X API",
    version="0.1.0",
    description="Data-X backend — análisis determinístico de datos",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes se registran aquí
# from app.api.routes import sessions, analyze, health
# app.include_router(health.router)
# app.include_router(sessions.router)
# app.include_router(analyze.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

### 5.2 Backend — `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "datax"

    litellm_api_key: str = ""
    litellm_model: str = "gpt-4o-mini"

    cors_origins: list[str] = ["http://localhost:3000"]

    otel_service_name: str = "datax-backend"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

### 5.3 Backend — `backend/app/core/logging.py`

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
```

### 5.4 Backend — Schemas canónicos

**`backend/app/schemas/session.py`**
```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class SessionResponse(BaseModel):
    session_id: str
    status: Literal["created", "processing", "ready", "error"]
    created_at: datetime
    source_metadata: dict
    schema_info: dict | None = None
    profile: dict | None = None
    contract_version: str = "v1"
```

**`backend/app/schemas/analyze.py`**
```python
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    session_id: str
    query: str


class AnalyzeResponse(BaseModel):
    session_id: str
    artifacts: list[dict]
    provenance: dict | None = None
    summary: str | None = None
    contract_version: str = "v1"


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None
```

### 5.5 Backend — Fixture de test

**`backend/tests/fixtures/ventas.csv`**
```csv
id,name,age,salary
1,Alice,28,75000
2,Bob,35,82000
3,Carol,41,91000
```

### 5.6 Frontend — `frontend/src/lib/api.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  createSession: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },

  analyze: (sessionId: string, query: string) =>
    request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, query }),
    }),
};
```

### 5.7 Frontend — `frontend/src/types/contracts.ts`

```typescript
// Tipos derivados del backend — fuente de verdad: schemas Pydantic

export interface SessionResponse {
  session_id: string;
  status: 'created' | 'processing' | 'ready' | 'error';
  created_at: string;
  source_metadata: Record<string, unknown>;
  schema_info: Record<string, unknown> | null;
  profile: Record<string, unknown> | null;
  contract_version: string;
}

export interface AnalyzeRequest {
  session_id: string;
  query: string;
}

export interface AnalyzeResponse {
  session_id: string;
  artifacts: Artifact[];
  provenance: ProvenanceData | null;
  summary: string | null;
  contract_version: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details: Record<string, unknown> | null;
}

// Artifacts
export interface Artifact {
  artifact_type: string;
  title: string;
  data: Record<string, unknown>;
}

export interface TableArtifact extends Artifact {
  artifact_type: 'table';
  data: {
    columns: string[];
    rows: Record<string, unknown>[];
  };
}

export interface MetricSetArtifact extends Artifact {
  artifact_type: 'metric_set';
  data: {
    metrics: Array<{ label: string; value: number | string }>;
  };
}

export interface ChartConfigArtifact extends Artifact {
  artifact_type: 'chart_config';
  data: {
    chart_type: 'bar' | 'line' | 'pie' | 'scatter';
    x_key: string;
    y_key: string;
    series: Record<string, unknown>[];
  };
}

export interface SummaryArtifact extends Artifact {
  artifact_type: 'summary';
  data: { text: string };
}

export interface AlertsArtifact extends Artifact {
  artifact_type: 'alerts';
  data: {
    items: Array<{ level: 'info' | 'warning' | 'error'; message: string }>;
  };
}

export interface ProvenanceData {
  spans: Array<{
    source: string;
    field: string;
    note: string;
  }>;
}
```

---

## 6. Flujo de trabajo entre los tres actores

### Paso 1 — IntelliJ (tú) hace el bootstrap

1. Creás el repo en GitHub.
2. Generás toda la estructura de carpetas con los archivos base.
3. Hacés commit y push a `main`.
4. Copiás los docs del proyecto a `docs/`.

### Paso 2 — Emergent recibe el repo

Emergent conecta al repo y recibe como contexto:
- El PRD backend (`docs/prd-backend-emergent.md`)
- Los schemas ya creados en `backend/app/schemas/`
- La estructura base de `backend/`
- Acceso de lectura a `frontend/` y `docs/`

Emergent solo escribe dentro de `backend/`. Implementa por fases, reporta, y espera tu aprobación antes de avanzar.

### Paso 3 — v0 recibe el repo

v0 conecta al repo y recibe como contexto:
- El PRD frontend (`docs/prd-front-v0.md`)
- Los tipos en `frontend/src/types/contracts.ts`
- La estructura base de `frontend/`
- Acceso de lectura a `backend/` y `docs/`

v0 solo escribe dentro de `frontend/`. Implementa por fases, reporta, y espera tu aprobación antes de avanzar.

### Coordinación

```
     docs/  ←── fuente de verdad ──→  docs/
       ↓                                ↓
   Emergent                            v0
   lee docs/                       lee docs/
   lee frontend/                   lee backend/
   ESCRIBE backend/                ESCRIBE frontend/
       ↓                                ↓
   endpoints + contracts ──────→  tipos + consumo API
```

Ambos pueden trabajar en paralelo. La integración se produce a través de los contracts: Emergent define endpoints y schemas Pydantic; v0 los consume como tipos TypeScript.

---

## 7. Configuración de IntelliJ IDEA

### 7.1 Abrir como proyecto

Abrí la carpeta raíz `data-x/` como proyecto. IntelliJ detectará ambos módulos.

### 7.2 Backend (Python)

1. Configurá un Python SDK (3.11+) apuntando a un virtualenv dentro de `backend/`.
2. Marcá `backend/` como "Sources Root".
3. Run configuration: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` con working directory en `backend/`.

### 7.3 Frontend (Node.js)

1. Abrí un terminal en `frontend/` y ejecutá `npm install`.
2. Marcá `frontend/src/` como "Sources Root".
3. Run configuration: `npm run dev` con working directory en `frontend/`.

### 7.4 Ambos corriendo

- Backend en `http://localhost:8000`
- Frontend en `http://localhost:3000`
- El frontend consume el backend via `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

---

## 8. Reglas de consistencia para IntelliJ

Cuando trabajes desde IntelliJ, respetá estas reglas para no generar conflictos con Emergent ni v0:

1. **Mismo stack, sin sorpresas.** No introduzcas dependencias que no estén en los PRDs. Si necesitás algo nuevo, agregalo al requirements.txt o package.json correspondiente y documentá por qué.

2. **No refactorices lo que Emergent o v0 van a implementar.** El scaffolding inicial debe ser mínimo y correcto, no sobre-engineered.

3. **Los schemas Pydantic son la fuente de verdad.** Los tipos TypeScript en `frontend/src/types/contracts.ts` son derivados. Si cambia un schema, se actualiza el tipo.

4. **Variables de entorno, nunca hardcoded.** Toda URL, key o config va por env var.

5. **Commits claros.** Prefijá commits con `[backend]`, `[frontend]`, o `[docs]` para que sea fácil rastrear qué cambió cada actor.

---

## 9. Deploy targets

| Componente | Plataforma sugerida | Configuración |
|------------|-------------------|---------------|
| Backend | Railway / Render | Dockerfile o Procfile, env vars |
| Frontend | Vercel | Auto-detect Next.js, env vars |
| MongoDB | MongoDB Atlas | Connection string en env var |

---

## 10. Checklist de bootstrap completo

- [ ] Repo creado en GitHub
- [ ] Estructura de carpetas generada
- [ ] `backend/app/main.py` con health check funcional
- [ ] `backend/app/core/config.py` con Pydantic Settings
- [ ] `backend/app/core/logging.py` con structlog
- [ ] `backend/app/schemas/` con contratos canónicos
- [ ] `backend/requirements.txt` completo
- [ ] `backend/.env.example` presente
- [ ] `frontend/` inicializado con Next.js + TypeScript
- [ ] `frontend/src/types/contracts.ts` con tipos derivados
- [ ] `frontend/src/lib/api.ts` con cliente HTTP
- [ ] `frontend/.env.example` presente
- [ ] shadcn/ui inicializado (`npx shadcn-ui@latest init`)
- [ ] Recharts instalado
- [ ] `docs/` con todos los PRDs y documentos
- [ ] `.gitignore` raíz configurado
- [ ] `.github/CODEOWNERS` configurado
- [ ] README raíz con descripción del proyecto
- [ ] Backend arranca sin errores (`uvicorn app.main:app`)
- [ ] Frontend arranca sin errores (`npm run dev`)
- [ ] `GET /health` responde `{"status": "ok"}`
- [ ] Primer commit y push a `main`
