from pydantic import BaseModel
from typing import Optional, List, Literal, Tuple
from datetime import datetime


class BoundingBox(BaseModel):
    """Coordenadas de un elemento en el documento (Docling format)"""
    l: float  # left
    t: float  # top
    r: float  # right
    b: float  # bottom
    coord_origin: Literal["TOPLEFT", "BOTTOMLEFT"] = "TOPLEFT"


class SourceLocation(BaseModel):
    """Ubicación precisa de evidencia en el documento fuente (Docling provenance)"""
    page: Optional[int] = None  # Número de página (1-indexed)
    bbox: Optional[BoundingBox] = None  # Bounding box en la página
    heading: Optional[str] = None  # Encabezado de sección
    section_path: Optional[List[str]] = None  # Jerarquía de secciones ["Chapter 1", "Section 1.2"]
    table_id: Optional[str] = None  # ID de tabla si aplica
    row_range: Optional[Tuple[int, int]] = None  # Rango de filas (start, end)
    cell_ref: Optional[str] = None  # Referencia de celda ej: "A1:B5"
    char_offset: Optional[Tuple[int, int]] = None  # Offset de caracteres en el texto


class DocumentChunk(BaseModel):
    """Chunk de documento con provenance completo"""
    chunk_id: str
    session_id: str
    text: str
    snippet: str  # Preview corto del texto
    chunk_order: int
    
    # Tipo de fuente
    source_type: Literal["section", "table", "page_reference", "heading", "list_item", "figure_caption"]
    source_id: str
    
    # Provenance detallado (Docling)
    location: Optional[SourceLocation] = None
    
    # Metadata adicional
    token_count: Optional[int] = None
    embedding_id: Optional[str] = None  # Referencia al vector en FAISS


class Evidence(BaseModel):
    """Evidencia numérica verificable del hallazgo"""
    metric: str
    value: float | int | str
    context: Optional[str] = None  # ej: "de 500 registros totales"
    source_location: Optional[SourceLocation] = None  # Dónde se encontró esta evidencia


class Finding(BaseModel):
    finding_id: str
    
    # Clasificación
    category: str  # "data_gap", "reliability_risk", "pattern", "opportunity", "quality_issue"
    severity: Literal["critical", "important", "suggestion", "insight"]
    
    # What → So What → Now What
    title: str  # Título claro en lenguaje humano
    what: str  # Qué encontramos (hecho)
    so_what: str  # Por qué importa (impacto)
    now_what: str  # Qué hacer (acción recomendada)
    
    # Detalles
    affected_columns: List[str] = []
    evidence: List[Evidence] = []
    confidence: Literal["verified", "high", "moderate"] = "verified"
    
    # Provenance (Sprint 0 - Docling-first)
    source_locations: List[SourceLocation] = []  # Ubicaciones en el documento fuente
    source_chunk_ids: List[str] = []  # IDs de chunks relacionados
    
    # Enriquecimiento LLM (Gold Layer)
    enriched_explanation: Optional[str] = None  # Explicación contextual del LLM
