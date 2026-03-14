import pandas as pd
import numpy as np
from pandas import DataFrame

class ProfilerService:
    def profile(self, df: DataFrame) -> dict:
        """
        Genera un perfil detallado de cada columna en el DataFrame.
        """
        profile_data = {}
        total_rows = len(df)

        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            count = int(series.count())
            null_count = int(series.isna().sum())
            null_percent = float((null_count / total_rows) * 100) if total_rows > 0 else 0.0
            unique_count = int(series.nunique())
            cardinality = float((unique_count / total_rows) * 100) if total_rows > 0 else 0.0

            col_profile = {
                "name": col,
                "dtype": dtype,
                "count": count,
                "null_count": null_count,
                "null_percent": null_percent,
                "unique_count": unique_count,
                "cardinality": cardinality
            }

            # Estadísticas para columnas numéricas
            if pd.api.types.is_numeric_dtype(series):
                try:
                    col_profile.update({
                        "min": float(series.min()) if count > 0 else None,
                        "max": float(series.max()) if count > 0 else None,
                        "mean": float(series.mean()) if count > 0 else None,
                        "median": float(series.median()) if count > 0 else None,
                        "std": float(series.std()) if count > 0 else None
                    })
                except (ValueError, TypeError):
                    # En caso de dtypes mixtos que fallan en min/max/etc.
                    pass
            
            # Estadísticas para columnas de texto (strings)
            elif pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                # Calcular longitudes de strings ignorando nulos
                lengths = series.dropna().astype(str).str.len()
                col_profile.update({
                    "min_length": int(lengths.min()) if not lengths.empty else 0,
                    "max_length": int(lengths.max()) if not lengths.empty else 0,
                    "top_values": [{"value": str(k), "count": int(v)} for k, v in series.value_counts().head(5).items()]
                })

            profile_data[col] = col_profile

        return profile_data
