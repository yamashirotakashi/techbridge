"""グローバルエラーハンドラー"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
import structlog

from app.core.exceptions import (
    TechBridgeException,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError
)

logger = structlog.get_logger(__name__)


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


def create_error_response(
    error: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """エラーレスポンスを作成"""
    error_content = ErrorResponse(
        error=error,
        message=message,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(error_content)
    )


def register_error_handlers(app: FastAPI) -> None:
    """エラーハンドラーを登録"""
    
    @app.exception_handler(TechBridgeException)
    async def techbridge_exception_handler(
        request: Request, 
        exc: TechBridgeException
    ) -> JSONResponse:
        """TechBridge例外ハンドラー"""
        logger.error(
            "TechBridge exception",
            error_type=exc.__class__.__name__,
            message=str(exc),
            details=exc.details,
            path=request.url.path
        )
        
        return create_error_response(
            error=exc.__class__.__name__,
            message=str(exc),
            status_code=exc.status_code,
            details=exc.details,
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(
        request: Request, 
        exc: NotFoundError
    ) -> JSONResponse:
        """NotFoundエラーハンドラー"""
        logger.warning(
            "Resource not found",
            resource=exc.resource,
            identifier=exc.identifier,
            path=request.url.path
        )
        
        return create_error_response(
            error="NotFoundError",
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": exc.resource, "identifier": exc.identifier},
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, 
        exc: ValidationError
    ) -> JSONResponse:
        """検証エラーハンドラー"""
        logger.warning(
            "Validation error",
            message=str(exc),
            field=exc.field,
            value=exc.value,
            path=request.url.path
        )
        
        return create_error_response(
            error="ValidationError",
            message=str(exc),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": exc.field, "value": exc.value},
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, 
        exc: AuthenticationError
    ) -> JSONResponse:
        """認証エラーハンドラー"""
        logger.warning(
            "Authentication failed",
            message=str(exc),
            path=request.url.path
        )
        
        return create_error_response(
            error="AuthenticationError",
            message=str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED,
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, 
        exc: AuthorizationError
    ) -> JSONResponse:
        """認可エラーハンドラー"""
        logger.warning(
            "Authorization failed",
            message=str(exc),
            path=request.url.path
        )
        
        return create_error_response(
            error="AuthorizationError",
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN,
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(ConflictError)
    async def conflict_error_handler(
        request: Request, 
        exc: ConflictError
    ) -> JSONResponse:
        """競合エラーハンドラー"""
        logger.warning(
            "Resource conflict",
            message=str(exc),
            details=exc.details,
            path=request.url.path
        )
        
        return create_error_response(
            error="ConflictError",
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
            details=exc.details,
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(
        request: Request, 
        exc: ExternalServiceError
    ) -> JSONResponse:
        """外部サービスエラーハンドラー"""
        logger.error(
            "External service error",
            service=exc.service,
            message=str(exc),
            details=exc.details,
            path=request.url.path
        )
        
        return create_error_response(
            error="ExternalServiceError",
            message=str(exc),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": exc.service, **exc.details},
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """リクエスト検証エラーハンドラー"""
        logger.warning(
            "Request validation error",
            errors=exc.errors(),
            body=exc.body,
            path=request.url.path
        )
        
        return create_error_response(
            error="RequestValidationError",
            message="リクエストの検証に失敗しました",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": exc.errors()},
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, 
        exc: IntegrityError
    ) -> JSONResponse:
        """データベース整合性エラーハンドラー"""
        logger.error(
            "Database integrity error",
            error=str(exc),
            path=request.url.path
        )
        
        # ユーザーに詳細を見せないようにする
        return create_error_response(
            error="IntegrityError",
            message="データの整合性エラーが発生しました",
            status_code=status.HTTP_409_CONFLICT,
            request_id=getattr(request.state, "request_id", None)
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """一般的な例外ハンドラー"""
        logger.exception(
            "Unhandled exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            path=request.url.path
        )
        
        # 本番環境では詳細を隠す
        if app.debug:
            message = f"{type(exc).__name__}: {str(exc)}"
        else:
            message = "内部サーバーエラーが発生しました"
        
        return create_error_response(
            error="InternalServerError",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=getattr(request.state, "request_id", None)
        )