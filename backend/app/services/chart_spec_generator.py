import pandas as pd
from uuid import uuid4
from typing import List, Dict, Any
from app.schemas.chart_spec import ChartSpec, AxisSpec, SeriesSpec

class ChartSpecGenerator:
    def __init__(self):
        pass

    def generate_null_distribution_chart(self, df: pd.DataFrame) -> ChartSpec:
        null_counts = df.isnull().sum()
        data = []
        for col, count in null_counts.items():
            data.append({"column": col, "null_count": int(count)})
        
        return ChartSpec(
            chart_id=f"chart_{uuid4().hex[:8]}",
            chart_type="bar",
            title="Distribución de valores nulos por columna",
            data=data,
            x_axis=AxisSpec(key="column", label="Columna", type="categorical"),
            y_axis=AxisSpec(key="null_count", label="Cantidad de Nulos", type="numeric"),
            series=[SeriesSpec(key="null_count", label="Nulos", color_hint="#ef4444")]
        )

    def generate_dtype_distribution_chart(self, df: pd.DataFrame) -> ChartSpec:
        dtypes = df.dtypes.value_counts()
        data = []
        for dtype, count in dtypes.items():
            data.append({"dtype": str(dtype), "count": int(count)})
        
        return ChartSpec(
            chart_id=f"chart_{uuid4().hex[:8]}",
            chart_type="pie",
            title="Distribución de tipos de datos",
            data=data,
            x_axis=AxisSpec(key="dtype", label="Tipo de Dato", type="categorical"),
            series=[SeriesSpec(key="count", label="Cantidad", color_hint="#3b82f6")]
        )

    def generate_numeric_summary_chart(self, df: pd.DataFrame) -> ChartSpec:
        numeric_df = df.select_dtypes(include=['number'])
        data = []
        if not numeric_df.empty:
            means = numeric_df.mean()
            for col, val in means.items():
                if not pd.isna(val):
                    data.append({"column": col, "mean": round(float(val), 2)})
        
        return ChartSpec(
            chart_id=f"chart_{uuid4().hex[:8]}",
            chart_type="bar",
            title="Promedio por columna numérica",
            data=data,
            x_axis=AxisSpec(key="column", label="Columna", type="categorical"),
            y_axis=AxisSpec(key="mean", label="Promedio", type="numeric"),
            series=[SeriesSpec(key="mean", label="Media", color_hint="#10b981")]
        )

    def generate_top_values_chart(self, df: pd.DataFrame, column: str) -> ChartSpec:
        top_10 = df[column].value_counts().head(10)
        data = []
        for val, count in top_10.items():
            data.append({"value": str(val), "count": int(count)})
        
        return ChartSpec(
            chart_id=f"chart_{uuid4().hex[:8]}",
            chart_type="bar",
            title=f"Top 10 valores en '{column}'",
            data=data,
            x_axis=AxisSpec(key="value", label="Valor", type="categorical"),
            y_axis=AxisSpec(key="count", label="Frecuencia", type="numeric"),
            series=[SeriesSpec(key="count", label="Frecuencia", color_hint="#8b5cf6")]
        )

    def generate_all_charts(self, df: pd.DataFrame, findings: List[Any] = None) -> List[ChartSpec]:
        charts = []
        if df.empty:
            return charts
            
        charts.append(self.generate_null_distribution_chart(df))
        charts.append(self.generate_dtype_distribution_chart(df))
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            charts.append(self.generate_numeric_summary_chart(df))
            
        # Generar top values para la primera columna categórica encontrada
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if not cat_cols.empty:
            charts.append(self.generate_top_values_chart(df, cat_cols[0]))
            
        return charts
