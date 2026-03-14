# CLAUDE.md — Data-X Project Context

## What is Data-X
Data-X is a data analysis platform: unified ingestion, deterministic analysis, reusable artifacts, and provenance. It's a monorepo with a Python/FastAPI backend and a Next.js/React frontend.

## Repository Structure
```
data-x/
├── backend/    → Python/FastAPI (Emergent ownership)
├── frontend/   → Next.js/React (v0 ownership)
├── docs/       → Product documentation (read-only)
├── datasets/   → Sample data files
```

## Critical Rules

### Ownership
- **Emergent** can ONLY write in `backend/`. Can read everything.
- **v0** can ONLY write in `frontend/`. Can read everything.
- **`docs/`** is read-only for all agents unless explicitly told otherwise.
- Cross-reading is allowed. Cross-writing is FORBIDDEN.

### Architecture Principles
- **Arquitectura Medallion (v3.0).** Los datos fluyen de Bronze (Raw) a Silver (Processed/EDA).
- **Backend calculates, frontend renders.** El backend genera Findings y ChartSpecs.
- **Finding as Unit of Value.** El análisis se organiza en hallazgos (Findings) detectados.
- **Docling-first ingestion.** Ingesta unificada con Docling (soporta CSV, XLSX, PDF).
- **Pandera schema validation.** Validación automática de esquemas en el pipeline Silver.
- **Deterministic layer.** Perfilado, validación y generación de especificaciones son determinísticos.
- **LiteLLM (Capa Gold).** Interpretación de datos mediante IA con mecanismo de retry y fallback determinístico.
- **Tests-first.** Suite de pruebas formal con pytest para asegurar la integridad del pipeline.
- **API-first.** El sistema funciona independientemente del frontend mediante la API `/api/*`.
- **Contracts are sacred.** Pydantic schemas (v2) son la fuente de verdad.

### What NOT to do
- Don't duplicate analytical logic in the frontend
- Don't introduce Supabase without explicit approval
- Don't add MCP/FastMCP in the MVP
- Don't create separate parsers per file format (use unified pipeline)
- Don't modify `docs/` without explicit instruction

## Backend Stack
- Python 3.11+ / FastAPI / Pydantic v2 / Uvicorn
- Motor (async MongoDB driver) → MongoDB Atlas
- Pandas, Pandera, SciPy, statsmodels, pingouin
- Docling (unified ingestion, fallback to pandas for CSV)
- LiteLLM (LLM gateway)
- OpenTelemetry + structlog

## Frontend Stack
- Next.js 14+ (App Router) / React 18+ / TypeScript
- shadcn/ui + Tailwind CSS
- Recharts (visualization)
- Lucide React (icons)

## Key Endpoints
- `GET /api/health` → `{"status": "ok"}`
- `POST /api/sessions` → Ingesta Medallion (Bronze/Silver). Devuelve SessionResponse.
- `GET /api/sessions/{id}/report` → Devuelve AnalysisReport completo.
- `POST /api/analyze` → Compatibilidad (Findings + ChartSpecs as artifacts).

## Artifacts & Components
- **Finding**: Hallazgo de calidad o estadístico (ID, Categoría, Severidad, Explicación).
- **ChartSpec**: Especificación agnóstica de gráfico (data, x_axis, y_axis, series).
- **DatasetOverview**: Resumen de filas, columnas, nulos y tipos.
- **ColumnProfile**: Estadísticas descriptivas detalladas por columna.

## Contract Versioning
All responses include `contract_version: "v1"`.

## Environment Variables
### Backend (.env)
- MONGODB_URI, MONGODB_DB
- LITELLM_API_KEY, LITELLM_MODEL
- CORS_ORIGINS
- OTEL_SERVICE_NAME

### Frontend (.env.local)
- NEXT_PUBLIC_API_BASE_URL (default: http://localhost:8000)

## Product Documentation
- `docs/prd-maestro.md` — Source of truth for the product
- `docs/prd-backend-emergent.md` — Backend operational spec
- `docs/prd-front-v0.md` — Frontend operational spec
- `docs/roadmap-2026.md` — Phase sequence

## Common Commands
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Backend Tests
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm install && npm run dev

# Test upload
curl -X POST http://localhost:8000/sessions -F "file=@datasets/ventas.csv"

# Test analyze
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","query":"Analiza los datos"}'
```

## Working Style
- One task per prompt
- Always specify scope (where to write, where to read)
- Report after each phase, wait for approval before continuing
- If something fails after 2 attempts, stop and ask
- Never auto-refactor files outside your scope
