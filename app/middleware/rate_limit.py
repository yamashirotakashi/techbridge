"""レート制限ミドルウェア"""

import time
from typing import Dict, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """シンプルなレート制限ミドルウェア"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.clients: Dict[str, Tuple[float, int]] = {}
        
    def _get_client_id(self, request: Request) -> str:
        """クライアントIDを取得"""
        # APIキーがある場合はそれを使用
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # IPアドレスを使用
        if request.client:
            return f"ip:{request.client.host}"
        
        return "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """レート制限をチェック"""
        current_time = time.time()
        
        if client_id not in self.clients:
            self.clients[client_id] = (current_time, 1)
            return False
        
        last_request_time, request_count = self.clients[client_id]
        time_passed = current_time - last_request_time
        
        # 1分以上経過している場合はリセット
        if time_passed >= 60:
            self.clients[client_id] = (current_time, 1)
            return False
        
        # バーストサイズを超えていないかチェック
        if request_count >= self.burst_size and time_passed < 1:
            return True
        
        # 分あたりのリクエスト数をチェック
        expected_requests = (time_passed / 60) * self.requests_per_minute
        if request_count > expected_requests:
            return True
        
        # リクエストカウントを増やす
        self.clients[client_id] = (last_request_time, request_count + 1)
        return False
    
    async def dispatch(self, request: Request, call_next):
        """リクエストを処理"""
        # ヘルスチェックエンドポイントは除外
        if request.url.path == "/health":
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        
        if self._is_rate_limited(client_id):
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RateLimitExceeded",
                    "message": "リクエスト数が制限を超えました。しばらく待ってから再試行してください。"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        response = await call_next(request)
        
        # レート制限情報をヘッダーに追加
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        
        return response