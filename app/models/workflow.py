"""
TechBridge ワークフローデータモデル
SQLAlchemy 2.0 対応
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, Boolean, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import ProgressStatus, NotificationStatus, EventType, WebhookSource


class WorkflowItem(Base):
    """ワークフローアイテム - メインの進捗管理テーブル"""
    
    __tablename__ = "workflow_items"
    
    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 識別子
    n_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    book_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # リポジトリ・チャンネル情報
    repository_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    slack_channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ステータス情報
    status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus), nullable=False, index=True)
    assigned_editor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # メタデータ（JSON形式で追加情報を格納）
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # リレーション
    status_history: Mapped[list["StatusHistory"]] = relationship(
        "StatusHistory", 
        back_populates="workflow_item",
        cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at.desc()"
    )
    
    notification_history: Mapped[list["NotificationHistory"]] = relationship(
        "NotificationHistory",
        back_populates="workflow_item", 
        cascade="all, delete-orphan",
        order_by="NotificationHistory.sent_at.desc()"
    )
    
    # インデックス
    __table_args__ = (
        Index('ix_workflow_items_status_updated', 'status', 'updated_at'),
        Index('ix_workflow_items_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowItem(n_number='{self.n_number}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'n_number': self.n_number,
            'book_id': self.book_id,
            'repository_name': self.repository_name,
            'slack_channel': self.slack_channel,
            'status': self.status.value,
            'assigned_editor': self.assigned_editor,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata or {}
        }


class StatusHistory(Base):
    """ステータス履歴テーブル"""
    
    __tablename__ = "status_history"
    
    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外部キー
    workflow_item_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_items.id", ondelete="CASCADE"),
        nullable=False
    )
    n_number: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # ステータス情報
    old_status: Mapped[Optional[ProgressStatus]] = mapped_column(Enum(ProgressStatus), nullable=True)
    new_status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus), nullable=False)
    
    # 変更情報
    changed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # 追加情報
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[WebhookSource]] = mapped_column(Enum(WebhookSource), nullable=True)
    
    # リレーション
    workflow_item: Mapped["WorkflowItem"] = relationship("WorkflowItem", back_populates="status_history")
    
    # インデックス
    __table_args__ = (
        Index('ix_status_history_n_number_changed_at', 'n_number', 'changed_at'),
        Index('ix_status_history_changed_at', 'changed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<StatusHistory(n_number='{self.n_number}', {self.old_status} -> {self.new_status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'n_number': self.n_number,
            'old_status': self.old_status.value if self.old_status else None,
            'new_status': self.new_status.value,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat(),
            'comment': self.comment,
            'source': self.source.value if self.source else None
        }


class NotificationHistory(Base):
    """通知履歴テーブル"""
    
    __tablename__ = "notification_history"
    
    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外部キー
    workflow_item_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_items.id", ondelete="CASCADE"),
        nullable=False
    )
    n_number: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # 通知情報
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # ステータス情報
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), 
        nullable=False,
        default=NotificationStatus.PENDING
    )
    
    # タイムスタンプ
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # エラー情報
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Slack情報
    slack_message_ts: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Slackメッセージタイムスタンプ
    
    # リレーション
    workflow_item: Mapped["WorkflowItem"] = relationship("WorkflowItem", back_populates="notification_history")
    
    # インデックス
    __table_args__ = (
        Index('ix_notification_history_n_number_sent_at', 'n_number', 'sent_at'),
        Index('ix_notification_history_status', 'status'),
        Index('ix_notification_history_sent_at', 'sent_at'),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationHistory(n_number='{self.n_number}', channel='{self.channel}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'n_number': self.n_number,
            'channel': self.channel,
            'message': self.message,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat(),
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'slack_message_ts': self.slack_message_ts
        }


class SystemEvent(Base):
    """システムイベントログテーブル"""
    
    __tablename__ = "system_events"
    
    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # イベント情報
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    n_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    
    # イベントデータ
    event_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # タイムスタンプ
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # 追加情報
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # インデックス
    __table_args__ = (
        Index('ix_system_events_type_occurred', 'event_type', 'occurred_at'),
        Index('ix_system_events_n_number_occurred', 'n_number', 'occurred_at'),
        Index('ix_system_events_occurred_at', 'occurred_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemEvent(type='{self.event_type}', n_number='{self.n_number}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'n_number': self.n_number,
            'event_data': self.event_data or {},
            'occurred_at': self.occurred_at.isoformat(),
            'source': self.source,
            'user_id': self.user_id
        }