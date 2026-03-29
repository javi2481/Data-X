import pytest
import pandas as pd
from app.schemas.validation_rules import ValidationRule
from app.services.validation_rules_service import ValidationRulesService

def test_validation_rule_min_max_logic():
    """Verifica que Pydantic rechace reglas matemáticamente imposibles."""
    with pytest.raises(ValueError, match="no puede ser mayor que max_val"):
        ValidationRule(column="edad", min_val=50, max_val=18)

    rule = ValidationRule(column="edad", min_val=18, max_val=50)
    assert rule.min_val == 18
    assert rule.max_val == 50

def test_validation_service_passed():
    """Verifica que los datos correctos pasen sin problemas."""
    df = pd.DataFrame({
        "edad": [25, 30, 45],
        "salario": [1000, 2000, 3000],
        "estado": ["activo", "inactivo", "activo"]
    })
    
    rules = [
        ValidationRule(column="edad", min_val=18, max_val=65),
        ValidationRule(column="salario", min_val=0),
        ValidationRule(column="estado", allowed_values=["activo", "inactivo"])
    ]
    
    svc = ValidationRulesService()
    result = svc.apply(df, rules)
    
    assert result.passed is True
    assert len(result.failed_columns) == 0
    assert len(result.error_details) == 0

def test_validation_service_failed():
    """Verifica que atrape y reporte múltiples violaciones en formato lazy."""
    df = pd.DataFrame({
        "edad": [15, 30, 70],  # Falla: 15 < 18, 70 > 65
        "salario": [-500, 2000, 3000], # Falla: -500 < 0
        "estado": ["borrado", "inactivo", "activo"] # Falla: 'borrado' no permitido
    })
    
    rules = [
        ValidationRule(column="edad", min_val=18, max_val=65),
        ValidationRule(column="salario", min_val=0),
        ValidationRule(column="estado", allowed_values=["activo", "inactivo"])
    ]
    
    svc = ValidationRulesService()
    result = svc.apply(df, rules)
    
    assert result.passed is False
    assert "edad" in result.failed_columns
    assert "salario" in result.failed_columns
    assert "estado" in result.failed_columns
    assert len(result.error_details) >= 3