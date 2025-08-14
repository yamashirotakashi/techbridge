#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge設定管理システム
外部化されたYAML設定ファイルの統合管理パッケージ

Phase 4完了: 外部設定ファイル構造実装
- 基本設定管理 (ConfigManager)
- 設定検証システム (ConfigValidator) 
- ファイル監視システム (ConfigWatcher)
- 統合管理システム (EnhancedConfigManager)

レガシー設定管理も引き続きサポート
"""

# バージョン情報
__version__ = "1.0.0"
__phase__ = "Phase 4 Complete"

# レガシー設定管理（後方互換性）
from .database import DatabaseConnection

# n_number_schema.py モジュールからの import を試行
try:
    from .n_number_schema import NNumberDatabaseSchema
except ImportError:
    # n_number_schema.py が存在しない場合は None として処理
    NNumberDatabaseSchema = None

# 新しい外部設定管理システム
try:
    from .config_manager import (
        ConfigManager,
        ConfigPaths,
        get_config_manager,
        reload_global_config
    )
    
    from .config_validator import (
        ConfigValidator,
        ValidationError,
        ValidationResult
    )
    
    from .config_watcher import (
        ConfigWatcher,
        ConfigChange,
        ConfigWatcherManager
    )
    
    from .enhanced_config_manager import (
        EnhancedConfigManager,
        get_enhanced_config_manager,
        cleanup_enhanced_config_manager
    )
    
    # 新システムが利用可能
    NEW_CONFIG_SYSTEM_AVAILABLE = True
    
except ImportError as e:
    # 新システムの依存関係が満たされていない場合
    NEW_CONFIG_SYSTEM_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"新しい設定システムが利用できません: {e}")

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TechWFConfig:
    """
    TechWFアプリケーション設定管理（レガシー）
    セキュリティ：パストラバーサル脆弱性対策済み
    
    注意: 新しいプロジェクトではEnhancedConfigManagerの使用を推奨
    """
    
    # デフォルト設定
    DEFAULT_DB_NAME = "techwf.db"
    DEFAULT_DATA_DIR = "data"
    
    @classmethod
    def get_project_root(cls) -> Path:
        """
        プロジェクトルートディレクトリの取得
        
        Returns:
            Path: プロジェクトルートの絶対パス
        """
        # 現在のファイルから3階層上がプロジェクトルート (src/config -> src -> techwf -> project)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        return project_root
    
    @classmethod
    def get_data_directory(cls) -> Path:
        """
        データディレクトリの安全な取得
        
        Returns:
            Path: データディレクトリの絶対パス
        """
        project_root = cls.get_project_root()
        data_dir = project_root / cls.DEFAULT_DATA_DIR
        
        # ディレクトリの作成（存在しない場合）
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Data directory ensured: {data_dir}")
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            raise
            
        return data_dir
    
    @classmethod
    def get_database_path(cls, db_name: Optional[str] = None) -> str:
        """
        データベースファイルパスの安全な取得
        
        Args:
            db_name: データベースファイル名（デフォルト: techwf.db）
            
        Returns:
            str: データベースファイルの絶対パス（文字列）
            
        Raises:
            ValueError: 不正なファイル名が指定された場合
        """
        if db_name is None:
            db_name = cls.DEFAULT_DB_NAME
            
        # セキュリティ: ファイル名の検証（パストラバーサル対策）
        if not cls._is_safe_filename(db_name):
            raise ValueError(f"Unsafe database filename: {db_name}")
            
        data_dir = cls.get_data_directory()
        return str(data_dir / db_name)
    
    @classmethod
    def _is_safe_filename(cls, filename: str) -> bool:
        """
        ファイル名の安全性チェック
        
        Args:
            filename: チェックするファイル名
            
        Returns:
            bool: 安全な場合True
        """
        # 不正な文字・パターンの検証
        import re
        
        # パストラバーサル攻撃対策
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
            
        # ファイル名として適切な文字のみ許可（英数字、ハイフン、アンダースコア、ドット）
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            return False
            
        # 拡張子チェック（.dbファイルのみ許可）
        if not filename.endswith('.db'):
            return False
            
        return True

# 簡易アクセス用のファクトリ関数
def create_config_system(project_root: str = None, 
                        enable_monitoring: bool = True,
                        enable_validation: bool = True,
                        enable_auto_repair: bool = True):
    """
    TechBridge設定システムの作成（推奨方法）
    
    Args:
        project_root: プロジェクトルートディレクトリ
        enable_monitoring: ファイル監視の有効化
        enable_validation: 設定検証の有効化  
        enable_auto_repair: 自動修復の有効化
        
    Returns:
        EnhancedConfigManagerインスタンス（利用可能な場合）
        
    Usage:
        # 基本的な使用方法
        with create_config_system() as config:
            theme = config.get('theme.default_theme')
            port = config.get_with_env_override('server.socket_server.port', 'TECHWF_PORT', 8888)
    """
    if not NEW_CONFIG_SYSTEM_AVAILABLE:
        logger.error("新しい設定システムが利用できません。依存関係を確認してください。")
        return None
    
    enhanced_manager = EnhancedConfigManager(
        project_root=project_root,
        auto_start_watching=enable_monitoring
    )
    
    if not enable_validation:
        enhanced_manager.disable_validation()
    if not enable_auto_repair:
        enhanced_manager.disable_auto_repair()
    
    return enhanced_manager

# バージョン情報表示
def show_system_info():
    """設定システム情報の表示"""
    print(f"TechBridge Configuration System")
    print(f"Version: {__version__}")
    print(f"Phase: {__phase__}")
    print(f"New System Available: {'Yes' if NEW_CONFIG_SYSTEM_AVAILABLE else 'No'}")
    if NEW_CONFIG_SYSTEM_AVAILABLE:
        print(f"Components:")
        print(f"  - ConfigManager: 基本設定管理")
        print(f"  - ConfigValidator: 設定検証・フォールバック")
        print(f"  - ConfigWatcher: リアルタイム監視")
        print(f"  - EnhancedConfigManager: 統合管理（推奨）")
    print(f"Legacy:")
    print(f"  - TechWFConfig: レガシー設定管理")
    print(f"  - DatabaseConnection: データベース接続")

# エクスポートするシンボルを定義（後方互換性）
__all__ = [
    'DatabaseConnection',
    'TechWFConfig',
    'create_config_system',
    'show_system_info',
    '__version__',
    '__phase__'
]

# NNumberDatabaseSchema が利用可能な場合のみエクスポート
if NNumberDatabaseSchema is not None:
    __all__.append('NNumberDatabaseSchema')

# 新しい設定システムが利用可能な場合はエクスポート
if NEW_CONFIG_SYSTEM_AVAILABLE:
    __all__.extend([
        'ConfigManager',
        'ConfigPaths', 
        'get_config_manager',
        'reload_global_config',
        'ConfigValidator',
        'ValidationError',
        'ValidationResult',
        'ConfigWatcher', 
        'ConfigChange',
        'ConfigWatcherManager',
        'EnhancedConfigManager',
        'get_enhanced_config_manager',
        'cleanup_enhanced_config_manager',
    ])