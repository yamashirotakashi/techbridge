#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI State Manager - UI状態管理システム
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class WindowState:
    """ウィンドウ状態"""
    x: int = 100
    y: int = 100
    width: int = 1200
    height: int = 800
    maximized: bool = False

@dataclass  
class TableState:
    """テーブル状態"""
    column_widths: List[int] = None
    sort_column: int = 0
    sort_order: str = "asc"  # "asc" or "desc"
    visible_columns: List[int] = None
    
    def __post_init__(self):
        if self.column_widths is None:
            self.column_widths = [150, 300, 200, 120, 150]  # デフォルトカラム幅
        if self.visible_columns is None:
            self.visible_columns = [0, 1, 2, 3, 4]  # 全カラム表示

@dataclass
class FilterState:
    """フィルター状態"""
    status_filter: str = "all"
    search_text: str = ""
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

@dataclass
class UIPreferences:
    """UI設定"""
    theme: str = "default"
    auto_refresh: bool = True
    refresh_interval: int = 30
    show_status_bar: bool = True
    show_toolbar: bool = True
    language: str = "ja"

@dataclass
class UIState:
    """UI状態の統合クラス"""
    window: WindowState = None
    table: TableState = None
    filter: FilterState = None
    preferences: UIPreferences = None
    last_saved: Optional[str] = None
    
    def __post_init__(self):
        if self.window is None:
            self.window = WindowState()
        if self.table is None:
            self.table = TableState()
        if self.filter is None:
            self.filter = FilterState()
        if self.preferences is None:
            self.preferences = UIPreferences()

class UIStateManager:
    """UI状態管理クラス"""
    
    def __init__(self, state_file: str = "ui_state.json"):
        """
        初期化
        
        Args:
            state_file: 状態ファイルのパス
        """
        self.state_file = Path(state_file)
        self._ui_state = UIState()
        self._load_state()
        
    def _load_state(self):
        """状態をファイルから読み込み"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 各セクションを復元
                if 'window' in data:
                    self._ui_state.window = WindowState(**data['window'])
                if 'table' in data:
                    self._ui_state.table = TableState(**data['table'])
                if 'filter' in data:
                    self._ui_state.filter = FilterState(**data['filter'])
                if 'preferences' in data:
                    self._ui_state.preferences = UIPreferences(**data['preferences'])
                
                self._ui_state.last_saved = data.get('last_saved')
                logger.info(f"UI state loaded from {self.state_file}")
            else:
                logger.info("UI state file not found, using defaults")
                
        except Exception as e:
            logger.error(f"Failed to load UI state: {e}")
            self._ui_state = UIState()  # デフォルトにフォールバック
    
    def save_state(self):
        """状態をファイルに保存"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 現在時刻を設定
            self._ui_state.last_saved = datetime.now().isoformat()
            
            # 辞書に変換
            state_dict = asdict(self._ui_state)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"UI state saved to {self.state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save UI state: {e}")
    
    # ウィンドウ状態の管理
    def get_window_state(self) -> WindowState:
        """ウィンドウ状態を取得"""
        return self._ui_state.window
    
    def set_window_state(self, x: int, y: int, width: int, height: int, maximized: bool = False):
        """ウィンドウ状態を設定"""
        self._ui_state.window.x = x
        self._ui_state.window.y = y
        self._ui_state.window.width = width
        self._ui_state.window.height = height
        self._ui_state.window.maximized = maximized
    
    # テーブル状態の管理
    def get_table_state(self) -> TableState:
        """テーブル状態を取得"""
        return self._ui_state.table
    
    def set_column_widths(self, widths: List[int]):
        """カラム幅を設定"""
        self._ui_state.table.column_widths = widths.copy()
    
    def set_sort_state(self, column: int, order: str):
        """ソート状態を設定"""
        self._ui_state.table.sort_column = column
        self._ui_state.table.sort_order = order
    
    def set_visible_columns(self, columns: List[int]):
        """表示カラムを設定"""
        self._ui_state.table.visible_columns = columns.copy()
    
    # フィルター状態の管理
    def get_filter_state(self) -> FilterState:
        """フィルター状態を取得"""
        return self._ui_state.filter
    
    def set_status_filter(self, status: str):
        """ステータスフィルターを設定"""
        self._ui_state.filter.status_filter = status
    
    def set_search_text(self, text: str):
        """検索テキストを設定"""
        self._ui_state.filter.search_text = text
    
    def set_date_range(self, start_date: Optional[str], end_date: Optional[str]):
        """日付範囲を設定"""
        self._ui_state.filter.date_range_start = start_date
        self._ui_state.filter.date_range_end = end_date
    
    # UI設定の管理
    def get_preferences(self) -> UIPreferences:
        """UI設定を取得"""
        return self._ui_state.preferences
    
    def set_theme(self, theme: str):
        """テーマを設定"""
        self._ui_state.preferences.theme = theme
    
    def set_auto_refresh(self, enabled: bool, interval: int = 30):
        """自動更新を設定"""
        self._ui_state.preferences.auto_refresh = enabled
        self._ui_state.preferences.refresh_interval = interval
    
    def set_ui_visibility(self, show_status_bar: bool = True, show_toolbar: bool = True):
        """UI表示設定"""
        self._ui_state.preferences.show_status_bar = show_status_bar
        self._ui_state.preferences.show_toolbar = show_toolbar
    
    def set_language(self, language: str):
        """言語を設定"""
        self._ui_state.preferences.language = language
    
    # ユーティリティメソッド
    def reset_to_defaults(self):
        """設定をデフォルトにリセット"""
        self._ui_state = UIState()
        logger.info("UI state reset to defaults")
    
    def export_state(self) -> Dict[str, Any]:
        """状態を辞書として取得"""
        return asdict(self._ui_state)
    
    def import_state(self, state_dict: Dict[str, Any]):
        """辞書から状態をインポート"""
        try:
            if 'window' in state_dict:
                self._ui_state.window = WindowState(**state_dict['window'])
            if 'table' in state_dict:
                self._ui_state.table = TableState(**state_dict['table'])
            if 'filter' in state_dict:
                self._ui_state.filter = FilterState(**state_dict['filter'])
            if 'preferences' in state_dict:
                self._ui_state.preferences = UIPreferences(**state_dict['preferences'])
            
            logger.info("UI state imported successfully")
            
        except Exception as e:
            logger.error(f"Failed to import UI state: {e}")
    
    def get_last_saved(self) -> Optional[str]:
        """最後の保存時刻を取得"""
        return self._ui_state.last_saved

# グローバル UI状態マネージャー
_ui_state_manager: Optional[UIStateManager] = None

def get_ui_state_manager() -> UIStateManager:
    """UI状態マネージャーのシングルトンインスタンスを取得"""
    global _ui_state_manager
    if _ui_state_manager is None:
        _ui_state_manager = UIStateManager()
    return _ui_state_manager