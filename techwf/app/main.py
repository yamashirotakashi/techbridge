"""FastAPI application main module."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, slack, webhook
from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.error_handlers import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Startup
    print(f"Starting TechBridge API v{settings.VERSION}")
    
    yield
    
    # Shutdown
    print("Shutting down TechBridge API")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Register error handlers
register_error_handlers(app)

# Add custom middleware (順序重要: RequestID → Logging → RateLimit)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst_size=10)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(
    webhook.router,
    prefix=f"{settings.API_V1_STR}/webhook",
    tags=["webhook"],
)
app.include_router(
    slack.router,
    prefix=f"{settings.API_V1_STR}/slack",
    tags=["slack"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TechBridge Progress Bridge API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }