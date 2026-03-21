import pingouin as pg
import pandas as pd
import warnings

# Ignorar FutureWarnings de pingouin por compatibilidad con pandas 3.x
warnings.filterwarnings("ignore", category=FutureWarning, module="pingouin")

class StatisticalTestsService:
    
    def test_normality(self, df: pd.DataFrame, column: str) -> dict:
        """Test Shapiro-Wilk para normalidad"""
        try:
            data = df[column].dropna()
            if len(data) < 8 or len(data) > 5000:
                return {"column": column, "test": "shapiro", "skipped": True,
                        "reason": "Requiere entre 8 y 5000 datos"}
            result = pg.normality(data)
            is_normal = bool(result['normal'].values[0])
            p_value = float(result['pval'].values[0])
            return {
                "column": column,
                "test": "shapiro",
                "is_normal": is_normal,
                "p_value": round(p_value, 4),
                "interpretation": "Los datos siguen un patrón regular (distribución normal)"
                    if is_normal else
                    "Los datos NO siguen un patrón regular — el promedio puede ser engañoso"
            }
        except Exception:
            return {"column": column, "test": "shapiro", "skipped": True, "reason": "Error en el cálculo"}
    
    def test_group_differences(self, df, numeric_col, group_col) -> dict:
        """Compara grupos si hay una columna categórica y una numérica"""
        try:
            groups = df[group_col].nunique()
            if groups < 2 or groups > 20:
                return None
            
            if groups == 2:
                # Filtrar nulos antes de comparar
                g1 = df[df[group_col] == df[group_col].unique()[0]][numeric_col].dropna()
                g2 = df[df[group_col] == df[group_col].unique()[1]][numeric_col].dropna()
                
                if len(g1) < 2 or len(g2) < 2:
                    return None
                    
                result = pg.ttest(g1, g2)
                # En algunas versiones de pingouin el p-valor es 'p-val', en otras 'p_val', 'p-unc', etc.
                p_val = None
                for col in ['p-val', 'p_val', 'p-unc', 'p_unc', 'pval', 'p']:
                    if col in result.columns:
                        p_val = float(result[col].values[0])
                        break
                
                if p_val is None:
                    return None
                    
                significant = p_val < 0.05
                return {
                    "test": "t-test",
                    "numeric_column": numeric_col,
                    "group_column": group_col,
                    "p_value": round(p_val, 4),
                    "significant": significant,
                    "interpretation": f"Hay diferencias significativas en '{numeric_col}' entre los grupos de '{group_col}'"
                        if significant else
                        f"No hay diferencias significativas en '{numeric_col}' entre los grupos de '{group_col}'"
                }
            else:
                result = pg.anova(data=df, dv=numeric_col, between=group_col)
                p_val = float(result['p-unc'].values[0])
                significant = p_val < 0.05
                return {
                    "test": "anova",
                    "numeric_column": numeric_col,
                    "group_column": group_col,
                    "groups": groups,
                    "p_value": round(p_val, 4),
                    "significant": significant,
                    "interpretation": f"Los {groups} grupos de '{group_col}' muestran diferencias significativas en '{numeric_col}'"
                        if significant else
                        f"No hay diferencias claras en '{numeric_col}' entre los {groups} grupos de '{group_col}'"
                }
        except Exception:
            return None
    
    def run_all_tests(self, df: pd.DataFrame) -> list[dict]:
        """Corre tests relevantes automáticamente"""
        results = []
        
        # Inferencia manual de tipos
        numeric_cols = []
        categorical_cols = []
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
            elif pd.api.types.is_object_dtype(df[col]) or isinstance(df[col].dtype, pd.CategoricalDtype):
                categorical_cols.append(col)

        # Normalidad para cada columna numérica
        for col in numeric_cols:
            results.append(self.test_normality(df, col))
        
        # Comparación entre grupos (categórica x numérica)
        for cat_col in categorical_cols:
            try:
                nunique = df[cat_col].nunique()
                if 2 <= nunique <= 20:
                    for num_col in numeric_cols:
                        result = self.test_group_differences(df, num_col, cat_col)
                        if result:
                            results.append(result)
            except Exception:
                continue
        
        return [r for r in results if r is not None]
