from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "datax"
    # LLM opcionales para Corte 2
    litellm_api_key: Optional[str] = ""
    litellm_model: Optional[str] = "gpt-4o-mini"
    cors_origins: list[str] = ["http://localhost:3000"]
    otel_service_name: str = "datax-backend"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
