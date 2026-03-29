# OpenSearch Architecture - Design Decisions

**Ref:** NXT-003 - Decisiones de diseño para retrieval vectorial en Data-X

---

## Overview

Este documento explica las decisiones arquitectónicas clave para la implementación de OpenSearch en Data-X, incluyendo estrategias de indexación, fallbacks, y trade-offs.

---

## 1. Estrategia de Indexación
### Decisión: Índice Dinámico por Sesión

**Patrón implementado:**
```
datax-{tier}-{session_id}
```

**Ejemplo:**
```
datax-enterprise-abc123-456def-789ghi
datax-professional-xyz789-012abc-345def
```

### Justificación

✅ **GDPR Compliance**
- Borrar sesión = borrar índice completo
- Sin necesidad de queries de cleanup complejas
- Alineado con `delete_session_data()` existente (BUG-002 fix)

✅ **Aislamiento Perfecto**
- Cada análisis es independiente
- No hay riesgo de data leakage entre usuarios
- Logs y debugging más fáciles (1 índice = 1 sesión)

✅ **Multi-Tenancy Natural**
- No requiere filtros adicionales en queries
- Escalabilidad horizontal (sharding automático por AWS)

✅ **Simplicidad Operacional**
- No requiere lifecycle policies complejas
- Monitoreo granular (stats por sesión)

### Trade-offs

❌ **Overhead de Creación**
- ~500ms por índice nuevo
- Mitigación: Indexación asíncrona (no bloquea el user)

❌ **Proliferación de Índices**
- Muchos índices pequeños vs pocos índices grandes
- Mitigación: OpenSearch maneja bien hasta 10K índices por cluster

### Alternativa Considerada: Índice Global por Tier

**Patrón:**
```
datax-{tier}  # Ej: datax-enterprise (compartido por todos los usuarios)
```

**Ventajas:**
- Sin overhead de creación
- Menos índices totales

**Desventajas rechazadas:**
- ❌ Requiere filtrado por `session_id` en **todas** las queries
- ❌ Cleanup complejo (borrado por documento, no por índice)
- ❌ Riesgo de data leakage si falla el filtro
- ❌ Requiere lifecycle policy para retention
- ❌ Peor alineación con GDPR

**Decisión:** Rechazada. El overhead de 500ms es aceptable vs complejidad y riesgos.

---

## 2. Tiers y Retrieval Strategy

### Mapping Tier → Servicio

| Tier | Sesión/día | Retrieval Service | Razón |
|------|----------------|-------------------|--------|
| **Lite** | < 100 | FAISS in-memory | Gratis, sin dependencias externas |
| **Professional** | 100-1000 | OpenSearch / Qdrant | Balance costo/escalabilidad |
| **Enterprise** | > 1000 | OpenSearch Serverless | Máxima escalabilidad, AWS integrado |

### Implementación

```python
# backend/app/api/routes/analyze.py

def get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:
    """
    Strategy pattern: Decide retrieval engine by tier.
    
    Fallback order:
    1. OpenSearch (if enabled + tier allows)
    2. Qdrant (if enabled + tier allows)
    3. FAISS (always available)
    """
    tier = current_user.get("tier", "lite")
    session_id = current_user.get("current_session_id", "unknown")
    
    # Lite tier: Always FAISS
    if tier == "lite":
        logger.info("retrieval_strategy", tier=tier, engine="faiss")
        return EmbeddingService()
    
    # Professional/Enterprise: Try OpenSearch first
    if tier in ["professional", "enterprise"]:
        if settings.opensearch_enabled:
            try:
                service = OpenSearchRetrievalService(
                    session_id=session_id,
                    tier=tier
                )
                if service.client:  # Connection successful
                    logger.info("retrieval_strategy", tier=tier, engine="opensearch")
                    return service
            except Exception as e:
                logger.error("opensearch_fallback", error=str(e))
        
        # Fallback: FAISS
        logger.warning(
            "retrieval_fallback_to_faiss",
            tier=tier,
            reason="opensearch_unavailable"
        )
    
    return EmbeddingService()
```

### Justificación
✅ **Graceful Degradation**
- Si OpenSearch falla, la app sigue funcionando con FAISS
- El usuario no ve errores, solo menor escalabilidad

✅ **Flexibilidad**
- Puedes habilitar/deshabilitar OpenSearch con 1 env var
- Fácil A/B testing entre engines

✅ **Consistencia de Interfaz**
- Todos los servicios implementan `BaseRetrievalService`
- Frontend no sabe qué engine se usa

---

## 3. Embedding Model

### Decisión: `paraphrase-multilingual-MiniLM-L12-v2`

**Características:**
- Dimensiones: 384
- Tamaño: 420MB
- Idiomas: 50+ (incluye Español)
- Performance: ~85% de mBERT con 5x menos parámetros

### Justificación

✅ **Consistencia**
- Mismo modelo que `EmbeddingService` (FAISS)
- Permite comparar resultados entre tiers
- Facilita migración FAISS → OpenSearch

✅ **Multilingual**
- Data-X es usado en LATAM (Español)
- Soporta datasets en múltiples idiomas

✅ **Performance**
- 384 dimensiones = buen balance accuracy/speed
- Indexing: ~2000 docs/segundo en CPU
- Query: < 50ms p99 para 1M vectors

### Alternativas Consideradas

| Modelo | Dims | Pros | Cons | Decisión |
|--------|------|------|------|----------|
| `all-MiniLM-L6-v2` | 384 | Más rápido | Solo Inglés | ❌ Rechazado |
| `mBERT-base` | 768 | Mejor accuracy | 2x dimensiones, lento | ❌ Rechazado |
| `paraphrase-multilingual-MiniLM` | 384 | **Multilingual + rápido** | - | ✅ **Elegido** |
| `text-embedding-ada-002` (OpenAI) | 1536 | SOTA accuracy | Requiere API, caro | ❌ Rechazado |

---

## 4. Index Configuration (k-NN)

### Parámetros Elegidos

```python
"method": {
    "name": "hnsw",           # Hierarchical Navigable Small World
    "space_type": "cosinesimil",  # Cosine similarity
    "engine": "nmslib",       # Non-Metric Space Library
    "parameters": {
        "ef_construction": 128, # Exploration factor during indexing
        "m": 16                 # Number of bidirectional links
    }
}
```

### Justificación

**HNSW (Hierarchical Navigable Small World)**
- ✅ Mejor algoritmo para 100K-10M vectors
- ✅ Query time: O(log N)
- ✅ Alto recall (> 95% @ k=10)

**Cosine Similarity**
- ✅ Estándar para embeddings normalizados
- ✅ Ignora magnitud, solo dirección (mejor para semántica)

**`ef_construction=128`**
- Balance entre indexing speed y accuracy
- Valores típicos: 100-200
- 128 = buen default para 384 dims

**`m=16`**
- Número de conexiones por nodo
- Valores típicos: 12-48
- 16 = balance memoria/recall

### Alternativas para Casos Específicos

**Si necesitas indexing ultrarrápido (sacrifice recall):**
```python
"ef_construction": 64,
"m": 8
```

**Si necesitas recall máximo (sacrifice indexing speed):**
```python
"ef_construction": 256,
"m": 32
```

**Para datasets gigantes (> 10M vectors):**
Considerar IVF (Inverted File Index) en lugar de HNSW:
```python
"method": {
    "name": "ivf",
    "parameters": {
        "nlist": 1024,  # Number of clusters
        "nprobe": 32    # Clusters to search
    }
}
```

---

## 5. Cleanup Strategy

### Implementación

```python
# backend/app/repositories/mongo.py

async def delete_session_data(self, session_id: str) -> bool:
    """
    GDPR-compliant session deletion.
    Deletes data from MongoDB AND OpenSearch.
    """
    try:
        # 1. MongoDB cleanup (existente)
        await self.sessions.delete_one({"session_id": session_id})
        await self.bronze.delete_many({"session_id": session_id})
        # ... (otros deletes)
        
        # 2. OpenSearch cleanup (NUEVO)
        if settings.opensearch_enabled:
            from app.services.retrieval.opensearch_service import OpenSearchRetrievalService
            retrieval_svc = OpenSearchRetrievalService(
                session_id=session_id,
                tier="enterprise"  # Tier doesn't matter for deletion
            )
            await retrieval_svc.delete_index()
        
        logger.info("session_deleted", session_id=session_id)
        return True
    except Exception as e:
        logger.error("session_deletion_failed", session_id=session_id, error=str(e))
        return False
```

### Justificación

✅ **Atomicidad**
- Si el delete de MongoDB falla, OpenSearch tampoco se borra
- Consistencia entre datastores

✅ **GDPR Compliance**
- "Right to be forgotten" implementado correctamente
- Un solo método borra **todos** los datos del usuario

✅ **Idempotencia**
- Llamar `delete_index()` múltiples veces no causa error
- OpenSearch ignora deletes de índices inexistentes

---

## 6. Filtrado y Metadatos

### Schema de Documentos en OpenSearch

```json
{
  "source_id": "finding-abc-123",
  "source_type": "finding",           // "finding" | "chunk"
  "text": "Full text for embedding",
  "snippet": "First 240 chars...",
  "evidence_ref": "finding-abc-123",
  "provenance": {                      // Solo para chunks
    "page": 5,
    "heading": "Sección 2.1",
    "section_path": "Cap 2 / Sección 2.1"
  },
  "session_id": "session-xyz-789",
  "embedding": [0.123, -0.456, ...],  // 384 floats
  "created_at": "2026-03-29T10:00:00Z"
}
```

### Queries con Filtros

```python
# Ejemplo: Solo findings de página 5
results = await retrieval_svc.search_hybrid_sources(
    query="¿Cuántos nulos hay?",
    top_k=5,
    filter_by_source_type="chunk",
    filter_by_page=5
)
```

**Query DSL generada:**
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "knn": {
            "embedding": {"vector": [...], "k": 5}
          }
        }
      ],
      "filter": [
        {"term": {"session_id": "session-xyz-789"}},
        {"term": {"source_type": "chunk"}},
        {"term": {"provenance.page": 5}}
      ]
    }
  }
}
```

### Beneficios

✅ **Precision Mejorada**
- Usuario puede preguntar "Qué dice la página 5 sobre nulos?"
- RAG solo busca en esa página

✅ **Performance**
- Filtros aplicados **antes** de k-NN
- OpenSearch optimiza queries automáticamente

---

## 7. Monitoring & Observability

### Logs Estructurados

Todos los eventos OpenSearch se loguean:

```python
logger.info(
    "opensearch_search_complete",
    query=query[:50],
    results=len(results),
    top_score=results[0]["score"],
    latency_ms=elapsed,
    index=self.index_name
)
```

### Métricas Clave

**Application-level:**
- `opensearch_indexing_duration_seconds` (histogram)
- `opensearch_search_latency_seconds` (histogram)
- `opensearch_errors_total` (counter)
- `opensearch_fallback_to_faiss_total` (counter)

**OpenSearch-level (CloudWatch):**
- `ClusterStatus.green` (gauge)
- `SearchLatency` (p50, p99)
- `IndexingLatency`
- `KNNSearchRequests`

### Alertas Sugeridas

```yaml
alerts:
  - name: OpenSearchDown
    condition: ClusterStatus != "green"
    severity: P1
    action: Fallback to FAISS automatically
  
  - name: HighSearchLatency
    condition: SearchLatency.p99 > 1000ms
    severity: P2
    action: Investigate slow queries
  
  - name: HighFallbackRate
    condition: opensearch_fallback_to_faiss_total > 10/min
    severity: P2
    action: Check OpenSearch connectivity
```

---

## 8. Cost Optimization

### Estrategias

**1. Lifecycle de Índices**

Borrar automáticamente índices de sesiones antiguas:

```python
# Cron job diario
async def cleanup_old_indices():
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Buscar sesiones > 30 días
    old_sessions = await session_repo.find({
        "created_at": {"$lt": cutoff_date}
    })
    
    for session in old_sessions:
        await delete_session_data(session["session_id"])
```

**2. Compresión de Embeddings**

Reducir de 384 dims a 256 dims con PCA (ahorra 33% storage):

```python
from sklearn.decomposition import PCA

pca = PCA(n_components=256)
compressed_embeddings = pca.fit_transform(embeddings)
```

**Trade-off:** ~2% loss in recall.

**3. Reserved Instances (AWS)**

Para cargas predecibles, usar Reserved Capacity en OpenSearch Serverless:
- Ahorro: ~30% vs on-demand
- Compromiso: 1 año

---

## 9. Testing Strategy

### Unit Tests

```python
# backend/tests/test_opensearch_service.py

@pytest.mark.asyncio
async def test_opensearch_fallback_to_faiss():
    """Si OpenSearch falla, debe usar FAISS sin error."""
    with patch('app.services.retrieval.opensearch_service.OPENSEARCH_AVAILABLE', False):
        service = OpenSearchRetrievalService(session_id="test", tier="enterprise")
        assert service.client is None  # No client created
```

### Integration Tests

```python
@pytest.mark.integration
async def test_opensearch_index_and_search():
    """Test completo de indexing + search."""
    service = OpenSearchRetrievalService(session_id="test-123", tier="professional")
    
    # Index test data
    await service.index_hybrid_sources(
        findings=[{"finding_id": "f1", "text": "Test finding"}],
        chunks=[]
    )
    
    # Search
    results = await service.search_hybrid_sources(query="test", top_k=5)
    assert len(results) > 0
    assert results[0]["source_id"] == "f1"
    
    # Cleanup
    await service.delete_index()
```

---

## 10. Migration Path

### De FAISS a OpenSearch

```python
async def migrate_session_to_opensearch(session_id: str):
    """
    Migra una sesión existente de FAISS (MongoDB) a OpenSearch.
    """
    # 1. Cargar cache FAISS desde MongoDB
    cache = await session_repo.get_hybrid_embeddings_cache(session_id)
    if not cache:
        return
    
    # 2. Deserializar source_map
    source_map = cache["source_map"]
    
    # 3. Crear servicio OpenSearch
    opensearch_svc = OpenSearchRetrievalService(
        session_id=session_id,
        tier="professional"
    )
    
    # 4. Recrear findings y chunks desde source_map
    findings = [s for s in source_map.values() if s["source_type"] == "finding"]
    chunks = [s for s in source_map.values() if s["source_type"] == "chunk"]
    
    # 5. Indexar en OpenSearch
    await opensearch_svc.index_hybrid_sources(findings, chunks)
    
    # 6. (Opcional) Borrar cache FAISS de MongoDB
    await session_repo.delete_hybrid_embeddings_cache(session_id)
    
    logger.info("session_migrated_to_opensearch", session_id=session_id)
```

---

## Summary

| Decisión | Opción Elegida | Justificación |
|-----------|----------------|---------------|
| **Estrategia de Índices** | Dinámico por sesión | GDPR, aislamiento, simplicidad |
| **Tier Mapping** | Lite=FAISS, Pro/Ent=OpenSearch | Costo-beneficio |
| **Embedding Model** | MiniLM-L12 multilingual (384d) | Consistencia, performance |
| **k-NN Algorithm** | HNSW (ef=128, m=16) | Balance accuracy/speed |
| **Cleanup** | Delete índice completo | Atomicidad, GDPR |
| **Fallback** | OpenSearch → FAISS | Graceful degradation |
| **Monitoring** | Logs estructurados + CloudWatch | Observability |

**Ver también:**
- `OPENSEARCH_SETUP.md` - Setup completo
- `OPENSEARCH_ALTERNATIVES.md` - Comparativa de soluciones
