# PRD Frontend

## Objetivo

Evolucionar el frontend actual para que haga visible el valor Docling-first y no se limite a presentar findings de dataset.

## Estado actual

Ya existe:
- landing
- login/register
- workspace
- findings
- charts
- query panel
- export
- historial

## Gap principal

El frontend todavía comunica más “dataset analysis” que “document intelligence”.

## Objetivo UX

El usuario debe sentir que:
- el sistema entendió su documento
- encontró tablas y contexto
- puede preguntar sobre el documento
- cada hallazgo tiene evidencia

## Flujos que deben existir al final del Corte 6

### 1. Upload
El usuario ve que puede subir CSV/XLSX/PDF/DOCX.

### 2. Processing
Mensajes de progreso orientados a valor, no a jerga técnica.

### 3. Resultados
- findings claros
- evidencia visible
- tablas detectadas
- narrativa utilizable

### 4. Query
Preguntas sobre findings y documento.

### 5. Exploración
- selector de tabla
- explorer documental inicial
- provenance panel

## Componentes a crear o reforzar

- `DocumentExplorer`
- `TableSelector`
- `EvidencePanel`
- mejoras en `QueryPanel`
- mejoras en `FileUploader`
- mejoras en `Workspace`

## Regla de presentación

Primero:
- valor
- explicación
- evidencia

Después:
- detalle técnico
- estructura
- debugging

## Criterio de éxito

El frontend deja de parecer una app para CSV con soporte PDF y pasa a parecer una plataforma capaz de entender documentos reales.
