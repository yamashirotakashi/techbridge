"""Application configuration."""

from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Project
    PROJECT_NAME: str = "TechBridge"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "techbridge"
    POSTGRES_PASSWORD: str = "techbridge"
    POSTGRES_DB: str = "techbridge"
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=info.data.get("POSTGRES_DB"),
        )

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    
    # Slack
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    SLACK_APP_TOKEN: Optional[str] = None
    
    # Google Sheets
    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_KEY: str  # JSON string or file path
    
    # External Systems
    TECH_WEBHOOK_SECRET: str
    TECHZIP_API_ENDPOINT: AnyHttpUrl
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "development"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"


settings = Settings()