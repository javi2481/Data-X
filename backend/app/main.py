from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import health, sessions, analyze

app = FastAPI(
    title="Data-X API",
    version="0.1.0"
)

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

# Registrar routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
