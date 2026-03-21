# AGENTS.md — Data-X Universal Context

> **Universal agent context file** for Junie, Claude Code, Codex, Copilot, Cursor, and others.
> This file replaces CLAUDE.md. All agents should read this before working on the codebase.

---

## Project Overview

**Data-X** is a data analysis platform with intelligent ingestion, deterministic analysis, and AI-powered insights. It's a monorepo with:

- `backend/` — Python/FastAPI (Owner: Emergent)
- `frontend/` — Next.js/React/TypeScript (Owner: v0)
- `docs/` — Product documentation (read-only)
- `datasets/` — Sample data files

---

## Critical Rules

### Ownership (Non-negotiable)

| Agent | Can Write | Can Read | Notes |
|-------|-----------|----------|-------|
| **Emergent** | `backend/` only | Everything | Backend API, services, data pipeline |
| **v0** | `frontend/` only | Everything | UI components, pages, styling |
| **All agents** | Nothing | `docs/` | Docs are read-only unless explicitly instructed |

**Cross-writing is FORBIDDEN.** Never modify files outside your scope.

### Architecture Principles

1. **Medallion Architecture v4.0**: Bronze (Raw) → Silver (Processed) → Gold (LLM Enrichment)
2. **Backend Calculates, Frontend Renders**: API generates Findings, ChartSpecs, Analysis Context
3. **Finding as Unit of Value**: Each finding has What/So What/Now What structure
4. **Docling-first Ingestion**: Unified pipeline for CSV, XLSX, PDF with fallback to pandas
5. **Pandera Schema Validation**: Automatic schema validation in Silver layer
6. **Deterministic + Statistical**: Profiling, validation, and statistical tests with `pingouin`
7. **LiteLLM Router**: LLM orchestration with fallback chain, local cache, cost tracking
8. **Tests-first**: pytest suite for pipeline integrity
9. **API-first**: System works independently via `/api/*` endpoints
10. **Contracts are Sacred**: Pydantic v2 schemas are source of truth

### What NOT to Do

- Don't duplicate analytical logic in the frontend
- Don't introduce Supabase without explicit approval
- Don't add MCP/FastMCP in the MVP
- Don't create separate parsers per file format
- Don't modify `docs/` without explicit instruction
- Don't cross-write between backend/frontend

---

## Tech Stack

### Backend

- Python 3.11+ / FastAPI / Pydantic v2 / Uvicorn
- Motor (async MongoDB driver) → MongoDB Atlas
- Pandas, Pandera, SciPy, statsmodels, pingouin
- Docling (unified ingestion)
- LiteLLM (LLM gateway)
- OpenTelemetry + structlog
- pytest + pytest-asyncio

### Frontend

- Next.js 14+ (App Router) / React 18+ / TypeScript
- shadcn/ui + Tailwind CSS v4
- Recharts (visualization)
- Lucide React (icons)

---

## Project Structure

```
data-x/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI routers
│   │   ├── core/            # Config, logging, telemetry
│   │   ├── db/              # MongoDB client
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/           # Pydantic models
│   │   └── services/        # Business logic
│   ├── tests/               # pytest suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/        # React components
│   │   │   └── ui/          # shadcn components
│   │   ├── lib/             # Utilities, API client
│   │   └── types/           # TypeScript contracts
│   └── package.json
├── docs/                    # Documentation (read-only)
└── datasets/               # Sample data
```

---

## Setup Commands

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

**Backend (.env)**
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=datax
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
OTEL_SERVICE_NAME=datax-backend
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/sessions` | Upload file, run Medallion pipeline |
| GET | `/api/sessions/{id}` | Get session metadata |
| GET | `/api/sessions/{id}/report` | Get full AnalysisReport |
| POST | `/api/analyze` | RAG query over findings |

---

## Code Conventions

### Python (Backend)

- **Type hints**: Use everywhere
- **Pydantic v2**: All schemas must inherit from BaseModel
- **async/await**: All DB operations must be async
- **structlog**: Use structured logging
- **Error handling**: Return JSONResponse with error_code

```python
# Good
async def get_session(session_id: str) -> SessionResponse:
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "..."}
        )
    return SessionResponse(**session)
```

### TypeScript (Frontend)

- **Strict mode**: Enabled
- **Interfaces**: Define contracts in `types/`
- **Components**: Use function components + hooks
- **Styling**: Tailwind + shadcn/ui
- **API calls**: Centralized in `lib/api.ts`

```typescript
// Good
interface Finding {
  finding_id: string;
  category: 'data_gap' | 'pattern' | 'opportunity';
  severity: 'critical' | 'important' | 'suggestion';
  what: string;
  so_what: string;
  now_what: string;
}
```

---

## Testing Instructions

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v --cov=app
```

**Test categories:**
- `test_health.py` — Health endpoint
- `test_sessions.py` — Session CRUD, upload
- `test_report.py` — Report generation
- `test_services.py` — Unit tests for services

### Frontend Tests

```bash
cd frontend
npm run lint
npm run build  # Must pass without errors
```

---

## PR Instructions

1. **One task per PR**: Don't mix backend and frontend changes
2. **Tests included**: All new features need tests
3. **Type safety**: No `any` types in TypeScript
4. **Lint passing**: Both Python (ruff) and TS (eslint)
5. **Commit format**: `[scope] description`
   - `[backend] Add rate limiting`
   - `[frontend] Add export button`
   - `[docs] Update API reference`

---

## Security Guidelines

### Backend

- **Never** commit `.env` files
- **Always** validate file uploads (size, type, content)
- **Use** parameterized queries (Motor does this)
- **Implement** rate limiting before public exposure
- **Set** restrictive CORS in production

### Frontend

- **Sanitize** user inputs
- **Use** CSP headers
- **Validate** API responses with Zod or similar
- **Store** tokens securely (httpOnly cookies preferred)

---

## Working Style

1. **Read first**: Always read relevant files before modifying
2. **Scope awareness**: Know which agent owns what
3. **Report after phases**: Wait for approval before continuing
4. **Fail fast**: If something fails after 2 attempts, stop and ask
5. **No auto-refactor**: Don't refactor files outside your scope

---

## Artifacts Reference

### Finding Schema

```python
class Finding(BaseModel):
    finding_id: str
    category: str  # data_gap, reliability_risk, pattern, opportunity, quality_issue
    severity: Literal["critical", "important", "suggestion", "insight"]
    title: str
    what: str      # What we found
    so_what: str    # Why it matters
    now_what: str   # What to do
    affected_columns: List[str]
    evidence: List[Evidence]
    confidence: Literal["verified", "high", "moderate"]
```

### ChartSpec Schema

```python
class ChartSpec(BaseModel):
    chart_id: str
    chart_type: Literal["bar", "line", "area", "pie", "histogram", "scatter"]
    title: str
    data: List[Dict]
    x_axis: AxisSpec
    y_axis: Optional[AxisSpec]
    series: List[SeriesSpec]
```

---

## Common Tasks

### Add a New Finding Detector

1. Add method in `backend/app/services/finding_builder.py`
2. Call it from `build_all_findings()`
3. Add template in `explanation_templates.py` (optional)
4. Write test in `tests/test_services.py`

### Add a New API Endpoint

1. Create route in `backend/app/api/routes/`
2. Add to `main.py` router inclusion
3. Create schema in `backend/app/schemas/`
4. Write test
5. Update frontend `lib/api.ts` if needed

### Add a New Frontend Component

1. Create in `frontend/src/components/`
2. Use shadcn/ui components when possible
3. Add to page in `app/`
4. Update types if needed

---

## Troubleshooting

### Backend

| Issue | Solution |
|-------|----------|
| MongoDB connection fails | Check MONGODB_URI, ensure MongoDB running |
| Docling import error | `pip install docling` or check Python version |
| Tests fail | Run with `pytest -v` for detailed output |

### Frontend

| Issue | Solution |
|-------|----------|
| Build fails | Check `next.config.ts`, run `npm install` |
| API not reachable | Check `NEXT_PUBLIC_API_BASE_URL` |
| Type errors | Run `npx tsc --noEmit` |

---

## Resources

- **Strategic Report**: `docs/strategic-report-corte4.md`
- **LiteLLM Plan**: `docs/litellm-integration-plan.md`
- **Docling Plan**: `docs/docling-integration-plan.md`

---

*Last updated: 2026-03-15*
*Version: 1.0*
