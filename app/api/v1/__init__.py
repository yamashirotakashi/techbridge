"""
TechBridge API v1
"""

from fastapi import APIRouter

from app.api.v1 import auth, progress, webhooks, slack, test

# メインAPIルーター
api_router = APIRouter()

# 各エンドポイントのルーターを追加
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])
api_router.include_router(slack.router, prefix="/slack", tags=["slack"])
api_router.include_router(test.router, prefix="/test", tags=["testing"])