import pandas as pd
import re
from pandas import DataFrame

class NormalizationService:
    def normalize(self, df: DataFrame) -> DataFrame:
        """
        Limpia y normaliza un DataFrame de pandas.
        """
        # 1. Limpiar nombres de columnas
        new_columns = {}
        for col in df.columns:
            # Lowercase
            clean_name = str(col).lower()
            # Reemplazar espacios por _
            clean_name = clean_name.replace(" ", "_")
            # Quitar caracteres especiales (solo dejar a-z0-9 y _)
            clean_name = re.sub(r'[^a-z0-9_]', '', clean_name)
            # Asegurar que no sea vacío o duplicado (simplificado)
            if not clean_name:
                clean_name = f"col_{list(df.columns).index(col)}"
            new_columns[col] = clean_name
        
        df = df.rename(columns=new_columns)

        # 2. Intentar convertir columnas a numéricas (coerce errors)
        for col in df.columns:
            # Si se puede convertir a numérico sin perder demasiada información (NaNs nuevos)
            # o si el dtype actual ya sugiere algo numérico pero está como string
            converted = pd.to_numeric(df[col], errors='coerce')
            
            # Decidimos si mantenemos la conversión:
            # Si la columna original tenía valores y la convertida tiene un porcentaje razonable de no-NaNs
            if not converted.isna().all():
                df[col] = converted

        # 3. Eliminar filas completamente vacías
        df = df.dropna(how='all')

        return df
