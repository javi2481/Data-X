from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

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

@app.get("/health")
async def health():
    return {"status": "ok"}

# TODO: Registrar routers aquí
# app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
# app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
