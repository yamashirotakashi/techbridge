"""リクエストIDミドルウェア"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """リクエストIDを生成・管理するミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理"""
        # リクエストIDを生成または取得
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # リクエストのstateに保存
        request.state.request_id = request_id
        
        # ロガーにバインド
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None
        )
        
        try:
            # リクエストを処理
            response = await call_next(request)
            
            # レスポンスヘッダーにリクエストIDを追加
            response.headers["X-Request-ID"] = request_id
            
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            
            return response
            
        except Exception as e:
            logger.exception(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e)
            )
            raise
        finally:
            # コンテキストをクリア
            structlog.contextvars.clear_contextvars()