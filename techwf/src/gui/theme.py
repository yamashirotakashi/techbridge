#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Theme Management - テーマ管理システム
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class TechWFTheme(Enum):
    """TechWF テーマ列挙"""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"

class TableColumns(Enum):
    """テーブルカラム定義"""
    N_NUMBER = 0
    TITLE = 1
    AUTHOR = 2
    STATUS = 3
    UPDATED = 4

@dataclass
class ThemeConfig:
    """テーマ設定"""
    name: str
    colors: Dict[str, str]
    fonts: Dict[str, str]
    styles: Dict[str, str]

class ThemeManager:
    """テーママネージャークラス"""
    
    def __init__(self):
        """初期化"""
        self._themes = self._initialize_themes()
        self._current_theme = TechWFTheme.DEFAULT
    
    def _initialize_themes(self) -> Dict[TechWFTheme, ThemeConfig]:
        """テーマを初期化"""
        themes = {}
        
        # デフォルトテーマ
        themes[TechWFTheme.DEFAULT] = ThemeConfig(
            name="Default",
            colors={
                "background": "#ffffff",
                "foreground": "#333333",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "accent": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "header_bg": "#f8f9fa",
                "selected": "#e3f2fd",
                "border": "#dee2e6"
            },
            fonts={
                "default": "Arial, sans-serif",
                "header": "Arial, sans-serif",
                "monospace": "Courier New, monospace"
            },
            styles={
                "button": "border-radius: 4px; padding: 8px 16px;",
                "table": "gridline-color: #dee2e6;",
                "input": "border: 1px solid #ced4da; border-radius: 4px;"
            }
        )
        
        # ダークテーマ
        themes[TechWFTheme.DARK] = ThemeConfig(
            name="Dark",
            colors={
                "background": "#2b2b2b",
                "foreground": "#ffffff",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "accent": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "header_bg": "#404040",
                "selected": "#1e3a8a",
                "border": "#555555"
            },
            fonts={
                "default": "Arial, sans-serif",
                "header": "Arial, sans-serif",
                "monospace": "Courier New, monospace"
            },
            styles={
                "button": "border-radius: 4px; padding: 8px 16px;",
                "table": "gridline-color: #555555;",
                "input": "border: 1px solid #555555; border-radius: 4px;"
            }
        )
        
        # ライトテーマ
        themes[TechWFTheme.LIGHT] = ThemeConfig(
            name="Light",
            colors={
                "background": "#fafafa",
                "foreground": "#212529",
                "primary": "#007bff",
                "secondary": "#6c757d",
                "accent": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "header_bg": "#e9ecef",
                "selected": "#cce5ff",
                "border": "#dee2e6"
            },
            fonts={
                "default": "Arial, sans-serif",
                "header": "Arial, sans-serif",
                "monospace": "Courier New, monospace"
            },
            styles={
                "button": "border-radius: 4px; padding: 8px 16px;",
                "table": "gridline-color: #dee2e6;",
                "input": "border: 1px solid #ced4da; border-radius: 4px;"
            }
        )
        
        return themes
    
    def get_current_theme(self) -> ThemeConfig:
        """現在のテーマを取得"""
        return self._themes[self._current_theme]
    
    def set_theme(self, theme: TechWFTheme):
        """テーマを設定"""
        if theme in self._themes:
            self._current_theme = theme
    
    def get_theme_names(self) -> Dict[TechWFTheme, str]:
        """テーマ名一覧を取得"""
        return {theme: config.name for theme, config in self._themes.items()}
    
    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """色を取得"""
        theme = self.get_current_theme()
        return theme.colors.get(key, fallback)
    
    def get_font(self, key: str, fallback: str = "Arial") -> str:
        """フォントを取得"""
        theme = self.get_current_theme()
        return theme.fonts.get(key, fallback)
    
    def get_style(self, key: str, fallback: str = "") -> str:
        """スタイルを取得"""
        theme = self.get_current_theme()
        return theme.styles.get(key, fallback)
    
    def generate_stylesheet(self) -> str:
        """スタイルシートを生成"""
        theme = self.get_current_theme()
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {theme.colors['background']};
            color: {theme.colors['foreground']};
            font-family: {theme.fonts['default']};
        }}
        
        QTableWidget {{
            background-color: {theme.colors['background']};
            color: {theme.colors['foreground']};
            gridline-color: {theme.colors['border']};
            selection-background-color: {theme.colors['selected']};
        }}
        
        QTableWidget::item {{
            padding: 5px;
            border-bottom: 1px solid {theme.colors['border']};
        }}
        
        QHeaderView::section {{
            background-color: {theme.colors['header_bg']};
            color: {theme.colors['foreground']};
            padding: 8px;
            border: none;
            border-right: 1px solid {theme.colors['border']};
            font-weight: bold;
        }}
        
        QPushButton {{
            background-color: {theme.colors['primary']};
            color: white;
            border: none;
            {theme.styles['button']}
        }}
        
        QPushButton:hover {{
            background-color: {self._adjust_color(theme.colors['primary'], -20)};
        }}
        
        QPushButton:pressed {{
            background-color: {self._adjust_color(theme.colors['primary'], -40)};
        }}
        
        QStatusBar {{
            background-color: {theme.colors['header_bg']};
            color: {theme.colors['foreground']};
            border-top: 1px solid {theme.colors['border']};
        }}
        
        QMenuBar {{
            background-color: {theme.colors['header_bg']};
            color: {theme.colors['foreground']};
        }}
        
        QMenuBar::item {{
            padding: 4px 8px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {theme.colors['selected']};
        }}
        
        QProgressBar {{
            border: 1px solid {theme.colors['border']};
            border-radius: 3px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme.colors['accent']};
            border-radius: 2px;
        }}
        """
        
        return stylesheet
    
    def _adjust_color(self, color: str, adjustment: int) -> str:
        """色の明度を調整"""
        # 簡単な色調整の実装
        if color.startswith('#'):
            try:
                # 16進数カラーを調整
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                
                r = max(0, min(255, r + adjustment))
                g = max(0, min(255, g + adjustment))
                b = max(0, min(255, b + adjustment))
                
                return f"#{r:02x}{g:02x}{b:02x}"
            except ValueError:
                return color
        return color

# グローバルテーママネージャー
_theme_manager: Optional[ThemeManager] = None

def get_theme_manager() -> ThemeManager:
    """テーママネージャーのシングルトンインスタンスを取得"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager