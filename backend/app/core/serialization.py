import numpy as np
import pandas as pd
from typing import Any

def clean_data_for_json(obj: Any) -> Any:
    """
    Limpia un objeto (dict, list, DataFrame, Serie) para que sea serializable a JSON.
    - Reemplaza NaN, Infinity, -Infinity por None.
    - Convierte tipos numpy a tipos nativos de Python.
    """
    if isinstance(obj, pd.DataFrame):
        # Convertir NaN e Infinitos a None
        return obj.replace([np.inf, -np.inf], np.nan).where(obj.notna(), None).to_dict(orient="records")
    
    if isinstance(obj, pd.Series):
        return obj.replace([np.inf, -np.inf], np.nan).where(obj.notna(), None).to_list()

    if isinstance(obj, dict):
        return {k: clean_data_for_json(v) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [clean_data_for_json(i) for i in obj]
    
    # Tipos numpy escalares
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        if np.isinf(obj) or np.isnan(obj):
            return None
        return float(obj)
    
    if isinstance(obj, np.bool_):
        return bool(obj)
    
    if isinstance(obj, np.ndarray):
        return clean_data_for_json(obj.tolist())
    
    # Manejar NaN/None genérico (incluye pd.NA)
    if pd.isna(obj):
        return None
        
    return obj
