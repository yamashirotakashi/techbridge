"""Webhook schemas."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class TechWebhookPayload(BaseModel):
    """Tech webhook payload schema."""
    
    event: str = Field(..., description="イベント種別")
    n_number: str = Field(..., description="N番号")
    book_id: Optional[str] = Field(None, description="書籍ID")
    title: Optional[str] = Field(None, description="タイトル")
    author: Optional[str] = Field(None, description="著者")
    status: str = Field(..., description="ステータス")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")


class TechzipWebhookPayload(BaseModel):
    """Techzip webhook payload schema."""
    
    event: str = Field(..., description="イベント種別")
    n_number: str = Field(..., description="N番号")
    repository_name: str = Field(..., description="リポジトリ名")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")


class WebhookResponse(BaseModel):
    """Webhook response schema."""
    
    status: str
    n_number: str
    message: str