#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PJINIT - 技術の泉シリーズプロジェクト初期化ツール
Phase 1リファクタリング版 - モジュラー構造
"""

import sys
import os
import asyncio
from pathlib import Path

# 必要なディレクトリをpythonpathに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Phase 1リファクタリング完成版

from utils.environment import (
    safe_print, 
    is_wsl, 
    pyqt6_available, 
    asyncio_integration, 
    get_environment_info
)


def print_environment_info():
    """環境情報を表示"""
    env_info = get_environment_info()
    
    safe_print("=== PJINIT 環境情報 ===")
    safe_print(f"Platform: {env_info['platform']}")
    safe_print(f"WSL環境: {'Yes' if env_info['is_wsl'] else 'No'}")
    safe_print(f"PyQt6: {'Available' if env_info['pyqt6_available'] else 'Not Available'}")
    safe_print(f"Asyncio統合: {env_info['asyncio_integration'] or 'None'}")
    
    safe_print("--- 外部サービス連携 ---")
    for service, available in env_info['services'].items():
        status = "Available" if available else "Not Available"
        safe_print(f"{service}: {status}")
    
    safe_print("========================")


def run_gui():
    """GUI版を実行"""
    if not pyqt6_available:
        safe_print("❌ PyQt6が利用できません。CLIモードで実行してください。")
        return run_cli()
    
    try:
        from PyQt6.QtWidgets import QApplication
        from application.app_controller import ApplicationController
        
        # QApplicationの初期化
        app = QApplication(sys.argv)
        
        # アプリケーション制御層の初期化
        controller = ApplicationController()
        
        if not controller.initialize():
            safe_print("❌ アプリケーション初期化に失敗しました")
            return 1
        
        # asyncio統合の設定
        if asyncio_integration:
            safe_print(f"✅ asyncio統合: {asyncio_integration}")
            if asyncio_integration == "asyncqt":
                from asyncqt import QEventLoop
            elif asyncio_integration == "qasync":
                import qasync
                from qasync import QEventLoop
            
            # イベントループの設定
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)
        
        # アプリケーション実行
        return controller.run()
        
    except Exception as e:
        safe_print(f"❌ GUI実行エラー: {e}")
        safe_print("CLIモードにフォールバック...")
        return run_cli()


def run_cli():
    """CLI版を実行"""
    safe_print("=== PJINIT CLI版 ===")
    try:
        # 動的インポート（直接パス指定）
        import importlib.util
        from pathlib import Path
        
        project_root = Path(__file__).parent
        core_path = project_root / 'core' / 'project_initializer.py'
        
        spec = importlib.util.spec_from_file_location("core.project_initializer", core_path)
        core_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core_module)
        
        ProjectInitializer = core_module.ProjectInitializer
        
        # プロジェクト初期化ツールの起動
        initializer = ProjectInitializer()
        
        # インタラクティブモード
        while True:
            safe_print("\n--- メニュー ---")
            safe_print("1. プロジェクト情報確認")
            safe_print("2. プロジェクト初期化")
            safe_print("3. 終了")
            
            choice = input("選択してください (1-3): ").strip()
            
            if choice == "1":
                n_code = input("N-code を入力してください: ").strip()
                if n_code:
                    safe_print(f"プロジェクト情報を確認中: {n_code}")
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        project_info = loop.run_until_complete(initializer.fetch_project_info(n_code))
                        
                        if project_info:
                            safe_print("✅ プロジェクト情報を取得しました:")
                            for key, value in project_info.items():
                                safe_print(f"  {key}: {value}")
                        else:
                            safe_print("❌ プロジェクト情報が見つかりませんでした")
                    except Exception as e:
                        safe_print(f"❌ エラー: {e}")
                    finally:
                        loop.close()
            
            elif choice == "2":
                safe_print("プロジェクト初期化機能は実装準備中です")
            
            elif choice == "3":
                safe_print("終了します")
                break
            
            else:
                safe_print("❌ 無効な選択です")
        
        return 0
        
    except ImportError as e:
        safe_print(f"❌ CLI版実行エラー: {e}")
        safe_print("必要なモジュールが見つかりません")
        return 1
    except Exception as e:
        safe_print(f"❌ 予期しないエラー: {e}")
        return 1


def main():
    """メインエントリーポイント"""
    print_environment_info()
    
    # コマンドライン引数の解析
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--cli', '-c']:
            return run_cli()
        elif sys.argv[1] in ['--help', '-h']:
            print_help()
            return 0
    
    # WSL環境での自動CLI切り替え
    if is_wsl and not pyqt6_available:
        safe_print("WSL環境でPyQt6が利用できません。CLIモードで実行します。")
        return run_cli()
    
    # デフォルトはGUI版
    return run_gui()


def print_help():
    """ヘルプメッセージを表示"""
    help_text = """
PJINIT - 技術の泉シリーズプロジェクト初期化ツール v1.2 (Phase 1リファクタリング版)

使用方法:
  python main_refactored.py [OPTIONS]

オプション:
  --cli, -c     CLIモードで実行
  --help, -h    このヘルプを表示

機能:
  - Google Sheetsからプロジェクト情報を取得
  - Slackチャンネルの自動作成
  - GitHubリポジトリの自動作成
  - TechBridge統合による一元管理

環境要件:
  - Python 3.8+
  - PyQt6 (GUI版)
  - TechBridge services (optional)

詳細な設定方法はCLAUDE.mdを参照してください。
"""
    safe_print(help_text)


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        safe_print("\\n中断されました")
        sys.exit(130)
    except Exception as e:
        safe_print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)