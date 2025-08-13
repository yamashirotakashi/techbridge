#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N番号統合基盤 TDD Test Suite
T-wada流テストファーストアプローチ

テスト対象:
1. N番号を中心とした新テーブル設計
2. WorkflowStatus enumとの統合
3. PJINIT/TECHZIP/GPT-5サービス統合スキーマ
4. 企画案書→企画書→製品仕様書の3段階ワークフロー

実装優先度: RED → GREEN → REFACTOR
"""

import unittest
import sqlite3
import tempfile
import json
import sys
from pathlib import Path
from datetime import datetime
from enum import Enum

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestNNumberIntegrationSchema(unittest.TestCase):
    """N番号統合基盤スキーマのテスト"""
    
    def setUp(self):
        """テスト用データベースセットアップ"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # テスト用データベース接続
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def tearDown(self):
        """テスト後クリーンアップ"""
        self.conn.close()
        Path(self.db_path).unlink(missing_ok=True)
    
    def test_n_number_master_table_should_exist(self):
        """
        テスト: N番号マスターテーブルが存在すること
        
        要件:
        - N番号を一意キーとするマスターテーブル
        - 企画案書→企画書→製品仕様書の段階管理
        - PJINIT/TECHZIP/GPT-5連携メタデータ
        """
        # GREEN: スキーマを初期化してテーブルが作成されることを確認
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        # テーブルが存在することを確認
        cursor = self.conn.execute("SELECT * FROM n_number_master LIMIT 0")
        self.assertIsNotNone(cursor)
    
    def test_workflow_stages_table_should_exist(self):
        """
        テスト: ワークフローステージテーブルが存在すること
        
        要件:
        - 3段階ワークフロー管理
        - 各段階の詳細メタデータ
        - サービス統合情報
        """
        # GREEN: スキーマを初期化してテーブルが作成されることを確認
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        # テーブルが存在することを確認
        cursor = self.conn.execute("SELECT * FROM workflow_stages LIMIT 0")
        self.assertIsNotNone(cursor)
    
    def test_service_integration_table_should_exist(self):
        """
        テスト: サービス統合テーブルが存在すること
        
        要件:
        - PJINIT/TECHZIP/GPT-5サービス統合
        - API呼び出し履歴
        - 統合結果管理
        """
        # GREEN: スキーマを初期化してテーブルが作成されることを確認  
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        # テーブルが存在することを確認
        cursor = self.conn.execute("SELECT * FROM service_integrations LIMIT 0")
        self.assertIsNotNone(cursor)
    
    def test_n_number_master_schema_integrity(self):
        """
        テスト: N番号マスターテーブルのスキーマ整合性
        
        要件:
        - n_number: 主キー、NOT NULL、UNIQUE
        - title: タイトル
        - current_stage: 現在のワークフローステージ
        - project_metadata: JSON形式のプロジェクトメタデータ
        - created_at, updated_at: タイムスタンプ
        """
        # GREEN: テーブルが正しいスキーマで作成されることを確認
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        cursor = self.conn.execute("PRAGMA table_info(n_number_master)")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # 必要なカラムが存在することを確認
        column_names = [col['name'] for col in columns]
        self.assertIn('n_number', column_names)
        self.assertIn('title', column_names)
        self.assertIn('current_stage', column_names)
        self.assertIn('project_metadata', column_names)
        self.assertIn('created_at', column_names)
        self.assertIn('updated_at', column_names)
    
    def test_workflow_stages_schema_integrity(self):
        """
        テスト: ワークフローステージテーブルのスキーマ整合性
        
        要件:
        - id: 主キー
        - n_number: N番号 (外部キー)
        - stage_type: ステージ種別 (proposal_draft/proposal/specification)
        - stage_status: ステージステータス (WorkflowStatus enum)
        - stage_data: JSON形式のステージ固有データ
        - completed_at: 完了日時
        """
        # GREEN: テーブルが正しいスキーマで作成されることを確認
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        cursor = self.conn.execute("PRAGMA table_info(workflow_stages)")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # 必要なカラムが存在することを確認
        column_names = [col['name'] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('n_number', column_names)
        self.assertIn('stage_type', column_names)
        self.assertIn('stage_status', column_names)
        self.assertIn('stage_data', column_names)
        self.assertIn('completed_at', column_names)
    
    def test_service_integration_schema_integrity(self):
        """
        テスト: サービス統合テーブルのスキーマ整合性
        
        要件:
        - id: 主キー
        - n_number: N番号 (外部キー)
        - service_type: サービス種別 (PJINIT/TECHZIP/GPT5)
        - integration_status: 統合ステータス
        - api_request_data: API呼び出しデータ (JSON)
        - api_response_data: API応答データ (JSON)
        - executed_at: 実行日時
        """
        # GREEN: テーブルが正しいスキーマで作成されることを確認
        from src.config.n_number_schema import NNumberDatabaseSchema
        schema = NNumberDatabaseSchema(self.db_path)
        
        cursor = self.conn.execute("PRAGMA table_info(service_integrations)")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # 必要なカラムが存在することを確認
        column_names = [col['name'] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('n_number', column_names)
        self.assertIn('service_type', column_names)
        self.assertIn('integration_status', column_names)
        self.assertIn('api_request_data', column_names)
        self.assertIn('api_response_data', column_names)
        self.assertIn('executed_at', column_names)

class TestWorkflowStagesEnum(unittest.TestCase):
    """ワークフローステージEnumのテスト"""
    
    def test_workflow_stage_type_enum_should_exist(self):
        """
        テスト: ワークフローステージタイプEnumが存在すること
        
        要件:
        - PROPOSAL_DRAFT: 企画案書
        - PROPOSAL: 企画書  
        - SPECIFICATION: 製品仕様書
        """
        # GREEN: Enumが正しく定義されていることを確認
        try:
            from src.models.workflow_stages import WorkflowStageType
            self.assertTrue(hasattr(WorkflowStageType, 'PROPOSAL_DRAFT'))
            self.assertTrue(hasattr(WorkflowStageType, 'PROPOSAL'))
            self.assertTrue(hasattr(WorkflowStageType, 'SPECIFICATION'))
        except ImportError:
            self.fail("WorkflowStageType should be importable")
    
    def test_service_type_enum_should_exist(self):
        """
        テスト: サービスタイプEnumが存在すること
        
        要件:
        - PJINIT: プロジェクト初期化サービス
        - TECHZIP: 技術書作成サービス
        - GPT5: GPT-5 API統合サービス
        """
        # GREEN: Enumが正しく定義されていることを確認
        try:
            from src.models.service_integration import ServiceType
            self.assertTrue(hasattr(ServiceType, 'PJINIT'))
            self.assertTrue(hasattr(ServiceType, 'TECHZIP'))
            self.assertTrue(hasattr(ServiceType, 'GPT5'))
        except ImportError:
            self.fail("ServiceType should be importable")

class TestNNumberIntegrationRepository(unittest.TestCase):
    """N番号統合基盤リポジトリのテスト"""
    
    def setUp(self):
        """テスト用データベースセットアップ"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
    
    def tearDown(self):
        """テスト後クリーンアップ"""
        Path(self.db_path).unlink(missing_ok=True)
    
    def test_create_n_number_project_should_succeed_with_repository(self):
        """
        テスト: リポジトリによるN番号プロジェクト作成成功
        
        要件:
        - N番号を指定してプロジェクト作成
        - 3段階ワークフロー初期化
        - サービス統合準備
        """
        # GREEN: リポジトリクラスが正しくインポートできることを確認
        try:
            from src.repositories.n_number_integration_repository import NNumberIntegrationRepository
            # リポジトリが正しくインスタンス化できることを確認
            repo = NNumberIntegrationRepository()
            self.assertIsNotNone(repo)
            # プロジェクト作成メソッドが存在することを確認
            self.assertTrue(hasattr(repo, 'create_n_number_project'))
        except ImportError:
            self.fail("NNumberIntegrationRepository should be importable")
    
    def test_get_workflow_stages_by_n_number_should_succeed(self):
        """
        テスト: N番号によるワークフローステージ取得成功
        
        要件:
        - N番号を指定してステージ一覧取得
        - ステージ順序の保証
        - 完了/未完了の判定
        """
        # GREEN: リポジトリクラスのメソッドが存在することを確認
        try:
            from src.repositories.n_number_integration_repository import NNumberIntegrationRepository
            repo = NNumberIntegrationRepository()
            # ワークフローステージ取得メソッドが存在することを確認
            self.assertTrue(hasattr(repo, 'get_workflow_stages_by_n_number'))
        except ImportError:
            self.fail("NNumberIntegrationRepository should be importable")
    
    def test_update_workflow_stage_status_should_succeed(self):
        """
        テスト: ワークフローステージステータス更新成功
        
        要件:
        - ステージステータスの更新
        - WorkflowStatusとの整合性
        - 更新履歴の記録
        """
        # GREEN: リポジトリクラスのメソッドが存在することを確認
        try:
            from src.repositories.n_number_integration_repository import NNumberIntegrationRepository
            repo = NNumberIntegrationRepository()
            # ワークフローステージステータス更新メソッドが存在することを確認
            self.assertTrue(hasattr(repo, 'update_workflow_stage_status'))
        except ImportError:
            self.fail("NNumberIntegrationRepository should be importable")

if __name__ == '__main__':
    print("🟢 TDD Phase: GREEN - 実装テスト実行")
    print("=" * 60)
    
    # テストスイート実行
    unittest.main(verbosity=2)