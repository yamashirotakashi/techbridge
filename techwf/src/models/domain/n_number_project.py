#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N Number Project Domain Model - N番号プロジェクトドメインモデル
ドメイン駆動設計によるコアビジネスロジック実装
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..workflow_stages import WorkflowStageType, StageStatus


@dataclass
class NNumberProject:
    """
    N番号プロジェクト ドメインモデル
    
    ビジネスルール:
    1. N番号は'N'で始まり6桁の数字が続く形式のみ許可
    2. タイトルは2文字以上100文字以内
    3. 作成時は必ず企画案書(PROPOSAL_DRAFT)ステージから開始
    """
    
    n_number: str
    title: str
    current_stage: WorkflowStageType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, n_number: str, title: str, creator: str) -> 'NNumberProject':
        """
        N番号プロジェクト作成ファクトリメソッド
        
        Args:
            n_number: N番号（N + 5桁数字形式）
            title: プロジェクトタイトル
            creator: 作成者
            
        Returns:
            NNumberProject: 作成されたプロジェクト
            
        Raises:
            ValueError: ビジネスルール違反時
        """
        # N番号形式検証
        if not cls._validate_n_number_format(n_number):
            raise ValueError(f"N番号の形式が不正です: {n_number}")
        
        # タイトル検証
        if not cls._validate_title(title):
            raise ValueError(f"タイトルが不正です: {title}")
        
        # デフォルトメタデータ設定
        default_metadata = {
            "creator": creator,
            "created_timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "project_type": "standard"
        }
        
        return cls(
            n_number=n_number,
            title=title,
            current_stage=WorkflowStageType.PROPOSAL_DRAFT,
            metadata=default_metadata
        )
    
    def transition_to_stage(self, target_stage: WorkflowStageType, completed_by: Optional[str] = None) -> bool:
        """
        ワークフローステージ遷移
        
        Args:
            target_stage: 遷移先ステージ
            completed_by: 完了者
            
        Returns:
            bool: 遷移成功可否
            
        Raises:
            ValueError: 不正な遷移時
        """
        if not self._is_valid_transition(self.current_stage, target_stage):
            raise ValueError(f"不正なステージ遷移: {self.current_stage.value} → {target_stage.value}")
        
        # 遷移実行
        self.current_stage = target_stage
        self.updated_at = datetime.now()
        
        # メタデータ更新
        if completed_by:
            self.metadata[f"completed_by_{target_stage.value}"] = completed_by
            self.metadata[f"completed_at_{target_stage.value}"] = datetime.now().isoformat()
        
        return True
    
    def update_title(self, new_title: str) -> None:
        """
        タイトル更新
        
        Args:
            new_title: 新しいタイトル
            
        Raises:
            ValueError: タイトルが不正時
        """
        if not self._validate_title(new_title):
            raise ValueError(f"タイトルが不正です: {new_title}")
        
        self.title = new_title
        self.updated_at = datetime.now()
    
    @staticmethod
    def _validate_n_number_format(n_number: str) -> bool:
        """N番号形式検証"""
        pattern = r'^N\d{5}$'
        return bool(re.match(pattern, n_number))
    
    @staticmethod
    def _validate_title(title: str) -> bool:
        """タイトル検証"""
        return len(title.strip()) >= 2 and len(title) <= 100
    
    def _is_valid_transition(self, current: WorkflowStageType, target: WorkflowStageType) -> bool:
        """
        ステージ遷移の妥当性検証
        
        許可される遷移:
        - PROPOSAL_DRAFT → PROPOSAL
        - PROPOSAL → SPECIFICATION
        """
        valid_transitions = {
            WorkflowStageType.PROPOSAL_DRAFT: [WorkflowStageType.PROPOSAL],
            WorkflowStageType.PROPOSAL: [WorkflowStageType.SPECIFICATION],
            WorkflowStageType.SPECIFICATION: []  # 最終段階
        }
        
        return target in valid_transitions.get(current, [])