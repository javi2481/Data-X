from pandas import DataFrame
from typing import Any

class ArtifactBuilder:
    def build_table_artifact(self, df: DataFrame, title: str, max_rows: int = 50) -> dict[str, Any]:
        """
        Crea un artifact de tipo tabla para previsualización.
        """
        # Seleccionar solo las primeras max_rows
        df_preview = df.head(max_rows)
        
        # Convertir a formato serializable: lista de diccionarios
        # Reemplazar NaNs por None para JSON
        rows = df_preview.where(df_preview.notnull(), None).to_dict(orient="records")
        
        return {
            "artifact_type": "table",
            "title": title,
            "data": {
                "columns": list(df.columns),
                "rows": rows
            }
        }

    def build_metric_set(self, schema_info: dict[str, Any]) -> dict[str, Any]:
        """
        Crea un conjunto de métricas descriptivas del dataset.
        """
        columns = schema_info.get("columns", [])
        row_count = schema_info.get("row_count", 0)
        null_counts = schema_info.get("null_counts", {})
        total_nulls = sum(null_counts.values())
        
        # Estimar cantidad de columnas numéricas basándonos en dtypes (simplificado)
        # En este punto el DataFrame ya pasó por NormalizationService
        # Los dtypes en schema_info podrían no estar actualizados si se llama
        # antes de la normalización, pero el prompt sugiere que el builder se usa
        # después. Aquí usaremos la información básica que tengamos.
        # Nota: La cuenta real la hará Emergent después con el ProfilerService.
        
        return {
            "artifact_type": "metric_set",
            "title": "Resumen del dataset",
            "data": {
                "metrics": [
                    {"label": "Filas", "value": row_count},
                    {"label": "Columnas", "value": len(columns)},
                    {"label": "Valores nulos totales", "value": total_nulls}
                ]
            }
        }

    def build_alerts(self, alerts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Crea un artifact para mostrar alertas de validación.
        """
        return {
            "artifact_type": "alerts",
            "title": "Alertas de Calidad",
            "data": {
                "items": alerts
            }
        }

    def build_summary(self, text: str) -> dict[str, Any]:
        """
        Crea un artifact de tipo resumen textual.
        """
        return {
            "artifact_type": "summary",
            "title": "Análisis inteligente",
            "data": {
                "text": text
            }
        }

    def build_chart_config(self, title: str, chart_type: str, x_data: list, y_data: list, x_label: str = "", y_label: str = "") -> dict[str, Any]:
        """
        Crea un artifact de tipo gráfico para que el frontend lo renderice con Recharts.
        """
        # Asegurar que no haya NaNs en los datos de entrada para JSON
        import math
        def clean_val(v):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return None
            return v

        clean_x = [clean_val(v) for v in x_data]
        clean_y = [clean_val(v) for v in y_data]

        return {
            "artifact_type": "chart_config",
            "title": title,
            "data": {
                "type": chart_type, # bar, line, pie, scatter
                "x_label": x_label,
                "y_label": y_label,
                "series": [
                    {
                        "name": y_label or "valor",
                        "data": [{"x": x, "y": y} for x, y in zip(clean_x, clean_y)]
                    }
                ]
            }
        }
