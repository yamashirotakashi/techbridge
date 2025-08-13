#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Stages Model - ワークフローステージ管理
N番号統合基盤のための拡張ワークフローモデル
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

class WorkflowStageType(Enum):
    """ワークフローステージタイプ列挙"""
    PROPOSAL_DRAFT = "proposal_draft"    # 企画案書
    PROPOSAL = "proposal"                 # 企画書
    SPECIFICATION = "specification"       # 製品仕様書

class StageStatus(Enum):
    """ステージステータス列挙"""
    NOT_STARTED = "not_started"          # 未開始
    IN_PROGRESS = "in_progress"          # 進行中
    REVIEW = "review"                    # レビュー中
    COMPLETED = "completed"              # 完了
    BLOCKED = "blocked"                  # ブロック中

@dataclass
class WorkflowStageDTO:
    """ワークフローステージ データ転送オブジェクト"""
    
    id: Optional[int]
    n_number: str
    stage_type: WorkflowStageType
    stage_status: StageStatus = StageStatus.NOT_STARTED
    stage_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.stage_data is None:
            self.stage_data = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStageDTO':
        """辞書からDTOを作成"""
        # ステージタイプの安全な変換
        stage_type_value = data.get('stage_type')
        try:
            stage_type = WorkflowStageType(stage_type_value)
        except ValueError:
            # 不明なステージタイプの場合は企画案書にフォールバック
            stage_type = WorkflowStageType.PROPOSAL_DRAFT
        
        # ステージステータスの安全な変換
        stage_status_value = data.get('stage_status', 'not_started')
        try:
            stage_status = StageStatus(stage_status_value)
        except ValueError:
            # 不明なステータスの場合は未開始にフォールバック
            stage_status = StageStatus.NOT_STARTED
            
        return cls(
            id=data.get('id'),
            n_number=data.get('n_number', ''),
            stage_type=stage_type,
            stage_status=stage_status,
            stage_data=data.get('stage_data', {}),
            completed_at=data.get('completed_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """DTOを辞書に変換"""
        return {
            'id': self.id,
            'n_number': self.n_number,
            'stage_type': self.stage_type.value,
            'stage_status': self.stage_status.value,
            'stage_data': self.stage_data,
            'completed_at': self.completed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }