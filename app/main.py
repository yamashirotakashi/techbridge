"""
TechBridge - 技術の泉シリーズ統合ワークフロー
FastAPI メインアプリケーション
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import TechBridgeException
from app.api.v1 import api_router
from app.utils.metrics import setup_metrics


# Sentry 初期化
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(auto_enabling_instrumentations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
    )

# StructLog 設定
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info("🚀 TechBridge starting up")
    
    # データベーステーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # メトリクス初期化
    setup_metrics()
    
    logger.info("✅ TechBridge startup complete")
    
    yield
    
    # 終了時処理
    logger.info("🛑 TechBridge shutting down")


# FastAPI アプリケーション初期化
app = FastAPI(
    title="TechBridge API",
    description="技術の泉シリーズ統合ワークフロー API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API ルーター追加
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(TechBridgeException)
async def techbridge_exception_handler(request: Request, exc: TechBridgeException):
    """TechBridge カスタム例外ハンドラー"""
    logger.error(
        "TechBridge error occurred",
        error_type=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    logger.error(
        "Unexpected error occurred",
        error_type=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "TechBridge API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": "techbridge",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )