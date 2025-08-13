#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Theme Applicator - テーマ適用システム
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QApplication, QWidget
from .theme import ThemeManager, TechWFTheme, get_theme_manager

logger = logging.getLogger(__name__)

class ThemeApplicator:
    """テーマ適用クラス"""
    
    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        """
        初期化
        
        Args:
            theme_manager: テーママネージャー
        """
        self.theme_manager = theme_manager or get_theme_manager()
        self._current_stylesheet = ""
    
    def apply_theme(self, widget: Optional[QWidget] = None):
        """
        テーマを適用
        
        Args:
            widget: 適用対象ウィジェット（Noneの場合はアプリケーション全体）
        """
        try:
            stylesheet = self.theme_manager.generate_stylesheet()
            
            if widget is not None:
                widget.setStyleSheet(stylesheet)
                logger.info(f"Theme applied to widget: {widget.__class__.__name__}")
            else:
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(stylesheet)
                    logger.info("Theme applied to application")
                else:
                    logger.warning("No QApplication instance found")
            
            self._current_stylesheet = stylesheet
            
        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
    
    def apply_theme_to_table(self, table_widget):
        """
        テーブルウィジェットに特化したテーマを適用
        
        Args:
            table_widget: QTableWidget
        """
        try:
            theme = self.theme_manager.get_current_theme()
            
            # テーブル固有のスタイル
            table_stylesheet = f"""
            QTableWidget {{
                background-color: {theme.colors['background']};
                color: {theme.colors['foreground']};
                gridline-color: {theme.colors['border']};
                selection-background-color: {theme.colors['selected']};
                alternate-background-color: {self._get_alternate_color(theme.colors['background'])};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme.colors['border']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {theme.colors['selected']};
                color: {theme.colors['foreground']};
            }}
            
            QHeaderView::section {{
                background-color: {theme.colors['header_bg']};
                color: {theme.colors['foreground']};
                padding: 10px;
                border: none;
                border-right: 1px solid {theme.colors['border']};
                border-bottom: 2px solid {theme.colors['border']};
                font-weight: bold;
            }}
            
            QHeaderView::section:hover {{
                background-color: {self._adjust_color(theme.colors['header_bg'], -10)};
            }}
            """
            
            table_widget.setStyleSheet(table_stylesheet)
            logger.info("Table-specific theme applied")
            
        except Exception as e:
            logger.error(f"Failed to apply table theme: {e}")
    
    def apply_theme_to_buttons(self, buttons: list):
        """
        ボタンリストに特化したテーマを適用
        
        Args:
            buttons: QPushButton のリスト
        """
        try:
            theme = self.theme_manager.get_current_theme()
            
            button_stylesheet = f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: white;
                border: none;
                {theme.styles['button']}
                font-weight: bold;
                min-height: 30px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {self._adjust_color(theme.colors['primary'], -20)};
            }}
            
            QPushButton:pressed {{
                background-color: {self._adjust_color(theme.colors['primary'], -40)};
            }}
            
            QPushButton:disabled {{
                background-color: {theme.colors['secondary']};
                color: #999999;
            }}
            """
            
            for button in buttons:
                button.setStyleSheet(button_stylesheet)
            
            logger.info(f"Button theme applied to {len(buttons)} buttons")
            
        except Exception as e:
            logger.error(f"Failed to apply button theme: {e}")
    
    def apply_status_colors(self, widget, status: str):
        """
        ステータスに応じた色を適用
        
        Args:
            widget: 対象ウィジェット
            status: ステータス文字列
        """
        try:
            theme = self.theme_manager.get_current_theme()
            
            color_mapping = {
                'completed': theme.colors['accent'],
                'second_proof': theme.colors['primary'],
                'first_proof': theme.colors['warning'],
                'manuscript_received': '#17a2b8',  # info color
                'manuscript_requested': theme.colors['warning'],
                'purchased': theme.colors['secondary'],
                'discovered': '#6c757d'  # muted color
            }
            
            color = color_mapping.get(status.lower(), theme.colors['foreground'])
            
            # ウィジェットに応じてスタイルを適用
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet(f"color: {color}; font-weight: bold;")
            
        except Exception as e:
            logger.error(f"Failed to apply status color: {e}")
    
    def get_current_stylesheet(self) -> str:
        """現在のスタイルシートを取得"""
        return self._current_stylesheet
    
    def refresh_theme(self, new_theme: TechWFTheme):
        """
        テーマを更新して再適用
        
        Args:
            new_theme: 新しいテーマ
        """
        try:
            self.theme_manager.set_theme(new_theme)
            self.apply_theme()
            logger.info(f"Theme refreshed to: {new_theme.value}")
        except Exception as e:
            logger.error(f"Failed to refresh theme: {e}")
    
    def get_current_theme(self):
        """現在のテーマ設定を取得"""
        return self.theme_manager.get_current_theme()
    
    def _get_alternate_color(self, base_color: str) -> str:
        """交互の背景色を生成"""
        return self._adjust_color(base_color, 10)
    
    def _adjust_color(self, color: str, adjustment: int) -> str:
        """色の明度を調整"""
        if color.startswith('#'):
            try:
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