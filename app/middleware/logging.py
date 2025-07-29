"""ロギングミドルウェア"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_request_response


class LoggingMiddleware(BaseHTTPMiddleware):
    """リクエスト/レスポンスのロギングミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理してログを記録"""
        # 開始時間を記録
        start_time = time.time()
        
        # リクエスト情報を収集
        request_info = {
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
        
        # リクエストIDがあれば追加
        if hasattr(request.state, "request_id"):
            request_info["request_id"] = request.state.request_id
        
        try:
            # リクエストを処理
            response = await call_next(request)
            
            # 処理時間を計算
            duration_ms = (time.time() - start_time) * 1000
            
            # ログを記録
            log_request_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                **request_info
            )
            
            return response
            
        except Exception as e:
            # エラー時もログを記録
            duration_ms = (time.time() - start_time) * 1000
            
            log_request_response(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                error=str(e),
                **request_info
            )
            
            raise