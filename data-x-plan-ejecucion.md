# Data-X — Plan de Ejecución Paso a Paso

Este documento es una guía operativa. Te dice exactamente qué hacer, en qué orden, y qué copiar/pegar en cada herramienta.

---

## FASE 1: Bootstrap en IntelliJ

Todo lo que sigue lo hacés vos desde IntelliJ IDEA. El objetivo es dejar el monorepo listo para que Emergent y v0 puedan empezar a trabajar sin ambigüedad.

### Paso 1.1 — Crear el repositorio en GitHub

1. Andá a GitHub → New Repository.
2. Nombre: `data-x` (o el que elijas).
3. Visibilidad: private (o public si querés).
4. NO inicialices con README (lo vas a crear vos).
5. Copiá la URL del repo.

### Paso 1.2 — Clonar e inicializar desde IntelliJ

Abrí terminal en IntelliJ:

```bash
git clone https://github.com/TU_USUARIO/data-x.git
cd data-x
```

### Paso 1.3 — Crear la estructura de carpetas completa

```bash
# Raíz
mkdir -p backend/app/core
mkdir -p backend/app/schemas
mkdir -p backend/app/services
mkdir -p backend/app/api/routes
mkdir -p backend/app/repositories
mkdir -p backend/app/db
mkdir -p backend/tests/fixtures
mkdir -p frontend/src/app/workspace
mkdir -p frontend/src/components/ui
mkdir -p frontend/src/lib
mkdir -p frontend/src/types
mkdir -p frontend/public
mkdir -p docs/reference
mkdir -p .github
```

### Paso 1.4 — Crear todos los __init__.py del backend

```bash
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/routes/__init__.py
touch backend/app/repositories/__init__.py
touch backend/app/db/__init__.py
```

### Paso 1.5 — Crear archivos del backend

Creá cada archivo desde IntelliJ. El contenido exacto de cada uno está en el documento `data-x-monorepo-setup.md` que ya tenés. Los archivos son:

| Archivo | Qué contiene |
|---------|-------------|
| `backend/app/main.py` | FastAPI app con health check y CORS |
| `backend/app/core/config.py` | Pydantic Settings con env vars |
| `backend/app/core/logging.py` | structlog configurado |
| `backend/app/schemas/session.py` | SessionResponse model |
| `backend/app/schemas/analyze.py` | AnalyzeRequest, AnalyzeResponse, ErrorResponse |
| `backend/app/schemas/artifacts.py` | Vacío con `# Emergent implementará` |
| `backend/app/schemas/provenance.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/ingest.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/normalization.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/validation.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/profiler.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/stats_engine.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/artifact_builder.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/provenance.py` | Vacío con `# Emergent implementará` |
| `backend/app/services/llm_service.py` | Vacío con `# Emergent implementará` |
| `backend/app/api/routes/health.py` | Vacío con `# Emergent implementará` |
| `backend/app/api/routes/sessions.py` | Vacío con `# Emergent implementará` |
| `backend/app/api/routes/analyze.py` | Vacío con `# Emergent implementará` |
| `backend/app/repositories/mongo.py` | Vacío con `# Emergent implementará` |
| `backend/app/db/client.py` | Vacío con `# Emergent implementará` |
| `backend/requirements.txt` | Dependencias Python completas |
| `backend/.env.example` | Variables de entorno de referencia |
| `backend/README.md` | Descripción breve del backend |

**Para los archivos placeholder**, el contenido es simplemente:

```python
# Emergent implementará este módulo.
# Ver docs/prd-backend-emergent.md para especificación.
```

### Paso 1.6 — Crear fixture de test

Archivo `backend/tests/fixtures/ventas.csv`:

```csv
id,name,age,salary
1,Alice,28,75000
2,Bob,35,82000
3,Carol,41,91000
```

### Paso 1.7 — Inicializar el frontend

Desde terminal en IntelliJ, posicionado en la raíz del repo:

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

Cuando pregunte opciones:
- TypeScript: **Yes**
- ESLint: **Yes**
- Tailwind: **Yes**
- src/ directory: **Yes**
- App Router: **Yes**
- Import alias: **@/***

Después:

```bash
# shadcn/ui
npx shadcn-ui@latest init

# Recharts
npm install recharts

# Lucide icons
npm install lucide-react
```

### Paso 1.8 — Crear archivos del frontend

| Archivo | Qué contiene |
|---------|-------------|
| `frontend/src/types/contracts.ts` | Tipos TypeScript derivados del backend |
| `frontend/src/lib/api.ts` | Cliente HTTP al backend |
| `frontend/.env.example` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |

El contenido exacto está en `data-x-monorepo-setup.md`.

### Paso 1.9 — Copiar documentación a docs/

Copiá los archivos de documentación del proyecto:

| Archivo origen | Destino |
|---------------|---------|
| `data-x-prd-maestro.md` | `docs/prd-maestro.md` |
| `data-x-prd-back-emergent.md` | `docs/prd-backend-emergent.md` |
| `data-x-prd-front-v0.md` | `docs/prd-front-v0.md` |
| `data-x-roadmap-2026.md` | `docs/roadmap-2026.md` |
| `data-x-technical-evolution.md` | `docs/technical-evolution.md` |
| `data-x-docling-strategy-2026.md` | `docs/docling-strategy.md` |
| `data-x-external-references.md` | `docs/reference/external-references.md` |

### Paso 1.10 — Crear archivos de configuración raíz

**`.gitignore`** — contenido en `data-x-monorepo-setup.md`

**`.github/CODEOWNERS`** — contenido en `data-x-monorepo-setup.md`

**`README.md`** (raíz):

```markdown
# Data-X

Plataforma de análisis de datos: ingestión unificada, análisis determinístico, artifacts reutilizables y provenance.

## Estructura

- `backend/` — Python/FastAPI (ownership: Emergent)
- `frontend/` — Next.js/React (ownership: v0)
- `docs/` — Documentación del producto (read-only)

## Setup local

### Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

### Frontend
cd frontend
npm install
npm run dev
```

### Paso 1.11 — Verificar que todo arranca

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Abrir http://localhost:8000/health → debe devolver {"status":"ok"}

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
# Abrir http://localhost:3000 → debe mostrar la página de Next.js
```

### Paso 1.12 — Commit y push

```bash
cd ..  # volver a la raíz
git add .
git commit -m "[bootstrap] estructura inicial del monorepo Data-X"
git push origin main
```

---

## FASE 2: Arrancar Emergent (Backend)

Una vez que el repo está en GitHub con la estructura completa, conectás Emergent al repositorio.

### Paso 2.1 — Conectar Emergent al repo

En Emergent.sh:
1. Conectá el repositorio `data-x`.
2. Emergent verá toda la estructura.

### Paso 2.2 — Primer prompt para Emergent

Este es el prompt de contexto inicial. Copiá y pegá:

```
## Contexto del proyecto
Este es el monorepo de Data-X, una plataforma de análisis de datos.

## Tu rol
Sos el responsable de implementar el backend del producto.

## Documentación
Leé estos archivos antes de hacer cualquier cosa:
- docs/prd-maestro.md (fuente de verdad del producto)
- docs/prd-backend-emergent.md (tu PRD operativo)
- docs/roadmap-2026.md (secuencia de fases)

## Scope del repositorio
- Escribir solo en: backend/
- Puede leer: frontend/, docs/
- No tocar: frontend/, docs/

## Estado actual
El scaffolding base ya existe:
- backend/app/main.py tiene health check funcional
- backend/app/core/config.py tiene Pydantic Settings
- backend/app/core/logging.py tiene structlog
- backend/app/schemas/ tiene los contratos canónicos (session.py, analyze.py)
- Los servicios en backend/app/services/ están como placeholders vacíos
- Las routes en backend/app/api/routes/ están como placeholders vacíos
- requirements.txt tiene todas las dependencias listadas

## Tarea
Leé la documentación indicada y proponé un plan de implementación
por fases/sprints, tal como indica el PRD backend.

NO implementes nada todavía. Solo proponé el plan.

## NO hacer
- no escribir código todavía
- no tocar frontend/
- no tocar docs/
- NO testing agent

## Si falla 2 veces
PARA y dame opciones
```

### Paso 2.3 — Flujo de trabajo con Emergent

Después del plan, el flujo es:

1. Emergent propone plan de fases.
2. Vos aprobás o ajustás.
3. Emergent ejecuta **una fase por vez**.
4. Al cerrar cada fase, presenta informe.
5. Vos verificás y aprobás antes de la siguiente.

Los prompts posteriores siguen el formato de la guía de prompts de Emergent (una tarea por prompt, scope claro, archivo exacto, verificación simple).

**Ejemplo de prompt para fase 1 (bootstrap backend):**

```
## Tarea
Implementar el bootstrap completo del backend: que arranque,
que el health check funcione como route real, y que la
estructura de imports sea válida.

## Scope
- Escribir solo en: backend/
- Puede leer: frontend/, docs/
- No tocar: frontend/, docs/

## Archivos a tocar
- backend/app/main.py
- backend/app/api/routes/health.py

## Debe hacer
- Mover el health check a routes/health.py como router de FastAPI
- Registrar el router en main.py
- Asegurar que todos los imports funcionen

## NO hacer
- no implementar otros servicios todavía
- no tocar schemas
- no agregar tests
- NO testing agent

## Verificación
python -c "from app.main import app; print('OK')"
curl -X GET http://localhost:8000/health

## Si falla 2 veces
PARA y dame opciones
```

---

## FASE 3: Arrancar v0 (Frontend)

v0 puede arrancar en paralelo con Emergent o después de que Emergent tenga los endpoints básicos listos. Lo ideal es que al menos `/health` y `/sessions` estén funcionando.

### Paso 3.1 — Conectar v0 al repo

En v0.dev:
1. Conectá el repositorio `data-x`.
2. v0 verá toda la estructura.

### Paso 3.2 — Primer prompt para v0

```
## Contexto
- Proyecto: Data-X, plataforma de análisis de datos
- Stack: Next.js 14 (App Router) + TypeScript + shadcn/ui + Recharts + Tailwind
- Backend externo: FastAPI (Python), URL por env var NEXT_PUBLIC_API_BASE_URL
- Archivos relevantes:
  - frontend/src/types/contracts.ts (tipos derivados del backend)
  - frontend/src/lib/api.ts (cliente HTTP al backend)
  - docs/prd-front-v0.md (tu PRD operativo)
  - docs/prd-maestro.md (fuente de verdad del producto)

## Scope
- Escribir solo en: frontend/
- Puede leer: backend/, docs/
- No tocar: backend/, docs/

## Estado actual
El proyecto Next.js ya está inicializado con:
- shadcn/ui configurado
- Recharts instalado
- Tipos TypeScript en src/types/contracts.ts
- Cliente API en src/lib/api.ts
- Página default de Next.js en src/app/page.tsx

## Tarea
Leé los PRDs en docs/ (especialmente prd-front-v0.md y prd-maestro.md)
y proponé un plan de implementación por fases/sprints.

NO implementes nada todavía. Solo proponé el plan.

## Restricciones
- NO modificar: backend/, docs/
- SI usar: shadcn/ui, Recharts, Tailwind, los tipos de contracts.ts
- Integración: via NEXT_PUBLIC_API_BASE_URL, no hardcodear
- No usar Supabase todavía
- No recalcular lógica analítica en frontend
```

### Paso 3.3 — Flujo de trabajo con v0

El flujo es el mismo que con Emergent:

1. v0 propone plan de fases.
2. Vos aprobás o ajustás.
3. v0 ejecuta **una feature principal por prompt**.
4. Al cerrar cada fase, presenta informe.
5. Vos verificás y aprobás antes de la siguiente.

Los prompts posteriores siguen el formato de la guía de prompts de v0.

**Ejemplo de prompt para la primera feature (landing):**

```
## Contexto
- Proyecto: Data-X
- Stack: Next.js + shadcn/ui + Tailwind
- Backend: FastAPI en NEXT_PUBLIC_API_BASE_URL

## Scope
- Escribir solo en: frontend/
- Puede leer: backend/, docs/
- No tocar: backend/, docs/

## Tarea
Crear la landing page del producto en frontend/src/app/page.tsx

## Debe incluir
- Hero con título "Data-X" y subtítulo descriptivo
- CTA "Comenzar" que lleve a /workspace
- Breve explicación del producto (3 features principales)
- Footer mínimo
- Diseño limpio, profesional, minimalista

## Restricciones
- NO modificar: layout.tsx (solo page.tsx)
- SI usar: shadcn/ui Button, Card si aplica
- No conectar a API todavía (esta es solo la landing estática)

## Resultado esperado
Landing profesional que explique Data-X y lleve al workspace
```

---

## FASE 4: Coordinación continua

### Regla de oro

```
IntelliJ = coordina, revisa, aprueba
Emergent = implementa backend, reporta, espera aprobación
v0       = implementa frontend, reporta, espera aprobación
```

### Orden recomendado de implementación

| # | Emergent (backend) | v0 (frontend) |
|---|-------------------|---------------|
| 1 | Bootstrap + health route | Landing page |
| 2 | Config + logging | Layout base + navegación |
| 3 | Schemas + contratos | Design system + componentes base |
| 4 | POST /sessions (ingest) | Workspace vacío + FileUploader |
| 5 | POST /analyze (pipeline) | Integración sesiones + upload |
| 6 | Profiler + stats engine | Vista de resultados |
| 7 | Artifact builder | ArtifactRenderer + renderers |
| 8 | Provenance service | ProvenancePanel |
| 9 | LLM service | Estados loading/error/empty |
| 10 | Persistencia MongoDB | Historial / sesiones |
| 11 | Observabilidad | Hardening UX |
| 12 | Hardening backend | Integración final |

Las fases 1-3 de ambos pueden ir en paralelo. A partir de la fase 4, conviene que el backend vaya uno o dos pasos adelante del frontend para que v0 tenga endpoints reales contra los cuales integrar.

### Cuándo sincronizar

Sincronizá cuando:
- Emergent cierra una fase que cambia contracts o endpoints.
- v0 necesita un endpoint que aún no existe.
- Hay un conflicto en el repo (raro si se respeta ownership).

### Cómo sincronizar

1. Emergent hace push a `main` (o a una branch `backend/fase-N`).
2. v0 hace pull para ver los cambios en `backend/`.
3. v0 actualiza `frontend/src/types/contracts.ts` si cambió algún schema.
4. v0 continúa implementando sobre contratos reales.

---

## Resumen ejecutivo

```
1. IntelliJ → crea repo, estructura, scaffolding, docs, push a main
2. Emergent → conecta repo, lee PRDs, propone plan, implementa backend por fases
3. v0       → conecta repo, lee PRDs, propone plan, implementa frontend por fases
4. Vos      → aprobás cada fase, coordinás, mantenés ownership de docs/
```

Eso es todo. Con el repo bootstrapeado y los PRDs en `docs/`, tanto Emergent como v0 tienen toda la información que necesitan para trabajar de forma autónoma dentro de su scope.
