"""
Settings and configuration management for PJINIT
TechBridge統合用の設定管理
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
# structlogの代替ログ実装
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    # structlogが無い場合は、printを使ったロガーを作成
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = SimpleLogger()


class PJINITSettings:
    """PJINIT専用設定クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.techbridge_root = self.project_root.parent.parent.parent
        self._load_environment()
        self._validate_settings()
        
    def _load_environment(self):
        """環境変数とconfigファイルから設定を読み込み"""
        
        # .envファイルの読み込み（オプション）
        try:
            from dotenv import load_dotenv
        except ImportError:
            # dotenvが無い場合はスキップ
            def load_dotenv(file_path):
                pass
        
        # 優先順位: ローカル -> 親ディレクトリ -> TechBridgeルート
        env_files = [
            self.project_root / ".env",
            self.project_root.parent / ".env", 
            self.techbridge_root / ".env"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                print(f"✅ 環境設定読み込み: {env_file}")
                break
        
        # TechBridge設定の参照を試行
        try:
            import sys
            sys.path.insert(0, str(self.techbridge_root))
            from app.core.config import settings as techbridge_settings
            self.techbridge_available = True
            self._import_techbridge_settings(techbridge_settings)
        except ImportError as e:
            print(f"⚠️ TechBridge設定を読み込めません: {e}")
            self.techbridge_available = False
            self._load_local_settings()
    
    def _import_techbridge_settings(self, techbridge_settings):
        """TechBridge設定のインポート"""
        self.SLACK_BOT_TOKEN = getattr(techbridge_settings, 'SLACK_BOT_TOKEN', None)
        self.SLACK_SIGNING_SECRET = getattr(techbridge_settings, 'SLACK_SIGNING_SECRET', None)
        self.GOOGLE_SHEETS_ID = getattr(techbridge_settings, 'GOOGLE_SHEETS_ID', None)
        self.GOOGLE_SERVICE_ACCOUNT_KEY = getattr(techbridge_settings, 'GOOGLE_SERVICE_ACCOUNT_KEY', None)
        self.GITHUB_TOKEN = getattr(techbridge_settings, 'GITHUB_TOKEN', None)
        self.GITHUB_ORG = getattr(techbridge_settings, 'GITHUB_ORG', None)
        logger.info("✅ TechBridge設定を統合しました")
        
    def _load_local_settings(self):
        """ローカル設定の読み込み"""
        self.SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
        self.SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
        self.GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
        self.GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        self.GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
        self.GITHUB_ORG = os.getenv('GITHUB_ORG')
        logger.info("⚠️ ローカル環境変数から設定を読み込みました")
        
    def _validate_settings(self):
        """設定の妥当性チェック"""
        self.services_status = {
            'slack': bool(self.SLACK_BOT_TOKEN and self.SLACK_BOT_TOKEN not in ['xoxb-your-slack-bot-token', '']),
            'google_sheets': bool(self.GOOGLE_SHEETS_ID and self.GOOGLE_SERVICE_ACCOUNT_KEY and 
                                 self.GOOGLE_SHEETS_ID not in ['your-google-sheets-id', '']),
            'github': bool(self.GITHUB_TOKEN and self.GITHUB_TOKEN not in ['ghp_your-github-token', 'your-github-token-here', ''])
        }
        
        available_services = [k for k, v in self.services_status.items() if v]
        if available_services:
            logger.info(f"✅ 利用可能なサービス: {', '.join(available_services)}")
        else:
            logger.warning("⚠️ 外部サービス設定が見つかりません")
    
    def get_service_status(self) -> Dict[str, bool]:
        """サービス状態を取得"""
        return self.services_status.copy()
        
    def is_service_available(self, service: str) -> bool:
        """サービスが利用可能かチェック"""
        return self.services_status.get(service, False)


# グローバル設定インスタンス
settings = PJINITSettings()