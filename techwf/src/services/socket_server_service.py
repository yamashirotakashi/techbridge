#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Socket Server Service - ソケット通信サービス
Phase 3 Refactoring: 外部通信の統合管理
"""

import logging
import socket
import threading
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SocketServerError(Exception):
    """ソケットサーバーエラー"""
    pass

class MessageType(Enum):
    """メッセージタイプ"""
    STATUS_UPDATE = "status_update"
    DATA_SYNC = "data_sync"
    WORKFLOW_UPDATE = "workflow_update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

class SocketServerService:
    """ソケットサーバーサービス"""
    
    def __init__(self, config_service=None):
        """
        初期化
        
        Args:
            config_service: 設定サービス
        """
        self.config_service = config_service
        self._server_socket = None
        self._clients = {}  # {client_id: socket}
        self._running = False
        self._server_thread = None
        self._message_handlers = {}
        
        # デフォルト設定
        self.host = "localhost"
        self.port = 8888
        self.max_clients = 10
        
        logger.info("SocketServerService initialized (stub implementation)")
    
    def start_server(self, host: str = None, port: int = None) -> bool:
        """
        サーバーを開始
        
        Args:
            host: ホストアドレス
            port: ポート番号
        
        Returns:
            bool: 開始成功フラグ
        """
        try:
            if self._running:
                logger.warning("Server is already running")
                return False
            
            self.host = host or self.host
            self.port = port or self.port
            
            logger.info(f"Starting socket server on {self.host}:{self.port}...")
            
            # スタブ実装 - 実際のソケットサーバーは後で実装
            # self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # self._server_socket.bind((self.host, self.port))
            # self._server_socket.listen(self.max_clients)
            
            self._running = True
            
            # サーバースレッドを開始（シミュレート）
            self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self._server_thread.start()
            
            logger.info(f"Socket server started successfully (simulated): {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start socket server: {e}")
            raise SocketServerError(f"Server start failed: {e}")
    
    def stop_server(self) -> bool:
        """
        サーバーを停止
        
        Returns:
            bool: 停止成功フラグ
        """
        try:
            if not self._running:
                logger.warning("Server is not running")
                return False
            
            logger.info("Stopping socket server...")
            
            self._running = False
            
            # クライアント接続を閉じる
            for client_id, client_socket in self._clients.items():
                try:
                    if client_socket:
                        logger.info(f"Closing client connection: {client_id} (simulated)")
                        # client_socket.close()
                except Exception as e:
                    logger.error(f"Error closing client {client_id}: {e}")
            
            self._clients.clear()
            
            # サーバーソケットを閉じる
            if self._server_socket:
                # self._server_socket.close()
                self._server_socket = None
            
            # サーバースレッドの終了を待つ
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=5.0)
            
            logger.info("Socket server stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop socket server: {e}")
            return False
    
    def is_running(self) -> bool:
        """サーバーが動作中か確認"""
        return self._running
    
    def send_message_to_client(self, client_id: str, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        特定のクライアントにメッセージを送信
        
        Args:
            client_id: クライアントID
            message_type: メッセージタイプ
            data: 送信データ
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            if not self._running:
                raise SocketServerError("Server is not running")
            
            if client_id not in self._clients:
                logger.warning(f"Client not found: {client_id}")
                return False
            
            message = {
                "type": message_type.value,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # スタブ実装 - メッセージ送信をシミュレート
            logger.info(f"Sending message to {client_id}: {message_type.value}")
            logger.debug(f"Message data: {data}")
            
            # 実際の実装では:
            # client_socket = self._clients[client_id]
            # message_json = json.dumps(message)
            # client_socket.send(message_json.encode('utf-8'))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            return False
    
    def broadcast_message(self, message_type: MessageType, data: Dict[str, Any]) -> int:
        """
        全クライアントにメッセージをブロードキャスト
        
        Args:
            message_type: メッセージタイプ
            data: 送信データ
        
        Returns:
            int: 送信成功したクライアント数
        """
        success_count = 0
        
        for client_id in list(self._clients.keys()):
            if self.send_message_to_client(client_id, message_type, data):
                success_count += 1
        
        logger.info(f"Broadcast message sent to {success_count}/{len(self._clients)} clients")
        return success_count
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """
        メッセージハンドラーを登録
        
        Args:
            message_type: メッセージタイプ
            handler: ハンドラー関数
        """
        self._message_handlers[message_type] = handler
        logger.info(f"Message handler registered: {message_type.value}")
    
    def get_client_list(self) -> List[str]:
        """
        接続中のクライアント一覧を取得
        
        Returns:
            List[str]: クライアントIDリスト
        """
        return list(self._clients.keys())
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        サーバー状態を取得
        
        Returns:
            Dict[str, Any]: サーバー状態情報
        """
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "client_count": len(self._clients),
            "clients": list(self._clients.keys()),
            "max_clients": self.max_clients
        }
    
    def _server_loop(self):
        """サーバーメインループ（スタブ実装）"""
        try:
            logger.info("Server loop started (simulated)")
            
            # スタブ実装 - サンプルクライアントを追加
            import time
            time.sleep(1)  # 起動待機
            
            # サンプルクライアント接続をシミュレート
            if self._running:
                self._clients["client_001"] = "simulated_socket_001"
                logger.info("Sample client connected: client_001")
            
            while self._running:
                time.sleep(1)
                # 実際の実装では:
                # client_socket, address = self._server_socket.accept()
                # self._handle_client_connection(client_socket, address)
            
            logger.info("Server loop ended")
            
        except Exception as e:
            logger.error(f"Server loop error: {e}")
            self._running = False
    
    def _handle_client_connection(self, client_socket, address):
        """クライアント接続処理（スタブ実装）"""
        # 実装予定: クライアントとの通信処理
        pass
    
    def _handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """クライアントメッセージ処理（スタブ実装）"""
        try:
            message_type = MessageType(message.get('type', ''))
            data = message.get('data', {})
            
            # 登録されたハンドラーを実行
            if message_type in self._message_handlers:
                handler = self._message_handlers[message_type]
                handler(client_id, data)
            
            logger.debug(f"Message handled: {client_id}, {message_type.value}")
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")

# ファクトリー関数
def create_socket_server_service(config_service=None) -> SocketServerService:
    """
    SocketServerServiceを作成
    
    Args:
        config_service: 設定サービス
        
    Returns:
        SocketServerService: サービスインスタンス
    """
    return SocketServerService(config_service)