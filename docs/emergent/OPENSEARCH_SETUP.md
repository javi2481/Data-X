# OpenSearch Setup Guide

**Ref:** NXT-003 - OpenSearchRetrievalService para tiers Enterprise y Professional

---

## Overview

Esta guía cubre la configuración de OpenSearch para el retrieval vectorial k-NN en Data-X. OpenSearch reemplaza FAISS in-memory para tiers escalables.

**Ventajas de OpenSearch:**
- ✅ Persistencia nativa (no requiere MongoDB para índices)
- ✅ Escalabilidad horizontal
- ✅ Filtrado eficiente con DSL queries
- ✅ Soporte AWS nativo (Serverless y Managed)
- ✅ Actualizaciones incrementales

**Cuándo usar:**
- Tier **Enterprise**: > 1000 sesiones/día
- Tier **Professional**: > 100 sesiones/día
- Tier **Lite**: Usar FAISS (ya implementado)

---

## Opción 1: AWS OpenSearch Serverless (Recomendado para producción)

### Ventajas
- Sin gestión de infraestructura
- Escalado automático
- Alta disponibilidad por defecto
- Facturación por uso (OCU - OpenSearch Compute Units)

### Pasos de Setup

#### 1. Crear Colección Serverless

```bash
aws opensearchserverless create-collection \
  --name datax-prod \
  --type VECTORSEARCH \
  --description "Data-X vector search for enterprise tier"
```

#### 2. Configurar Data Access Policy

```json
[
  {
    "Rules": [
      {
        "Resource": ["collection/datax-prod"],
        "Permission": [
          "aoss:CreateIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ],
        "ResourceType": "collection"
      },
      {
        "Resource": ["index/datax-prod/*"],
        "Permission": [
          "aoss:CreateIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ],
        "ResourceType": "index"
      }
    ],
    "Principal": ["arn:aws:iam::ACCOUNT_ID:role/DataX-Backend-Role"],
    "Description": "Data access for DataX backend"
  }
]
```

Aplicar policy:

```bash
aws opensearchserverless create-access-policy \
  --name datax-data-access \
  --type data \
  --policy file://data-access-policy.json
```

#### 3. Configurar Network Policy (si usas VPC)

```json
[
  {
    "Rules": [
      {
        "Resource": ["collection/datax-prod"],
        "ResourceType": "collection"
      }
    ],
    "AllowFromPublic": false,
    "SourceVPCEs": ["vpce-xxxxxxxxx"]
  }
]
```

#### 4. Variables de Entorno para Data-X

```bash
# backend/.env
OPENSEARCH_ENABLED=true
OPENSEARCH_HOST=your-collection-id.us-east-1.aoss.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_USE_AWS_AUTH=true
OPENSEARCH_REGION=us-east-1
OPENSEARCH_SERVERLESS=true
```

#### 5. IAM Role para Backend

Asegurar que el backend tenga estos permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:us-east-1:ACCOUNT_ID:collection/*"
    }
  ]
}
```

#### 6. Instalar Dependencias

```bash
cd backend
pip install opensearch-py boto3 requests-aws4auth
```

#### 7. Verificar Conexión

```python
from app.services.retrieval.opensearch_service import OpenSearchRetrievalService

# Test connection
service = OpenSearchRetrievalService(session_id="test-123", tier="enterprise")
print("OpenSearch connected:", service.client is not None)
```

---

## Opción 2: AWS OpenSearch Service (Managed)

### Ventajas
- Control completo sobre configuración
- Soporte para plugins personalizados
- Costos predecibles (instancias reservadas)

### Pasos de Setup

#### 1. Crear Dominio

```bash
aws opensearch create-domain \
  --domain-name datax-prod \
  --engine-version OpenSearch_2.11 \
  --cluster-config InstanceType=t3.medium.search,InstanceCount=2 \
  --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=100 \
  --access-policies file://access-policy.json
```

**Access Policy** (`access-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/DataX-Backend-Role"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:ACCOUNT_ID:domain/datax-prod/*"
    }
  ]
}
```

#### 2. Variables de Entorno

```bash
OPENSEARCH_ENABLED=true
OPENSEARCH_HOST=search-datax-prod-xxxxx.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_USE_AWS_AUTH=true
OPENSEARCH_REGION=us-east-1
OPENSEARCH_SERVERLESS=false
```

#### 3. Habilitar k-NN Plugin

El plugin k-NN ya viene habilitado por defecto en OpenSearch 2.x. Verificar:

```bash
curl -XGET "https://YOUR_DOMAIN/_cat/plugins?v"
```

Deberías ver `opensearch-knn` en la lista.

---

## Opción 3: OpenSearch Self-Hosted (Docker)

### Ventajas
- Control total
- Sin costos de cloud
- Ideal para desarrollo y testing

### Docker Compose

Crear `docker-compose-opensearch.yml`:

```yaml
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: datax-opensearch
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true  # Solo para dev
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch-data:/usr/share/opensearch/data
    networks:
      - datax-network

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:2.11.0
    container_name: datax-opensearch-dashboards
    ports:
      - "5601:5601"
    environment:
      - OPENSEARCH_HOSTS=http://opensearch:9200
      - DISABLE_SECURITY_DASHBOARDS_PLUGIN=true
    depends_on:
      - opensearch
    networks:
      - datax-network

volumes:
  opensearch-data:

networks:
  datax-network:
    driver: bridge
```

Levantar:

```bash
docker-compose -f docker-compose-opensearch.yml up -d
```

### Variables de Entorno (Dev)

```bash
OPENSEARCH_ENABLED=true
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USE_SSL=false
OPENSEARCH_VERIFY_CERTS=false
OPENSEARCH_USE_AWS_AUTH=false
```

---

## Estrategia de Índices

### Índice Dinámico por Sesión (Implementado)

**Patrón:** `datax-{tier}-{session_id}`

**Ejemplo:**
- `datax-enterprise-abc123-456def-789ghi`
- `datax-professional-xyz789-012abc-345def`

**Ventajas:**
- ✅ Aislamiento perfecto entre análisis
- ✅ Cleanup fácil (borrar sesión = borrar índice)
- ✅ GDPR compliance automático
- ✅ Multi-tenancy natural

**Desventaja:**
- ❌ Overhead de creación (~500ms por sesión)

**Cuándo usar:** < 1000 sesiones/día

### Índice Global por Tier (Alternativa)

**Patrón:** `datax-{tier}`

**Ejemplo:**
- `datax-enterprise` (todos los usuarios enterprise)
- `datax-professional` (todos los usuarios professional)

**Ventajas:**
- ✅ Sin overhead de creación
- ✅ Mejor para alto volumen (> 1000 sesiones/día)

**Desventajas:**
- ❌ Requiere filtrado por `session_id` en cada query
- ❌ Cleanup más complejo (borrado por documento, no por índice)
- ❌ Requiere lifecycle policy para retention

**Implementación:**

Modificar `opensearch_service.py`:

```python
self.index_name = f"datax-{tier}"  # En lugar de incluir session_id

# En queries, agregar filtro obligatorio:
query_body["query"]["bool"]["filter"].append(
    {"term": {"session_id": self.session_id}}
)

# Lifecycle policy para retention (30 días):
PUT _plugins/_ism/policies/datax-retention-policy
{
  "policy": {
    "description": "Delete documents older than 30 days",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ]
  }
}
```

---

## Monitoring & Troubleshooting

### Verificar Salud del Cluster

```bash
curl -X GET "https://YOUR_DOMAIN/_cluster/health?pretty"
```

### Ver Índices Creados

```bash
curl -X GET "https://YOUR_DOMAIN/_cat/indices?v"
```

### Stats de k-NN

```bash
curl -X GET "https://YOUR_DOMAIN/_plugins/_knn/stats"
```

### CloudWatch Metrics (AWS)

Monitorear:
- `ClusterStatus.green`
- `SearchLatency` (p99 < 500ms)
- `IndexingLatency` (p99 < 1000ms)
- `KNNSearchRequests`
- `CPUUtilization` (< 80%)
- `JVMMemoryPressure` (< 85%)

### Logs Estructurados

Data-X loguea todos los eventos de OpenSearch:

```python
logger.info(
    "opensearch_search_complete",
    query=query[:50],
    results=len(results),
    latency_ms=elapsed
)
```

Filtrar en tu stack de logs:

```bash
# CloudWatch Logs Insights
fields @timestamp, @message
| filter @message like /opensearch/
| sort @timestamp desc
```

---

## Costos Estimados (AWS)

### OpenSearch Serverless

**OCU Pricing (us-east-1):**
- Indexing OCU: $0.24/hora
- Search OCU: $0.24/hora

**Ejemplo: 1000 sesiones/día**
- Indexing: 1 OCU continuo = $175/mes
- Search: 0.5 OCU promedio = $87/mes
- **Total: ~$262/mes**

### OpenSearch Managed

**Instancias (us-east-1):**
- `t3.medium.search` (2 nodos): $120/mes
- EBS gp3 (200GB): $16/mes
- **Total: ~$136/mes**

**Recomendación:** Usar Managed para cargas predecibles, Serverless para spikes.

---

## Next Steps

1. ✅ Elegir opción de deployment (Serverless, Managed, Self-hosted)
2. ✅ Configurar variables de entorno en `backend/.env`
3. ✅ Instalar dependencias: `opensearch-py`, `boto3`, `requests-aws4auth`
4. ✅ Configurar tier en `get_retrieval_strategy()` (ya implementado)
5. ✅ Testing inicial con sesión de prueba
6. ⚠️ Configurar monitoring y alertas
7. ⚠️ Implementar lifecycle policies para retention
8. ⚠️ Configurar backups (snapshots)

**Ver también:**
- `OPENSEARCH_ALTERNATIVES.md` - Alternativas opensource
- `OPENSEARCH_ARCHITECTURE.md` - Decisiones de diseño
