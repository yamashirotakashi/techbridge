#!/usr/bin/env python3
"""
TechWF GUI creation test (non-blocking)
"""

import sys
import os
import signal
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath('.'))

def test_gui_creation():
    """GUI作成テスト"""
    try:
        print("=== TechWF GUI Creation Test ===")
        
        # 仮想ディスプレイ設定（Linuxでの実行時）
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import TechWFMainWindow
        
        print("Creating QApplication...")
        app = QApplication.instance()
        if app is None:
            app = QApplication(['test'])
        
        print("Creating data directory...")
        os.makedirs("data", exist_ok=True)
        
        print("Creating TechWFMainWindow...")
        db_path = "data/test_techwf.db"
        window = TechWFMainWindow(db_path)
        
        print("✅ TechWFMainWindow created successfully!")
        print(f"   Window title: '{window.windowTitle()}'")
        print(f"   Central widget exists: {window.centralWidget() is not None}")
        print(f"   Window size: {window.size().width()}x{window.size().height()}")
        
        # ウィジェットの確認
        if hasattr(window, 'workflow_table') and window.workflow_table:
            print(f"   Workflow table exists: {window.workflow_table.columnCount()} columns")
        
        if hasattr(window, 'sync_buttons') and window.sync_buttons:
            print(f"   Sync buttons exist: {list(window.sync_buttons.keys())}")
        
        # ウィンドウを閉じる
        window.close()
        app.quit()
        
        print("\n🎉 GUI creation test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ GUI creation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def timeout_handler(signum, frame):
    """タイムアウトハンドラ"""
    print("\n⏰ Test timed out")
    sys.exit(124)

if __name__ == "__main__":
    print("Starting TechWF GUI creation test...")
    
    # 30秒のタイムアウトを設定
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        success = test_gui_creation()
        signal.alarm(0)  # タイムアウトをクリア
        
        if success:
            print("\n✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(3)