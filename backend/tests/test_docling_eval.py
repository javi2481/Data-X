import pytest
import json
import os
from pathlib import Path
from app.services.ingest import IngestService

# Directorio de fixtures (donde guardarás tus PDFs de prueba y sus JSONs con resultados esperados)
GOLDENS_DIR = Path(__file__).parent / "fixtures" / "goldens"

@pytest.mark.asyncio
@pytest.mark.skipif(not GOLDENS_DIR.exists(), reason="Directorio de goldens no encontrado")
async def test_docling_table_extraction_accuracy():
    """
    Prueba de regresión ('Golden Test') para asegurar que las actualizaciones
    de Docling no degraden la precisión de extracción de tablas.
    """
    ingest_service = IngestService()
    
    # Cargar pares de (archivo_prueba, resultado_esperado)
    golden_files = list(GOLDENS_DIR.glob("*.json"))
    
    for golden_file in golden_files:
        with open(golden_file, "r", encoding="utf-8") as f:
            expected_data = json.load(f)
            
        pdf_path = GOLDENS_DIR / expected_data["test_filename"]
        if not pdf_path.exists():
            continue
            
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
            
        # Ejecutar Docling sobre el documento de prueba
        result = await ingest_service.ingest_file(
            file_bytes=file_bytes,
            filename=expected_data["test_filename"],
            content_type="application/pdf"
        )
        
        conversion_meta = result.get("conversion_metadata", {})
        
        # Validación 1: Misma cantidad de tablas
        assert conversion_meta.get("tables_found") == expected_data["expected_tables_count"], \
            f"Degradación en conteo de tablas para {pdf_path.name}"
            
        # Validación 2: Threshold de Confianza
        # Nos aseguramos de que la confianza de Docling no baje más de un 5% respecto a su mejor versión
        current_confidence = conversion_meta.get("confidence", 0.0)
        expected_confidence = expected_data.get("expected_confidence", 0.0)
        
        assert current_confidence >= (expected_confidence - 0.05), \
            f"Degradación de confianza en Docling para {pdf_path.name}"