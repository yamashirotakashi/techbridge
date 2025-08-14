"""
PJINIT アプリケーション制御層
Phase 1リファクタリング: アプリケーション層の分離
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSlot

# 絶対インポート（相対インポート問題の回避）
try:
    from ui.main_window import ProjectInitializerWindow
    from core.project_initializer import ProjectInitializer
    from utils.environment import is_wsl, safe_print
except ImportError:
    # パッケージ構造が異なる場合のフォールバック
    import sys
    from pathlib import Path
    
    # 現在のディレクトリを基準にしてインポートパスを修正
    current_dir = Path(__file__).parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
        
    from ui.main_window import ProjectInitializerWindow
    from core.project_initializer import ProjectInitializer
    from utils.environment import is_wsl, safe_print


class ApplicationController(QObject):
    """アプリケーション制御層 - UIとビジネスロジックの仲介"""
    
    def __init__(self):
        super().__init__()
        self.window: Optional[ProjectInitializerWindow] = None
        self.project_initializer: Optional[ProjectInitializer] = None
        self._current_project_info: Optional[Dict[str, Any]] = None
    
    def initialize(self):
        """アプリケーションの初期化"""
        try:
            # メインウィンドウの作成
            self.window = ProjectInitializerWindow()
            
            # シグナル・スロットの接続
            self._connect_signals()
            
            # ProjectInitializerの初期化
            self.project_initializer = ProjectInitializer()
            
            safe_print("✅ アプリケーション初期化完了")
            return True
            
        except Exception as e:
            safe_print(f"❌ アプリケーション初期化失敗: {e}")
            return False
    
    def _connect_signals(self):
        """UIシグナルとスロットを接続"""
        if self.window:
            # プロジェクト情報確認
            self.window.project_info_requested.connect(self._handle_project_info_request)
            
            # プロジェクト初期化実行
            self.window.initialization_requested.connect(self._handle_initialization_request)
            
            # 設定保存
            self.window.settings_save_requested.connect(self._handle_settings_save)
    
    @pyqtSlot(str)
    def _handle_project_info_request(self, n_code: str):
        """プロジェクト情報確認のハンドラ"""
        try:
            if self.window:
                self.window.set_status_message("プロジェクト情報を確認中...")
                self.window.clear_log()
                
            # ビジネスロジック層に処理を委譲
            project_info = asyncio.run(self._fetch_project_info_async(n_code))
            
            if project_info:
                self._current_project_info = project_info
                if self.window:
                    self.window.display_project_info(project_info)
                    self.window.set_status_message("プロジェクト情報確認完了")
            else:
                if self.window:
                    self.window.display_error(f"Nコード {n_code} の情報が見つかりません")
                    self.window.set_status_message("プロジェクト情報確認失敗")
                    
        except Exception as e:
            error_msg = f"プロジェクト情報確認エラー: {str(e)}"
            if self.window:
                self.window.display_error(error_msg)
                self.window.set_status_message("エラー発生")
            safe_print(f"❌ {error_msg}")
    
    async def _fetch_project_info_async(self, n_code: str) -> Optional[Dict[str, Any]]:
        """非同期でプロジェクト情報を取得"""
        if not self.project_initializer:
            return None
        
        try:
            # Google Sheetsから情報を取得
            project_info = await self.project_initializer.fetch_project_info(n_code)
            return project_info
            
        except Exception as e:
            safe_print(f"❌ プロジェクト情報取得失敗: {e}")
            return None
    
    @pyqtSlot(dict)
    def _handle_initialization_request(self, params: Dict[str, Any]):
        """プロジェクト初期化実行のハンドラ"""
        try:
            if not self._current_project_info:
                if self.window:
                    self.window.display_error("先にプロジェクト情報を確認してください")
                return
            
            if self.window:
                self.window.set_status_message("プロジェクト初期化実行中...")
                self.window.set_progress_visible(True)
                self.window.append_log("=== プロジェクト初期化開始 ===")
            
            # ビジネスロジック層に処理を委譲
            result = asyncio.run(self._execute_initialization_async(params))
            
            if result.get('success', False):
                if self.window:
                    self.window.append_log("=== プロジェクト初期化完了 ===")
                    self.window.set_status_message("プロジェクト初期化完了")
                    
                    # 手動タスクがある場合は表示
                    manual_tasks = result.get('manual_tasks', [])
                    if manual_tasks:
                        self._show_manual_tasks(manual_tasks)
            else:
                error_msg = result.get('error', '不明なエラー')
                if self.window:
                    self.window.append_log(f"❌ エラー: {error_msg}")
                    self.window.set_status_message("プロジェクト初期化失敗")
                
        except Exception as e:
            error_msg = f"プロジェクト初期化エラー: {str(e)}"
            if self.window:
                self.window.append_log(f"❌ {error_msg}")
                self.window.set_status_message("エラー発生")
            safe_print(f"❌ {error_msg}")
            
        finally:
            if self.window:
                self.window.set_progress_visible(False)
    
    async def _execute_initialization_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """非同期でプロジェクト初期化を実行"""
        if not self.project_initializer or not self._current_project_info:
            return {'success': False, 'error': 'プロジェクト初期化の準備ができていません'}
        
        try:
            # パラメータにプロジェクト情報を追加
            full_params = {**params, 'project_info': self._current_project_info}
            
            # プログレス更新のコールバック設定
            def progress_callback(message: str):
                if self.window:
                    self.window.append_log(message)
            
            # ビジネスロジック実行
            result = await self.project_initializer.initialize_project(
                full_params, 
                progress_callback=progress_callback
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _show_manual_tasks(self, manual_tasks: list):
        """手動タスクの表示"""
        if not manual_tasks or not self.window:
            return
        
        task_text = "以下のタスクを手動で実行してください:\\n\\n"
        for i, task in enumerate(manual_tasks, 1):
            task_text += f"{i}. {task.get('description', '不明なタスク')}\\n"
        
        QMessageBox.information(self.window, "手動タスク", task_text)
    
    @pyqtSlot(dict)
    def _handle_settings_save(self, settings: Dict[str, Any]):
        """設定保存のハンドラ"""
        try:
            # 設定をファイルまたは環境変数に保存
            # 現在は環境変数への反映のみ実装
            os.environ['SLACK_BOT_TOKEN'] = settings.get('slack_token', '')
            os.environ['GITHUB_ORG_TOKEN'] = settings.get('github_token', '')
            
            if self.window:
                self.window.set_status_message("設定を保存しました")
            
            safe_print("✅ 設定保存完了")
            
        except Exception as e:
            error_msg = f"設定保存エラー: {str(e)}"
            if self.window:
                self.window.set_status_message("設定保存失敗")
            safe_print(f"❌ {error_msg}")
    
    def show_window(self):
        """メインウィンドウを表示"""
        if self.window:
            self.window.show()
    
    def run(self) -> int:
        """アプリケーションを実行"""
        if not self.window:
            safe_print("❌ ウィンドウが初期化されていません")
            return 1
        
        # ウィンドウを表示
        self.show_window()
        
        # アプリケーションのメインループ開始
        app = QApplication.instance()
        if app:
            return app.exec()
        else:
            safe_print("❌ QApplicationインスタンスが見つかりません")
            return 1