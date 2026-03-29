import pandas as pd
import pandera as pa
from typing import List
import structlog

from app.schemas.validation_rules import ValidationRule, ValidationResult, RuleErrorDetail

logger = structlog.get_logger(__name__)

class ValidationRulesService:
    """
    Servicio que transforma reglas de negocio declarativas (Pydantic/JSON) 
    en validaciones determinísticas nativas y vectorizadas de Pandera.
    """

    def _map_dtype(self, dtype_str: str) -> pa.DataType | None:
        """Mapea tipos de datos en texto a los tipos nativos de Pandera."""
        if not dtype_str:
            return None
        mapping = {
            "int": pa.Int,
            "float": pa.Float,
            "str": pa.String,
            "datetime": pa.DateTime,
            "bool": pa.Bool
        }
        return mapping.get(dtype_str.lower())

    def apply(self, df: pd.DataFrame, rules: List[ValidationRule]) -> ValidationResult:
        """Aplica una lista de reglas a un DataFrame en modo lazy (recolectando todos los errores)."""
        logger.info("validation_rules_start", rules_count=len(rules))
        
        columns_schema = {}
        
        for rule in rules:
            checks = []
            
            # Traducir los parámetros Pydantic a pa.Check
            if rule.min_val is not None:
                checks.append(pa.Check.greater_than_or_equal_to(rule.min_val))
            if rule.max_val is not None:
                checks.append(pa.Check.less_than_or_equal_to(rule.max_val))
            if rule.regex is not None:
                checks.append(pa.Check.str_matches(rule.regex))
            if rule.allowed_values is not None:
                checks.append(pa.Check.isin(rule.allowed_values))
            
            col_kwargs = {
                "nullable": not rule.required,
                "required": False,  # No forzamos que exista la columna para no romper si el documento es distinto
            }
            
            mapped_dtype = self._map_dtype(rule.dtype)
            if mapped_dtype:
                col_kwargs["dtype"] = mapped_dtype
            if checks:
                col_kwargs["checks"] = checks

            columns_schema[rule.column] = pa.Column(**col_kwargs)
        
        schema = pa.DataFrameSchema(columns=columns_schema)
        
        try:
            # lazy=True obliga a evaluar TODAS las filas y reglas antes de lanzar excepción
            schema.validate(df, lazy=True)
            logger.info("validation_rules_passed")
            return ValidationResult(passed=True, failed_columns=[], error_details=[])
            
        except pa.errors.SchemaErrors as err:
            failed_columns = set()
            error_details = []

            for schema_error in err.schema_errors:
                col = str(getattr(schema_error, "column_name", None) or "dataset")
                check = str(getattr(schema_error, "check", ""))
                message = str(schema_error)
                failed_columns.add(col)
                error_details.append(RuleErrorDetail(column=col, check=check, message=message))
            
            logger.warning("validation_rules_failed", failed_columns=list(failed_columns), error_count=len(error_details))
            return ValidationResult(passed=False, failed_columns=list(failed_columns), error_details=error_details)
        except Exception as e:
            logger.error("validation_rules_error", error=str(e))
            return ValidationResult(passed=False, failed_columns=["dataset"], error_details=[RuleErrorDetail(column="dataset", check="fatal", message=str(e))])