"""
Tests for DocumentChunkingService with Docling provenance extraction.
Sprint 0: Validates that provenance (page, bbox, heading) is correctly extracted.
"""
import pytest
from app.services.document_chunking_service import DocumentChunkingService
from app.schemas.finding import SourceLocation, BoundingBox


class TestDocumentChunkingServiceProvenance:
    """Tests for Docling-first provenance extraction."""

    def test_fallback_chunking_without_document_payload(self):
        """When no document_payload is provided, fallback to character-based chunking."""
        service = DocumentChunkingService(max_chars=100, overlap_chars=20)
        
        chunks = service.build_chunks(
            session_id="sess_test_1",
            narrative_context="This is a test narrative that should be chunked by characters.",
            tables=[{"table_id": "table_0", "row_count": 5, "column_count": 2, "headers": ["A", "B"]}],
            document_payload=None,
        )
        
        assert len(chunks) >= 2
        # Check narrative chunk exists
        narrative_chunks = [c for c in chunks if c["source_type"] == "section"]
        assert len(narrative_chunks) >= 1
        
        # Check table chunk exists
        table_chunks = [c for c in chunks if c["source_type"] == "table"]
        assert len(table_chunks) == 1
        assert table_chunks[0]["source_id"] == "table_0"

    def test_docling_provenance_extraction_with_texts_array(self):
        """Extract provenance from Docling 'texts' array format."""
        service = DocumentChunkingService()
        
        # Simulated Docling document_payload with 'texts' structure
        document_payload = {
            "texts": [
                {
                    "text": "This is the first paragraph of the document with enough text to be valid.",
                    "label": "paragraph",
                    "prov": [{"page": 1, "bbox": {"l": 10, "t": 20, "r": 200, "b": 50}}],
                },
                {
                    "text": "Chapter 1: Introduction to the Analysis",
                    "label": "heading",
                    "prov": [{"page": 1, "bbox": {"l": 10, "t": 60, "r": 300, "b": 80}}],
                },
                {
                    "text": "Second paragraph with detailed analysis results and findings for the report.",
                    "label": "paragraph",
                    "prov": [{"page": 2, "bbox": {"l": 10, "t": 100, "r": 200, "b": 150}}],
                },
            ],
            "tables": [],
        }
        
        chunks = service.build_chunks(
            session_id="sess_docling_1",
            narrative_context=None,
            tables=[],
            document_payload=document_payload,
        )
        
        assert len(chunks) == 3
        
        # Verify first chunk has page 1
        assert chunks[0]["location"] is not None
        assert chunks[0]["location"]["page"] == 1
        assert chunks[0]["location"]["bbox"]["l"] == 10
        
        # Verify heading chunk
        heading_chunks = [c for c in chunks if c["source_type"] == "heading"]
        assert len(heading_chunks) == 1
        
        # Verify second paragraph has page 2
        assert chunks[2]["location"]["page"] == 2

    def test_docling_provenance_extraction_with_body(self):
        """Extract provenance from Docling 'body' format."""
        service = DocumentChunkingService()
        
        # Simulated Docling document_payload with 'body' structure
        document_payload = {
            "body": [
                {
                    "type": "heading",
                    "text": "Executive Summary of Quarterly Report",
                    "level": 1,
                    "prov": [{"page": 1, "bbox": [0, 0, 500, 50]}],
                },
                {
                    "type": "paragraph",
                    "text": "This report analyzes the quarterly performance metrics across all departments.",
                    "prov": [{"page": 1, "bbox": [10, 60, 480, 120]}],
                },
            ],
        }
        
        chunks = service.build_chunks(
            session_id="sess_docling_2",
            narrative_context=None,
            tables=[],
            document_payload=document_payload,
        )
        
        assert len(chunks) == 2
        
        # Heading should have section_path
        heading_chunk = chunks[0]
        assert heading_chunk["source_type"] == "heading"
        assert heading_chunk["location"]["heading"] == "Executive Summary of Quarterly Report"

    def test_table_chunks_with_provenance(self):
        """Tables should have provenance when available in document_payload."""
        service = DocumentChunkingService()
        
        document_payload = {
            "texts": [
                {
                    "text": "Analysis section with detailed explanation for the table below.",
                    "label": "paragraph",
                    "prov": [{"page": 3}],
                }
            ],
            "tables": [
                {
                    "prov": [{"page": 5, "bbox": {"l": 50, "t": 100, "r": 500, "b": 300}}],
                }
            ],
        }
        
        tables = [{"table_id": "table_0", "row_count": 10, "column_count": 3, "headers": ["X", "Y", "Z"]}]
        
        chunks = service.build_chunks(
            session_id="sess_table_prov",
            narrative_context=None,
            tables=tables,
            document_payload=document_payload,
        )
        
        # Find the table chunk
        table_chunks = [c for c in chunks if c["source_type"] == "table"]
        assert len(table_chunks) == 1
        
        table_chunk = table_chunks[0]
        assert table_chunk["location"] is not None
        assert table_chunk["location"]["page"] == 5
        assert table_chunk["location"]["table_id"] == "table_0"

    def test_bbox_parsing_dict_format(self):
        """BoundingBox should be parsed from dict format."""
        service = DocumentChunkingService()
        
        bbox = service._parse_bbox({"l": 10.5, "t": 20.0, "r": 100.0, "b": 50.5})
        
        assert bbox is not None
        assert bbox.l == 10.5
        assert bbox.t == 20.0
        assert bbox.r == 100.0
        assert bbox.b == 50.5

    def test_bbox_parsing_list_format(self):
        """BoundingBox should be parsed from list format."""
        service = DocumentChunkingService()
        
        bbox = service._parse_bbox([15, 25, 150, 75])
        
        assert bbox is not None
        assert bbox.l == 15
        assert bbox.t == 25
        assert bbox.r == 150
        assert bbox.b == 75

    def test_bbox_parsing_x0_y0_format(self):
        """BoundingBox should be parsed from x0/y0/x1/y1 format."""
        service = DocumentChunkingService()
        
        bbox = service._parse_bbox({"x0": 5, "y0": 10, "x1": 200, "y1": 100})
        
        assert bbox is not None
        assert bbox.l == 5
        assert bbox.t == 10
        assert bbox.r == 200
        assert bbox.b == 100

    def test_source_type_mapping(self):
        """Docling types should be correctly mapped to schema source_types."""
        service = DocumentChunkingService()
        
        assert service._map_docling_type_to_source_type("paragraph") == "section"
        assert service._map_docling_type_to_source_type("heading") == "heading"
        assert service._map_docling_type_to_source_type("list-item") == "list_item"
        assert service._map_docling_type_to_source_type("table") == "table"
        assert service._map_docling_type_to_source_type("figure") == "figure_caption"
        assert service._map_docling_type_to_source_type("unknown_type") == "section"

    def test_empty_document_payload_returns_fallback(self):
        """Empty document_payload should trigger fallback chunking."""
        service = DocumentChunkingService()
        
        chunks = service.build_chunks(
            session_id="sess_empty",
            narrative_context="Fallback narrative text that should be used when payload is empty.",
            tables=[],
            document_payload={},  # Empty dict
        )
        
        # Should use fallback
        assert len(chunks) >= 1
        assert chunks[0]["source_type"] == "section"

    def test_chunk_order_is_sequential(self):
        """Chunks should have sequential chunk_order starting from 0."""
        service = DocumentChunkingService()
        
        document_payload = {
            "texts": [
                {"text": "First paragraph with enough content to be included.", "label": "paragraph", "prov": [{"page": 1}]},
                {"text": "Second paragraph following the first one.", "label": "paragraph", "prov": [{"page": 1}]},
                {"text": "Third paragraph to ensure order is correct.", "label": "paragraph", "prov": [{"page": 2}]},
            ]
        }
        
        chunks = service.build_chunks(
            session_id="sess_order",
            narrative_context=None,
            tables=[{"table_id": "t1", "row_count": 1, "column_count": 1, "headers": ["H"]}],
            document_payload=document_payload,
        )
        
        orders = [c["chunk_order"] for c in chunks]
        assert orders == list(range(len(chunks)))


class TestSourceLocationSchema:
    """Tests for SourceLocation Pydantic schema."""

    def test_source_location_minimal(self):
        """SourceLocation should work with minimal fields."""
        loc = SourceLocation(page=1)
        assert loc.page == 1
        assert loc.bbox is None
        assert loc.heading is None

    def test_source_location_full(self):
        """SourceLocation should support all fields."""
        bbox = BoundingBox(l=10, t=20, r=100, b=50)
        loc = SourceLocation(
            page=5,
            bbox=bbox,
            heading="Chapter 1",
            section_path=["Part A", "Chapter 1"],
            table_id="table_0",
            row_range=(0, 10),
            char_offset=(100, 500),
        )
        
        assert loc.page == 5
        assert loc.bbox.l == 10
        assert loc.heading == "Chapter 1"
        assert loc.section_path == ["Part A", "Chapter 1"]
        assert loc.table_id == "table_0"
        assert loc.row_range == (0, 10)

    def test_bounding_box_defaults(self):
        """BoundingBox should have correct defaults."""
        bbox = BoundingBox(l=0, t=0, r=100, b=100)
        assert bbox.coord_origin == "TOPLEFT"
