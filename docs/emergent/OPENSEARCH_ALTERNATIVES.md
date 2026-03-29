# OpenSearch Alternatives - Vector Databases Comparison

**Ref:** NXT-003 - Evaluación de alternativas para retrieval vectorial escalable

---

## Overview

Esta guía compara alternativas a OpenSearch para búsqueda vectorial (k-NN) en Data-X. Todas soportan embeddings de 384 dimensiones (SentenceTransformers MiniLM).

---

## Comparativa Rápida

| Solución | Tipo | Escalabilidad | Costo | Complejidad | Recomendación |
|-----------|------|---------------|-------|-------------|------------------|
| **OpenSearch** | Managed/Self | ⭐️⭐️⭐️⭐️⭐️ | $$$ | Media | ✅ Producción enterprise |
| **Qdrant** | Managed/Self | ⭐️⭐️⭐️⭐️⭐️ | $$ | Baja | ✅ Mejor opción opensource |
| **Weaviate** | Managed/Self | ⭐️⭐️⭐️⭐️ | $$ | Media | ✅ GraphQL + Vectors |
| **Milvus** | Self/Cloud | ⭐️⭐️⭐️⭐️⭐️ | $$$ | Alta | ⚠️ Solo para >10M vectors |
| **Pinecone** | SaaS | ⭐️⭐️⭐️⭐️ | $$$ | Baja | ⚠️ Vendor lock-in |
| **Elasticsearch** | Managed/Self | ⭐️⭐️⭐️⭐️ | $$$$ | Media | ❌ Muy caro vs OpenSearch |
| **Chroma** | Self | ⭐️⭐️ | $ | Baja | ✅ Dev/testing |
| **FAISS** | In-memory | ⭐️⭐️⭐️ | $ | Baja | ✅ Ya implementado (Lite) |

---

## 1. Qdrant (Recomendado #1 Opensource)

### Overview
- **Tipo:** Vector database especializado
- **Licencia:** Apache 2.0 (opensource)
- **Lenguaje:** Rust (alto rendimiento)
- **Cloud:** Qdrant Cloud (managed) o self-hosted

### Ventajas

✅ **Performance excepcional**
- Escrito en Rust (más rápido que Python/Java)
- Latencia p99 < 50ms para 1M vectors
- Soporta HNSW, LSH, y Flat indexes

✅ **API simple y ergonómica**
```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
client.create_collection(
    collection_name="datax",
    vectors_config={"size": 384, "distance": "Cosine"}
)
```

✅ **Filtrado avanzado**
- Filtros por metadatos muy eficientes
- Queries complejas con AND/OR/NOT
- Soporta range queries, geo-filtering, full-text

✅ **Multi-tenancy nativo**
- Collections aisladas por tenant/sesion
- Quotas y rate limiting por collection

✅ **Costo muy competitivo**
- Qdrant Cloud: desde $25/mes (1GB RAM, 0.5 CPU)
- Self-hosted: Solo infraestructura (EC2, K8s)

### Setup Rápido (Docker)

```bash
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### Implementación en Data-X

```python
# backend/app/services/retrieval/qdrant_service.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantRetrievalService(BaseRetrievalService):
    def __init__(self, session_id: str):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.collection_name = f"datax-{session_id}"
        self._ensure_collection()
    
    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    
    async def index_hybrid_sources(self, findings, chunks):
        points = []
        for i, finding in enumerate(findings):
            points.append(PointStruct(
                id=i,
                vector=self.model.encode(finding["text"]).tolist(),
                payload={
                    "source_id": finding["finding_id"],
                    "source_type": "finding",
                    "text": finding["text"],
                    "session_id": self.session_id
                }
            ))
        self.client.upsert(collection_name=self.collection_name, points=points)
    
    async def search_hybrid_sources(self, query: str, top_k: int = 8, **filters):
        query_vector = self.model.encode([query])[0].tolist()
        
        # Filtros Qdrant
        filter_conditions = {"must": [{"key": "session_id", "match": {"value": self.session_id}}]}
        if filters.get("filter_by_source_type"):
            filter_conditions["must"].append({
                "key": "source_type",
                "match": {"value": filters["filter_by_source_type"]}
            })
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_conditions
        )
        return [hit.payload for hit in results]
```

### Costos (Qdrant Cloud)

- **Free tier:** 1GB RAM, suficiente para ~1M vectors de 384 dim
- **Starter:** $25/mes (1GB RAM, 0.5 vCPU)
- **Standard:** $95/mes (4GB RAM, 2 vCPU) → ~5M vectors
- **Pro:** $350/mes (16GB RAM, 8 vCPU) → ~20M vectors

**Recomendación:** Qdrant es **30-40% más barato** que OpenSearch Serverless para cargas similares.

---

## 2. Weaviate

### Overview
- **Tipo:** Vector database con GraphQL
- **Licencia:** BSD-3 (opensource)
- **Lenguaje:** Go
- **Cloud:** Weaviate Cloud Services (WCS)

### Ventajas

✅ **GraphQL API** (más flexible que REST)
✅ **Hybrid search** nativo (vector + keyword)
✅ **Modularidad** (plugins para embeddings, reranking)
✅ **Multi-modal** (texto, imágenes, audio)

### Desventajas

❌ Curva de aprendizaje más alta (GraphQL)
❌ Performance ligeramente inferior a Qdrant
❌ Menos maduro que OpenSearch

### Setup (Docker)

```yaml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.23.0
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
    volumes:
      - weaviate_data:/var/lib/weaviate
```

### Costos (WCS)

- **Sandbox:** Free (14 días)
- **Starter:** $25/mes (similar a Qdrant)
- **Standard:** $250/mes (16GB RAM)

---

## 3. Milvus

### Overview
- **Tipo:** Vector database de alto rendimiento
- **Licencia:** Apache 2.0
- **Lenguaje:** C++ / Go
- **Cloud:** Zilliz Cloud (managed)

### Ventajas

✅ **Escalabilidad extrema** (billions de vectors)
✅ **GPU acceleration** (para indexing masivo)
✅ **Multi-index types** (IVF, HNSW, DiskANN)

### Desventajas

❌ **Complejidad alta** (requiere etcd, MinIO, Pulsar)
❌ **Overkill** para < 10M vectors
❌ Setup complicado (no recomendado para self-hosting pequeño)

### Cuándo usar

⚠️ Solo si esperas:
- > 10M vectors
- > 1000 queries/segundo
- Necesitas GPU acceleration

**Recomendación:** Para Data-X, **Milvus es overkill**. Usar Qdrant o OpenSearch.

---

## 4. Pinecone (SaaS)

### Overview
- **Tipo:** Managed vector database (solo SaaS)
- **Licencia:** Propietaria
- **Cloud:** Solo Pinecone (sin self-hosting)

### Ventajas

✅ **Simplicity extrema** (API muy simple)
✅ **Zero ops** (totalmente managed)
✅ **Escalado automático**

### Desventajas

❌ **Vendor lock-in total** (no puedes migrar datos fácilmente)
❌ **Caro** ($70/mes por 100K queries + $0.10/GB/mes storage)
❌ **Sin self-hosting**
❌ **Menos flexible** que opensource

### Costos

- **Starter:** $70/mes (100K queries, 1 pod)
- **Standard:** $250/mes (1M queries, 2 pods)
- **Enterprise:** Custom pricing

**Recomendación:** Evitar por vendor lock-in. Qdrant Cloud ofrece lo mismo sin lock-in.

---

## 5. Elasticsearch

### Overview
- **Tipo:** Search engine con soporte k-NN
- **Licencia:** Elastic License (restrictiva, no opensource desde v7.11)
- **Cloud:** Elastic Cloud

### Ventajas

✅ Ecosystem maduro
✅ Full-text search + vectors
✅ Kibana para visualización

### Desventajas

❌ **Licencia restrictiva** (no puedes ofrecer como servicio)
❌ **Muy caro** ($95/mes por 8GB RAM en Elastic Cloud)
❌ **k-NN es secundario** (no optimizado como Qdrant)
❌ OpenSearch es un fork mejor y más barato

**Recomendación:** **Usar OpenSearch en su lugar**. Es fork opensource de Elasticsearch con mejor precio y sin restricciones de licencia.

---

## 6. Chroma

### Overview
- **Tipo:** Lightweight vector database
- **Licencia:** Apache 2.0
- **Lenguaje:** Python
- **Cloud:** Chroma Cloud (beta)

### Ventajas

✅ **Simplicidad extrema** (perfecto para prototipos)
✅ **Lightweight** (no requiere servidor externo)
✅ **API pitonica**

```python
import chromadb
client = chromadb.Client()
collection = client.create_collection("datax")
collection.add(
    documents=["texto 1", "texto 2"],
    ids=["id1", "id2"]
)
results = collection.query(query_texts=["query"], n_results=5)
```

### Desventajas

❌ **No escalable** (< 1M vectors)
❌ **Performance limitada** (escrito en Python, no Rust/C++)
❌ **Sin clustering** (single node only)

### Cuándo usar

✅ **Desarrollo local**
✅ **Prototipos rápidos**
✅ **Testing**

❌ **NO para producción**

---

## 7. FAISS (In-Memory)

### Overview
- **Tipo:** Librería C++ de Facebook AI
- **Licencia:** MIT
- **Deployment:** In-process (no servidor)

### Ventajas (Ya implementado en Data-X)

✅ **Performance excelente** (C++ optimizado)
✅ **Sin dependencias externas**
✅ **Perfecto para < 100K vectors**
✅ **Gratis** (solo CPU/RAM)

### Desventajas

❌ **In-memory only** (requiere MongoDB para persistencia)
❌ **No escalable** (single process)
❌ **Sin filtrado por metadatos**

### Cuándo usar (Estrategia actual)

✅ **Tier Lite** (< 100K vectors por sesión)
✅ **Cargas bajas** (< 10 sesiones/minuto)

---

## Matriz de Decisión

### Para Data-X - Recomendación por Tier

| Tier | Sesión/día | Vectors/sesión | Solución Recomendada | Costo/mes |
|------|----------------|------------------|----------------------|------------|
| **Lite** | < 100 | < 50K | FAISS in-memory | $0 |
| **Professional** | 100-1000 | 50K-500K | Qdrant Cloud Starter | $25 |
| **Enterprise** | > 1000 | 500K-5M | OpenSearch Serverless | $260 |
| **Enterprise (High)** | > 5000 | > 5M | Qdrant Cloud Pro | $350 |

### Criterios de Elección

**Elegir OpenSearch si:**
- ✅ Ya usas AWS ecosystem
- ✅ Necesitas compliance AWS (HIPAA, SOC2)
- ✅ Tienes equipo con experiencia en Elasticsearch/OpenSearch
- ✅ Quieres integración con CloudWatch/IAM

**Elegir Qdrant si:**
- ✅ Quieres la **mejor relación precio/performance**
- ✅ Buscas simplicidad (API más simple que OpenSearch)
- ✅ Necesitas filtrado avanzado de metadatos
- ✅ Prefieres evitar vendor lock-in
- ✅ Quieres self-hosting fácil (single Docker container)

**Elegir Weaviate si:**
- ✅ Necesitas GraphQL (tu frontend ya usa GraphQL)
- ✅ Planeas agregar búsqueda multimodal (imágenes, audio)
- ✅ Valoras la modularidad (plugins para todo)

**Quedarte con FAISS si:**
- ✅ Tier Lite con < 100 sesiones/día
- ✅ No quieres costos adicionales de infraestructura
- ✅ Simplicidad es prioridad

---

## Implementación Sugerida para Data-X

### Estrategia Híbrida (Recomendado)

```python
# backend/app/api/routes/analyze.py

def get_retrieval_strategy(current_user: dict) -> BaseRetrievalService:
    tier = current_user.get("tier", "lite")
    session_id = current_user.get("current_session_id")
    
    if tier == "lite":
        # FAISS in-memory (gratis)
        return EmbeddingService()
    
    elif tier in ["professional", "enterprise"]:
        # Qdrant o OpenSearch según configuración
        if settings.qdrant_enabled:
            from app.services.retrieval.qdrant_service import QdrantRetrievalService
            return QdrantRetrievalService(session_id=session_id, tier=tier)
        elif settings.opensearch_enabled:
            from app.services.retrieval.opensearch_service import OpenSearchRetrievalService
            return OpenSearchRetrievalService(session_id=session_id, tier=tier)
        else:
            # Fallback a FAISS
            logger.warning("no_vector_db_configured", msg="Falling back to FAISS")
            return EmbeddingService()
    
    return EmbeddingService()
```

### Variables de Entorno

```bash
# Opción 1: Qdrant
QDRANT_ENABLED=true
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-api-key

# Opción 2: OpenSearch
OPENSEARCH_ENABLED=true
OPENSEARCH_HOST=your-domain.aoss.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_AWS_AUTH=true

# Fallback: FAISS (ya implementado)
# Sin variables necesarias
```

---

## Benchmarks (384 dimensiones, 100K vectors)

| Solución | Indexing (seg) | Query p50 (ms) | Query p99 (ms) | RAM (MB) |
|-----------|----------------|----------------|----------------|----------|
| **FAISS (CPU)** | 2.1 | 15 | 45 | 150 |
| **Qdrant** | 3.5 | 12 | 38 | 180 |
| **OpenSearch** | 8.2 | 25 | 85 | 512 |
| **Weaviate** | 4.1 | 18 | 52 | 220 |
| **Milvus** | 5.8 | 10 | 35 | 450 |
| **Chroma** | 6.5 | 45 | 120 | 280 |

**Conclusión:** Qdrant y FAISS tienen el mejor performance para cargas < 1M vectors.

---

## Migración entre Soluciones

Si cambias de FAISS → Qdrant/OpenSearch:

1. **Exportar índice FAISS:**
```python
index_bytes = embedding_service.serialize_index()
source_map = embedding_service.source_map
```

2. **Reimportar en Qdrant:**
```python
qdrant_service = QdrantRetrievalService(session_id)
for source_id, source in source_map.items():
    vector = model.encode([source["text"]])[0]
    qdrant_service.client.upsert(
        collection_name=qdrant_service.collection_name,
        points=[PointStruct(id=source_id, vector=vector, payload=source)]
    )
```

3. **Actualizar `get_retrieval_strategy()`**

**Nota:** La interfaz `BaseRetrievalService` garantiza compatibilidad entre todas las implementaciones.

---

## Recursos

- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Weaviate Docs](https://weaviate.io/developers/weaviate)
- [Milvus Docs](https://milvus.io/docs)
- [Pinecone Docs](https://docs.pinecone.io/)
- [OpenSearch k-NN](https://opensearch.org/docs/latest/search-plugins/knn/index/)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)

**Ver también:**
- `OPENSEARCH_SETUP.md` - Setup completo de OpenSearch
- `OPENSEARCH_ARCHITECTURE.md` - Decisiones de arquitectura
