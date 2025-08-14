#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge設定ファイル監視システム
Phase 4: 外部設定ファイル構造実装 - ファイル監視・自動再読込機能

YAML設定ファイルの変更を監視し、リアルタイムで設定を更新
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import logging
from datetime import datetime
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """設定変更情報"""
    config_name: str
    file_path: str
    change_type: str  # modified, created, deleted
    timestamp: datetime
    previous_data: Optional[Dict[str, Any]] = None
    current_data: Optional[Dict[str, Any]] = None


class ConfigFileHandler(FileSystemEventHandler):
    """設定ファイル変更イベントハンドラー"""
    
    def __init__(self, watcher: 'ConfigWatcher'):
        self.watcher = watcher
        self._last_modified = {}  # ファイル毎の最終更新時刻
        
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # 設定ファイル以外は無視
        if not self._is_config_file(file_path):
            return
            
        # 短時間での重複イベントを防ぐ
        now = time.time()
        last_modified = self._last_modified.get(str(file_path), 0)
        if now - last_modified < 1.0:  # 1秒以内の重複は無視
            return
        self._last_modified[str(file_path)] = now
        
        logger.info(f"設定ファイル変更検出: {file_path}")
        self.watcher._handle_file_change(str(file_path), 'modified')
    
    def on_created(self, event):
        """ファイル作成時の処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self._is_config_file(file_path):
            logger.info(f"設定ファイル作成検出: {file_path}")
            self.watcher._handle_file_change(str(file_path), 'created')
    
    def on_deleted(self, event):
        """ファイル削除時の処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self._is_config_file(file_path):
            logger.warning(f"設定ファイル削除検出: {file_path}")
            self.watcher._handle_file_change(str(file_path), 'deleted')
    
    def _is_config_file(self, file_path: Path) -> bool:
        """設定ファイルかどうかの判定"""
        if file_path.suffix not in ['.yaml', '.yml', '.json']:
            return False
            
        # 一時ファイルやバックアップファイルは無視
        if any(pattern in file_path.name for pattern in ['.tmp', '.backup', '.swp', '~']):
            return False
            
        return True


class ConfigWatcher:
    """
    TechBridge設定ファイル監視システム
    
    設定ファイルの変更を監視し、自動的に設定を再読み込み。
    変更通知とコールバック機能を提供。
    """
    
    def __init__(self, config_manager, watch_directories: List[str] = None):
        """
        設定監視システムの初期化
        
        Args:
            config_manager: ConfigManagerインスタンス
            watch_directories: 監視ディレクトリ一覧
        """
        self.config_manager = config_manager
        self.watch_directories = watch_directories or [
            str(config_manager.project_root / "config")
        ]
        
        self.observer = Observer()
        self.event_handler = ConfigFileHandler(self)
        self.is_watching = False
        
        # コールバック関数登録
        self.change_callbacks: List[Callable[[ConfigChange], None]] = []
        self.reload_callbacks: List[Callable[[str], None]] = []
        
        # 変更履歴
        self.change_history: List[ConfigChange] = []
        self.max_history_size = 100
        
        # スレッド制御
        self._lock = threading.Lock()
        
    def add_change_callback(self, callback: Callable[[ConfigChange], None]):
        """設定変更コールバックの追加"""
        self.change_callbacks.append(callback)
        
    def add_reload_callback(self, callback: Callable[[str], None]):
        """設定再読み込みコールバックの追加"""
        self.reload_callbacks.append(callback)
        
    def start_watching(self):
        """ファイル監視の開始"""
        if self.is_watching:
            logger.warning("設定監視は既に開始されています")
            return
            
        try:
            # 監視ディレクトリの設定
            for directory in self.watch_directories:
                dir_path = Path(directory)
                if dir_path.exists():
                    self.observer.schedule(
                        self.event_handler, 
                        str(dir_path), 
                        recursive=True
                    )
                    logger.info(f"設定監視開始: {dir_path}")
                else:
                    logger.warning(f"監視ディレクトリが存在しません: {dir_path}")
            
            self.observer.start()
            self.is_watching = True
            logger.info("TechBridge設定ファイル監視システム開始")
            
        except Exception as e:
            logger.error(f"設定監視開始エラー: {e}")
            raise
    
    def stop_watching(self):
        """ファイル監視の停止"""
        if not self.is_watching:
            return
            
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.is_watching = False
            logger.info("設定ファイル監視システム停止")
            
        except Exception as e:
            logger.error(f"設定監視停止エラー: {e}")
    
    def _handle_file_change(self, file_path: str, change_type: str):
        """ファイル変更の処理"""
        with self._lock:
            try:
                # 設定名の推定
                config_name = self._determine_config_name(file_path)
                if not config_name:
                    return
                
                # 変更前データの取得（修正の場合）
                previous_data = None
                if change_type == 'modified' and hasattr(self.config_manager, '_configs'):
                    previous_data = self.config_manager._configs.get(config_name, {}).copy()
                
                # 設定の再読み込み
                if change_type != 'deleted':
                    self.config_manager.reload_config(config_name)
                    current_data = self.config_manager._configs.get(config_name, {})
                else:
                    current_data = None
                
                # 変更情報の作成
                change = ConfigChange(
                    config_name=config_name,
                    file_path=file_path,
                    change_type=change_type,
                    timestamp=datetime.now(),
                    previous_data=previous_data,
                    current_data=current_data
                )
                
                # 履歴への追加
                self._add_to_history(change)
                
                # コールバック実行
                self._execute_callbacks(change)
                
                logger.info(f"設定変更処理完了: {config_name} ({change_type})")
                
            except Exception as e:
                logger.error(f"設定変更処理エラー {file_path}: {e}")
    
    def _determine_config_name(self, file_path: str) -> Optional[str]:
        """ファイルパスから設定名を判定"""
        path = Path(file_path)
        filename = path.stem
        
        # 設定ファイル名から設定名をマッピング
        config_mapping = {
            'theme_config': 'theme',
            'ui_config': 'ui',
            'server_config': 'server',
            'paths_config': 'paths'
        }
        
        return config_mapping.get(filename)
    
    def _add_to_history(self, change: ConfigChange):
        """変更履歴への追加"""
        self.change_history.append(change)
        
        # 履歴サイズ制限
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]
    
    def _execute_callbacks(self, change: ConfigChange):
        """コールバック関数の実行"""
        # 変更コールバック
        for callback in self.change_callbacks:
            try:
                callback(change)
            except Exception as e:
                logger.error(f"変更コールバックエラー: {e}")
        
        # 再読み込みコールバック
        for callback in self.reload_callbacks:
            try:
                callback(change.config_name)
            except Exception as e:
                logger.error(f"再読み込みコールバックエラー: {e}")
    
    def get_recent_changes(self, limit: int = 10) -> List[ConfigChange]:
        """最近の変更履歴の取得"""
        with self._lock:
            return self.change_history[-limit:] if self.change_history else []
    
    def get_changes_by_config(self, config_name: str) -> List[ConfigChange]:
        """特定の設定に関する変更履歴の取得"""
        with self._lock:
            return [
                change for change in self.change_history 
                if change.config_name == config_name
            ]
    
    def clear_history(self):
        """変更履歴のクリア"""
        with self._lock:
            self.change_history.clear()
            logger.info("設定変更履歴をクリアしました")
    
    def export_change_history(self, output_path: Optional[str] = None) -> str:
        """変更履歴のエクスポート"""
        if output_path is None:
            output_path = f"config_change_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        from dataclasses import asdict
        
        history_data = {
            'export_info': {
                'total_changes': len(self.change_history),
                'exported_at': datetime.now().isoformat(),
                'watch_directories': self.watch_directories
            },
            'changes': [
                {
                    **asdict(change),
                    'timestamp': change.timestamp.isoformat()
                }
                for change in self.change_history
            ]
        }
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(history_data, file, indent=2, ensure_ascii=False)
        
        logger.info(f"設定変更履歴エクスポート完了: {output_file}")
        return str(output_file)


class ConfigWatcherManager:
    """設定監視システム管理クラス"""
    
    def __init__(self):
        self.watchers: Dict[str, ConfigWatcher] = {}
        self._global_callbacks: List[Callable[[str, ConfigChange], None]] = []
    
    def create_watcher(self, 
                      name: str,
                      config_manager,
                      watch_directories: List[str] = None) -> ConfigWatcher:
        """設定監視システムの作成"""
        watcher = ConfigWatcher(config_manager, watch_directories)
        
        # グローバルコールバックの追加
        for callback in self._global_callbacks:
            watcher.add_change_callback(
                lambda change, cb=callback, watcher_name=name: cb(watcher_name, change)
            )
        
        self.watchers[name] = watcher
        return watcher
    
    def get_watcher(self, name: str) -> Optional[ConfigWatcher]:
        """設定監視システムの取得"""
        return self.watchers.get(name)
    
    def start_all(self):
        """全監視システムの開始"""
        for name, watcher in self.watchers.items():
            try:
                watcher.start_watching()
            except Exception as e:
                logger.error(f"監視システム開始エラー {name}: {e}")
    
    def stop_all(self):
        """全監視システムの停止"""
        for name, watcher in self.watchers.items():
            try:
                watcher.stop_watching()
            except Exception as e:
                logger.error(f"監視システム停止エラー {name}: {e}")
    
    def add_global_callback(self, callback: Callable[[str, ConfigChange], None]):
        """グローバルコールバックの追加"""
        self._global_callbacks.append(callback)
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.start_all()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.stop_all()


if __name__ == "__main__":
    # 設定監視システムのテスト
    from config_manager import ConfigManager
    
    print("=== TechBridge設定監視システム テスト ===")
    
    # ConfigManagerの作成
    config_manager = ConfigManager("/mnt/c/Users/tky99/dev/techbridge")
    
    # 設定監視システムの作成
    watcher = ConfigWatcher(
        config_manager,
        watch_directories=["/mnt/c/Users/tky99/dev/techbridge/config"]
    )
    
    # コールバック関数の定義
    def on_config_change(change: ConfigChange):
        print(f"設定変更: {change.config_name} - {change.change_type}")
        print(f"ファイル: {change.file_path}")
        print(f"時刻: {change.timestamp}")
    
    def on_config_reload(config_name: str):
        print(f"設定再読み込み: {config_name}")
    
    # コールバック登録
    watcher.add_change_callback(on_config_change)
    watcher.add_reload_callback(on_config_reload)
    
    # 監視開始
    try:
        watcher.start_watching()
        print("設定監視システムが開始されました")
        print("設定ファイルを編集して変更を確認してください")
        print("Ctrl+C で終了")
        
        # 監視継続
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n監視を停止します...")
        watcher.stop_watching()
        
        # 変更履歴の表示
        recent_changes = watcher.get_recent_changes(5)
        if recent_changes:
            print("\n最近の変更:")
            for change in recent_changes:
                print(f"- {change.config_name}: {change.change_type} ({change.timestamp})")
        
    print("=== テスト完了 ===")