import pandas as pd
import io
import os
import tempfile
from typing import Any
import structlog

# Intentar importar Docling
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

logger = structlog.get_logger(__name__)

class IngestService:
    def __init__(self):
        self.converter = DocumentConverter() if DOCLING_AVAILABLE else None

    async def ingest_file(self, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
        """
        Lee archivos usando Docling como pipeline principal, con pandas como fallback.
        """
        conversion_metadata = {
            "method": "unknown",
            "confidence": None,
            "tables_found": False
        }

        # Intentar con Docling primero
        if DOCLING_AVAILABLE:
            try:
                # Docling a veces prefiere archivos en disco, creamos un temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                try:
                    result = self.converter.convert(tmp_path)
                    
                    # Extraer tablas. Docling 2.x devuelve un objeto con tablas.
                    # Asumimos que queremos la primera tabla relevante para este MVP.
                    tables = result.document.tables
                    if tables:
                        # Convertir la primera tabla de Docling a Pandas DataFrame
                        # Nota: La API exacta puede variar según versión, pero export_to_dataframe es común en wrappers
                        df = tables[0].export_to_dataframe()
                        conversion_metadata["method"] = "docling"
                        conversion_metadata["tables_found"] = True
                        # Docling no siempre da un float simple de confidence por documento, 
                        # pero algunos modelos de tabla sí. Ponemos un placeholder o extraemos si existe.
                        conversion_metadata["confidence"] = getattr(result, "confidence", 0.95)
                        
                        logger.info("ingest_success", method="docling", filename=filename)
                        
                        return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                logger.warning("docling_failed", error=str(e), filename=filename)
                # Fallback a pandas

        # Fallback a Pandas (solo CSV por ahora según requisitos previos, o lo que soporte pandas)
        try:
            is_csv = (
                content_type in ["text/csv", "application/vnd.ms-excel"] or
                filename.lower().endswith(".csv")
            )
            
            if is_csv:
                # Intentar detectar separador automáticamente (, ; \t)
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python', dtype=str)
                except Exception:
                    # Fallback simple si falla la auto-detección
                    df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
                
                conversion_metadata["method"] = "fallback"
                conversion_metadata["reason"] = "docling_error_or_not_available" if DOCLING_AVAILABLE else "docling_not_installed"
                
                logger.info("ingest_success", method="fallback", filename=filename)
                return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
            else:
                raise ValueError(f"Formato {content_type} no soportado por el motor de fallback.")
                
        except Exception as e:
            logger.error("ingest_failed", error=str(e), filename=filename)
            raise ValueError(f"Error en la ingesta de datos: {str(e)}")

    def _prepare_response(self, df: pd.DataFrame, filename: str, content_type: str, size: int, conversion_metadata: dict) -> dict:
        schema_info = {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count": len(df),
            "null_counts": df.isnull().sum().to_dict()
        }

        source_metadata = {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size
        }

        return {
            "dataframe": df,
            "schema_info": schema_info,
            "source_metadata": source_metadata,
            "conversion_metadata": conversion_metadata
        }
