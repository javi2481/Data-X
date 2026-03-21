# PRD Backend

## Objetivo

Reconfigurar el backend para que el documento estructurado sea el activo central del sistema, sin perder las capacidades ya construidas del pipeline Bronze / Silver / Gold.

## Estado actual

Ya existe:
- FastAPI
- auth
- sesiones
- reportes
- findings
- RAG básico
- Docling en ingesta
- Mongo
- embeddings
- LiteLLM

## Gap principal

El backend todavía degrada el documento demasiado pronto hacia un DataFrame.

## Objetivo técnico

Pasar de:
`documento -> tabla elegida -> DataFrame`

a:
`documento -> DoclingDocument persistido -> tablas + narrativa + chunks + provenance -> findings + query`

## Responsabilidades

- upload y sesiones
- auth
- persistencia documental
- findings
- retrieval
- APIs para frontend
- provenance

## Nuevas entidades recomendadas

- `DoclingRawDocument`
- `DocumentTable`
- `DocumentChunk`
- `EvidenceReference`
- `SourceLocation`

## Cambios prioritarios

### 1. Persistencia Bronze
Guardar:
- `DoclingDocument`
- metadata estructural
- tablas múltiples
- narrativa

### 2. Chunking
- introducir chunker semántico
- persistir `doc_chunks`

### 3. Retrieval
- indexar findings + chunks
- combinar ambos en `analyze`

### 4. Provenance
- llevar source refs a findings y respuestas

## APIs a reforzar

- `POST /api/sessions`
- `GET /api/sessions/{id}/report`
- `POST /api/analyze`
- nuevas lecturas documentales si hacen falta:
  - `GET /api/sessions/{id}/document`
  - `GET /api/sessions/{id}/tables`
  - `GET /api/sessions/{id}/chunks`

## No funcionales

- robustez
- limpieza de temporales
- mejores timeouts
- trazabilidad
- contratos estables
