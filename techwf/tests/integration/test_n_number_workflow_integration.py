#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N番号統合基盤 - 統合テスト
T-wada流TDD REFACTOR フェーズ

実際のワークフローシナリオテスト:
1. N番号プロジェクト作成
2. 3段階ワークフロー実行
3. PJINIT/TECHZIP/GPT-5サービス統合
4. 企画案書→企画書→製品仕様書の実ワークフロー
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.n_number_schema import NNumberDatabaseSchema
from src.repositories.n_number_integration_repository import NNumberIntegrationRepository
from src.models.workflow_stages import WorkflowStageType, StageStatus
from src.models.service_integration import ServiceType, IntegrationStatus

class TestNNumberWorkflowIntegration(unittest.TestCase):
    """N番号統合ワークフローの統合テスト"""
    
    def setUp(self):
        """統合テスト用セットアップ"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # N番号統合基盤初期化
        self.db_schema = NNumberDatabaseSchema(self.db_path)
        self.repository = NNumberIntegrationRepository(self.db_schema)
    
    def tearDown(self):
        """テスト後クリーンアップ"""
        Path(self.db_path).unlink(missing_ok=True)
    
    def test_complete_n_number_workflow_scenario(self):
        """
        完全なN番号ワークフローシナリオテスト
        
        シナリオ:
        1. N番号「N0001TB」のプロジェクト作成
        2. 企画案書段階の開始・完了
        3. 企画書段階の開始・完了  
        4. 製品仕様書段階の開始・完了
        5. 各段階でのPJINIT/TECHZIP/GPT-5統合
        """
        n_number = "N0001TB"
        title = "TechBridge統合ワークフローテスト"
        
        # Step 1: N番号プロジェクト作成
        success = self.repository.create_n_number_project(n_number, title)
        self.assertTrue(success, "N番号プロジェクト作成が成功すること")
        
        # Step 2: プロジェクト情報確認
        project = self.repository.get_n_number_project(n_number)
        self.assertIsNotNone(project, "作成されたプロジェクトが取得できること")
        self.assertEqual(project.n_number, n_number)
        self.assertEqual(project.title, title)
        self.assertEqual(project.current_stage, WorkflowStageType.PROPOSAL_DRAFT)
        
        # Step 3: 3段階ワークフローステージ確認
        stages = self.repository.get_workflow_stages_by_n_number(n_number)
        self.assertEqual(len(stages), 3, "3つのワークフローステージが作成されること")
        
        # ステージ順序確認
        stage_types = [stage.stage_type for stage in stages]
        expected_stages = [
            WorkflowStageType.PROPOSAL_DRAFT,
            WorkflowStageType.PROPOSAL,
            WorkflowStageType.SPECIFICATION
        ]
        self.assertEqual(stage_types, expected_stages, "ステージが正しい順序で作成されること")
        
        # Step 4: 企画案書段階の実行
        success = self.repository.update_workflow_stage_status(
            n_number, 
            WorkflowStageType.PROPOSAL_DRAFT, 
            'in_progress'
        )
        self.assertTrue(success, "企画案書段階の進行中更新が成功すること")
        
        # Step 5: 企画案書段階の完了
        success = self.repository.update_workflow_stage_status(
            n_number,
            WorkflowStageType.PROPOSAL_DRAFT,
            'completed'
        )
        self.assertTrue(success, "企画案書段階の完了更新が成功すること")
        
        # Step 6: 企画書段階の実行
        success = self.repository.update_workflow_stage_status(
            n_number,
            WorkflowStageType.PROPOSAL, 
            'in_progress'
        )
        self.assertTrue(success, "企画書段階の進行中更新が成功すること")
        
        # Step 7: 企画書段階の完了
        success = self.repository.update_workflow_stage_status(
            n_number,
            WorkflowStageType.PROPOSAL,
            'completed'
        )
        self.assertTrue(success, "企画書段階の完了更新が成功すること")
        
        # Step 8: 製品仕様書段階の実行・完了
        success = self.repository.update_workflow_stage_status(
            n_number,
            WorkflowStageType.SPECIFICATION,
            'completed'
        )
        self.assertTrue(success, "製品仕様書段階の完了更新が成功すること")
        
        # Step 9: 最終状態確認
        final_project = self.repository.get_n_number_project(n_number)
        self.assertEqual(final_project.current_stage, WorkflowStageType.SPECIFICATION,
                        "最終的に製品仕様書段階になること")
        
        print(f"✅ N番号ワークフロー完了: {n_number} - {title}")
        print(f"   最終段階: {final_project.current_stage.value}")
    
    def test_service_integration_workflow(self):
        """
        サービス統合ワークフローテスト
        
        シナリオ:
        1. N番号プロジェクト作成
        2. PJINIT サービス統合実行
        3. TECHZIP サービス統合実行
        4. GPT-5 サービス統合実行
        """
        n_number = "N0002SV"
        title = "サービス統合テストプロジェクト"
        
        # プロジェクト作成
        success = self.repository.create_n_number_project(n_number, title)
        self.assertTrue(success)
        
        # 各サービス統合をシミュレート
        services = [
            (ServiceType.PJINIT, "プロジェクト初期化", {"template": "techbook", "output_path": "/dist"}),
            (ServiceType.TECHZIP, "技術書作成", {"format": "pdf", "pages": 120}),
            (ServiceType.GPT5, "AI支援分析", {"model": "gpt-5", "task": "content_review"})
        ]
        
        for service_type, description, request_data in services:
            # サービス統合レコード作成をシミュレート
            with self.db_schema.get_connection() as conn:
                conn.execute("""
                    INSERT INTO service_integrations 
                    (n_number, service_type, integration_status, api_request_data, executed_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    n_number,
                    service_type.value,
                    IntegrationStatus.SUCCESS.value,
                    json.dumps(request_data),
                    datetime.now().isoformat()
                ))
                conn.commit()
        
        # 統合結果確認
        with self.db_schema.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM service_integrations 
                WHERE n_number = ?
                ORDER BY created_at
            """, (n_number,))
            
            integrations = [dict(row) for row in cursor.fetchall()]
            self.assertEqual(len(integrations), 3, "3つのサービス統合が記録されること")
            
            # 各サービス統合の確認
            for i, (service_type, _, _) in enumerate(services):
                integration = integrations[i]
                self.assertEqual(integration['service_type'], service_type.value)
                self.assertEqual(integration['integration_status'], IntegrationStatus.SUCCESS.value)
                self.assertIsNotNone(integration['api_request_data'])
        
        print(f"✅ サービス統合ワークフロー完了: {n_number}")
        print(f"   統合サービス数: {len(integrations)}")
    
    def test_concurrent_n_number_projects(self):
        """
        複数N番号プロジェクトの並行処理テスト
        
        シナリオ:
        1. 複数のN番号プロジェクトを作成
        2. それぞれ異なる段階まで進行
        3. 個別のプロジェクトが独立して動作することを確認
        """
        projects = [
            ("N0003A", "プロジェクトA", WorkflowStageType.PROPOSAL_DRAFT),
            ("N0003B", "プロジェクトB", WorkflowStageType.PROPOSAL),
            ("N0003C", "プロジェクトC", WorkflowStageType.SPECIFICATION)
        ]
        
        # 各プロジェクトを作成
        for n_number, title, target_stage in projects:
            success = self.repository.create_n_number_project(n_number, title)
            self.assertTrue(success, f"プロジェクト{n_number}の作成が成功すること")
            
            # 目標段階まで進行
            if target_stage == WorkflowStageType.PROPOSAL:
                # 企画案書完了
                self.repository.update_workflow_stage_status(
                    n_number, WorkflowStageType.PROPOSAL_DRAFT, 'completed'
                )
            elif target_stage == WorkflowStageType.SPECIFICATION:
                # 企画案書・企画書完了
                self.repository.update_workflow_stage_status(
                    n_number, WorkflowStageType.PROPOSAL_DRAFT, 'completed'
                )
                self.repository.update_workflow_stage_status(
                    n_number, WorkflowStageType.PROPOSAL, 'completed'
                )
        
        # 各プロジェクトの独立性確認
        for n_number, title, expected_stage in projects:
            project = self.repository.get_n_number_project(n_number)
            self.assertIsNotNone(project)
            self.assertEqual(project.current_stage, expected_stage, 
                           f"プロジェクト{n_number}が期待された段階にあること")
            
            stages = self.repository.get_workflow_stages_by_n_number(n_number)
            self.assertEqual(len(stages), 3, f"プロジェクト{n_number}に3つのステージがあること")
        
        print(f"✅ 並行プロジェクト処理完了: {len(projects)}プロジェクト")

if __name__ == '__main__':
    print("🔵 TDD Phase: REFACTOR - 統合テスト実行")
    print("=" * 60)
    
    # 統合テストスイート実行
    unittest.main(verbosity=2)