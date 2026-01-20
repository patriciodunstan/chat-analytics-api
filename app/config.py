"""Application configuration using Pydantic Settings."""
from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    @property
    def database_url(self) -> str:
        url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/chat_analytics")
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # JWT
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # LLM Configuration (GLM-4.6 via Z.AI)
    llm_api_key: str = ""
    llm_model: str = "glm-4.6"
    llm_base_url: str = "https://api.z.ai/api/paas/v4/"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
