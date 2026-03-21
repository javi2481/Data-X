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

## Sprint 0: Foundation of Provenance ✅ COMPLETED

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

---

## Sprint 1: HybridChunker Integration ✅ COMPLETED

### What was implemented

#### 1. DoclingChunkingService (`backend/app/services/docling_chunking_service.py`)

New service using Docling's HybridChunker:
- Token-aware chunk sizing (default 512 tokens, configurable)
- Uses HuggingFace tokenizer (sentence-transformers/all-MiniLM-L6-v2)
- Preserves document hierarchy (headings, sections)
- Extracts full provenance (page, bbox, heading path)
- Falls back to legacy DocumentChunkingService if unavailable
- Singleton pattern via `get_docling_chunking_service()`

#### 2. EvidencePanel (`frontend/src/components/EvidencePanel.tsx`)

New React component for displaying source provenance:
- Shows page numbers, bounding boxes, section paths
- Displays table references
- Shows match scores when available
- Snippet preview for each source
- Clickable sources to navigate to findings

#### 3. QueryPanel Updates (`frontend/src/components/QueryPanel.tsx`)

Enhanced with provenance display:
- Toggle between simple badges and detailed EvidencePanel
- Page number display in compact view
- Integration with EvidencePanel for detailed view

#### 4. FindingCard Updates (`frontend/src/components/FindingCard.tsx`)

Added provenance display:
- `source_locations` display with page/heading/table info
- `source_chunk_ids` display for related fragments
- New `SourceLocationBadge` helper component

#### 5. Sessions Route (`backend/app/api/routes/sessions.py`)

Updated to use DoclingChunkingService:
- Uses HybridChunker when `document_payload` is available
- Falls back to legacy chunking for CSV files
- Imported `get_docling_chunking_service`

#### 6. Tests (`backend/tests/test_docling_chunking_service.py`)

New test file with:
- Service initialization tests
- Singleton pattern tests
- Fallback behavior tests
- Bbox parsing tests
- Chunk field validation tests
- Integration tests for HybridChunker

### Design Decisions

1. **Optional HybridChunker**: Service works even if HybridChunker import fails
2. **Token-aware sizing**: Default 512 tokens aligns with embedding model limits
3. **Singleton service**: Reuse initialized tokenizer for performance
4. **Progressive disclosure**: Simple view by default, detailed provenance on demand

---

## Upcoming Tasks

### Sprint 2: Enhanced Document Intelligence (P1)
- [ ] Generate suggested questions from document structure
- [ ] Add functional table selector in UI
- [ ] Update documentation

---

## Backlog (Future)
- PDF page viewer with bbox highlighting
- Multi-document session support
- Document comparison features
- Export provenance to standard formats
- Real-time collaboration features
