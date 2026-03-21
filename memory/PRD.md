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

## Sprint 2: Enhanced Document Intelligence ✅ COMPLETED

### What was implemented

#### 1. Motor/PyMongo Compatibility Fix

**Problem**: Motor 3.3.1 incompatible with PyMongo 4.16.0 (`_QUERY_OPTIONS` import error)

**Solution**: Pinned versions in `requirements.txt`:
```
pymongo>=4.5.0,<4.9
motor>=3.3.0,<3.6
```

**Note**: Motor is deprecated (EOL May 2026). Future migration to PyMongo Async API recommended.

#### 2. SuggestedQuestionsService (`backend/app/services/suggested_questions_service.py`)

New service for generating contextual questions:
- Questions based on finding categories and severity
- Questions from document structure (headings, sections)
- Questions from table metadata
- Priority-based ordering
- Deduplication
- Template-based generation

#### 3. Suggested Questions API Endpoint (`backend/app/api/routes/analyze.py`)

New endpoint: `GET /api/analyze/{session_id}/suggested-questions`
- Returns prioritized questions
- Context-aware generation
- Rate limited (100/hour)

#### 4. SuggestedQuestions Component (`frontend/src/components/SuggestedQuestions.tsx`)

New React component:
- Displays contextual questions with icons
- Click to fill query input
- Collapsible panel
- Refresh capability
- Category-based coloring

#### 5. QueryPanel Integration

- SuggestedQuestions shown when no result displayed
- Click fills query input automatically

#### 6. DocumentContextPanel Enhancement (`frontend/src/components/DocumentContextPanel.tsx`)

Functional table selector:
- Visual indication of selected table
- Confidence score display
- Click to select different table
- Loading state during re-analysis
- Expandable context viewer

#### 7. uv Migration Analysis (`docs/UV_MIGRATION_ANALYSIS.md`)

Comprehensive analysis document:
- Comparison pip vs uv
- Migration plan phases
- Risk assessment
- Timeline recommendations
- **Recommendation**: Proceed with uv migration

### Tests Added
- SuggestedQuestionsService: 8 unit tests
- Motor/PyMongo import verification

---

## Sprint 3: Production Readiness ✅ COMPLETED

### What was implemented

#### 1. Motor → PyMongo Async Migration (`backend/app/db/client.py`)

**Migrated from deprecated Motor to PyMongo native Async API:**
- Replaced `AsyncIOMotorClient` with `AsyncMongoClient`
- Updated `requirements.txt`: removed `motor`, updated `pymongo>=4.10.0,<4.17`
- No code changes needed in repository layer (API compatible)

**Benefits:**
- Better latency and throughput
- Single dependency instead of two
- Future-proof (Motor EOL May 2026)

#### 2. PDFPageViewer Component (`frontend/src/components/PDFPageViewer.tsx`)

New React component for document visualization:
- PDF page display with zoom controls (0.5x - 3x)
- Bounding box overlays for provenance highlighting
- Fullscreen mode
- Page navigation (prev/next)
- Toggle highlight visibility
- Coordinate conversion (TOPLEFT/BOTTOMLEFT origins)
- Click handlers for highlight interaction
- Helper function `sourceLocationToHighlight`

#### 3. Performance Optimizer (`backend/app/services/performance_optimizer.py`)

New service for handling large documents:

**BatchProcessor:**
- Process items in configurable batch sizes
- Async variant with thread pool
- Progress logging

**ChunkIterator:**
- Lazy iteration over large text/lists
- Configurable chunk size and overlap
- Memory-efficient streaming

**DocumentCache:**
- LRU eviction strategy
- Configurable max size
- Access-order tracking

**EmbeddingCache:**
- Specialized for embedding storage
- Hash-based deduplication
- Auto-eviction at capacity

**estimate_processing_time:**
- Time estimation utility
- Automatic recommendations

### Tests Added
- PyMongo Async import verification
- BatchProcessor batch processing
- ChunkIterator text chunking
- DocumentCache LRU behavior
- EmbeddingCache storage/retrieval
- Time estimation accuracy
- Singleton pattern verification

### Design Decisions

1. **Drop-in replacement**: PyMongo Async API is compatible with Motor's interface
2. **Coordinate system handling**: PDFPageViewer supports both TOPLEFT and BOTTOMLEFT origins
3. **LRU caching**: Efficient memory management for large document workflows
4. **Lazy iteration**: ChunkIterator avoids loading entire documents into memory

---

## Upcoming Tasks

### Sprint 4: uv Migration & Final Polish (P1)
- [ ] Implement uv migration (replace pip)
- [ ] Update CI/CD for uv
- [ ] Add pyproject.toml (optional)
- [ ] Final documentation updates

---

## Backlog (Future)
- Multi-document session support
- Document comparison features
- Export provenance to standard formats
- Real-time collaboration features
- Internationalization (i18n)
- PDF rendering server-side (page image generation)
