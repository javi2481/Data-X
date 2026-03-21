from __future__ import annotations

from typing import Any, Optional, List, Dict, Tuple
from app.schemas.finding import SourceLocation, BoundingBox, DocumentChunk


class DocumentChunkingService:
    """
    Chunking semántico con provenance completo para Docling-first architecture.
    
    Sprint 0: Extrae ubicaciones precisas (página, bbox, sección) del document_payload
    cuando está disponible, con fallback a chunking básico por caracteres.
    """

    def __init__(self, max_chars: int = 1200, overlap_chars: int = 120):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def build_chunks(
        self,
        session_id: str,
        narrative_context: str | None,
        tables: list[dict[str, Any]] | None,
        document_payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Construye chunks con provenance.
        
        Si document_payload está disponible (Docling), extrae provenance estructurado.
        Si no, usa fallback por caracteres.
        """
        chunks: list[dict[str, Any]] = []
        order = 0

        # Intentar extraer chunks estructurados de Docling
        if document_payload:
            docling_chunks = self._extract_docling_chunks(session_id, document_payload)
            if docling_chunks:
                for chunk in docling_chunks:
                    chunk["chunk_order"] = order
                    chunks.append(chunk)
                    order += 1
                
                # Agregar chunks de tablas con provenance
                table_chunks = self._extract_table_chunks_with_provenance(
                    session_id, tables, document_payload
                )
                for chunk in table_chunks:
                    chunk["chunk_order"] = order
                    chunks.append(chunk)
                    order += 1
                
                return chunks

        # Fallback: chunking por caracteres (legacy)
        if narrative_context:
            text_chunks = self._split_text(narrative_context)
            for idx, text in enumerate(text_chunks):
                chunk_id = f"chunk_narrative_{idx}"
                chunks.append(
                    {
                        "session_id": session_id,
                        "chunk_id": chunk_id,
                        "source_type": "section",
                        "source_id": chunk_id,
                        "text": text,
                        "snippet": text[:240],
                        "chunk_order": order,
                        "location": None,  # Sin provenance en fallback
                    }
                )
                order += 1

        for table in tables or []:
            table_id = str(table.get("table_id", f"table_{order}"))
            headers = table.get("headers", []) or []
            table_text = (
                f"Table {table_id}. Rows: {table.get('row_count', 0)}. "
                f"Columns: {table.get('column_count', 0)}. "
                f"Headers: {', '.join([str(h) for h in headers])}"
            )
            chunk_id = f"chunk_{table_id}"
            chunks.append(
                {
                    "session_id": session_id,
                    "chunk_id": chunk_id,
                    "source_type": "table",
                    "source_id": table_id,
                    "text": table_text,
                    "snippet": table_text[:240],
                    "chunk_order": order,
                    "location": SourceLocation(table_id=table_id).model_dump(),
                }
            )
            order += 1

        return chunks

    def _extract_docling_chunks(
        self, session_id: str, document_payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extrae chunks estructurados del document_payload de Docling.
        
        Navega por 'body' o 'main-text' para extraer elementos con su provenance.
        """
        chunks: list[dict[str, Any]] = []
        
        # Docling puede usar diferentes keys para el contenido principal
        body = document_payload.get("body") or document_payload.get("main-text") or []
        
        if not body:
            # Intentar con la estructura texts/groups
            texts = document_payload.get("texts", [])
            if texts:
                return self._extract_from_texts_array(session_id, texts, document_payload)
            return []

        current_heading: Optional[str] = None
        section_path: List[str] = []
        chunk_idx = 0

        for item in body:
            item_type = item.get("type", "").lower()
            text_content = self._get_text_content(item)
            
            if not text_content or len(text_content.strip()) < 10:
                continue

            # Actualizar contexto de sección
            if item_type in ["heading", "title", "section-header"]:
                current_heading = text_content.strip()
                level = item.get("level", 1)
                # Mantener jerarquía de secciones
                section_path = section_path[:level-1] + [current_heading]

            # Extraer provenance
            location = self._extract_location_from_item(item, current_heading, section_path)
            
            # Determinar source_type
            source_type = self._map_docling_type_to_source_type(item_type)
            
            chunk_id = f"chunk_docling_{chunk_idx}"
            chunks.append({
                "session_id": session_id,
                "chunk_id": chunk_id,
                "source_type": source_type,
                "source_id": chunk_id,
                "text": text_content,
                "snippet": text_content[:240],
                "chunk_order": 0,  # Se asigna después
                "location": location.model_dump() if location else None,
            })
            chunk_idx += 1

        return chunks

    def _extract_from_texts_array(
        self, session_id: str, texts: list[dict], document_payload: dict
    ) -> list[dict[str, Any]]:
        """
        Extrae chunks de la estructura 'texts' de Docling (formato alternativo).
        """
        chunks: list[dict[str, Any]] = []
        chunk_idx = 0
        
        for text_item in texts:
            text_content = text_item.get("text", "")
            if not text_content or len(text_content.strip()) < 10:
                continue
            
            # Extraer provenance del item
            prov = text_item.get("prov", [])
            location = self._extract_location_from_prov(prov)
            
            label = text_item.get("label", "paragraph").lower()
            source_type = self._map_docling_type_to_source_type(label)
            
            chunk_id = f"chunk_texts_{chunk_idx}"
            chunks.append({
                "session_id": session_id,
                "chunk_id": chunk_id,
                "source_type": source_type,
                "source_id": chunk_id,
                "text": text_content,
                "snippet": text_content[:240],
                "chunk_order": 0,
                "location": location.model_dump() if location else None,
            })
            chunk_idx += 1
        
        return chunks

    def _extract_location_from_item(
        self, item: dict, heading: Optional[str], section_path: List[str]
    ) -> Optional[SourceLocation]:
        """
        Extrae SourceLocation de un item de Docling.
        """
        page = None
        bbox = None
        
        # Buscar provenance en el item
        prov = item.get("prov", [])
        if prov and isinstance(prov, list) and len(prov) > 0:
            first_prov = prov[0]
            page = first_prov.get("page", first_prov.get("page_no"))
            
            bbox_data = first_prov.get("bbox")
            if bbox_data:
                bbox = self._parse_bbox(bbox_data)
        
        # También puede venir en location directamente
        loc = item.get("location", {})
        if loc:
            page = page or loc.get("page")
            if not bbox and loc.get("bbox"):
                bbox = self._parse_bbox(loc.get("bbox"))
        
        if page is None and bbox is None and not heading and not section_path:
            return None
        
        return SourceLocation(
            page=page,
            bbox=bbox,
            heading=heading,
            section_path=section_path if section_path else None,
        )

    def _extract_location_from_prov(self, prov: list) -> Optional[SourceLocation]:
        """
        Extrae SourceLocation de un array de provenance.
        """
        if not prov or not isinstance(prov, list) or len(prov) == 0:
            return None
        
        first_prov = prov[0]
        page = first_prov.get("page", first_prov.get("page_no"))
        bbox = None
        
        bbox_data = first_prov.get("bbox")
        if bbox_data:
            bbox = self._parse_bbox(bbox_data)
        
        if page is None and bbox is None:
            return None
        
        return SourceLocation(page=page, bbox=bbox)

    def _parse_bbox(self, bbox_data: Any) -> Optional[BoundingBox]:
        """
        Parsea bounding box de diferentes formatos de Docling.
        """
        if bbox_data is None:
            return None
        
        # Formato dict: {l, t, r, b} o {x0, y0, x1, y1}
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
        
        # Formato lista: [l, t, r, b]
        if isinstance(bbox_data, (list, tuple)) and len(bbox_data) >= 4:
            return BoundingBox(
                l=float(bbox_data[0]),
                t=float(bbox_data[1]),
                r=float(bbox_data[2]),
                b=float(bbox_data[3]),
            )
        
        return None

    def _extract_table_chunks_with_provenance(
        self,
        session_id: str,
        tables: list[dict[str, Any]] | None,
        document_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extrae chunks de tablas con su provenance del document_payload.
        """
        chunks: list[dict[str, Any]] = []
        
        # Obtener tablas del payload de Docling
        docling_tables = document_payload.get("tables", [])
        
        for idx, table in enumerate(tables or []):
            table_id = str(table.get("table_id", f"table_{idx}"))
            headers = table.get("headers", []) or []
            
            table_text = (
                f"Table {table_id}. Rows: {table.get('row_count', 0)}. "
                f"Columns: {table.get('column_count', 0)}. "
                f"Headers: {', '.join([str(h) for h in headers])}"
            )
            
            # Buscar provenance en docling_tables
            location = None
            if idx < len(docling_tables):
                docling_table = docling_tables[idx]
                prov = docling_table.get("prov", [])
                if prov:
                    loc = self._extract_location_from_prov(prov)
                    if loc:
                        loc.table_id = table_id
                        location = loc
                    else:
                        location = SourceLocation(table_id=table_id)
                else:
                    location = SourceLocation(table_id=table_id)
            else:
                location = SourceLocation(table_id=table_id)
            
            chunk_id = f"chunk_{table_id}"
            chunks.append({
                "session_id": session_id,
                "chunk_id": chunk_id,
                "source_type": "table",
                "source_id": table_id,
                "text": table_text,
                "snippet": table_text[:240],
                "chunk_order": 0,
                "location": location.model_dump() if location else None,
            })
        
        return chunks

    def _get_text_content(self, item: dict) -> str:
        """
        Extrae el contenido de texto de un item de Docling.
        """
        # Intentar diferentes keys comunes
        for key in ["text", "content", "value", "raw"]:
            if key in item and item[key]:
                return str(item[key])
        
        # Si hay children, concatenar
        children = item.get("children", [])
        if children:
            texts = [self._get_text_content(c) for c in children if isinstance(c, dict)]
            return " ".join(filter(None, texts))
        
        return ""

    def _map_docling_type_to_source_type(self, docling_type: str) -> str:
        """
        Mapea tipos de Docling a source_type del schema.
        """
        mapping = {
            "paragraph": "section",
            "text": "section",
            "heading": "heading",
            "title": "heading",
            "section-header": "heading",
            "list-item": "list_item",
            "list_item": "list_item",
            "table": "table",
            "figure": "figure_caption",
            "caption": "figure_caption",
            "page-header": "page_reference",
            "page-footer": "page_reference",
        }
        return mapping.get(docling_type.lower(), "section")

    def _split_text(self, text: str) -> list[str]:
        """Fallback: split por caracteres con overlap."""
        normalized = text.strip()
        if not normalized:
            return []
        if len(normalized) <= self.max_chars:
            return [normalized]

        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(start + self.max_chars, len(normalized))
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start = max(0, end - self.overlap_chars)
        return chunks
