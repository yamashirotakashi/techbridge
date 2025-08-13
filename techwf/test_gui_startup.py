#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF GUI startup test
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath('.'))

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """必要なモジュールのインポートテスト"""
    try:
        print("=== Import Test Phase ===")
        
        # Qt関連のインポートテスト
        print("Testing Qt imports...")
        from PySide6.QtWidgets import QApplication, QMainWindow
        print("✅ PySide6 QtWidgets OK")
        
        # 基本的なインポートテスト
        print("Testing basic modules...")
        from src.repositories.publication_repository import PublicationRepository
        print("✅ PublicationRepository OK")
        
        from src.services.config_service import get_config_service
        print("✅ ConfigService OK")
        
        from src.gui.theme import ThemeManager
        print("✅ ThemeManager OK")
        
        from src.gui.service_manager import ServiceManager
        print("✅ ServiceManager OK")
        
        # メインウィンドウクラスのインポートテスト
        print("Testing MainWindow import...")
        from src.gui.main_window import TechWFMainWindow
        print("✅ TechWFMainWindow import OK")
        
        print("=== All imports successful ===")
        return True
        
    except Exception as e:
        print(f"❌ Import Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_creation():
    """GUI作成テスト（表示なし）"""
    try:
        print("=== GUI Creation Test ===")
        
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import TechWFMainWindow
        
        # QApplicationを作成
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("Creating main window...")
        
        # データベースパス
        db_path = "data/techwf.db"
        os.makedirs("data", exist_ok=True)  # ディレクトリ作成
        
        # メインウィンドウ作成
        window = TechWFMainWindow(db_path)
        
        print("✅ MainWindow created successfully")
        print(f"Window title: {window.windowTitle()}")
        print(f"Central widget: {window.centralWidget()}")
        
        # ウィンドウを閉じる
        window.close()
        
        print("=== GUI creation successful ===")
        return True
        
    except Exception as e:
        print(f"❌ GUI Creation Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("TechWF GUI Startup Test")
    print("=" * 50)
    
    # インポートテスト
    if not test_imports():
        sys.exit(1)
    
    print()
    
    # GUI作成テスト
    if not test_gui_creation():
        sys.exit(1)
    
    print()
    print("🎉 All tests passed! GUI startup should work.")