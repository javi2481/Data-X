# Arquitectura y Ownership

## Estado actual

La base actual es correcta:
- FastAPI como API principal
- Next.js como frontend
- MongoDB como persistencia
- pipeline Bronze / Silver / Gold
- Docling como ingesta documental parcial
- LiteLLM para enriquecimiento y query

## Problema actual

La arquitectura sigue demasiado centrada en el DataFrame como activo principal.

Eso limita:
- query documental
- provenance
- múltiples tablas
- narrativa
- trazabilidad fina

## Arquitectura objetivo

### 1. Product/API plane
Responsable de:
- auth
- sesiones
- usuarios
- jobs
- exposición de APIs
- control de estado

### 2. Document plane
Responsable de:
- ingestión Docling
- `DoclingDocument`
- tablas
- narrativa
- chunks
- provenance

### 3. Insight plane
Responsable de:
- profiling
- findings
- charts
- enriquecimiento
- RAG sobre findings y chunks

### 4. Experience plane
Responsable de:
- upload
- workspace
- findings UI
- explorer documental
- panel de evidencia
- query

## Principios

1. **Docling-first**
2. **Contracts are Sacred**
3. **Backend calcula, frontend renderiza**
4. **El documento estructurado es un activo persistente**
5. **Toda respuesta importante debe ser trazable**

## Ownership

### Cursor
- herramienta principal de implementación
- backend + frontend
- refactors
- integración

### Emergent
- puede leer todo
- puede auditar backend
- solo modifica `backend/` con autorización explícita

### v0
- puede leer todo
- puede auditar frontend
- solo modifica `frontend/` con autorización explícita

### docs/
- fuente de verdad
- lectura para todos
- edición manual y deliberada

## Regla operativa

Ningún agente redefine estrategia desde código.

La estrategia vive en:
- `docs/`
- PRDs
- roadmap
- este archivo
