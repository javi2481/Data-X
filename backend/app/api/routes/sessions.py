from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid
from typing import Any, List

from app.schemas.session import SessionResponse
from app.schemas.analyze import ErrorResponse
from app.schemas.medallion import BronzeRecord, SilverRecord, GoldRecord, DatasetOverview, ColumnProfile
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.profiler import ProfilerService
from app.services.docling_quality_gate import DoclingQualityGate
from app.services.finding_builder import FindingBuilder
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.eda_extended import EDAExtendedService
from app.services.llm_service import LLMService
from app.services.schema_validator import SchemaValidator
from app.services.statistical_tests import StatisticalTestsService
from app.services.document_chunking_service import DocumentChunkingService
from app.services.docling_chunking_service import get_docling_chunking_service
from app.services.ingestion.distributed_strategy import DistributedIngestionService
from app.services.embedding_service import EmbeddingService
from app.repositories.mongo import session_repo
from app.api.dependencies import get_current_user
from fastapi import Depends
from app.core.rate_limit import limiter

router = APIRouter()

ingest_service = IngestService()
normalization_service = NormalizationService()
profiler_service = ProfilerService()
quality_gate = DoclingQualityGate()
finding_builder = FindingBuilder()
chart_spec_generator = ChartSpecGenerator()
eda_service = EDAExtendedService()
llm_service = LLMService()
schema_validator = SchemaValidator()
stat_tests_service = StatisticalTestsService()
chunking_service = DocumentChunkingService()  # Legacy fallback
docling_chunking_service = get_docling_chunking_service()  # Sprint 1: HybridChunker
distributed_ingestion_service = DistributedIngestionService()

def get_ingestion_strategy(current_user: dict) -> Any:
    """
    Patrón Strategy: Decide entre pipeline local (Docling) o distribuido (IBM Data Prep Kit).
    """
    tier = current_user.get("tier", "lite")
    if tier == "enterprise":
        import structlog
        structlog.get_logger(__name__).info("strategy_injection", strategy="distributed_ingestion", user=current_user["sub"])
        return distributed_ingestion_service
    return ingest_service

@router.post("", 
    response_model=SessionResponse, 
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Crear nueva sesión de análisis",
    description="Carga un archivo CSV, ejecuta el pipeline Medallion (Bronze/Silver) y genera los hallazgos iniciales."
)
@limiter.limit("20/hour")
async def create_session(
    request: Request,
    file: UploadFile = File(...),
    table_index: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una sesión a partir de un archivo subido.
    Pipeline Medallion: Bronze -> Silver.
    """
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_FILE", "message": "No se proporcionó un nombre de archivo"}
        )
    
    # Soporte para CSV, XLSX, XLS, PDF y DOCX
    allowed_extensions = [".csv", ".xlsx", ".xls", ".pdf", ".docx"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "UNSUPPORTED_FORMAT", 
                "message": f"Formato de archivo no soportado. Formatos aceptados: {', '.join(allowed_extensions)}"
            }
        )

    MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB
    
    try:
        content = await file.read()
        
        # Validar tamaño máximo
        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={"error_code": "FILE_TOO_LARGE", "message": "El archivo es demasiado grande (máx 50MB)"}
            )
            
        # Validar MIME type real y Magic Numbers
        filename_lower = file.filename.lower()
        content_type = file.content_type
        
        if filename_lower.endswith(".pdf"):
            if not content.startswith(b"%PDF"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo PDF no tiene una firma válida (%PDF)"}
                )
        elif filename_lower.endswith(".xlsx"):
            if not content.startswith(b"PK\x03\x04"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo XLSX no tiene una firma válida (PK header)"}
                )
        elif filename_lower.endswith(".docx"):
            if not content.startswith(b"PK\x03\x04"):
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo DOCX no tiene una firma válida (PK header)"}
                )
        elif filename_lower.endswith(".csv"):
            if content_type not in ["text/csv", "text/plain"]:
                return JSONResponse(
                    status_code=400,
                    content={"error_code": "INVALID_FILE", "message": "El archivo CSV debe ser text/csv o text/plain"}
                )
        
        if len(content) == 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_FILE", "message": "El archivo está vacío (0 bytes)"}
            )

        # 1. BRONZE: Ingesta (Docling/Fallback) con timeout de 60s
        import asyncio
        import time
        start_time = time.time()
        
        ingestion_strategy = get_ingestion_strategy(current_user)
        
        try:
            ingest_result = await asyncio.wait_for(
                ingestion_strategy.ingest_file(
                    file_bytes=content,
                    filename=file.filename,
                    content_type=file.content_type or "text/csv",
                    table_index=table_index,
                ),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=400,
                content={"error_code": "PROCESSING_TIMEOUT", "message": "Archivo demasiado grande o complejo para procesar (timeout 60s)"}
            )
        
        df = ingest_result["dataframe"]
        
        # Validar que el DataFrame no esté vacío
        if df.empty or len(df.columns) == 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_FILE", "message": "El archivo no contiene datos válidos o columnas legibles"}
            )
        source_metadata = ingest_result["source_metadata"]
        conversion_metadata = ingest_result["conversion_metadata"]
        
        # Quality Gate
        gate_result = quality_gate.evaluate(conversion_metadata)
        
        session_id = f"sess_{uuid.uuid4()}"
        ingested_at = datetime.utcnow()

        bronze_record = BronzeRecord(
            session_id=session_id,
            original_filename=file.filename,
            content_type=file.content_type or "text/csv",
            size_bytes=len(content),
            ingestion_source=conversion_metadata["method"],
            quality_decision=gate_result["status"],
            quality_scores=gate_result.get("scores", {}),
            quality_baseline=gate_result.get("baseline", {}),
            schema_version=conversion_metadata.get("schema_version", "legacy_v1"),
            source_metadata=source_metadata,
            tables_found=conversion_metadata.get("tables_found", 1),
            selected_table_index=conversion_metadata.get("selected_table", 0),
            narrative_context=conversion_metadata.get("narrative_context"),
            table_confidence=conversion_metadata.get("confidence"),
            document_payload=conversion_metadata.get("document_payload"),
            document_metadata=conversion_metadata.get("document_metadata", {}),
            tables=conversion_metadata.get("tables", []),
            provenance_refs=conversion_metadata.get("provenance_refs", []),
            ingested_at=ingested_at
        )
        
        await session_repo.save_bronze(bronze_record.model_dump())

        if gate_result["status"] == "reject":
            session_data = {
                "session_id": session_id,
                "user_id": current_user["sub"],
                "status": "error",
                "created_at": ingested_at.isoformat(),
                "source_metadata": source_metadata,
                "quality_decision": gate_result["status"],
                "finding_count": 0,
                "contract_version": "v1",
            }
            await session_repo.create_session(session_data.copy())
            session_data.pop("_id", None)
            return JSONResponse(
                status_code=200,
                content={
                    **session_data,
                    "warnings": gate_result.get("warnings", []),
                    "message": "Documento rechazado por quality gate; no se ejecutó análisis Silver/Gold.",
                },
            )

        # 2. SILVER: Normalización + Perfilado + EDA Extendido + Findings + Charts
        # Normalización
        df = normalization_service.normalize(df)
        
        # Perfilado
        profile_data = profiler_service.profile(df)
        
        # Validación de esquema (Corte 3)
        schema_results = schema_validator.validate_and_report(df)
        
        # EDA Extendido (Corte 2)
        eda_results = {
            "correlations": eda_service.compute_correlations(df),
            "outliers": eda_service.detect_all_outliers(df),
            "distributions": eda_service.analyze_distributions(df)
        }
        
        column_profiles = []
        for col_name, col_data in profile_data.items():
            column_profiles.append(ColumnProfile(
                name=col_name,
                dtype=col_data.get("dtype", "unknown"),
                count=col_data.get("count", 0),
                null_count=col_data.get("null_count", 0),
                null_percent=col_data.get("null_percent", 0.0),
                unique_count=col_data.get("unique_count", 0),
                cardinality=col_data.get("cardinality", 0.0),
                min=col_data.get("min"),
                max=col_data.get("max"),
                mean=col_data.get("mean"),
                median=col_data.get("median"),
                std=col_data.get("std"),
                top_values=col_data.get("top_values")
            ))

        overview = DatasetOverview(
            row_count=len(df),
            column_count=len(df.columns),
            numeric_columns=len(df.select_dtypes(include=['number']).columns),
            categorical_columns=len(df.select_dtypes(include=['object', 'category']).columns),
            datetime_columns=len(df.select_dtypes(include=['datetime']).columns),
            total_nulls=int(df.isnull().sum().sum()),
            total_null_percent=float(df.isnull().sum().sum() / (len(df) * len(df.columns))) if len(df) > 0 else 0.0,
            duplicate_rows=int(df.duplicated().sum()),
            duplicate_percent=float(df.duplicated().sum() / len(df)) if len(df) > 0 else 0.0
        )

        # Tests Estadísticos (Corte 4)
        test_results = stat_tests_service.run_all_tests(df)

        # Findings (ACTUALIZADO para Corte 4)
        findings = finding_builder.build_all_findings(
            df, 
            eda_results=eda_results, 
            schema_results=schema_results,
            test_results=test_results
        )
        
        # Charts (ACTUALIZADO para Corte 2)
        charts = chart_spec_generator.generate_all_charts(df, findings, eda_results=eda_results)

        # Preview de datos (usar helper de serialización segura)
        from app.core.serialization import clean_data_for_json
        data_preview = clean_data_for_json(df.head(50))

        silver_record = SilverRecord(
            session_id=session_id,
            dataset_overview=overview,
            column_profiles=column_profiles,
            findings=[f.model_dump() for f in findings],
            chart_specs=[c.model_dump() for c in charts],
            data_preview=data_preview,
            processed_at=datetime.utcnow()
        )
        
        await session_repo.save_silver(silver_record.model_dump())

        # 2.5 Chunks documentales + índice híbrido (Sprint 1: HybridChunker cuando disponible)
        # Usar DoclingChunkingService (HybridChunker) si hay document_payload
        if bronze_record.document_payload:
            document_chunks = docling_chunking_service.build_chunks(
                session_id=session_id,
                document_payload=bronze_record.document_payload,
                narrative_context=bronze_record.narrative_context,
                tables=[t.model_dump() if hasattr(t, "model_dump") else t for t in bronze_record.tables],
            )
        else:
            # Fallback a chunking legacy para archivos sin document_payload (CSV)
            document_chunks = chunking_service.build_chunks(
                session_id=session_id,
                narrative_context=bronze_record.narrative_context,
                tables=[t.model_dump() if hasattr(t, "model_dump") else t for t in bronze_record.tables],
                document_payload=None,
            )
        chunks_saved = await session_repo.save_document_chunks(session_id, document_chunks)

        hybrid_embedding_service = EmbeddingService()
        await hybrid_embedding_service.index_hybrid_sources(
            findings=[f.model_dump() for f in findings],
            chunks=document_chunks,
        )
        await session_repo.save_hybrid_embeddings_cache(
            {
                "session_id": session_id,
                "faiss_index": hybrid_embedding_service.serialize_index(),
                "source_map": hybrid_embedding_service.source_map,
                "source_ids": hybrid_embedding_service.source_ids,
                "model_name": hybrid_embedding_service.model_name,
                "created_at": datetime.now(),
                "stats": {
                    "chunks_indexed": chunks_saved,
                    "findings_indexed": len(findings),
                    "total_indexed": len(hybrid_embedding_service.source_ids),
                },
            }
        )

        # 3. GOLD (Corte 4): Summary + Enriched Explanations with costs
        if llm_service.router:
            report_data_for_llm = {
                "original_filename": file.filename,
                "row_count": len(df),
                "column_count": len(df.columns),
                "narrative_context": bronze_record.narrative_context,
                "dataset_overview": overview.model_dump(),
                "findings": [f.model_dump() for f in findings],
                "column_profiles": [cp.model_dump() for cp in column_profiles]
            }
            
            summary_result = await llm_service.generate_executive_summary(report_data_for_llm)
            
            total_cost = summary_result.get("cost_usd", 0.0)
            calls_count = 1
            model_used = summary_result.get("model", "")
            
            enriched_explanations = {}
            # Enriquecer solo los más críticos para ahorrar tokens
            for f in findings:
                if f.severity in ["critical", "important"]:
                    enriched = await llm_service.generate_enriched_explanation(f, report_data_for_llm)
                    if enriched.get("explanation"):
                        enriched_explanations[f.finding_id] = enriched["explanation"]
                        total_cost += enriched.get("cost_usd", 0.0)
                        calls_count += 1
                        model_used = enriched.get("model", model_used)
            
            # Generar recomendaciones dinámicas
            recommendations = await llm_service.generate_recommendations(findings)
            
            gold_record = GoldRecord(
                session_id=session_id,
                executive_summary=summary_result.get("summary", ""),
                enriched_explanations=enriched_explanations,
                recommendations=recommendations,
                llm_cost_usd=total_cost,
                llm_model_used=model_used,
                llm_calls_count=calls_count,
                generated_at=datetime.utcnow()
            )
            await session_repo.save_gold(gold_record.model_dump())

        # 4. Sesión principal
        duration = time.time() - start_time
        from app.core.logging import get_logger
        struct_logger = get_logger(__name__)
        struct_logger.info("session_processing_complete", session_id=session_id, duration_sec=round(duration, 2))

        session_data = {
            "session_id": session_id,
            "user_id": current_user["sub"],
            "status": "ready" if gate_result["status"] != "reject" else "error",
            "created_at": ingested_at.isoformat(),
            "source_metadata": source_metadata,
            "quality_decision": gate_result["status"],
            "dataset_overview": overview.model_dump(),
            "finding_count": len(findings),
            "document_chunks_count": chunks_saved,
            "contract_version": "v1"
        }
        await session_repo.create_session(session_data.copy())
        
        # Eliminar _id si se agregó durante el guardado
        session_data.pop("_id", None)
        
        return JSONResponse(status_code=200, content=session_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("", 
    response_model=List[SessionResponse],
    summary="Listar historial de sesiones",
    description="Devuelve una lista paginada de todas las sesiones realizadas ordenadas por fecha."
)
@limiter.limit("100/minute")
async def list_sessions(
    request: Request,
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    sessions = await session_repo.list_sessions_by_user(
        user_id=current_user["sub"],
        limit=limit, 
        offset=offset
    )
    return [SessionResponse(**s) for s in sessions]

@router.get("/{session_id}", 
    response_model=SessionResponse,
    summary="Obtener información de sesión",
    description="Recupera los metadatos y el resumen del estado actual de una sesión específica."
)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )
    
    if session.get("user_id") != current_user["sub"]:
        return JSONResponse(
            status_code=403,
            content={"error_code": "ACCESS_DENIED", "message": "No tienes permiso para acceder a esta sesión"}
        )
        
    return SessionResponse(**session)
