#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N番号統合基盤 サービスオーケストレーター
TDD REFACTOR フェーズ - PJINIT/TECHZIP/GPT-5統合実装

目的:
1. N番号ワークフローに基づくサービス統合自動実行
2. サービス間の依存関係管理
3. 実際のCRUD操作による統合テスト
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from ..models.n_number_master import NNumberMasterDTO
from ..models.workflow_stages import WorkflowStageType
from ..models.service_integration import ServiceType, ServiceIntegrationDTO, IntegrationStatus
from ..repositories.enhanced_n_number_repository import EnhancedNNumberRepository
from .adapters.pjinit_service_adapter import PJINITServiceAdapter
from .adapters.techzip_service_adapter import TECHZIPServiceAdapter
from .adapters.gpt5_service_adapter import GPT5ServiceAdapter

logger = logging.getLogger(__name__)

class NNumberServiceOrchestrator:
    """N番号統合基盤サービスオーケストレーター"""
    
    def __init__(self, enhanced_repo: EnhancedNNumberRepository):
        """
        初期化
        
        Args:
            enhanced_repo: 強化版N番号統合基盤リポジトリ
        """
        self.enhanced_repo = enhanced_repo
        
        # サービスアダプター初期化
        self.pjinit_adapter = PJINITServiceAdapter()
        self.techzip_adapter = TECHZIPServiceAdapter()
        self.gpt5_adapter = GPT5ServiceAdapter()
        
        # サービス統合実行履歴
        self._integration_history = {}
        
        logger.info("NNumberServiceOrchestrator initialized")
    
    async def execute_stage_workflow(self, n_number: str, stage_type: WorkflowStageType) -> bool:
        """
        ステージワークフロー実行
        
        指定されたステージに応じて適切なサービス統合を実行
        
        Args:
            n_number: N番号
            stage_type: ワークフローステージタイプ
            
        Returns:
            bool: 実行成功時True
        """
        try:
            logger.info(f"Starting stage workflow: {n_number} - {stage_type.value}")
            
            # プロジェクト情報取得
            project = self.enhanced_repo.get_n_number_project_cached(n_number)
            if not project:
                logger.error(f"Project not found: {n_number}")
                return False
            
            # ステージに応じたサービス統合実行
            if stage_type == WorkflowStageType.PROPOSAL_DRAFT:
                return await self._execute_proposal_draft_workflow(project)
            elif stage_type == WorkflowStageType.PROPOSAL:
                return await self._execute_proposal_workflow(project)
            elif stage_type == WorkflowStageType.SPECIFICATION:
                return await self._execute_specification_workflow(project)
            else:
                logger.warning(f"Unknown stage type: {stage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute stage workflow: {e}")
            return False
    
    async def _execute_proposal_draft_workflow(self, project: NNumberMasterDTO) -> bool:
        """
        企画案書段階ワークフロー実行
        
        1. PJINIT: プロジェクト初期化
        2. GPT-5: 企画案書生成支援
        
        Args:
            project: N番号プロジェクト
            
        Returns:
            bool: 実行成功時True
        """
        try:
            n_number = project.n_number
            
            # 1. PJINIT実行 - プロジェクト初期化
            pjinit_request = {
                'n_number': n_number,
                'title': project.title,
                'template_type': 'techbook',
                'output_path': f'/dist/{n_number}',
                'stage': 'proposal_draft'
            }
            
            pjinit_result = await self.pjinit_adapter.execute_integration(pjinit_request)
            if not pjinit_result.get('success', False):
                logger.error(f"PJINIT integration failed: {n_number}")
                return False
            
            # 統合結果記録
            await self._record_service_integration(
                n_number, ServiceType.PJINIT, pjinit_request, pjinit_result
            )
            
            # 2. GPT-5実行 - 企画案書生成支援
            gpt5_request = {
                'n_number': n_number,
                'task_type': 'proposal_draft_generation',
                'input_data': {
                    'title': project.title,
                    'project_metadata': project.project_metadata
                },
                'model': 'gpt-5',
                'parameters': {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            }
            
            gpt5_result = await self.gpt5_adapter.execute_integration(gpt5_request)
            if not gpt5_result.get('success', False):
                logger.warning(f"GPT-5 integration failed: {n_number}")
                # GPT-5は必須ではないので継続
            else:
                # 統合結果記録
                await self._record_service_integration(
                    n_number, ServiceType.GPT5, gpt5_request, gpt5_result
                )
            
            # ステージステータス更新
            self.enhanced_repo.update_workflow_stage_status_safe(
                n_number, WorkflowStageType.PROPOSAL_DRAFT, 'completed'
            )
            
            logger.info(f"Proposal draft workflow completed: {n_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute proposal draft workflow: {e}")
            return False
    
    async def _execute_proposal_workflow(self, project: NNumberMasterDTO) -> bool:
        """
        企画書段階ワークフロー実行
        
        1. GPT-5: 企画書レビューと改善提案
        2. TECHZIP: 技術書構成案生成
        
        Args:
            project: N番号プロジェクト
            
        Returns:
            bool: 実行成功時True
        """
        try:
            n_number = project.n_number
            
            # 1. GPT-5実行 - 企画書レビューと改善提案
            gpt5_request = {
                'n_number': n_number,
                'task_type': 'proposal_review',
                'input_data': {
                    'title': project.title,
                    'current_stage': project.current_stage.value,
                    'project_metadata': project.project_metadata
                },
                'model': 'gpt-5',
                'parameters': {
                    'temperature': 0.5,
                    'max_tokens': 3000
                }
            }
            
            gpt5_result = await self.gpt5_adapter.execute_integration(gpt5_request)
            if gpt5_result.get('success', False):
                await self._record_service_integration(
                    n_number, ServiceType.GPT5, gpt5_request, gpt5_result
                )
            
            # 2. TECHZIP実行 - 技術書構成案生成
            techzip_request = {
                'n_number': n_number,
                'operation': 'generate_structure',
                'input_data': {
                    'title': project.title,
                    'format': 'pdf',
                    'target_pages': 120
                },
                'stage': 'proposal'
            }
            
            techzip_result = await self.techzip_adapter.execute_integration(techzip_request)
            if not techzip_result.get('success', False):
                logger.error(f"TECHZIP integration failed: {n_number}")
                return False
            
            # 統合結果記録
            await self._record_service_integration(
                n_number, ServiceType.TECHZIP, techzip_request, techzip_result
            )
            
            # ステージステータス更新
            self.enhanced_repo.update_workflow_stage_status_safe(
                n_number, WorkflowStageType.PROPOSAL, 'completed'
            )
            
            logger.info(f"Proposal workflow completed: {n_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute proposal workflow: {e}")
            return False
    
    async def _execute_specification_workflow(self, project: NNumberMasterDTO) -> bool:
        """
        製品仕様書段階ワークフロー実行
        
        1. GPT-5: 最終レビューと品質チェック
        2. TECHZIP: 最終成果物生成
        3. PJINIT: プロジェクト完了処理
        
        Args:
            project: N番号プロジェクト
            
        Returns:
            bool: 実行成功時True
        """
        try:
            n_number = project.n_number
            
            # 1. GPT-5実行 - 最終レビューと品質チェック
            gpt5_request = {
                'n_number': n_number,
                'task_type': 'final_quality_review',
                'input_data': {
                    'title': project.title,
                    'project_metadata': project.project_metadata,
                    'workflow_stages': 'specification'
                },
                'model': 'gpt-5',
                'parameters': {
                    'temperature': 0.3,  # 低めの温度で一貫性重視
                    'max_tokens': 4000
                }
            }
            
            gpt5_result = await self.gpt5_adapter.execute_integration(gpt5_request)
            if gpt5_result.get('success', False):
                await self._record_service_integration(
                    n_number, ServiceType.GPT5, gpt5_request, gpt5_result
                )
            
            # 2. TECHZIP実行 - 最終成果物生成
            techzip_request = {
                'n_number': n_number,
                'operation': 'generate_final_output',
                'input_data': {
                    'title': project.title,
                    'format': 'pdf',
                    'output_path': f'/dist/{n_number}/final',
                    'quality': 'production'
                },
                'stage': 'specification'
            }
            
            techzip_result = await self.techzip_adapter.execute_integration(techzip_request)
            if not techzip_result.get('success', False):
                logger.error(f"TECHZIP final integration failed: {n_number}")
                return False
            
            await self._record_service_integration(
                n_number, ServiceType.TECHZIP, techzip_request, techzip_result
            )
            
            # 3. PJINIT実行 - プロジェクト完了処理
            pjinit_request = {
                'n_number': n_number,
                'operation': 'project_completion',
                'output_path': f'/dist/{n_number}',
                'stage': 'specification'
            }
            
            pjinit_result = await self.pjinit_adapter.execute_integration(pjinit_request)
            if pjinit_result.get('success', False):
                await self._record_service_integration(
                    n_number, ServiceType.PJINIT, pjinit_request, pjinit_result
                )
            
            # ステージステータス更新
            self.enhanced_repo.update_workflow_stage_status_safe(
                n_number, WorkflowStageType.SPECIFICATION, 'completed'
            )
            
            logger.info(f"Specification workflow completed: {n_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute specification workflow: {e}")
            return False
    
    async def _record_service_integration(self, n_number: str, service_type: ServiceType,
                                        request_data: Dict[str, Any], 
                                        result_data: Dict[str, Any]):
        """
        サービス統合結果記録
        
        Args:
            n_number: N番号
            service_type: サービスタイプ
            request_data: リクエストデータ
            result_data: 結果データ
        """
        try:
            # データベースに統合履歴を記録
            import sqlite3
            
            with sqlite3.connect(self.enhanced_repo.db_schema.db_path) as conn:
                integration_status = IntegrationStatus.SUCCESS if result_data.get('success', False) else IntegrationStatus.FAILURE
                
                conn.execute("""
                    INSERT INTO service_integrations 
                    (n_number, service_type, integration_status, api_request_data, api_response_data, executed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    n_number,
                    service_type.value,
                    integration_status.value,
                    json.dumps(request_data),
                    json.dumps(result_data),
                    datetime.now().isoformat()
                ))
                conn.commit()
            
            # メモリ履歴にも記録
            if n_number not in self._integration_history:
                self._integration_history[n_number] = []
            
            self._integration_history[n_number].append({
                'service_type': service_type.value,
                'status': integration_status.value,
                'executed_at': datetime.now().isoformat(),
                'request_summary': {
                    'operation': request_data.get('operation', request_data.get('task_type')),
                    'stage': request_data.get('stage')
                }
            })
            
            logger.info(f"Service integration recorded: {n_number} - {service_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to record service integration: {e}")
    
    def get_integration_history(self, n_number: str) -> List[Dict[str, Any]]:
        """
        統合履歴取得
        
        Args:
            n_number: N番号
            
        Returns:
            List[Dict[str, Any]]: 統合履歴一覧
        """
        try:
            # データベースから履歴取得
            import sqlite3
            
            with sqlite3.connect(self.enhanced_repo.db_schema.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM service_integrations 
                    WHERE n_number = ?
                    ORDER BY executed_at DESC
                """, (n_number,))
                
                history = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # JSON文字列をパース
                    if row_dict.get('api_request_data'):
                        try:
                            row_dict['api_request_data'] = json.loads(row_dict['api_request_data'])
                        except json.JSONDecodeError:
                            row_dict['api_request_data'] = {}
                    
                    if row_dict.get('api_response_data'):
                        try:
                            row_dict['api_response_data'] = json.loads(row_dict['api_response_data'])
                        except json.JSONDecodeError:
                            row_dict['api_response_data'] = {}
                    
                    history.append(row_dict)
                
                return history
            
        except Exception as e:
            logger.error(f"Failed to get integration history: {e}")
            return []
    
    async def validate_service_integrations(self, n_number: str) -> Dict[str, Any]:
        """
        サービス統合妥当性検証
        
        Args:
            n_number: N番号
            
        Returns:
            Dict[str, Any]: 検証結果
        """
        try:
            # プロジェクト情報取得
            project = self.enhanced_repo.get_n_number_project_cached(n_number)
            if not project:
                return {'valid': False, 'error': 'Project not found'}
            
            # 統合履歴取得
            history = self.get_integration_history(n_number)
            
            # 各サービスの統合状況確認
            service_status = {
                'pjinit': {'executed': False, 'success': False},
                'techzip': {'executed': False, 'success': False},
                'gpt5': {'executed': False, 'success': False}
            }
            
            for integration in history:
                service = integration.get('service_type')
                status = integration.get('integration_status')
                
                if service in service_status:
                    service_status[service]['executed'] = True
                    if status == IntegrationStatus.SUCCESS.value:
                        service_status[service]['success'] = True
            
            # 妥当性判定
            validation_result = {
                'valid': True,
                'project': {
                    'n_number': project.n_number,
                    'title': project.title,
                    'current_stage': project.current_stage.value
                },
                'service_status': service_status,
                'total_integrations': len(history),
                'validation_timestamp': datetime.now().isoformat()
            }
            
            # 必須サービスチェック（プロジェクトの段階に応じて）
            if project.current_stage == WorkflowStageType.SPECIFICATION:
                # 完了段階では全サービスが実行されているべき
                for service, status in service_status.items():
                    if service != 'gpt5' and not status['executed']:  # GPT-5は必須ではない
                        validation_result['valid'] = False
                        validation_result['missing_services'] = validation_result.get('missing_services', [])
                        validation_result['missing_services'].append(service)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate service integrations: {e}")
            return {'valid': False, 'error': str(e)}