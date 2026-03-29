# Docling Strategy — Core Subsystem

## Decisión estratégica

Data-X se reconvierte a una arquitectura **Docling-first**.

Eso significa que Docling deja de ser tratado como:
- parser de PDF
- helper para extraer una tabla
- paso previo antes del DataFrame

Y pasa a ser tratado como:
- subsistema documental
- fuente de estructura
- fuente de contexto
- base para provenance
- base para chunking semántico
- base para query documental

## Estado actual

Hoy Docling ya está integrado, pero su uso es parcial:
- convierte documentos
- detecta tablas
- aporta contexto narrativo básico
- luego el sistema se apoya demasiado rápido en un DataFrame seleccionado

Ese diseño fue correcto para llegar a un MVP, pero limita el diferencial del producto.

## Estado objetivo

El activo central de una sesión debe ser el **documento estructurado**, no solo la tabla elegida.

### Flujo objetivo

1. archivo subido
2. **DoclingRouter decide**: embebido (chico) o docling-serve (grande)
3. procesamiento con Docling
4. persistencia de `DoclingDocument`
5. extracción de:
   - tablas
   - narrativa
   - metadatos estructurales
   - referencias de origen
6. chunking semántico
7. **SensitiveDataGuard** filtra columnas sensibles
8. **ydata-profiling** genera ProfilingSummary (L2)
9. findings y query sobre:
   - findings (consumen ProfilingSummary)
   - tablas
   - narrativa
   - chunks
10. **ContextBuilder** serializa a Markdown con budget de tokens
11. respuestas con evidencia verificable

## Capacidades Docling que deben entrar en Data-X

### 1. Documento estructurado completo
Guardar `DoclingDocument.export_to_dict()` o equivalente persistible.

### 2. Multi-tabla real
No quedarse con una tabla. Guardar y explotar todas las tablas relevantes.

### 3. Narrativa documental
Usar `doc.texts` y/o equivalente para preguntas sobre:
- riesgos
- notas
- observaciones
- explicaciones del documento

### 4. Chunking semántico
Adoptar `HybridChunker` o estrategia equivalente para:
- RAG documental
- recuperación más fiel
- trazabilidad por chunk

### 5. Provenance
Cada finding importante debe poder señalar:
- archivo
- página
- sección
- tabla
- fila o chunk cuando aplique

## Qué no hacer

- aplanar el documento demasiado temprano
- tratar Docling como una librería auxiliar más
- construir nuevas features sobre un modelo documental incompleto
- mover a microservicios antes de consolidar el modelo documental local

## Orden correcto

### Completado
- Persistencia de `DoclingDocument`
- Multi-tabla persistente
- Chunking semántico híbrido
- Mapeo Automático de Provenance (Findings <-> Chunks)
- RAG documental híbrido (Findings + Chunks)
- Evidencia visible en FindingCard y QueryPanel
- Provenance Visual: PDF rendering real con bboxes resaltados
- Endpoint de Imágenes: Servir páginas de PDF para el frontend
- Interoperabilidad: Navegación cross-tab (Evidencia -> Documento)

### Ahora
- **DoclingRouter Híbrido**: Routing embebido/serve por tamaño de archivo
- **Deploy docling-serve**: Container separado en Railway (CPU)
- **Profiling L2**: ydata-profiling como fuente de verdad estadística descriptiva
- **SensitiveDataGuard**: Protección de datos sensibles pre-profiling
- **ContextBuilder**: Serialización Markdown con budget de tokens para LLM

### Después
- Explorer documental interactivo enriquecido
- Comparación de datasets entre sesiones (profiler.compare())
- Time-series profiling on-demand (tsmode=True)
- **PydanticAI Agent para queries multi-paso**: Evolución de `/api/analyze` — el agente usa tools para responder preguntas complejas. La capa agéntica solo opera en la fase de query.
- **Docling PII nativo**: Complementar SensitiveDataGuard (columnas) con la detección PII de Docling (narrativa).
- **OCR configurable**: Parámetro `accuracy=fast|high` en DoclingRouter (Tesseract vs SuryaOCR).
- **OpenCV como única capa visual complementaria** (Fase 7):
  - Pre-Docling: quality gate (Laplaciano), deskew (con `cv2.minAreaRect`), CLAHE, denoising.
  - Post-Docling: validación auditando la metadata nativa de Docling (confidence de TableFormer) usando OpenCV puro como backup (sin dependencias extra).
  - Enriquecimiento: QR codes (pyzbar), firmas, sellos → PictureItem con ProvenanceItem
- **FraudGuard: detección de fraude documental** (Fase 8):
  - Layer 1: PDF forensics (pikepdf metadata + pdfminer.six fuentes + pyhanko firmas)
  - Layer 2: Visual forensics nativo (Algoritmo ELA implementado directamente con OpenCV `cv2.absdiff`).
  - Layer 3: Numérico (benford_py + validación matemática + Z-Score)
- **FraudGuard: detección de fraude documental** (Fase 8):
  - Layer 1: PDF forensics (pikepdf metadata + pdfminer.six fuentes + pyhanko firmas)
  - Layer 2: Visual forensics nativo (Algoritmo ELA implementado directamente con OpenCV `cv2.absdiff`).
  - Layer 3: Numérico (benford_py + validación matemática + Z-Score)
  - Layer 4: Cruzado/Fiscal (satcfdi SAT México + PyAfipWs AFIP + cross-document)
  - Produce FraudReport con risk_score, findings con evidence, integrado al provenance
- Desacople operativo mediante workers/colas (ARQ + Redis)
- docling-serve con GPU para clientes enterprise

### Mucho después
- **VLM Pipeline para gráficos embebidos**: Docling extrae imágenes → VLM → FAISS
- **XBRL support**: balances financieros enterprise (bancos, estudios contables LATAM)
- **Information Extraction con templates Pydantic** por vertical (financiero, legal, médico)
- Layer 5 FraudGuard: detección de documentos AI-generated (gap actual en open-source)
- Detección avanzada de firmas (sigver CNN) y sellos (stamp2vec embeddings)
- `docling-graph`: Grafos semánticos sobre documentos para RAG avanzado
- Escalabilidad enterprise con motores distribuidos

## Qué NO hacer (reforzado)

- No meter frameworks agénticos (CrewAI, LangGraph, LlamaIndex) en el pipeline de ingesta
- n8n no reemplaza al pipeline_orchestrator
- La capa agéntica solo opera en queries del usuario (PydanticAI)
- **OpenCV no reduce a Docling** — lo refuerza dándole mejor input y validando su output
- Toda feature de OpenCV debe responder: ¿esto hace que Docling funcione mejor, o agrega valor donde Docling no llega?
- **FraudGuard nunca usa lenguaje absoluto** — scores de riesgo, no "este documento es fraudulento"
- No usar opencv-python (con GUI) en contenedores — siempre opencv-python-headless
- No correr corrección de perspectiva en el event loop de FastAPI — delegar a ARQ worker
- TruFor solo para benchmarks/investigación — licencia no-comercial

## Regla de producto (actualizada)

Toda decisión nueva debe responder:

> ¿Estamos reforzando a Docling como subsistema central, o lo estamos reduciendo otra vez a un parser de apoyo?

Y para OpenCV/FraudGuard, la segunda pregunta:

> ¿Esto hace que Docling funcione mejor, o agrega valor donde Docling no llega? Si ninguna de las dos, no entra.

### Actualización Final: 2026-03-24
En implementación: DoclingRouter híbrido, Profiling L2 con ydata-profiling, SensitiveDataGuard, ContextBuilder.
En roadmap: OpenCV como capa visual (Fase 7), FraudGuard detección de fraude (Fase 8), PydanticAI Agent (Fase 6).
