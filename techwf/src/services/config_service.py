#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Service - 設定管理サービス
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TechWFConfig:
    """TechWF設定クラス"""
    
    # Google Sheets設定
    sheets_enabled: bool = False
    sheets_id: str = ""
    sheets_credentials_path: str = ""
    
    # Slack設定
    slack_enabled: bool = False
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    
    # データベース設定
    db_path: str = "data/techwf.db"
    
    # UI設定
    theme: str = "default"
    auto_refresh: bool = True
    refresh_interval: int = 30
    
    # ファイル監視設定
    file_watch_enabled: bool = True
    watch_directory: str = "data/import"

class ConfigService:
    """設定サービスクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.config_path = Path(config_path)
        self._config = TechWFConfig()
        self._load_config()
    
    def _load_config(self):
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 設定を更新
                for key, value in data.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
                        
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info("Configuration file not found, using defaults")
                self._save_config()  # デフォルト設定を保存
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
    
    def _save_config(self):
        """設定ファイルを保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """設定値を変更"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._save_config()
        else:
            logger.warning(f"Unknown configuration key: {key}")
    
    def get_all(self) -> Dict[str, Any]:
        """全設定を取得"""
        return asdict(self._config)
    
    def update_config(self, updates: Dict[str, Any]):
        """設定を一括更新"""
        for key, value in updates.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")
        
        self._save_config()
    
    @property
    def sheets_enabled(self) -> bool:
        """Google Sheets有効フラグ"""
        return self._config.sheets_enabled and bool(self._config.sheets_id)
    
    @property
    def slack_enabled(self) -> bool:
        """Slack有効フラグ"""
        return self._config.slack_enabled and bool(self._config.slack_bot_token)
    
    def get_config(self) -> TechWFConfig:
        """設定オブジェクトを取得"""
        return self._config

# シングルトンインスタンス
_config_service: Optional[ConfigService] = None

def get_config_service() -> ConfigService:
    """設定サービスのシングルトンインスタンスを取得"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service

def reset_config_service():
    """設定サービスをリセット（テスト用）"""
    global _config_service
    _config_service = None