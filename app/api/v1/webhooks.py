"""Webhookエンドポイント"""

import hmac
import hashlib
import json
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.deps import get_db
from app.core.logging import log_webhook_event
from app.services.workflow import WorkflowService
from app.services.slack import SlackService
from app.models.enums import ProgressStatus as WorkflowStatus

logger = structlog.get_logger(__name__)
router = APIRouter()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Webhook署名を検証"""
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/tech/status-change")
async def handle_tech_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """[tech]からのステータス変更Webhookを処理"""
    # 署名を取得
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature"
        )
    
    # ボディを取得
    body = await request.body()
    
    # 署名を検証
    if not verify_webhook_signature(body, signature, settings.TECH_WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # JSONをパース
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    logger.info(
        "Received tech webhook",
        event=payload.get("event"),
        n_number=payload.get("n_number"),
        status=payload.get("status")
    )
    
    try:
        # ワークフローサービスを使用して更新
        workflow_service = WorkflowService(db)
        
        # ステータスをEnumに変換
        status_str = payload.get("status", "").upper()
        try:
            new_status = WorkflowStatus[status_str]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_str}"
            )
        
        # ワークフローアイテムを作成または更新
        item = await workflow_service.create_or_update(
            n_number=payload.get("n_number"),
            book_id=payload.get("book_id"),
            title=payload.get("title"),
            author=payload.get("author"),
            status=new_status,
            repository_name=f"n{payload.get('n_number', '').lower()}-{payload.get('title', '').replace(' ', '-').lower()[:30]}",
            slack_channel="#general",  # TODO: Google Sheetsから取得
            workflow_metadata=payload.get("metadata", {})
        )
        
        # Slack通知を送信
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        await slack_service.send_status_update(
            channel=item.slack_channel,
            n_number=item.n_number,
            title=item.title,
            old_status=None,  # 新規の場合
            new_status=new_status
        )
        
        # ログを記録
        log_webhook_event(
            event_type="status_change",
            source="tech",
            n_number=item.n_number,
            success=True,
            status=new_status.value
        )
        
        return {
            "status": "success",
            "n_number": item.n_number,
            "message": f"Status updated to {new_status.value}"
        }
        
    except Exception as e:
        logger.error(
            "Failed to process tech webhook",
            error=str(e),
            n_number=payload.get("n_number")
        )
        
        log_webhook_event(
            event_type="status_change",
            source="tech",
            n_number=payload.get("n_number", "unknown"),
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.post("/techzip/completion")
async def handle_techzip_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """[techzip]からの完了通知Webhookを処理"""
    # 署名を取得
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature"
        )
    
    # ボディを取得
    body = await request.body()
    
    # 署名を検証
    if not verify_webhook_signature(body, signature, settings.TECHZIP_WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # JSONをパース
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    logger.info(
        "Received techzip webhook",
        event=payload.get("event"),
        n_number=payload.get("n_number"),
        repository_name=payload.get("repository_name")
    )
    
    try:
        # ワークフローサービスを使用して更新
        workflow_service = WorkflowService(db)
        
        # 既存のアイテムを取得
        item = await workflow_service.get_by_n_number(payload.get("n_number"))
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow item not found: {payload.get('n_number')}"
            )
        
        # ステータスを更新
        old_status = item.status
        item = await workflow_service.update_status(
            n_number=payload.get("n_number"),
            status=WorkflowStatus.COMPLETED,
            workflow_metadata=payload.get("metadata", {})
        )
        
        # Slack通知を送信
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        await slack_service.send_completion_notification(
            channel=item.slack_channel,
            n_number=item.n_number,
            repository_name=payload.get("repository_name"),
            workflow_metadata=payload.get("metadata", {})
        )
        
        # ログを記録
        log_webhook_event(
            event_type="completion",
            source="techzip",
            n_number=item.n_number,
            success=True,
            repository_name=payload.get("repository_name")
        )
        
        return {
            "status": "success",
            "n_number": item.n_number,
            "message": "Completion notification processed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to process techzip webhook",
            error=str(e),
            n_number=payload.get("n_number")
        )
        
        log_webhook_event(
            event_type="completion",
            source="techzip",
            n_number=payload.get("n_number", "unknown"),
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )