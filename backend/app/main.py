from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, sessions, analyze, reports
from app.db.client import db
from contextlib import asynccontextmanager

from app.core.telemetry import setup_telemetry
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_telemetry(app)
    await db.connect_to_db()
    
    # Crear índices
    if db.db is not None:
        await db.db.sessions.create_index("session_id", unique=True)
        await db.db.bronze.create_index("session_id")
        await db.db.silver.create_index("session_id")
        await db.db.sessions.create_index([("created_at", -1)])
        print("🚀 Índices de MongoDB creados/verificados")
        
    yield
    # Shutdown
    await db.close_db_connection()

app = FastAPI(
    title="Data-X API",
    version="0.1.0",
    lifespan=lifespan
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Configurar CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error_code": "VALIDATION_ERROR", "message": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # En producción usaríamos un logger aquí
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": f"Ha ocurrido un error inesperado: {str(exc)}"},
    )

# Registrar routers (prefijo /api)
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(reports.router, prefix="/api/sessions", tags=["reports"])

# Mantener compatibilidad (sin /api) - Opcional, pero recomendado
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
