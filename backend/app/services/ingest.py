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
        Soporta CSV, PDF, XLSX, XLS.
        """
        ext = os.path.splitext(filename)[1].lower()
        is_pdf = ext == ".pdf" or content_type == "application/pdf"
        is_excel = ext in [".xlsx", ".xls"] or content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]
        is_csv = ext == ".csv" or content_type in ["text/csv", "application/vnd.ms-excel"]

        conversion_metadata = {
            "method": "unknown",
            "confidence": None,
            "tables_found": False
        }

        # Intentar con Docling primero (Preferido para PDF y Excel)
        if DOCLING_AVAILABLE:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                try:
                    result = self.converter.convert(tmp_path)
                    
                    # Extraer tablas. Docling 2.x devuelve un objeto con tablas.
                    tables = result.document.tables
                    if tables:
                        # Convertir la primera tabla de Docling a Pandas DataFrame
                        df = tables[0].export_to_dataframe()
                        conversion_metadata["method"] = "docling"
                        conversion_metadata["tables_found"] = True
                        conversion_metadata["confidence"] = getattr(result, "confidence", 0.95)
                        
                        logger.info("ingest_success", method="docling", filename=filename, format=ext)
                        return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
                    
                    elif is_pdf:
                        # Requerimiento: Si PDF no tiene tablas, error.
                        raise ValueError("No se encontraron tablas estructuradas en el archivo PDF.")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                if is_pdf and "No se encontraron tablas" in str(e):
                    raise
                logger.warning("docling_failed", error=str(e), filename=filename)

        # Fallback a Pandas
        try:
            if is_csv:
                # Intentar detectar separador automáticamente (, ; \t)
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python', dtype=str)
                except Exception:
                    # Fallback simple si falla la auto-detección
                    df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
                
                conversion_metadata["method"] = "fallback"
                conversion_metadata["reason"] = "docling_error_or_not_available" if DOCLING_AVAILABLE else "docling_not_installed"
                
                logger.info("ingest_success", method="fallback_csv", filename=filename)
                return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
            
            elif is_excel:
                # Fallback para Excel usando pandas (requiere openpyxl para xlsx)
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
                conversion_metadata["method"] = "fallback"
                conversion_metadata["reason"] = "docling_error_or_not_available"
                
                logger.info("ingest_success", method="fallback_excel", filename=filename)
                return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
            
            elif is_pdf:
                # Si llegamos aquí y es PDF, es que falló Docling y no hay fallback razonable para tablas
                raise ValueError("El motor de análisis Docling no pudo extraer tablas del PDF y no hay fallback disponible.")
                
            else:
                raise ValueError(f"Formato {ext} / {content_type} no soportado por el motor de ingesta.")
                
        except Exception as e:
            if isinstance(e, ValueError) and "Docling" in str(e):
                raise
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
