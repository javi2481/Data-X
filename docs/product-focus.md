# Product Focus — Data-X
*Última actualización: Marzo 2026*

## Qué es Data-X
Plataforma de análisis conversacional determinista. El usuario sube documentos empresariales y hace preguntas en lenguaje natural, recibiendo análisis estadístico real y verificable. **El cálculo es interno. La interpretación es el producto.**

## Posicionamiento
**"El único analizador que te muestra cómo llegó a cada conclusión, adaptado a tu escala."**

Data-X ocupa una categoría nueva: **Inferencia Estadística Determinística con Soporte Documental No Estructurado.** Es una herramienta accesible para individuos y PyMEs, pero lo suficientemente robusta para escalar al entorno Enterprise.

- No es un chatbot (no adivina números).
- No es una caja negra (brinda provenance y calidad geométrica).

## Arquitectura Multi-Tier (Segmentación Tecnológica)
Para asegurar márgenes de rentabilidad (Unit Economics), Data-X adapta su motor interno según el plan del cliente, operando bajo un **Patrón Strategy** en el backend.

| Característica | Tier "Lite" (Free / PyMEs) | Tier "Enterprise" (Corp / API) |
| :--- | :--- | :--- |
| **Casos de Uso** | 10-50 PDFs/mes, consultas simples. | +50.000 documentos, manuales, históricos. |
| **Motor de Ingesta** | `StandardIngestionService` (DoclingRouter + ARQ/Redis). | `DistributedIngestionService` (IBM Data Prep Kit + Ray/Spark). |
| **Motor RAG** | `FaissRetrievalService` (Caché en memoria). | `OpenSearchRetrievalService` (Motor Distribuido). |
| **Tipo de Búsqueda** | Búsqueda Vectorial Pura. | Búsqueda Híbrida (Vectores + BM25 Léxico). |

## Los 5 diferenciales reales
1. **Calidad de Extracción Adaptable:** Desde un Docling embebido hasta clústeres de ingesta masiva con IBM Data Prep Kit.
2. **El LLM nunca computa:** Código duro (Pandas, OpenCV, SciPy) precalcula; PydanticAI orquesta y narra.
3. **Seguridad Zero Trust:** SensitiveDataGuard + FraudGuard (Forense PDF, Visual y Numérico) antes de que el LLM vea el dato.
4. **Transparencia Técnica Auditable:** Panel con stats crudas, contexto del LLM, y score de confianza validado.
5. **Aislamiento Corporativo:** OpenSearch + MongoDB multi-tenant aseguran que los datos nunca se crucen.