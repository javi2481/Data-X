from fastapi import APIRouter, HTTPException, Depends, status, Request
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import auth_service
from app.core.rate_limit import limiter
from app.db.client import db
from datetime import datetime
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/hour")
async def register(request: Request, user_in: UserCreate):
    # Verificar si el usuario ya existe
    existing_user = await db.db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado"
        )
    
    # Crear nuevo usuario
    user_id = str(uuid.uuid4())
    hashed_password = auth_service.hash_password(user_in.password)
    
    user_dict = {
        "user_id": user_id,
        "email": user_in.email,
        "password": hashed_password,
        "name": user_in.name,
        "created_at": datetime.utcnow()
    }
    
    await db.db.users.insert_one(user_dict)
    
    # Generar token
    access_token = auth_service.create_access_token(user_id, user_in.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    user = await db.db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    if not auth_service.verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    access_token = auth_service.create_access_token(user["user_id"], user["email"])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

from app.api.dependencies import get_current_user

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.db.users.find_one({"user_id": current_user["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.get("/me/usage", summary="Obtener estadísticas de uso y costos")
async def get_my_usage(current_user: dict = Depends(get_current_user)):
    """
    Calcula el costo total de LLM, tokens consumidos y tiempo de procesamiento
    asociado a las sesiones de este usuario (Tier B2B/Enterprise).
    """
    user_id = current_user["sub"]
    
    pipeline = [
        {"$lookup": {
            "from": "sessions",
            "localField": "session_id",
            "foreignField": "session_id",
            "as": "session_info"
        }},
        {"$unwind": "$session_info"},
        {"$match": {"session_info.user_id": user_id}},
        {"$group": {
            "_id": "$session_info.user_id",
            "total_cost_usd": {"$sum": "$llm_cost_usd"},
            "total_tokens": {"$sum": "$tokens_to_llm"},
            "total_processing_time_ms": {"$sum": "$duration_ms"}
        }}
    ]
    
    cursor = db.db.usage_events.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    
    sessions_count = await db.db.sessions.count_documents({"user_id": user_id})
    
    return {
        "user_id": user_id,
        "total_sessions": sessions_count,
        "total_cost_usd": round(result[0].get("total_cost_usd", 0.0), 4) if result else 0.0,
        "total_tokens": result[0].get("total_tokens", 0) if result else 0,
        "total_processing_time_ms": result[0].get("total_processing_time_ms", 0) if result else 0
    }
