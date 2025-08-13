#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N番号統合基盤 GUI統合モジュール
TDD REFACTOR フェーズ - 7,240行PySide6 GUIとの実際の統合

目的:
1. 既存のPublicationRepositoryとN番号統合基盤の統合
2. リアルタイムデータバインディング
3. GUIイベントとN番号ワークフローの連携
"""

import logging
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot
from datetime import datetime

from ..repositories.enhanced_n_number_repository import EnhancedNNumberRepository
from ..repositories.publication_repository import PublicationRepository
from ..models.n_number_master import NNumberMasterDTO
from ..models.workflow_stages import WorkflowStageType
from ..config.n_number_schema import NNumberDatabaseSchema

logger = logging.getLogger(__name__)

class NNumberGUIIntegrator(QObject):
    """N番号統合基盤とGUI統合管理クラス"""
    
    # シグナル定義
    project_created = Signal(str, str)  # n_number, title
    stage_updated = Signal(str, str, str)  # n_number, stage_type, status
    data_synchronized = Signal()  # データ同期完了
    error_occurred = Signal(str)  # エラー発生
    
    def __init__(self, db_path: str):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス
        """
        super().__init__()
        
        # データベース接続
        self.db_schema = NNumberDatabaseSchema(db_path)
        self.n_number_repo = EnhancedNNumberRepository(self.db_schema)
        self.publication_repo = PublicationRepository(db_path)
        
        # 統合データキャッシュ
        self._integrated_data_cache = {}
        
        logger.info(f"NNumberGUIIntegrator initialized with database: {db_path}")
    
    def create_integrated_publication_record(self, n_number: str, title: str, 
                                           additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        統合出版レコード作成
        
        N番号統合基盤とpublicationsテーブル両方にデータを作成
        
        Args:
            n_number: N番号
            title: タイトル
            additional_data: 追加データ（publicationsテーブル用）
            
        Returns:
            bool: 作成成功時True
        """
        try:
            # 1. N番号統合基盤にプロジェクト作成
            success = self.n_number_repo.create_n_number_project_safe(n_number, title)
            if not success:
                logger.error(f"Failed to create N-Number project: {n_number}")
                return False
            
            # 2. publicationsテーブルにも対応レコード作成
            publication_data = {
                'n_number': n_number,
                'title': title,
                'current_status': 'DISCOVERED',  # 初期状態
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 追加データがある場合はマージ
            if additional_data:
                publication_data.update(additional_data)
            
            # PublicationRepositoryを使用してレコード作成
            pub_success = self._create_publication_record(publication_data)
            if not pub_success:
                logger.warning(f"Failed to create publication record for: {n_number}")
                # N番号統合基盤の作成は成功しているので、継続
            
            # キャッシュ更新
            self._update_integrated_cache(n_number)
            
            # GUI シグナル発行
            self.project_created.emit(n_number, title)
            
            logger.info(f"Integrated publication record created: {n_number} - {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create integrated publication record: {e}")
            self.error_occurred.emit(f"統合レコード作成失敗: {str(e)}")
            return False
    
    def _create_publication_record(self, publication_data: Dict[str, Any]) -> bool:
        """
        publicationsテーブルレコード作成
        
        Args:
            publication_data: 出版データ
            
        Returns:
            bool: 作成成功時True
        """
        try:
            # PublicationRepositoryのメソッドを使用
            # 注意: 既存のPublicationRepositoryインターフェースに合わせる必要がある
            
            # 一般的なSQL挿入を実行（実際のPublicationRepositoryのメソッドに置き換える）
            import sqlite3
            
            with sqlite3.connect(self.db_schema.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO publications 
                    (n_number, title, current_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    publication_data.get('n_number'),
                    publication_data.get('title'),
                    publication_data.get('current_status', 'DISCOVERED'),
                    publication_data.get('created_at'),
                    publication_data.get('updated_at')
                ))
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to create publication record: {e}")
            return False
    
    def sync_workflow_stage_update(self, n_number: str, stage_type: WorkflowStageType, 
                                 stage_status: str) -> bool:
        """
        ワークフローステージ更新の同期
        
        N番号統合基盤の更新をGUIにリアルタイム反映
        
        Args:
            n_number: N番号
            stage_type: ステージタイプ
            stage_status: ステージステータス
            
        Returns:
            bool: 更新成功時True
        """
        try:
            # 1. N番号統合基盤のステージ更新
            success = self.n_number_repo.update_workflow_stage_status_safe(
                n_number, stage_type, stage_status
            )
            
            if not success:
                logger.error(f"Failed to update workflow stage: {n_number} {stage_type}")
                return False
            
            # 2. publicationsテーブルのステータス同期
            self._sync_publication_status(n_number, stage_type, stage_status)
            
            # 3. キャッシュ更新
            self._update_integrated_cache(n_number)
            
            # 4. GUI シグナル発行
            self.stage_updated.emit(n_number, stage_type.value, stage_status)
            
            logger.info(f"Workflow stage synchronized: {n_number} {stage_type.value} -> {stage_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync workflow stage update: {e}")
            self.error_occurred.emit(f"ワークフロー同期失敗: {str(e)}")
            return False
    
    def _sync_publication_status(self, n_number: str, stage_type: WorkflowStageType, 
                               stage_status: str) -> bool:
        """
        publicationsテーブルステータス同期
        
        Args:
            n_number: N番号
            stage_type: ステージタイプ
            stage_status: ステージステータス
            
        Returns:
            bool: 同期成功時True
        """
        try:
            # N番号ステージを既存のpublicationsステータスにマッピング
            status_mapping = {
                WorkflowStageType.PROPOSAL_DRAFT: {
                    'not_started': 'DISCOVERED',
                    'in_progress': 'MANUSCRIPT_REQUESTED',
                    'completed': 'MANUSCRIPT_RECEIVED'
                },
                WorkflowStageType.PROPOSAL: {
                    'not_started': 'MANUSCRIPT_RECEIVED',
                    'in_progress': 'FIRST_PROOF',
                    'completed': 'SECOND_PROOF'
                },
                WorkflowStageType.SPECIFICATION: {
                    'not_started': 'SECOND_PROOF',
                    'in_progress': 'SECOND_PROOF',
                    'completed': 'COMPLETED'
                }
            }
            
            # マッピングされたステータスを取得
            mapped_status = status_mapping.get(stage_type, {}).get(stage_status, 'DISCOVERED')
            
            # publicationsテーブル更新
            import sqlite3
            with sqlite3.connect(self.db_schema.db_path) as conn:
                conn.execute("""
                    UPDATE publications 
                    SET current_status = ?, updated_at = ?
                    WHERE n_number = ?
                """, (
                    mapped_status,
                    datetime.now().isoformat(),
                    n_number
                ))
                conn.commit()
                
            logger.info(f"Publication status synchronized: {n_number} -> {mapped_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync publication status: {e}")
            return False
    
    def get_integrated_project_data(self, n_number: str) -> Optional[Dict[str, Any]]:
        """
        統合プロジェクトデータ取得
        
        N番号統合基盤とpublicationsテーブルの情報を統合して返す
        
        Args:
            n_number: N番号
            
        Returns:
            Optional[Dict[str, Any]]: 統合プロジェクトデータ
        """
        try:
            # キャッシュ確認
            if n_number in self._integrated_data_cache:
                return self._integrated_data_cache[n_number]
            
            # N番号統合基盤からデータ取得
            n_number_project = self.n_number_repo.get_n_number_project_cached(n_number)
            if not n_number_project:
                return None
            
            # ワークフローステージ取得
            workflow_stages = self.n_number_repo.get_workflow_stages_by_n_number(n_number)
            
            # publicationsテーブルからデータ取得
            publication_data = self._get_publication_data(n_number)
            
            # 統合データ構築
            integrated_data = {
                'n_number': n_number_project.n_number,
                'title': n_number_project.title,
                'current_stage': n_number_project.current_stage.value,
                'project_metadata': n_number_project.project_metadata,
                'workflow_stages': [stage.to_dict() for stage in workflow_stages],
                'publication_data': publication_data,
                'created_at': n_number_project.created_at,
                'updated_at': n_number_project.updated_at
            }
            
            # キャッシュ保存
            self._integrated_data_cache[n_number] = integrated_data
            
            return integrated_data
            
        except Exception as e:
            logger.error(f"Failed to get integrated project data: {e}")
            return None
    
    def _get_publication_data(self, n_number: str) -> Optional[Dict[str, Any]]:
        """
        publicationsテーブルデータ取得
        
        Args:
            n_number: N番号
            
        Returns:
            Optional[Dict[str, Any]]: 出版データ
        """
        try:
            import sqlite3
            with sqlite3.connect(self.db_schema.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM publications WHERE n_number = ? LIMIT 1
                """, (n_number,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get publication data: {e}")
            return None
    
    def _update_integrated_cache(self, n_number: str):
        """
        統合データキャッシュ更新
        
        Args:
            n_number: N番号
        """
        try:
            # キャッシュから削除（次回取得時に再構築）
            if n_number in self._integrated_data_cache:
                del self._integrated_data_cache[n_number]
                
        except Exception as e:
            logger.error(f"Failed to update integrated cache: {e}")
    
    @Slot()
    def force_data_synchronization(self):
        """
        データ強制同期
        
        全キャッシュクリアとGUI更新
        """
        try:
            # 全キャッシュクリア
            self._integrated_data_cache.clear()
            
            # GUI更新シグナル発行
            self.data_synchronized.emit()
            
            logger.info("Data synchronization completed")
            
        except Exception as e:
            logger.error(f"Failed to force data synchronization: {e}")
            self.error_occurred.emit(f"データ同期失敗: {str(e)}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        パフォーマンス統計情報取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            # N番号統合基盤の統計
            n_number_stats = self.n_number_repo.get_performance_stats()
            
            # キャッシュ統計
            cache_stats = {
                'cache_size': len(self._integrated_data_cache),
                'cached_projects': list(self._integrated_data_cache.keys())
            }
            
            # 統合統計
            integrated_stats = {
                'n_number_stats': n_number_stats,
                'cache_stats': cache_stats,
                'integration_version': '1.0.0',
                'last_sync': datetime.now().isoformat()
            }
            
            return integrated_stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}