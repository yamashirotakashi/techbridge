#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF MainWindow デバッグプログラム
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_databinding_import():
    """DataBindingManagerのインポートテスト"""
    try:
        print("=== DataBindingManager Import Test ===")
        from src.gui.data_binding_manager import DataBindingManager
        print("✅ DataBindingManager import successful")
        return True
    except Exception as e:
        print(f"❌ DataBindingManager import failed: {e}")
        traceback.print_exc()
        return False

def test_main_window_init():
    """MainWindowの初期化テスト"""
    try:
        print("\n=== MainWindow Initialization Test ===")
        
        # 必要なインポート
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import TechWFMainWindow
        
        app = QApplication([])
        
        # データベースパス
        db_path = "data/test_techwf.db"
        
        print("Creating TechWFMainWindow...")
        window = TechWFMainWindow(db_path)
        print("✅ MainWindow created successfully")
        
        # DataBindingManagerが存在するかチェック
        if hasattr(window, 'data_binding_manager'):
            print("✅ DataBindingManager attribute found")
            if window.data_binding_manager:
                print("✅ DataBindingManager instance created")
            else:
                print("❌ DataBindingManager is None")
        else:
            print("❌ DataBindingManager attribute not found")
        
        # ワークフローテーブルが存在するかチェック
        if hasattr(window, 'workflow_table'):
            print("✅ workflow_table attribute found")
            if window.workflow_table:
                print(f"✅ workflow_table created, rows: {window.workflow_table.rowCount()}")
            else:
                print("❌ workflow_table is None")
        else:
            print("❌ workflow_table attribute not found")
        
        window.close()
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ MainWindow initialization failed: {e}")
        traceback.print_exc()
        return False

def test_sample_data():
    """サンプルデータテスト"""
    try:
        print("\n=== Sample Data Test ===")
        from src.gui.data_binding_manager import DataBindingManager, WorkflowData
        
        # サンプルデータ作成
        sample_data = [
            WorkflowData("N12345", "サンプル書籍1", "著者A", "原稿依頼", "2025-01-15"),
            WorkflowData("N23456", "サンプル書籍2", "著者B", "初校", "2025-01-20")
        ]
        
        print(f"✅ Sample data created: {len(sample_data)} items")
        for i, item in enumerate(sample_data):
            print(f"  {i+1}: {item.to_table_row()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("TechWF MainWindow Debug Program")
    print("=" * 50)
    
    tests = [
        ("DataBinding Import", test_databinding_import),
        ("Sample Data", test_sample_data),
        ("MainWindow Init", test_main_window_init)
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
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        print("💡 DataBindingManager should work correctly in the main application.")
    else:
        print("\n⚠️  Some tests failed. Check the error details above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())