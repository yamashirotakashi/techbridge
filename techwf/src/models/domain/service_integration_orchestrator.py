#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Integration Orchestrator - サービス統合オーケストレーター
複数のサービス（PJINIT/TECHZIP/GPT-5）を協調制御するドメインサービス
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from ..service_integration import ServiceType


@dataclass
class ServiceResult:
    """サービス実行結果"""
    service_type: ServiceType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    executed_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationResult:
    """統合実行結果"""
    success: bool = False
    service_results: Dict[ServiceType, ServiceResult] = field(default_factory=dict)
    integration_id: str = ""
    executed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.integration_id:
            self.integration_id = f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@dataclass 
class IntegrationHistoryEntry:
    """統合履歴エントリ"""
    integration_id: str
    n_number: str
    services_used: List[ServiceType]
    result: IntegrationResult
    timestamp: datetime = field(default_factory=datetime.now)


class ServiceIntegrationOrchestrator:
    """
    サービス統合オーケストレーター
    
    複数のサービス呼び出しを協調制御し、
    エラー処理やロールバックを管理する
    """
    
    def __init__(self):
        self._integration_history: List[IntegrationHistoryEntry] = []
    
    def execute_integration_workflow(
        self,
        n_number: str,
        services: List[ServiceType],
        integration_data: Dict[str, Any]
    ) -> IntegrationResult:
        """
        統合ワークフローの実行
        
        Args:
            n_number: 対象N番号
            services: 実行するサービスリスト
            integration_data: 統合データ
            
        Returns:
            IntegrationResult: 統合結果
        """
        result = IntegrationResult()
        
        try:
            # サービスを順序実行
            for service_type in services:
                service_result = self._execute_service(
                    service_type, n_number, integration_data
                )
                result.service_results[service_type] = service_result
                
                # 1つでも失敗したら全体を失敗とする（現在の簡単な実装）
                if not service_result.success:
                    result.success = False
                    break
            else:
                # 全て成功
                result.success = True
            
            # 履歴に記録
            history_entry = IntegrationHistoryEntry(
                integration_id=result.integration_id,
                n_number=n_number,
                services_used=services,
                result=result
            )
            self._integration_history.append(history_entry)
            
        except Exception as e:
            result.success = False
            # エラーハンドリング（簡略化）
            
        return result
    
    def get_integration_history(self, n_number: Optional[str] = None) -> List[IntegrationHistoryEntry]:
        """
        統合履歴の取得
        
        Args:
            n_number: 対象N番号（Noneの場合は全て）
            
        Returns:
            List[IntegrationHistoryEntry]: 統合履歴リスト
        """
        if n_number is None:
            return self._integration_history.copy()
        
        return [
            entry for entry in self._integration_history
            if entry.n_number == n_number
        ]
    
    def _execute_service(
        self,
        service_type: ServiceType,
        n_number: str,
        integration_data: Dict[str, Any]
    ) -> ServiceResult:
        """
        個別サービスの実行（モック実装）
        
        Args:
            service_type: サービスタイプ
            n_number: N番号
            integration_data: 統合データ
            
        Returns:
            ServiceResult: サービス実行結果
        """
        # GREEN段階なので、常に成功する最小実装
        return ServiceResult(
            service_type=service_type,
            success=True,
            data={
                "n_number": n_number,
                "service": service_type.value,
                "message": f"{service_type.value} executed successfully"
            }
        )