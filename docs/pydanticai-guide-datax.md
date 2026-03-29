# PydanticAI para Data-X — Guía Completa
## De los conceptos básicos al diseño de la capa agéntica

*Documento educativo + diseño técnico — 2026-03-23*

---

## Parte 1: Entender los conceptos (sin código todavía)

### ¿Qué es un "agente" de IA?

Olvidate por un momento de robots y ciencia ficción. En el contexto de LLMs, 
un "agente" es simplemente un **loop** que hace esto:

```
1. Recibe una pregunta del usuario
2. Piensa qué necesita para responder
3. Si necesita datos, LLAMA a una herramienta (función Python)
4. Recibe el resultado de la herramienta
5. Piensa si ya puede responder o necesita más datos
6. Si necesita más, vuelve al paso 3
7. Cuando tiene todo, genera la respuesta final
```

La diferencia con un LLM normal (como cuando le preguntás algo a ChatGPT) 
es que el LLM normal responde en un solo paso — no puede "ir a buscar" datos 
en medio de la respuesta. Un agente sí puede.

**Ejemplo concreto en Data-X:**

Sin agente (lo que tenés hoy):
```
Usuario: "Compará las ventas del Q1 con las del Q3"
→ FAISS busca chunks con "ventas Q1 Q3" (una sola búsqueda)
→ LLM recibe los chunks y trata de responder con lo que encontró
→ Problema: puede que no haya un chunk que tenga AMBOS trimestres juntos
```

Con agente:
```
Usuario: "Compará las ventas del Q1 con las del Q3"
→ Agente piensa: "necesito datos de Q1 y datos de Q3 por separado"
→ Llama tool: search_faiss("ventas Q1") → recibe chunks de Q1
→ Llama tool: search_faiss("ventas Q3") → recibe chunks de Q3
→ Llama tool: get_profiling_summary(session_id) → recibe stats
→ Ahora tiene todo → genera respuesta comparativa con evidencia
```

El agente toma **decisiones** sobre qué herramientas usar y en qué orden. 
Pero las herramientas mismas son determinísticas — FAISS siempre devuelve 
los mismos chunks para la misma query, y el ProfilingSummary es un cálculo 
fijo. El agente solo decide el **camino**, no el **cálculo**.

---

### ¿Qué es PydanticAI?

PydanticAI es un framework para construir agentes de IA. Fue creado por 
el mismo equipo que hizo Pydantic (la librería de validación que ya usás 
en todo Data-X con FastAPI).

La filosofía es: **"lo mismo que FastAPI hizo por las APIs web, PydanticAI 
lo hace por los agentes de IA"**. Es minimalista, tipado, y se siente 
como escribir Python normal — no como aprender un framework nuevo.

**¿Por qué PydanticAI y no otros?**

| Framework | Problema para Data-X |
|---|---|
| LangChain | Pesado, inventó su propio lenguaje (LCEL), trae 200+ dependencias |
| CrewAI | Diseñado para "equipos de agentes" conversando — overkill para queries |
| LlamaIndex | Trae su propio RAG y vector store — duplica lo que ya tenés |
| LangGraph | State machines complejas — curva de aprendizaje alta |
| **PydanticAI** | **Minimal, tipado, ya usás Pydantic, no trae RAG propio** |

PydanticAI no trae RAG, no trae vector store, no trae document loader. 
Eso es una ventaja para Data-X porque vos ya tenés todo eso 
(FAISS, HybridChunker, Docling). PydanticAI solo agrega la capa de 
"decisión inteligente" encima.

---

### Los 5 conceptos clave de PydanticAI

#### Concepto 1: Agent (el agente)

Es el objeto principal. Se crea una vez y se reutiliza (como un router 
de FastAPI). Tiene:
- Un modelo LLM (via LiteLLM, OpenRouter, Ollama, etc.)
- Instrucciones (system prompt)
- Un tipo de output (un modelo Pydantic)
- Tools (herramientas que puede llamar)

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class MyResponse(BaseModel):
    answer: str
    confidence: float

agent = Agent(
    'openrouter:anthropic/claude-sonnet-4',  # el modelo
    instructions='Sos un analista de datos experto.',  # system prompt
    output_type=MyResponse,  # lo que DEBE devolver
)
```

**Lo clave**: el `output_type` es un modelo Pydantic. PydanticAI le manda 
el JSON schema al LLM y valida la respuesta. Si el LLM devuelve algo 
que no cumple el schema, PydanticAI le dice "esto está mal, intentá de nuevo" 
automáticamente. Es como Pandera pero para las respuestas del LLM.

#### Concepto 2: Tools (herramientas)

Son funciones Python normales que el agente puede llamar. El agente ve 
el nombre, la descripción (docstring), y los parámetros de la función, 
y decide si necesita llamarla y con qué argumentos.

```python
@agent.tool_plain
def search_documents(query: str, max_results: int = 5) -> list[str]:
    """Busca fragmentos relevantes en los documentos de la sesión."""
    # FAISS search aquí — código determinístico
    results = faiss_index.search(query, k=max_results)
    return [chunk.text for chunk in results]
```

El decorador `@agent.tool_plain` registra la función. El LLM ve:
- Nombre: `search_documents`
- Descripción: "Busca fragmentos relevantes en los documentos de la sesión."
- Parámetros: `query` (string, requerido), `max_results` (int, default 5)

Y decide: "para responder esta pregunta, necesito llamar a 
`search_documents` con query='ventas Q1'".

**Poder oculto de las Tools (Validation con Pydantic V2):**
En Data-X aprovecharemos Pydantic V2 a fondo. Las herramientas pueden usar `@model_validator(mode='after')` y `Field(frozen=True)`. Esto asegura que los datos devueltos por la herramienta al agente sean inmutables y matemáticamente consistentes, eliminando la necesidad de validaciones defensivas complejas dentro del prompt del LLM.

**`tool_plain` vs `tool`**: `tool_plain` es para funciones que no necesitan 
contexto del agente. `tool` es para funciones que sí lo necesitan 
(acceso a dependencias — concepto 3).

#### Concepto 3: Dependencies (dependencias)

Son los datos y servicios que el agente necesita para funcionar. 
Se pasan cuando ejecutás el agente, y las tools pueden acceder a ellos 
via `RunContext`.

Pensalo como la inyección de dependencias de FastAPI (`Depends()`), 
pero para agentes:

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class AnalysisDeps:
    session_id: str
    embedding_service: EmbeddingService
    profiling_summary: ProfilingSummary

agent = Agent(
    'openrouter:anthropic/claude-sonnet-4',
    deps_type=AnalysisDeps,  # el TIPO, no una instancia
)

@agent.tool
async def search_chunks(ctx: RunContext[AnalysisDeps], query: str) -> list[str]:
    """Busca chunks relevantes en FAISS para esta sesión."""
    # ctx.deps tiene acceso a todo lo que pasaste
    results = await ctx.deps.embedding_service.search(
        session_id=ctx.deps.session_id,
        query=query,
    )
    return [r.text for r in results]
```

Cuando ejecutás el agente, le pasás las dependencias concretas:

```python
deps = AnalysisDeps(
    session_id="abc123",
    embedding_service=get_embedding_service(),
    profiling_summary=session.profiling_summary,
)
result = await agent.run("Compará ventas Q1 vs Q3", deps=deps)
```

**¿Por qué es útil?** Porque cada ejecución del agente tiene su propio 
contexto (sesión, usuario, datos). Las tools acceden a ese contexto 
sin usar variables globales. Y en tests, podés mockear las dependencias 
fácilmente.

#### Concepto 4: Output Type (tipo de salida)

Es el modelo Pydantic que define QUÉ debe devolver el agente. 
PydanticAI valida la respuesta automáticamente. Si falla, le pide 
al LLM que lo intente de nuevo (retry con reflection).

```python
class AnalysisResponse(BaseModel):
    """Respuesta estructurada del análisis."""
    answer: str = Field(description="Respuesta en lenguaje natural")
    sources: list[SourceRef] = Field(description="Fuentes utilizadas")
    confidence: float = Field(ge=0, le=1, description="Nivel de confianza")
    requires_more_data: bool = Field(description="Si necesita más contexto")
```

El LLM SIEMPRE devuelve un objeto que cumple este schema. No hay 
"a veces devuelve texto, a veces JSON" — es Pydantic validado.

**Retry with Reflection (Autocorrección):** Si el LLM falla en respetar este esquema (ej. devuelve un `string` donde va un `float`), PydanticAI intercepta el error nativo, y re-lanza el prompt automáticamente diciéndole al modelo su error exacto para que se corrija sin requerir bloques `try/except` de nuestro lado.

Esto es fundamental para Data-X porque significa que la respuesta del 
agente tiene la misma estructura que tus schemas existentes. El frontend 
sabe exactamente qué esperar.

#### Concepto 5: TestModel (testing sin LLM)

PydanticAI tiene un `TestModel` que simula un LLM sin hacer llamadas 
reales. Genera respuestas válidas según el output_type, y podés verificar 
qué tools se llamaron y con qué argumentos.

```python
from pydantic_ai.models.test import TestModel

with agent.override(model=TestModel()):
    result = await agent.run("test query", deps=mock_deps)
    # result.output es un AnalysisResponse válido (generado por TestModel)
    # No se hizo ninguna llamada HTTP a un LLM
```

Esto es perfecto para tus tests con Hypothesis: podés bombardear el 
agente con queries extremas y verificar que nunca crashea, sin gastar 
tokens ni depender de un API externo.

---

### ¿Cómo encaja esto en Data-X?

Recordá la regla fundamental: **el pipeline de ingesta es 100% determinístico. 
La capa agéntica solo opera en queries del usuario.**

```
                    DETERMINÍSTICO (no cambia)
                    ┌─────────────────────────────┐
                    │ Docling → Pandera → Profiler │
                    │ → FindingBuilder → Stats     │
                    │ → Drift → ContextBuilder     │
                    └──────────────┬──────────────┘
                                   │
                    Genera datos precalculados
                                   │
                                   ▼
        AGÉNTICO (solo en queries)
        ┌──────────────────────────────────────┐
        │ Usuario pregunta algo                 │
        │ → PydanticAI Agent decide qué tools   │
        │   necesita para responder             │
        │ → Las tools consultan datos           │
        │   determinísticos (FAISS, profiling,  │
        │   findings)                           │
        │ → El agente arma la respuesta         │
        │   estructurada (Pydantic validated)   │
        └──────────────────────────────────────┘
```

Las tools del agente son **lecturas** sobre datos ya calculados. 
El agente no computa estadísticas, no valida schemas, no detecta drift. 
Solo lee lo que el pipeline determinístico ya calculó y decide cómo 
combinar esa información para responder la pregunta del usuario.

---

## Parte 2: El diseño para Data-X

### 2.1 Las dependencias del agente

Todo lo que el agente necesita para una sesión:

```python
# backend/app/services/analysis_agent.py

from dataclasses import dataclass
from app.services.embedding_service import EmbeddingService
from app.schemas.profiling import ProfilingSummary
from app.schemas.finding import Finding

@dataclass
class AnalysisDeps:
    """
    Dependencias inyectadas al agente para cada ejecución.
    
    Cada campo es un servicio o dato que las tools pueden acceder
    via ctx.deps. Nada es global — todo es por sesión.
    """
    session_id: str
    user_query: str
    
    # Datos precalculados por el pipeline determinístico
    profiling_summary: ProfilingSummary
    findings: list[Finding]
    
    # Servicios para consultar
    embedding_service: EmbeddingService
    
    # Metadata del documento
    document_name: str
    total_pages: int | None = None
```

### 2.2 El schema de respuesta

```python
# backend/app/schemas/analysis_response.py

from pydantic import BaseModel, Field

class SourceReference(BaseModel):
    """Una fuente citada en la respuesta."""
    text: str = Field(description="Fragmento de texto de la fuente")
    page: int | None = Field(default=None, description="Número de página")
    section: str | None = Field(default=None, description="Sección del documento")
    chunk_id: str | None = Field(default=None, description="ID del chunk en FAISS")

class AnalysisResponse(BaseModel):
    """
    Respuesta estructurada del agente de análisis.
    
    PydanticAI valida que el LLM siempre devuelva un objeto
    con esta estructura. Si falla validación, reintenta automáticamente.
    """
    answer: str = Field(
        description="Respuesta en lenguaje natural, clara y concisa"
    )
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Fuentes del documento que respaldan la respuesta"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Nivel de confianza (0=nula, 1=total)"
    )
    reasoning: str = Field(
        description="Explicación breve de cómo se llegó a la respuesta"
    )
```

### 2.3 Las tools del agente

Cada tool es una función Python que consulta datos determinísticos:

```python
# backend/app/services/analysis_agent.py (continuación)

from pydantic_ai import Agent, RunContext

# Crear el agente (una sola vez, como un router de FastAPI)
analysis_agent = Agent(
    'openrouter:anthropic/claude-sonnet-4',  # o el modelo que configures en LiteLLM
    deps_type=AnalysisDeps,
    output_type=AnalysisResponse,
    instructions="""
    Sos un analista de datos experto. Tu trabajo es responder preguntas 
    sobre documentos empresariales usando SOLO los datos que te proporcionan 
    las herramientas disponibles.
    
    Reglas:
    - NUNCA inventes datos o estadísticas
    - SIEMPRE citá las fuentes (página, sección) de donde sacás la información
    - Si no tenés suficiente información, decilo claramente
    - Usá las herramientas disponibles para buscar datos antes de responder
    - El confidence debe reflejar qué tan bien respaldada está tu respuesta
    """,
)


@analysis_agent.tool
async def search_documents(
    ctx: RunContext[AnalysisDeps], 
    query: str, 
    max_results: int = 5
) -> str:
    """
    Busca fragmentos relevantes en los documentos de la sesión actual.
    Usa esta herramienta cuando necesites encontrar información específica 
    en el documento.
    
    Args:
        query: Texto de búsqueda (qué estás buscando)
        max_results: Cantidad máxima de resultados (default 5)
    """
    results = await ctx.deps.embedding_service.search(
        session_id=ctx.deps.session_id,
        query=query,
        k=max_results,
    )
    
    if not results:
        return "No se encontraron fragmentos relevantes para esta búsqueda."
    
    # Formatear como Markdown para que el LLM lo entienda bien
    formatted = []
    for i, chunk in enumerate(results, 1):
        page_info = f" (p.{chunk.page})" if chunk.page else ""
        section_info = f" — {chunk.section}" if chunk.section else ""
        formatted.append(
            f"**Fuente {i}**{page_info}{section_info}:\n{chunk.text}"
        )
    
    return "\n\n".join(formatted)


@analysis_agent.tool
async def get_dataset_profile(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Obtiene el perfil estadístico del dataset de la sesión.
    Incluye: resumen del dataset, alertas de calidad, correlaciones.
    Usa esta herramienta cuando necesites estadísticas o métricas numéricas.
    """
    ps = ctx.deps.profiling_summary
    
    lines = [
        f"## Perfil del dataset: {ctx.deps.document_name}",
        f"- {ps.total_rows:,} filas × {ps.total_columns} columnas",
        f"- {ps.total_missing_percent}% valores nulos globales",
        f"- {ps.duplicate_rows:,} filas duplicadas",
    ]
    
    if ps.alerts:
        lines.append("\n### Alertas de calidad")
        for alert in ps.alerts[:10]:
            lines.append(f"- `{alert.column}`: {alert.detail}")
    
    if ps.correlations:
        lines.append("\n### Correlaciones significativas")
        for corr in ps.correlations[:5]:
            lines.append(
                f"- `{corr.column_a}` ↔ `{corr.column_b}`: {corr.pearson}"
            )
    
    return "\n".join(lines)


@analysis_agent.tool
async def get_findings(
    ctx: RunContext[AnalysisDeps], 
    category: str | None = None
) -> str:
    """
    Obtiene los hallazgos del análisis de la sesión.
    Los hallazgos son observaciones determinísticas sobre los datos
    (outliers, patrones, problemas de calidad).
    
    Args:
        category: Filtrar por categoría (opcional). 
                  Opciones: 'data_quality', 'statistical', 'pattern', 'anomaly'
    """
    findings = ctx.deps.findings
    
    if category:
        findings = [f for f in findings if f.category == category]
    
    if not findings:
        return f"No se encontraron hallazgos{' en la categoría ' + category if category else ''}."
    
    lines = [f"## {len(findings)} hallazgos encontrados"]
    for f in findings[:15]:  # máximo 15 para no saturar el contexto
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(f.severity, "⚪")
        lines.append(f"\n{severity_icon} **[{f.severity.upper()}]** {f.what}")
        lines.append(f"  → Impacto: {f.so_what}")
        lines.append(f"  → Acción: {f.now_what}")
    
    return "\n".join(lines)


@analysis_agent.tool
async def get_column_details(
    ctx: RunContext[AnalysisDeps], 
    column_name: str
) -> str:
    """
    Obtiene el perfil detallado de una columna específica.
    Incluye estadísticas, tipo de dato, valores nulos, distribución.
    
    Args:
        column_name: Nombre exacto de la columna a consultar
    """
    ps = ctx.deps.profiling_summary
    col = ps.columns.get(column_name)
    
    if not col:
        available = ", ".join(list(ps.columns.keys())[:20])
        return f"Columna '{column_name}' no encontrada. Columnas disponibles: {available}"
    
    lines = [
        f"## Columna: {col.name}",
        f"- Tipo: {col.semantic_type} ({col.dtype})",
        f"- Valores: {col.count:,} no-nulos de {ps.total_rows:,} ({col.null_percent}% nulos)",
        f"- Únicos: {col.unique_count:,} ({col.cardinality}% cardinalidad)",
    ]
    
    if col.is_sensitive:
        lines.append(f"- ⚠️ DATOS SENSIBLES ({col.sensitive_pattern}) — estadísticas detalladas omitidas")
    else:
        if col.mean is not None:
            lines.extend([
                f"- Media: {col.mean}",
                f"- Mediana: {col.median}",
                f"- Desv. estándar: {col.std}",
                f"- Rango: [{col.min}, {col.max}]",
            ])
            if col.skewness is not None:
                lines.append(f"- Asimetría: {col.skewness}")
    
    return "\n".join(lines)
```

### 2.4 Cómo se ejecuta

En tu endpoint `/api/analyze`, en vez del RAG lineal actual:

```python
# backend/app/api/routes/analyze.py

from app.services.analysis_agent import analysis_agent, AnalysisDeps

@router.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    # Obtener datos de la sesión (ya calculados por el pipeline)
    session = await session_repo.get(request.session_id)
    profiling = ProfilingSummary(**session["profiling_summary"])
    findings = [Finding(**f) for f in session["findings"]]
    
    # Armar las dependencias
    deps = AnalysisDeps(
        session_id=request.session_id,
        user_query=request.query,
        profiling_summary=profiling,
        findings=findings,
        embedding_service=get_embedding_service(),
        document_name=session["filename"],
        total_pages=session.get("page_count"),
    )
    
    # Ejecutar el agente
    result = await analysis_agent.run(request.query, deps=deps)
    
    # result.output es un AnalysisResponse validado por Pydantic
    return result.output
```

### 2.5 Qué pasa internamente (el loop del agente)

Cuando el usuario pregunta "¿Cuáles son los principales problemas de calidad?":

```
Paso 1: PydanticAI manda al LLM:
  - System prompt (instrucciones del agente)
  - User message ("¿Cuáles son los principales problemas de calidad?")
  - Lista de tools disponibles (search_documents, get_dataset_profile, 
    get_findings, get_column_details)

Paso 2: El LLM responde: "Voy a llamar a get_findings(category='data_quality')"

Paso 3: PydanticAI ejecuta la tool, obtiene los findings, y le devuelve 
  el resultado al LLM

Paso 4: El LLM responde: "También necesito el perfil del dataset. 
  Llamo a get_dataset_profile()"

Paso 5: PydanticAI ejecuta la tool, devuelve el perfil

Paso 6: El LLM ahora tiene suficiente info. Genera un AnalysisResponse:
  {
    "answer": "Los principales problemas son...",
    "sources": [...],
    "confidence": 0.85,
    "reasoning": "Basado en 5 findings de calidad y el perfil del dataset..."
  }

Paso 7: PydanticAI valida con Pydantic. Si pasa → retorna al usuario.
  Si falla → le dice al LLM "esto no valida, intentá de nuevo"
```

### 2.6 Testing sin LLM

```python
# backend/tests/test_analysis_agent.py

import pytest
from pydantic_ai.models.test import TestModel
from app.services.analysis_agent import analysis_agent, AnalysisDeps

@pytest.mark.asyncio
async def test_agent_returns_valid_response():
    """El agente siempre devuelve un AnalysisResponse válido."""
    mock_deps = AnalysisDeps(
        session_id="test-123",
        user_query="test query",
        profiling_summary=make_test_profiling(),
        findings=[make_test_finding()],
        embedding_service=MockEmbeddingService(),
        document_name="test.pdf",
    )
    
    with analysis_agent.override(model=TestModel()):
        result = await analysis_agent.run("¿Hay problemas?", deps=mock_deps)
        
        # Siempre devuelve AnalysisResponse válido
        assert isinstance(result.output, AnalysisResponse)
        assert 0 <= result.output.confidence <= 1
        assert len(result.output.answer) > 0


@pytest.mark.asyncio
async def test_agent_calls_appropriate_tools():
    """Verificar que el agente llama a las tools correctas."""
    with analysis_agent.override(model=TestModel()):
        result = await analysis_agent.run("test", deps=mock_deps)
        
        # Podés inspeccionar qué tools se llamaron
        tool_calls = [
            msg for msg in result.all_messages()
            if hasattr(msg, 'tool_name')
        ]
        # Verificar que se llamaron tools esperadas
```

---

## Parte 3: Lo que cambia y lo que NO cambia

### NO cambia (tu pipeline determinístico sigue igual):
- Docling, DoclingRouter, Quality Gate → sin cambios
- Pandera, SensitiveDataGuard → sin cambios  
- ydata-profiling, FindingBuilder → sin cambios
- Stats, Drift, Anomalías → sin cambios
- ContextBuilder → se usa DENTRO de las tools del agente

### SÍ cambia:
- `llm_service.py` se simplifica — ya no arma el prompt manualmente
- `/api/analyze` usa `analysis_agent.run()` en vez de RAG lineal
- La respuesta es SIEMPRE un `AnalysisResponse` Pydantic-validado
- Queries complejas multi-paso funcionan automáticamente

### Lo que ganás:
- **Queries multi-paso**: "Compará Q1 con Q3" funciona porque el agente 
  hace múltiples búsquedas
- **Respuestas estructuradas garantizadas**: el schema Pydantic se valida 
  siempre, con retry automático
- **Testing sin LLM**: TestModel para CI, sin costo, sin flakiness
- **Streaming**: PydanticAI soporta streaming de structured output 
  (para mejorar la UX del QueryPanel)
- **Auditoría**: podés ver exactamente qué tools llamó, con qué args, 
  y qué devolvieron

### Lo que NO ganás (y está bien):
- No reemplaza tu pipeline — lo complementa
- No hace que el LLM compute — las tools consultan datos pre-calculados
- No necesita CrewAI/LangGraph/n8n — PydanticAI solo es suficiente

---

## Parte 4: Integración con LiteLLM

PydanticAI soporta LiteLLM nativamente. Podés usar OpenRouter (que ya 
tenés) directamente:

```python
# Opción 1: OpenRouter directo
agent = Agent('openrouter:anthropic/claude-sonnet-4')

# Opción 2: Via LiteLLM (si querés usar tu Router con fallback)
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel(
    'anthropic/claude-sonnet-4',
    base_url='http://localhost:4000',  # tu LiteLLM proxy si lo usás
    api_key=settings.LITELLM_API_KEY,
)
agent = Agent(model)

# Opción 3: Ollama local (para development sin costo)
agent = Agent('ollama:qwen3:8b')
```

Tu fallback chain (OpenRouter → Ollama) se mantiene. Podés configurar 
el modelo del agente via variable de entorno:

```env
ANALYSIS_AGENT_MODEL=openrouter:anthropic/claude-sonnet-4
```

---

## Parte 5: Orden de implementación

| Paso | Qué | Cuándo |
|---|---|---|
| 1 | Schema `AnalysisResponse` en `schemas/` | Con el L2 (Fase 2) |
| 2 | `AnalysisDeps` dataclass | Con el L2 (Fase 2) |
| 3 | `analysis_agent.py` con las 4 tools | Fase 6 (semanas 14-16) |
| 4 | Reemplazar RAG lineal en `/api/analyze` | Fase 6 |
| 5 | Tests con TestModel | Fase 6 |
| 6 | Streaming en el frontend (SSE) | Rediseño frontend con v0 |

Los pasos 1-2 se pueden preparar ahora (son solo schemas). 
Los pasos 3-5 son Fase 6, después de que L2/L3/L4/L5 estén estables.
El paso 6 es frontend, va con el rediseño visual.

---

## Parte 6: Glosario rápido

| Término | Qué significa en Data-X |
|---|---|
| **Agent** | El objeto que decide qué tools llamar para responder |
| **Tool** | Una función Python que consulta datos (FAISS, profiling, findings) |
| **Dependencies** | Los datos y servicios de una sesión (inyectados via RunContext) |
| **Output Type** | El schema Pydantic que la respuesta DEBE cumplir |
| **RunContext** | El contenedor que las tools usan para acceder a las dependencias |
| **TestModel** | Un LLM fake para testing sin API calls |
| **Reflection** | Cuando PydanticAI le dice al LLM "tu respuesta no valida, intentá de nuevo" |
| **Structured Output** | Respuesta del LLM validada contra un schema Pydantic |
| **Tool-use** | La capacidad del LLM de decidir llamar funciones Python |
