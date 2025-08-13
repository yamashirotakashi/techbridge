#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N Number Integration Database Schema
N番号統合基盤用のデータベーススキーマ定義
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

class NNumberDatabaseSchema:
    """N番号統合基盤データベーススキーマ管理"""
    
    def __init__(self, db_path: str = "techwf_n_integration.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self._ensure_database_directory()
        self._initialize_n_number_tables()
    
    def _ensure_database_directory(self):
        """データベースディレクトリの作成"""
        try:
            db_dir = Path(self.db_path).parent
            if str(db_dir) != '.':
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Database directory ensured: {db_dir}")
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")
            raise
    
    def _initialize_n_number_tables(self):
        """N番号統合基盤テーブルの初期化"""
        try:
            with self.get_connection() as conn:
                # N番号マスターテーブル
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS n_number_master (
                        n_number TEXT PRIMARY KEY NOT NULL,
                        title TEXT NOT NULL,
                        current_stage TEXT DEFAULT 'proposal_draft',
                        project_metadata TEXT,  -- JSON形式のメタデータ
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # ワークフローステージテーブル
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_stages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        n_number TEXT NOT NULL,
                        stage_type TEXT NOT NULL,  -- proposal_draft/proposal/specification
                        stage_status TEXT DEFAULT 'not_started',
                        stage_data TEXT,  -- JSON形式のステージ固有データ
                        completed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (n_number) REFERENCES n_number_master (n_number),
                        UNIQUE(n_number, stage_type)
                    )
                """)
                
                # サービス統合テーブル
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS service_integrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        n_number TEXT NOT NULL,
                        service_type TEXT NOT NULL,  -- pjinit/techzip/gpt5
                        integration_status TEXT DEFAULT 'pending',
                        api_request_data TEXT,   -- JSON形式のリクエストデータ
                        api_response_data TEXT,  -- JSON形式のレスポンスデータ
                        executed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (n_number) REFERENCES n_number_master (n_number)
                    )
                """)
                
                # インデックス作成
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_workflow_stages_n_number 
                    ON workflow_stages(n_number)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_service_integrations_n_number 
                    ON service_integrations(n_number)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_service_integrations_status 
                    ON service_integrations(integration_status)
                """)
                
                conn.commit()
                logger.info(f"N-Number integration tables initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"N-Number table initialization failed: {e}")
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
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_table_info(self, table_name: str) -> list:
        """
        テーブル情報の取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            list: テーブルのカラム情報
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return []
    
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