"""
TechBridge カスタム例外定義
"""

from typing import Optional, Dict, Any


class TechBridgeException(Exception):
    """TechBridge基底例外クラス"""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(TechBridgeException):
    """データベース関連エラー"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, 500)


class ExternalAPIError(TechBridgeException):
    """外部API関連エラー"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, 502)


class SlackNotificationError(ExternalAPIError):
    """Slack通知エラー"""
    
    def __init__(self, message: str, channel: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if channel:
            error_details["channel"] = channel
        super().__init__(f"Slack notification failed: {message}", error_details)


class GoogleSheetsError(ExternalAPIError):
    """Google Sheets APIエラー"""
    
    def __init__(self, message: str, sheet_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if sheet_id:
            error_details["sheet_id"] = sheet_id
        super().__init__(f"Google Sheets API error: {message}", error_details)


class WorkflowError(TechBridgeException):
    """ワークフロー処理エラー"""
    
    def __init__(self, message: str, n_number: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if n_number:
            error_details["n_number"] = n_number
        super().__init__(f"Workflow error: {message}", error_details, 422)


class ValidationError(TechBridgeException):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(f"Validation error: {message}", error_details, 400)


class AuthenticationError(TechBridgeException):
    """認証エラー"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, 401)


class AuthorizationError(TechBridgeException):
    """認可エラー"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, 403)


class NotFoundError(TechBridgeException):
    """リソース未発見エラー"""
    
    def __init__(self, resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found: {identifier}"
        error_details = details or {}
        error_details.update({"resource": resource, "identifier": identifier})
        super().__init__(message, error_details, 404)


class ConflictError(TechBridgeException):
    """競合エラー"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Conflict: {message}", details, 409)


class RateLimitError(TechBridgeException):
    """レート制限エラー"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, 429)


class ConfigurationError(TechBridgeException):
    """設定エラー"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        super().__init__(f"Configuration error: {message}", error_details, 500)