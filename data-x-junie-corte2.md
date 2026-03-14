# Data-X — Junie: Corte 2 Completo (Backend + Frontend)

Pegale todo esto a Junie. Primero hace todo el backend, después todo el frontend.

---

```
## Contexto
Corte 1 completo y auditado. Ahora implementamos el Corte 2 que agrega:
- LiteLLM reactivado para explicaciones dinámicas y summaries
- EDA Extendido: correlaciones, outliers, distribuciones
- /api/analyze con motor de razonamiento real
- Gold Layer parcial: explicaciones enriquecidas
- Historial básico de sesiones
- Frontend actualizado para consumir todo

Hacé cada fase, commit al final de cada una. Si algo falla después de
2 intentos, dejá TODO y seguí. Think More activado.

## Scope general
- Backend primero (fases C2B1 a C2B7)
- Frontend después (fases C2F1 a C2F5)

=============================================
PARTE A — BACKEND CORTE 2
=============================================

=========================================
FASE C2B1 — REACTIVAR LiteLLM
=========================================

### Dependencias
Descomentar litellm en backend/requirements.txt:
litellm>=1.50.0

Instalar:
pip install litellm

### backend/app/services/llm_service.py (REACTIVAR)
Quitar el marcador DEPRECATED/desactivado. El servicio debe:

1. Método async generate_explanation(finding: dict, dataset_context: dict) -> str
   - Recibe un Finding y contexto del dataset (overview, column_profiles)
   - Arma un prompt que pide explicar el finding en lenguaje claro
   - Llama a LiteLLM con el modelo configurado en settings
   - Devuelve explicación enriquecida
   - Si LiteLLM falla → fallback a template estático existente

2. Método async generate_executive_summary(report_data: dict) -> str
   - Recibe dataset_overview, findings, column_profiles
   - Arma un prompt que pide un resumen ejecutivo del dataset
   - Devuelve resumen de 3-5 oraciones
   - Si falla → fallback a resumen estático

3. Método async answer_query(query: str, session_context: dict) -> dict
   - Recibe query del usuario + contexto de la sesión (findings, overview, profiles)
   - Arma un prompt con el contexto completo
   - Devuelve: {"answer": str, "relevant_findings": list[str], "confidence": str}
   - Si falla → {"answer": "No se pudo procesar la consulta", ...}

4. Configuración:
   - Usar settings.litellm_model (default: "gpt-4o-mini")
   - Usar settings.litellm_api_key
   - Timeout: 30 segundos
   - Retry: 1 intento
   - Logging con structlog en cada llamada

### backend/app/core/config.py (MODIFICAR)
Restaurar litellm_api_key y litellm_model como campos opcionales:
litellm_api_key: str = ""
litellm_model: str = "gpt-4o-mini"

### backend/.env.example (ACTUALIZAR)
Agregar:
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o-mini

## Commit
git commit -m "[backend] C2B1: LiteLLM reactivado con fallback a templates"

=========================================
FASE C2B2 — EDA EXTENDIDO
=========================================

### Dependencias
Descomentar en requirements.txt:
scipy>=1.11.0
pingouin>=0.5.3

### backend/app/services/eda_extended.py (CREAR)
Clase EDAExtendedService con métodos:

1. compute_correlations(df: DataFrame) -> dict
   - Correlación de Pearson entre todas las columnas numéricas
   - Devuelve: {"matrix": dict, "strong_correlations": list}
   - strong_correlations = pares con |r| > 0.7
   - Usar pandas .corr() + scipy.stats.pearsonr para p-values

2. detect_outliers(df: DataFrame, column: str, method: str = "iqr") -> dict
   - Método IQR: Q1, Q3, IQR, bounds, count de outliers
   - Método z-score: umbral 3, count de outliers
   - Devuelve: {"method": str, "column": str, "outlier_count": int,
     "outlier_percent": float, "bounds": {"lower": float, "upper": float},
     "details": list} (primeros 10 valores outlier)

3. detect_all_outliers(df: DataFrame) -> list[dict]
   - Corre detect_outliers en TODAS las columnas numéricas
   - Devuelve lista de resultados

4. analyze_distributions(df: DataFrame) -> list[dict]
   - Para cada columna numérica: skewness, kurtosis
   - Clasificar: "normal", "right_skewed", "left_skewed", "heavy_tailed"
   - Devuelve: [{"column": str, "skewness": float, "kurtosis": float,
     "classification": str}]

### backend/app/services/finding_builder.py (MODIFICAR)
Agregar nuevos métodos que generen Findings a partir de EDA extendido:

- detect_strong_correlations(correlations: dict) -> list[Finding]
  (pares con |r| > 0.7 → warning, |r| > 0.9 → critical)
- detect_outliers_findings(outlier_results: list) -> list[Finding]
  (columnas con outliers > 5% → warning)
- detect_distribution_issues(distributions: list) -> list[Finding]
  (skewness extrema → info)

Agregar al método build_all_findings() para que incluya estos nuevos findings.

### backend/app/services/explanation_templates.py (ACTUALIZAR)
Agregar templates para nuevos findings:
- "strong_correlation": "Las columnas '{col1}' y '{col2}' tienen una correlación de {value} ({classification}). Esto puede indicar redundancia o dependencia."
- "outlier_detected": "La columna '{column}' tiene {count} outliers ({percent}%) usando método {method}. Rango esperado: [{lower}, {upper}]."
- "skewed_distribution": "La columna '{column}' muestra una distribución {classification} (skewness: {value}). Considerar transformación logarítmica."

## Commit
git commit -m "[backend] C2B2: EDA extendido — correlaciones, outliers, distribuciones"

=========================================
FASE C2B3 — CHARTSPECS EXTENDIDOS
=========================================

### backend/app/services/chart_spec_generator.py (MODIFICAR)
Agregar nuevos generadores:

1. generate_correlation_heatmap(correlations: dict) -> ChartSpec
   - chart_type: "heatmap" (o "scatter" como fallback si heatmap no es viable)
   - Mostrar matriz de correlación

2. generate_outlier_chart(df, column, outlier_result) -> ChartSpec
   - chart_type: "scatter"
   - Puntos normales vs outliers coloreados diferente

3. generate_distribution_chart(df, column) -> ChartSpec
   - chart_type: "histogram"
   - Distribución de valores de la columna

4. Actualizar generate_all_charts() para incluir los nuevos charts
   cuando haya datos de EDA extendido disponibles

## Commit
git commit -m "[backend] C2B3: ChartSpecs extendidos — correlación, outliers, distribución"

=========================================
FASE C2B4 — GOLD LAYER + PIPELINE ACTUALIZADO
=========================================

### backend/app/schemas/medallion.py (MODIFICAR)
Agregar GoldRecord:

class GoldRecord(BaseModel):
    session_id: str
    executive_summary: str
    enriched_explanations: dict  # finding_id -> LLM explanation
    recommendations: list[str]
    generated_at: datetime

### Pipeline actualizado en POST /api/sessions
El flujo ahora es Bronze → Silver → Gold (parcial):

1. Bronze: ingesta + quality gate (sin cambios)
2. Silver: normalización + profiling + EDA base + EDA extendido + findings + charts (ACTUALIZADO)
3. Gold parcial: si LiteLLM está configurado, generar:
   - Executive summary
   - Explicaciones enriquecidas para findings de severity critical y warning
   - Persistir GoldRecord en MongoDB
   Si LiteLLM NO está configurado, saltar Gold y usar templates

### backend/app/schemas/report.py (MODIFICAR)
Agregar a AnalysisReport:
    executive_summary: Optional[str] = None
    enriched_explanations: dict = {}  # finding_id -> LLM explanation (si disponible)

### GET /api/sessions/{id}/report (MODIFICAR)
Incluir executive_summary y enriched_explanations del GoldRecord si existe.

## Commit
git commit -m "[backend] C2B4: Gold Layer parcial + pipeline Bronze→Silver→Gold"

=========================================
FASE C2B5 — /api/analyze REAL
=========================================

### backend/app/api/routes/analyze.py (REESCRIBIR)
El endpoint POST /api/analyze deja de ser un cascarón y se convierte
en un motor de consulta real:

Request: {"session_id": str, "query": str}

Flujo:
1. Recuperar sesión de MongoDB
2. Recuperar SilverRecord (findings, overview, profiles, charts)
3. Recuperar GoldRecord si existe
4. Llamar a LLMService.answer_query(query, context)
5. Filtrar findings relevantes a la query si es posible
6. Devolver:
   {
     "session_id": str,
     "query": str,
     "answer": str,  // respuesta LLM
     "relevant_findings": list[Finding],  // findings filtrados
     "relevant_charts": list[ChartSpec],  // charts relacionados
     "confidence": str,  // "high", "medium", "low"
     "contract_version": "v1"
   }

Si LiteLLM no está configurado:
- answer = "LLM no configurado. Mostrando findings del análisis."
- relevant_findings = todos los findings
- confidence = "n/a"

### backend/app/schemas/analyze.py (ACTUALIZAR)
Actualizar AnalyzeResponse para reflejar la nueva estructura.

## Commit
git commit -m "[backend] C2B5: /api/analyze con motor LLM real"

=========================================
FASE C2B6 — HISTORIAL DE SESIONES
=========================================

### backend/app/api/routes/sessions.py (MODIFICAR)
Agregar endpoint:

GET /api/sessions
- Devuelve lista de sesiones ordenadas por created_at desc
- Cada sesión incluye: session_id, status, source_metadata.filename,
  created_at, finding_count, quality_decision
- Paginación simple: ?limit=20&offset=0

### backend/app/repositories/mongo.py (MODIFICAR)
Agregar método:
- list_sessions(limit: int = 20, offset: int = 0) -> list[dict]

## Commit
git commit -m "[backend] C2B6: historial de sesiones con paginación"

=========================================
FASE C2B7 — VERIFICACIÓN BACKEND CORTE 2
=========================================

1. python -c "from app.main import app; print('OK')"
2. uvicorn app.main:app --reload --port 8000
3. curl http://localhost:8000/api/health
4. curl -X POST http://localhost:8000/api/sessions -F "file=@tests/fixtures/ventas.csv"
   → Debe incluir findings de EDA extendido (correlaciones, outliers si aplica)
5. curl http://localhost:8000/api/sessions/SESSION_ID/report
   → Debe incluir executive_summary (si LiteLLM configurado) y más charts
6. curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"session_id":"SESSION_ID","query":"¿Qué problemas tiene el dataset?"}'
   → Debe devolver respuesta LLM o fallback
7. curl http://localhost:8000/api/sessions?limit=5
   → Debe devolver lista de sesiones

Si algo falla, máximo 2 intentos. Si no se resuelve, TODO y seguí.

## Commit
git commit -m "[backend] C2B7: backend Corte 2 verificado"
git push origin main

=============================================
PARTE B — FRONTEND CORTE 2
=============================================

=========================================
FASE C2F1 — ACTUALIZAR CONTRACTS Y API
=========================================

### frontend/src/types/contracts.ts (ACTUALIZAR)
Agregar/modificar:

- AnalysisReport: agregar executive_summary (string|null), enriched_explanations (Record)
- AnalyzeResponse: nueva estructura con answer, relevant_findings, relevant_charts, confidence
- SessionListItem: {session_id, status, filename, created_at, finding_count, quality_decision}

### frontend/src/lib/api.ts (ACTUALIZAR)
Agregar:
- listSessions(limit?: number, offset?: number) → GET /api/sessions?limit=N&offset=N
  Retorna SessionListItem[]

Actualizar:
- analyze() para devolver la nueva AnalyzeResponse

## Commit
git commit -m "[frontend] C2F1: contracts y API actualizados para Corte 2"

=========================================
FASE C2F2 — COMPONENTES NUEVOS
=========================================

### ExecutiveSummary.tsx (CREAR)
- Recibe executive_summary (string o null)
- Si existe: muestra en un card destacado con ícono de documento
- Si no existe: no renderizar nada
- Diseño: card con borde izquierdo de color, texto formateado

### EnrichedExplanation.tsx (CREAR)
- Se usa dentro de FindingCard
- Si el finding tiene enriched_explanation (del Gold Layer), mostrarla
  en un bloque expandible "Explicación detallada (IA)"
- Si no tiene, mostrar la explanation por template como hasta ahora

### QueryPanel.tsx (CREAR)
- Input de texto para query + botón "Consultar"
- Enviar con Enter
- Loading state mientras procesa
- Mostrar respuesta:
  - answer del LLM en card principal
  - relevant_findings como mini FindingsList
  - confidence badge
- Opción de hacer otra consulta

### SessionHistory.tsx (CREAR)
- Llama a api.listSessions()
- Lista de sesiones con: filename, fecha, finding_count, quality badge
- Click en una sesión → cargar su report
- Diseño: sidebar o lista colapsable

## Commit
git commit -m "[frontend] C2F2: componentes Corte 2 — summary, query, historial"

=========================================
FASE C2F3 — WORKSPACE ACTUALIZADO
=========================================

### Workspace (MODIFICAR)
Agregar al flujo existente:

1. **Executive Summary** — mostrar arriba de todo si existe (después de overview)
2. **Explicaciones enriquecidas** — FindingCard usa enriched_explanation cuando disponible
3. **Query Panel** — sección al final del report para hacer consultas interactivas
4. **Historial** — sidebar o sección que muestre sesiones anteriores
5. **Navegación** — poder ir a una sesión anterior sin perder la actual

### Layout actualizado del reporte:
a) DatasetOverviewCards
b) ExecutiveSummary (si existe)
c) DataPreviewTable
d) FindingsList (con enriched explanations)
e) ChartGallery (ahora con charts de correlación, outliers, distribución)
f) ColumnProfilesTable
g) ProvenancePanel
h) QueryPanel (consulta interactiva)

### Sidebar o sección de historial:
- Mostrar últimas 10 sesiones
- Click para cargar report de cualquier sesión

## Commit
git commit -m "[frontend] C2F3: workspace actualizado con summary, query, historial"

=========================================
FASE C2F4 — UX POLISH CORTE 2
=========================================

- Executive summary con diseño destacado (gradiente suave o borde de color)
- Query panel con placeholder "Preguntá sobre tu dataset..."
- Confidence badge: high=verde, medium=amarillo, low=rojo
- Historial: mostrar fecha relativa ("hace 2 horas", "ayer")
- Charts nuevos (correlación, outliers) se renderizan correctamente en ChartGallery
- Si hay muchos findings (>10), mostrar los primeros 5 y botón "Ver todos"
- Responsive en todos los componentes nuevos

## Commit
git commit -m "[frontend] C2F4: UX polish Corte 2"

=========================================
FASE C2F5 — VERIFICACIÓN E2E Y PUSH
=========================================

1. npm run build (sin errores)
2. npm run dev
3. Con backend corriendo:
   - Subir CSV
   - Verificar executive summary (si LiteLLM configurado)
   - Verificar nuevos charts (correlación, distribución)
   - Verificar nuevos findings (outliers, correlaciones)
   - Usar query panel: escribir "¿Qué problemas tiene el dataset?"
   - Verificar respuesta del LLM o fallback
   - Verificar historial de sesiones
4. Sin backend (solo frontend): verificar que no crashee, muestre errores correctamente

## Commit
git add .
git commit -m "[frontend] Corte 2 completo — LLM, EDA extendido, query, historial"
git push origin main
```
