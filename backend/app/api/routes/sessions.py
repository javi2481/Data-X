from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import uuid
from typing import Dict, Any

from app.schemas.session import SessionResponse
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.validation import ValidationService
from app.services.profiler import ProfilerService
from app.services.docling_quality_gate import DoclingQualityGate
from app.repositories.mongo import session_repo
from app.services.provenance import provenance_service

router = APIRouter()

ingest_service = IngestService()
normalization_service = NormalizationService()
validation_service = ValidationService()
profiler_service = ProfilerService()
quality_gate = DoclingQualityGate()

@router.post("", response_model=SessionResponse)
async def create_session(file: UploadFile = File(...)):
    """
    Crea una sesión a partir de un archivo subido.
    Realiza ingesta, normalización y validación inicial.
    Persiste los metadatos y resultados en MongoDB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó un nombre de archivo")
    
    try:
        content = await file.read()
        
        # 1. Ingesta (ahora incluye Docling/Fallback)
        ingest_result = await ingest_service.ingest_file(
            file_bytes=content,
            filename=file.filename,
            content_type=file.content_type or "text/csv"
        )
        
        df = ingest_result["dataframe"]
        schema_info = ingest_result["schema_info"]
        source_metadata = ingest_result["source_metadata"]
        conversion_metadata = ingest_result["conversion_metadata"]
        
        # 2. Quality Gate
        gate_result = quality_gate.evaluate(conversion_metadata)
        
        # 3. Normalización
        df = normalization_service.normalize(df)
        
        # 4. Validación
        alerts = validation_service.validate(df, schema_info)
        
        # 5. Perfilado de datos
        profile = profiler_service.profile(df)
        
        # Actualizar schema_info después de normalización
        schema_info["columns"] = list(df.columns)
        schema_info["row_count"] = len(df)
        
        # 6. Persistir en MongoDB
        session_id = f"sess_{uuid.uuid4()}"
        created_at = datetime.utcnow()
        
        # Provenance incluye info de ingesta
        steps = [
            {"step": "ingest", "method": conversion_metadata["method"], "timestamp": created_at},
            {"step": "quality_gate", "status": gate_result["status"], "timestamp": created_at},
            {"step": "normalize", "timestamp": created_at},
            {"step": "validate", "timestamp": created_at},
            {"step": "profile", "timestamp": created_at},
            {"step": "persist", "timestamp": created_at}
        ]

        session_data = {
            "session_id": session_id,
            "status": "ready" if gate_result["status"] != "fail" else "error",
            "created_at": created_at,
            "source_metadata": source_metadata,
            "schema_info": schema_info,
            "profile": profile,
            "alerts": alerts,
            "quality_gate": gate_result,
            "provenance": steps
        }
        
        await session_repo.create_session(session_data)
        
        return SessionResponse(
            session_id=session_id,
            status="ready" if gate_result["status"] != "fail" else "error",
            created_at=created_at,
            source_metadata=source_metadata,
            schema_info=schema_info,
            profile=profile,
            quality_gate=gate_result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
