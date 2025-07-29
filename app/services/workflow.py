"""ワークフローサービス"""

from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.workflow import WorkflowItem
from app.models.enums import ProgressStatus as WorkflowStatus

logger = structlog.get_logger(__name__)


class WorkflowService:
    """ワークフロー管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_or_update(
        self,
        n_number: str,
        book_id: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        repository_name: Optional[str] = None,
        slack_channel: Optional[str] = None,
        assigned_editor: Optional[str] = None,
        workflow_workflow_metadata: Optional[dict] = None
    ) -> WorkflowItem:
        """ワークフローアイテムを作成または更新"""
        # 既存のアイテムを検索
        result = await self.db.execute(
            select(WorkflowItem).where(WorkflowItem.n_number == n_number)
        )
        item = result.scalar_one_or_none()
        
        if item:
            # 更新
            if book_id is not None:
                item.book_id = book_id
            if title is not None:
                item.title = title
            if author is not None:
                item.author = author
            if status is not None:
                item.status = status
            if repository_name is not None:
                item.repository_name = repository_name
            if slack_channel is not None:
                item.slack_channel = slack_channel
            if assigned_editor is not None:
                item.assigned_editor = assigned_editor
            if workflow_metadata is not None:
                item.workflow_metadata = workflow_metadata
            
            item.updated_at = datetime.utcnow()
            
            logger.info(
                "Updated workflow item",
                n_number=n_number,
                status=status.value if status else None
            )
        else:
            # 新規作成
            item = WorkflowItem(
                n_number=n_number,
                book_id=book_id or "",
                title=title or "",
                author=author or "",
                status=status or WorkflowStatus.DISCOVERED,
                repository_name=repository_name or "",
                slack_channel=slack_channel or "#general",
                assigned_editor=assigned_editor,
                workflow_metadata=workflow_metadata or {}
            )
            self.db.add(item)
            
            logger.info(
                "Created workflow item",
                n_number=n_number,
                status=item.status.value
            )
        
        await self.db.commit()
        await self.db.refresh(item)
        
        return item
    
    async def get_by_n_number(self, n_number: str) -> Optional[WorkflowItem]:
        """N番号でワークフローアイテムを取得"""
        result = await self.db.execute(
            select(WorkflowItem).where(WorkflowItem.n_number == n_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_status(
        self,
        status: WorkflowStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowItem]:
        """ステータスでワークフローアイテムを取得"""
        result = await self.db.execute(
            select(WorkflowItem)
            .where(WorkflowItem.status == status)
            .order_by(WorkflowItem.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_by_editor(
        self,
        editor: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowItem]:
        """編集者でワークフローアイテムを取得"""
        result = await self.db.execute(
            select(WorkflowItem)
            .where(WorkflowItem.assigned_editor == editor)
            .order_by(WorkflowItem.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_multi_with_filters(
        self,
        status: Optional[WorkflowStatus] = None,
        assigned_editor: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[WorkflowItem], int]:
        """フィルタ付きでワークフローアイテムを取得"""
        # 基本クエリ
        query = select(WorkflowItem)
        count_query = select(WorkflowItem)
        
        # フィルタを追加
        conditions = []
        if status is not None:
            conditions.append(WorkflowItem.status == status)
        if assigned_editor is not None:
            conditions.append(WorkflowItem.assigned_editor == assigned_editor)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 総数を取得
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # データを取得
        query = query.order_by(WorkflowItem.updated_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return items, total
    
    async def update_status(
        self,
        n_number: str,
        status: WorkflowStatus,
        workflow_workflow_metadata: Optional[dict] = None
    ) -> Optional[WorkflowItem]:
        """ステータスを更新"""
        item = await self.get_by_n_number(n_number)
        if not item:
            return None
        
        item.status = status
        item.updated_at = datetime.utcnow()
        
        if workflow_metadata:
            if item.workflow_metadata:
                item.workflow_metadata.update(workflow_metadata)
            else:
                item.workflow_metadata = workflow_metadata
        
        await self.db.commit()
        await self.db.refresh(item)
        
        logger.info(
            "Updated workflow status",
            n_number=n_number,
            status=status.value
        )
        
        return item
    
    async def assign_editor(
        self,
        n_number: str,
        editor: str
    ) -> Optional[WorkflowItem]:
        """編集者を割り当て"""
        item = await self.get_by_n_number(n_number)
        if not item:
            return None
        
        item.assigned_editor = editor
        item.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(item)
        
        logger.info(
            "Assigned editor",
            n_number=n_number,
            editor=editor
        )
        
        return item