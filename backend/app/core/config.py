"""
Manufacturing Decision Copilot - Backend Configuration
"""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── Application ──────────────────────────────────────────────────
    app_name: str = "Manufacturing Decision Copilot"
    app_version: str = "0.1.0"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-in-production"

    # ─── API ─────────────────────────────────────────────────────────
    api_prefix: str = "/api/v1"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ─── AI Provider Configuration ─────────────────────────────────────
    # Supported LLM providers: "gemini", "openai", "groq", "ollama"
    ai_provider: Literal["gemini", "openai", "groq", "ollama"] = "gemini"
    
    # Supported Embedding providers: "local", "gemini", "openai"
    embedding_provider: Literal["local", "gemini", "openai"] = "local"

    # Gemini API Settings (Free tier from Google AI Studio)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # OpenAI API Settings (Optional fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Groq API Settings (Optional fallback)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Ollama Settings (Optional offline fallback)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Local Embedding Model Name
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"

    # ─── Database ─────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mdc_db"

    @property
    def async_database_url(self) -> str:
        """Returns database URL formatted with asyncpg driver prefix for SQLAlchemy async engine."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # asyncpg uses ssl=require instead of sslmode=require
        url = url.replace("sslmode=require", "ssl=require")
        return url

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL for Alembic migrations and psycopg2 worker connections."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")

    # ─── Redis ────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ─── ChromaDB ─────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "document_chunks"

    # ─── Storage ──────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ─── Scoring Defaults ─────────────────────────────────────────────
    default_cost_weight: float = 0.30
    default_quality_weight: float = 0.20
    default_delivery_weight: float = 0.15
    default_risk_weight: float = 0.15
    default_capability_weight: float = 0.10
    default_compliance_weight: float = 0.10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
