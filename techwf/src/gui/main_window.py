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


class TechWFEventHandler:
    """
    TechWF Event Handler Coordinator
    
    Centralized handler for all UI events and callbacks.
    Separates event handling logic from main window management.
    """
    
    def __init__(self, main_window):
        """
        Initialize event handler with reference to main window.
        
        Args:
            main_window: TechWFMainWindow instance for delegation
        """
        self.main_window = main_window
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def on_table_item_clicked(self, item):
        """Handle table item click events"""
        if item:
            row = item.row()
            self.logger.info(f"Table item clicked at row {row}")
            self.main_window.workflow_table.selectRow(row)
            
    def on_table_cell_clicked(self, row, column):
        """Handle table cell click events"""
        self.logger.info(f"Table cell clicked: row {row}, column {column}")
        if hasattr(self.main_window, 'controller') and self.main_window.controller:
            self.main_window.controller.on_cell_clicked(row, column)
            
    def on_theme_changed(self, theme_name: str):
        """Handle theme change events"""
        try:
            self.logger.info(f"Theme changed to: {theme_name}")
            if hasattr(self.main_window, 'theme_applicator') and self.main_window.theme_applicator:
                self.main_window.theme_applicator.apply_theme(theme_name)
            if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
                self.main_window.status_bar.showMessage(f"Theme changed to {theme_name}", 3000)
        except Exception as e:
            self.logger.error(f"Error applying theme {theme_name}: {e}")
            
    def on_theme_error(self, error_type: str, message: str):
        """Handle theme-related errors"""
        self.logger.error(f"Theme error [{error_type}]: {message}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Theme error: {message}", 5000)
            
    def on_service_error(self, service_name: str, error_message: str):
        """Handle service initialization/operation errors"""
        self.logger.error(f"Service error in {service_name}: {error_message}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Service error: {error_message}", 5000)
            
    def on_service_initialized(self, service_name: str):
        """Handle successful service initialization"""
        self.logger.info(f"Service initialized: {service_name}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"{service_name} initialized", 2000)
            
    def on_data_refresh_requested(self):
        """Handle data refresh requests"""
        self.logger.info("Data refresh requested")
        if hasattr(self.main_window, 'refresh_data'):
            self.main_window.refresh_data()
            
    def on_data_loaded(self, workflows: List):
        """Handle successful data loading"""
        count = len(workflows) if workflows else 0
        self.logger.info(f"Data loaded: {count} workflows")
        if hasattr(self.main_window, 'update_stats'):
            self.main_window.update_stats()
            
    def on_sync_completed(self, operation_type: str, success: bool, message: str):
        """Handle synchronization completion"""
        status = "successful" if success else "failed"
        self.logger.info(f"Sync {status}: {operation_type} - {message}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Sync {status}: {message}", 3000)
            
    def on_data_error(self, operation: str, error_message: str):
        """Handle data operation errors"""
        self.logger.error(f"Data error in {operation}: {error_message}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Data error: {error_message}", 5000)
            
    def on_binding_updated(self, component: str, data: dict):
        """Handle data binding updates"""
        self.logger.debug(f"Binding updated for {component}")
        
    def on_progress_updated(self, percentage: int, status_message: str):
        """Handle progress updates"""
        if hasattr(self.main_window, '_update_progress'):
            self.main_window._update_progress(percentage, status_message)
            
    def on_monitor_refresh_requested(self):
        """Handle monitor dashboard refresh requests"""
        self.logger.info("Monitor refresh requested")
        if hasattr(self.main_window, 'monitor_dashboard') and self.main_window.monitor_dashboard:
            self.main_window.monitor_dashboard.refresh()
            
    def on_start_monitor_requested(self, book_title: str, dummy_n_number: str):
        """Handle monitor start requests"""
        self.logger.info(f"Start monitor requested for: {book_title} ({dummy_n_number})")
        
    def on_stop_monitor_requested(self, monitor_id: str):
        """Handle monitor stop requests"""
        self.logger.info(f"Stop monitor requested for ID: {monitor_id}")
        
    def on_external_data_started(self, file_path: str):
        """Handle external data import start"""
        self.logger.info(f"External data import started: {file_path}")
        if hasattr(self.main_window, 'progress_bar') and self.main_window.progress_bar:
            self.main_window.progress_bar.setVisible(True)
            self.main_window.progress_bar.setRange(0, 0)  # Indeterminate progress
            
    def on_external_data_imported(self, file_path: str, data: dict):
        """Handle successful external data import"""
        self.logger.info(f"External data imported from: {file_path}")
        if hasattr(self.main_window, 'progress_bar') and self.main_window.progress_bar:
            self.main_window.progress_bar.setVisible(False)
        if hasattr(self.main_window, 'refresh_data'):
            self.main_window.refresh_data()
            
    def on_external_data_error(self, file_path: str, error_message: str):
        """Handle external data import errors"""
        self.logger.error(f"External data import error from {file_path}: {error_message}")
        if hasattr(self.main_window, 'progress_bar') and self.main_window.progress_bar:
            self.main_window.progress_bar.setVisible(False)
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Import error: {error_message}", 5000)
            
    def on_settings_changed(self):
        """Handle settings change events"""
        self.logger.info("Settings changed")
        
    def on_dialog_error(self, dialog_type: str, error_message: str):
        """Handle dialog-related errors"""
        self.logger.error(f"Dialog error [{dialog_type}]: {error_message}")
        
    def on_settings_requested(self):
        """Handle settings dialog requests"""
        if hasattr(self.main_window, 'show_settings'):
            self.main_window.show_settings()
            
    def on_about_requested(self):
        """Handle about dialog requests"""
        if hasattr(self.main_window, 'show_about'):
            self.main_window.show_about()
            
    def on_data_export_requested(self):
        """Handle data export requests"""
        self.logger.info("Data export requested")
        
    def on_tsv_import_requested(self):
        """Handle TSV import requests"""
        if hasattr(self.main_window, 'tsv_import_service') and self.main_window.tsv_import_service:
            try:
                self.main_window.tsv_import_service.import_data()
                self.logger.info("TSV import completed successfully")
                if hasattr(self.main_window, 'refresh_data'):
                    self.main_window.refresh_data()
            except Exception as e:
                self.logger.error(f"TSV import failed: {e}")
                if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
                    self.main_window.status_bar.showMessage(f"TSV import failed: {e}", 5000)
                    
    def on_error_occurred(self, level: str, message: str):
        """Handle general error events"""
        self.logger.error(f"Error occurred [{level}]: {message}")
        if hasattr(self.main_window, 'status_bar') and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Error: {message}", 5000)
            
    def on_refresh_clicked(self):
        """Handle refresh button clicks"""
        self.logger.info("Refresh button clicked")
        if hasattr(self.main_window, 'refresh_data'):
            self.main_window.refresh_data()


class TechWFMainWindow(QMainWindow):
    """
    TechWF v0.5 メインウィンドウクラス
    技術書典商業化タブのパターンを踏襲した5カラム表示
    """
    
    # シグナル定義
    status_updated = Signal(str)  # ステータス更新
    data_changed = Signal()       # データ変更
    
    def __init__(self, db_path: str = None):
        """
        メインウィンドウの初期化
        
        Args:
            db_path: データベースファイルパス（Noneの場合は安全なデフォルトパスを使用）
        """
        super().__init__()
        
        # セキュリティ修正: パストラバーサル脆弱性対策
        # db_pathが指定されていない場合は、安全な設定管理システムを使用
        if db_path is None:
            from techwf.src.config import TechWFConfig
            db_path = TechWFConfig.get_database_path()
            logger.info(f"セキュアなデータベースパス使用: {db_path}")
        
        # === Phase 3 Refactoring: ThemeApplicator導入 ===
        # テーマ管理をThemeApplicatorに委譲  
        self.theme_applicator = ThemeApplicator()
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
        from .service_manager import get_service_manager
        self.service_manager = get_service_manager()
        self.service_manager.initialize_services()
        
        # ServiceManagerからサービス参照を取得
        self.sheets_service = self.service_manager.get_google_sheets_service()
        self.slack_service = self.service_manager.get_slack_service()
        
        # === Architectural Refactoring: Event Handler分離 ===
        # イベント処理をTechWFEventHandlerに委譲
        self.event_handler_coordinator = TechWFEventHandler(self)
        
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
        from ..services.socket_server_service import SocketServerService
        self.socket_server = SocketServerService(self.config_service)
        self.socket_server.start_server()
        
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
        
        # FileWatcherServiceシグナル接続（Event Handler経由）
        self.file_watcher_service.file_imported.connect(self.event_handler_coordinator.on_external_data_imported)
        self.file_watcher_service.import_error.connect(self.event_handler_coordinator.on_external_data_error)
        self.file_watcher_service.import_started.connect(self.event_handler_coordinator.on_external_data_started)
        
        logger.info(f"外部システム連携監視開始: {self.file_watcher_service.get_watch_directory()}")
        
        # UI状態管理初期化
        self.ui_manager = UIStateManager("ui_state.json")
        
        # === Phase 1 Refactoring: UIComponentManager導入 ===
        # UIComponentManager初期化（UI作成ロジック分離）
        from .ui_component_manager import UIComponentManager
        self.ui_component_manager = UIComponentManager(self.theme, self)
        
        # UI Setup Chain（UIComponentManagerに委譲）
        self.ui_component_manager.setup_ui()
        
        # メニューバー・ステータスバー・シグナルセットアップ
        self.menu_bar_manager.setup_menubar()
        self.menu_bar_manager.setup_statusbar()
        self.setup_signals()
        
        # 初期データ読み込み
        self.load_initial_data()
        
        logger.info("TechWF Main Window 初期化完了")

    def setup_signals(self):
        """
        シグナル・スロット接続 (全Manager経由)
        
        Phase 3 Refactoring: 全Managerを使用した統合シグナル接続
        """
        # EventCoordinatorでシグナル接続を実行
        if hasattr(self, 'event_coordinator'):
            self.event_coordinator.setup_signals()
            
        # DialogManagerでダイアログ関連シグナル接続
        if hasattr(self, 'dialog_manager'):
            self.dialog_manager.setup_signals()
            
        # FileWatcherServiceでファイル監視シグナル接続済み（__init__で実行済み）
        logger.info("シグナル接続完了: Event Coordinator & Dialog Manager")

    def load_initial_data(self):
        """
        初期データ読み込み（DataBindingManager経由）
        Phase 4 Refactoring: DataBindingManagerに委譲
        """
        if hasattr(self, 'data_binding_manager'):
            self.data_binding_manager.load_initial_data()
        else:
            logger.warning("DataBindingManager not initialized")

    def refresh_data(self):
        """
        データの更新（DataBindingManager経由）
        Phase 4 Refactoring: DataBindingManagerに委譲
        """
        if hasattr(self, 'data_binding_manager'):
            self.data_binding_manager.refresh_data()
        else:
            logger.warning("DataBindingManager not initialized")

    def show_settings(self):
        """Phase 3 Refactoring: DialogManagerに移行済み"""
        if hasattr(self, 'dialog_manager'):
            return self.dialog_manager.show_settings()
        return False

    def show_about(self):
        """
        バージョン情報表示 (DialogManager経由)
        Phase 3 Refactoring: DialogManagerに移行済み
        """
        if hasattr(self, 'dialog_manager'):
            self.dialog_manager.show_about()
        else:
            logger.warning("DialogManagerが初期化されていません")

    def closeEvent(self, event):
        """
        ウィンドウ閉じる処理
        """
        # ソケットサーバーを停止
        if hasattr(self, 'socket_server'):
            self.socket_server.stop_server()
            
        # FileWatcherServiceを停止
        if hasattr(self, 'file_watcher_service'):
            self.file_watcher_service.cleanup()
            
        # 監視ダッシュボードのクリーンアップ
        if hasattr(self, 'monitor_dashboard'):
            self.monitor_dashboard.close()
            
        logger.info("TechWF メインウィンドウ終了 - 外部システム連携サービス停止完了")
        event.accept()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from techwf.src.config import TechWFConfig
    
    app = QApplication(sys.argv)
    
    # セキュアなデータベースパス設定
    db_path = TechWFConfig.get_database_path()
    
    # メインウィンドウ作成・表示
    window = TechWFMainWindow(db_path)
    window.show()
    
    sys.exit(app.exec())