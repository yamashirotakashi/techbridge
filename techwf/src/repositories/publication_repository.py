#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publication Repository - データベース操作クラス
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from ..config.database import DatabaseConnection

logger = logging.getLogger(__name__)

class PublicationRepository:
    """出版ワークフロー データベースリポジトリ"""
    
    def __init__(self, db_connection: Union[DatabaseConnection, str]):
        """
        初期化
        
        Args:
            db_connection: DatabaseConnectionオブジェクトまたはデータベースファイルパス（後方互換性のため）
        """
        if isinstance(db_connection, str):
            # 後方互換性：文字列パスの場合はDatabaseConnectionを作成
            self.db_connection = DatabaseConnection(db_connection)
            logger.warning("Using string path for database. Consider using DatabaseConnection object directly.")
        else:
            # DatabaseConnectionオブジェクトを直接使用
            self.db_connection = db_connection
        
        # データベースの初期化はDatabaseConnectionで既に行われているため不要
        logger.info("PublicationRepository initialized with DatabaseConnection")
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """全ワークフローデータを取得"""
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM publications 
                    ORDER BY updated_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []
    
    def get_workflow_by_n_number(self, n_number: str) -> Optional[Dict[str, Any]]:
        """N番号でワークフローデータを取得"""
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM publications WHERE n_number = ?
                """, (n_number,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get workflow {n_number}: {e}")
            return None
    
    def create_or_update_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """ワークフローデータの作成または更新"""
        try:
            with self.db_connection.get_connection() as conn:
                # INSERT OR REPLACE を使用
                conn.execute("""
                    INSERT OR REPLACE INTO publications 
                    (n_number, title, author, status, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    workflow_data.get('n_number'),
                    workflow_data.get('title'),
                    workflow_data.get('author'),
                    workflow_data.get('status', 'discovered'),
                    datetime.now().isoformat()
                ))
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to create/update workflow: {e}")
            return False
    
    def update_workflow_status(self, n_number: str, status: str) -> bool:
        """ワークフローステータス更新"""
        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE publications 
                    SET status = ?, updated_at = ?
                    WHERE n_number = ?
                """, (status, datetime.now().isoformat(), n_number))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update status for {n_number}: {e}")
            return False