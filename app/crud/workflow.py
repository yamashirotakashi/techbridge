"""Workflow CRUD operations."""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowItem
from app.models.enums import ProgressStatus as WorkflowStatus
from app.schemas.progress import WorkflowItemCreate, WorkflowItemUpdate


async def get_workflow_item(
    db: AsyncSession, 
    workflow_id: int
) -> Optional[WorkflowItem]:
    """Get workflow item by ID."""
    result = await db.execute(
        select(WorkflowItem).where(WorkflowItem.id == workflow_id)
    )
    return result.scalar_one_or_none()


async def get_workflow_item_by_n_number(
    db: AsyncSession, 
    n_number: str
) -> Optional[WorkflowItem]:
    """Get workflow item by N number."""
    result = await db.execute(
        select(WorkflowItem).where(WorkflowItem.n_number == n_number)
    )
    return result.scalar_one_or_none()


async def get_workflow_items(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[WorkflowStatus] = None,
    assigned_editor: Optional[str] = None
) -> Tuple[List[WorkflowItem], int]:
    """Get workflow items with filters."""
    # Build query
    query = select(WorkflowItem)
    count_query = select(WorkflowItem)
    
    # Apply filters
    conditions = []
    if status is not None:
        conditions.append(WorkflowItem.status == status)
    if assigned_editor is not None:
        conditions.append(WorkflowItem.assigned_editor == assigned_editor)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    # Get items with pagination
    query = query.order_by(WorkflowItem.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items, total


async def create_workflow_item(
    db: AsyncSession, 
    workflow: WorkflowItemCreate
) -> WorkflowItem:
    """Create new workflow item."""
    db_workflow = WorkflowItem(**workflow.model_dump())
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


async def update_workflow_item(
    db: AsyncSession,
    workflow_id: int,
    workflow_update: WorkflowItemUpdate
) -> Optional[WorkflowItem]:
    """Update workflow item."""
    db_workflow = await get_workflow_item(db, workflow_id)
    if not db_workflow:
        return None
    
    update_data = workflow_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_workflow, field, value)
    
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


async def update_workflow_status(
    db: AsyncSession,
    n_number: str,
    status: WorkflowStatus,
    workflow_metadata: Optional[Dict[str, Any]] = None
) -> Optional[WorkflowItem]:
    """Update workflow status by N number."""
    db_workflow = await get_workflow_item_by_n_number(db, n_number)
    if not db_workflow:
        return None
    
    db_workflow.status = status
    if workflow_metadata:
        if db_workflow.workflow_metadata:
            db_workflow.workflow_metadata.update(workflow_metadata)
        else:
            db_workflow.workflow_metadata = workflow_metadata
    
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


async def assign_editor(
    db: AsyncSession,
    n_number: str,
    editor: str
) -> Optional[WorkflowItem]:
    """Assign editor to workflow item."""
    db_workflow = await get_workflow_item_by_n_number(db, n_number)
    if not db_workflow:
        return None
    
    db_workflow.assigned_editor = editor
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


async def get_multi_with_filters(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[WorkflowStatus] = None,
    assigned_editor: Optional[str] = None
) -> Tuple[List[WorkflowItem], int]:
    """Get workflow items with filters (alias for get_workflow_items)."""
    return await get_workflow_items(db, skip, limit, status, assigned_editor)


async def delete_workflow_item(
    db: AsyncSession, 
    workflow_id: int
) -> bool:
    """Delete workflow item."""
    db_workflow = await get_workflow_item(db, workflow_id)
    if not db_workflow:
        return False
    
    await db.delete(db_workflow)
    await db.commit()
    return True