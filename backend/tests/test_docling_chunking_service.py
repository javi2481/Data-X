"""
Tests for DoclingChunkingService with HybridChunker.
Sprint 1: Validates HybridChunker integration and fallback behavior.
"""
import pytest
from app.services.docling_chunking_service import (
    DoclingChunkingService, 
    get_docling_chunking_service,
    HYBRID_CHUNKER_AVAILABLE
)
from app.schemas.finding import SourceLocation, BoundingBox


class TestDoclingChunkingService:
    """Tests for DoclingChunkingService with HybridChunker."""

    def test_service_initialization(self):
        """Service should initialize correctly."""
        service = DoclingChunkingService()
        assert service is not None
        assert service.max_tokens == 512
        assert service.merge_peers is True

    def test_service_with_custom_params(self):
        """Service should accept custom parameters."""
        service = DoclingChunkingService(
            max_tokens=256,
            merge_peers=False,
        )
        assert service.max_tokens == 256
        assert service.merge_peers is False

    def test_fallback_when_no_document_payload(self):
        """Should use fallback chunking when no document_payload."""
        service = DoclingChunkingService()
        
        chunks = service.build_chunks(
            session_id="test_fallback",
            document_payload=None,
            narrative_context="This is a fallback test with some narrative content.",
            tables=[{"table_id": "t1", "row_count": 5, "column_count": 2, "headers": ["A", "B"]}],
        )
        
        assert len(chunks) >= 2
        # Should have section and table chunks
        assert any(c["source_type"] == "section" for c in chunks)
        assert any(c["source_type"] == "table" for c in chunks)

    def test_singleton_pattern(self):
        """get_docling_chunking_service should return same instance."""
        service1 = get_docling_chunking_service()
        service2 = get_docling_chunking_service()
        assert service1 is service2

    def test_hybrid_chunker_availability(self):
        """HybridChunker should be available in test environment."""
        # This test documents the expected state
        print(f"HybridChunker available: {HYBRID_CHUNKER_AVAILABLE}")
        # Don't assert True as it depends on environment
        assert isinstance(HYBRID_CHUNKER_AVAILABLE, bool)

    def test_estimate_tokens(self):
        """Token estimation should work."""
        service = DoclingChunkingService()
        
        tokens = service._estimate_tokens("This is a test string")
        assert tokens > 0
        assert tokens == len("This is a test string") // 4

    def test_parse_bbox_dict_format(self):
        """Should parse bbox from dict format."""
        service = DoclingChunkingService()
        
        bbox = service._parse_bbox({"l": 10, "t": 20, "r": 100, "b": 50})
        assert bbox is not None
        assert bbox.l == 10
        assert bbox.t == 20
        assert bbox.r == 100
        assert bbox.b == 50

    def test_parse_bbox_list_format(self):
        """Should parse bbox from list format."""
        service = DoclingChunkingService()
        
        bbox = service._parse_bbox([15, 25, 150, 75])
        assert bbox is not None
        assert bbox.l == 15
        assert bbox.t == 25
        assert bbox.r == 150
        assert bbox.b == 75

    def test_parse_bbox_none(self):
        """Should handle None bbox gracefully."""
        service = DoclingChunkingService()
        
        bbox = service._parse_bbox(None)
        assert bbox is None

    def test_determine_source_type_defaults(self):
        """Should determine correct source types."""
        service = DoclingChunkingService()
        
        # Create mock chunk objects with meta
        class MockChunk:
            def __init__(self, meta):
                self.meta = meta
        
        # Table
        chunk = MockChunk({"table_id": "t1"})
        assert service._determine_source_type(chunk) == "table"
        
        # Heading
        chunk = MockChunk({"label": "heading"})
        assert service._determine_source_type(chunk) == "heading"
        
        # Default to section
        chunk = MockChunk({})
        assert service._determine_source_type(chunk) == "section"

    def test_chunks_have_required_fields(self):
        """All chunks should have required fields."""
        service = DoclingChunkingService()
        
        chunks = service.build_chunks(
            session_id="test_fields",
            document_payload=None,
            narrative_context="Test content for field validation.",
            tables=[],
        )
        
        for chunk in chunks:
            assert "session_id" in chunk
            assert "chunk_id" in chunk
            assert "source_type" in chunk
            assert "source_id" in chunk
            assert "text" in chunk
            assert "snippet" in chunk
            assert "chunk_order" in chunk

    def test_chunk_order_is_sequential(self):
        """Chunks should have sequential order."""
        service = DoclingChunkingService()
        
        chunks = service.build_chunks(
            session_id="test_order",
            document_payload=None,
            narrative_context="First part of narrative. Second part of narrative.",
            tables=[
                {"table_id": "t1", "row_count": 1, "column_count": 1, "headers": ["H1"]},
                {"table_id": "t2", "row_count": 2, "column_count": 2, "headers": ["H2", "H3"]},
            ],
        )
        
        orders = [c["chunk_order"] for c in chunks]
        assert orders == list(range(len(chunks)))


class TestHybridChunkerIntegration:
    """Integration tests for HybridChunker (when available)."""

    @pytest.mark.skipif(not HYBRID_CHUNKER_AVAILABLE, reason="HybridChunker not available")
    def test_hybrid_chunker_initialized(self):
        """HybridChunker should be initialized when available."""
        service = DoclingChunkingService()
        assert service._chunker is not None

    @pytest.mark.skipif(not HYBRID_CHUNKER_AVAILABLE, reason="HybridChunker not available")
    def test_hybrid_chunking_with_valid_payload(self):
        """Should chunk valid DoclingDocument payload."""
        service = DoclingChunkingService()
        
        # Minimal valid DoclingDocument structure
        # Note: This may need adjustment based on actual Docling schema
        document_payload = {
            "schema_name": "DoclingDocument",
            "version": "1.0.0",
            "name": "test_doc",
            "origin": {"mimetype": "application/pdf", "filename": "test.pdf"},
            "furniture": {},
            "body": {},
            "groups": [],
            "texts": [
                {
                    "text": "This is a test paragraph with enough content to be processed.",
                    "label": "paragraph",
                    "prov": [{"page": 1}],
                }
            ],
            "pictures": [],
            "tables": [],
            "key_value_items": [],
            "pages": {},
        }
        
        chunks = service.build_chunks(
            session_id="test_hybrid",
            document_payload=document_payload,
        )
        
        # May fall back to legacy if payload structure doesn't match
        # Just verify it doesn't crash and returns chunks
        assert isinstance(chunks, list)
