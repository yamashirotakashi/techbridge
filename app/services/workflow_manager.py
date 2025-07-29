"""Workflow management service."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import workflow as workflow_crud
from app.models.workflow import WorkflowItem
from app.models.enums import ProgressStatus as WorkflowStatus
from app.schemas.progress import WorkflowItemCreate, WorkflowItemUpdate


class WorkflowManager:
    """High-level workflow management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_workflow_by_n_number(self, n_number: str) -> Optional[WorkflowItem]:
        """Get workflow item by N number."""
        return await workflow_crud.get_workflow_item_by_n_number(self.db, n_number)
    
    async def get_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowStatus] = None,
        assigned_editor: Optional[str] = None
    ) -> tuple[List[WorkflowItem], int]:
        """Get workflows with filters."""
        return await workflow_crud.get_workflow_items(
            self.db, skip, limit, status, assigned_editor
        )
    
    async def create_workflow(self, workflow_data: WorkflowItemCreate) -> WorkflowItem:
        """Create new workflow item."""
        return await workflow_crud.create_workflow_item(self.db, workflow_data)
    
    async def update_workflow(
        self,
        workflow_id: int,
        workflow_update: WorkflowItemUpdate
    ) -> Optional[WorkflowItem]:
        """Update workflow item."""
        return await workflow_crud.update_workflow_item(
            self.db, workflow_id, workflow_update
        )
    
    async def update_status(
        self,
        n_number: str,
        status: WorkflowStatus,
        workflow_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowItem]:
        """Update workflow status."""
        return await workflow_crud.update_workflow_status(
            self.db, n_number, status, workflow_metadata
        )
    
    async def assign_editor(self, n_number: str, editor: str) -> Optional[WorkflowItem]:
        """Assign editor to workflow."""
        return await workflow_crud.assign_editor(self.db, n_number, editor)
    
    async def delete_workflow(self, workflow_id: int) -> bool:
        """Delete workflow item."""
        return await workflow_crud.delete_workflow_item(self.db, workflow_id)