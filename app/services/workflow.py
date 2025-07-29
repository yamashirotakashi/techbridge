"""Workflow management service."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowItem, WorkflowStatus
from app.services.google_sheets import GoogleSheetsService
from app.services.slack import SlackService

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow items."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sheets_service = GoogleSheetsService()
        
    async def get_by_n_number(self, n_number: str) -> Optional[WorkflowItem]:
        """Get workflow item by N-number."""
        result = await self.db.execute(
            select(WorkflowItem).where(WorkflowItem.n_number == n_number)
        )
        return result.scalar_one_or_none()

    async def get_by_book_id(self, book_id: str) -> Optional[WorkflowItem]:
        """Get workflow item by book ID."""
        result = await self.db.execute(
            select(WorkflowItem).where(WorkflowItem.book_id == book_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        n_number: str,
        book_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowItem:
        """Create or update workflow item."""
        workflow = await self.get_by_n_number(n_number)
        
        if workflow:
            # Update existing
            if book_id:
                workflow.book_id = book_id
            if status:
                workflow.status = status
            if metadata:
                workflow.metadata.update(metadata)
        else:
            # Create new
            workflow = WorkflowItem(
                n_number=n_number,
                book_id=book_id,
                status=status or WorkflowStatus.DISCOVERED,
                metadata=metadata or {},
            )
            self.db.add(workflow)

        # Try to resolve Slack channel from Google Sheets
        if not workflow.slack_channel:
            channel = await self.sheets_service.get_slack_channel(n_number)
            if channel:
                workflow.slack_channel = channel

        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow

    async def update_status_from_tech(
        self,
        book_id: str,
        n_number: str,
        status: WorkflowStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowItem:
        """Update workflow status from tech webhook."""
        logger.info(
            f"Updating status from tech: book_id={book_id}, "
            f"n_number={n_number}, status={status}"
        )
        
        # Create or update workflow
        workflow = await self.create_or_update(
            n_number=n_number,
            book_id=book_id,
            status=status,
            metadata=metadata,
        )
        
        # Send Slack notification if channel is set
        if workflow.slack_channel:
            slack_service = SlackService()
            await slack_service.send_status_update(
                channel=workflow.slack_channel,
                n_number=n_number,
                old_status=None,  # TODO: Track previous status
                new_status=status,
                metadata=metadata,
            )
        
        return workflow

    async def mark_completed_from_techzip(
        self,
        n_number: str,
        repository_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowItem:
        """Mark workflow as completed from techzip."""
        logger.info(
            f"Marking completed from techzip: n_number={n_number}, "
            f"repository={repository_name}"
        )
        
        workflow = await self.get_by_n_number(n_number)
        if not workflow:
            # Create new workflow if doesn't exist
            workflow = WorkflowItem(
                n_number=n_number,
                repository_name=repository_name,
                status=WorkflowStatus.COMPLETED,
                metadata=metadata or {},
            )
            self.db.add(workflow)
        else:
            workflow.repository_name = repository_name
            workflow.status = WorkflowStatus.COMPLETED
            if metadata:
                workflow.metadata.update(metadata)
        
        await self.db.commit()
        await self.db.refresh(workflow)
        
        # Send Slack notification
        if workflow.slack_channel:
            slack_service = SlackService()
            await slack_service.send_completion_notification(
                channel=workflow.slack_channel,
                n_number=n_number,
                repository_name=repository_name,
                metadata=metadata,
            )
        
        return workflow

    async def update_status_manual(
        self,
        n_number: str,
        status: WorkflowStatus,
        updated_by: str,
    ) -> Optional[WorkflowItem]:
        """Manually update workflow status."""
        workflow = await self.get_by_n_number(n_number)
        if not workflow:
            return None
        
        old_status = workflow.status
        workflow.status = status
        workflow.metadata["last_updated_by"] = updated_by
        
        await self.db.commit()
        await self.db.refresh(workflow)
        
        logger.info(
            f"Manual status update: n_number={n_number}, "
            f"old_status={old_status}, new_status={status}, "
            f"updated_by={updated_by}"
        )
        
        return workflow

    async def list_by_status(
        self,
        status: WorkflowStatus,
        limit: int = 100,
    ) -> List[WorkflowItem]:
        """List workflow items by status."""
        result = await self.db.execute(
            select(WorkflowItem)
            .where(WorkflowItem.status == status)
            .order_by(WorkflowItem.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())