"""
TechBridge 設定管理
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    app_name: str = Field("TechBridge", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # データベース設定
    database_url: str = Field(..., env="DATABASE_URL")
    database_echo: bool = Field(False, env="DATABASE_ECHO")
    
    # Redis設定
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Slack設定
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    management_channel: str = Field("#techbridge-management", env="MANAGEMENT_CHANNEL")
    default_channel: str = Field("#techbridge-default", env="DEFAULT_CHANNEL")
    
    # Google Sheets設定
    google_sheets_id: str = Field(..., env="GOOGLE_SHEETS_ID")
    google_service_account_key: str = Field(..., env="GOOGLE_SERVICE_ACCOUNT_KEY")
    
    # Webhook設定
    tech_webhook_secret: str = Field(..., env="TECH_WEBHOOK_SECRET")
    techzip_webhook_secret: str = Field(..., env="TECHZIP_WEBHOOK_SECRET")
    
    # External URLs
    tech_project_url: Optional[str] = Field(None, env="TECH_PROJECT_URL")
    techzip_project_url: Optional[str] = Field(None, env="TECHZIP_PROJECT_URL")
    
    # CORS設定
    allowed_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"], 
        env="ALLOWED_ORIGINS"
    )
    
    # セキュリティ設定
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 監視・ログ設定
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    
    # 通知設定
    notification_retry_attempts: int = Field(3, env="NOTIFICATION_RETRY_ATTEMPTS")
    notification_retry_delay: int = Field(5, env="NOTIFICATION_RETRY_DELAY")
    
    # Google Sheets API設定
    sheets_api_timeout: int = Field(30, env="SHEETS_API_TIMEOUT")
    sheets_api_retry_attempts: int = Field(3, env="SHEETS_API_RETRY_ATTEMPTS")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """ログレベルの検証"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """CORS許可オリジンの解析"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("slack_bot_token")
    def validate_slack_token(cls, v):
        """Slack Bot トークンの検証"""
        if not v.startswith("xoxb-"):
            raise ValueError("Invalid Slack bot token format")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """データベースURLの検証"""
        if not v.startswith(("postgresql://", "sqlite:///")):
            raise ValueError("Unsupported database URL format")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()