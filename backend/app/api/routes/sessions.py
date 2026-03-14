from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import uuid
from typing import Dict, Any

from app.schemas.session import SessionResponse
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.validation import ValidationService

router = APIRouter()

# Store temporal en memoria
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

ingest_service = IngestService()
normalization_service = NormalizationService()
validation_service = ValidationService()

@router.post("", response_model=SessionResponse)
async def create_session(file: UploadFile = File(...)):
    """
    Crea una sesión a partir de un archivo subido.
    Realiza ingesta, normalización y validación inicial.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó un nombre de archivo")
    
    try:
        content = await file.read()
        
        # 1. Ingesta
        ingest_result = await ingest_service.ingest_file(
            file_bytes=content,
            filename=file.filename,
            content_type=file.content_type or "text/csv"
        )
        
        df = ingest_result["dataframe"]
        schema_info = ingest_result["schema_info"]
        source_metadata = ingest_result["source_metadata"]
        
        # 2. Normalización
        df = normalization_service.normalize(df)
        
        # 3. Validación
        alerts = validation_service.validate(df, schema_info)
        
        # Actualizar schema_info después de normalización (opcional pero recomendado)
        schema_info["columns"] = list(df.columns)
        schema_info["row_count"] = len(df)
        
        # 4. Persistir en memoria (temporal)
        session_id = str(uuid.uuid4())
        SESSION_STORE[session_id] = {
            "df": df,
            "schema_info": schema_info,
            "source_metadata": source_metadata,
            "alerts": alerts,
            "created_at": datetime.utcnow()
        }
        
        return SessionResponse(
            session_id=session_id,
            status="ready",
            created_at=SESSION_STORE[session_id]["created_at"],
            source_metadata=source_metadata,
            schema_info=schema_info
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # En producción usaríamos un logger aquí
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
