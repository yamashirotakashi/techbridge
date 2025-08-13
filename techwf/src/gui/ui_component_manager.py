#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Component Manager - UI要素の作成・配置・管理システム
Phase 2 復旧: UIComponentManager完全実装
"""

import logging
from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QGroupBox, QSplitter,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)

class UIComponentManager(QObject):
    """UI要素の作成・配置・管理クラス"""
    
    # シグナル定義
    component_created = Signal(str)  # コンポーネント名
    layout_updated = Signal()
    theme_applied = Signal()
    
    def __init__(self, theme, main_window, parent=None):
        """
        初期化
        
        Args:
            theme: テーマ設定
            main_window: メインウィンドウインスタンス
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.theme = theme
        self.main_window = main_window
        self._components = {}
        self._layouts = {}
        
        logger.info("UIComponentManager initialized")
    
    def setup_main_ui(self, parent) -> None:
        """
        メインUIのセットアップ
        Phase 1の_setup_minimal_ui()を拡張・改良
        """
        try:
            logger.info("Setting up main UI components...")
            
            # 中央ウィジェットを作成
            central_widget = QWidget()
            parent.setCentralWidget(central_widget)
            
            # メインレイアウト
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # ツールバーエリアを作成
            toolbar_widget = self._create_toolbar()
            main_layout.addWidget(toolbar_widget)
            
            # メインワークエリアを作成
            work_area = self._create_work_area()
            main_layout.addWidget(work_area, 1)  # 伸縮可能
            
            # ステータスエリアを作成
            status_area = self._create_status_area()
            main_layout.addWidget(status_area)
            
            # コンポーネント登録
            self._components['central_widget'] = central_widget
            self._layouts['main_layout'] = main_layout
            
            self.component_created.emit("main_ui")
            logger.info("Main UI setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup main UI: {e}")
            self._create_fallback_ui(parent)
    
    def _create_toolbar(self) -> QWidget:
        """ツールバーエリアの作成"""
        try:
            toolbar_group = QGroupBox("操作")
            toolbar_layout = QHBoxLayout(toolbar_group)
            
            # 同期ボタングループ
            sync_group = self._create_sync_buttons()
            toolbar_layout.addWidget(sync_group)
            
            # セパレーター
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            toolbar_layout.addWidget(separator)
            
            # 外部アプリボタングループ
            app_group = self._create_app_buttons()
            toolbar_layout.addWidget(app_group)
            
            # 右側にスペース
            toolbar_layout.addStretch()
            
            # 設定ボタン
            settings_button = QPushButton("設定")
            settings_button.setObjectName("settings_button")
            toolbar_layout.addWidget(settings_button)
            
            self._components['toolbar'] = toolbar_group
            self._components['settings_button'] = settings_button
            
            return toolbar_group
            
        except Exception as e:
            logger.error(f"Failed to create toolbar: {e}")
            return QWidget()
    
    def _create_sync_buttons(self) -> QWidget:
        """同期ボタングループの作成"""
        sync_group = QGroupBox("データ同期")
        sync_layout = QHBoxLayout(sync_group)
        
        # 同期ボタンを作成
        self.main_window.sync_buttons = {}
        
        buttons_config = [
            ('from_sheet', 'Sheetsから同期', '🔄'),
            ('to_sheet', 'Sheetsに送信', '📤'),
            ('refresh', '更新', '🔄')
        ]
        
        for button_id, text, icon in buttons_config:
            button = QPushButton(f"{icon} {text}")
            button.setObjectName(f"sync_{button_id}")
            button.setToolTip(f"{text}を実行します")
            sync_layout.addWidget(button)
            self.main_window.sync_buttons[button_id] = button
        
        self._components['sync_buttons'] = self.main_window.sync_buttons
        return sync_group
    
    def _create_app_buttons(self) -> QWidget:
        """外部アプリボタングループの作成"""
        app_group = QGroupBox("外部ツール")
        app_layout = QHBoxLayout(app_group)
        
        # 外部アプリボタンを作成
        app_buttons = {}
        
        apps_config = [
            ('techzip', 'TechZip', '📦'),
            ('pjinit', 'PJInit', '🚀'),
            ('sheets', 'Sheets', '📊')
        ]
        
        for app_id, text, icon in apps_config:
            button = QPushButton(f"{icon} {text}")
            button.setObjectName(f"app_{app_id}")
            button.setToolTip(f"{text}を起動します")
            app_layout.addWidget(button)
            app_buttons[app_id] = button
        
        self._components['app_buttons'] = app_buttons
        return app_group
    
    def _create_work_area(self) -> QWidget:
        """メインワークエリアの作成"""
        try:
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # ワークフローテーブル
            table_widget = self._create_main_table()
            splitter.addWidget(table_widget)
            
            # 詳細パネル（縮小可能）
            detail_panel = self._create_detail_panel()
            splitter.addWidget(detail_panel)
            
            # 分割比率設定（テーブル70%, 詳細30%）
            splitter.setSizes([700, 300])
            
            self._components['work_area'] = splitter
            return splitter
            
        except Exception as e:
            logger.error(f"Failed to create work area: {e}")
            return self._create_main_table()
    
    def _create_main_table(self) -> QTableWidget:
        """メインワークフローテーブルの作成"""
        try:
            # テーブルインスタンスを作成
            table = QTableWidget()
            
            # テーブルの基本設定
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels([
                "N番号", "書名", "著者", "ステータス", "更新日"
            ])
            
            # ヘッダーサイズ調整
            header = table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            
            # テーブルの外観設定
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            table.setSortingEnabled(True)
            
            # グリッド表示
            table.setShowGrid(True)
            table.setGridStyle(Qt.PenStyle.SolidLine)
            
            # メインウィンドウへの参照も設定
            self.main_window.workflow_table = table
            
            # 内部コンポーネント辞書に保存
            self._components['workflow_table'] = table
            
            logger.info(f"Main workflow table created successfully: {type(table)}")
            return table
            
        except Exception as e:
            logger.error(f"Failed to create main table: {e}")
            fallback_table = QTableWidget()
            self._components['workflow_table'] = fallback_table
            return fallback_table
    
    def _create_detail_panel(self) -> QWidget:
        """詳細パネルの作成"""
        detail_group = QGroupBox("詳細情報")
        detail_layout = QVBoxLayout(detail_group)
        
        # 選択された項目の詳細表示
        detail_label = QLabel("項目を選択してください")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        detail_label.setWordWrap(True)
        detail_layout.addWidget(detail_label)
        
        # アクションボタン
        action_layout = QHBoxLayout()
        
        edit_button = QPushButton("📝 編集")
        edit_button.setObjectName("edit_button")
        action_layout.addWidget(edit_button)
        
        delete_button = QPushButton("🗑️ 削除")
        delete_button.setObjectName("delete_button")
        action_layout.addWidget(delete_button)
        
        action_layout.addStretch()
        detail_layout.addLayout(action_layout)
        
        # 余白を追加
        detail_layout.addStretch()
        
        # コンポーネント登録
        self._components['detail_panel'] = detail_group
        self._components['detail_label'] = detail_label
        self._components['edit_button'] = edit_button
        self._components['delete_button'] = delete_button
        
        return detail_group
    
    def _create_status_area(self) -> QWidget:
        """ステータスエリアの作成"""
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setMaximumHeight(30)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # ステータスメッセージ
        status_label = QLabel("準備完了")
        status_label.setObjectName("status_label")
        status_layout.addWidget(status_label)
        
        # 右側にスペース
        status_layout.addStretch()
        
        # 接続状態
        connection_label = QLabel("未接続")
        connection_label.setObjectName("connection_label")
        connection_label.setStyleSheet("color: orange;")
        status_layout.addWidget(connection_label)
        
        self._components['status_area'] = status_frame
        self._components['status_label'] = status_label
        self._components['connection_label'] = connection_label
        
        return status_frame
    
    def _create_fallback_ui(self, parent):
        """フォールバックUI（エラー時用）"""
        try:
            fallback_widget = QWidget()
            fallback_layout = QVBoxLayout(fallback_widget)
            
            error_label = QLabel("UIの初期化中にエラーが発生しました")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px;")
            fallback_layout.addWidget(error_label)
            
            retry_button = QPushButton("再試行")
            retry_button.clicked.connect(lambda: self.setup_main_ui(parent))
            fallback_layout.addWidget(retry_button)
            
            parent.setCentralWidget(fallback_widget)
            
        except Exception as e:
            logger.critical(f"Failed to create fallback UI: {e}")
    
    def get_workflow_table(self) -> Optional[QTableWidget]:
        """ワークフローテーブルを取得"""
        return self._components.get('workflow_table')
    
    def get_sync_buttons(self) -> Dict[str, QPushButton]:
        """同期ボタンを取得"""
        return self._components.get('sync_buttons', {})
    
    def get_component(self, name: str) -> Optional[QWidget]:
        """指定されたコンポーネントを取得"""
        return self._components.get(name)
    
    def update_theme(self, theme) -> None:
        """テーマを更新"""
        try:
            self.theme = theme
            
            # 各コンポーネントにテーマを適用
            for name, component in self._components.items():
                if hasattr(component, 'setStyleSheet'):
                    self._apply_theme_to_component(component, name)
            
            self.theme_applied.emit()
            logger.info("Theme updated for all components")
            
        except Exception as e:
            logger.error(f"Failed to update theme: {e}")
    
    def _apply_theme_to_component(self, component, name: str):
        """個別コンポーネントにテーマを適用"""
        try:
            # テーマに基づくスタイルシート適用
            if hasattr(self.theme, 'get_component_style'):
                style = self.theme.get_component_style(name)
                if style:
                    component.setStyleSheet(style)
                    
        except Exception as e:
            logger.debug(f"Could not apply theme to component {name}: {e}")
    
    def refresh_layout(self):
        """レイアウトを更新"""
        try:
            for layout in self._layouts.values():
                if hasattr(layout, 'update'):
                    layout.update()
            
            self.layout_updated.emit()
            
        except Exception as e:
            logger.error(f"Failed to refresh layout: {e}")
    
    def set_component_enabled(self, component_name: str, enabled: bool):
        """コンポーネントの有効/無効を設定"""
        component = self.get_component(component_name)
        if component and hasattr(component, 'setEnabled'):
            component.setEnabled(enabled)
    
    def update_status_message(self, message: str):
        """ステータスメッセージを更新"""
        status_label = self.get_component('status_label')
        if status_label:
            status_label.setText(message)
    
    def update_connection_status(self, connected: bool, service_name: str = ""):
        """接続状態を更新"""
        connection_label = self.get_component('connection_label')
        if connection_label:
            if connected:
                text = f"接続済み: {service_name}" if service_name else "接続済み"
                connection_label.setText(text)
                connection_label.setStyleSheet("color: green;")
            else:
                connection_label.setText("未接続")
                connection_label.setStyleSheet("color: orange;")


# ファクトリー関数
def create_ui_component_manager(theme, main_window, parent=None) -> UIComponentManager:
    """
    UIComponentManagerを作成
    
    Args:
        theme: テーマ設定
        main_window: メインウィンドウ
        parent: 親オブジェクト
        
    Returns:
        UIComponentManager: インスタンス
    """
    return UIComponentManager(theme, main_window, parent)