# Data-X — Junie: Refactorizar backend hacia arquitectura v3.0

Pegale todo esto a Junie. Es un prompt largo pero necesario.

---

```
## Contexto
El backend actual funciona pero necesita refactorizarse hacia una arquitectura
más madura definida en el PRD v3.0. Los cambios principales son:

1. Arquitectura Medallion (Bronze/Silver/Gold) para organizar el flujo de datos
2. Finding como unidad central de valor (reemplaza artifacts genéricos)
3. ChartSpec agnóstico a librería frontend
4. Templates estáticos para explicaciones (SIN LiteLLM en Corte 1)
5. AnalysisReport como salida principal
6. Endpoints reorganizados

## Scope
- Escribir solo en: backend/
- Puede leer: frontend/, docs/
- NO tocar: frontend/, docs/

## Plan de refactorización
Hacelo en fases. Commit al final de cada fase. Si algo falla después
de 2 intentos, dejá un TODO y seguí.

=============================================
FASE R1 — NUEVOS SCHEMAS (Medallion + Finding)
=============================================

Reemplazar/refactorizar los schemas en backend/app/schemas/.

### backend/app/schemas/finding.py (CREAR)
```python
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class Evidence(BaseModel):
    metric: str
    value: float | int | str
    threshold: Optional[float | int] = None
    detail: Optional[str] = None

class Finding(BaseModel):
    finding_id: str
    category: Literal[
        "high_null_rate", "duplicate_rows", "constant_column",
        "high_cardinality", "low_cardinality", "type_mismatch",
        "column_stats", "data_quality_warning", "schema_warning"
    ]
    severity: Literal["critical", "warning", "info"]
    title: str
    technical_summary: str
    explanation: str  # Generado por template estático en Corte 1
    impact: Optional[str] = None
    affected_columns: List[str] = []
    evidence: List[Evidence] = []
    recommendations: List[str] = []
```

### backend/app/schemas/chart_spec.py (CREAR)
```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

class AxisSpec(BaseModel):
    key: str
    label: str
    type: Literal["categorical", "numeric", "datetime"] = "categorical"

class SeriesSpec(BaseModel):
    key: str
    label: str
    color_hint: Optional[str] = None

class ChartSpec(BaseModel):
    chart_id: str
    chart_type: Literal["bar", "line", "area", "pie", "histogram", "scatter"]
    title: str
    data: List[Dict[str, Any]]
    x_axis: AxisSpec
    y_axis: Optional[AxisSpec] = None
    series: List[SeriesSpec] = []
```

### backend/app/schemas/medallion.py (CREAR)
```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class BronzeRecord(BaseModel):
    """Raw ingestion data"""
    session_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    ingestion_source: Literal["docling", "pandas_fallback"]
    quality_decision: Literal["accept", "warning", "reject"]
    quality_scores: Dict[str, Any] = {}
    source_metadata: Dict[str, Any] = {}
    ingested_at: datetime

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    count: int
    null_count: int
    null_percent: float
    unique_count: int
    cardinality: float
    # Numéricas
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    # Strings
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None

class DatasetOverview(BaseModel):
    row_count: int
    column_count: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    total_nulls: int
    total_null_percent: float
    duplicate_rows: int
    duplicate_percent: float

class SilverRecord(BaseModel):
    """Processed + EDA results"""
    session_id: str
    dataset_overview: DatasetOverview
    column_profiles: List[ColumnProfile]
    findings: List[Dict[str, Any]]  # List of Finding dicts
    chart_specs: List[Dict[str, Any]]  # List of ChartSpec dicts
    processed_at: datetime
```

### backend/app/schemas/report.py (CREAR)
```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProvenanceInfo(BaseModel):
    source: str
    ingestion_method: str
    quality_decision: str
    processing_steps: List[str] = []
    affected_columns: List[str] = []

class AnalysisReport(BaseModel):
    session_id: str
    status: Literal["completed", "partial", "error"]
    dataset_overview: Dict[str, Any]
    column_profiles: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    chart_specs: List[Dict[str, Any]]
    explanations: Dict[str, str] = {}  # finding_id -> explanation text
    provenance: ProvenanceInfo
    contract_version: str = "v1"
    generated_at: datetime
```

### backend/app/schemas/session.py (MODIFICAR)
Actualizar SessionResponse para reflejar Medallion:
```python
class SessionResponse(BaseModel):
    session_id: str
    status: Literal["created", "processing", "ready", "error"]
    created_at: datetime
    source_metadata: dict
    quality_decision: Optional[str] = None
    dataset_overview: Optional[dict] = None
    finding_count: Optional[int] = None
    contract_version: str = "v1"
```

## Commit
git commit -m "[backend] fase R1: schemas Medallion + Finding + ChartSpec + AnalysisReport"

=============================================
FASE R2 — FINDING BUILDER + TEMPLATES
=============================================

### backend/app/services/finding_builder.py (CREAR)
Clase FindingBuilder que analiza un DataFrame y genera Findings:

Métodos:
- detect_high_null_rate(df, threshold=0.3) -> List[Finding]
  (columnas con >30% nulls → severity warning/critical según %)
- detect_duplicate_rows(df) -> List[Finding]
  (filas duplicadas → warning si >5%, critical si >20%)
- detect_constant_columns(df) -> List[Finding]
  (columnas con 1 solo valor único → info)
- detect_high_cardinality(df, threshold=0.95) -> List[Finding]
  (columnas con cardinality >95% → info)
- detect_low_cardinality(df, threshold=3) -> List[Finding]
  (columnas con <=3 valores únicos → info, posible categórica)
- generate_column_stats(df) -> List[Finding]
  (stats descriptivos por columna como findings tipo info)
- build_all_findings(df) -> List[Finding]
  (ejecuta todos los detectores y devuelve lista consolidada)

Cada Finding debe tener:
- finding_id generado (f"finding_{uuid4().hex[:8]}")
- evidence con métricas concretas
- explanation generado por template
- affected_columns

### backend/app/services/explanation_templates.py (CREAR)
Templates estáticos para explicaciones (SIN LLM):

```python
TEMPLATES = {
    "high_null_rate": "La columna '{column}' tiene {percent}% de valores nulos ({count} de {total}). Esto puede afectar la calidad del análisis.",
    "duplicate_rows": "Se detectaron {count} filas duplicadas ({percent}% del dataset). Considerar deduplicación.",
    "constant_column": "La columna '{column}' tiene un único valor ('{value}'). No aporta información diferenciadora.",
    "high_cardinality": "La columna '{column}' tiene {unique} valores únicos de {total} ({percent}% cardinalidad). Posiblemente sea un identificador.",
    "low_cardinality": "La columna '{column}' tiene solo {unique} valores únicos. Posiblemente sea categórica.",
    "column_stats": "Columna '{column}': tipo {dtype}, {count} valores, rango [{min}, {max}], media {mean}.",
    "data_quality_warning": "{message}",
    "schema_warning": "{message}",
}

def render_explanation(category: str, **kwargs) -> str:
    template = TEMPLATES.get(category, "{message}")
    return template.format(**{k: v for k, v in kwargs.items() if v is not None})
```

## Commit
git commit -m "[backend] fase R2: FindingBuilder + explanation templates"

=============================================
FASE R3 — CHARTSPEC GENERATOR
=============================================

### backend/app/services/chart_spec_generator.py (CREAR)
Clase ChartSpecGenerator que genera ChartSpecs a partir del DataFrame y findings:

Métodos:
- generate_null_distribution_chart(df) -> ChartSpec
  (bar chart: nulls por columna)
- generate_dtype_distribution_chart(df) -> ChartSpec
  (pie chart: distribución de tipos de columna)
- generate_numeric_summary_chart(df) -> ChartSpec
  (bar chart: media por columna numérica)
- generate_top_values_chart(df, column) -> ChartSpec
  (bar chart: top 10 valores de una columna categórica)
- generate_all_charts(df, findings) -> List[ChartSpec]
  (genera charts relevantes según el dataset)

Cada ChartSpec debe tener:
- chart_id generado
- chart_type apropiado
- data como lista de dicts (el frontend mapea a Recharts)
- x_axis y y_axis con key y label
- series con key y label

## Commit
git commit -m "[backend] fase R3: ChartSpec generator"

=============================================
FASE R4 — REFACTORIZAR PIPELINE Y ROUTES
=============================================

### Pipeline Medallion
Refactorizar el flujo en POST /sessions para seguir Bronze → Silver:

```
1. Recibir archivo (upload)
2. BRONZE:
   - Ingerir via Docling/fallback (IngestService existente)
   - Quality gate (DoclingQualityGate existente)
   - Persistir BronzeRecord en MongoDB
3. SILVER:
   - Normalizar (NormalizationService existente)
   - Validar (ValidationService existente)
   - Profiler (ProfilerService existente → genera ColumnProfiles)
   - FindingBuilder → genera Findings
   - ChartSpecGenerator → genera ChartSpecs
   - ExplanationTemplates → genera explicaciones
   - Persistir SilverRecord en MongoDB
4. Devolver SessionResponse con overview + finding_count
```

### Endpoints refactorizados

#### POST /api/sessions (MODIFICAR)
- Ruta cambia a /api/sessions (agregar prefijo /api si no existe)
- Ejecuta pipeline completo Bronze → Silver
- Devuelve SessionResponse actualizado

#### GET /api/sessions/{session_id} (CREAR)
- Devuelve estado de la sesión con overview básico

#### GET /api/sessions/{session_id}/report (CREAR)
- Devuelve AnalysisReport completo:
  - dataset_overview
  - column_profiles
  - findings (con explicaciones)
  - chart_specs
  - provenance
  - contract_version: "v1"

#### POST /analyze (MANTENER pero adaptar)
- Sigue aceptando query libre
- Pero ahora devuelve findings filtrados según la query si es posible
- O devuelve el AnalysisReport completo si la query es genérica
- Esto mantiene compatibilidad con el frontend existente

#### GET /health (MANTENER)
- Sin cambios

### backend/app/main.py (MODIFICAR)
- Registrar nuevas routes
- Mantener las existentes para no romper el frontend

### MongoDB
- Colección "bronze" para BronzeRecords
- Colección "silver" para SilverRecords
- Las colecciones existentes se mantienen

## Commit
git commit -m "[backend] fase R4: pipeline Medallion + endpoints refactorizados"

=============================================
FASE R5 — LIMPIAR LiteLLM DEL CORTE 1
=============================================

El PRD v3.0 dice que LiteLLM está FUERA del Corte 1.
El LLMService existente debe quedar desactivado pero no borrado.

### Qué hacer
- En POST /sessions: NO llamar a LLMService
- En POST /analyze: NO llamar a LLMService para summary
- Usar explanation_templates para todas las explicaciones
- En el summary del AnalysisReport, generar un resumen estático:
  "Dataset '{filename}' con {rows} filas y {cols} columnas.
   Se detectaron {n} findings: {critical} críticos, {warnings} advertencias,
   {info} informativos."
- NO borrar LLMService — dejarlo con comentario:
  # LLMService disponible para Corte 2. Desactivado en Corte 1.
- Quitar litellm de las dependencias obligatorias
  (moverlo a un grupo opcional en requirements.txt o dejarlo comentado)

## Commit
git commit -m "[backend] fase R5: LiteLLM desactivado para Corte 1, templates estáticos"

=============================================
FASE R6 — ACTUALIZAR REQUIREMENTS Y CONFIG
=============================================

### backend/requirements.txt
Actualizar a:
```
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.5.0
python-multipart>=0.0.9
docling>=2.78.0
pandas>=3.0.0
pandera>=0.18.0
pymongo>=4.6.0
motor>=3.3.0
structlog>=24.1.0
python-dotenv>=1.0.0
opentelemetry-api>=1.27.0
opentelemetry-sdk>=1.27.0
opentelemetry-instrumentation-fastapi>=0.48b0
httpx>=0.27.0
# Corte 2+:
# litellm>=1.50.0
# scipy>=1.11.0
# pingouin>=0.5.3
# statsmodels>=0.14.0
```

### Verificar config.py
- Quitar litellm_api_key y litellm_model de settings obligatorios
  (dejarlos como opcionales con default vacío para Corte 2)

## Commit
git commit -m "[backend] fase R6: requirements y config actualizados para Corte 1"

=============================================
FASE R7 — VERIFICACIÓN Y CIERRE
=============================================

### Verificar
1. python -c "from app.main import app; print('OK')"
2. uvicorn app.main:app --reload --port 8000
3. curl http://localhost:8000/health (o /api/health)
4. curl -X POST http://localhost:8000/api/sessions -F "file=@tests/fixtures/ventas.csv"
   → Debe devolver SessionResponse con quality_decision y finding_count
5. curl http://localhost:8000/api/sessions/SESSION_ID/report
   → Debe devolver AnalysisReport con findings, chart_specs, provenance

### Si algo falla
Máximo 2 intentos por error. Si no se resuelve, dejá TODO y seguí.

### Commit final
git add .
git commit -m "[backend] refactorización completa hacia arquitectura v3.0 Medallion"
git push origin main

=============================================
RESUMEN DE CAMBIOS
=============================================

| Antes (Junie) | Después (v3.0) |
|---------------|----------------|
| Artifacts genéricos | Findings como unidad central |
| chart_config artifact | ChartSpec agnóstico |
| LLM para summaries | Templates estáticos (Corte 1) |
| /analyze con query | /sessions/{id}/report |
| Estructura plana | Medallion Bronze/Silver/Gold |
| ArtifactBuilder | FindingBuilder + ChartSpecGenerator |
| LiteLLM activo | LiteLLM desactivado (Corte 2) |

Lo que SE MANTIENE:
- IngestService (Docling + fallback)
- DoclingQualityGate
- NormalizationService
- ValidationService
- ProfilerService
- ProvenanceService
- MongoDB connection
- OpenTelemetry
- structlog
- CORS config
- Health endpoint
```
