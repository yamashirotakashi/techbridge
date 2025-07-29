"""
TechBridge 進捗管理API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import ProgressStatus
from app.schemas.progress import (
    ProgressResponse,
    ProgressListResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
    WorkflowItemResponse
)
from app.crud import workflow as workflow_crud
from app.services.workflow_manager import WorkflowManager

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/{n_number}", response_model=ProgressResponse)
async def get_progress(
    n_number: str,
    db: AsyncSession = Depends(get_db)
) -> ProgressResponse:
    """
    指定されたN番号の進捗情報を取得
    
    Args:
        n_number: N番号（例: N02345）
        db: データベースセッション
        
    Returns:
        進捗情報
        
    Raises:
        HTTPException: N番号が見つからない場合（404）
    """
    logger.info("Getting progress", n_number=n_number)
    
    # N番号の形式チェック
    if not n_number.upper().startswith('N'):
        raise ValidationError("N番号は'N'で始まる必要があります", field="n_number")
    
    # 正規化
    n_number = n_number.upper()
    
    # データベースから取得
    workflow_item = await workflow_crud.get_workflow_item_by_n_number(db, n_number)
    if not workflow_item:
        raise NotFoundError("WorkflowItem", n_number)
    
    logger.info("Progress retrieved successfully", n_number=n_number, status=workflow_item.status)
    
    return WorkflowItemResponse.model_validate(workflow_item)


@router.get("/", response_model=ProgressListResponse)
async def list_progress(
    status: Optional[ProgressStatus] = Query(None, description="ステータスでフィルタ"),
    assigned_editor: Optional[str] = Query(None, description="担当編集者でフィルタ"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数制限"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_db)
) -> ProgressListResponse:
    """
    進捗情報のリストを取得
    
    Args:
        status: フィルタするステータス
        assigned_editor: フィルタする担当編集者
        limit: 取得件数制限
        offset: オフセット
        db: データベースセッション
        
    Returns:
        進捗情報のリスト
    """
    logger.info(
        "Listing progress",
        status=status,
        assigned_editor=assigned_editor,
        limit=limit,
        offset=offset
    )
    
    # データベースから取得
    workflow_items, total = await workflow_crud.get_multi_with_filters(
        db,
        skip=offset,
        limit=limit,
        status=status,
        assigned_editor=assigned_editor
    )
    
    # レスポンス形式に変換
    items = [WorkflowItemResponse.model_validate(item) for item in workflow_items]
    
    logger.info("Progress list retrieved", count=len(items), total=total)
    
    return ProgressListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/{n_number}/update", response_model=StatusUpdateResponse)
async def update_status(
    n_number: str,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> StatusUpdateResponse:
    """
    指定されたN番号のステータスを更新
    
    Args:
        n_number: N番号
        request: ステータス更新リクエスト
        db: データベースセッション
        
    Returns:
        更新結果
        
    Raises:
        HTTPException: N番号が見つからない場合、または無効な遷移の場合
    """
    logger.info(
        "Updating status",
        n_number=n_number,
        new_status=request.status,
        updated_by=request.updated_by
    )
    
    # N番号の形式チェック
    if not n_number.upper().startswith('N'):
        raise ValidationError("N番号は'N'で始まる必要があります", field="n_number")
    
    # 正規化
    n_number = n_number.upper()
    
    # 既存のワークフローアイテムを取得
    workflow_item = await workflow_crud.get_workflow_item_by_n_number(db, n_number)
    if not workflow_item:
        raise NotFoundError("WorkflowItem", n_number)
    
    # ステータス遷移の妥当性チェック
    if not workflow_item.status.can_transition_to(request.status):
        raise ValidationError(
            f"無効なステータス遷移: {workflow_item.status} -> {request.status}",
            field="status"
        )
    
    # ワークフローマネージャーを使用して更新
    workflow_manager = WorkflowManager()
    
    try:
        updated_item = await workflow_manager.update_status(
            n_number=n_number,
            new_status=request.status,
            updated_by=request.updated_by or current_user.get("sub", "unknown"),
            comment=request.comment,
            db=db
        )
        
        logger.info(
            "Status updated successfully",
            n_number=n_number,
            old_status=workflow_item.status,
            new_status=request.status
        )
        
        return StatusUpdateResponse(
            n_number=n_number,
            old_status=workflow_item.status,
            new_status=request.status,
            message="ステータスを正常に更新しました"
        )
        
    except Exception as e:
        logger.error("Status update failed", n_number=n_number, error=str(e))
        raise HTTPException(status_code=500, detail=f"ステータス更新に失敗しました: {str(e)}")


@router.get("/{n_number}/history")
async def get_status_history(
    n_number: str,
    limit: int = Query(50, ge=1, le=100, description="取得件数制限"),
    db: AsyncSession = Depends(get_db)
):
    """
    指定されたN番号のステータス履歴を取得
    
    Args:
        n_number: N番号
        limit: 取得件数制限
        db: データベースセッション
        
    Returns:
        ステータス履歴
    """
    logger.info("Getting status history", n_number=n_number, limit=limit)
    
    # N番号の形式チェック
    if not n_number.upper().startswith('N'):
        raise ValidationError("N番号は'N'で始まる必要があります", field="n_number")
    
    # 正規化
    n_number = n_number.upper()
    
    # ワークフローアイテムの存在確認
    workflow_item = await workflow_crud.get_workflow_item_by_n_number(db, n_number)
    if not workflow_item:
        raise NotFoundError("WorkflowItem", n_number)
    
    # ステータス履歴取得
    history = await workflow_crud.get_status_history(db, n_number, limit)
    
    logger.info("Status history retrieved", n_number=n_number, count=len(history))
    
    return {
        "n_number": n_number,
        "history": [item.to_dict() for item in history]
    }


@router.get("/{n_number}/notifications")
async def get_notification_history(
    n_number: str,
    limit: int = Query(50, ge=1, le=100, description="取得件数制限"),
    db: AsyncSession = Depends(get_db)
):
    """
    指定されたN番号の通知履歴を取得
    
    Args:
        n_number: N番号
        limit: 取得件数制限
        db: データベースセッション
        
    Returns:
        通知履歴
    """
    logger.info("Getting notification history", n_number=n_number, limit=limit)
    
    # N番号の形式チェック
    if not n_number.upper().startswith('N'):
        raise ValidationError("N番号は'N'で始まる必要があります", field="n_number")
    
    # 正規化
    n_number = n_number.upper()
    
    # ワークフローアイテムの存在確認
    workflow_item = await workflow_crud.get_workflow_item_by_n_number(db, n_number)
    if not workflow_item:
        raise NotFoundError("WorkflowItem", n_number)
    
    # 通知履歴取得
    notifications = await workflow_crud.get_notification_history(db, n_number, limit)
    
    logger.info("Notification history retrieved", n_number=n_number, count=len(notifications))
    
    return {
        "n_number": n_number,
        "notifications": [item.to_dict() for item in notifications]
    }