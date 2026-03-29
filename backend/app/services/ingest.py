import pandas as pd
import io
import os
import tempfile
from typing import Any
import structlog
from app.core.config import settings

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

    async def ingest_file(self, file_bytes: bytes, filename: str, content_type: str, table_index: int = 0) -> dict[str, Any]:
        """
        Lee archivos usando Docling como pipeline principal, con pandas como fallback.
        Soporta CSV, PDF, XLSX, DOCX.
        """
        ext = os.path.splitext(filename)[1].lower()
        is_pdf = ext == ".pdf" or content_type == "application/pdf"
        is_excel = ext in [".xlsx", ".xls"] or content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]
        is_docx = ext == ".docx" or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_csv = ext == ".csv" or content_type in ["text/csv", "application/vnd.ms-excel"]

        conversion_metadata = {
            "method": "unknown",
            "confidence": None,
            "tables_found": 0,
            "selected_table": table_index,
            "narrative_context": None,
            "document_payload": None,
            "document_metadata": {},
            "tables": [],
            "provenance_refs": [],
            "schema_version": "legacy_v1",
        }

        # Intentar con Docling primero
        if DOCLING_AVAILABLE and (is_pdf or is_excel or is_docx):
            
            # REF-005: OpenCV Quality Gate opcional para PDFs
            # Permite deshabilitarlo en producción para reducir latencia de 2-5s
            if is_pdf and settings.enable_pdf_quality_gate:
                from app.services.opencv_pipeline import OpenCVPipeline
                cv_pipeline = OpenCVPipeline()
                images = cv_pipeline.pdf_to_cv2_images(file_bytes)
                if images:
                    # Evaluamos la primera página como muestra representativa
                    qg_result = cv_pipeline.quality_gate_image(images[0])
                    if not qg_result["passed"]:
                        logger.warning("ingest_rejected_vision_quality", variance=qg_result["variance"])
                        raise ValueError(
                            f"El documento fue rechazado por baja calidad visual (borroso o fuera de foco). "
                            f"Nivel de nitidez detectado: {round(qg_result['variance'], 2)}"
                        )
            elif is_pdf and not settings.enable_pdf_quality_gate:
                logger.debug("pdf_quality_gate_disabled", filename=filename)
                        
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                try:
                    result = self.converter.convert(tmp_path)
                    doc = result.document
                    conversion_metadata["document_payload"] = self._safe_export_document_dict(doc)
                    conversion_metadata["document_metadata"] = self._build_document_metadata(doc, filename, content_type)
                    conversion_metadata["schema_version"] = "docling_v1"
                    
                    # 1. Multitabla
                    tables = doc.tables
                    conversion_metadata["tables_found"] = len(tables)
                    conversion_metadata["tables"] = self._extract_tables_metadata(tables)
                    conversion_metadata["provenance_refs"] = self._build_min_provenance_refs(tables)
                    
                    if tables:
                        # Seleccionar tabla por index
                        idx = min(table_index, len(tables) - 1)
                        selected_table = tables[idx]
                        df = selected_table.export_to_dataframe()
                        
                        conversion_metadata["method"] = "docling"
                        conversion_metadata["selected_table"] = idx
                        # 3. Confidence scores
                        conversion_metadata["confidence"] = getattr(selected_table, "confidence", 0.9)
                        
                        # 2. Contexto narrativo completo en Markdown
                        try:
                            conversion_metadata["narrative_context"] = result.document.export_to_markdown()
                        except Exception:
                            pass
                            
                        logger.info("ingest_success", method="docling", filename=filename, tables=len(tables))
                        return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
                    
                    elif is_pdf or is_docx:
                        raise ValueError("No se encontraron tablas estructuradas en el documento.")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                logger.warning("docling_failed", error=str(e), filename=filename)

        # Fallback a Pandas
        try:
            if is_csv:
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python', dtype=str)
                except Exception:
                    df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
                
                conversion_metadata["method"] = "pandas_fallback"
                conversion_metadata["tables_found"] = 1
                conversion_metadata["schema_version"] = "legacy_v1"
                
                logger.info("ingest_success", method="fallback_csv", filename=filename)
                return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
            
            elif is_excel:
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
                conversion_metadata["method"] = "pandas_fallback"
                conversion_metadata["tables_found"] = 1
                conversion_metadata["schema_version"] = "legacy_v1"
                
                logger.info("ingest_success", method="fallback_excel", filename=filename)
                return self._prepare_response(df, filename, content_type, len(file_bytes), conversion_metadata)
            
            else:
                raise ValueError(f"Formato {ext} no soportado o sin tablas detectadas.")
                
        except Exception as e:
            logger.error("ingest_failed", error=str(e), filename=filename)
            raise ValueError(f"Error en la ingesta: {str(e)}")

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

    def _safe_export_document_dict(self, document: Any) -> dict[str, Any] | None:
        try:
            if hasattr(document, "export_to_dict"):
                return document.export_to_dict()
        except Exception:
            logger.warning("docling_export_to_dict_failed")
        return None

    def _build_document_metadata(self, document: Any, filename: str, content_type: str) -> dict[str, Any]:
        metadata = {
            "filename": filename,
            "content_type": content_type,
            "docling_available": DOCLING_AVAILABLE,
        }
        try:
            tables = getattr(document, "tables", [])
            metadata["tables_count"] = len(tables)
        except Exception:
            metadata["tables_count"] = 0
        return metadata

    def _extract_tables_metadata(self, tables: list[Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for idx, table in enumerate(tables):
            table_meta: dict[str, Any] = {
                "table_id": f"table_{idx}",
                "index": idx,
                "row_count": None,
                "column_count": None,
                "headers": [],
                "confidence": self._to_float(getattr(table, "confidence", None)),
            }
            try:
                df = table.export_to_dataframe()
                table_meta["row_count"] = len(df)
                table_meta["column_count"] = len(df.columns)
                table_meta["headers"] = [str(col) for col in df.columns]
            except Exception:
                pass
            result.append(table_meta)
        return result

    def _build_min_provenance_refs(self, tables: list[Any]) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for idx, _ in enumerate(tables):
            refs.append(
                {
                    "source_type": "table",
                    "ref_id": f"table_{idx}",
                    "table_id": f"table_{idx}",
                }
            )
        return refs

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        if hasattr(value, "value"):
            try:
                return float(value.value)
            except (TypeError, ValueError):
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
