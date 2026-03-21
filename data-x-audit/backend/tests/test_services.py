import pytest
import pandas as pd
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.profiler import ProfilerService
from app.services.finding_builder import FindingBuilder
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.eda_extended import EDAExtendedService
from app.services.docling_quality_gate import DoclingQualityGate
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

async def test_ingest_csv():
    ingest_service = IngestService()
    file_path = FIXTURES_DIR / "ventas.csv"
    with open(file_path, "rb") as f:
        content = f.read()
        res = await ingest_service.ingest_file(content, "ventas.csv", "text/csv")
    
    assert "dataframe" in res
    assert not res["dataframe"].empty
    assert "salary" in res["dataframe"].columns

def test_normalization(ventas_df):
    norm_service = NormalizationService()
    df_norm = norm_service.normalize(ventas_df)
    
    assert isinstance(df_norm, pd.DataFrame)
    # Verificar que los headers estén limpios
    assert all(c == str(c).strip() for c in df_norm.columns)

def test_profiler(ventas_df):
    profiler = ProfilerService()
    profiles_dict = profiler.profile(ventas_df)
    
    assert isinstance(profiles_dict, dict)
    assert len(profiles_dict) > 0
    first_col = list(profiles_dict.keys())[0]
    assert "name" in profiles_dict[first_col]
    assert "dtype" in profiles_dict[first_col]

def test_finding_builder(ventas_df):
    builder = FindingBuilder()
    findings = builder.build_all_findings(ventas_df, eda_results={}, schema_results=[])
    
    assert isinstance(findings, list)
    if len(findings) > 0:
        first = findings[0]
        # Validar nuevo esquema Corte 4 (ahora pueden ser objetos Pydantic o dicts)
        # Si es objeto Pydantic, usamos .model_dump()
        if hasattr(first, "model_dump"):
            first_dict = first.model_dump()
        else:
            first_dict = first
            
        assert "what" in first_dict
        assert "so_what" in first_dict
        assert "now_what" in first_dict
        assert "severity" in first_dict
        assert first_dict["severity"] in ["critical", "important", "suggestion", "insight"]
        assert "category" in first_dict
        assert first_dict["category"] in ["data_gap", "reliability_risk", "pattern", "opportunity", "quality_issue"]

def test_chart_spec_generator(ventas_df):
    generator = ChartSpecGenerator()
    charts = generator.generate_all_charts(ventas_df, findings=[], eda_results={})
    
    assert isinstance(charts, list)
    assert len(charts) > 0
    assert hasattr(charts[0], "chart_type")

def test_eda_extended_correlations(ventas_df):
    eda = EDAExtendedService()
    res = eda.compute_correlations(ventas_df)
    
    assert isinstance(res, dict)
    assert "matrix" in res
    assert "strong_correlations" in res

def test_eda_extended_outliers(ventas_df):
    eda = EDAExtendedService()
    # En ventas.csv, 'salary' es numérico
    if "salary" in ventas_df.columns:
        outliers = eda.detect_outliers(ventas_df, "salary")
        assert isinstance(outliers, dict)
        if outliers:
            assert "method" in outliers
            assert "outlier_count" in outliers

def test_docling_quality_gate_marks_pandas_fallback_as_warning():
    gate = DoclingQualityGate()
    result = gate.evaluate({
        "method": "pandas_fallback",
        "confidence": None,
        "tables_found": 1,
    })
    assert result["status"] == "warning"
    assert result["method"] == "pandas_fallback"
    assert "baseline" in result
