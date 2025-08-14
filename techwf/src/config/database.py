#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Configuration - データベース接続設定クラス
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """データベース接続管理クラス"""
    
    def __init__(self, db_path: str = "techwf.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス（デフォルト: techwf.db）
        """
        self.db_path = db_path
        self._ensure_database_directory()
        self._initialize_tables()
        
    def _ensure_database_directory(self):
        """データベースディレクトリの作成"""
        try:
            db_dir = Path(self.db_path).parent
            if str(db_dir) != '.':  # カレントディレクトリ以外の場合
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Database directory ensured: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")
            raise
    
    def _initialize_tables(self):
        """データベーステーブルの初期化"""
        try:
            with self.get_connection() as conn:
                # publications テーブル
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS publications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        n_number TEXT UNIQUE NOT NULL,
                        title TEXT,
                        author TEXT,
                        status TEXT DEFAULT 'discovered',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # その他必要なテーブルを追加
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        n_number TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (n_number) REFERENCES publications (n_number)
                    )
                """)
                
                conn.commit()
                logger.info(f"Database tables initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Database table initialization failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        データベース接続のコンテキストマネージャー
        
        Yields:
            sqlite3.Connection: データベース接続オブジェクト
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 行を辞書のようにアクセス可能にする
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """
        SQLクエリの実行
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
            
        Returns:
            list: SELECT文の場合は結果リスト、その他はNone
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                
                # SELECT文の場合は結果を返す
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return None
                    
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[dict]:
        """
        単一行を返すSQLクエリの実行
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ
            
        Returns:
            dict: 結果の単一行、見つからない場合はNone
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Single query execution failed: {e}")
            raise
    
    def check_health(self) -> bool:
        """
        データベース接続の健全性チェック
        
        Returns:
            bool: 接続が正常な場合True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> list:
        """
        テーブル情報の取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            list: テーブルのカラム情報
        """
        # セキュリティ: テーブル名の厳格な検証（SQL Injection対策）
        # SQLiteの識別子は英数字とアンダースコアのみ許可
        import re
        
        # より厳格な入力検証：SQLite識別子規則に準拠
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            logger.error(f"Invalid table name format: {table_name}")
            raise ValueError(f"Invalid table name format: {table_name}")
        
        # 追加セキュリティ: テーブル名の長さ制限
        if len(table_name) > 64:
            logger.error(f"Table name too long: {table_name}")
            raise ValueError(f"Table name exceeds maximum length: {table_name}")
        
        # SQLインジェクション対策: 既知の危険パターンチェック
        dangerous_patterns = ['--', ';', '/*', '*/', 'union', 'select', 'drop', 'delete', 'insert', 'update']
        table_name_lower = table_name.lower()
        for pattern in dangerous_patterns:
            if pattern in table_name_lower:
                logger.error(f"Dangerous pattern detected in table name: {table_name}")
                raise ValueError(f"Dangerous pattern detected in table name: {table_name}")
        
        try:
            with self.get_connection() as conn:
                # SQLite PRAGMA文はパラメータ化クエリをサポートしていないため、
                # 厳格な入力検証後にf-stringを使用（セキュリティ承認済み）
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return []
    
    def backup_database(self, backup_path: str) -> bool:
        """
        データベースのバックアップ
        
        Args:
            backup_path: バックアップファイルパス
            
        Returns:
            bool: バックアップが成功した場合True
        """
        try:
            # バックアップディレクトリの作成
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source:
                backup_conn = sqlite3.connect(backup_path)
                source.backup(backup_conn)
                backup_conn.close()
                
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False