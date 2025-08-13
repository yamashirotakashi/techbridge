#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N Number Integration Repository - N番号統合基盤リポジトリ
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..config.n_number_schema import NNumberDatabaseSchema
from ..models.n_number_master import NNumberMasterDTO
from ..models.workflow_stages import WorkflowStageDTO, WorkflowStageType
from ..models.service_integration import ServiceIntegrationDTO, ServiceType

logger = logging.getLogger(__name__)

class NNumberIntegrationRepository:
    """N番号統合基盤データベースリポジトリ"""
    
    def __init__(self, db_schema: Optional[NNumberDatabaseSchema] = None):
        """
        初期化
        
        Args:
            db_schema: N番号データベーススキーマ（省略時は新規作成）
        """
        if db_schema is None:
            self.db_schema = NNumberDatabaseSchema()
        else:
            self.db_schema = db_schema
        
        logger.info("NNumberIntegrationRepository initialized")
    
    def create_n_number_project(self, n_number: str, title: str) -> bool:
        """
        N番号プロジェクト作成
        
        Args:
            n_number: N番号
            title: プロジェクトタイトル
            
        Returns:
            bool: 作成成功時True
        """
        try:
            with self.db_schema.get_connection() as conn:
                # N番号マスター作成
                conn.execute("""
                    INSERT INTO n_number_master 
                    (n_number, title, current_stage, project_metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    n_number,
                    title,
                    WorkflowStageType.PROPOSAL_DRAFT.value,
                    json.dumps({})
                ))
                
                # 3段階ワークフローステージ初期化
                stages = [
                    WorkflowStageType.PROPOSAL_DRAFT,
                    WorkflowStageType.PROPOSAL,
                    WorkflowStageType.SPECIFICATION
                ]
                
                for stage in stages:
                    conn.execute("""
                        INSERT INTO workflow_stages 
                        (n_number, stage_type, stage_status, stage_data)
                        VALUES (?, ?, ?, ?)
                    """, (
                        n_number,
                        stage.value,
                        'not_started',
                        json.dumps({})
                    ))
                
                conn.commit()
                logger.info(f"N-Number project created: {n_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create N-Number project {n_number}: {e}")
            return False
    
    def get_workflow_stages_by_n_number(self, n_number: str) -> List[WorkflowStageDTO]:
        """
        N番号によるワークフローステージ取得
        
        Args:
            n_number: N番号
            
        Returns:
            List[WorkflowStageDTO]: ワークフローステージ一覧
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM workflow_stages 
                    WHERE n_number = ?
                    ORDER BY 
                        CASE stage_type
                            WHEN 'proposal_draft' THEN 1
                            WHEN 'proposal' THEN 2
                            WHEN 'specification' THEN 3
                        END
                """, (n_number,))
                
                stages = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # JSON文字列をパース
                    if row_dict.get('stage_data'):
                        row_dict['stage_data'] = json.loads(row_dict['stage_data'])
                    
                    stages.append(WorkflowStageDTO.from_dict(row_dict))
                
                return stages
                
        except Exception as e:
            logger.error(f"Failed to get workflow stages for {n_number}: {e}")
            return []
    
    def update_workflow_stage_status(self, n_number: str, stage_type: WorkflowStageType, 
                                   stage_status: str) -> bool:
        """
        ワークフローステージステータス更新
        
        Args:
            n_number: N番号
            stage_type: ステージタイプ
            stage_status: 新しいステージステータス
            
        Returns:
            bool: 更新成功時True
        """
        try:
            with self.db_schema.get_connection() as conn:
                # ステージステータス更新
                cursor = conn.execute("""
                    UPDATE workflow_stages 
                    SET stage_status = ?, updated_at = ?
                    WHERE n_number = ? AND stage_type = ?
                """, (
                    stage_status,
                    datetime.now().isoformat(),
                    n_number,
                    stage_type.value
                ))
                
                # 完了時は現在ステージも更新
                if stage_status == 'completed':
                    conn.execute("""
                        UPDATE n_number_master 
                        SET current_stage = ?, updated_at = ?
                        WHERE n_number = ?
                    """, (
                        stage_type.value,
                        datetime.now().isoformat(),
                        n_number
                    ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update stage status for {n_number}: {e}")
            return False
    
    def get_n_number_project(self, n_number: str) -> Optional[NNumberMasterDTO]:
        """
        N番号プロジェクト取得
        
        Args:
            n_number: N番号
            
        Returns:
            Optional[NNumberMasterDTO]: プロジェクト情報
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM n_number_master WHERE n_number = ?
                """, (n_number,))
                
                row = cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    # JSON文字列をパース
                    if row_dict.get('project_metadata'):
                        row_dict['project_metadata'] = json.loads(row_dict['project_metadata'])
                    
                    return NNumberMasterDTO.from_dict(row_dict)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get N-Number project {n_number}: {e}")
            return None