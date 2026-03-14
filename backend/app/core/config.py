from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "datax"
    litellm_api_key: str = ""
    litellm_model: str = "gpt-4o-mini"
    cors_origins: list[str] = ["http://localhost:3000"]
    otel_service_name: str = "datax-backend"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
