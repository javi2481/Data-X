import pytest
import pandas as pd
from app.services.embedding_service import EmbeddingService
from app.services.document_chunking_service import DocumentChunkingService

def test_index_findings():
    service = EmbeddingService()
    findings = [
        {"finding_id": "1", "what": "High salary detected", "category": "pattern"},
        {"finding_id": "2", "what": "Missing emails", "category": "data_gap"},
        {"finding_id": "3", "what": "Duplicates in names", "category": "quality_issue"}
    ]
    service.index_findings(findings)
    assert service.index is not None
    assert service.index.ntotal == 3
    assert len(service.findings_map) == 3

def test_search_returns_relevant():
    service = EmbeddingService()
    findings = [
        {"finding_id": "salary_1", "what": "The salary column has outliers", "category": "pattern"},
        {"finding_id": "email_1", "what": "Many emails are missing", "category": "data_gap"}
    ]
    service.index_findings(findings)
    
    # Buscar algo relacionado con salario
    results = service.search("finding salary issues", top_k=1)
    assert len(results) == 1
    assert results[0]["finding_id"] == "salary_1"

def test_search_empty_index():
    service = EmbeddingService()
    # Buscar sin indexar nada
    results = service.search("any query")
    # Según la implementación actual, si no hay índice devuelve lista vacía
    assert isinstance(results, list)
    assert len(results) == 0

def test_document_chunking_builds_narrative_and_table_chunks():
    chunking = DocumentChunkingService(max_chars=50, overlap_chars=10)
    chunks = chunking.build_chunks(
        session_id="sess_test",
        narrative_context="Este es un contexto narrativo largo para validar chunking semantico de documento.",
        tables=[{"table_id": "table_0", "row_count": 10, "column_count": 3, "headers": ["a", "b", "c"]}],
        document_payload=None,  # Sprint 0: Now requires document_payload parameter
    )
    assert len(chunks) >= 2
    assert any(c["source_type"] == "section" for c in chunks)
    assert any(c["source_type"] == "table" for c in chunks)

@pytest.mark.asyncio
async def test_index_hybrid_sources_and_search():
    service = EmbeddingService()
    findings = [{"finding_id": "f_1", "title": "Ventas altas", "what": "Suba en ventas", "so_what": "Mejor margen"}]
    chunks = [{"chunk_id": "chunk_1", "source_id": "table_0", "text": "Tabla de ventas por mes", "snippet": "ventas por mes", "provenance": {"table_id": "table_0"}}]
    await service.index_hybrid_sources(findings=findings, chunks=chunks)
    assert service.index is not None
    assert len(service.source_map) == 2
    results = await service.search_hybrid_sources("ventas", top_k=2)
    assert len(results) >= 1
    assert results[0]["source_type"] in ["finding", "chunk"]
