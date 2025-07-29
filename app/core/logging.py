"""ロギング設定"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder

from app.core.config import settings


def setup_logging() -> None:
    """ロギングを設定"""
    
    # ログレベルを設定
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 標準ライブラリのロギング設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # structlogのプロセッサー設定
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.LINENO,
                CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.contextvars.merge_contextvars,
    ]
    
    # 出力フォーマットの設定
    if settings.LOG_FORMAT == "json":
        # JSON形式
        renderer = structlog.processors.JSONRenderer()
    else:
        # テキスト形式（開発環境向け）
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=30,
        )
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # フォーマッター設定
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    
    # ハンドラー設定
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)
    
    # 外部ライブラリのログレベル調整
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 開発環境では詳細ログを有効化
    if settings.ENVIRONMENT == "development":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """ロガーを取得"""
    return structlog.get_logger(name)


class LoggingContext:
    """ロギングコンテキストマネージャー"""
    
    def __init__(self, **kwargs: Any):
        self.context = kwargs
    
    def __enter__(self):
        structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.clear_contextvars()


def log_request_response(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra: Any
) -> None:
    """リクエスト/レスポンスをログ出力"""
    logger = get_logger("api.request")
    
    log_data: Dict[str, Any] = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **extra
    }
    
    if status_code >= 500:
        logger.error("Request failed", **log_data)
    elif status_code >= 400:
        logger.warning("Request error", **log_data)
    else:
        logger.info("Request completed", **log_data)


def log_webhook_event(
    event_type: str,
    source: str,
    n_number: str,
    success: bool,
    **extra: Any
) -> None:
    """Webhookイベントをログ出力"""
    logger = get_logger("webhook")
    
    log_data: Dict[str, Any] = {
        "event_type": event_type,
        "source": source,
        "n_number": n_number,
        "success": success,
        **extra
    }
    
    if success:
        logger.info("Webhook processed", **log_data)
    else:
        logger.error("Webhook failed", **log_data)


def log_slack_command(
    command: str,
    user: str,
    channel: str,
    success: bool,
    **extra: Any
) -> None:
    """Slackコマンドをログ出力"""
    logger = get_logger("slack.command")
    
    log_data: Dict[str, Any] = {
        "command": command,
        "user": user,
        "channel": channel,
        "success": success,
        **extra
    }
    
    if success:
        logger.info("Slack command executed", **log_data)
    else:
        logger.error("Slack command failed", **log_data)


def log_external_api_call(
    service: str,
    operation: str,
    success: bool,
    duration_ms: float,
    **extra: Any
) -> None:
    """外部API呼び出しをログ出力"""
    logger = get_logger("external_api")
    
    log_data: Dict[str, Any] = {
        "service": service,
        "operation": operation,
        "success": success,
        "duration_ms": duration_ms,
        **extra
    }
    
    if success:
        logger.info("External API call succeeded", **log_data)
    else:
        logger.error("External API call failed", **log_data)