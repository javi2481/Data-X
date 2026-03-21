import pytest
import pandas as pd
import numpy as np
from app.services.statistical_tests import StatisticalTestsService

def test_normality_numeric_column():
    service = StatisticalTestsService()
    # Crear datos normales
    np.random.seed(42)
    data = np.random.normal(0, 1, 100)
    df = pd.DataFrame({"normal_col": data})
    
    results = service.run_all_tests(df)
    
    # Buscar el resultado de normalidad para normal_col
    normality_res = next((r for r in results if r.get("test") == "shapiro" and r.get("column") == "normal_col"), None)
    
    assert normality_res is not None
    assert "is_normal" in normality_res
    assert "p_value" in normality_res
    assert isinstance(normality_res["is_normal"], bool)

def test_normality_skips_small_sample():
    service = StatisticalTestsService()
    df = pd.DataFrame({"small_col": [1, 2, 3]})
    
    results = service.run_all_tests(df)
    
    # Nuestra implementación actual retorna un dict con la razón del skip
    normality_res = next((r for r in results if r.get("column") == "small_col"), None)
    assert normality_res is not None
    assert "reason" in normality_res
    assert "skip" in normality_res.get("reason").lower() or "requiere" in normality_res.get("reason").lower()

def test_group_differences_two_groups():
    service = StatisticalTestsService()
    # Para T-test necesitamos más datos y variabilidad
    np.random.seed(42)
    df = pd.DataFrame({
        "group": ["A"] * 25 + ["B"] * 25,
        "value": list(np.random.normal(10, 1, 25)) + list(np.random.normal(25, 1, 25))
    })
    
    # IMPORTANTE: Asegurarnos que las columnas tengan los tipos correctos para select_dtypes
    # StatisticalTestsService.test_group_differences puede fallar si no hay variabilidad o tipos raros
    
    # Forzar el test individualmente para verificar lógica
    result = service.test_group_differences(df, "value", "group")
    
    assert result is not None
    assert result["test"] == "t-test"
    assert result["p_value"] < 0.05 # Hay diferencia significativa
    assert "interpretation" in result
