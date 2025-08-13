#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF v0.5 メイン実行スクリプト
技術書典・TechBridge統合ワークフロー GUI版
"""

import sys
import os
import logging
from pathlib import Path

# パスの設定（実行場所から相対的にsrcディレクトリを追加）
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# PySide6をインポート
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt, QDir
    from PySide6.QtGui import QPixmap, QIcon
except ImportError as e:
    print(f"PySide6がインストールされていません: {e}")
    print("pip install PySide6 を実行してください")
    sys.exit(1)

# ログ設定
def setup_logging():
    """ログ設定のセットアップ"""
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "techwf.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """必要な依存関係をチェック"""
    required_modules = [
        'sqlite3',
        'json',
        'pathlib',
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"必要なモジュールが見つかりません: {', '.join(missing_modules)}"
        print(error_msg)
        return False
    
    return True

def setup_database():
    """データベースの初期化"""
    data_dir = current_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "techwf.db"
    return str(db_path)

def main():
    """メイン実行関数"""
    try:
        # ログ設定
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("=== TechWF v0.5 起動開始 ===")
        
        # 依存関係チェック
        if not check_dependencies():
            return 1
        
        # Qt アプリケーション作成
        app = QApplication(sys.argv)
        app.setApplicationName("TechWF")
        app.setApplicationVersion("0.5")
        app.setOrganizationName("TechBridge")
        
        # 設定サービス初期化
        from src.services.config_service import get_config_service
        config_service = get_config_service()
        
        # データベース初期化（設定ファイルのパスを優先）
        config_db_path = config_service.get("db_path", "data/techwf.db")
        db_path = setup_database()  # ディレクトリ作成
        
        # 設定ファイルのパスを使用
        final_db_path = config_db_path
        logger.info(f"設定ファイルのデータベースパス: {final_db_path}")
        
        # メインウィンドウをインポート・作成
        try:
            # パッケージ実行のため、絶対インポートを使用
            from src.gui.main_window import TechWFMainWindow
            
            # メインウィンドウ作成
            window = TechWFMainWindow(final_db_path)
            
            # ウィンドウ設定
            window.setWindowTitle("TechWF v0.5 - 技術書典統合ワークフロー")
            window.resize(1200, 800)
            
            # 表示
            window.show()
            
            logger.info("TechWF GUI起動完了")
            
            # イベントループ開始
            return app.exec()
            
        except ImportError as e:
            logger.error(f"メインウィンドウのインポートエラー: {e}")
            QMessageBox.critical(None, "起動エラー", 
                               f"アプリケーションの起動に失敗しました:\n{e}\n\n"
                               "必要なファイルが不足している可能性があります。")
            return 1
            
        except Exception as e:
            logger.error(f"アプリケーション起動エラー: {e}")
            QMessageBox.critical(None, "起動エラー", 
                               f"予期しないエラーが発生しました:\n{e}")
            return 1
    
    except Exception as e:
        print(f"致命的エラー: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)