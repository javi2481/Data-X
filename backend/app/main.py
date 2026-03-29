from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, sessions, analyze, reports, auth
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.db.client import db
from contextlib import asynccontextmanager

from app.core.telemetry import setup_telemetry
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Hardening de Seguridad: Prevenir arranque vulnerable
    if not settings.jwt_secret_key:
        raise RuntimeError("🚨 SEGURIDAD CRÍTICA: JWT_SECRET_KEY no está configurado. Abortando inicio.")
        
    # Startup
    setup_telemetry(app)
    await db.connect_to_db()
    
    # Crear índices — ACT-009: índices compuestos para queries frecuentes
    if db.db is not None:
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("user_id", unique=True)
        await db.db.sessions.create_index("session_id", unique=True)
        # Índice compuesto (user_id, created_at DESC): cubre la query más frecuente
        # find({"user_id": X}).sort("created_at", -1) en O(log n) en lugar de O(n)
        await db.db.sessions.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_sessions_user_date"
        )
        # Índices en colecciones Medallion para lookups por session_id
        await db.db.bronze.create_index("session_id", name="idx_bronze_session")
        await db.db.silver.create_index("session_id", name="idx_silver_session")
        await db.db.gold.create_index("session_id", name="idx_gold_session")
        print("🚀 Índices de MongoDB creados/verificados")
        
    yield
    # Shutdown
    await db.close_db_connection()

app = FastAPI(
    title="Data-X API",
    version="0.1.0",
    lifespan=lifespan
)
app.state.limiter = limiter

async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Demasiadas solicitudes. Intenta de nuevo en unos minutos."
        }
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Configurar CORS restrictivo
origins = settings.cors_origins.split(",") if settings.cors_origins else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Solo dominios explícitos
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    from app.core.logging import get_logger
    logger = get_logger("app.main")
    logger.warning("validation_error", error=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error_code": "VALIDATION_ERROR", "message": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    from app.core.logging import get_logger
    logger = get_logger("app.main")
    logger.error("internal_error", error=str(exc), traceback=traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "Ha ocurrido un error inesperado en el servidor."},
    )

# Registrar routers — ACT-012: eliminados registros legacy sin prefijo /api
# que generaban rutas duplicadas en el OpenAPI spec y potenciales colisiones.
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(reports.router, prefix="/api/sessions", tags=["reports"])
