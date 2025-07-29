"""Progress API schemas."""

from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ProgressStatus as WorkflowStatus


class WorkflowItemBase(BaseModel):
    """Base schema for workflow items."""
    
    n_number: str = Field(..., description="N番号")
    book_id: Optional[str] = Field(None, description="書籍ID")
    title: Optional[str] = Field(None, description="タイトル")
    author: Optional[str] = Field(None, description="著者")
    repository_name: Optional[str] = Field(None, description="リポジトリ名")
    slack_channel: Optional[str] = Field(None, description="Slackチャンネル")
    status: WorkflowStatus = Field(..., description="ワークフローステータス")
    assigned_editor: Optional[str] = Field(None, description="担当編集者")
    workflow_metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")


class WorkflowItemCreate(WorkflowItemBase):
    """Schema for creating workflow items."""
    pass


class WorkflowItemUpdate(BaseModel):
    """Schema for updating workflow items."""
    
    book_id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    repository_name: Optional[str] = None
    slack_channel: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    assigned_editor: Optional[str] = None
    workflow_metadata: Optional[Dict[str, Any]] = None


class WorkflowItemResponse(WorkflowItemBase):
    """Schema for workflow item responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for workflow list responses."""
    
    items: list[WorkflowItemResponse]
    total: int
    limit: int
    offset: int


class WorkflowStatusUpdate(BaseModel):
    """Schema for status updates."""
    
    status: WorkflowStatus
    workflow_metadata: Optional[Dict[str, Any]] = None


class EditorAssignment(BaseModel):
    """Schema for editor assignments."""
    
    editor: str


class ProgressResponse(BaseModel):
    """General progress response schema."""
    
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Aliases for compatibility
ProgressListResponse = WorkflowListResponse
ProgressCreate = WorkflowItemCreate
ProgressUpdate = WorkflowItemUpdate
StatusUpdateRequest = WorkflowStatusUpdate
ProgressDetail = WorkflowItemResponse
EditorAssignRequest = EditorAssignment
StatusUpdateResponse = ProgressResponse
EditorAssignResponse = ProgressResponse