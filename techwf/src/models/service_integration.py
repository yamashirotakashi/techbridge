#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Integration Model - サービス統合管理
N番号統合基盤のためのサービス統合モデル
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

class ServiceType(Enum):
    """サービスタイプ列挙"""
    PJINIT = "pjinit"                    # プロジェクト初期化サービス
    TECHZIP = "techzip"                  # 技術書作成サービス
    GPT5 = "gpt5"                        # GPT-5 API統合サービス

class IntegrationStatus(Enum):
    """統合ステータス列挙"""
    PENDING = "pending"                   # 実行待ち
    RUNNING = "running"                   # 実行中
    SUCCESS = "success"                   # 成功
    FAILED = "failed"                     # 失敗
    CANCELLED = "cancelled"               # キャンセル

@dataclass
class ServiceIntegrationDTO:
    """サービス統合 データ転送オブジェクト"""
    
    id: Optional[int]
    n_number: str
    service_type: ServiceType
    integration_status: IntegrationStatus = IntegrationStatus.PENDING
    api_request_data: Optional[Dict[str, Any]] = None
    api_response_data: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.api_request_data is None:
            self.api_request_data = {}
        if self.api_response_data is None:
            self.api_response_data = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceIntegrationDTO':
        """辞書からDTOを作成"""
        # サービスタイプの安全な変換
        service_type_value = data.get('service_type')
        try:
            service_type = ServiceType(service_type_value)
        except ValueError:
            # 不明なサービスタイプの場合はPJINITにフォールバック
            service_type = ServiceType.PJINIT
        
        # 統合ステータスの安全な変換
        integration_status_value = data.get('integration_status', 'pending')
        try:
            integration_status = IntegrationStatus(integration_status_value)
        except ValueError:
            # 不明なステータスの場合は実行待ちにフォールバック
            integration_status = IntegrationStatus.PENDING
            
        return cls(
            id=data.get('id'),
            n_number=data.get('n_number', ''),
            service_type=service_type,
            integration_status=integration_status,
            api_request_data=data.get('api_request_data', {}),
            api_response_data=data.get('api_response_data', {}),
            executed_at=data.get('executed_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """DTOを辞書に変換"""
        return {
            'id': self.id,
            'n_number': self.n_number,
            'service_type': self.service_type.value,
            'integration_status': self.integration_status.value,
            'api_request_data': self.api_request_data,
            'api_response_data': self.api_response_data,
            'executed_at': self.executed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }