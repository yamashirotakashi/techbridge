#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N Number Master Model - N番号マスター管理
N番号統合基盤の中核となるマスターモデル
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from .workflow_stages import WorkflowStageType

@dataclass
class NNumberMasterDTO:
    """N番号マスター データ転送オブジェクト"""
    
    n_number: str                                    # N番号 (主キー)
    title: str                                       # タイトル
    current_stage: WorkflowStageType                 # 現在のワークフローステージ
    project_metadata: Optional[Dict[str, Any]] = None # プロジェクトメタデータ
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.project_metadata is None:
            self.project_metadata = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NNumberMasterDTO':
        """辞書からDTOを作成"""
        # 現在ステージの安全な変換
        current_stage_value = data.get('current_stage', 'proposal_draft')
        try:
            current_stage = WorkflowStageType(current_stage_value)
        except ValueError:
            # 不明なステージの場合は企画案書にフォールバック
            current_stage = WorkflowStageType.PROPOSAL_DRAFT
            
        return cls(
            n_number=data.get('n_number', ''),
            title=data.get('title', ''),
            current_stage=current_stage,
            project_metadata=data.get('project_metadata', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """DTOを辞書に変換"""
        return {
            'n_number': self.n_number,
            'title': self.title,
            'current_stage': self.current_stage.value,
            'project_metadata': self.project_metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }