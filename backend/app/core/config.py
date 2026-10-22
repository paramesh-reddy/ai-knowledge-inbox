"""Application settings and configuration."""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI Knowledge Inbox"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    # Database
    # Default to sqlite+aiosqlite if not explicitly configured with Postgres for frictionless local runs
    database_url: str = Field(
        default="sqlite+aiosqlite:///./knowledge_inbox.db",
        alias="DATABASE_URL",
    )

    # Google Gemini AI
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL")
    gemini_embedding_model: str = Field(
        default="gemini-embedding-2-preview", alias="GEMINI_EMBEDDING_MODEL"
    )
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")

    # Storage and Ingestion
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=10, alias="MAX_FILE_SIZE_MB")
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    retrieval_min_score: float = Field(default=0.35, alias="RETRIEVAL_MIN_SCORE")

    # Processing Worker
    job_max_retries: int = Field(default=3, alias="JOB_MAX_RETRIES")
    job_poll_interval_seconds: float = Field(default=2.0, alias="JOB_POLL_INTERVAL_SECONDS")
    job_stale_timeout_seconds: int = Field(default=300, alias="JOB_STALE_TIMEOUT_SECONDS")

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def resolve_api_key(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip() and v != "MY_GEMINI_API_KEY":
            return v.strip()
        env_val = os.getenv("GEMINI_API_KEY")
        if env_val and env_val.strip() and env_val != "MY_GEMINI_API_KEY":
            return env_val.strip()
        return None

    @property
    def is_postgres(self) -> bool:
        return "postgres" in self.database_url.lower()

    @property
    def absolute_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent.parent / path
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
