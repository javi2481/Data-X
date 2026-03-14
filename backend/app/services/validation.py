from pandas import DataFrame
from typing import Any

# DEPRECATED: La lógica de validación ahora se integra en FindingBuilder en v3.0.
class ValidationService:
    def validate(self, df: DataFrame, schema_info: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Detecta problemas de calidad y alertas básicas del dataset.
        """
        alerts = []
        
        # 1. Verificar si el dataset está vacío
        if df.empty or len(df.columns) == 0:
            return [{"level": "error", "message": "El dataset está vacío", "field": None}]

        # 2. Detectar columnas con más del 50% de nulls
        row_count = len(df)
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > (row_count / 2):
                alerts.append({
                    "level": "warning",
                    "message": f"La columna '{col}' tiene más del 50% de valores nulos ({null_count}/{row_count})",
                    "field": col
                })

        # 3. Detectar si hay 0 columnas numéricas
        # Usamos select_dtypes para identificar columnas numéricas
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            alerts.append({
                "level": "info",
                "message": "No se detectaron columnas numéricas. Algunos análisis podrían no estar disponibles.",
                "field": None
            })

        return alerts
