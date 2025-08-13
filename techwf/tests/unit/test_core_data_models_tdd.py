#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コアデータモデルクラス TDD Test Suite - Phase RED
T-wada流テストファーストアプローチによる厳密な実装

Week 1 Day 3-4: コアデータモデルクラス実装
- ドメインロジックの厳密な実装
- ビジネスルールの実装
- GUI統合準備
- サービス統合インターフェース

RED段階: 失敗するテストを書く → 最小限の実装 → リファクタリング
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestNNumberProjectDomainModel(unittest.TestCase):
    """N番号プロジェクトドメインモデルのテスト"""
    
    def test_n_number_project_creation_should_enforce_business_rules(self):
        """
        RED: N番号プロジェクト作成時のビジネスルール強制
        
        ビジネスルール:
        1. N番号は'N'で始まり6桁の数字が続く形式のみ許可
        2. タイトルは2文字以上100文字以内
        3. 作成時は必ず企画案書(PROPOSAL_DRAFT)ステージから開始
        4. プロジェクトメタデータにデフォルト値を設定
        """
        # このテストは現在失敗する（実装していないため）
        from src.models.domain.n_number_project import NNumberProject
        
        # 正常な作成
        project = NNumberProject.create(
            n_number="N12345",
            title="テスト企画",
            creator="テストユーザー"
        )
        
        self.assertEqual(project.n_number, "N12345")
        self.assertEqual(project.title, "テスト企画")
        self.assertEqual(project.current_stage.name, "PROPOSAL_DRAFT")
        self.assertIn("creator", project.metadata)
        
        # 不正なN番号での作成は失敗
        with self.assertRaises(ValueError):
            NNumberProject.create("INVALID", "テスト", "ユーザー")
            
        # 空のタイトルでの作成は失敗
        with self.assertRaises(ValueError):
            NNumberProject.create("N12346", "", "ユーザー")
    
    def test_workflow_stage_transition_should_follow_strict_rules(self):
        """
        RED: ワークフローステージ遷移の厳密なルール
        
        遷移ルール:
        1. PROPOSAL_DRAFT → PROPOSAL のみ許可
        2. PROPOSAL → SPECIFICATION のみ許可
        3. 逆方向の遷移は禁止（例外: 管理者権限）
        4. 同一ステージ内でのステータス更新は許可
        5. 遷移時には前段階の完了チェックが必須
        """
        from src.models.domain.n_number_project import NNumberProject
        from src.models.workflow_stages import WorkflowStageType
        
        project = NNumberProject.create("N12347", "遷移テスト", "ユーザー")
        
        # 正常な遷移: PROPOSAL_DRAFT → PROPOSAL
        success = project.transition_to_stage(
            WorkflowStageType.PROPOSAL, 
            completed_by="ユーザー"
        )
        self.assertTrue(success)
        self.assertEqual(project.current_stage, WorkflowStageType.PROPOSAL)
        
        # 不正な遷移: PROPOSAL → PROPOSAL_DRAFT (逆方向)
        with self.assertRaises(ValueError):
            project.transition_to_stage(WorkflowStageType.PROPOSAL_DRAFT)
        
        # 正常な遷移: PROPOSAL → SPECIFICATION
        success = project.transition_to_stage(WorkflowStageType.SPECIFICATION)
        self.assertTrue(success)
        self.assertEqual(project.current_stage, WorkflowStageType.SPECIFICATION)
    
    def test_service_integration_orchestrator_should_coordinate_apis(self):
        """
        RED: サービス統合オーケストレーターによるAPI協調
        
        統合要件:
        1. PJINIT/TECHZIP/GPT-5サービスの統合管理
        2. 各サービス呼び出しの順序制御
        3. エラー時のロールバック機能
        4. 統合結果のメタデータ保存
        5. 統合状態の追跡・監視
        """
        from src.models.domain.service_integration_orchestrator import ServiceIntegrationOrchestrator
        from src.models.service_integration import ServiceType
        
        orchestrator = ServiceIntegrationOrchestrator()
        
        # サービス統合の実行
        result = orchestrator.execute_integration_workflow(
            n_number="N12348",
            services=[ServiceType.PJINIT, ServiceType.GPT5],
            integration_data={"project_type": "book", "priority": "high"}
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.service_results), 2)
        self.assertIn(ServiceType.PJINIT, result.service_results)
        self.assertIn(ServiceType.GPT5, result.service_results)
        
        # 統合履歴の確認
        history = orchestrator.get_integration_history("N12348")
        self.assertGreater(len(history), 0)

class TestWorkflowBusinessRules(unittest.TestCase):
    """ワークフロービジネスルールのテスト"""
    
    def test_stage_completion_validator_should_enforce_criteria(self):
        """
        RED: ステージ完了バリデーターによる完了基準強制
        
        完了基準:
        1. PROPOSAL_DRAFT: タイトル、概要、担当者が必須
        2. PROPOSAL: 詳細企画書、予算、スケジュールが必須
        3. SPECIFICATION: 技術仕様、UI設計、テスト計画が必須
        4. 各ステージで最低1回のレビューが必須
        5. 承認者の電子署名が必須
        """
        from src.models.domain.stage_completion_validator import StageCompletionValidator
        from src.models.workflow_stages import WorkflowStageType
        
        validator = StageCompletionValidator()
        
        # PROPOSAL_DRAFTステージの完了基準チェック
        incomplete_data = {
            "title": "テスト企画",
            # 概要と担当者が不足
        }
        
        result = validator.validate_stage_completion(
            WorkflowStageType.PROPOSAL_DRAFT,
            incomplete_data
        )
        self.assertFalse(result.is_valid)
        self.assertIn("概要が必須", str(result.validation_errors))
        
        # 完了基準を満たすデータ
        complete_data = {
            "title": "テスト企画",
            "overview": "企画概要です",
            "assignee": "担当者",
            "reviewer": "レビュアー",
            "approval_signature": "承認印"
        }
        
        result = validator.validate_stage_completion(
            WorkflowStageType.PROPOSAL_DRAFT,
            complete_data
        )
        self.assertTrue(result.is_valid)
    
    def test_gui_data_binding_manager_should_sync_with_domain_models(self):
        """
        RED: GUIデータバインディングマネージャーとドメインモデルの同期
        
        GUI統合要件:
        1. ドメインモデルの変更をGUIに自動反映
        2. GUI操作をドメインロジックを通して実行
        3. データ整合性の維持
        4. リアルタイム更新の保証
        5. エラー状態のGUI表示
        """
        from src.models.domain.n_number_project import NNumberProject
        from src.gui.domain_gui_binding import DomainGuiBindingManager
        
        # ドメインモデルの作成
        project = NNumberProject.create("N12349", "GUI統合テスト", "ユーザー")
        
        # GUIバインディングマネージャーの設定
        binding_manager = DomainGuiBindingManager()
        binding_manager.bind_project(project)
        
        # ドメインモデルの変更がGUIに反映されることを確認
        project.update_title("更新されたタイトル")
        
        # GUIからバインディングマネージャー経由でのデータ取得
        gui_data = binding_manager.get_project_display_data("N12349")
        self.assertEqual(gui_data["title"], "更新されたタイトル")
        self.assertEqual(gui_data["stage_display"], "企画案書")

class TestServiceIntegrationInterfaces(unittest.TestCase):
    """サービス統合インターフェースのテスト"""
    
    def test_pjinit_service_adapter_should_handle_project_initialization(self):
        """
        RED: PJINITサービスアダプターによるプロジェクト初期化
        
        PJINIT統合要件:
        1. N番号プロジェクトの初期化要求
        2. プロジェクトテンプレートの取得
        3. ディレクトリ構造の作成指示
        4. 初期ファイル生成の管理
        5. 初期化ログの記録
        """
        from src.services.adapters.pjinit_service_adapter import PJInitServiceAdapter
        
        adapter = PJInitServiceAdapter()
        
        # プロジェクト初期化の実行
        result = adapter.initialize_project(
            n_number="N12350",
            project_type="technical_book",
            template_config={
                "structure": "standard",
                "tools": ["latex", "markdown"],
                "ci_cd": True
            }
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.project_path)
        self.assertIn("初期化完了", result.message)
    
    def test_techzip_service_adapter_should_handle_book_generation(self):
        """
        RED: TECHZIPサービスアダプターによる技術書生成
        
        TECHZIP統合要件:
        1. 技術書プロジェクトの管理
        2. 原稿ファイルの処理
        3. PDF生成の制御
        4. 生成ログの追跡
        5. 品質チェックの統合
        """
        from src.services.adapters.techzip_service_adapter import TechZipServiceAdapter
        
        adapter = TechZipServiceAdapter()
        
        # 技術書生成の実行
        result = adapter.generate_technical_book(
            n_number="N12351",
            content_config={
                "format": "pdf",
                "template": "standard",
                "chapters": ["intro", "main", "conclusion"]
            }
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.output_path)
    
    def test_gpt5_service_adapter_should_provide_ai_assistance(self):
        """
        RED: GPT-5サービスアダプターによるAI支援
        
        GPT-5統合要件:
        1. プロジェクト情報をコンテキストとした支援
        2. 段階別の適切なプロンプト生成
        3. AI応答の構造化処理
        4. 応答品質の評価
        5. 学習データの蓄積
        """
        from src.services.adapters.gpt5_service_adapter import GPT5ServiceAdapter
        
        adapter = GPT5ServiceAdapter()
        
        # AI支援の実行
        result = adapter.get_stage_assistance(
            n_number="N12352",
            stage="PROPOSAL_DRAFT",
            assistance_type="content_generation",
            context_data={
                "title": "AI技術解説書",
                "target_audience": "エンジニア",
                "page_count": 200
            }
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.generated_content)
        self.assertGreater(result.quality_score, 0.7)

if __name__ == '__main__':
    print("🔴 TDD Phase: RED - 失敗するテストを作成")
    print("コアデータモデルクラス実装のためのテストファースト")
    print("=" * 60)
    
    # テストスイート実行（現時点では全て失敗するはず）
    unittest.main(verbosity=2)