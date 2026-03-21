# Plan de Implementación — Corte 6

## Objetivo real del Corte 6

Completar la transición desde un MVP de análisis con Docling parcial hacia una plataforma Docling-first con:
- documento estructurado persistido
- RAG documental
- provenance
- UX documental visible

## Entregable de negocio

Al final del Corte 6, el usuario debe poder:
- subir un PDF/documento real
- ver cuántas tablas y contexto encontró el sistema
- navegar evidencia
- hacer preguntas sobre findings y sobre el documento
- confiar en el origen de cada respuesta

## Orden de ejecución

## Sprint 0 — Hardening
### Backend
- revisar config/JWT
- revisar timeouts Mongo
- cerrar deuda crítica de errores
- subir cobertura en rutas y servicios críticos

### Frontend
- polling con backoff
- export robusto
- manejo de errores consistente

## Sprint 1 — Bronze documental
### Backend
- persistir `DoclingDocument`
- guardar tablas múltiples
- guardar narrativa
- nuevo schema/document model

### Resultado esperado
La sesión ya no depende solo de una tabla elegida.

## Sprint 2 — RAG documental
### Backend
- introducir `HybridChunker`
- generar `doc_chunks`
- indexar findings + chunks
- actualizar analyze

### Resultado esperado
Preguntas sobre secciones, narrativa y documento completo.

## Sprint 3 — Provenance
### Backend
- agregar referencias de fuente a findings
- propagar página/sección/tabla/chunk

### Frontend
- panel de evidencia
- enlaces desde findings a evidencia

## Sprint 4 — UX Docling-first
### Frontend
- selector de tabla
- document explorer inicial
- copy orientado a valor documental
- preguntas sugeridas
- progreso no técnico

## Criterio de salida del Corte 6

El Corte 6 está completo cuando:
- el documento estructurado es persistente
- el query no depende solo de findings
- el usuario ve evidencia real
- el frontend comunica claramente el valor documental
