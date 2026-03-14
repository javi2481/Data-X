from fastapi import APIRouter, UploadFile, File, HTTPException, Query
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
from app.repositories.mongo import session_repo

router = APIRouter()

ingest_service = IngestService()
normalization_service = NormalizationService()
profiler_service = ProfilerService()
quality_gate = DoclingQualityGate()
finding_builder = FindingBuilder()
chart_spec_generator = ChartSpecGenerator()
eda_service = EDAExtendedService()
llm_service = LLMService()

@router.post("", 
    response_model=SessionResponse, 
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Crear nueva sesión de análisis",
    description="Carga un archivo CSV, ejecuta el pipeline Medallion (Bronze/Silver) y genera los hallazgos iniciales."
)
async def create_session(file: UploadFile = File(...)):
    """
    Crea una sesión a partir de un archivo subido.
    Pipeline Medallion: Bronze -> Silver.
    """
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_FILE", "message": "No se proporcionó un nombre de archivo"}
        )
    
    # Soporte solo para CSV en Corte 1
    allowed_extensions = [".csv"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return JSONResponse(
            status_code=400,
            content={"error_code": "UNSUPPORTED_FORMAT", "message": f"Formato de archivo no soportado. Solo se permiten: {', '.join(allowed_extensions)}"}
        )

    MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB
    
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={"error_code": "FILE_TOO_LARGE", "message": "El archivo es demasiado grande (máx 50MB)"}
            )
        
        if len(content) == 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_FILE", "message": "El archivo está vacío (0 bytes)"}
            )

        # 1. BRONZE: Ingesta (Docling/Fallback)
        ingest_result = await ingest_service.ingest_file(
            file_bytes=content,
            filename=file.filename,
            content_type=file.content_type or "text/csv"
        )
        
        df = ingest_result["dataframe"]
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
            source_metadata=source_metadata,
            ingested_at=ingested_at
        )
        
        await session_repo.save_bronze(bronze_record.model_dump())

        # 2. SILVER: Normalización + Perfilado + EDA Extendido + Findings + Charts
        # Normalización
        df = normalization_service.normalize(df)
        
        # Perfilado
        profile_data = profiler_service.profile(df)
        
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

        # Findings (ACTUALIZADO para Corte 2)
        findings = finding_builder.build_all_findings(df, eda_results=eda_results)
        
        # Charts (ACTUALIZADO para Corte 2)
        charts = chart_spec_generator.generate_all_charts(df, findings, eda_results=eda_results)

        # Preview de datos (convertir NaN a None para JSON)
        preview_df = df.head(50).where(df.head(50).notna(), None)
        data_preview = preview_df.to_dict(orient="records")

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

        # 3. GOLD (NUEVO Corte 2): Summary + Enriched Explanations
        if llm_service.api_key:
            report_data_for_llm = {
                "dataset_overview": overview.model_dump(),
                "findings": [f.model_dump() for f in findings],
                "column_profiles": [cp.model_dump() for cp in column_profiles]
            }
            
            executive_summary = await llm_service.generate_executive_summary(report_data_for_llm)
            
            # Enriquecer solo los más importantes (critical y warning)
            enriched_explanations = {}
            for f in findings:
                if f.severity in ["critical", "warning"]:
                    enriched = await llm_service.generate_explanation(f.model_dump(), report_data_for_llm["dataset_overview"])
                    enriched_explanations[f.finding_id] = enriched
            
            gold_record = GoldRecord(
                session_id=session_id,
                executive_summary=executive_summary,
                enriched_explanations=enriched_explanations,
                recommendations=["Revisar los hallazgos críticos de calidad", "Verificar correlaciones fuertes detectadas"],
                generated_at=datetime.utcnow()
            )
            await session_repo.save_gold(gold_record.model_dump())

        # 4. Sesión principal
        session_data = {
            "session_id": session_id,
            "status": "ready" if gate_result["status"] != "reject" else "error",
            "created_at": ingested_at,
            "source_metadata": source_metadata,
            "quality_decision": gate_result["status"],
            "dataset_overview": overview.model_dump(),
            "finding_count": len(findings),
            "contract_version": "v1"
        }
        await session_repo.create_session(session_data)
        
        return SessionResponse(**session_data)
        
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
async def list_sessions(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    sessions = await session_repo.list_sessions(limit=limit, offset=offset)
    return [SessionResponse(**s) for s in sessions]

@router.get("/{session_id}", 
    response_model=SessionResponse,
    summary="Obtener información de sesión",
    description="Recupera los metadatos y el resumen del estado actual de una sesión específica."
)
async def get_session(session_id: str):
    session = await session_repo.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error_code": "SESSION_NOT_FOUND", "message": "La sesión solicitada no existe"}
        )
    return SessionResponse(**session)
