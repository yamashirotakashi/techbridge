#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge統合設定管理システム
外部化されたYAML設定ファイルの読み込み・管理
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigPaths:
    """設定ファイルパス管理"""
    theme_config: str = "config/theme_config.yaml"
    ui_config: str = "config/ui_config.yaml"
    paths_config: str = "config/paths_config.yaml"
    server_config: str = "config/server_config.yaml"


class ConfigManager:
    """
    TechBridge統合設定管理クラス
    
    外部化されたYAML設定ファイルを読み込み、
    環境変数によるオーバーライドをサポート
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        設定管理システムの初期化
        
        Args:
            project_root: プロジェクトルートディレクトリ（Noneの場合は自動検出）
        """
        self.project_root = Path(project_root) if project_root else self._detect_project_root()
        self.config_paths = ConfigPaths()
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_all_configs()
        
    def _detect_project_root(self) -> Path:
        """プロジェクトルートの自動検出"""
        current_path = Path(__file__).resolve()
        
        # 現在のファイルから上向きに検索
        for parent in current_path.parents:
            if (parent / "config").exists() or (parent / "CLAUDE.md").exists():
                return parent
                
        # 環境変数からの取得を試行
        env_root = os.getenv('TECHWF_PROJECT_ROOT')
        if env_root:
            return Path(env_root)
            
        # デフォルト値
        return Path("/mnt/c/Users/tky99/dev/techbridge")
    
    def _load_yaml_config(self, config_name: str, file_path: str) -> Dict[str, Any]:
        """
        YAML設定ファイルの読み込み
        
        Args:
            config_name: 設定名
            file_path: ファイルパス
            
        Returns:
            設定辞書
        """
        full_path = self.project_root / file_path
        
        try:
            if not full_path.exists():
                logger.warning(f"設定ファイルが見つかりません: {full_path}")
                return {}
                
            with open(full_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) or {}
                
            # 環境変数の展開
            config = self._expand_environment_variables(config)
            
            logger.info(f"設定ファイル読み込み完了: {config_name} ({full_path})")
            return config
            
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー {config_name}: {e}")
            return {}
    
    def _expand_environment_variables(self, config: Any) -> Any:
        """
        設定内の環境変数プレースホルダーを展開
        
        Args:
            config: 設定値（辞書、リスト、文字列等）
            
        Returns:
            展開後の設定値
        """
        if isinstance(config, dict):
            return {key: self._expand_environment_variables(value) 
                   for key, value in config.items()}
        elif isinstance(config, list):
            return [self._expand_environment_variables(item) for item in config]
        elif isinstance(config, str):
            # ${VAR_NAME}形式の環境変数展開
            import re
            pattern = r'\$\{([^}]+)\}'
            
            def replace_env_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # 見つからない場合は元の値
                
            return re.sub(pattern, replace_env_var, config)
        else:
            return config
    
    def _load_all_configs(self):
        """全設定ファイルの読み込み"""
        self._configs = {
            'theme': self._load_yaml_config('theme', self.config_paths.theme_config),
            'ui': self._load_yaml_config('ui', self.config_paths.ui_config),
            'paths': self._load_yaml_config('paths', self.config_paths.paths_config),
            'server': self._load_yaml_config('server', self.config_paths.server_config),
        }
        
    def reload_config(self, config_name: Optional[str] = None):
        """
        設定の再読み込み
        
        Args:
            config_name: 再読み込みする設定名（Noneの場合は全設定）
        """
        if config_name:
            if config_name in self._configs:
                file_path = getattr(self.config_paths, f"{config_name}_config")
                self._configs[config_name] = self._load_yaml_config(config_name, file_path)
        else:
            self._load_all_configs()
            
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値の取得（ドット記法サポート）
        
        Args:
            key_path: 設定キーパス（例: "theme.colors.background"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        config_name = keys[0]
        
        if config_name not in self._configs:
            logger.warning(f"未知の設定カテゴリ: {config_name}")
            return default
            
        current = self._configs[config_name]
        
        for key in keys[1:]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
    
    def get_with_env_override(self, key_path: str, env_var: str, default: Any = None) -> Any:
        """
        環境変数オーバーライド付き設定取得
        
        Args:
            key_path: 設定キーパス
            env_var: 環境変数名
            default: デフォルト値
            
        Returns:
            設定値（環境変数優先）
        """
        # 環境変数が設定されている場合は優先
        env_value = os.getenv(env_var)
        if env_value is not None:
            # 数値型の自動変換
            try:
                if '.' in env_value:
                    return float(env_value)
                else:
                    return int(env_value)
            except ValueError:
                return env_value
                
        # 設定ファイルから取得
        return self.get(key_path, default)
    
    def get_theme_config(self, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """
        テーマ設定の取得
        
        Args:
            theme_name: テーマ名（Noneの場合はデフォルト）
            
        Returns:
            テーマ設定辞書
        """
        if not theme_name:
            theme_name = self.get('theme.default_theme', 'light')
            
        theme_config = self.get(f'theme.themes.{theme_name}', {})
        
        # 特別なカラー設定をマージ
        special_colors = self.get('theme.theme_applicator.special_colors', {})
        if 'colors' in theme_config:
            theme_config['colors'].update(special_colors)
            
        return theme_config
    
    def get_path(self, path_key: str, **format_kwargs) -> str:
        """
        パス設定の取得とフォーマット
        
        Args:
            path_key: パスキー（例: "dynamic_paths.output.pdf_file"）
            **format_kwargs: フォーマット用キーワード引数
            
        Returns:
            解決されたパス
        """
        path_template = self.get(path_key, "")
        if not path_template:
            return ""
            
        try:
            return path_template.format(**format_kwargs)
        except KeyError as e:
            logger.warning(f"パステンプレートのフォーマットエラー {path_key}: {e}")
            return path_template
    
    def validate_path_security(self, file_path: str) -> bool:
        """
        パスのセキュリティ検証
        
        Args:
            file_path: 検証するファイルパス
            
        Returns:
            True if safe, False if dangerous
        """
        forbidden_patterns = self.get('paths.security.forbidden_patterns', [])
        
        for pattern in forbidden_patterns:
            if pattern in file_path:
                logger.warning(f"危険なパスパターンを検出: {file_path}")
                return False
                
        return True
    
    def get_server_config(self) -> Dict[str, Any]:
        """サーバー設定の取得（環境変数オーバーライド付き）"""
        config = self.get('server', {})
        
        # 環境変数オーバーライドの適用
        env_mappings = self.get('server.environment_variables', {})
        
        for config_key, env_var in env_mappings.items():
            if config_key == 'SOCKET_PORT':
                config['socket_server']['port'] = self.get_with_env_override(
                    'server.socket_server.port', env_var, 8888
                )
            elif config_key == 'HTTP_PORT':
                config['http_server']['port'] = self.get_with_env_override(
                    'server.http_server.port', env_var, 8000
                )
                
        return config
    
    def export_config(self, output_path: str, format_type: str = 'yaml'):
        """
        現在の設定をファイルに出力
        
        Args:
            output_path: 出力ファイルパス
            format_type: 出力形式（'yaml' または 'json'）
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == 'yaml':
                with open(output_file, 'w', encoding='utf-8') as file:
                    yaml.dump(self._configs, file, 
                             default_flow_style=False, 
                             allow_unicode=True,
                             indent=2)
            elif format_type == 'json':
                with open(output_file, 'w', encoding='utf-8') as file:
                    json.dump(self._configs, file, 
                             indent=2, 
                             ensure_ascii=False)
            else:
                raise ValueError(f"未サポートの出力形式: {format_type}")
                
            logger.info(f"設定ファイル出力完了: {output_file}")
            
        except Exception as e:
            logger.error(f"設定ファイル出力エラー: {e}")
            raise


# グローバル設定管理インスタンス
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """グローバル設定管理インスタンスの取得"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_global_config():
    """グローバル設定の再読み込み"""
    global _config_manager
    if _config_manager:
        _config_manager.reload_config()
    else:
        _config_manager = ConfigManager()


if __name__ == "__main__":
    # 設定管理システムのテスト
    config = ConfigManager()
    
    print("=== TechBridge設定管理システム テスト ===")
    
    # テーマ設定の取得
    print(f"デフォルトテーマ: {config.get('theme.default_theme')}")
    print(f"ライトテーマ背景色: {config.get('theme.themes.light.colors.background')}")
    
    # UI設定の取得
    print(f"テーブル比率: {config.get('ui.layout.main_splitter.table_ratio')}%")
    
    # パス設定の取得とフォーマット
    pdf_path = config.get_path('paths.dynamic_paths.output.pdf_file', n_number='N12345')
    print(f"PDFファイルパス: {pdf_path}")
    
    # サーバー設定の取得
    server_config = config.get_server_config()
    print(f"ソケットポート: {server_config['socket_server']['port']}")
    
    print("=== テスト完了 ===")