"""
DoclingChunkingService: HybridChunker wrapper for Docling-first architecture.

Sprint 1: Uses docling's HybridChunker for structure-aware chunking with
token limits, while preserving full provenance (page, bbox, heading).
"""
from __future__ import annotations

from typing import Any, Optional, List, Dict
import structlog

from app.schemas.finding import SourceLocation, BoundingBox

logger = structlog.get_logger(__name__)

# Try to import Docling chunking components
try:
    from docling.chunking import HybridChunker
    from docling_core.types.doc import DoclingDocument
    HYBRID_CHUNKER_AVAILABLE = True
except ImportError:
    HYBRID_CHUNKER_AVAILABLE = False
    logger.warning("docling_hybrid_chunker_not_available", 
                   message="HybridChunker not available, will use fallback")


class DoclingChunkingService:
    """
    Structure-aware chunking using Docling's HybridChunker.
    
    Features:
    - Token-aware chunk sizing (respects embedding model limits)
    - Preserves document hierarchy (headings, sections)
    - Extracts full provenance (page, bbox, heading path)
    - Falls back to basic chunking if HybridChunker unavailable
    """

    def __init__(
        self,
        max_tokens: int = 512,
        merge_peers: bool = True,
        tokenizer_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize the chunking service.
        
        Args:
            max_tokens: Maximum tokens per chunk (default 512 for most embedding models)
            merge_peers: Whether to merge undersized adjacent chunks with same metadata
            tokenizer_model: HuggingFace model ID for tokenization
        """
        self.max_tokens = max_tokens
        self.merge_peers = merge_peers
        self.tokenizer_model = tokenizer_model
        self._chunker: Optional[HybridChunker] = None
        
        if HYBRID_CHUNKER_AVAILABLE:
            self._init_chunker()

    def _init_chunker(self) -> None:
        """Initialize the HybridChunker with tokenizer."""
        try:
            # Try with HuggingFace tokenizer
            from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
            from transformers import AutoTokenizer
            
            tokenizer = HuggingFaceTokenizer(
                tokenizer=AutoTokenizer.from_pretrained(self.tokenizer_model),
                max_tokens=self.max_tokens,
            )
            self._chunker = HybridChunker(
                tokenizer=tokenizer,
                max_tokens=self.max_tokens,
                merge_peers=self.merge_peers,
            )
            logger.info("hybrid_chunker_initialized", 
                       model=self.tokenizer_model, 
                       max_tokens=self.max_tokens)
        except ImportError:
            # Fallback: try without specific tokenizer
            try:
                self._chunker = HybridChunker(
                    max_tokens=self.max_tokens,
                    merge_peers=self.merge_peers,
                )
                logger.info("hybrid_chunker_initialized_basic", max_tokens=self.max_tokens)
            except Exception as e:
                logger.warning("hybrid_chunker_init_failed", error=str(e))
                self._chunker = None

    def build_chunks(
        self,
        session_id: str,
        document_payload: Dict[str, Any] | None,
        narrative_context: str | None = None,
        tables: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Build chunks from document with full provenance.
        
        If document_payload is available and HybridChunker works, uses structure-aware
        chunking. Otherwise falls back to basic character-based chunking.
        
        Args:
            session_id: Session identifier
            document_payload: Serialized DoclingDocument dict
            narrative_context: Markdown text (fallback)
            tables: Table metadata list (fallback)
            
        Returns:
            List of chunk dicts with provenance
        """
        # Try HybridChunker first
        if self._chunker and document_payload:
            try:
                chunks = self._chunk_with_hybrid(session_id, document_payload)
                if chunks:
                    logger.info("hybrid_chunking_success", 
                               session_id=session_id, 
                               chunk_count=len(chunks))
                    return chunks
            except Exception as e:
                logger.warning("hybrid_chunking_failed", 
                              session_id=session_id, 
                              error=str(e))

        # Fallback to basic chunking
        return self._chunk_fallback(session_id, narrative_context, tables, document_payload)

    def _chunk_with_hybrid(
        self, 
        session_id: str, 
        document_payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Use HybridChunker for structure-aware chunking.
        """
        # Reconstruct DoclingDocument from payload
        try:
            doc = DoclingDocument.model_validate(document_payload)
        except Exception as e:
            logger.warning("docling_document_reconstruction_failed", error=str(e))
            return []

        # Generate chunks using HybridChunker
        chunk_iter = self._chunker.chunk(doc)
        chunks: List[Dict[str, Any]] = []
        
        for idx, chunk in enumerate(chunk_iter):
            chunk_id = f"chunk_hybrid_{idx}"
            
            # Extract text
            text = chunk.text if hasattr(chunk, 'text') else str(chunk)
            
            # Extract provenance from chunk metadata
            location = self._extract_chunk_provenance(chunk)
            
            # Determine source type from chunk
            source_type = self._determine_source_type(chunk)
            
            chunks.append({
                "session_id": session_id,
                "chunk_id": chunk_id,
                "source_type": source_type,
                "source_id": chunk_id,
                "text": text,
                "snippet": text[:240] if text else "",
                "chunk_order": idx,
                "location": location.model_dump() if location else None,
                "token_count": self._estimate_tokens(text),
                "chunker": "hybrid",
            })

        return chunks

    def _extract_chunk_provenance(self, chunk: Any) -> Optional[SourceLocation]:
        """
        Extract SourceLocation from a HybridChunker chunk.
        
        HybridChunker chunks have metadata including:
        - headings: list of heading texts
        - captions: list of caption texts
        - page: page number (if available)
        - bbox: bounding box (if available)
        """
        page = None
        bbox = None
        heading = None
        section_path = None
        
        # Try to get metadata from chunk
        meta = getattr(chunk, 'meta', None) or {}
        if hasattr(chunk, 'metadata'):
            meta = chunk.metadata
        
        # Extract headings as section path
        headings = meta.get('headings', []) or getattr(chunk, 'headings', [])
        if headings:
            section_path = [str(h) for h in headings]
            heading = section_path[-1] if section_path else None
        
        # Extract page info
        page = meta.get('page') or getattr(chunk, 'page', None)
        
        # Extract bbox if available
        bbox_data = meta.get('bbox') or getattr(chunk, 'bbox', None)
        if bbox_data:
            bbox = self._parse_bbox(bbox_data)
        
        # Try provenance array
        prov = meta.get('prov', []) or getattr(chunk, 'prov', [])
        if prov and isinstance(prov, list) and len(prov) > 0:
            first_prov = prov[0]
            if not page:
                page = first_prov.get('page', first_prov.get('page_no'))
            if not bbox and first_prov.get('bbox'):
                bbox = self._parse_bbox(first_prov['bbox'])

        if page is None and bbox is None and not heading:
            return None

        return SourceLocation(
            page=page,
            bbox=bbox,
            heading=heading,
            section_path=section_path,
        )

    def _determine_source_type(self, chunk: Any) -> str:
        """Determine source_type from chunk metadata."""
        meta = getattr(chunk, 'meta', None) or {}
        if hasattr(chunk, 'metadata'):
            meta = chunk.metadata
            
        # Check for table
        if meta.get('table_id') or meta.get('is_table'):
            return "table"
        
        # Check for heading
        label = meta.get('label', '').lower()
        if label in ['heading', 'title', 'section-header']:
            return "heading"
        
        if label in ['list-item', 'list_item']:
            return "list_item"
        
        if label in ['figure', 'caption']:
            return "figure_caption"
        
        return "section"

    def _parse_bbox(self, bbox_data: Any) -> Optional[BoundingBox]:
        """Parse bounding box from various formats."""
        if bbox_data is None:
            return None
        
        if isinstance(bbox_data, dict):
            if "l" in bbox_data:
                return BoundingBox(
                    l=float(bbox_data.get("l", 0)),
                    t=float(bbox_data.get("t", 0)),
                    r=float(bbox_data.get("r", 0)),
                    b=float(bbox_data.get("b", 0)),
                    coord_origin=bbox_data.get("coord_origin", "TOPLEFT"),
                )
            elif "x0" in bbox_data:
                return BoundingBox(
                    l=float(bbox_data.get("x0", 0)),
                    t=float(bbox_data.get("y0", 0)),
                    r=float(bbox_data.get("x1", 0)),
                    b=float(bbox_data.get("y1", 0)),
                )
        
        if isinstance(bbox_data, (list, tuple)) and len(bbox_data) >= 4:
            return BoundingBox(
                l=float(bbox_data[0]),
                t=float(bbox_data[1]),
                r=float(bbox_data[2]),
                b=float(bbox_data[3]),
            )
        
        return None

    def _estimate_tokens(self, text: str) -> int:
        """Rough token count estimation (4 chars per token average)."""
        return len(text) // 4 if text else 0

    def _chunk_fallback(
        self,
        session_id: str,
        narrative_context: str | None,
        tables: List[Dict[str, Any]] | None,
        document_payload: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:
        """
        Fallback chunking when HybridChunker is unavailable.
        Uses the legacy DocumentChunkingService logic.
        """
        from app.services.document_chunking_service import DocumentChunkingService
        
        legacy_service = DocumentChunkingService()
        return legacy_service.build_chunks(
            session_id=session_id,
            narrative_context=narrative_context,
            tables=tables,
            document_payload=document_payload,
        )


# Singleton instance for reuse
_docling_chunking_service: Optional[DoclingChunkingService] = None


def get_docling_chunking_service() -> DoclingChunkingService:
    """Get or create the DoclingChunkingService singleton."""
    global _docling_chunking_service
    if _docling_chunking_service is None:
        _docling_chunking_service = DoclingChunkingService()
    return _docling_chunking_service
