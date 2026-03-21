import pandas as pd
import numpy as np
from pandas import DataFrame

class StatsEngine:
    def descriptive_stats(self, df: DataFrame) -> dict:
        """
        Devuelve estadísticas descriptivas completas del DataFrame.
        """
        # describe() incluye count, mean, std, min, 25%, 50%, 75%, max para numéricas
        stats = df.describe(include='all').replace({np.nan: None})
        return stats.to_dict()

    def correlation_matrix(self, df: DataFrame) -> dict:
        """
        Calcula la matriz de correlación para columnas numéricas.
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {}
        
        corr = numeric_df.corr().replace({np.nan: None})
        return corr.to_dict()

    def detect_outliers(self, df: DataFrame, column: str) -> dict:
        """
        Detecta outliers en una columna específica usando el método IQR.
        """
        if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
            return {"count": 0, "bounds": None, "outliers": []}

        series = df[column].dropna()
        if series.empty:
            return {"count": 0, "bounds": None, "outliers": []}

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        
        return {
            "count": int(len(outliers)),
            "bounds": {
                "lower": float(lower_bound),
                "upper": float(upper_bound),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr)
            }
        }
