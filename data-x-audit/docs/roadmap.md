# Roadmap

## Punto de partida real

Data-X ya cuenta con:
- auth y sesiones
- ingestión de CSV/XLSX/PDF
- pipeline Bronze → Silver → Gold
- findings y charts
- reportes y export
- query panel
- frontend usable

No estamos arrancando de cero.

## Objetivo del roadmap

Recentrar el producto en el documento estructurado y completar la reconversión a un sistema Docling-first.

## Fase 0 — Hardening

### Objetivo
Cerrar deuda técnica que afecta confianza y estabilidad.

### Trabajo
- JWT/config segura
- Mongo con timeout/pool
- polling con backoff
- export JSON con Blob
- sincronización de explanations
- más tests críticos

## Fase 1 — Bronze documental real

### Objetivo
Persistir el documento estructurado como activo principal.

### Trabajo
- guardar `DoclingDocument`
- guardar todas las tablas
- guardar narrativa
- guardar metadata estructural
- preparar referencias de provenance

## Fase 2 — RAG documental real

### Objetivo
Permitir preguntas sobre documento, no solo sobre findings.

### Trabajo
- `HybridChunker`
- `doc_chunks`
- embeddings de chunks
- índice combinado findings + chunks
- actualizar `/api/analyze`

## Fase 3 — Provenance verificable

### Objetivo
Que cada hallazgo importante pueda rastrearse al origen.

### Trabajo
- `source_location`
- referencias de página/sección/tabla/chunk
- panel de evidencia
- findings enlazables a origen

## Fase 4 — UX Docling-first

### Objetivo
Hacer visible el valor diferencial del plano documental.

### Trabajo
- document explorer
- selector de tabla
- mejor copy de uploader/progreso
- preguntas sugeridas
- evidencia visible en UI

## Fase 5 — Escalabilidad operativa

### Objetivo
Aislar procesamiento pesado cuando el uso lo exija.

### Trabajo
- jobs o workers
- colas
- posible desacople de Docling
- evaluar `docling-serve` solo si hay necesidad real

## Qué no entra ahora

- grafos semánticos
- complejidad enterprise prematura
- dashboards custom tipo BI generalista
- microservicios por moda
