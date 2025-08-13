#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain GUI Binding Manager - ドメイン-GUIバインディングマネージャー
ドメインモデルとGUIコンポーネントの双方向データバインディング
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass

from ..models.domain.n_number_project import NNumberProject


@dataclass
class GuiDisplayData:
    """GUI表示用データ"""
    title: str
    current_stage: str
    stage_display: str
    progress_percentage: float
    metadata: Dict[str, Any]


class DomainGuiBindingManager:
    """
    ドメイン-GUIバインディングマネージャー
    
    ドメインモデルの変更をGUIに自動反映し、
    GUI操作をドメインロジック経由で実行する
    """
    
    def __init__(self):
        self._bound_projects: Dict[str, NNumberProject] = {}
        self._gui_update_callbacks: List[Callable[[str, GuiDisplayData], None]] = []
    
    def bind_project(self, project: NNumberProject) -> None:
        """
        プロジェクトのバインディング登録
        
        Args:
            project: N番号プロジェクト
        """
        self._bound_projects[project.n_number] = project
        
        # GUI更新通知
        self._notify_gui_update(project.n_number)
    
    def get_project_display_data(self, n_number: str) -> Dict[str, Any]:
        """
        プロジェクトのGUI表示データ取得
        
        Args:
            n_number: N番号
            
        Returns:
            Dict[str, Any]: GUI表示データ
        """
        project = self._bound_projects.get(n_number)
        if not project:
            return {}
        
        # ステージ表示名のマッピング
        stage_display_names = {
            "proposal_draft": "企画案書",
            "proposal": "企画書",
            "specification": "製品仕様書"
        }
        
        return {
            "title": project.title,
            "current_stage": project.current_stage.value,
            "stage_display": stage_display_names.get(project.current_stage.value, "不明"),
            "progress_percentage": self._calculate_progress_percentage(project),
            "n_number": project.n_number,
            "created_at": project.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": project.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": project.metadata
        }
    
    def update_project_via_gui(
        self,
        n_number: str,
        field: str,
        value: Any,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        GUI経由でのプロジェクト更新
        
        Args:
            n_number: N番号
            field: 更新フィールド
            value: 新しい値
            updated_by: 更新者
            
        Returns:
            bool: 更新成功可否
        """
        project = self._bound_projects.get(n_number)
        if not project:
            return False
        
        try:
            # フィールド別の更新処理
            if field == "title":
                project.update_title(value)
            # 他のフィールドの更新処理は必要に応じて追加
            
            # GUI更新通知
            self._notify_gui_update(n_number)
            return True
            
        except ValueError:
            # ドメインロジック違反
            return False
    
    def register_gui_update_callback(
        self,
        callback: Callable[[str, GuiDisplayData], None]
    ) -> None:
        """
        GUI更新コールバック登録
        
        Args:
            callback: 更新コールバック関数
        """
        self._gui_update_callbacks.append(callback)
    
    def _notify_gui_update(self, n_number: str) -> None:
        """GUI更新通知"""
        display_data = self.get_project_display_data(n_number)
        
        # 登録されたコールバックに通知
        for callback in self._gui_update_callbacks:
            try:
                callback(n_number, display_data)
            except Exception:
                # コールバックエラーは無視（ログ出力などは実装時に追加）
                pass
    
    def _calculate_progress_percentage(self, project: NNumberProject) -> float:
        """
        進捗率計算
        
        Args:
            project: N番号プロジェクト
            
        Returns:
            float: 進捗率 (0.0-100.0)
        """
        stage_progress = {
            "proposal_draft": 25.0,
            "proposal": 60.0,
            "specification": 100.0
        }
        
        return stage_progress.get(project.current_stage.value, 0.0)