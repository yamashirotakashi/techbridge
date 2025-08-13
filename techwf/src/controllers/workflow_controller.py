#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Controller - ワークフローロジック制御
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from ..repositories.publication_repository import PublicationRepository
from ..models.publication_workflow import PublicationWorkflowDTO, WorkflowStatus

logger = logging.getLogger(__name__)

class WorkflowController:
    """ワークフロー制御クラス"""
    
    def __init__(self, 
                 repository: PublicationRepository,
                 config_service: Optional[Any] = None,
                 sheets_service: Optional[Any] = None,
                 slack_service: Optional[Any] = None,
                 progress_callback: Optional[Callable] = None):
        """
        初期化
        
        Args:
            repository: データベースリポジトリ
            config_service: 設定サービス
            sheets_service: Google Sheetsサービス
            slack_service: Slackサービス
            progress_callback: 進捗コールバック
        """
        self.repository = repository
        self.config_service = config_service
        self.sheets_service = sheets_service
        self.slack_service = slack_service
        self.progress_callback = progress_callback
        
    def get_all_workflows(self) -> List[PublicationWorkflowDTO]:
        """全ワークフローを取得"""
        try:
            data = self.repository.get_all_workflows()
            return [PublicationWorkflowDTO.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []
    
    def get_workflow_by_n_number(self, n_number: str) -> Optional[PublicationWorkflowDTO]:
        """N番号でワークフローを取得"""
        try:
            data = self.repository.get_workflow_by_n_number(n_number)
            return PublicationWorkflowDTO.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get workflow {n_number}: {e}")
            return None
    
    def create_or_update_workflow(self, workflow: PublicationWorkflowDTO) -> bool:
        """ワークフローの作成または更新"""
        try:
            return self.repository.create_or_update_workflow(workflow.to_dict())
        except Exception as e:
            logger.error(f"Failed to create/update workflow: {e}")
            return False
    
    def update_workflow_status(self, n_number: str, status: WorkflowStatus) -> bool:
        """ワークフローステータスの更新"""
        try:
            return self.repository.update_workflow_status(n_number, status.value)
        except Exception as e:
            logger.error(f"Failed to update status for {n_number}: {e}")
            return False
    
    def sync_from_sheets(self) -> int:
        """Google Sheetsからデータを同期"""
        if not self.sheets_service:
            logger.warning("Sheets service not available")
            return 0
        
        try:
            # Google Sheetsからデータを取得（スタブ実装）
            logger.info("Syncing from Google Sheets...")
            if self.progress_callback:
                self.progress_callback("Google Sheetsから同期中...", 50)
            
            # 実際の実装ではsheets_serviceを使用
            count = 0
            
            if self.progress_callback:
                self.progress_callback(f"{count}件を同期完了", 100)
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync from sheets: {e}")
            return 0
    
    def sync_to_sheets(self) -> int:
        """Google Sheetsにデータを同期"""
        if not self.sheets_service:
            logger.warning("Sheets service not available")
            return 0
        
        try:
            # Google Sheetsにデータを転送（スタブ実装）
            logger.info("Syncing to Google Sheets...")
            if self.progress_callback:
                self.progress_callback("Google Sheetsに転送中...", 50)
            
            workflows = self.get_all_workflows()
            count = len(workflows)
            
            if self.progress_callback:
                self.progress_callback(f"{count}件を転送完了", 100)
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to sync to sheets: {e}")
            return 0
    
    def post_to_slack(self, n_number: str, message: str) -> bool:
        """Slackにメッセージを投稿"""
        if not self.slack_service:
            logger.warning("Slack service not available")
            return False
        
        try:
            # Slackにメッセージを投稿（スタブ実装）
            logger.info(f"Posting to Slack for {n_number}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            return False