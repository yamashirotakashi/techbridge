#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Handler Service - PySide6イベントハンドリング統合サービス
Phase 2 復旧: EventHandlerService完全実装 + EventCoordinator統合
"""

import logging
import subprocess
import os
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QTimer, QProcess
from PySide6.QtWidgets import (
    QMessageBox, QInputDialog, QProgressDialog, QWidget, 
    QTableWidget, QPushButton, QApplication
)
from PySide6.QtGui import QKeyEvent, QMouseEvent, QCloseEvent

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """イベント優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class EventContext:
    """イベントコンテキスト情報"""
    event_type: str
    source_widget: Optional[QWidget]
    timestamp: float
    priority: EventPriority
    data: Dict[str, Any]

class EventHandlerService(QObject):
    """
    PySide6イベントハンドリング統合サービス
    EventCoordinatorとの連携によるイベント処理システム + ビジネスロジック処理
    """
    
    # シグナル定義 - UI Events
    event_processed = Signal(str, object)  # イベント名, コンテキスト
    event_failed = Signal(str, str)  # イベント名, エラーメッセージ
    handler_registered = Signal(str)  # ハンドラー名
    handler_removed = Signal(str)  # ハンドラー名
    
    # シグナル定義 - Business Logic Events  
    operation_started = Signal(str)  # 操作名
    operation_completed = Signal(str, bool, str)  # 操作名, 成功/失敗, メッセージ
    progress_updated = Signal(int, str)  # 進捗率, メッセージ
    status_message = Signal(str)  # ステータスメッセージ
    error_occurred = Signal(str, str)  # エラーレベル, メッセージ
    
    def __init__(self, main_window, event_coordinator=None, parent=None):
        """
        初期化
        
        Args:
            main_window: メインウィンドウインスタンス
            event_coordinator: EventCoordinatorインスタンス（オプション）
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.main_window = main_window
        self.event_coordinator = event_coordinator
        
        # UI Event Handling 
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._widget_handlers: Dict[QWidget, Dict[str, Callable]] = {}
        self._global_filters: List[Callable] = []
        
        # Business Logic Operations
        self._operations_in_progress = set()
        self._external_processes = {}
        
        # Event Statistics
        self._event_stats = {
            'processed': 0,
            'failed': 0,
            'filtered': 0
        }
        
        # デバウンスタイマー（重複イベント抑制）
        self._debounce_timers: Dict[str, QTimer] = {}
        self._debounce_delays = {
            'table_selection_changed': 100,  # 100ms
            'button_clicked': 50,
            'resize_event': 200
        }
        
        # EventCoordinator統合設定
        if self.event_coordinator:
            self._setup_event_coordinator_integration()
        
        logger.info("EventHandlerService initialized with EventCoordinator integration")
    
    # === UI Event Handling Methods ===
    
    def setup_main_window_events(self) -> None:
        """メインウィンドウのイベントセットアップ"""
        try:
            logger.info("Setting up main window events...")
            
            # ウィンドウクローズイベント
            if hasattr(self.main_window, 'closeEvent'):
                original_close = self.main_window.closeEvent
                self.main_window.closeEvent = lambda event: self._handle_window_close(event, original_close)
            
            # ウィンドウリサイズイベント
            if hasattr(self.main_window, 'resizeEvent'):
                original_resize = self.main_window.resizeEvent
                self.main_window.resizeEvent = lambda event: self._handle_window_resize(event, original_resize)
            
            # UI components events
            self._setup_ui_component_events()
            
            logger.info("Main window events setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup main window events: {e}")
    
    def register_event_handler(self, event_name: str, handler: Callable, 
                             priority: EventPriority = EventPriority.NORMAL) -> None:
        """
        イベントハンドラーを登録
        
        Args:
            event_name: イベント名
            handler: ハンドラー関数
            priority: 優先度
        """
        try:
            if event_name not in self._event_handlers:
                self._event_handlers[event_name] = []
            
            # 優先度でソート
            self._event_handlers[event_name].append((handler, priority))
            self._event_handlers[event_name].sort(key=lambda x: x[1].value, reverse=True)
            
            # EventCoordinatorにも登録
            if self.event_coordinator:
                self.event_coordinator.register_event_handler(event_name, handler)
            
            self.handler_registered.emit(event_name)
            logger.debug(f"Event handler registered: {event_name} (priority: {priority.name})")
            
        except Exception as e:
            logger.error(f"Failed to register event handler {event_name}: {e}")
    
    def emit_event(self, event_name: str, context: Optional[EventContext] = None, 
                   debounce: bool = True, **kwargs) -> None:
        """
        イベントを発火
        
        Args:
            event_name: イベント名
            context: イベントコンテキスト
            debounce: デバウンス機能を使用するか
            **kwargs: 追加データ
        """
        try:
            # デバウンス処理
            if debounce and event_name in self._debounce_delays:
                if event_name in self._debounce_timers:
                    self._debounce_timers[event_name].stop()
                
                timer = QTimer()
                timer.timeout.connect(
                    lambda: self._process_debounced_event(event_name, context, kwargs)
                )
                timer.setSingleShot(True)
                timer.start(self._debounce_delays[event_name])
                self._debounce_timers[event_name] = timer
                return
            
            # 即座にイベント処理
            self._process_event_immediately(event_name, context, kwargs)
            
        except Exception as e:
            logger.error(f"Failed to emit event {event_name}: {e}")
            self.event_failed.emit(event_name, str(e))
    
    def _setup_event_coordinator_integration(self):
        """EventCoordinatorとの統合設定"""
        try:
            # EventCoordinatorのシグナルを監視
            self.event_coordinator.data_refresh_requested.connect(
                lambda: self.emit_event('data_refresh_requested')
            )
            self.event_coordinator.status_update_requested.connect(
                lambda msg: self.emit_event('status_update_requested', data={'message': msg})
            )
            self.event_coordinator.error_occurred.connect(
                lambda err_type, msg: self.emit_event('error_occurred', 
                                                    data={'type': err_type, 'message': msg})
            )
            
            # カスタムイベントハンドラー登録
            self.register_event_handler('table_row_selected', self._handle_table_row_selected)
            self.register_event_handler('table_item_double_clicked', self._handle_table_item_double_clicked)
            self.register_event_handler('button_clicked', self._handle_button_clicked)
            self.register_event_handler('auto_refresh_triggered', self._handle_auto_refresh)
            
            logger.info("EventCoordinator integration completed")
            
        except Exception as e:
            logger.error(f"Failed to setup EventCoordinator integration: {e}")
    
    def _setup_ui_component_events(self):
        """UIコンポーネントのイベントセットアップ"""
        try:
            # ワークフローテーブルのイベント
            if hasattr(self.main_window, 'workflow_table'):
                table = self.main_window.workflow_table
                if self.event_coordinator:
                    self.event_coordinator.setup_table_events(table)
            
            # 同期ボタンのイベント
            if hasattr(self.main_window, 'sync_buttons'):
                buttons = self.main_window.sync_buttons
                if self.event_coordinator:
                    self.event_coordinator.setup_button_events(buttons)
            
        except Exception as e:
            logger.error(f"Failed to setup UI component events: {e}")
    
    def _process_debounced_event(self, event_name: str, context: Optional[EventContext], kwargs: Dict):
        """デバウンス処理されたイベントの実行"""
        # タイマーをクリーンアップ
        if event_name in self._debounce_timers:
            del self._debounce_timers[event_name]
        
        self._process_event_immediately(event_name, context, kwargs)
    
    def _process_event_immediately(self, event_name: str, context: Optional[EventContext], kwargs: Dict):
        """イベントの即座処理"""
        try:
            # グローバルフィルターチェック
            for filter_func in self._global_filters:
                if not filter_func(event_name, context):
                    self._event_stats['filtered'] += 1
                    return
            
            # ハンドラー実行
            if event_name in self._event_handlers:
                for handler, priority in self._event_handlers[event_name]:
                    try:
                        if context:
                            handler(context, **kwargs)
                        else:
                            handler(**kwargs)
                    except Exception as e:
                        logger.error(f"Handler {handler.__name__} failed for {event_name}: {e}")
            
            # EventCoordinatorにも通知
            if self.event_coordinator:
                self.event_coordinator.emit_event(event_name, context, **kwargs)
            
            self._event_stats['processed'] += 1
            self.event_processed.emit(event_name, context)
            
        except Exception as e:
            self._event_stats['failed'] += 1
            logger.error(f"Failed to process event {event_name}: {e}")
            self.event_failed.emit(event_name, str(e))
    
    def _handle_window_close(self, event: QCloseEvent, original_handler: Callable):
        """ウィンドウクローズイベントハンドラー"""
        try:
            context = EventContext(
                event_type='window_close',
                source_widget=self.main_window,
                timestamp=QApplication.instance().time(),
                priority=EventPriority.HIGH,
                data={'can_close': True}
            )
            
            self.emit_event('window_close_requested', context, debounce=False)
            
            # 元のハンドラーを実行
            if original_handler:
                original_handler(event)
                
        except Exception as e:
            logger.error(f"Window close handler error: {e}")
    
    def _handle_window_resize(self, event, original_handler: Callable):
        """ウィンドウリサイズイベントハンドラー"""
        try:
            context = EventContext(
                event_type='window_resize',
                source_widget=self.main_window,
                timestamp=QApplication.instance().time(),
                priority=EventPriority.LOW,
                data={'size': event.size()}
            )
            
            self.emit_event('window_resized', context)
            
            # 元のハンドラーを実行
            if original_handler:
                original_handler(event)
                
        except Exception as e:
            logger.error(f"Window resize handler error: {e}")
    
    def _handle_table_row_selected(self, row: int):
        """テーブル行選択ハンドラー"""
        try:
            logger.debug(f"Table row selected: {row}")
            
            # UI状態管理に通知
            if hasattr(self.main_window, 'ui_state_manager'):
                self.main_window.ui_state_manager.set_selected_row(row)
            
            # 詳細パネル更新
            self._update_detail_panel(row)
            
        except Exception as e:
            logger.error(f"Table row selection handler error: {e}")
    
    def _handle_table_item_double_clicked(self, row: int, column: int, text: str):
        """テーブルアイテムダブルクリックハンドラー"""
        try:
            logger.debug(f"Table item double clicked: row={row}, col={column}, text={text}")
            
            # 編集ダイアログを開く
            if hasattr(self.main_window, 'dialog_manager'):
                self.main_window.dialog_manager.show_edit_dialog(row)
            
        except Exception as e:
            logger.error(f"Table double click handler error: {e}")
    
    def _handle_button_clicked(self, button_name: str, checked: bool):
        """ボタンクリックハンドラー - ビジネスロジックにルーティング"""
        try:
            logger.debug(f"Button clicked: {button_name} (checked: {checked})")
            
            # ビジネスロジックメソッドにルーティング
            if button_name == 'from_sheet':
                self.handle_sync_from_sheet()
            elif button_name == 'to_sheet':
                self.handle_sync_to_sheet()
            elif button_name == 'refresh':
                self.handle_data_refresh()
            
        except Exception as e:
            logger.error(f"Button click handler error: {e}")
    
    def _handle_auto_refresh(self):
        """自動更新ハンドラー"""
        try:
            logger.debug("Auto refresh triggered")
            self.handle_data_refresh()
            
        except Exception as e:
            logger.error(f"Auto refresh handler error: {e}")
    
    def _update_detail_panel(self, row: int):
        """詳細パネルの更新"""
        try:
            # UIComponentManagerから詳細ラベルを取得
            if hasattr(self.main_window, 'ui_component_manager'):
                detail_label = self.main_window.ui_component_manager.get_component('detail_label')
                if detail_label and hasattr(self.main_window, 'workflow_table'):
                    table = self.main_window.workflow_table
                    if 0 <= row < table.rowCount():
                        # 行データを取得して表示
                        row_data = []
                        for col in range(table.columnCount()):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        
                        detail_text = f"""選択された項目:
N番号: {row_data[0] if len(row_data) > 0 else ''}
書名: {row_data[1] if len(row_data) > 1 else ''}
著者: {row_data[2] if len(row_data) > 2 else ''}
ステータス: {row_data[3] if len(row_data) > 3 else ''}
更新日: {row_data[4] if len(row_data) > 4 else ''}"""
                        
                        detail_label.setText(detail_text)
                        
        except Exception as e:
            logger.error(f"Failed to update detail panel: {e}")
    
    # === Business Logic Methods ===
    
    def handle_sync_from_sheet(self):
        """Google Sheetsからの同期処理"""
        try:
            operation_id = "sync_from_sheet"
            if operation_id in self._operations_in_progress:
                self.status_message.emit("既に同期処理が実行中です")
                return
            
            self.operation_started.emit("Google Sheetsからの同期")
            self._operations_in_progress.add(operation_id)
            
            # ServiceManagerが利用可能かチェック
            if not hasattr(self.main_window, 'service_manager'):
                self.error_occurred.emit("error", "ServiceManagerが初期化されていません")
                return
            
            service_manager = self.main_window.service_manager
            
            # Google Sheetsサービスの状態確認
            if not service_manager.is_sheets_service_available():
                self.error_occurred.emit("warning", "Google Sheetsサービスが利用できません")
                return
            
            # 進捗表示開始
            self.progress_updated.emit(10, "Google Sheetsに接続中...")
            
            # データ取得処理（仮実装）
            self._simulate_async_operation(
                operation_id, 
                self._sync_from_sheet_worker,
                "Google Sheetsからの同期が完了しました"
            )
            
        except Exception as e:
            logger.error(f"Sync from sheet error: {e}")
            self.error_occurred.emit("error", f"同期エラー: {e}")
            self._operations_in_progress.discard(operation_id)
    
    def handle_sync_to_sheet(self):
        """Google Sheetsへの送信処理"""
        try:
            operation_id = "sync_to_sheet"
            if operation_id in self._operations_in_progress:
                self.status_message.emit("既に送信処理が実行中です")
                return
            
            self.operation_started.emit("Google Sheetsへの送信")
            self._operations_in_progress.add(operation_id)
            
            # 変更データの確認
            if not self._has_unsaved_changes():
                self.status_message.emit("送信する変更がありません")
                self._operations_in_progress.discard(operation_id)
                return
            
            # 確認ダイアログ
            reply = QMessageBox.question(
                self.main_window,
                "確認",
                "変更をGoogle Sheetsに送信しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self._operations_in_progress.discard(operation_id)
                return
            
            # 進捗表示開始
            self.progress_updated.emit(10, "Google Sheetsに送信中...")
            
            # データ送信処理（仮実装）
            self._simulate_async_operation(
                operation_id,
                self._sync_to_sheet_worker,
                "Google Sheetsへの送信が完了しました"
            )
            
        except Exception as e:
            logger.error(f"Sync to sheet error: {e}")
            self.error_occurred.emit("error", f"送信エラー: {e}")
            self._operations_in_progress.discard(operation_id)
    
    def handle_data_refresh(self):
        """データ更新処理"""
        try:
            operation_id = "data_refresh"
            if operation_id in self._operations_in_progress:
                self.status_message.emit("既に更新処理が実行中です")
                return
            
            self.operation_started.emit("データ更新")
            self._operations_in_progress.add(operation_id)
            
            # 進捗表示開始
            self.progress_updated.emit(10, "データベースから読み込み中...")
            
            # データ更新処理
            self._simulate_async_operation(
                operation_id,
                self._refresh_data_worker,
                "データ更新が完了しました"
            )
            
        except Exception as e:
            logger.error(f"Data refresh error: {e}")
            self.error_occurred.emit("error", f"データ更新エラー: {e}")
            self._operations_in_progress.discard(operation_id)
    
    def handle_post_to_slack(self, message: str = "", channel: str = ""):
        """Slack通知送信処理"""
        try:
            operation_id = "post_to_slack"
            if operation_id in self._operations_in_progress:
                self.status_message.emit("既にSlack通知処理が実行中です")
                return
            
            # メッセージ入力ダイアログ
            if not message:
                message, ok = QInputDialog.getText(
                    self.main_window,
                    "Slack通知",
                    "送信するメッセージを入力してください:",
                    text="TechWFから通知: "
                )
                if not ok or not message.strip():
                    return
            
            self.operation_started.emit("Slack通知送信")
            self._operations_in_progress.add(operation_id)
            
            # 進捗表示開始
            self.progress_updated.emit(10, "Slackに送信中...")
            
            # Slack送信処理（仮実装）
            self._simulate_async_operation(
                operation_id,
                lambda: self._slack_post_worker(message, channel),
                f"Slack通知を送信しました: {message[:30]}..."
            )
            
        except Exception as e:
            logger.error(f"Slack post error: {e}")
            self.error_occurred.emit("error", f"Slack送信エラー: {e}")
            self._operations_in_progress.discard(operation_id)
    
    def handle_launch_techzip(self, n_number: str = ""):
        """TechZipアプリケーション起動処理"""
        try:
            operation_id = "launch_techzip"
            
            # TechZipの実行ファイルパス
            techzip_paths = [
                "/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool/dist/TechZip.exe",
                "/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool/main.py",
                "C:\\Users\\tky99\\dev\\technical-fountain-series-support-tool\\dist\\TechZip.exe"
            ]
            
            techzip_path = None
            for path in techzip_paths:
                if os.path.exists(path):
                    techzip_path = path
                    break
            
            if not techzip_path:
                self.error_occurred.emit("error", "TechZipアプリケーションが見つかりません")
                return
            
            self.operation_started.emit("TechZip起動")
            
            # N番号を引数として起動
            args = [techzip_path]
            if n_number:
                args.append(f"--n-number={n_number}")
            
            # 外部プロセス起動
            process = QProcess(self)
            process.finished.connect(
                lambda exit_code: self._on_external_process_finished("TechZip", exit_code)
            )
            
            self._external_processes[operation_id] = process
            
            if techzip_path.endswith('.exe'):
                process.start(techzip_path, args[1:])
            else:
                process.start("python", args)
            
            if process.waitForStarted(5000):
                self.status_message.emit(f"TechZipを起動しました (N番号: {n_number or '未指定'})")
                self.operation_completed.emit("TechZip起動", True, "正常に起動しました")
            else:
                self.error_occurred.emit("error", "TechZipの起動に失敗しました")
                
        except Exception as e:
            logger.error(f"TechZip launch error: {e}")
            self.error_occurred.emit("error", f"TechZip起動エラー: {e}")
    
    def handle_launch_pjinit(self):
        """PJInitアプリケーション起動処理"""
        try:
            operation_id = "launch_pjinit"
            
            # PJInitの実行ファイルパス
            pjinit_paths = [
                "/mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer/dist/PJinit.1.1.exe",
                "/mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer/main.py",
                "C:\\Users\\tky99\\dev\\techbridge\\app\\mini_apps\\project_initializer\\dist\\PJinit.1.1.exe"
            ]
            
            pjinit_path = None
            for path in pjinit_paths:
                if os.path.exists(path):
                    pjinit_path = path
                    break
            
            if not pjinit_path:
                self.error_occurred.emit("error", "PJInitアプリケーションが見つかりません")
                return
            
            self.operation_started.emit("PJInit起動")
            
            # 外部プロセス起動
            process = QProcess(self)
            process.finished.connect(
                lambda exit_code: self._on_external_process_finished("PJInit", exit_code)
            )
            
            self._external_processes[operation_id] = process
            
            if pjinit_path.endswith('.exe'):
                process.start(pjinit_path)
            else:
                process.start("python", [pjinit_path])
            
            if process.waitForStarted(5000):
                self.status_message.emit("PJInitを起動しました")
                self.operation_completed.emit("PJInit起動", True, "正常に起動しました")
            else:
                self.error_occurred.emit("error", "PJInitの起動に失敗しました")
                
        except Exception as e:
            logger.error(f"PJInit launch error: {e}")
            self.error_occurred.emit("error", f"PJInit起動エラー: {e}")
    
    def handle_open_google_sheets(self):
        """Google Sheetsをブラウザで開く"""
        try:
            # Google Sheets URLを構築
            sheets_url = "https://docs.google.com/spreadsheets/d/17DKsMGQ6mBUGUTv3rC6a5BNQH_rMEVPbIYWaJgc3c7I/edit"
            
            # ブラウザで開く
            import webbrowser
            webbrowser.open(sheets_url)
            
            self.status_message.emit("Google Sheetsをブラウザで開きました")
            self.operation_completed.emit("Google Sheets Open", True, "ブラウザで開きました")
            
        except Exception as e:
            logger.error(f"Open sheets error: {e}")
            self.error_occurred.emit("error", f"Google Sheets開くエラー: {e}")
    
    def _simulate_async_operation(self, operation_id: str, worker_func: Callable, success_message: str):
        """非同期操作のシミュレート"""
        try:
            # タイマーを使って段階的に進捗を更新
            self._current_operation = operation_id
            self._current_worker = worker_func
            self._current_success_message = success_message
            self._progress_step = 0
            
            self._progress_timer = QTimer(self)
            self._progress_timer.timeout.connect(self._update_progress)
            self._progress_timer.start(500)  # 0.5秒ごとに更新
            
        except Exception as e:
            logger.error(f"Async operation setup error: {e}")
            self._operations_in_progress.discard(operation_id)
    
    def _update_progress(self):
        """進捗更新処理"""
        try:
            self._progress_step += 1
            progress = min(self._progress_step * 20, 90)  # 最大90%まで
            
            if self._progress_step == 1:
                self.progress_updated.emit(progress, "処理を開始しています...")
            elif self._progress_step == 2:
                self.progress_updated.emit(progress, "データを処理中...")
            elif self._progress_step == 3:
                self.progress_updated.emit(progress, "処理を完了しています...")
            elif self._progress_step >= 4:
                # 処理完了
                self._progress_timer.stop()
                
                # ワーカー関数実行
                try:
                    self._current_worker()
                    self.progress_updated.emit(100, self._current_success_message)
                    self.operation_completed.emit(self._current_operation, True, self._current_success_message)
                except Exception as e:
                    error_msg = f"処理エラー: {e}"
                    self.progress_updated.emit(100, error_msg)
                    self.operation_completed.emit(self._current_operation, False, error_msg)
                
                self._operations_in_progress.discard(self._current_operation)
                
        except Exception as e:
            logger.error(f"Progress update error: {e}")
            self._progress_timer.stop()
            self._operations_in_progress.discard(self._current_operation)
    
    def _sync_from_sheet_worker(self):
        """Google Sheetsからの同期ワーカー（仮実装）"""
        # 実際の実装では、ServiceManagerを使ってGoogle Sheets APIを呼び出す
        logger.info("Simulating sync from Google Sheets...")
        
        # データベースアクセス（仮）
        if hasattr(self.main_window, 'workflow_controller'):
            controller = self.main_window.workflow_controller
            # controller.refresh_from_sheets()
        
        return True
    
    def _sync_to_sheet_worker(self):
        """Google Sheetsへの送信ワーカー（仮実装）"""
        # 実際の実装では、ServiceManagerを使ってGoogle Sheets APIを呼び出す
        logger.info("Simulating sync to Google Sheets...")
        
        # データベースからデータ取得・送信（仮）
        if hasattr(self.main_window, 'workflow_controller'):
            controller = self.main_window.workflow_controller
            # controller.sync_to_sheets()
        
        return True
    
    def _refresh_data_worker(self):
        """データ更新ワーカー"""
        logger.info("Refreshing data from database...")
        
        # データベースからリフレッシュ
        if hasattr(self.main_window, 'workflow_controller'):
            controller = self.main_window.workflow_controller
            # controller.refresh_data()
        
        # UIテーブルを更新
        if hasattr(self.main_window, 'workflow_table') and self.main_window.workflow_table:
            table = self.main_window.workflow_table
            
            # サンプルデータでテーブル更新
            table.setRowCount(3)
            sample_data = [
                ["N12345", "サンプル書籍1", "著者A", "原稿依頼", "2025-01-15"],
                ["N23456", "サンプル書籍2", "著者B", "初校", "2025-01-20"],
                ["N34567", "サンプル書籍3", "著者C", "完成", "2025-01-25"]
            ]
            
            from PySide6.QtWidgets import QTableWidgetItem
            for row, row_data in enumerate(sample_data):
                for col, cell_data in enumerate(row_data):
                    table.setItem(row, col, QTableWidgetItem(str(cell_data)))
        
        return True
    
    def _slack_post_worker(self, message: str, channel: str):
        """Slack投稿ワーカー（仮実装）"""
        logger.info(f"Simulating Slack post: {message}")
        
        # 実際の実装では、ServiceManagerを使ってSlack APIを呼び出す
        if hasattr(self.main_window, 'service_manager'):
            service_manager = self.main_window.service_manager
            # service_manager.post_to_slack(message, channel)
        
        return True
    
    def _has_unsaved_changes(self) -> bool:
        """未保存の変更があるかチェック"""
        # 実際の実装では、DataBindingManagerなどでチェック
        return True  # 仮実装
    
    def _on_external_process_finished(self, app_name: str, exit_code: int):
        """外部プロセス終了時の処理"""
        if exit_code == 0:
            self.status_message.emit(f"{app_name}が正常に終了しました")
        else:
            self.status_message.emit(f"{app_name}が異常終了しました (exit code: {exit_code})")
    
    def cancel_operation(self, operation_id: str):
        """進行中の操作をキャンセル"""
        if operation_id in self._operations_in_progress:
            self._operations_in_progress.discard(operation_id)
            self.status_message.emit(f"操作 '{operation_id}' がキャンセルされました")
            
            # タイマーを停止
            if hasattr(self, '_progress_timer') and self._progress_timer.isActive():
                self._progress_timer.stop()
    
    def get_operations_in_progress(self) -> List[str]:
        """進行中の操作一覧を取得"""
        return list(self._operations_in_progress)
    
    def is_operation_in_progress(self, operation_id: str) -> bool:
        """指定の操作が進行中かチェック"""
        return operation_id in self._operations_in_progress
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """イベント統計情報を取得"""
        return {
            **self._event_stats,
            'registered_handlers': len(self._event_handlers),
            'widget_handlers': len(self._widget_handlers),
            'global_filters': len(self._global_filters),
            'operations_in_progress': len(self._operations_in_progress)
        }
    
    def reset_statistics(self) -> None:
        """統計情報をリセット"""
        self._event_stats = {'processed': 0, 'failed': 0, 'filtered': 0}
        logger.info("Event statistics reset")
    
    def add_global_filter(self, filter_func: Callable) -> None:
        """
        グローバルイベントフィルターを追加
        
        Args:
            filter_func: フィルター関数 (event_name, context) -> bool
        """
        self._global_filters.append(filter_func)
        logger.debug("Global event filter added")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # デバウンスタイマーを停止
            for timer in self._debounce_timers.values():
                timer.stop()
            self._debounce_timers.clear()
            
            # 進行中の操作をキャンセル
            for operation_id in list(self._operations_in_progress):
                self.cancel_operation(operation_id)
            
            # 外部プロセスを終了
            for process in self._external_processes.values():
                if process.state() != QProcess.ProcessState.NotRunning:
                    process.kill()
                    process.waitForFinished(3000)
            self._external_processes.clear()
            
            # ハンドラーをクリア
            self._event_handlers.clear()
            self._widget_handlers.clear()
            self._global_filters.clear()
            
            # プログレスタイマーを停止
            if hasattr(self, '_progress_timer') and self._progress_timer.isActive():
                self._progress_timer.stop()
            
            logger.info("EventHandlerService cleanup completed")
            
        except Exception as e:
            logger.error(f"EventHandlerService cleanup error: {e}")


# ファクトリー関数
def create_event_handler_service(main_window, event_coordinator=None, parent=None) -> EventHandlerService:
    """
    EventHandlerServiceを作成
    
    Args:
        main_window: メインウィンドウ
        event_coordinator: EventCoordinatorインスタンス（オプション）
        parent: 親オブジェクト
        
    Returns:
        EventHandlerService: インスタンス
    """
    return EventHandlerService(main_window, event_coordinator, parent)