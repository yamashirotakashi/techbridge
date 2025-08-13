#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Manager - サービス管理システム
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from ..services.config_service import get_config_service
from ..services.google_sheets_service import create_google_sheets_service
from ..services.slack_service import create_slack_service

logger = logging.getLogger(__name__)

class ServiceManager(QObject):
    """サービス管理クラス"""
    
    # シグナル定義
    sheets_service_changed = Signal(bool)  # Google Sheetsサービス状態変更
    slack_service_changed = Signal(bool)   # Slackサービス状態変更
    service_error = Signal(str, str)       # サービスエラー (service_name, error_message)
    service_initialized = Signal(str)       # サービス初期化完了 (service_name)
    
    def __init__(self):
        """
        初期化
        """
        super().__init__()
        self.config_service = get_config_service()
        self._google_sheets_service = None
        self._slack_service = None
        self._services_initialized = False
        logger.info("ServiceManager initialized")
    
    def initialize_services(self) -> bool:
        """
        サービスを初期化
        
        Returns:
            bool: 初期化成功フラグ
        """
        try:
            logger.info("Initializing external services...")
            
            # Google Sheets サービス
            self._google_sheets_service = create_google_sheets_service(self.config_service)
            logger.info("Google Sheets service created")
            self.service_initialized.emit("google_sheets")
            
            # Slack サービス
            self._slack_service = create_slack_service(self.config_service)
            logger.info("Slack service created")
            self.service_initialized.emit("slack")
            
            # 認証は必要に応じて実行（設定があれば）
            config = self.config_service.get_config()
            
            # Google Sheets認証（認証情報があれば）
            if hasattr(config, 'google_credentials_path') and config.google_credentials_path:
                try:
                    self._google_sheets_service.authenticate(config.google_credentials_path)
                    logger.info("Google Sheets authentication completed")
                    self.sheets_service_changed.emit(True)
                except Exception as e:
                    logger.warning(f"Google Sheets authentication failed: {e}")
                    self.service_error.emit("google_sheets", str(e))
                    self.sheets_service_changed.emit(False)
            else:
                self.sheets_service_changed.emit(False)
            
            # Slack認証（トークンがあれば）
            if hasattr(config, 'slack_bot_token') and config.slack_bot_token:
                try:
                    self._slack_service.authenticate(
                        bot_token=config.slack_bot_token,
                        signing_secret=getattr(config, 'slack_signing_secret', None)
                    )
                    logger.info("Slack authentication completed")
                    self.slack_service_changed.emit(True)
                except Exception as e:
                    logger.warning(f"Slack authentication failed: {e}")
                    self.service_error.emit("slack", str(e))
                    self.slack_service_changed.emit(False)
            else:
                self.slack_service_changed.emit(False)
            
            self._services_initialized = True
            logger.info("All services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            self.service_error.emit("initialization", str(e))
            return False
    
    def get_google_sheets_service(self):
        """
        Google Sheetsサービスを取得
        
        Returns:
            GoogleSheetsService: サービスインスタンス
        """
        if not self._services_initialized:
            self.initialize_services()
        return self._google_sheets_service
    
    def get_slack_service(self):
        """
        Slackサービスを取得
        
        Returns:
            SlackService: サービスインスタンス
        """
        if not self._services_initialized:
            self.initialize_services()
        return self._slack_service
    
    def is_google_sheets_available(self) -> bool:
        """
        Google Sheetsサービスが利用可能か確認
        
        Returns:
            bool: 利用可能フラグ
        """
        try:
            service = self.get_google_sheets_service()
            return service is not None and service.is_authenticated()
        except Exception:
            return False
    
    def is_slack_available(self) -> bool:
        """
        Slackサービスが利用可能か確認
        
        Returns:
            bool: 利用可能フラグ
        """
        try:
            service = self.get_slack_service()
            return service is not None and service.is_authenticated()
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        全サービスの状態を取得
        
        Returns:
            Dict[str, Any]: サービス状態情報
        """
        return {
            'services_initialized': self._services_initialized,
            'google_sheets': {
                'available': self.is_google_sheets_available(),
                'service_exists': self._google_sheets_service is not None
            },
            'slack': {
                'available': self.is_slack_available(),
                'service_exists': self._slack_service is not None
            },
            'config': {
                'loaded': self.config_service is not None
            }
        }
    
    def refresh_services(self) -> bool:
        """
        サービスを再初期化
        
        Returns:
            bool: 成功フラグ
        """
        try:
            logger.info("Refreshing all services...")
            
            # サービスをリセット
            self._google_sheets_service = None
            self._slack_service = None
            self._services_initialized = False
            
            # 再初期化
            return self.initialize_services()
            
        except Exception as e:
            logger.error(f"Failed to refresh services: {e}")
            return False
    
    def test_google_sheets_connection(self) -> bool:
        """
        Google Sheets接続をテスト
        
        Returns:
            bool: 接続成功フラグ
        """
        try:
            service = self.get_google_sheets_service()
            if not service or not service.is_authenticated():
                return False
            
            # テスト用のダミーリクエスト（実際の実装では認証確認）
            logger.info("Testing Google Sheets connection...")
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False
    
    def test_slack_connection(self) -> bool:
        """
        Slack接続をテスト
        
        Returns:
            bool: 接続成功フラグ
        """
        try:
            service = self.get_slack_service()
            if not service or not service.is_authenticated():
                return False
            
            # テスト用のダミーリクエスト（実際の実装では認証確認）
            logger.info("Testing Slack connection...")
            return True
            
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False

# グローバル サービスマネージャー
_service_manager: Optional[ServiceManager] = None

def get_service_manager() -> ServiceManager:
    """サービスマネージャーのシングルトンインスタンスを取得"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager