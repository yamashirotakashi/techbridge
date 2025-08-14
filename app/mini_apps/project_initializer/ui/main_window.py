"""
PJINIT メインウィンドウUI
Phase 1リファクタリング: UI層の分離
"""

import os
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QGridLayout,
    QCheckBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction


class ProjectInitializerWindow(QMainWindow):
    """メインウィンドウ - UI層のみに特化"""
    
    # UIイベントシグナル
    project_info_requested = pyqtSignal(str)  # Nコード
    initialization_requested = pyqtSignal(dict)  # パラメータ
    settings_save_requested = pyqtSignal(dict)  # 設定
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("技術の泉シリーズプロジェクト初期化ツール v1.2")
        self.setGeometry(100, 100, 1000, 700)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # レイアウト
        layout = QVBoxLayout(main_widget)
        
        # タブウィジェット
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # 初期化タブ
        init_tab = self._create_init_tab()
        tabs.addTab(init_tab, "プロジェクト初期化")
        
        # 設定タブ
        settings_tab = self._create_settings_tab()
        tabs.addTab(settings_tab, "設定")
        
        # ステータスバー
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # メニューバー
        self._create_menu_bar()
    
    def _create_init_tab(self):
        """初期化タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Nコード入力
        input_group = QGroupBox("プロジェクト情報")
        input_layout = QGridLayout()
        
        input_layout.addWidget(QLabel("Nコード:"), 0, 0)
        self.n_code_input = QLineEdit()
        self.n_code_input.setPlaceholderText("例: N09999")
        input_layout.addWidget(self.n_code_input, 0, 1)
        
        self.check_button = QPushButton("情報確認")
        self.check_button.clicked.connect(self._on_check_project_info)
        input_layout.addWidget(self.check_button, 0, 2)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # プロジェクト情報表示
        info_group = QGroupBox("確認結果")
        info_layout = QGridLayout()
        
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setMinimumHeight(200)
        self.info_display.setMaximumHeight(300)
        info_layout.addWidget(self.info_display, 0, 0, 1, 2)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 実行オプション
        options_group = QGroupBox("実行オプション")
        options_layout = QVBoxLayout()
        
        self.create_slack_cb = QCheckBox("Slackチャンネルを作成")
        self.create_slack_cb.setChecked(True)
        options_layout.addWidget(self.create_slack_cb)
        
        self.create_github_cb = QCheckBox("GitHubリポジトリを作成")
        self.create_github_cb.setChecked(True)
        options_layout.addWidget(self.create_github_cb)
        
        self.update_sheets_cb = QCheckBox("Google Sheetsを更新")
        self.update_sheets_cb.setChecked(True)
        options_layout.addWidget(self.update_sheets_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 実行ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.execute_button = QPushButton("プロジェクト初期化実行")
        self.execute_button.clicked.connect(self._on_execute_initialization)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button)
        
        layout.addLayout(button_layout)
        
        # ログ表示
        log_group = QGroupBox("実行ログ")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
    
    def _create_settings_tab(self):
        """設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API設定
        api_group = QGroupBox("API設定")
        api_layout = QGridLayout()
        
        # Slack Bot Token
        api_layout.addWidget(QLabel("Slack Bot Token:"), 0, 0)
        self.slack_token_input = QLineEdit()
        # Remove password masking as requested by user
        # self.slack_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.slack_token_input, 0, 1)
        
        # Slack User Token (new)
        api_layout.addWidget(QLabel("Slack User Token:"), 1, 0)
        self.slack_user_token_input = QLineEdit()
        self.slack_user_token_input.setPlaceholderText("xoxp-... (プライベートチャンネル作成用)")
        api_layout.addWidget(self.slack_user_token_input, 1, 1)
        
        # Slack Invitation Bot Token (招待Bot専用)
        api_layout.addWidget(QLabel("Slack Invitation Bot Token:"), 2, 0)
        self.slack_invitation_token_input = QLineEdit()
        self.slack_invitation_token_input.setPlaceholderText("xoxb-... (招待Bot用)")
        api_layout.addWidget(self.slack_invitation_token_input, 2, 1)
        
        # GitHub Token
        api_layout.addWidget(QLabel("GitHub Token:"), 3, 0)
        self.github_token_input = QLineEdit()
        api_layout.addWidget(self.github_token_input, 3, 1)
        
        # GitHub Organization Token
        api_layout.addWidget(QLabel("GitHub Org Token:"), 4, 0)
        self.github_org_token_input = QLineEdit()
        self.github_org_token_input.setPlaceholderText("ghp-... (組織用トークン)")
        api_layout.addWidget(self.github_org_token_input, 4, 1)
        
        # Slack Signing Secret
        api_layout.addWidget(QLabel("Slack Signing Secret:"), 5, 0)
        self.slack_signing_secret_input = QLineEdit()
        api_layout.addWidget(self.slack_signing_secret_input, 5, 1)
        
        # Slack Client ID & Secret
        api_layout.addWidget(QLabel("Slack Client ID:"), 6, 0)
        self.slack_client_id_input = QLineEdit()
        api_layout.addWidget(self.slack_client_id_input, 6, 1)
        
        api_layout.addWidget(QLabel("Slack Client Secret:"), 7, 0)
        self.slack_client_secret_input = QLineEdit()
        api_layout.addWidget(self.slack_client_secret_input, 7, 1)
        
        # Google Service Account Key Path
        api_layout.addWidget(QLabel("Google Service Account Key:"), 8, 0)
        self.google_service_key_input = QLineEdit()
        self.google_service_key_input.setPlaceholderText("Path to service account JSON file")
        api_layout.addWidget(self.google_service_key_input, 8, 1)
        
        # Google Sheets ID
        api_layout.addWidget(QLabel("発行計画シートID:"), 9, 0)
        self.planning_sheet_input = QLineEdit()
        api_layout.addWidget(self.planning_sheet_input, 9, 1)
        
        api_layout.addWidget(QLabel("購入リストシートID:"), 10, 0)
        self.purchase_sheet_input = QLineEdit()
        api_layout.addWidget(self.purchase_sheet_input, 10, 1)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 保存ボタン
        save_button = QPushButton("設定を保存")
        save_button.clicked.connect(self._on_save_settings)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
        return widget
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        about_action = QAction("このツールについて", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_settings(self):
        """設定を読み込み"""
        # 環境変数から読み込み
        self.slack_token_input.setText(os.getenv("SLACK_BOT_TOKEN", ""))
        self.slack_user_token_input.setText(os.getenv("SLACK_USER_TOKEN", ""))
        self.slack_invitation_token_input.setText(os.getenv("SLACK_INVITATION_BOT_TOKEN", ""))
        self.github_token_input.setText(os.getenv("GITHUB_TOKEN", ""))
        self.github_org_token_input.setText(os.getenv("GITHUB_ORG_TOKEN", ""))
        self.slack_signing_secret_input.setText(os.getenv("SLACK_SIGNING_SECRET", ""))
        self.slack_client_id_input.setText(os.getenv("SLACK_CLIENT_ID", ""))
        self.slack_client_secret_input.setText(os.getenv("SLACK_CLIENT_SECRET", ""))
        self.google_service_key_input.setText(os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", ""))
        self.planning_sheet_input.setText("17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ")
        self.purchase_sheet_input.setText("1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c")
    
    def _on_check_project_info(self):
        """プロジェクト情報確認のUIイベントハンドラ"""
        n_code = self.n_code_input.text().strip()
        if not n_code:
            QMessageBox.warning(self, "エラー", "Nコードを入力してください")
            return
        
        # ビジネスロジック層にシグナル送信
        self.project_info_requested.emit(n_code)
    
    def _on_execute_initialization(self):
        """プロジェクト初期化実行のUIイベントハンドラ"""
        params = self._collect_parameters()
        self.initialization_requested.emit(params)
    
    def _on_save_settings(self):
        """設定保存のUIイベントハンドラ"""
        settings = {
            'slack_token': self.slack_token_input.text(),
            'slack_user_token': self.slack_user_token_input.text(),
            'slack_invitation_token': self.slack_invitation_token_input.text(),
            'github_token': self.github_token_input.text(),
            'github_org_token': self.github_org_token_input.text(),
            'slack_signing_secret': self.slack_signing_secret_input.text(),
            'slack_client_id': self.slack_client_id_input.text(),
            'slack_client_secret': self.slack_client_secret_input.text(),
            'google_service_key': self.google_service_key_input.text(),
            'planning_sheet_id': self.planning_sheet_input.text(),
            'purchase_sheet_id': self.purchase_sheet_input.text()
        }
        self.settings_save_requested.emit(settings)
        QMessageBox.information(self, "設定保存", "設定を保存しました")
    
    def _collect_parameters(self) -> dict:
        """UIから実行パラメータを収集"""
        return {
            'n_code': self.n_code_input.text().strip(),
            'create_slack_channel': self.create_slack_cb.isChecked(),
            'create_github_repo': self.create_github_cb.isChecked(),
            'update_google_sheets': self.update_sheets_cb.isChecked(),
            'slack_token': self.slack_token_input.text(),
            'slack_user_token': self.slack_user_token_input.text(),
            'slack_invitation_token': self.slack_invitation_token_input.text(),
            'github_token': self.github_token_input.text(),
            'github_org_token': self.github_org_token_input.text(),
            'slack_signing_secret': self.slack_signing_secret_input.text(),
            'slack_client_id': self.slack_client_id_input.text(),
            'slack_client_secret': self.slack_client_secret_input.text(),
            'google_service_key': self.google_service_key_input.text(),
            'planning_sheet_id': self.planning_sheet_input.text(),
            'purchase_sheet_id': self.purchase_sheet_input.text()
        }
    
    def display_project_info(self, project_info: Dict[str, Any]):
        """プロジェクト情報をUIに表示"""
        info_text = f"""プロジェクト情報:
タイトル: {project_info.get('book_title', 'N/A')}
リポジトリ名: {project_info.get('repository_name', 'N/A')}
著者: {project_info.get('author', 'N/A')}
Slack Channel: {project_info.get('slack_channel', 'N/A')}
購入URL: {project_info.get('book_url_from_purchase', '見つかりませんでした')}
"""
        self.info_display.setPlainText(info_text)
        self.execute_button.setEnabled(True)
    
    def display_error(self, error_message: str):
        """エラーメッセージをUIに表示"""
        self.info_display.setPlainText(f"エラー: {error_message}")
        self.execute_button.setEnabled(False)
        QMessageBox.warning(self, "エラー", error_message)
    
    def append_log(self, message: str):
        """ログメッセージをUIに追加"""
        self.log_display.append(message)
    
    def clear_log(self):
        """ログをクリア"""
        self.log_display.clear()
    
    def set_progress_visible(self, visible: bool):
        """プログレスバーの表示制御"""
        self.progress_bar.setVisible(visible)
    
    def set_progress_value(self, value: int):
        """プログレスバーの値設定"""
        self.progress_bar.setValue(value)
    
    def set_status_message(self, message: str):
        """ステータスバーのメッセージ設定"""
        self.status_bar.showMessage(message)
    
    def show_about(self):
        """Aboutダイアログ表示"""
        QMessageBox.about(self, "このツールについて", 
            "技術の泉シリーズプロジェクト初期化ツール v1.2\n"
            "TechBridge統合版")
    
    def closeEvent(self, event):
        """ウィンドウクローズイベント"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, '確認', 
                                       '実行中のタスクがあります。終了してもよろしいですか？',
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.worker:
                    self.worker.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()