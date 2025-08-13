#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Coordinator - イベント統合管理システム
Phase 3 Refactoring: イベント処理の集約化
"""

import logging
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class EventCoordinator(QObject):
    """イベント統合管理クラス"""
    
    # シグナル定義
    data_refresh_requested = Signal()
    status_update_requested = Signal(str)
    error_occurred = Signal(str, str)  # (error_type, message)
    
    def __init__(self, main_window, parent=None):
        """
        初期化
        
        Args:
            main_window: メインウィンドウインスタンス
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.main_window = main_window
        self._event_handlers = {}
        self._timer_handlers = {}
        
        # 自動更新タイマー
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        
        logger.info("EventCoordinator initialized")
    
    def register_event_handler(self, event_name: str, handler: Callable):
        """
        イベントハンドラーを登録
        
        Args:
            event_name: イベント名
            handler: ハンドラー関数
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
        logger.debug(f"Event handler registered: {event_name}")
    
    def emit_event(self, event_name: str, *args, **kwargs):
        """
        イベントを発火
        
        Args:
            event_name: イベント名
            *args: 位置引数
            **kwargs: キーワード引数
        """
        try:
            if event_name in self._event_handlers:
                for handler in self._event_handlers[event_name]:
                    handler(*args, **kwargs)
                logger.debug(f"Event emitted: {event_name}")
        except Exception as e:
            logger.error(f"Event handler error for {event_name}: {e}")
            self.error_occurred.emit("EventHandler", str(e))
    
    def setup_table_events(self, table_widget):
        """
        テーブルイベントのセットアップ
        
        Args:
            table_widget: QTableWidget
        """
        try:
            # セル選択変更
            table_widget.itemSelectionChanged.connect(
                lambda: self._on_table_selection_changed(table_widget)
            )
            
            # セルダブルクリック
            table_widget.itemDoubleClicked.connect(
                lambda item: self._on_table_item_double_clicked(table_widget, item)
            )
            
            # ヘッダークリック（ソート）
            table_widget.horizontalHeader().sectionClicked.connect(
                lambda section: self._on_header_clicked(table_widget, section)
            )
            
            logger.info("Table events setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup table events: {e}")
    
    def setup_button_events(self, buttons: Dict[str, Any]):
        """
        ボタンイベントのセットアップ
        
        Args:
            buttons: ボタン辞書 {'button_name': QPushButton}
        """
        try:
            for button_name, button in buttons.items():
                if hasattr(button, 'clicked'):
                    button.clicked.connect(
                        lambda checked, name=button_name: self._on_button_clicked(name, checked)
                    )
            
            logger.info(f"Button events setup completed: {len(buttons)} buttons")
            
        except Exception as e:
            logger.error(f"Failed to setup button events: {e}")
    
    def setup_auto_refresh(self, interval_seconds: int = 30):
        """
        自動更新のセットアップ
        
        Args:
            interval_seconds: 更新間隔（秒）
        """
        try:
            self.auto_refresh_timer.setInterval(interval_seconds * 1000)
            self.auto_refresh_timer.start()
            logger.info(f"Auto refresh enabled: {interval_seconds}s interval")
        except Exception as e:
            logger.error(f"Failed to setup auto refresh: {e}")
    
    def stop_auto_refresh(self):
        """自動更新を停止"""
        self.auto_refresh_timer.stop()
        logger.info("Auto refresh stopped")
    
    def _on_table_selection_changed(self, table_widget):
        """テーブル選択変更ハンドラー"""
        try:
            current_row = table_widget.currentRow()
            if current_row >= 0:
                self.emit_event('table_row_selected', current_row)
                logger.debug(f"Table row selected: {current_row}")
        except Exception as e:
            logger.error(f"Table selection change error: {e}")
    
    def _on_table_item_double_clicked(self, table_widget, item):
        """テーブルアイテムダブルクリックハンドラー"""
        try:
            if item:
                row = item.row()
                column = item.column()
                self.emit_event('table_item_double_clicked', row, column, item.text())
                logger.debug(f"Table item double clicked: {row}, {column}")
        except Exception as e:
            logger.error(f"Table double click error: {e}")
    
    def _on_header_clicked(self, table_widget, section):
        """ヘッダークリックハンドラー（ソート）"""
        try:
            # ソート順の切り替え
            current_order = getattr(self, '_last_sort_order', None)
            if getattr(self, '_last_sort_column', -1) == section:
                new_order = 1 if current_order == 0 else 0  # Qt.AscendingOrder/DescendingOrder
            else:
                new_order = 0  # Qt.AscendingOrder
            
            self._last_sort_column = section
            self._last_sort_order = new_order
            
            self.emit_event('table_sort_requested', section, new_order)
            logger.debug(f"Table sort requested: column {section}, order {new_order}")
            
        except Exception as e:
            logger.error(f"Header click error: {e}")
    
    def _on_button_clicked(self, button_name: str, checked: bool):
        """ボタンクリックハンドラー"""
        try:
            self.emit_event('button_clicked', button_name, checked)
            logger.debug(f"Button clicked: {button_name}")
            
            # 特定ボタンの標準処理
            if button_name == 'refresh':
                self.data_refresh_requested.emit()
            elif button_name == 'sync_sheets':
                self.emit_event('sync_sheets_requested')
            elif button_name == 'sync_slack':
                self.emit_event('sync_slack_requested')
                
        except Exception as e:
            logger.error(f"Button click error: {e}")
    
    def _on_auto_refresh(self):
        """自動更新ハンドラー"""
        try:
            self.emit_event('auto_refresh_triggered')
            self.data_refresh_requested.emit()
            logger.debug("Auto refresh triggered")
        except Exception as e:
            logger.error(f"Auto refresh error: {e}")
    
    def show_error_message(self, title: str, message: str):
        """
        エラーメッセージ表示
        
        Args:
            title: タイトル
            message: メッセージ
        """
        try:
            if self.main_window:
                QMessageBox.critical(self.main_window, title, message)
            logger.error(f"Error message shown: {title} - {message}")
        except Exception as e:
            logger.error(f"Failed to show error message: {e}")
    
    def show_info_message(self, title: str, message: str):
        """
        情報メッセージ表示
        
        Args:
            title: タイトル
            message: メッセージ
        """
        try:
            if self.main_window:
                QMessageBox.information(self.main_window, title, message)
            logger.info(f"Info message shown: {title} - {message}")
        except Exception as e:
            logger.error(f"Failed to show info message: {e}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            self.stop_auto_refresh()
            self._event_handlers.clear()
            self._timer_handlers.clear()
            logger.info("EventCoordinator cleanup completed")
        except Exception as e:
            logger.error(f"EventCoordinator cleanup error: {e}")

# ファクトリー関数
def create_event_coordinator(main_window, parent=None) -> EventCoordinator:
    """
    EventCoordinatorを作成
    
    Args:
        main_window: メインウィンドウ
        parent: 親オブジェクト
        
    Returns:
        EventCoordinator: インスタンス
    """
    return EventCoordinator(main_window, parent)