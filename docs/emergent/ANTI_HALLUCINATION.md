# Anti-Hallucination Guardrails

**Ref:** NXT-004 - Mejoras para reducir alucinaciones del LLM en el RAG

---

## Overview

Los modelos de lenguaje (LLMs) pueden "alucinar" - inventar información que parece correcta pero no existe en las fuentes provistas. En un sistema de análisis de datos como Data-X, esto es crítico porque:

- ❌ El usuario confía en los hallazgos para tomar decisiones de negocio
- ❌ Una alucinación puede llevar a decisiones erróneas
- ❌ Pierde credibilidad del producto

Este documento explica los guardrails implementados para minimizar alucinaciones.

---

## 1. Tipos de Alucinaciones

### 1.1 Fuentes Inventadas

**Ejemplo:**
```
Usuario: "¿Cuántos nulos hay en la columna edad?"
LLM: "Según el finding F-999, hay 50 nulos en la columna edad."

Problema: F-999 no existe en los datos reales.
```

**Mitigación:** Verificación cruzada de `source_id`.

### 1.2 Datos Inventados

**Ejemplo:**
```
Usuario: "¿Cuál es el promedio de ingresos?"
LLM: "El promedio de ingresos es $75,000."

Problema: Ese valor no aparece en ningún finding o chunk.
```

**Mitigación:** Confidence scoring + verificación de especificidad.

### 1.3 Respuestas Genéricas

**Ejemplo:**
```
Usuario: "¿Hay outliers en los datos?"
LLM: "Sí, hay algunos outliers que deberías revisar."

Problema: Respuesta vaga sin citar fuentes específicas.
```

**Mitigación:** Exigir fuentes y rechazar respuestas sin `sources_used`.

---

## 2. Guardrails Implementados

### 2.1 Verificación Cruzada de Sources

**Qué es:**
Chequear que cada `source_id` citado en la respuesta del LLM efectivamente exista en el `source_map` disponible.

**Implementación:**

```python
def _verify_sources_exist(sources_used: list[dict], available_source_map: dict) -> tuple[bool, list[str]]:
    """
    Verifica que las fuentes citadas existan en source_map.
    
    Returns:
        (all_valid, invalid_ids)
    """
    invalid_ids = []
    
    for source in sources_used:
        source_id = source.get("source_id", "")
        if source_id and source_id not in available_source_map:
            invalid_ids.append(source_id)
    
    return len(invalid_ids) == 0, invalid_ids
```

**Resultado:**
- Si **todas** las fuentes existen: `hallucination_risk -= 0.0` (no penaliza)
- Si **alguna** fuente no existe: `hallucination_risk += 0.4` (penalización fuerte)

**Por qué 0.4:**
Inventar una fuente es un error grave. Aumentar el riesgo en 0.4 hace que el score supere el threshold de confianza (0.5) y se muestre un warning al usuario.

---

### 2.2 Hallucination Risk Score

**Qué es:**
Un score de 0.0 a 1.0 que indica qué tan probable es que la respuesta contenga alucinaciones.

**Cálculo:**

```python
def calculate_hallucination_risk(
    confidence: str,
    sources_used: list[dict],
    answer: str,
    available_source_map: dict
) -> float:
    """
    Calcula el riesgo de alucinación.
    
    Score:
        0.0 - 0.3: Respuesta confiable ✅
        0.3 - 0.6: Baja confianza ⚠️
        0.6 - 1.0: Alta probabilidad de alucinación ❌
    """
    risk = 0.0
    
    # Factor 1: Fuentes inventadas (GRAVE)
    all_valid, invalid_ids = _verify_sources_exist(sources_used, available_source_map)
    if not all_valid:
        risk += 0.4
        logger.warning(
            "sources_verification_failed",
            invalid_ids=invalid_ids,
            msg="LLM cited non-existent sources"
        )
    
    # Factor 2: Confianza baja del LLM
    if confidence == "low":
        risk += 0.3
    elif confidence == "medium":
        risk += 0.1
    
    # Factor 3: Sin fuentes citadas
    if len(sources_used) == 0:
        risk += 0.2
    
    # Factor 4: Respuesta muy corta (< 50 chars)
    # Indica respuesta genérica o evasiva
    if len(answer) < 50:
        risk += 0.1
    
    return min(risk, 1.0)  # Cap at 1.0
```

**Ejemplo de cálculo:**

**Caso 1: Respuesta Óptima**
```python
confidence = "high"
sources_used = [{"source_id": "f-001"}, {"source_id": "chunk-123"}]
answer = "Según el finding F-001, hay 50 nulos en la columna edad (5% del dataset). El chunk-123 confirma que estos nulos están concentrados en el segmento de jóvenes."
available_source_map = {"f-001": {...}, "chunk-123": {...}}

risk = 0.0  # Fuentes válidas
risk += 0.0  # Confidence high
risk += 0.0  # Tiene fuentes
risk += 0.0  # Respuesta larga y específica
# TOTAL: 0.0 ✅ CONFIABLE
```

**Caso 2: Respuesta Sospechosa**
```python
confidence = "low"
sources_used = [{"source_id": "F-999"}]  # ¡No existe!
answer = "Hay algunos nulos."
available_source_map = {"f-001": {...}, "chunk-123": {...}}

risk = 0.4  # Fuente inventada
risk += 0.3  # Confidence low
risk += 0.0  # Tiene fuentes (aunque inválidas)
risk += 0.1  # Respuesta muy corta
# TOTAL: 0.8 ❌ ALTA ALUCINACIÓN
```

---

### 2.3 Threshold de Confianza

**Parámetro:** `HALLUCINATION_RISK_THRESHOLD = 0.5`

**Lógica:**

```python
if hallucination_risk >= HALLUCINATION_RISK_THRESHOLD:
    # Rechazar respuesta o mostrar warning crítico
    return {
        "answer": "No puedo responder con certeza basado en las fuentes disponibles.",
        "confidence": "low",
        "hallucination_risk": hallucination_risk,
        "warning": "La respuesta generada tenía alta probabilidad de contener información incorrecta."
    }
```

**Thresholds:**

| Risk Score | Nivel | Acción |
|------------|-------|--------|
| 0.0 - 0.3 | 🟢 Bajo | Mostrar respuesta normalmente |
| 0.3 - 0.5 | 🟡 Medio | Agregar badge "Baja confianza" en UI |
| 0.5 - 0.7 | 🟠 Alto | Mostrar warning: "Respuesta poco confiable" |
| 0.7 - 1.0 | 🔴 Crítico | Rechazar respuesta, mostrar mensaje genérico |

---

### 2.4 Prompts Mejorados

**Antes:**
```python
system_prompt = """Respondé basándote en los hallazgos."""
```

**Después (NXT-004):**
```python
system_prompt = """Sos un analista de datos experto. Respondé basándote EXCLUSIVAMENTE
en los hallazgos y fuentes documentales que te doy. No inventes datos.
Si la pregunta no se puede responder con estas fuentes, decilo honestamente.

REGLAS ESTRICTAS:
1. SIEMPRE cita el source_id exacto de donde sacaste cada información.
2. Si no tenés suficiente información, decí "No tengo suficiente información para responder."
3. No hagas suposiciones ni generalizaciones sin evidencia directa.
4. Si un número o estadística no aparece en las fuentes, NO lo inventes.

Respondé SOLO con un objeto JSON con esta estructura exacta:
{
  "answer": "tu respuesta detallada pero clara en lenguaje de negocio",
  "confidence": "high|medium|low",
  "sources_used": [
    {"source_type":"finding|chunk","source_id":"id_exacto","evidence_ref":"ref"}
  ]
}"""
```

**Mejoras:**
- ✅ Enfatiza "EXCLUSIVAMENTE" y "No inventes"
- ✅ Agrega reglas numéricas explícitas
- ✅ Instruye cómo responder si falta info

---

### 2.5 Verificación de Especificidad

**Qué es:**
Chequear que la respuesta contenga detalles específicos (números, nombres de columnas, valores) y no solo generalidades.

**Implementación:**

```python
def _check_answer_specificity(answer: str, context_sources: list[dict]) -> float:
    """
    Retorna un score de especificidad (0.0 = genérico, 1.0 = muy específico).
    """
    specificity_score = 0.0
    
    # Criterio 1: Contiene números
    import re
    if re.search(r'\d+', answer):
        specificity_score += 0.3
    
    # Criterio 2: Menciona nombres de columnas de las fuentes
    column_mentions = 0
    for source in context_sources:
        text = source.get("text", "")
        # Extraer nombres de columnas (heurística simple)
        columns = re.findall(r'columna\s+["\']?([a-zA-Z_]+)["\']?', text, re.IGNORECASE)
        for col in columns:
            if col.lower() in answer.lower():
                column_mentions += 1
    
    if column_mentions > 0:
        specificity_score += 0.4
    
    # Criterio 3: Longitud razonable (> 100 chars)
    if len(answer) > 100:
        specificity_score += 0.3
    
    return min(specificity_score, 1.0)
```

**Uso:**

```python
specificity = _check_answer_specificity(answer, context_sources)

if specificity < 0.3:
    # Respuesta muy genérica
    hallucination_risk += 0.2
```

---

## 3. Flujo Completo

### 3.1 Diagrama

```
Usuario hace pregunta
        |
        v
Retrieve fuentes (RAG) → source_map
        |
        v
LLM genera respuesta + sources_used
        |
        v
Guardrails (NXT-004)
        |
        |───> Verificar sources_used existen en source_map
        |───> Calcular hallucination_risk
        |───> Verificar especificidad
        |
        v
Decisión:
  - risk < 0.3 → Mostrar respuesta ✅
  - 0.3 <= risk < 0.5 → Mostrar con badge "Baja confianza" ⚠️
  - risk >= 0.5 → Rechazar, mostrar mensaje genérico ❌
        |
        v
Retornar a frontend
```

### 3.2 Ejemplo de Response

**Respuesta Confiable:**
```json
{
  "answer": "Según el finding F-001, hay 50 nulos en la columna 'edad' (5% del dataset). Estos nulos están concentrados en el segmento de jóvenes menores de 25 años.",
  "confidence": "high",
  "sources_used": [
    {"source_type": "finding", "source_id": "f-001", "evidence_ref": "data_gap_finding"}
  ],
  "hallucination_risk": 0.0,
  "cost_usd": 0.0023
}
```

**Respuesta con Warning:**
```json
{
  "answer": "Hay algunos valores nulos en los datos que deberías revisar.",
  "confidence": "low",
  "sources_used": [],
  "hallucination_risk": 0.5,
  "warning": "Esta respuesta tiene baja confianza. Verifica los hallazgos manualmente.",
  "cost_usd": 0.0018
}
```

**Respuesta Rechazada:**
```json
{
  "answer": "No puedo responder con certeza basado en las fuentes disponibles. Por favor, reformula tu pregunta o revisa los hallazgos manualmente en el reporte.",
  "confidence": "low",
  "sources_used": [],
  "hallucination_risk": 0.8,
  "warning": "La respuesta inicial tenía alta probabilidad de contener información incorrecta.",
  "rejected": true,
  "cost_usd": 0.0020
}
```

---

## 4. Frontend Integration

### 4.1 UI Components

**Badge de Confianza:**

```tsx
// frontend/src/components/AnalysisResponse.tsx

function ConfidenceBadge({ hallucinationRisk }: { hallucinationRisk: number }) {
  if (hallucinationRisk < 0.3) {
    return <Badge variant="success">✅ Alta confianza</Badge>
  } else if (hallucinationRisk < 0.5) {
    return <Badge variant="warning">⚠️ Baja confianza</Badge>
  } else {
    return <Badge variant="danger">❌ Respuesta poco confiable</Badge>
  }
}
```

**Warning Alert:**

```tsx
{response.warning && (
  <Alert variant="warning">
    <AlertTitle>Advertencia</AlertTitle>
    <AlertDescription>{response.warning}</AlertDescription>
  </Alert>
)}
```

### 4.2 Logging al Usuario

Cuando `hallucination_risk >= 0.5`, mostrar:

```
⚠️ Advertencia: Esta respuesta tiene alta probabilidad de ser inexacta.

Motivo: La IA no pudo encontrar suficiente información en las fuentes disponibles.

Recomendación:
- Revisa los hallazgos manualmente en la pestaña "Reporte"
- Reformula tu pregunta de manera más específica
- Verifica que el dataset contenga la información que buscas
```

---

## 5. Testing

### 5.1 Unit Tests

```python
# backend/tests/test_anti_hallucination.py

def test_verify_sources_all_valid():
    sources_used = [{"source_id": "f-001"}, {"source_id": "chunk-123"}]
    source_map = {"f-001": {}, "chunk-123": {}}
    
    all_valid, invalid = _verify_sources_exist(sources_used, source_map)
    assert all_valid is True
    assert len(invalid) == 0

def test_verify_sources_some_invalid():
    sources_used = [{"source_id": "f-001"}, {"source_id": "f-999"}]  # f-999 no existe
    source_map = {"f-001": {}}
    
    all_valid, invalid = _verify_sources_exist(sources_used, source_map)
    assert all_valid is False
    assert "f-999" in invalid

def test_hallucination_risk_high_confidence_valid_sources():
    risk = calculate_hallucination_risk(
        confidence="high",
        sources_used=[{"source_id": "f-001"}],
        answer="Respuesta detallada con más de 50 caracteres que menciona hallazgos específicos.",
        available_source_map={"f-001": {}}
    )
    assert risk < 0.3  # Debe ser bajo

def test_hallucination_risk_invalid_sources():
    risk = calculate_hallucination_risk(
        confidence="low",
        sources_used=[{"source_id": "f-999"}],  # No existe
        answer="Respuesta corta",
        available_source_map={"f-001": {}}
    )
    assert risk >= 0.5  # Debe ser alto
```

### 5.2 Integration Tests

```python
@pytest.mark.asyncio
async def test_answer_query_with_invalid_sources():
    """
    Si el LLM cita fuentes inválidas, el guardrail debe rechazar la respuesta.
    """
    llm_service = LLMService()
    
    # Mock del LLM para que retorne fuentes inventadas
    with patch.object(llm_service.router, 'acompletion') as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "answer": "Según F-999, hay nulos.",
                        "confidence": "high",
                        "sources_used": [{"source_id": "f-999"}]  # Inventado
                    })
                )
            )]
        )
        
        # Ejecutar query
        result = await llm_service.answer_query(
            query="¿Hay nulos?",
            relevant_findings=[],
            context_sources=[],
            available_source_map={"f-001": {}}  # f-999 no está aquí
        )
        
        # Assertions
        assert result["hallucination_risk"] >= 0.4  # Penalización por fuente inválida
        assert "warning" in result or result["rejected"] is True
```

---

## 6. Metrics & Monitoring

### 6.1 Métricas Clave

```python
# Prometheus metrics
hallucination_risk_histogram = Histogram(
    'llm_hallucination_risk',
    'Distribution of hallucination risk scores',
    buckets=[0.0, 0.3, 0.5, 0.7, 1.0]
)

rejected_responses_counter = Counter(
    'llm_responses_rejected_total',
    'Total responses rejected due to high hallucination risk'
)

invalid_sources_counter = Counter(
    'llm_invalid_sources_total',
    'Total invalid sources cited by LLM'
)
```

### 6.2 Dashboards

**Métricas a monitorear:**

1. **Hallucination Risk Distribution**
   - Histograma de scores
   - Target: > 80% con risk < 0.3

2. **Rejection Rate**
   - % de respuestas rechazadas por alto risk
   - Target: < 5%

3. **Invalid Sources Rate**
   - Frecuencia de fuentes inventadas
   - Target: < 1%

4. **Confidence Distribution**
   - % de respuestas high/medium/low confidence
   - Target: > 60% high confidence

---

## 7. Tuning del Sistema

### 7.1 Ajustar Thresholds

Si tienes **demasiados falsos positivos** (respuestas correctas rechazadas):

```python
# Aumentar threshold
HALLUCINATION_RISK_THRESHOLD = 0.6  # Era 0.5
```

Si tienes **demasiadas alucinaciones pasando**:

```python
# Disminuir threshold
HALLUCINATION_RISK_THRESHOLD = 0.4  # Era 0.5

# O aumentar penalizaciones
if not all_valid:
    risk += 0.5  # Era 0.4
```

### 7.2 A/B Testing

Probar diferentes configuraciones:

```python
if user_id % 2 == 0:
    # Grupo A: Guardrails estrictos
    THRESHOLD = 0.4
else:
    # Grupo B: Guardrails relajados
    THRESHOLD = 0.6

# Medir:
# - User satisfaction (thumbs up/down)
# - Reported errors
# - Engagement (queries por sesión)
```

---

## 8. Future Improvements

### 8.1 RAG Avanzado (No implementado aún)

**Self-consistency:**
- Generar 3 respuestas independientes
- Comparar y usar la más consistente

**Chain-of-Verification:**
- LLM genera respuesta
- LLM genera preguntas de verificación
- LLM responde las verificaciones
- LLM revisa respuesta original

### 8.2 Feedback Loop

Capturar feedback del usuario:

```python
# Cuando usuario hace thumbs down
if user_feedback == "incorrect":
    # Log para retraining
    logger.warning(
        "user_reported_hallucination",
        query=query,
        response=answer,
        hallucination_risk=risk,
        sources_used=sources_used
    )
```

---

## Summary

| Guardrail | Objetivo | Threshold | Penalización |
|-----------|----------|-----------|---------------|
| **Fuentes inventadas** | Detectar IDs inválidos | N/A | +0.4 risk |
| **Confidence score** | Usar self-assessment del LLM | low/medium/high | +0.3/+0.1/+0.0 |
| **Sin fuentes** | Forzar citación | len=0 | +0.2 risk |
| **Respuesta corta** | Detectar vaguedad | < 50 chars | +0.1 risk |
| **Threshold final** | Rechazar o warning | >= 0.5 | Reject response |

**Resultado esperado:**
- ✅ 90% de respuestas con risk < 0.3 (alta confianza)
- ✅ < 5% de respuestas rechazadas
- ✅ < 1% de fuentes inventadas

**Ver también:**
- `llm_service.py` - Implementación completa
- `analysis_response.py` - Schema con hallucination_risk
