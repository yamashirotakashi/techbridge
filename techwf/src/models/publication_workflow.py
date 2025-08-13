#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publication Workflow DTO - データ転送オブジェクト
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class WorkflowStatus(Enum):
    """ワークフローステータス列挙"""
    DISCOVERED = "discovered"
    PURCHASED = "purchased"
    MANUSCRIPT_REQUESTED = "原稿依頼"
    MANUSCRIPT_RECEIVED = "manuscript_received"
    FIRST_PROOF = "初校"
    SECOND_PROOF = "再校"
    COMPLETED = "完成"

@dataclass
class PublicationWorkflowDTO:
    """出版ワークフロー データ転送オブジェクト"""
    
    n_number: str
    title: str
    author: str
    status: WorkflowStatus = WorkflowStatus.DISCOVERED
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PublicationWorkflowDTO':
        """辞書からDTOを作成"""
        # ステータス値の安全な変換
        status_value = data.get('status', 'discovered')
        try:
            status = WorkflowStatus(status_value)
        except ValueError:
            # 不明なステータスの場合はDISCOVEREDにフォールバック
            status = WorkflowStatus.DISCOVERED
            
        return cls(
            n_number=data.get('n_number', ''),
            title=data.get('title', ''),
            author=data.get('author', ''),
            status=status,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """DTOを辞書に変換"""
        return {
            'n_number': self.n_number,
            'title': self.title,
            'author': self.author,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }