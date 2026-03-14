import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Any

class EDAExtendedService:
    def __init__(self):
        pass

    def compute_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula la matriz de correlación de Pearson para columnas numéricas.
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or numeric_df.shape[1] < 2:
            return {"matrix": {}, "strong_correlations": []}

        # Reemplazar NaN con None para compatibilidad JSON
        corr_matrix = numeric_df.corr().replace({np.nan: None})
        strong_correlations = []
        
        cols = numeric_df.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col1, col2 = cols[i], cols[j]
                
                # Obtener series sin NaNs sincronizadas
                v1 = numeric_df[col1]
                v2 = numeric_df[col2]
                mask = ~v1.isna() & ~v2.isna()
                v1_sync = v1[mask]
                v2_sync = v2[mask]
                
                if len(v1_sync) < 2:
                    continue
                
                # Pearson r y p-value usando scipy
                r, p_value = stats.pearsonr(v1_sync, v2_sync)
                
                if not pd.isna(r) and abs(r) > 0.7:
                    classification = "muy fuerte" if abs(r) > 0.9 else "fuerte"
                    strong_correlations.append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": round(float(r), 3),
                        "p_value": round(float(p_value), 5),
                        "significant": bool(p_value < 0.05),
                        "classification": classification
                    })
        
        return {
            "matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations
        }

    def detect_outliers(self, df: pd.DataFrame, column: str, method: str = "iqr") -> Dict[str, Any]:
        """
        Detecta outliers en una columna usando IQR o Z-score.
        """
        series = df[column].dropna()
        if series.empty or not pd.api.types.is_numeric_dtype(series):
            return {}

        outliers = []
        bounds = {"lower": 0.0, "upper": 0.0}
        
        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = series[(series < lower) | (series > upper)]
            bounds = {"lower": float(lower), "upper": float(upper)}
        else:
            # Z-score fallback si falla stats.zscore
            try:
                z_scores = np.abs(stats.zscore(series))
                outliers = series[z_scores > 3]
            except:
                mean = series.mean()
                std = series.std()
                outliers = series[np.abs(series - mean) > 3 * std]
            
            mean = series.mean()
            std = series.std()
            bounds = {"lower": float(mean - 3 * std), "upper": float(mean + 3 * std)}

        return {
            "method": method,
            "column": column,
            "outlier_count": int(len(outliers)),
            "outlier_percent": round(float(len(outliers) / len(df) * 100), 2) if len(df) > 0 else 0,
            "bounds": bounds,
            "details": [float(x) if isinstance(x, (int, float, np.number)) else str(x) for x in outliers.head(10).tolist()]
        }

    def detect_all_outliers(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detecta outliers en todas las columnas numéricas.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        results = []
        for col in numeric_cols:
            res = self.detect_outliers(df, col)
            if res and res.get("outlier_count", 0) > 0:
                results.append(res)
        return results

    def analyze_distributions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analiza skewness y kurtosis de las columnas numéricas.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        results = []
        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty: continue
            
            skew = float(series.skew())
            kurt = float(series.kurt())
            
            classification = "normal"
            if skew > 1: classification = "right_skewed"
            elif skew < -1: classification = "left_skewed"
            
            if kurt > 3: classification += " (heavy_tailed)"
            
            results.append({
                "column": col,
                "skewness": round(skew, 3),
                "kurtosis": round(kurt, 3),
                "classification": classification
            })
        return results
