#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF DataBinding デバッグプログラム（GUI非表示）
DataBindingManager初期化問題の特定
"""
import sys
import os
import logging
import traceback

# パス設定
sys.path.insert(0, os.path.abspath('.'))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_step_by_step():
    """ステップごとの詳細テスト"""
    try:
        print("=== Step by Step Test (No GUI) ===")
        
        # Step 1: Repository
        print("Step 1: Repository initialization...")
        from src.repositories.publication_repository import PublicationRepository
        repository = PublicationRepository("data/test_techwf.db")
        print("✅ Repository OK")
        
        # Step 2: Config Service
        print("Step 2: Config service initialization...")
        from src.services.config_service import get_config_service
        config_service = get_config_service()
        print("✅ Config Service OK")
        
        # Step 3: WorkflowController
        print("Step 3: WorkflowController initialization...")
        from src.controllers.workflow_controller import WorkflowController
        controller = WorkflowController(
            repository=repository,
            config_service=config_service,
            sheets_service=None,
            slack_service=None,
            progress_callback=None
        )
        print("✅ WorkflowController OK")
        
        # Step 4: UIStateManager
        print("Step 4: UIStateManager initialization...")
        from src.gui.ui_state_manager import UIStateManager
        ui_manager = UIStateManager("test_ui_state.json")
        print("✅ UIStateManager OK")
        
        # Step 5: Mock MainWindow
        print("Step 5: Mock MainWindow creation...")
        class MockMainWindow:
            def __init__(self):
                self.workflow_table = None  # 模拟table
        
        mock_main_window = MockMainWindow()
        print("✅ Mock MainWindow OK")
        
        # Step 6: DataBindingManager
        print("Step 6: DataBindingManager initialization...")
        from src.gui.data_binding_manager import DataBindingManager
        data_binding_manager = DataBindingManager(
            main_window=mock_main_window,
            workflow_controller=controller,
            ui_state_manager=ui_manager,
            parent=None
        )
        print("✅ DataBindingManager OK")
        
        # Step 7: Sample Data Generation
        print("Step 7: Sample data generation...")
        sample_data = data_binding_manager._get_sample_data()
        print(f"✅ Sample data generated: {len(sample_data)} items")
        for i, item in enumerate(sample_data):
            print(f"  {i+1}: {item.to_table_row()}")
        
        # Step 8: Data Conversion
        print("Step 8: Data conversion test...")
        raw_data = [
            {"n_number": "N99999", "title": "テスト書籍", "author": "テスト著者", "status": "テスト中", "updated_at": "2025-01-01"}
        ]
        converted_data = data_binding_manager._convert_to_workflow_data(raw_data)
        print(f"✅ Data conversion OK: {len(converted_data)} items")
        for item in converted_data:
            print(f"  Converted: {item.to_table_row()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Step by step test failed: {e}")
        traceback.print_exc()
        return False

def test_controller_data():
    """コントローラーからのデータ取得テスト"""
    try:
        print("\n=== Controller Data Test ===")
        
        # Setup
        from src.repositories.publication_repository import PublicationRepository
        from src.services.config_service import get_config_service
        from src.controllers.workflow_controller import WorkflowController
        
        repository = PublicationRepository("data/test_techwf.db")
        config_service = get_config_service()
        controller = WorkflowController(
            repository=repository,
            config_service=config_service,
            sheets_service=None,
            slack_service=None,
            progress_callback=None
        )
        
        # データ取得テスト
        if hasattr(controller, 'get_all_workflows'):
            workflows = controller.get_all_workflows()
            print(f"✅ Controller data: {len(workflows)} workflows found")
            if workflows:
                print(f"  First workflow: {workflows[0]}")
        else:
            print("⚠️ Controller does not have get_all_workflows method")
            print("  This is expected - using fallback sample data")
        
        return True
        
    except Exception as e:
        print(f"❌ Controller data test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("TechWF DataBinding Debug Program (No GUI)")
    print("=" * 60)
    
    tests = [
        ("Step by Step", test_step_by_step),
        ("Controller Data", test_controller_data)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        print("💡 DataBindingManager components work correctly.")
        print("💡 The issue might be in the GUI integration or table binding.")
    else:
        print("\n⚠️  Some tests failed. Check the error details above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())