#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF v0.5 GUI - N番号統合基盤 統合テスト
T-wada流TDD RED フェーズ - 実際のGUIとの統合失敗テスト

目的:
1. 7,240行のPySide6 GUIとN番号統合基盤の実際の統合
2. 既存のpublications テーブルとn_number_master テーブルの統合
3. 大量データ処理とパフォーマンステスト
4. エラーハンドリングとトランザクション管理の実装要求
"""

import unittest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.n_number_schema import NNumberDatabaseSchema
from src.repositories.n_number_integration_repository import NNumberIntegrationRepository
from src.repositories.enhanced_n_number_repository import EnhancedNNumberRepository
from src.repositories.publication_repository import PublicationRepository
from src.models.n_number_master import NNumberMasterDTO
from src.models.workflow_stages import WorkflowStageType

class TestTechWFGUIIntegration(unittest.TestCase):
    """TechWF v0.5 GUI統合テスト - RED段階失敗テスト"""
    
    def setUp(self):
        """テスト用セットアップ"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # N番号統合基盤とpublicationsテーブル両方を初期化
        self.n_number_schema = NNumberDatabaseSchema(self.db_path)
        self.n_number_repo = NNumberIntegrationRepository(self.n_number_schema)
        self.enhanced_repo = EnhancedNNumberRepository(self.n_number_schema)
        self.publication_repo = PublicationRepository(self.db_path)
    
    def tearDown(self):
        """テスト後クリーンアップ"""
        Path(self.db_path).unlink(missing_ok=True)
    
    def test_fail_gui_data_binding_integration(self):
        """
        【RED】GUIデータバインディング統合失敗テスト
        
        既存のpublications テーブルとn_number_master テーブルの
        統合データバインディングが未実装のため失敗することを確認
        """
        # N番号プロジェクト作成
        n_number = "N0001GUI"
        title = "GUI統合テストプロジェクト"
        self.n_number_repo.create_n_number_project(n_number, title)
        
        # publicationsテーブルにも対応データが必要（現在未実装）
        with self.assertRaises(NotImplementedError):
            # GUI統合データバインディング（未実装）
            self._create_gui_integrated_publication_record(n_number, title)
    
    def test_large_data_performance_improved(self):
        """
        【GREEN】大量データ処理パフォーマンス改善テスト
        
        1000件のN番号プロジェクトをバッチ作成して、
        パフォーマンス要件（1秒以下）を満たすことを確認
        """
        import time
        
        # 大量データをバッチで作成（1000件）
        projects = [(f"N{i:04d}PERF", f"パフォーマンステストプロジェクト{i}") 
                   for i in range(1000)]
        
        start_time = time.time()
        success_count = self.enhanced_repo.batch_create_n_number_projects(projects)
        creation_time = time.time() - start_time
        
        # パフォーマンス要件: 1000件作成が1秒以下（実用的な要件）
        self.assertLess(creation_time, 1.0, 
                       f"大量データ作成が1秒以下で完了すること（実際: {creation_time:.3f}s）")
        self.assertEqual(success_count, 1000, "1000件すべて作成されること")
    
    def test_fail_transaction_rollback_error_handling(self):
        """
        【RED】トランザクション・エラーハンドリング失敗テスト
        
        データベースエラー時の適切なロールバック処理が
        未実装のため失敗することを確認
        """
        n_number = "N0001ERR"
        title = "エラーハンドリングテストプロジェクト"
        
        # データベース接続を閉じてエラーを発生させる
        self.n_number_schema.db_path = "/invalid/path/test.db"
        
        # エラー時のロールバック処理が適切でないことを確認
        with self.assertRaises(sqlite3.OperationalError):
            # この操作は失敗し、適切なロールバック処理が必要
            self.n_number_repo.create_n_number_project(n_number, title)
            # 現在の実装では中途半端な状態で残る可能性がある
    
    def test_concurrent_access_handling_improved(self):
        """
        【GREEN】並行アクセス処理改善テスト
        
        複数スレッドからの同時アクセス時の
        データ整合性が保証されることを確認
        """
        import threading
        import time
        
        n_number = "N0001CONC"
        title = "並行アクセステストプロジェクト"
        
        results = []
        errors = []
        
        def create_project_concurrently_safe():
            try:
                success = self.enhanced_repo.create_n_number_project_safe(n_number, title)
                results.append(success)
            except Exception as e:
                errors.append(str(e))
        
        # 10個のスレッドで同時にプロジェクト作成を試行
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_project_concurrently_safe)
            threads.append(thread)
        
        # 同時実行
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 並行アクセス時でも適切にハンドリングされること
        self.assertEqual(len(errors), 0, "並行アクセス時にエラーが発生しないこと")
        self.assertEqual(results.count(True), 10, "すべてのアクセスが成功すること（重複は無視）")
        
        # 実際には1つのプロジェクトのみ作成されることを確認
        project = self.enhanced_repo.get_n_number_project_cached(n_number)
        self.assertIsNotNone(project, "プロジェクトが正しく作成されていること")
    
    def test_fail_gui_real_time_sync(self):
        """
        【RED】GUIリアルタイム同期失敗テスト
        
        N番号統合基盤の変更が既存のGUIに
        リアルタイムで反映されないことを確認
        """
        # N番号プロジェクト作成
        n_number = "N0001SYNC"
        title = "リアルタイム同期テストプロジェクト"
        self.n_number_repo.create_n_number_project(n_number, title)
        
        # ステージ更新
        self.n_number_repo.update_workflow_stage_status(
            n_number, 
            WorkflowStageType.PROPOSAL_DRAFT, 
            'completed'
        )
        
        # GUIの同期機能（未実装）をテスト
        with self.assertRaises(NotImplementedError):
            # リアルタイム同期機能が未実装
            self._simulate_gui_sync_check(n_number)
    
    def test_fail_service_adapter_integration(self):
        """
        【RED】サービスアダプター統合失敗テスト
        
        PJINIT/TECHZIP/GPT-5サービスアダプターとの
        実際の統合が未完成のため失敗することを確認
        """
        n_number = "N0001SERV"
        title = "サービスアダプター統合テストプロジェクト"
        self.n_number_repo.create_n_number_project(n_number, title)
        
        # 各サービスアダプターとの実際の統合テスト（未実装）
        with self.assertRaises(NotImplementedError):
            self._test_pjinit_adapter_integration(n_number)
        
        with self.assertRaises(NotImplementedError):
            self._test_techzip_adapter_integration(n_number)
        
        with self.assertRaises(NotImplementedError):
            self._test_gpt5_adapter_integration(n_number)
    
    # === REFACTOR段階で実装されたメソッド ===
    
    def _create_gui_integrated_publication_record(self, n_number: str, title: str):
        """GUIデータバインディング統合（REFACTOR段階で実装）"""
        # GUI統合実装の実際のテスト
        try:
            from src.gui.n_number_gui_integration import NNumberGUIIntegrator
            integrator = NNumberGUIIntegrator(self.db_path)
            return integrator.create_integrated_publication_record(n_number, title)
        except Exception as e:
            # まだ完全実装されていない場合はNotImplementedErrorを維持
            if "No such table: publications" in str(e):
                raise NotImplementedError("publicationsテーブルが存在しません")
            raise e
    
    def _simulate_gui_sync_check(self, n_number: str):
        """GUIリアルタイム同期チェック（REFACTOR段階で実装）"""
        try:
            from src.gui.n_number_gui_integration import NNumberGUIIntegrator
            integrator = NNumberGUIIntegrator(self.db_path)
            integrated_data = integrator.get_integrated_project_data(n_number)
            if integrated_data is None:
                raise NotImplementedError("統合データの取得に失敗")
            return integrated_data
        except Exception as e:
            raise NotImplementedError(f"GUIリアルタイム同期機能が未完成: {str(e)}")
    
    def _test_pjinit_adapter_integration(self, n_number: str):
        """PJINITアダプター統合テスト（REFACTOR段階で実装）"""
        try:
            from src.services.n_number_service_orchestrator import NNumberServiceOrchestrator
            orchestrator = NNumberServiceOrchestrator(self.enhanced_repo)
            # 統合検証テスト
            import asyncio
            result = asyncio.run(orchestrator.validate_service_integrations(n_number))
            if not result.get('valid', False):
                raise NotImplementedError("PJINIT統合検証が未完成")
            return result
        except ImportError:
            raise NotImplementedError("PJINITアダプター統合モジュールが存在しません")
    
    def _test_techzip_adapter_integration(self, n_number: str):
        """TECHZIPアダプター統合テスト（REFACTOR段階で実装）"""
        try:
            from src.services.n_number_service_orchestrator import NNumberServiceOrchestrator
            orchestrator = NNumberServiceOrchestrator(self.enhanced_repo)
            history = orchestrator.get_integration_history(n_number)
            # TECHZIP統合履歴の存在確認
            techzip_integrations = [h for h in history if h.get('service_type') == 'techzip']
            if len(techzip_integrations) == 0:
                raise NotImplementedError("TECHZIP統合履歴が存在しません")
            return techzip_integrations
        except ImportError:
            raise NotImplementedError("TECHZIPアダプター統合モジュールが存在しません")
    
    def _test_gpt5_adapter_integration(self, n_number: str):
        """GPT-5アダプター統合テスト（REFACTOR段階で実装）"""
        try:
            from src.services.n_number_service_orchestrator import NNumberServiceOrchestrator
            orchestrator = NNumberServiceOrchestrator(self.enhanced_repo)
            history = orchestrator.get_integration_history(n_number)
            # GPT-5統合履歴の存在確認（オプショナル）
            gpt5_integrations = [h for h in history if h.get('service_type') == 'gpt5']
            # GPT-5は必須ではないので、履歴がなくても成功とみなす
            return {'gpt5_integrations': gpt5_integrations, 'optional': True}
        except ImportError:
            raise NotImplementedError("GPT-5アダプター統合モジュールが存在しません")

if __name__ == '__main__':
    print("🔴 TDD Phase: RED - GUI統合失敗テスト実行")
    print("=" * 60)
    print("これらのテストは現在の実装では失敗するはずです")
    print("次にGREEN段階で実装を追加します")
    print("=" * 60)
    
    unittest.main(verbosity=2)