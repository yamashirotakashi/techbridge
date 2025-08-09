"""
TechWF Dialog Manager

Phase 3 Refactoring: ダイアログ操作とメッセージ表示を専門に管理するクラス
設定ダイアログ、詳細表示、About表示、汎用ダイアログ処理を統合管理

Author: Claude (Serena MCP)
Created: 2025-08-04
"""

import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QDialog

logger = logging.getLogger(__name__)


class DialogManager(QObject):
    """
    ダイアログ管理クラス
    
    各種ダイアログの表示と管理を統合的に処理し、
    メインウィンドウから複雑なダイアログ処理ロジックを分離
    """
    
    # ダイアログ操作シグナル
    settings_changed = Signal()           # 設定変更通知
    dialog_error = Signal(str, str)       # ダイアログエラー(dialog_type, error_message)
    
    def __init__(self, main_window, parent=None):
        """
        DialogManagerの初期化
        
        Args:
            main_window: メインウィンドウインスタンス
            parent: 親オブジェクト
        """
        super().__init__(parent)
        
        self.main_window = main_window
        
        logger.info("DialogManager初期化完了")
    
    def handle_dialog_request(self, dialog_type: str, data: dict):
        """
        EventHandlerServiceからのダイアログ表示リクエストを処理
        
        Args:
            dialog_type: ダイアログタイプ ('warning', 'error', 'info', 'question')
            data: ダイアログ表示データ (title, message, etc.)
        
        Returns:
            questionダイアログの場合はTrue/False、その他の場合はNone
        """
        try:
            if dialog_type == "warning":
                QMessageBox.warning(self.main_window, data.get("title", "警告"), data.get("message", ""))
                return None
            elif dialog_type == "error":
                QMessageBox.critical(self.main_window, data.get("title", "エラー"), data.get("message", ""))
                return None
            elif dialog_type == "info":
                QMessageBox.information(self.main_window, data.get("title", "情報"), data.get("message", ""))
                return None
            elif dialog_type == "question":
                reply = QMessageBox.question(
                    self.main_window, 
                    data.get("title", "確認"), 
                    data.get("message", ""),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                return reply == QMessageBox.Yes
            else:
                logger.warning(f"未知のダイアログタイプ: {dialog_type}")
                return None
                
        except Exception as e:
            logger.error(f"ダイアログ表示エラー ({dialog_type}): {e}")
            self.dialog_error.emit(dialog_type, str(e))
            return None

    def show_workflow_details(self, n_number: str):
        """
        ワークフロー詳細ダイアログ表示（簡略化版）
        Phase 3 Refactoring: UI詳細表示の簡略化
        
        Args:
            n_number: 表示対象のN番号
        """
        try:
            workflow = self.main_window.workflow_controller.get_workflow_by_n_number(n_number)
            if not workflow:
                QMessageBox.warning(self.main_window, "データエラー", f"ワークフロー {n_number} が見つかりません")
                return
            
            # 簡略化された詳細表示
            details = f"""
            書籍名: {workflow.book_title}
            著者名: {workflow.author_name}
            現在ステータス: {workflow.current_status}
            次のタスク: {workflow.next_task or '未設定'}
            締切日: {workflow.due_date.strftime('%Y年%m月%d日') if workflow.due_date else '未設定'}
            優先度: {workflow.get_priority_label()}
            """
            
            QMessageBox.information(self.main_window, f"詳細情報 - {workflow.book_title}", details)
            
            logger.info(f"ワークフロー詳細表示: {n_number}")
            
        except Exception as e:
            logger.error(f"詳細表示エラー: {e}")
            self.dialog_error.emit("workflow_details", str(e))
            QMessageBox.critical(self.main_window, "エラー", f"詳細情報の表示に失敗しました:\n{e}")

    def show_about(self):
        """
        バージョン情報表示
        """
        try:
            about_text = """
            <h2>TechWF v0.5</h2>
            <p><b>技術書出版進行管理システム</b></p>
            <p>技術書典商業化タブのパターンを踏襲した進行管理ツール</p>
            <hr>
            <p><b>機能:</b></p>
            <ul>
            <li>Google Sheets双方向同期</li>
            <li>Slack自動投稿</li>
            <li>TechGate連携</li>
            <li>進捗統計表示</li>
            </ul>
            <p><small>© 2025 TechBridge Project</small></p>
            """
            QMessageBox.about(self.main_window, "TechWF v0.5について", about_text)
            
            logger.info("About ダイアログ表示")
            
        except Exception as e:
            logger.error(f"About ダイアログエラー: {e}")
            self.dialog_error.emit("about", str(e))

    def show_settings(self):
        """
        設定ダイアログ表示
        """
        try:
            from .comprehensive_settings_dialog import SettingsDialog
            
            dialog = SettingsDialog(self.main_window.config_service, self.main_window)
            dialog.settings_changed.connect(self._on_dialog_settings_changed)
            
            if dialog.exec() == QDialog.Accepted:
                logger.info("設定変更が適用されました")
                return True
            else:
                logger.info("設定変更がキャンセルされました")
                return False
            
        except Exception as e:
            logger.error(f"設定ダイアログエラー: {e}")
            self.dialog_error.emit("settings", str(e))
            QMessageBox.critical(self.main_window, "設定エラー", f"設定画面の表示に失敗しました:\n{e}")
            return False
    
    def _on_dialog_settings_changed(self):
        """
        設定ダイアログからの設定変更通知ハンドラー
        """
        try:
            logger.info("DialogManager: 設定変更通知受信")
            self.settings_changed.emit()
            
        except Exception as e:
            logger.error(f"設定変更通知処理エラー: {e}")
            self.dialog_error.emit("settings_change", str(e))
    
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """
        確認ダイアログの表示
        
        Args:
            title: ダイアログタイトル
            message: 確認メッセージ
        
        Returns:
            ユーザーの選択結果（Yes=True, No=False）
        """
        try:
            reply = QMessageBox.question(
                self.main_window,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
            
        except Exception as e:
            logger.error(f"確認ダイアログエラー: {e}")
            self.dialog_error.emit("confirmation", str(e))
            return False
    
    def show_error_dialog(self, title: str, message: str):
        """
        エラーダイアログの表示
        
        Args:
            title: ダイアログタイトル
            message: エラーメッセージ
        """
        try:
            QMessageBox.critical(self.main_window, title, message)
            
        except Exception as e:
            logger.error(f"エラーダイアログ表示エラー: {e}")
    
    def show_info_dialog(self, title: str, message: str):
        """
        情報ダイアログの表示
        
        Args:
            title: ダイアログタイトル
            message: 情報メッセージ
        """
        try:
            QMessageBox.information(self.main_window, title, message)
            
        except Exception as e:
            logger.error(f"情報ダイアログ表示エラー: {e}")
    
    def show_warning_dialog(self, title: str, message: str):
        """
        警告ダイアログの表示
        
        Args:
            title: ダイアログタイトル
            message: 警告メッセージ
        """
        try:
            QMessageBox.warning(self.main_window, title, message)
            
        except Exception as e:
            logger.error(f"警告ダイアログ表示エラー: {e}")