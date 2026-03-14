import pandas as pd
import pandera as pa
from typing import List, Dict, Any

class SchemaValidator:
    """
    Servicio para validación de esquemas de datos usando Pandera.
    Proporciona inferencia automática de esquemas y reporte de inconsistencias.
    """

    def infer_schema(self, df: pd.DataFrame) -> pa.DataFrameSchema:
        """
        Infiere automáticamente un esquema de Pandera basado en el DataFrame actual.
        """
        return pa.infer_schema(df)

    def validate(self, df: pd.DataFrame, schema: pa.DataFrameSchema) -> List[Dict[str, Any]]:
        """
        Valida el DataFrame contra el esquema proporcionado.
        Captura errores de validación y los convierte a un formato compatible con Finding.
        """
        results = []
        try:
            schema.validate(df, lazy=True)
        except pa.errors.SchemaErrors as err:
            # Los errores se encuentran en err.schema_errors
            for _, row in err.schema_errors.iterrows():
                # Pandera reporta errores de columna, tipo, nulos, etc.
                column = row.get("column")
                check = row.get("check")
                # El mensaje de error crudo puede ser muy técnico, intentamos simplificar
                message = row.get("reason", str(err))
                
                # Manejar casos donde column es None (ej. validaciones a nivel de DF)
                column_name = str(column) if column is not None else "dataset"
                
                results.append({
                    "category": "schema_warning",
                    "severity": "warning",
                    "column": column_name,
                    "message": message,
                    "check": str(check)
                })
        except Exception as e:
            # Error genérico de validación
            results.append({
                "category": "schema_warning",
                "severity": "warning",
                "column": "dataset",
                "message": f"Error inesperado en validación: {str(e)}",
                "check": "unexpected_error"
            })
            
        return results

    def validate_and_report(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Infiere el esquema y valida el DataFrame en un solo paso.
        Ideal para el pipeline Silver cuando no hay un esquema predefinido.
        """
        if df is None or df.empty:
            return []
            
        try:
            schema = self.infer_schema(df)
            return self.validate(df, schema)
        except Exception as e:
            return [{
                "category": "schema_warning",
                "severity": "warning",
                "column": "dataset",
                "message": f"Error al inferir esquema: {str(e)}",
                "check": "infer_schema_error"
            }]
