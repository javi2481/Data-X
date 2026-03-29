# Arquitectura Multi-Tier: El Patrón Strategy en Data-X
*Documento de Diseño Interno — Marzo 2026*

## El Problema
Data-X atiende a dos públicos distintos:
1. **B2C/PyME:** Requieren velocidad, bajo costo de servidor, y bajo volumen de documentos.
2. **B2B Enterprise:** Requieren ingesta masiva (miles de PDFs), búsqueda corporativa exacta y alta disponibilidad.

Usar infraestructura Enterprise (OpenSearch, IBM Data Prep Kit) para usuarios B2C destruye la rentabilidad (Unit Economics). Usar infraestructura Lite (FAISS, embebidos) para usuarios B2B destruye la performance.

## La Solución: Patrón Strategy + Inyección de Dependencias
El backend de FastAPI decidirá en **tiempo de ejecución** qué motor utilizar, leyendo el perfil del cliente desde MongoDB, sin alterar la lógica de negocio core (PydanticAI, Docling, FraudGuard).

### 1. Strategy de Recuperación (RAG)

```python
# app/services/retrieval/base.py
from abc import ABC, abstractmethod

class BaseRetrievalService(ABC):
    @abstractmethod
    async def search(self, session_id: str, query: str, top_k: int) -> list[dict]:
        pass
    
    @abstractmethod
    async def index_document(self, session_id: str, vectors: list, metadata: dict) -> bool:
        pass
```

### 2. Strategy de Motores (Ejemplo de uso)

| Componente | Implementación "Lite" (B2C) | Implementación "Enterprise" (B2B) | Justificación |
| :--- | :--- | :--- | :--- |
| **RAG / DB Vectorial** | `FaissRetrievalService` (In-memory, transitorio, idle cost $0) | `OpenSearchRetrievalService` (Cluster dedicado, persistente, RBAC nativo) | OpenSearch asegura escalabilidad e indexación histórica; FAISS minimiza costos de servidor para picos de uso esporádicos B2C. |
| **Ingesta Documental** | `DoclingRouter` (Embebido local / Container compartido) | `DistributedIngestionService` (IBM Data Prep Kit en Ray/Spark) | Evitamos levantar clusters pesados para usuarios que solo analizan un CSV o PDF corto. |
| **PII / Redaction** | `SensitiveDataGuard` (Python Regex en FastAPI) | Redacción en batch delegada al pipeline distribuido. | Optimización de CPU en el API principal. |
| **Observabilidad** | `structlog` (Logs estructurados simples) | `OpenTelemetry` (Traces distribuidos APM) | B2B requiere SLAs estrictos; si el pipeline falla, OpenTelemetry indica el milisegundo exacto y el nodo (FastAPI vs Worker) del fallo. |

### Conclusión
Con este diseño, Data-X es fundamentalmente un producto **orientado al usuario final (B2C)** en su experiencia de usuario (UX limpia, explorador de documentos intuitivo), pero tiene el "motor intercambiable" bajo el capó para cerrar ventas corporativas sin tener que reescribir el código base.