# Sprint 1.5 — Backend Cleanup + Frontend Features

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver todos los bugs y gaps identificados en el análisis del proyecto: crear el orquestador de pipeline faltante (blocker crítico), corregir la configuración de Redis, limpiar archivos huérfanos, agregar el endpoint de FraudGuard, y conectar el frontend al pipeline async + agregar las tabs de FraudGuard y Data Drift.

**Architecture:**
- Backend: `PipelineOrchestrator` centraliza el pipeline Bronze→Silver→Gold que antes vivía inline en `sessions.py`. El endpoint `POST /sessions/{id}/fraud` activa FraudGuard on-demand. La configuración de Redis se saca de `Settings` en lugar de estar hardcodeada.
- Frontend: Se agrega polling correcto para el nuevo flujo async (HTTP 202), dos nuevas tabs (FraudGuard, DataDrift), y los métodos faltantes en `api.ts`.

**Tech Stack:** FastAPI, PyMongo, ARQ, Redis, PydanticAI, Next.js 16, React 19, TypeScript, Tailwind v4

---

## Mapa de Archivos

### Crear
- `backend/app/services/pipeline_orchestrator.py` — Orquesta Bronze→Silver→Gold para el worker ARQ
- `backend/app/api/routes/fraud.py` — Endpoint `POST /sessions/{id}/fraud`
- `frontend/src/components/FraudGuardPanel.tsx` — Tab UI para el reporte de fraude
- `frontend/src/components/DataDriftPanel.tsx` — Tab UI para comparación de sesiones

### Modificar
- `backend/app/core/config.py` — Agregar `redis_host`, `redis_port`
- `backend/app/services/job_queue.py` — Leer Redis desde settings
- `backend/app/worker.py` — Leer Redis desde settings
- `backend/app/main.py` — Registrar `fraud.router`
- `frontend/src/types/contracts.ts` — Agregar `"queued"` al status, tipos `FraudReport`, `CompareResult`, `UsageStats`
- `frontend/src/lib/api.ts` — Agregar `getSessionStatus()`, `deleteSession()`, `compareSessions()`, `getFraudReport()`, `getMyUsage()`
- `frontend/src/app/workspace/page.tsx` — Corregir `handleUploadComplete` + agregar tabs FraudGuard/Drift/Delete

### Eliminar
- `docs/base.py` — Copia huérfana de `BaseIngestionOrchestrator`
- `backend/distributed_strategy.py` — Duplicado en raíz de backend (versión real en `app/services/ingestion/`)
- `backend/app/api/routes/base.py` — Copia idéntica de `docs/base.py`, sin registrar en ningún router

---

## Task 1: Crear PipelineOrchestrator (BLOCKER CRÍTICO)

> El worker ARQ importa `app.services.pipeline_orchestrator.PipelineOrchestrator` que no existe.
> Sin este archivo, el worker no puede arrancar → ningún archivo puede procesarse.

**Files:**
- Create: `backend/app/services/pipeline_orchestrator.py`
- Test: `backend/tests/test_pipeline_orchestrator.py`

- [ ] **Step 1: Escribir el test que verifica que el worker puede importar el orquestador**

```python
# backend/tests/test_pipeline_orchestrator.py
import pytest

def test_pipeline_orchestrator_importable():
    """Verifica que el módulo existe y la clase es importable (lo mínimo para que ARQ no rompa)."""
    from app.services.pipeline_orchestrator import PipelineOrchestrator
    assert callable(PipelineOrchestrator)

def test_pipeline_orchestrator_has_run_method():
    from app.services.pipeline_orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    assert hasattr(orchestrator, 'run_full_pipeline')
    import asyncio
    assert asyncio.iscoroutinefunction(orchestrator.run_full_pipeline)
```

- [ ] **Step 2: Correr el test para confirmar que falla**

```bash
cd backend && python -m pytest tests/test_pipeline_orchestrator.py -v
```
Esperado: `FAILED` con `ModuleNotFoundError: No module named 'app.services.pipeline_orchestrator'`

- [ ] **Step 3: Crear `pipeline_orchestrator.py`**

```python
# backend/app/services/pipeline_orchestrator.py
import os
import structlog
from datetime import datetime
from typing import Any, Dict

from app.repositories.mongo import session_repo
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.profiler import ProfilerService
from app.services.docling_quality_gate import DoclingQualityGate
from app.services.finding_builder import FindingBuilder
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.eda_extended import EDAExtendedService
from app.services.llm_service import LLMService
from app.services.schema_validator import SchemaValidator
from app.services.statistical_tests import StatisticalTestsService
from app.services.docling_chunking_service import get_docling_chunking_service
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """
    Orquesta el pipeline completo Bronze → Silver → Gold para una sesión.
    Llamado exclusivamente desde el worker ARQ (app/worker.py).
    """

    def __init__(self):
        self.ingest_service = IngestService()
        self.normalization_service = NormalizationService()
        self.profiler_service = ProfilerService()
        self.quality_gate = DoclingQualityGate()
        self.finding_builder = FindingBuilder()
        self.chart_spec_generator = ChartSpecGenerator()
        self.eda_service = EDAExtendedService()
        self.llm_service = LLMService()
        self.schema_validator = SchemaValidator()
        self.stat_tests_service = StatisticalTestsService()
        self.docling_chunking_service = get_docling_chunking_service()
        self.embedding_service = EmbeddingService()

    async def run_full_pipeline(
        self,
        session_id: str,
        file_path: str,
        filename: str,
        content_type: str,
        table_index: int = 0,
    ) -> None:
        """
        Ejecuta Bronze → Silver → Gold y actualiza el estado de la sesión en MongoDB.
        Limpia el archivo temporal al finalizar (éxito o error).
        """
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # ─── BRONZE ───────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "status": "processing",
                "progress_message": "Bronze: Ingestando documento...",
            })

            quality_result = await self.quality_gate.evaluate(
                file_bytes, filename, content_type
            )

            ingest_result = await self.ingest_service.ingest_file(
                file_bytes, filename, content_type, table_index
            )

            df = self.normalization_service.normalize(ingest_result["df"])

            bronze_doc: Dict[str, Any] = {
                "session_id": session_id,
                "original_filename": filename,
                "ingestion_source": "docling",
                "quality_decision": quality_result.get("decision", "PASS"),
                "schema_version": "v1",
                "narrative_context": ingest_result.get("narrative_context"),
                "tables": ingest_result.get("tables", []),
                "document_metadata": ingest_result.get("document_metadata", {}),
                "provenance_refs": ingest_result.get("provenance_refs", []),
                "created_at": datetime.utcnow().isoformat(),
            }
            await session_repo.save_bronze(session_id, bronze_doc)

            # ─── SILVER ───────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "progress_message": "Silver: Perfilando datos y detectando hallazgos...",
            })

            profile_data = self.profiler_service.profile(df)
            stat_tests = self.stat_tests_service.run_all_tests(df)
            findings = self.finding_builder.build_findings(df, profile_data, stat_tests)

            eda_extras = self.eda_service.run(df)
            if isinstance(eda_extras, dict):
                findings.extend(eda_extras.get("findings", []))

            chart_specs = self.chart_spec_generator.generate(df, profile_data, findings)

            chunks = await self.docling_chunking_service.chunk_document(
                narrative=bronze_doc.get("narrative_context") or "",
                tables=bronze_doc.get("tables", []),
                session_id=session_id,
            )

            findings_dicts = [
                f.model_dump() if hasattr(f, "model_dump") else dict(f)
                for f in findings
            ]
            chunks_dicts = [
                c.model_dump() if hasattr(c, "model_dump") else dict(c)
                for c in chunks
            ]

            await self.embedding_service.index_hybrid_sources(
                findings=findings_dicts,
                chunks=chunks_dicts,
            )

            silver_doc: Dict[str, Any] = {
                "session_id": session_id,
                "dataset_overview": profile_data.get("dataset_overview", {}),
                "column_profiles": profile_data.get("column_profiles", []),
                "findings": findings_dicts,
                "chart_specs": [
                    c.model_dump() if hasattr(c, "model_dump") else dict(c)
                    for c in chart_specs
                ],
                "data_preview": df.head(50).to_dict(orient="records"),
                "statistical_tests": stat_tests,
                "created_at": datetime.utcnow().isoformat(),
            }
            await session_repo.save_silver(session_id, silver_doc)

            # ─── GOLD ─────────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "progress_message": "Gold: Enriqueciendo con IA...",
            })

            gold_result = await self.llm_service.enrich(
                session_id=session_id,
                findings=findings_dicts,
                dataset_overview=silver_doc["dataset_overview"],
                column_profiles=silver_doc["column_profiles"],
            )

            await session_repo.save_gold(session_id, {
                "session_id": session_id,
                "executive_summary": gold_result.get("executive_summary"),
                "enriched_explanations": gold_result.get("enriched_explanations", {}),
                "llm_cost_usd": gold_result.get("llm_cost_usd", 0.0),
                "llm_model_used": gold_result.get("llm_model_used", ""),
                "llm_calls_count": gold_result.get("llm_calls_count", 0),
                "created_at": datetime.utcnow().isoformat(),
            })

            # ─── FINALIZAR ────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "status": "ready",
                "quality_decision": quality_result.get("decision", "PASS"),
                "finding_count": len(findings_dicts),
                "progress_message": "Pipeline completado exitosamente.",
            })

            logger.info("pipeline_complete", session_id=session_id, findings=len(findings_dicts))

        except Exception as e:
            logger.error("pipeline_failed", session_id=session_id, error=str(e))
            await session_repo.update_session(session_id, {
                "status": "error",
                "progress_message": f"Error en el pipeline: {str(e)}",
            })
            raise

        finally:
            try:
                os.unlink(file_path)
            except OSError:
                pass
```

- [ ] **Step 4: Correr los tests**

```bash
cd backend && python -m pytest tests/test_pipeline_orchestrator.py -v
```
Esperado: `2 passed`

- [ ] **Step 5: Verificar que el worker puede importar el módulo**

```bash
cd backend && python -c "from app.worker import WorkerSettings; print('Worker importable OK')"
```
Esperado: `Worker importable OK`

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/pipeline_orchestrator.py backend/tests/test_pipeline_orchestrator.py
git commit -m "feat(worker): create PipelineOrchestrator — Bronze→Silver→Gold for ARQ"
```

---

## Task 2: Corregir Redis hardcodeado en Settings

> `job_queue.py` y `worker.py` usan `localhost` hardcodeado.
> En Docker, el hostname del servicio Redis es `redis` (nombre del servicio en docker-compose).

**Files:**
- Modify: `backend/app/core/config.py:20` (agregar `redis_host`, `redis_port`)
- Modify: `backend/app/services/job_queue.py:14` (leer de settings)
- Modify: `backend/app/worker.py:56` (leer de settings)

- [ ] **Step 1: Escribir el test**

```python
# backend/tests/test_redis_config.py
def test_redis_settings_come_from_config():
    """Verifica que job_queue usa la configuración centralizada de Settings."""
    from app.services.job_queue import JobQueueService
    from app.core.config import settings
    svc = JobQueueService()
    assert svc.redis_settings.host == settings.redis_host
    assert svc.redis_settings.port == settings.redis_port
```

- [ ] **Step 2: Correr para confirmar fallo**

```bash
cd backend && python -m pytest tests/test_redis_config.py -v
```
Esperado: `FAILED` — el host es `localhost` y settings no tiene `redis_host`.

- [ ] **Step 3: Agregar campos a `config.py`**

En `backend/app/core/config.py`, agregar dentro de la clase `Settings`:

```python
    # Redis (ARQ job queue)
    redis_host: str = "localhost"
    redis_port: int = 6379
```

- [ ] **Step 4: Actualizar `job_queue.py`**

Reemplazar la línea 15 (`self.redis_settings = RedisSettings(host='localhost', port=6379)`) con:

```python
        from app.core.config import settings as _settings
        self.redis_settings = RedisSettings(
            host=_settings.redis_host,
            port=_settings.redis_port,
        )
```

- [ ] **Step 5: Actualizar `worker.py`**

Reemplazar la línea 56 (`redis_settings = RedisSettings(host='localhost', port=6379)`) con:

```python
    @classmethod
    def get_redis_settings(cls):
        from app.core.config import settings
        return RedisSettings(host=settings.redis_host, port=settings.redis_port)

    redis_settings = property(get_redis_settings)
```

> Nota: ARQ lee `WorkerSettings.redis_settings` como atributo de clase. La forma más simple es usar un `classmethod` o simplemente leer settings en tiempo de import:

Alternativa simple para `worker.py` (línea 56):
```python
from app.core.config import settings as _cfg
...
class WorkerSettings:
    functions = [run_pipeline_task]
    redis_settings = RedisSettings(host=_cfg.redis_host, port=_cfg.redis_port)
    max_tries = 3
    job_timeout = 600
```

- [ ] **Step 6: Correr el test**

```bash
cd backend && python -m pytest tests/test_redis_config.py -v
```
Esperado: `PASSED`

- [ ] **Step 7: Agregar `REDIS_HOST=redis` al `.env` de producción y `docker-compose.yml`**

En `backend/.env.example` (crear si no existe) y en cualquier documentación de deploy:
```
REDIS_HOST=redis
REDIS_PORT=6379
```

En `docker-compose.yml`, verificar que el backend tenga `REDIS_HOST=redis` en `environment` o que el `.env` lo contenga.

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/config.py backend/app/services/job_queue.py backend/app/worker.py
git commit -m "fix(config): make Redis host/port configurable via Settings (fixes Docker)"
```

---

## Task 3: Limpiar archivos huérfanos

> Tres archivos son duplicados idénticos sin ningún router que los use.

**Files:**
- Delete: `docs/base.py`
- Delete: `backend/distributed_strategy.py`
- Delete: `backend/app/api/routes/base.py`

- [ ] **Step 1: Confirmar que ningún archivo los importa**

```bash
cd backend && grep -r "from app.api.routes.base\|from distributed_strategy" app/ tests/ --include="*.py"
grep -r "docs/base" c:/Users/Equipo/data-x --include="*.py" --include="*.ts" --include="*.md"
```
Esperado: ninguna salida (no hay importaciones).

- [ ] **Step 2: Eliminar los tres archivos**

```bash
rm c:/Users/Equipo/data-x/docs/base.py
rm c:/Users/Equipo/data-x/backend/distributed_strategy.py
rm c:/Users/Equipo/data-x/backend/app/api/routes/base.py
```

- [ ] **Step 3: Correr la suite de tests completa para confirmar que nada se rompió**

```bash
cd backend && python -m pytest tests/ -v --tb=short -q
```
Esperado: todos los tests existentes siguen pasando, ningún `ImportError`.

- [ ] **Step 4: Commit**

```bash
git add -u
git commit -m "chore: remove orphan duplicate files (docs/base.py, distributed_strategy.py, routes/base.py)"
```

---

## Task 4: Endpoint `POST /sessions/{id}/fraud`

> FraudGuardOrchestrator está implementado pero no tiene ningún endpoint HTTP.
> La UI de FraudGuard del frontend necesita este endpoint para mostrar resultados.

**Files:**
- Create: `backend/app/api/routes/fraud.py`
- Modify: `backend/app/main.py` (registrar el router)
- Modify: `backend/app/repositories/mongo.py` (agregar `save_fraud` y `get_fraud`)
- Test: `backend/tests/test_fraud_endpoint.py`

- [ ] **Step 1: Agregar `save_fraud` y `get_fraud` al repositorio MongoDB**

En `backend/app/repositories/mongo.py`, agregar los siguientes métodos a la clase `SessionRepository`:

```python
    async def save_fraud(self, session_id: str, data: dict) -> None:
        await self.db.fraud_reports.replace_one(
            {"session_id": session_id},
            data,
            upsert=True,
        )

    async def get_fraud(self, session_id: str) -> dict | None:
        doc = await self.db.fraud_reports.find_one({"session_id": session_id})
        if doc:
            doc.pop("_id", None)
        return doc
```

- [ ] **Step 2: Escribir el test del endpoint**

```python
# backend/tests/test_fraud_endpoint.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def auth_headers():
    """Genera un token JWT válido para tests."""
    from app.services.auth_service import auth_service
    token = auth_service.create_access_token("test-user-id", "test@test.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_fraud_endpoint_returns_404_for_unknown_session(auth_headers):
    with patch("app.api.routes.fraud.session_repo") as mock_repo:
        mock_repo.get_session = AsyncMock(return_value=None)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/sessions/nonexistent/fraud", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_fraud_endpoint_returns_cached_report(auth_headers):
    fake_report = {
        "session_id": "sess_test",
        "risk_score": 12.5,
        "risk_level": "LOW",
        "findings": [],
        "disclaimer": "test",
        "generated_at": "2026-01-01T00:00:00",
    }
    with patch("app.api.routes.fraud.session_repo") as mock_repo:
        mock_repo.get_session = AsyncMock(return_value={
            "session_id": "sess_test",
            "user_id": "test-user-id",
            "status": "ready",
        })
        mock_repo.get_fraud = AsyncMock(return_value=fake_report)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/sessions/sess_test/fraud", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_score"] == 12.5
    assert body["risk_level"] == "LOW"
```

- [ ] **Step 3: Correr test para confirmar fallo**

```bash
cd backend && python -m pytest tests/test_fraud_endpoint.py -v
```
Esperado: `FAILED` — router no existe, returns 404 on all routes.

- [ ] **Step 4: Crear `backend/app/api/routes/fraud.py`**

```python
# backend/app/api/routes/fraud.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.repositories.mongo import session_repo
from app.api.dependencies import get_current_user
from app.services.fraud_guard import FraudGuardOrchestrator
from app.schemas.fraud import FraudReport

router = APIRouter()
fraud_guard = FraudGuardOrchestrator()


@router.post(
    "/{session_id}/fraud",
    response_model=FraudReport,
    summary="Ejecutar análisis FraudGuard",
    description=(
        "Ejecuta las 4 capas forenses (PDF forensics, ELA, Benford, LATAM fiscal) "
        "sobre el documento de la sesión. El resultado se cachea en MongoDB."
    ),
)
async def run_fraud_analysis(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "Sesión no encontrada"},
        )

    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(
            status_code=403,
            content={"error_code": "ACCESS_DENIED", "message": "Sin permiso"},
        )

    # Devolver caché si ya se calculó
    cached = await session_repo.get_fraud(session_id)
    if cached:
        return cached

    # Obtener datos de la sesión para ejecutar FraudGuard
    bronze = await session_repo.get_bronze(session_id)
    silver = await session_repo.get_silver(session_id)

    import pandas as pd
    df = pd.DataFrame(silver.get("data_preview", [])) if silver else pd.DataFrame()
    document_text = bronze.get("narrative_context", "") if bronze else ""

    report = await fraud_guard.analyze(
        session_id=session_id,
        df=df if not df.empty else None,
        document_text=document_text,
    )

    report_dict = report.model_dump(mode="json")
    report_dict["session_id"] = session_id
    await session_repo.save_fraud(session_id, report_dict)

    return report
```

- [ ] **Step 5: Registrar el router en `main.py`**

En `backend/app/main.py`, agregar:

```python
from app.api.routes import health, sessions, analyze, reports, auth, fraud
```

Y después de los otros `include_router`:

```python
app.include_router(fraud.router, prefix="/api/sessions", tags=["fraud"])
```

- [ ] **Step 6: Correr los tests**

```bash
cd backend && python -m pytest tests/test_fraud_endpoint.py -v
```
Esperado: `2 passed`

- [ ] **Step 7: Correr suite completa**

```bash
cd backend && python -m pytest tests/ -v -q
```
Esperado: todos los tests anteriores siguen pasando.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/routes/fraud.py backend/app/main.py backend/app/repositories/mongo.py backend/tests/test_fraud_endpoint.py
git commit -m "feat(fraud): add POST /sessions/{id}/fraud endpoint with MongoDB caching"
```

---

## Task 5: Corregir tipos en `contracts.ts` (frontend)

> `SessionResponse.status` no incluye `"queued"` — TypeScript lanzará errores
> cuando el backend retorne `{status: "queued"}` tras el upload async.
> También faltan los tipos para FraudReport, CompareResult y UsageStats.

**Files:**
- Modify: `frontend/src/types/contracts.ts`

- [ ] **Step 1: Actualizar `SessionResponse.status`**

En `contracts.ts`, localizar:

```typescript
export interface SessionResponse {
  session_id: string;
  status: 'created' | 'processing' | 'ready' | 'error';
```

Reemplazar con:

```typescript
export interface SessionResponse {
  session_id: string;
  status: 'queued' | 'created' | 'processing' | 'ready' | 'error';
  progress_message?: string;
```

- [ ] **Step 2: Agregar tipos de FraudGuard al final del archivo**

```typescript
// ============================================
// FraudGuard Types
// ============================================

export type FraudLayer =
  | "pdf_forensics"
  | "visual_forensics"
  | "numeric_semantic"
  | "fiscal_validation";

export type FraudSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface FraudFinding {
  layer: FraudLayer;
  indicator: string;
  severity: FraudSeverity;
  evidence: string;
  page?: number;
  confidence: number;
}

export interface FraudReport {
  session_id: string;
  risk_score: number;
  risk_level: FraudSeverity;
  findings: FraudFinding[];
  disclaimer: string;
  generated_at: string;
}

// ============================================
// Compare / Drift Types
// ============================================

export interface CompareResult {
  session_current: string;
  session_baseline: string;
  overview_diff: {
    row_count_change: number;
    null_percent_change: number;
  };
  findings_diff: {
    new_findings_count: number;
    resolved_findings_count: number;
    new_findings: Finding[];
    resolved_findings: Finding[];
  };
}

// ============================================
// Usage / Cost Types
// ============================================

export interface UsageStats {
  user_id: string;
  total_sessions: number;
  total_cost_usd: number;
  total_tokens: number;
  total_processing_time_ms: number;
}
```

- [ ] **Step 3: Verificar que TypeScript compila sin errores**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: ningún error de tipos.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/contracts.ts
git commit -m "feat(frontend/types): add queued status, FraudReport, CompareResult, UsageStats"
```

---

## Task 6: Agregar métodos faltantes a `api.ts`

> El frontend no tiene métodos para: status polling ligero, delete session,
> compare sessions, get fraud report, get usage stats.

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Agregar los cinco métodos faltantes al objeto `api`**

En `frontend/src/lib/api.ts`, dentro del objeto `export const api = { ... }`, agregar al final (antes del cierre `}`):

```typescript
  async getSessionStatus(sessionId: string): Promise<{
    session_id: string;
    status: string;
    progress_message: string;
    quality_decision?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/status`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse(res);
  },

  async deleteSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { ...getAuthHeaders() },
    });
    await handleResponse<{ message: string }>(res);
  },

  async compareSessions(currentSessionId: string, baselineSessionId: string): Promise<import('@/types/contracts').CompareResult> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${currentSessionId}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ target_session_id: baselineSessionId }),
    });
    return handleResponse(res);
  },

  async getFraudReport(sessionId: string): Promise<import('@/types/contracts').FraudReport> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/fraud`, {
      method: 'POST',
      headers: { ...getAuthHeaders() },
    });
    return handleResponse(res);
  },

  async getMyUsage(): Promise<import('@/types/contracts').UsageStats> {
    const res = await fetch(`${API_BASE_URL}/api/auth/me/usage`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse(res);
  },
```

- [ ] **Step 2: Verificar compilación TypeScript**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(frontend/api): add getSessionStatus, deleteSession, compareSessions, getFraudReport, getMyUsage"
```

---

## Task 7: Corregir flujo de upload async en el workspace

> `handleUploadComplete` llama directamente a `loadReport()` ignorando que la sesión
> llega en estado `"queued"`. Esto causa un error 404 al intentar cargar el reporte
> antes de que el pipeline ARQ haya terminado.
> También usar `getSessionStatus` (endpoint ligero) en lugar de `getSession` (endpoint pesado) para polling.

**Files:**
- Modify: `frontend/src/app/workspace/page.tsx`

- [ ] **Step 1: Corregir `handleUploadComplete`**

Localizar en `workspace/page.tsx`:

```typescript
  const handleUploadComplete = (sessionRes: SessionResponse) => {
    setSession(sessionRes);
    router.push(`/workspace?session_id=${sessionRes.session_id}`);
    loadReport(sessionRes.session_id);
  };
```

Reemplazar con:

```typescript
  const handleUploadComplete = (sessionRes: SessionResponse) => {
    setSession(sessionRes);
    router.push(`/workspace?session_id=${sessionRes.session_id}`);
    // Si la sesión llega en "queued" (pipeline async), iniciar polling
    if (sessionRes.status === 'queued' || sessionRes.status === 'processing') {
      setState('uploading');
      pollUntilReady(sessionRes.session_id);
    } else if (sessionRes.status === 'ready') {
      loadReport(sessionRes.session_id);
    }
  };
```

- [ ] **Step 2: Agregar función `pollUntilReady` como `useCallback`**

Agregar después de `loadSession` y antes de `handleUploadComplete`:

```typescript
  const pollUntilReady = useCallback(async (sid: string) => {
    const poll = async () => {
      try {
        const statusData = await api.getSessionStatus(sid);
        if (statusData.status === 'ready') {
          const sessionData = await api.getSession(sid);
          setSession(sessionData);
          loadReport(sid);
        } else if (statusData.status === 'error') {
          setError({ title: 'Error en el pipeline', desc: statusData.progress_message || 'El procesamiento falló.' });
          setState('error');
        } else {
          // Still processing — show progress message
          setSession(prev => prev ? {
            ...prev,
            status: statusData.status as SessionResponse['status'],
          } : prev);
          setTimeout(poll, 2500);
        }
      } catch (e) {
        console.error('Polling error', e);
        setTimeout(poll, 5000); // Retry más lento en caso de error de red
      }
    };
    poll();
  }, [loadReport]);
```

- [ ] **Step 3: Actualizar `loadSession` para usar el endpoint de status en el polling**

Localizar el bloque `else` en `loadSession` (la parte que hace polling con `setTimeout`):

```typescript
      } else {
        // Polling simple si está procesando
        setTimeout(() => {
          const poll = async () => {
```

Reemplazar todo ese bloque `else` con:

```typescript
      } else {
        // Delegar al polling optimizado usando el endpoint ligero /status
        pollUntilReady(sid);
      }
```

- [ ] **Step 4: Actualizar el mensaje de progreso en el loading state para mostrar `progress_message`**

Localizar:
```typescript
              {state === 'uploading' ? 'Ingestando y validando esquema...' : 'Generando hallazgos enriquecidos con IA...'}
```

Reemplazar con:
```typescript
              {session?.progress_message
                ? session.progress_message
                : state === 'uploading'
                  ? 'Iniciando pipeline de análisis...'
                  : 'Generando hallazgos enriquecidos con IA...'}
```

- [ ] **Step 5: Verificar compilación**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/workspace/page.tsx
git commit -m "fix(frontend/workspace): fix upload flow for async 202 — proper polling via /status endpoint"
```

---

## Task 8: Componente `FraudGuardPanel`

> FraudGuard es el diferenciador más potente del producto y su UI no existe.

**Files:**
- Create: `frontend/src/components/FraudGuardPanel.tsx`

- [ ] **Step 1: Crear el componente**

```tsx
// frontend/src/components/FraudGuardPanel.tsx
"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { FraudReport, FraudSeverity } from "@/types/contracts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, ShieldCheck, Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

const SEVERITY_COLORS: Record<FraudSeverity, string> = {
  LOW: "bg-green-100 text-green-800 border-green-200",
  MEDIUM: "bg-yellow-100 text-yellow-800 border-yellow-200",
  HIGH: "bg-orange-100 text-orange-800 border-orange-200",
  CRITICAL: "bg-red-100 text-red-800 border-red-200",
};

const LAYER_LABELS: Record<string, string> = {
  pdf_forensics: "Forense PDF",
  visual_forensics: "Análisis Visual (ELA)",
  numeric_semantic: "Ley de Benford",
  fiscal_validation: "Validación Fiscal LATAM",
};

export function FraudGuardPanel({ sessionId }: { sessionId: string }) {
  const [report, setReport] = useState<FraudReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFraudReport(sessionId);
      setReport(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al ejecutar FraudGuard";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-muted-foreground">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-sm font-medium">Ejecutando las 4 capas de análisis forense...</p>
        <p className="text-xs">PDF Forensics · ELA · Benford · Fiscal LATAM</p>
      </div>
    );
  }

  if (!report) {
    return (
      <Card className="border-dashed border-2">
        <CardContent className="flex flex-col items-center justify-center py-16 gap-6">
          <ShieldAlert className="w-16 h-16 text-muted-foreground/50" />
          <div className="text-center space-y-2">
            <h3 className="font-semibold text-lg">Análisis FraudGuard</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Ejecuta las 4 capas forenses: metadatos PDF, análisis visual de manipulación (ELA),
              Ley de Benford para datos numéricos, y validación fiscal LATAM.
            </p>
          </div>
          <Button onClick={runAnalysis} disabled={loading} className="gap-2">
            <ShieldAlert className="w-4 h-4" />
            Ejecutar FraudGuard
          </Button>
          {error && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" /> {error}
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  const riskColor = SEVERITY_COLORS[report.risk_level];

  return (
    <div className="space-y-6">
      {/* Risk Score Header */}
      <Card className={`border-2 ${report.risk_level === "LOW" ? "border-green-200" : report.risk_level === "CRITICAL" ? "border-red-400" : "border-orange-300"}`}>
        <CardContent className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            {report.risk_level === "LOW" ? (
              <ShieldCheck className="w-12 h-12 text-green-600" />
            ) : (
              <ShieldAlert className="w-12 h-12 text-red-600" />
            )}
            <div>
              <p className="text-sm text-muted-foreground font-medium">Puntuación de Riesgo</p>
              <p className="text-4xl font-extrabold">{report.risk_score.toFixed(1)}<span className="text-lg font-normal text-muted-foreground">/100</span></p>
            </div>
          </div>
          <Badge className={`text-base px-4 py-2 ${riskColor}`}>
            {report.risk_level}
          </Badge>
        </CardContent>
      </Card>

      {/* Findings by Layer */}
      {report.findings.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-10 gap-3 text-muted-foreground">
            <ShieldCheck className="w-10 h-10 text-green-500" />
            <p className="font-medium">No se detectaron indicadores de fraude</p>
            <p className="text-xs">{report.disclaimer}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <h3 className="font-semibold text-base">
            {report.findings.length} Indicador{report.findings.length !== 1 ? "es" : ""} Detectado{report.findings.length !== 1 ? "s" : ""}
          </h3>
          {report.findings.map((finding, idx) => (
            <Card key={idx} className="border">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      {LAYER_LABELS[finding.layer] || finding.layer}
                    </p>
                    <CardTitle className="text-base mt-0.5">{finding.indicator}</CardTitle>
                  </div>
                  <Badge className={SEVERITY_COLORS[finding.severity]}>{finding.severity}</Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-2">
                <p className="text-sm text-muted-foreground">{finding.evidence}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {finding.page && <span>Página {finding.page}</span>}
                  <span>Confianza: {(finding.confidence * 100).toFixed(0)}%</span>
                </div>
              </CardContent>
            </Card>
          ))}
          <p className="text-xs text-muted-foreground italic">{report.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar compilación**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/FraudGuardPanel.tsx
git commit -m "feat(frontend): add FraudGuardPanel component — 4-layer forensic analysis UI"
```

---

## Task 9: Componente `DataDriftPanel`

> `POST /sessions/{id}/compare` existe en el backend pero no hay UI que lo consuma.

**Files:**
- Create: `frontend/src/components/DataDriftPanel.tsx`

- [ ] **Step 1: Crear el componente**

```tsx
// frontend/src/components/DataDriftPanel.tsx
"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { CompareResult, SessionListItem } from "@/types/contracts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, TrendingDown, Minus, GitCompareArrows, AlertCircle } from "lucide-react";

interface DataDriftPanelProps {
  sessionId: string;
  sessions: SessionListItem[];
}

export function DataDriftPanel({ sessionId, sessions }: DataDriftPanelProps) {
  const [baselineId, setBaselineId] = useState<string>("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const otherSessions = sessions.filter(
    (s) => s.session_id !== sessionId && s.status === "ready"
  );

  const runComparison = async () => {
    if (!baselineId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.compareSessions(sessionId, baselineId);
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al comparar sesiones");
    } finally {
      setLoading(false);
    }
  };

  if (otherSessions.length === 0) {
    return (
      <Card className="border-dashed border-2">
        <CardContent className="flex flex-col items-center py-16 gap-3 text-muted-foreground">
          <GitCompareArrows className="w-12 h-12 opacity-40" />
          <p className="font-medium">Necesitas al menos 2 sesiones para comparar</p>
          <p className="text-sm">Sube otro dataset para habilitar la comparación de drift.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Selector de sesión base */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <GitCompareArrows className="w-4 h-4 text-primary" />
            Seleccionar Sesión Base
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3 items-end">
          <div className="flex-1">
            <select
              value={baselineId}
              onChange={(e) => setBaselineId(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">— Seleccionar sesión base —</option>
              {otherSessions.map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.filename} — {new Date(s.created_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={runComparison} disabled={!baselineId || loading}>
            {loading ? "Comparando..." : "Comparar"}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <div className="flex items-center gap-2 text-destructive text-sm p-3 bg-destructive/10 rounded-md">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Overview diff */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Cambio en filas</p>
                <div className="flex items-center gap-2 mt-1">
                  {result.overview_diff.row_count_change > 0
                    ? <TrendingUp className="w-4 h-4 text-green-500" />
                    : result.overview_diff.row_count_change < 0
                    ? <TrendingDown className="w-4 h-4 text-red-500" />
                    : <Minus className="w-4 h-4 text-muted-foreground" />}
                  <span className="text-2xl font-bold">
                    {result.overview_diff.row_count_change > 0 ? "+" : ""}
                    {result.overview_diff.row_count_change}
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Cambio en % nulos</p>
                <div className="flex items-center gap-2 mt-1">
                  {result.overview_diff.null_percent_change > 0
                    ? <TrendingUp className="w-4 h-4 text-red-500" />
                    : result.overview_diff.null_percent_change < 0
                    ? <TrendingDown className="w-4 h-4 text-green-500" />
                    : <Minus className="w-4 h-4 text-muted-foreground" />}
                  <span className="text-2xl font-bold">
                    {result.overview_diff.null_percent_change > 0 ? "+" : ""}
                    {(result.overview_diff.null_percent_change * 100).toFixed(2)}%
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* New findings */}
          {result.findings_diff.new_findings_count > 0 && (
            <Card className="border-orange-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-orange-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {result.findings_diff.new_findings_count} Nuevos Hallazgos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.findings_diff.new_findings.map((f) => (
                  <div key={f.finding_id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <span className="text-sm font-medium">{f.title}</span>
                    <Badge variant="outline" className="text-xs">{f.severity}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Resolved findings */}
          {result.findings_diff.resolved_findings_count > 0 && (
            <Card className="border-green-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-green-700 flex items-center gap-2">
                  <TrendingDown className="w-4 h-4" />
                  {result.findings_diff.resolved_findings_count} Hallazgos Resueltos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.findings_diff.resolved_findings.map((f) => (
                  <div key={f.finding_id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <span className="text-sm font-medium line-through text-muted-foreground">{f.title}</span>
                    <Badge variant="outline" className="text-xs opacity-60">{f.severity}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result.findings_diff.new_findings_count === 0 && result.findings_diff.resolved_findings_count === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground text-sm">
                No hay cambios en los hallazgos entre las dos sesiones.
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verificar compilación**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DataDriftPanel.tsx
git commit -m "feat(frontend): add DataDriftPanel component — session comparison UI"
```

---

## Task 10: Conectar nuevas tabs en el Workspace + Delete button

> Registrar FraudGuardPanel y DataDriftPanel como tabs navegables.
> Agregar botón de eliminar sesión en `SessionHistory`.

**Files:**
- Modify: `frontend/src/app/workspace/page.tsx`
- Modify: `frontend/src/components/SessionHistory.tsx`

- [ ] **Step 1: Agregar imports en `workspace/page.tsx`**

Localizar la sección de imports de componentes y agregar:

```typescript
import { FraudGuardPanel } from '@/components/FraudGuardPanel';
import { DataDriftPanel } from '@/components/DataDriftPanel';
```

También agregar el import del ícono Lucide:

```typescript
import {
  ..., // los que ya están
  ShieldAlert,
  GitCompareArrows,
} from 'lucide-react';
```

- [ ] **Step 2: Agregar estado para las sesiones disponibles (para DataDriftPanel)**

Después de `const [activeTab, setActiveTab] = useState<string>('overview');`, agregar:

```typescript
  const [availableSessions, setAvailableSessions] = useState<import('@/types/contracts').SessionListItem[]>([]);

  useEffect(() => {
    api.listSessions().then(data => setAvailableSessions(data.items)).catch(() => {});
  }, []);
```

- [ ] **Step 3: Agregar las dos entradas de navegación en el sidebar nav**

Localizar el último `<NavItem>` del sidebar (el de "Trazabilidad") y agregar después:

```tsx
                <NavItem
                  label="FraudGuard"
                  icon={ShieldAlert}
                  active={activeTab === 'fraud'}
                  onClick={() => setActiveTab('fraud')}
                />
                <NavItem
                  label="Data Drift"
                  icon={GitCompareArrows}
                  active={activeTab === 'drift'}
                  onClick={() => setActiveTab('drift')}
                />
```

- [ ] **Step 4: Agregar los paneles de contenido**

Después del bloque `{activeTab === 'document' && ...}` y antes del cierre del `<div className="lg:col-span-9 ...">`, agregar:

```tsx
              {activeTab === 'fraud' && report && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-primary" />
                    FraudGuard — Análisis Forense
                  </h2>
                  <FraudGuardPanel sessionId={report.session_id} />
                </section>
              )}

              {activeTab === 'drift' && report && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <GitCompareArrows className="w-5 h-5 text-primary" />
                    Comparación de Sesiones — Data Drift
                  </h2>
                  <DataDriftPanel
                    sessionId={report.session_id}
                    sessions={availableSessions}
                  />
                </section>
              )}
```

- [ ] **Step 5: Agregar botón de eliminar en `SessionHistory.tsx`**

En `frontend/src/components/SessionHistory.tsx`, el componente recibe `onSelectSession`. Necesitamos agregar un prop `onDeleteSession` opcional.

Agregar al interface de props:

```typescript
interface SessionHistoryProps {
  onSelectSession: (sessionId: string) => void;
  onDeleteSession?: (sessionId: string) => void;
  currentSessionId?: string;
}
```

Dentro del componente, agregar un botón de borrar en el render de cada sesión (localizar el elemento que muestra cada sesión en la lista y agregar):

```tsx
{onDeleteSession && (
  <button
    onClick={(e) => {
      e.stopPropagation();
      if (confirm('¿Eliminar esta sesión permanentemente?')) {
        api.deleteSession(session.session_id)
          .then(() => onDeleteSession(session.session_id))
          .catch(console.error);
      }
    }}
    className="p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-colors"
    title="Eliminar sesión"
  >
    <Trash2 className="w-3.5 h-3.5" />
  </button>
)}
```

Agregar el import de `Trash2` de `lucide-react` y el import de `api`.

- [ ] **Step 6: Pasar el callback en workspace**

En `workspace/page.tsx`, en las instancias de `<SessionHistory>`, agregar:

```tsx
<SessionHistory
  onSelectSession={handleSelectSession}
  onDeleteSession={(sid) => {
    // Si se borra la sesión activa, resetear el workspace
    if (sid === session?.session_id) resetWorkspace();
    setAvailableSessions(prev => prev.filter(s => s.session_id !== sid));
  }}
  currentSessionId={session?.session_id}
/>
```

- [ ] **Step 7: Verificar compilación final**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Step 8: Commit final**

```bash
git add frontend/src/app/workspace/page.tsx frontend/src/components/SessionHistory.tsx
git commit -m "feat(frontend/workspace): wire FraudGuard tab, DataDrift tab, delete session button"
```

---

## Verificación Final

- [ ] **Levantar el stack completo**

```bash
cd c:/Users/Equipo/data-x && docker-compose up --build
```

- [ ] **Verificar que el worker ARQ arranca sin ImportError**

```bash
docker-compose logs backend | grep -E "arq|worker|pipeline|ImportError"
```
Esperado: `arq_worker_startup` — sin `ImportError`.

- [ ] **Correr la suite completa de tests del backend**

```bash
cd backend && python -m pytest tests/ -v -q
```
Esperado: todos los tests pasando, 0 failed.

- [ ] **Verificar TypeScript del frontend**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores.

- [ ] **Commit final del informe actualizado**

```bash
git add docs/
git commit -m "docs: update informe-analisis-completo.md with Sprint 1.5 status"
```

---

*Plan generado el 2026-03-29 — Sprint 1.5 Data-X*
