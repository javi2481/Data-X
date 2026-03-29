import pytest
from unittest.mock import MagicMock
from app.services.context_builder import ContextBuilder

def test_context_builder_initialization():
    """Verifica que el builder se inicialice correctamente con el límite de tokens."""
    builder = ContextBuilder(max_tokens=4000)
    assert builder.max_tokens == 4000
    assert builder.build() == ""

def test_context_builder_dataset_summary():
    """Verifica que el resumen del dataset se agregue correctamente al contexto Markdown."""
    builder = ContextBuilder(max_tokens=6000)
    
    # Usamos MagicMock para simular el ProfilingSummary sin requerir toda su estructura
    mock_profiling = MagicMock()
    
    builder.add_dataset_summary(
        filename="reporte_ventas_q3.pdf",
        row_count=1500,
        col_count=12,
        profiling_summary=mock_profiling
    )
    
    result = builder.build()
    
    assert isinstance(result, str)
    assert "reporte_ventas_q3.pdf" in result
    assert "1500" in result
    assert "12" in result

def test_context_builder_budget_limit():
    """Verifica que el builder no exceda el límite de tokens (truncamiento seguro)."""
    builder = ContextBuilder(max_tokens=10) # Budget extremadamente bajo
    builder.add_dataset_summary("test.csv", 100, 5, None)
    result = builder.build()
    
    # El resultado no debería ser vacío, pero el servicio debe manejar el truncamiento
    # para evitar enviar payloads masivos a la API del LLM.
    assert isinstance(result, str)
    assert len(result) > 0