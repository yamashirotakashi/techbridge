#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PJINIT Service Adapter - PJINITサービスアダプター
プロジェクト初期化サービスとの統合
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class PJInitResult:
    """PJINIT実行結果"""
    success: bool
    project_path: Optional[str] = None
    message: str = ""
    execution_details: Dict[str, Any] = None
    executed_at: datetime = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.now()
        if self.execution_details is None:
            self.execution_details = {}


class PJInitServiceAdapter:
    """
    PJINITサービスアダプター
    
    プロジェクト初期化サービス (PJINIT) との統合を担当する
    """
    
    def __init__(self):
        self.service_name = "PJINIT"
        self.service_version = "1.0"
    
    def initialize_project(
        self,
        n_number: str,
        project_type: str,
        template_config: Dict[str, Any]
    ) -> PJInitResult:
        """
        プロジェクト初期化の実行
        
        Args:
            n_number: N番号
            project_type: プロジェクトタイプ
            template_config: テンプレート設定
            
        Returns:
            PJInitResult: 初期化結果
        """
        try:
            # GREEN段階の最小実装: 常に成功する
            project_path = f"/projects/{n_number}"
            
            execution_details = {
                "n_number": n_number,
                "project_type": project_type,
                "template_config": template_config,
                "created_directories": [
                    f"{project_path}/src",
                    f"{project_path}/docs",
                    f"{project_path}/tests"
                ],
                "created_files": [
                    f"{project_path}/README.md",
                    f"{project_path}/.gitignore",
                    f"{project_path}/requirements.txt"
                ]
            }
            
            return PJInitResult(
                success=True,
                project_path=project_path,
                message="初期化完了",
                execution_details=execution_details
            )
            
        except Exception as e:
            return PJInitResult(
                success=False,
                message=f"初期化失敗: {str(e)}"
            )
    
    def get_available_templates(self) -> Dict[str, Any]:
        """
        利用可能なテンプレート取得
        
        Returns:
            Dict[str, Any]: テンプレート情報
        """
        return {
            "technical_book": {
                "name": "技術書プロジェクト",
                "description": "技術書作成用プロジェクトテンプレート",
                "tools": ["latex", "markdown", "pandoc"],
                "structure": "standard"
            },
            "web_application": {
                "name": "Webアプリケーション",
                "description": "Webアプリケーション開発用テンプレート",
                "tools": ["react", "nodejs", "docker"],
                "structure": "webapp"
            }
        }