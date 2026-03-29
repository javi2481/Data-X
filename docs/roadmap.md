Fase 10 — Infraestructura Multi-Tier y Patrón Strategy (Semanas 28-31) ← **NUEVO**
*Objetivo: Desacoplar la infraestructura de ingesta y búsqueda para soportar el modelo de negocio B2C (Lite) vs B2B (Enterprise).*

- [ ] **Core Architecture:** Implementar Patrón Strategy en el backend de FastAPI.
- [ ] **Capa de Búsqueda (Retrieval Strategy):**
  - [ ] Interfaz base: `BaseRetrievalService`
  - [ ] Implementación 1: `FaissRetrievalService` (Mantiene el sistema actual en memoria para B2C).
  - [ ] Implementación 2: `OpenSearchRetrievalService` (Búsqueda híbrida para B2B).
  - [ ] Inyección de dependencias dinámica en `/api/analyze` basada en el `tenant_id` y su plan.
- [ ] **Capa de Ingesta Masiva (Ingestion Strategy):**
  - [ ] Interfaz base: `BaseIngestionOrchestrator`
  - [ ] Implementación 1: `StandardIngestionService` (Uso actual de DoclingRouter + ARQ/Redis).
  - [ ] Implementación 2: `DistributedIngestionService` (Integración de **IBM Data Prep Kit** para procesamiento por lotes masivos, redacción PII y paralelización con Ray).
- [ ] **Optimización Cognitiva (LLM):**
  - [ ] Actualizar *System Prompts* de PydanticAI implementando técnica **CoD (Chain of Drafts)** para reducir latencia y consumo de tokens.
  - [ ] Implementar técnica **AoT (Atom of Thoughts)** en las *Tools* del agente para razonamiento seguro de datos espaciales y metadatos de OpenSearch.