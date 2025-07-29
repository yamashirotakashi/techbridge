"""Workflow data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Import WorkflowStatus from enums module
from app.models.enums import ProgressStatus as WorkflowStatus


class WorkflowItem(Base):
    """Workflow item model."""
    
    __tablename__ = "workflow_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    n_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    book_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    author: Mapped[Optional[str]] = mapped_column(String(100))
    repository_name: Mapped[Optional[str]] = mapped_column(String(100))
    slack_channel: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus),
        default=WorkflowStatus.DISCOVERED,
        index=True,
    )
    assigned_editor: Mapped[Optional[str]] = mapped_column(String(50))
    workflow_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<WorkflowItem(n_number={self.n_number}, status={self.status})>"