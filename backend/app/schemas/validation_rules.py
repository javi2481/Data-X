from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any, List

class ValidationRule(BaseModel):
    """
    Define una regla de negocio determinística para aplicar sobre una columna de datos.
    """
    column: str = Field(description="Nombre exacto de la columna en el dataset")
    dtype: Optional[str] = Field(None, description="Tipo de dato esperado (ej: int, float, str, datetime, bool)")
    required: bool = Field(False, description="Si es True, la columna no puede tener valores nulos")
    min_val: Optional[float] = Field(None, description="Límite inferior permitido")
    max_val: Optional[float] = Field(None, description="Límite superior permitido")
    regex: Optional[str] = Field(None, description="Expresión regular para validar cadenas de texto")
    allowed_values: Optional[List[Any]] = Field(None, description="Lista estricta de valores permitidos (categorías)")

    @model_validator(mode='after')
    def check_min_max(self) -> 'ValidationRule':
        """Valida internamente que la regla tenga sentido matemático."""
        if self.min_val is not None and self.max_val is not None:
            if self.min_val > self.max_val:
                raise ValueError(f"En la columna '{self.column}', min_val ({self.min_val}) no puede ser mayor que max_val ({self.max_val}).")
        return self
    
    model_config = {"frozen": True}  # Las reglas son inmutables una vez instanciadas


class RuleErrorDetail(BaseModel):
    """Detalle de una validación fallida."""
    column: str
    check: str
    message: str


class ValidationResult(BaseModel):
    """
    Resultado de aplicar todas las reglas contra el DataFrame.
    Se persistirá en MongoDB en el summary de la sesión.
    """
    passed: bool
    failed_columns: List[str] = Field(default_factory=list)
    error_details: List[RuleErrorDetail] = Field(default_factory=list)