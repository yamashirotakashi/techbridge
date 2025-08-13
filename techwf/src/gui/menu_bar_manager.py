#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Menu Bar Manager - メニューバー・ステータスバー管理システム
Phase 3 Refactoring: UI管理の集約化
"""

import logging
from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import QMenuBar, QMenu, QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt, Signal, QObject

logger = logging.getLogger(__name__)

class MenuBarManager(QObject):
    """メニューバー・ステータスバー管理クラス"""
    
    # シグナル定義
    action_triggered = Signal(str)  # アクション名
    
    def __init__(self, main_window, theme, parent=None):
        """
        初期化
        
        Args:
            main_window: メインウィンドウインスタンス
            theme: テーマ設定
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.main_window = main_window
        self.theme = theme
        self._actions = {}
        self._status_widgets = {}
        
        # メニューバー・ステータスバーをセットアップ
        self.setup_menubar()
        self.setup_statusbar()
        
        logger.info("MenuBarManager initialized")
    
    def setup_menubar(self):
        """メニューバーのセットアップ"""
        try:
            menubar = self.main_window.menuBar()
            
            # ファイルメニュー
            file_menu = self._create_file_menu(menubar)
            
            # 編集メニュー
            edit_menu = self._create_edit_menu(menubar)
            
            # 表示メニュー
            view_menu = self._create_view_menu(menubar)
            
            # ツールメニュー
            tools_menu = self._create_tools_menu(menubar)
            
            # ヘルプメニュー
            help_menu = self._create_help_menu(menubar)
            
            logger.info("Menu bar setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup menu bar: {e}")
    
    def _create_file_menu(self, menubar: QMenuBar) -> QMenu:
        """ファイルメニューを作成"""
        file_menu = menubar.addMenu("ファイル(&F)")
        
        # 新規作成
        new_action = self._create_action(
            "新規作成(&N)", "Ctrl+N", "新しいワークフロー項目を作成"
        )
        file_menu.addAction(new_action)
        self._actions['file_new'] = new_action
        
        # インポート
        import_action = self._create_action(
            "インポート(&I)", "Ctrl+I", "データをインポート"
        )
        file_menu.addAction(import_action)
        self._actions['file_import'] = import_action
        
        # エクスポート
        export_action = self._create_action(
            "エクスポート(&E)", "Ctrl+E", "データをエクスポート"
        )
        file_menu.addAction(export_action)
        self._actions['file_export'] = export_action
        
        file_menu.addSeparator()
        
        # 終了
        exit_action = self._create_action(
            "終了(&X)", "Ctrl+Q", "アプリケーションを終了"
        )
        file_menu.addAction(exit_action)
        self._actions['file_exit'] = exit_action
        
        return file_menu
    
    def _create_edit_menu(self, menubar: QMenuBar) -> QMenu:
        """編集メニューを作成"""
        edit_menu = menubar.addMenu("編集(&E)")
        
        # 編集
        edit_action = self._create_action(
            "編集(&E)", "Ctrl+Return", "選択された項目を編集"
        )
        edit_menu.addAction(edit_action)
        self._actions['edit_item'] = edit_action
        
        # 削除
        delete_action = self._create_action(
            "削除(&D)", "Delete", "選択された項目を削除"
        )
        edit_menu.addAction(delete_action)
        self._actions['edit_delete'] = delete_action
        
        edit_menu.addSeparator()
        
        # 設定
        settings_action = self._create_action(
            "設定(&S)", "Ctrl+,", "アプリケーション設定"
        )
        edit_menu.addAction(settings_action)
        self._actions['edit_settings'] = settings_action
        
        return edit_menu
    
    def _create_view_menu(self, menubar: QMenuBar) -> QMenu:
        """表示メニューを作成"""
        view_menu = menubar.addMenu("表示(&V)")
        
        # 更新
        refresh_action = self._create_action(
            "更新(&R)", "F5", "データを更新"
        )
        view_menu.addAction(refresh_action)
        self._actions['view_refresh'] = refresh_action
        
        view_menu.addSeparator()
        
        # テーマ切り替え
        theme_dark_action = self._create_action(
            "ダークテーマ(&D)", "", "ダークテーマに切り替え"
        )
        view_menu.addAction(theme_dark_action)
        self._actions['view_theme_dark'] = theme_dark_action
        
        theme_light_action = self._create_action(
            "ライトテーマ(&L)", "", "ライトテーマに切り替え"
        )
        view_menu.addAction(theme_light_action)
        self._actions['view_theme_light'] = theme_light_action
        
        return view_menu
    
    def _create_tools_menu(self, menubar: QMenuBar) -> QMenu:
        """ツールメニューを作成"""
        tools_menu = menubar.addMenu("ツール(&T)")
        
        # Google Sheets同期
        sync_sheets_action = self._create_action(
            "Google Sheets同期(&G)", "Ctrl+G", "Google Sheetsと同期"
        )
        tools_menu.addAction(sync_sheets_action)
        self._actions['tools_sync_sheets'] = sync_sheets_action
        
        # Slack通知
        slack_notify_action = self._create_action(
            "Slack通知(&S)", "Ctrl+S", "Slackに通知を送信"
        )
        tools_menu.addAction(slack_notify_action)
        self._actions['tools_slack_notify'] = slack_notify_action
        
        tools_menu.addSeparator()
        
        # データベース最適化
        optimize_db_action = self._create_action(
            "データベース最適化(&O)", "", "データベースを最適化"
        )
        tools_menu.addAction(optimize_db_action)
        self._actions['tools_optimize_db'] = optimize_db_action
        
        return tools_menu
    
    def _create_help_menu(self, menubar: QMenuBar) -> QMenu:
        """ヘルプメニューを作成"""
        help_menu = menubar.addMenu("ヘルプ(&H)")
        
        # バージョン情報
        about_action = self._create_action(
            "バージョン情報(&A)", "", "TechWFについて"
        )
        help_menu.addAction(about_action)
        self._actions['help_about'] = about_action
        
        return help_menu
    
    def _create_action(self, text: str, shortcut: str = "", tooltip: str = "") -> QAction:
        """QActionを作成"""
        action = QAction(text, self.main_window)
        
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        
        if tooltip:
            action.setStatusTip(tooltip)
            action.setToolTip(tooltip)
        
        # シグナル接続
        action.triggered.connect(lambda: self._on_action_triggered(action))
        
        return action
    
    def _on_action_triggered(self, action: QAction):
        """アクション実行ハンドラー"""
        try:
            # アクション名を特定
            action_name = None
            for name, act in self._actions.items():
                if act == action:
                    action_name = name
                    break
            
            if action_name:
                self.action_triggered.emit(action_name)
                logger.debug(f"Menu action triggered: {action_name}")
            
        except Exception as e:
            logger.error(f"Menu action error: {e}")
    
    def setup_statusbar(self):
        """ステータスバーのセットアップ"""
        try:
            statusbar = self.main_window.statusBar()
            
            # メインメッセージラベル
            self._status_widgets['message'] = QLabel("準備完了")
            statusbar.addWidget(self._status_widgets['message'])
            
            # プログレスバー（通常は非表示）
            self._status_widgets['progress'] = QProgressBar()
            self._status_widgets['progress'].setVisible(False)
            self._status_widgets['progress'].setMaximumWidth(200)
            statusbar.addWidget(self._status_widgets['progress'])
            
            # 右端の情報
            statusbar.addPermanentWidget(QLabel("  "))  # スペーサー
            
            # 接続状態インジケーター
            self._status_widgets['connection'] = QLabel("未接続")
            self._status_widgets['connection'].setStyleSheet("color: orange;")
            statusbar.addPermanentWidget(self._status_widgets['connection'])
            
            # 最終更新時刻
            self._status_widgets['last_update'] = QLabel("--:--")
            statusbar.addPermanentWidget(self._status_widgets['last_update'])
            
            logger.info("Status bar setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup status bar: {e}")
    
    def update_status_message(self, message: str):
        """ステータスメッセージを更新"""
        try:
            if 'message' in self._status_widgets:
                self._status_widgets['message'].setText(message)
            logger.debug(f"Status message updated: {message}")
        except Exception as e:
            logger.error(f"Failed to update status message: {e}")
    
    def show_progress(self, show: bool = True, value: int = 0, maximum: int = 100):
        """プログレスバーの表示/非表示"""
        try:
            if 'progress' in self._status_widgets:
                progress = self._status_widgets['progress']
                progress.setVisible(show)
                if show:
                    progress.setMaximum(maximum)
                    progress.setValue(value)
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    def update_connection_status(self, connected: bool, service_name: str = ""):
        """接続状態を更新"""
        try:
            if 'connection' in self._status_widgets:
                widget = self._status_widgets['connection']
                if connected:
                    widget.setText(f"接続済み: {service_name}" if service_name else "接続済み")
                    widget.setStyleSheet("color: green;")
                else:
                    widget.setText("未接続")
                    widget.setStyleSheet("color: orange;")
        except Exception as e:
            logger.error(f"Failed to update connection status: {e}")
    
    def update_last_update_time(self, time_str: str):
        """最終更新時刻を更新"""
        try:
            if 'last_update' in self._status_widgets:
                self._status_widgets['last_update'].setText(time_str)
        except Exception as e:
            logger.error(f"Failed to update last update time: {e}")
    
    def get_action(self, action_name: str) -> Optional[QAction]:
        """アクションを取得"""
        return self._actions.get(action_name)
    
    def enable_action(self, action_name: str, enabled: bool = True):
        """アクションを有効/無効化"""
        action = self.get_action(action_name)
        if action:
            action.setEnabled(enabled)

# ファクトリー関数
def create_menu_bar_manager(main_window, theme, parent=None) -> MenuBarManager:
    """
    MenuBarManagerを作成
    
    Args:
        main_window: メインウィンドウ
        theme: テーマ設定
        parent: 親オブジェクト
        
    Returns:
        MenuBarManager: インスタンス
    """
    return MenuBarManager(main_window, theme, parent)