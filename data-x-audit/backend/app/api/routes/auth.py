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
