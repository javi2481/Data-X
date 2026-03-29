from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List
import warnings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "datax"

    # LLM
    litellm_api_key: Optional[str] = ""
    litellm_model: Optional[str] = "gpt-4o-mini"
    # ACT-007: modelo de fallback para alta disponibilidad del pipeline IA
    # Ej: "openrouter/anthropic/claude-3-haiku" o "openrouter/openai/gpt-3.5-turbo"
    litellm_fallback_model: Optional[str] = ""

    cors_origins: str = "http://localhost:3000"
    otel_service_name: str = "datax-backend"
    otel_exporter_otlp_endpoint: Optional[str] = "http://localhost:4317"

    # Redis (ARQ job queue)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # REF-005: hacer el quality gate de PDF opcional para ahorrar latencia
    enable_pdf_quality_gate: bool = True

    # ACT-014: detectar configuraciones incompletas en startup, no en runtime
    @model_validator(mode="after")
    def check_critical_config(self) -> "Settings":
        if not self.jwt_secret_key:
            warnings.warn(
                "JWT_SECRET_KEY no configurada. El servidor rechazará el arranque.",
                stacklevel=2,
            )
        if not self.litellm_api_key:
            warnings.warn(
                "LITELLM_API_KEY no configurada. Las funciones de IA estarán deshabilitadas.",
                stacklevel=2,
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
