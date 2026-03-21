# Data-X — Home

## Qué es Data-X hoy

Data-X ya es un producto funcional, no un concepto:
- backend FastAPI operativo
- frontend Next.js usable
- autenticación y sesiones
- pipeline Bronze → Silver → Gold
- findings determinísticos
- reportes, export y query panel
- integración parcial de Docling para PDFs/documentos

## Qué problema tenemos

El sistema ya funciona, pero todavía usa Docling de forma parcial.

Hoy el flujo real es, en esencia:

`Docling -> selección de tabla -> DataFrame -> findings -> embeddings -> LLM`

Ese flujo sirve para un MVP, pero no alcanza para la visión objetivo.

## Hacia dónde vamos

Data-X debe pasar a ser un producto **Docling-first**:

`DoclingDocument completo -> tablas + narrativa + chunks + provenance -> findings + RAG documental + evidencia verificable`

## Tesis central

**Docling no es una librería auxiliar.  
Docling es el subsistema documental central del producto.**

## Estado actual resumido

### Ya existe
- ingestión de CSV, XLSX y PDF
- findings, charts y reportes
- historial de sesiones
- query sobre análisis
- export
- auth básica
- arquitectura modular suficiente para iterar

### Falta
- persistir `DoclingDocument` completo
- usar todas las tablas del documento
- chunking semántico real
- provenance fuerte
- query sobre documento, no solo sobre findings
- explorer documental en frontend

## Modo de trabajo

- **Cursor**: entorno principal de desarrollo
- **Emergent**: puede leer todo; solo modifica `backend/` con autorización explícita
- **v0**: puede leer todo; solo modifica `frontend/` con autorización explícita
- **docs/**: fuente de verdad; no se editan automáticamente

## Prioridad actual

No hacer más features aisladas.

La prioridad es:
1. consolidar el plano documental
2. reconectar RAG con el documento
3. exponer evidencia/provenance
4. hacer visible el valor Docling en la UX
