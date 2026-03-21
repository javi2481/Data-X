# Data-X: Document-Analytical Platform PRD

## Original Problem Statement
Auditar el repositorio Data-X existente, cruzar con el ecosistema Docling oficial, y ejecutar un plan de implementación para transicionar la aplicación a una arquitectura "Docling-first" con provenance completo de documentos (ubicación fuente, chunks, bounding boxes) para findings y UI frontend.

## Architecture Overview
```
/app/data-x-audit/
├── backend/         # FastAPI backend
│   ├── app/
│   │   ├── api/routes/
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── repositories/ # Data access
│   └── tests/
├── frontend/        # Next.js frontend (React/TypeScript)
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── types/        # TypeScript contracts
└── docs/            # Strategic documentation
```

## Tech Stack
- **Backend**: FastAPI, Python 3.11+, Pydantic v2
- **Frontend**: Next.js, React, TypeScript
- **Database**: MongoDB (via Motor async driver)
- **Document Processing**: Docling (DocumentConverter)
- **Architecture**: Medallion (Bronze/Silver/Gold pipelines)
- **Embeddings**: FAISS

---

## Sprint 0: Foundation of Provenance ✅ COMPLETED (2024-12-XX)

### What was implemented

#### 1. Backend Schemas (`backend/app/schemas/`)

**finding.py** - Added:
- `BoundingBox`: Coordenadas de elementos en el documento (l, t, r, b, coord_origin)
- `SourceLocation`: Ubicación precisa con page, bbox, heading, section_path, table_id, row_range, cell_ref, char_offset
- `DocumentChunk`: Chunk con provenance completo (chunk_id, session_id, text, snippet, source_type, source_id, location)
- Updated `Evidence` to include `source_location`
- Updated `Finding` to include `source_locations` and `source_chunk_ids`

**analyze.py** - Added:
- Updated `SourceReference` with `location` (SourceLocation) and `chunk_id` fields

#### 2. Frontend Contracts (`frontend/src/types/contracts.ts`)

Added TypeScript interfaces:
- `BoundingBox`
- `SourceLocation`
- `DocumentChunk`
- Updated `Evidence` with `source_location`
- Updated `Finding` with `source_locations` and `source_chunk_ids`
- Updated `EvidenceSource` with `location` and `chunk_id`
- Updated `SourceType` to include "heading"

#### 3. DocumentChunkingService (`backend/app/services/document_chunking_service.py`)

Complete refactor to extract Docling provenance:
- Accepts `document_payload` parameter from Docling
- Extracts page numbers, bounding boxes, headings, section paths
- Supports multiple Docling formats: `texts` array, `body` structure
- Parses bbox in dict format (`{l,t,r,b}`), list format (`[l,t,r,b]`), and x0/y0 format
- Maps Docling types (paragraph, heading, list-item, etc.) to schema source_types
- Fallback to character-based chunking when no document_payload

#### 4. Sessions Route (`backend/app/api/routes/sessions.py`)

Updated `create_session` to pass `document_payload` to chunking service.

#### 5. Tests (`backend/tests/`)

- `test_chunking_provenance.py`: 10+ unit tests for provenance extraction
- Updated `test_embeddings.py` for new signature

### Design Decisions

1. **Backward Compatibility**: Fallback chunking when `document_payload` is None
2. **Flexible Bbox Parsing**: Supports multiple Docling formats
3. **Optional Provenance Fields**: All location fields are Optional to handle partial data
4. **Tuple Types**: Used for `row_range` and `char_offset` to represent ranges

### Tests Added
- `test_fallback_chunking_without_document_payload`
- `test_docling_provenance_extraction_with_texts_array`
- `test_docling_provenance_extraction_with_body`
- `test_table_chunks_with_provenance`
- `test_bbox_parsing_dict_format`
- `test_bbox_parsing_list_format`
- `test_bbox_parsing_x0_y0_format`
- `test_source_type_mapping`
- `test_empty_document_payload_returns_fallback`
- `test_chunk_order_is_sequential`

### Risks
- Motor/PyMongo version incompatibility (known issue, needs resolution)
- Docling payload structure may vary between versions

---

## Upcoming Tasks

### Sprint 1: Docling HybridChunker Integration (P1)
- [ ] Integrate `HybridChunker` from docling-core
- [ ] Create `DoclingChunkingService` as wrapper
- [ ] Create `EvidencePanel.tsx` frontend component
- [ ] Expand sources display in `QueryPanel.tsx`
- [ ] Update UI copy to reflect Docling context

### Sprint 2: Enhanced Document Intelligence (P2)
- [ ] Generate suggested questions from document structure
- [ ] Add functional table selector
- [ ] Update documentation

---

## Backlog (Future)
- PDF page viewer with bbox highlighting
- Multi-document session support
- Document comparison features
- Export provenance to standard formats
