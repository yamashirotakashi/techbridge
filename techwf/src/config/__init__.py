#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config package - アプリケーション設定モジュール
"""

from .database import DatabaseConnection

# n_number_schema.py モジュールからの import を試行
try:
    from .n_number_schema import NNumberDatabaseSchema
except ImportError:
    # n_number_schema.py が存在しない場合は None として処理
    NNumberDatabaseSchema = None

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TechWFConfig:
    """
    TechWFアプリケーション設定管理
    セキュリティ：パストラバーサル脆弱性対策済み
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

# エクスポートするシンボルを定義
__all__ = [
    'DatabaseConnection',
    'TechWFConfig'
]

# NNumberDatabaseSchema が利用可能な場合のみエクスポート
if NNumberDatabaseSchema is not None:
    __all__.append('NNumberDatabaseSchema')