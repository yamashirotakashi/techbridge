#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF v0.5 メインウィンドウ
技術書典商業化タブのUIパターンを踏襲したQt6実装
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QHeaderView, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QLabel, QProgressBar, QSplitter, QFrame, QDialog, QFormLayout, QTextEdit,
    QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QAction, QIcon, QFont, QColor, QPixmap
from typing import List, Optional, Dict, Any
import logging
import webbrowser
from datetime import datetime, date

from ..repositories.publication_repository import PublicationRepository
from ..models.publication_workflow import PublicationWorkflowDTO
from ..services.config_service import get_config_service, ConfigService
from ..services.google_sheets_service import GoogleSheetsService, GoogleSheetsError
from ..services.slack_service import SlackService, SlackError, SlackMessageTemplate
from .theme import ThemeManager, TechWFTheme, TableColumns
from .theme_applicator import ThemeApplicator
from ..controllers.workflow_controller import WorkflowController
from .ui_state_manager import UIStateManager

logger = logging.getLogger(__name__)

from pathlib import Path

class TechWFMainWindow(QMainWindow):
    """
    TechWF v0.5 メインウィンドウクラス
    技術書典商業化タブのパターンを踏襲した5カラム表示
    """
    
    # シグナル定義
    status_updated = Signal(str)  # ステータス更新
    data_changed = Signal()       # データ変更
    
    def __init__(self, db_path: str):
        """
        メインウィンドウの初期化
        
        Args:
            db_path: データベースファイルパス
        """
        super().__init__()
        
        # === Phase 3 Refactoring: ThemeApplicator導入 ===
        # テーマ管理をThemeApplicatorに委譲
        self.theme_applicator = ThemeApplicator(self)
        self.theme = self.theme_applicator.get_current_theme()
        
        # データベースリポジトリ初期化
        try:
            self.repository = PublicationRepository(db_path)
            logger.info(f"データベース接続完了: {db_path}")
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            QMessageBox.critical(self, "データベースエラー", 
                               f"データベースに接続できません:\n{e}")
            return
        
        # 設定サービス初期化
        self.config_service = get_config_service()
        
        # === Phase 3 Refactoring: ServiceManager導入 ===
        # サービス管理をServiceManagerに委譲
        from .service_manager import ServiceManager
        self.service_manager = ServiceManager(self)
        self.service_manager.initialize_all_services()
        
        # ServiceManagerからサービス参照を取得
        self.sheets_service = self.service_manager.get_sheets_service()
        self.slack_service = self.service_manager.get_slack_service()
        
        # === Phase 3 Refactoring: EventCoordinator導入 ===
        # イベント処理をEventCoordinatorに委譲
        from .event_coordinator import EventCoordinator
        self.event_coordinator = EventCoordinator(self, self)
        
        # === Phase 3 Refactoring: DialogManager導入 ===
        # ダイアログ処理をDialogManagerに委譲
        from .dialog_manager import DialogManager
        self.dialog_manager = DialogManager(self, self)
        
        # === Phase 3 Refactoring: MenuBarManager導入 ===
        # メニューバー・ステータスバー管理をMenuBarManagerに委譲
        from .menu_bar_manager import MenuBarManager
        self.menu_bar_manager = MenuBarManager(self, self.theme, self)
        
        # コントローラー初期化（進捗コールバック付き）
        self.controller = WorkflowController(
            repository=self.repository,
            config_service=self.config_service,
            sheets_service=self.sheets_service,
            slack_service=self.slack_service,
            progress_callback=None
        )
        
        # ソケットサーバー初期化（技術書典スクレイパーからの転記受付）
        from ..services.socket_server import SocketServerService
        self.socket_server = SocketServerService(
            self.repository, 
            data_changed_callback=lambda: self.data_changed.emit()
        )
        self.socket_server.start()
        
        # === 新機能: FileWatcherService統合 ===
        # 外部システム連携用ファイル監視サービス
        from ..services.file_watcher_service import FileWatcherService
        from ..services.tsv_import_service import TSVImportService
        
        # TSVImportService初期化
        self.tsv_import_service = TSVImportService(
            repository=self.repository,
            sheets_service=self.sheets_service
        )
        
        # FileWatcherService初期化
        self.file_watcher_service = FileWatcherService(
            tsv_import_service=self.tsv_import_service
        )
        
        # FileWatcherServiceシグナル接続
        self.file_watcher_service.file_imported.connect(self._on_external_data_imported)
        self.file_watcher_service.import_error.connect(self._on_external_data_error)
        self.file_watcher_service.import_started.connect(self._on_external_data_started)
        
        logger.info(f"外部システム連携監視開始: {self.file_watcher_service.get_watch_directory()}")
        
        # UI状態管理初期化
        self.ui_manager = UIStateManager(self.theme)
        
        # === Phase 1 Refactoring: UIComponentManager導入 ===
        # UIComponentManager初期化（UI作成ロジック分離）
        from . import UIComponentManager
        self.ui_component_manager = UIComponentManager(self.theme, self)
        
        # === Phase 2 Refactoring: EventHandlerService導入 ===
        # EventHandlerService初期化（イベント処理ロジック分離）
        from . import EventHandlerService
        self.event_handler = EventHandlerService(self, self)
        
        # === Phase 4 Refactoring: DataBindingManager導入 ===
        # DataBindingManager初期化（データバインディング・同期ロジック分離）
        from .ui_state_manager import DataBindingManager
        self.data_binding_manager = DataBindingManager(
            controller=self.controller,
            ui_manager=self.ui_manager,
            progress_callback=self._update_progress,
            parent=self
        )
        
        # ServiceManagerシグナル接続
        self.service_manager.sheets_service_changed.connect(self._update_sync_button_states)
        self.service_manager.slack_service_changed.connect(self._update_slack_button_states)
        self.service_manager.service_error.connect(self._on_service_error)
        self.service_manager.service_initialized.connect(self._on_service_initialized)
        
        # EventHandlerServiceシグナル接続
        self.event_handler.status_update_requested.connect(self.status_updated.emit)
        self.event_handler.data_refresh_requested.connect(self._on_data_refresh_requested)
        self.event_handler.dialog_show_requested.connect(self._handle_dialog_request)
        
        # DataBindingManagerシグナル接続
        self.data_binding_manager.data_loaded.connect(self._on_data_loaded)
        self.data_binding_manager.data_sync_completed.connect(self._on_sync_completed)
        self.data_binding_manager.data_error.connect(self._on_data_error)
        self.data_binding_manager.binding_updated.connect(self._on_binding_updated)
        self.data_binding_manager.progress_updated.connect(self._on_progress_updated)
        
        # UIComponentManagerシグナル接続（EventHandlerService経由）
        self.ui_component_manager.sync_from_sheet_requested.connect(self.event_handler.handle_sync_from_sheet)
        self.ui_component_manager.sync_to_sheet_requested.connect(self.event_handler.handle_sync_to_sheet)
        self.ui_component_manager.slack_post_requested.connect(self.event_handler.handle_post_to_slack)
        self.ui_component_manager.techzip_launch_requested.connect(self.event_handler.handle_launch_techzip)
        self.ui_component_manager.pjinit_launch_requested.connect(self.event_handler.handle_launch_pjinit)
        self.ui_component_manager.refresh_requested.connect(self._on_data_refresh_requested)
        
        # UI要素の参照保持（UIComponentManagerから取得）
        self.workflow_table = None
        self.status_bar = None
        self.progress_bar = None
        self.sync_buttons = {}
        
        # 自動更新タイマー
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_data_refresh_requested)
        
        # === UI初期化（UIComponentManager使用） ===
        # メインUIセットアップ
        self.ui_component_manager.setup_main_ui(self)
        
        # UIComponentManagerから作成されたウィジェット参照を取得
        self.workflow_table = self.ui_component_manager.get_workflow_table()
        self.sync_buttons = self.ui_component_manager.get_sync_buttons()
        
        # === Phase 4: 監視ダッシュボード統合 ===
        self._integrate_monitor_dashboard()
        
        # === Phase 3 Refactoring: MenuBarManagerでメニューバー・ステータスバー設定 ===
        self.menu_bar_manager.setup_menu_bar()
        self.menu_bar_manager.setup_status_bar()
        
        # MenuBarManagerから作成されたウィジェット参照を取得
        self.status_bar = self.menu_bar_manager.get_status_bar()
        self.progress_bar = self.menu_bar_manager.get_progress_bar()
        
        # UI管理クラスにウィジェット登録
        self.ui_manager.set_table_widget(self.workflow_table)
        self.ui_manager.set_progress_bar(self.progress_bar)
        
        # シグナル接続
        self.setup_signals()
        
        # 初期データ読み込み（DataBindingManager経由）
        self.data_binding_manager.load_initial_data()
        
        # === Phase 4: 監視サービス初期化 ===
        self._initialize_monitor_services()
        
        logger.info("TechWF メインウィンドウ初期化完了 - Phase 4 監視ダッシュボード統合 + 外部システム連携")

    def _initialize_sheets_service(self):
        """
        Google Sheetsサービスの初期化 (ServiceManager経由)
        Phase 3 Refactoring: ServiceManagerに移行済み
        """
        # ServiceManagerが処理するため、削除予定のメソッド
        pass

    def _update_sync_button_states(self, enabled: bool):
        """
        同期ボタンの状態更新 (ServiceManager経由)
        Phase 3 Refactoring: ServiceManagerに移行済み
        
        Args:
            enabled: 有効・無効
        """
        if hasattr(self, 'sync_buttons'):
            self.sync_buttons['from_sheet'].setEnabled(enabled)
            self.sync_buttons['to_sheet'].setEnabled(enabled)
            
            if enabled:
                self.sync_buttons['from_sheet'].setToolTip("Google Sheetsからデータを取得")
                self.sync_buttons['to_sheet'].setToolTip("Google Sheetsにデータを転記")
            else:
                self.sync_buttons['from_sheet'].setToolTip("Google Sheets設定が無効または未設定")
                self.sync_buttons['to_sheet'].setToolTip("Google Sheets設定が無効または未設定")

    def _initialize_slack_service(self):
        """
        Slackサービスの初期化 (ServiceManager経由)
        Phase 3 Refactoring: ServiceManagerに移行済み
        """
        # ServiceManagerが処理するため、削除予定のメソッド
        pass

    def _update_slack_button_states(self, enabled: bool):
        """
        Slackボタンの状態更新 (ServiceManager経由)
        Phase 3 Refactoring: ServiceManagerに移行済み
        
        Args:
            enabled: 有効・無効
        """
        # Slackボタンが作成されていれば状態更新
        if hasattr(self, 'slack_button'):
            self.slack_button.setEnabled(enabled)
            
            if enabled:
                self.slack_button.setToolTip("選択した著者にSlackメッセージを送信")
            else:
                self.slack_button.setToolTip("Slack設定が無効または未設定")


    def setup_menu_bar(self):
        """Phase 3 Refactoring: MenuBarManagerに移行済み"""
        if hasattr(self, 'menu_bar_manager'):
            self.menu_bar_manager.setup_menu_bar()


    def setup_status_bar(self):
        """Phase 3 Refactoring: MenuBarManagerに移行済み"""
        if hasattr(self, 'menu_bar_manager'):
            self.menu_bar_manager.setup_status_bar()

    def setup_signals(self):
        """
        シグナル・スロット接続 (全Manager経由)
        
        Phase 3 Refactoring: 全Managerを使用した統合シグナル接続
        """
        # EventCoordinatorでシグナル接続を実行
        self.event_coordinator.setup_signals()
        
        # EventCoordinatorからのシグナル接続
        self.event_coordinator.selection_changed.connect(self.on_selection_changed)
        self.event_coordinator.status_update_requested.connect(self.status_updated.emit)
        
        # DialogManagerシグナル接続
        self.dialog_manager.settings_changed.connect(self._on_settings_changed)
        self.dialog_manager.dialog_error.connect(self._on_dialog_error)
        
        # MenuBarManagerシグナル接続
        self.menu_bar_manager.settings_requested.connect(self._on_settings_requested)
        self.menu_bar_manager.about_requested.connect(self._on_about_requested)
        self.menu_bar_manager.data_export_requested.connect(self._on_data_export_requested)
        self.menu_bar_manager.tsv_import_requested.connect(self._on_tsv_import_requested)
        self.menu_bar_manager.status_message_changed.connect(self.status_updated.emit)
        
        logger.info("Phase 3 Refactoring: 全Manager経由でシグナル接続完了")

    def load_initial_data(self):
        """
        初期データ読み込み（DataBindingManager経由）
        Phase 4 Refactoring: DataBindingManagerに委譲
        """
        self.data_binding_manager.load_initial_data()

    def refresh_data(self):
        """
        データの更新（DataBindingManager経由）
        Phase 4 Refactoring: DataBindingManagerに委譲
        """
        self.data_binding_manager.refresh_data()

    def _handle_dialog_request(self, dialog_type: str, data: dict):
        """
        EventHandlerServiceからのダイアログ表示リクエストを処理 (DialogManager経由)
        Phase 3 Refactoring: DialogManagerに移行済み
        
        Args:
            dialog_type: ダイアログタイプ ('warning', 'error', 'info', 'question')
            data: ダイアログ表示データ (title, message, etc.)
        """
        if hasattr(self, 'dialog_manager'):
            return self.dialog_manager.handle_dialog_request(dialog_type, data)
        else:
            logger.warning("DialogManagerが初期化されていません")


    def update_stats(self):
        """
        統計情報更新（DataBindingManager経由）
        Phase 4 Refactoring: DataBindingManagerに委譲
        """
        self.data_binding_manager.update_stats()

    # スロット実装
    def on_selection_changed(self, selected_n_numbers: List[str]):
        """
        UI管理クラスからの選択変更通知ハンドラー (EventCoordinator経由)
        Phase 3 Refactoring: EventCoordinatorに処理を委譲
        
        Args:
            selected_n_numbers: 選択されたN番号リスト
        """
        # EventCoordinatorが既に処理済みなので、追加処理があれば記述
        logger.debug(f"選択変更通知受信: {len(selected_n_numbers)}件")
    
    def _on_table_item_clicked(self, item):
        """
        テーブルアイテムクリック時のハンドラー (EventCoordinator経由)
        Phase 3 Refactoring: EventCoordinatorに移行済み
        
        Args:
            item: クリックされたテーブルアイテム
        """
        # EventCoordinatorが処理するため、削除予定のメソッド
        if hasattr(self, 'event_coordinator'):
            self.event_coordinator.on_table_item_clicked(item)
    
    def _on_table_cell_clicked(self, row, column):
        """
        テーブルセルクリック時のハンドラー (EventCoordinator経由)
        Phase 3 Refactoring: EventCoordinatorに移行済み
        
        Args:
            row: 行番号
            column: 列番号
        """
        # EventCoordinatorが処理するため、削除予定のメソッド
        if hasattr(self, 'event_coordinator'):
            self.event_coordinator.on_table_cell_clicked(row, column)

    def on_cell_clicked(self, row, col):
        """
        テーブルセルクリック時の処理 (EventCoordinator経由)
        Phase 3 Refactoring: EventCoordinatorに移行済み
        
        Args:
            row: 行番号
            col: 列番号
        """
        # EventCoordinatorが処理するため、削除予定のメソッド
        if hasattr(self, 'event_coordinator'):
            self.event_coordinator.on_cell_clicked(row, col)

    def show_workflow_details(self, n_number: str):
        """
        ワークフロー詳細ダイアログ表示 (DialogManager経由)
        Phase 3 Refactoring: DialogManagerに移行済み
        
        Args:
            n_number: 表示対象のN番号
        """
        if hasattr(self, 'dialog_manager'):
            self.dialog_manager.show_workflow_details(n_number)
        else:
            logger.warning("DialogManagerが初期化されていません")


    def show_about(self):
        """
        バージョン情報表示 (DialogManager経由)
        Phase 3 Refactoring: DialogManagerに移行済み
        """
        if hasattr(self, 'dialog_manager'):
            self.dialog_manager.show_about()
        else:
            logger.warning("DialogManagerが初期化されていません")

    def show_settings(self):
        """Phase 3 Refactoring: DialogManagerに移行済み"""
        if hasattr(self, 'dialog_manager'):
            return self.dialog_manager.show_settings()
        return False

    def on_settings_changed(self):
        """
        設定変更時の処理 (ServiceManager経由)
        Phase 3 Refactoring: ServiceManagerに移行済み
        """
        try:
            # ServiceManagerに設定変更を通知
            if hasattr(self, 'service_manager'):
                self.service_manager.reinitialize_services()
            
            # ステータス更新
            self.status_updated.emit("設定が更新されました")
            
            logger.info("設定変更に伴う再初期化完了")
            
        except Exception as e:
            logger.error(f"設定変更処理エラー: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "設定変更", f"設定変更の反映中にエラーが発生しました:\n{e}")

    # === Phase 3 Refactoring: Theme Event Handlers ===
    def _on_theme_changed(self, theme_name: str):
        """
        テーマ変更時のイベントハンドラー
        
        Args:
            theme_name: 新しいテーマ名
        """
        try:
            # テーマ参照を更新
            self.theme = self.theme_applicator.get_current_theme()
            
            # UI管理クラスにテーマ変更を通知
            if hasattr(self, 'ui_manager'):
                self.ui_manager.update_theme(self.theme)
            
            # UIComponentManagerにテーマ変更を通知
            if hasattr(self, 'ui_component_manager'):
                self.ui_component_manager.update_theme(self.theme)
            
            # ステータスバーでテーマ変更を通知
            self.status_updated.emit(f"テーマを '{theme_name}' に変更しました")
            logger.info(f"Theme changed to: {theme_name}")
            
        except Exception as e:
            logger.error(f"Theme change event handler error: {e}")
            self._on_theme_error("theme_change_handler", str(e))

    def _on_theme_error(self, error_type: str, message: str):
        """
        テーマエラー時のイベントハンドラー
        
        Args:
            error_type: エラータイプ
            message: エラーメッセージ
        """
        error_msg = f"テーマエラー ({error_type}): {message}"
        logger.error(error_msg)
        
        # ユーザーにエラーを通知（重要なエラーのみ）
        if error_type in ["initialization", "loading", "critical"]:
            QMessageBox.warning(self, "テーマエラー", 
                              f"テーマの処理中にエラーが発生しました:\n{message}\n\n"
                              "フォールバックテーマを使用します。")
        
        # ステータスバーにエラー通知
        self.status_updated.emit(f"テーマエラー: {error_type}")

    # === Phase 3 Refactoring: ServiceManager Signal Handlers ===
    
    def _on_service_error(self, service_name: str, error_message: str):
        """
        ServiceManagerからのサービスエラー通知ハンドラー
        
        Args:
            service_name: エラーが発生したサービス名
            error_message: エラーメッセージ
        """
        error_msg = f"サービスエラー ({service_name}): {error_message}"
        logger.error(error_msg)
        
        # 重要なサービスエラーの場合はユーザーに通知
        if service_name in ["initialization", "google_sheets", "slack"]:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "サービスエラー", 
                              f"サービス '{service_name}' でエラーが発生しました:\n{error_message}")
        
        # ステータスバーにエラー通知
        self.status_updated.emit(f"サービスエラー: {service_name}")
    
    def _on_service_initialized(self, service_name: str):
        """
        ServiceManagerからのサービス初期化完了通知ハンドラー
        
        Args:
            service_name: 初期化完了したサービス名
        """
        logger.info(f"サービス初期化完了: {service_name}")
        self.status_updated.emit(f"{service_name} サービス準備完了")
        
        # サービス初期化完了時にコントローラーのサービス参照を更新
        if hasattr(self, 'controller'):
            self.controller.sheets_service = self.service_manager.get_sheets_service()
            self.controller.slack_service = self.service_manager.get_slack_service()

    # === Phase 4 Refactoring: DataBindingManager Signal Handlers ===
    
    def _on_data_refresh_requested(self):
        """
        データ更新要求ハンドラー（DataBindingManager経由）
        Phase 4 Refactoring: EventHandlerServiceとDataBindingManagerの統合
        """
        self.data_binding_manager.refresh_data()
    
    def _on_data_loaded(self, workflows: List):
        """
        データ読み込み完了シグナルハンドラー
        
        Args:
            workflows: 読み込まれたワークフローリスト
        """
        logger.info(f"データ読み込み完了: {len(workflows)}件")
        self.data_changed.emit()
    
    def _on_sync_completed(self, operation_type: str, count: int):
        """
        同期完了シグナルハンドラー
        
        Args:
            operation_type: 同期操作タイプ
            count: 処理された件数
        """
        message = f"{operation_type}同期完了: {count}件"
        logger.info(message)
        self.status_updated.emit(message)
        QMessageBox.information(self, "同期完了", message)
    
    def _on_data_error(self, operation: str, error_message: str):
        """
        データ操作エラーシグナルハンドラー
        
        Args:
            operation: エラーが発生した操作
            error_message: エラーメッセージ
        """
        logger.error(f"{operation}エラー: {error_message}")
        self.status_updated.emit(f"エラー: {error_message}")
        QMessageBox.warning(self, f"{operation}エラー", error_message)
    
    def _on_binding_updated(self, component: str, data: dict):
        """
        バインディング更新シグナルハンドラー
        
        Args:
            component: 更新されたコンポーネント名
            data: 更新データ
        """
        logger.debug(f"バインディング更新: {component} - {data}")
        self.data_changed.emit()
    
    def _on_progress_updated(self, status_message: str, percentage: int):
        """
        進捗更新シグナルハンドラー
        
        Args:
            status_message: ステータスメッセージ
            percentage: 進捗率（0-100）
        """
        self.status_updated.emit(status_message)
        if self.progress_bar:
            if percentage > 0:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(percentage)
            if percentage >= 100:
                self.progress_bar.setVisible(False)
    
    def _update_progress(self, status_message: str, percentage: int):
        """
        進捗更新コールバック（DataBindingManager用）
        
        Args:
            status_message: ステータスメッセージ
            percentage: 進捗率（0-100）
        """
        self._on_progress_updated(status_message, percentage)

    def _integrate_monitor_dashboard(self):
        """
        Phase 4: 監視ダッシュボードをタブとして統合
        """
        try:
            # メインウィジェットを取得
            central_widget = self.centralWidget()
            if not central_widget:
                logger.error("Central widget not found")
                return
            
            # 既存のレイアウトを取得
            main_layout = central_widget.layout()
            if not main_layout:
                logger.error("Main layout not found")
                return
            
            # タブウィジェットを作成（まだ存在しない場合）
            if not hasattr(self, 'main_tab_widget'):
                # 既存のウィジェットを一時的に保存
                existing_widgets = []
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(0)
                    if item:
                        widget = item.widget()
                        if widget:
                            existing_widgets.append(widget)
                            main_layout.removeWidget(widget)
                
                # タブウィジェット作成
                self.main_tab_widget = QTabWidget()
                
                # 既存のワークフロー画面をタブに追加
                workflow_container = QWidget()
                workflow_layout = QVBoxLayout(workflow_container)
                for widget in existing_widgets:
                    workflow_layout.addWidget(widget)
                
                self.main_tab_widget.addTab(workflow_container, "📋 ワークフロー")
                
                # メインレイアウトにタブウィジェットを追加
                main_layout.addWidget(self.main_tab_widget)
            
            # 監視ダッシュボードタブを追加
            from .views.monitor_dashboard_view import MonitorDashboardView
            self.monitor_dashboard = MonitorDashboardView(self)
            
            # ダッシュボードシグナル接続
            self.monitor_dashboard.refresh_requested.connect(self._on_monitor_refresh_requested)
            self.monitor_dashboard.start_monitor_requested.connect(self._on_start_monitor_requested)
            self.monitor_dashboard.stop_monitor_requested.connect(self._on_stop_monitor_requested)
            
            # タブに追加
            self.main_tab_widget.addTab(self.monitor_dashboard, "📊 監視ダッシュボード")
            
            logger.info("Monitor dashboard integrated successfully")
            
        except Exception as e:
            logger.error(f"Failed to integrate monitor dashboard: {e}")
            # エラーでも継続
    
    def _initialize_monitor_services(self):
        """
        Phase 4: 監視関連サービスの初期化
        """
        try:
            # 監視ステータスサービス
            from ..services.monitor_status_service import MonitorStatusService
            self.monitor_status_service = MonitorStatusService(
                db_path="data/monitor_history.db"
            )
            
            # 通知サービス
            from ..services.notification_service import NotificationService
            self.notification_service = NotificationService()
            
            # Slackサービスが有効なら登録
            if self.slack_service:
                self.notification_service.register_slack_service(self.slack_service)
            
            # N番号監視サービス（シートベース）
            from ..services.sheet_based_n_number_monitor import SheetBasedNNumberMonitor
            
            # GAS設定を取得（将来的に設定ファイルから読み込み）
            gas_config = self.config_service.get('gas_monitor', {})
            if gas_config.get('enabled', False):
                self.n_number_monitor = SheetBasedNNumberMonitor(
                    gas_endpoint=gas_config.get('endpoint', ''),
                    token=gas_config.get('token', '')
                )
                logger.info("Sheet-based N-number monitor initialized")
            else:
                self.n_number_monitor = None
                logger.info("N-number monitor not configured")
            
            logger.info("Monitor services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitor services: {e}")
            # エラーでも継続
    
    def _on_monitor_refresh_requested(self):
        """
        監視ダッシュボードからのリフレッシュ要求
        """
        logger.debug("Monitor dashboard refresh requested")
        # 必要に応じて監視ステータスを更新
        if hasattr(self, 'monitor_status_service'):
            active_monitors = self.monitor_status_service.get_active_monitors()
            logger.info(f"Active monitors: {len(active_monitors)}")
    
    def _on_start_monitor_requested(self, book_title: str, dummy_n_number: str):
        """
        監視開始要求
        
        Args:
            book_title: 書籍タイトル
            dummy_n_number: ダミーN番号
        """
        logger.info(f"Monitor start requested: {book_title}")
        # N番号監視サービスを使用して監視開始
        # 実装は次のフェーズで
    
    def _on_stop_monitor_requested(self, monitor_id: str):
        """
        監視停止要求
        
        Args:
            monitor_id: 監視ID
        """
        logger.info(f"Monitor stop requested: {monitor_id}")
        # 監視停止処理
        # 実装は次のフェーズで
    
    def closeEvent(self, event):
        """
        ウィンドウ閉じる処理
        """
        self.refresh_timer.stop()
        
        # ソケットサーバーを停止
        if hasattr(self, 'socket_server'):
            self.socket_server.stop()
            
        # FileWatcherServiceを停止
        if hasattr(self, 'file_watcher_service'):
            self.file_watcher_service.cleanup()
            
        # 監視ダッシュボードのクリーンアップ
        if hasattr(self, 'monitor_dashboard'):
            self.monitor_dashboard.close()
            
        logger.info("TechWF メインウィンドウ終了 - 外部システム連携サービス停止完了")
        event.accept()

    # === 外部システム連携イベントハンドラー ===
    def _on_external_data_started(self, file_path: str):
        """外部データインポート開始イベント"""
        try:
            file_name = Path(file_path).name
            message = f"外部システムからのデータ受信開始: {file_name}"
            logger.info(message)
            self.status_updated.emit(message)
            
            # 進捗表示開始
            if self.progress_bar:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # 不定進捗表示
                
        except Exception as e:
            logger.error(f"外部データ開始イベントエラー: {e}")
            
    def _on_external_data_imported(self, file_path: str, data: dict):
        """外部データインポート完了イベント"""
        try:
            file_name = Path(file_path).name
            book_title = data.get('data', {}).get('book_title', '不明')
            message = f"外部システムからのデータ受信完了: {book_title} ({file_name})"
            logger.info(message)
            
            # ステータス更新
            self.status_updated.emit(message)
            
            # 進捗バー非表示
            if self.progress_bar:
                self.progress_bar.setVisible(False)
                
            # データ再読み込み（画面更新）
            self.data_changed.emit()
            
            # ユーザーへの通知
            QMessageBox.information(
                self,
                "外部データ受信完了",
                f"技術書典スクレイパーからのデータを受信しました:\n\n"
                f"書名: {book_title}\n"
                f"ファイル: {file_name}\n\n"
                f"データベースとGoogle Sheetsに自動保存されました。"
            )
            
        except Exception as e:
            logger.error(f"外部データ完了イベントエラー: {e}")
            
    def _on_external_data_error(self, file_path: str, error_message: str):
        """外部データインポートエラーイベント"""
        try:
            file_name = Path(file_path).name
            message = f"外部システムデータ受信エラー: {file_name} - {error_message}"
            logger.error(message)
            
            # ステータス更新
            self.status_updated.emit(f"エラー: {error_message}")
            
            # 進捗バー非表示
            if self.progress_bar:
                self.progress_bar.setVisible(False)
                
            # エラーダイアログ
            QMessageBox.warning(
                self,
                "外部データ受信エラー", 
                f"技術書典スクレイパーからのデータ受信でエラーが発生しました:\n\n"
                f"ファイル: {file_name}\n"
                f"エラー: {error_message}\n\n"
                f"ファイル形式やデータ内容を確認してください。"
            )
            
        except Exception as e:
            logger.error(f"外部データエラーイベントエラー: {e}")


# メイン実行部分（テスト用）
    # === Phase 3 Refactoring: 新しいManagerシグナルハンドラー ===
    
    def _on_settings_changed(self):
        """DialogManagerからの設定変更通知ハンドラー"""
        self.on_settings_changed()
    
    def _on_dialog_error(self, dialog_type: str, error_message: str):
        """DialogManagerからのエラー通知ハンドラー"""
        logger.error(f"DialogManager error ({dialog_type}): {error_message}")
        self.status_updated.emit(f"ダイアログエラー: {error_message}")
    
    def _on_settings_requested(self):
        """MenuBarManagerからの設定要求ハンドラー"""
        self.show_settings()
    
    def _on_about_requested(self):
        """MenuBarManagerからのAbout要求ハンドラー"""
        self.show_about()
    
    def _on_data_export_requested(self):
        """MenuBarManagerからのデータエクスポート要求ハンドラー"""
        logger.info("データエクスポート要求受信")
        self.status_updated.emit("データエクスポート機能は今後実装予定です")
    
    def _on_tsv_import_requested(self):
        """MenuBarManagerからのTSVインポート要求ハンドラー"""
        logger.info("TSVインポート要求受信")
        
        try:
            # TSVインポートダイアログを表示
            from .dialogs.tsv_import_dialog import TSVImportDialog
            
            dialog = TSVImportDialog(
                parent=self,
                repository=self.repository,
                sheets_service=self.sheets_service
            )
            
            if dialog.exec():
                # インポート成功時の処理
                self.status_updated.emit("TSVインポートが完了しました")
                # データを再読み込み
                self.refresh_data()
            else:
                self.status_updated.emit("TSVインポートがキャンセルされました")
                
        except Exception as e:
            logger.error(f"TSVインポートダイアログ表示エラー: {e}")
            QMessageBox.critical(
                self, 
                "TSVインポートエラー",
                f"TSVインポートダイアログの表示に失敗しました:\n{str(e)}"
            )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # データベースパス（相対パス）
    db_path = "../../../data/techwf.db"
    
    # メインウィンドウ作成・表示
    window = TechWFMainWindow(db_path)
    window.show()
    
    sys.exit(app.exec())
