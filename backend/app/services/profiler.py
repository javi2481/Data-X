import pandas as pd
import numpy as np
from pandas import DataFrame
import structlog
import time

logger = structlog.get_logger(__name__)

class ProfilerService:
    def _clean_value(self, val):
        if pd.isna(val) or (isinstance(val, (float, int)) and np.isinf(val)):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def profile(self, df: DataFrame) -> dict:
        """
        Genera un perfil detallado de cada columna en el DataFrame.
        """
        start_time = time.time()
        logger.info("profiling_start", columns=len(df.columns), rows=len(df))
        
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
                        "min": self._clean_value(series.min()) if count > 0 else None,
                        "max": self._clean_value(series.max()) if count > 0 else None,
                        "mean": self._clean_value(series.mean()) if count > 0 else None,
                        "median": self._clean_value(series.median()) if count > 0 else None,
                        "std": self._clean_value(series.std()) if count > 0 else None
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

        duration = time.time() - start_time
        logger.info("profiling_complete", duration_sec=round(duration, 3))
        return profile_data
