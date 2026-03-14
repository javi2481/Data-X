import pandas as pd
import io
from typing import Any

class IngestService:
    async def ingest_file(self, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
        """
        Lee archivos CSV y detecta información básica del schema.
        """
        # Validar si es CSV (por content_type o extensión)
        is_csv = (
            content_type in ["text/csv", "application/vnd.ms-excel"] or
            filename.lower().endswith(".csv")
        )
        
        if not is_csv:
            raise ValueError("Formato no soportado. Solo CSV por ahora.")

        try:
            # Leer CSV con pandas usando dtypes como strings para evitar conversiones prematuras
            # TODO: Docling entraría aquí después para manejar múltiples formatos
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        except Exception as e:
            raise ValueError(f"El CSV está mal formado: {str(e)}")

        # Detectar schema
        schema_info = {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count": len(df),
            "null_counts": df.isnull().sum().to_dict()
        }

        # Metadatos de la fuente
        source_metadata = {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes)
        }

        return {
            "dataframe": df,
            "schema_info": schema_info,
            "source_metadata": source_metadata
        }
