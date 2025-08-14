"""
Service Adapter Pattern for PJINIT
TechBridgeサービス層への統一インターフェース
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
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

# TechBridgeサービス層への相対パスを追加
techbridge_root = Path(__file__).parent.parent.parent.parent
if str(techbridge_root) not in sys.path:
    sys.path.insert(0, str(techbridge_root))

# TechBridge app servicesパスも追加
app_services_path = techbridge_root / "app"
if str(app_services_path) not in sys.path:
    sys.path.insert(0, str(app_services_path))

try:
    from services.google_sheets import GoogleSheetsService
    from services.slack import SlackService
    from services.github import GitHubService
    from core.config import settings
    SERVICES_AVAILABLE = True
    print(f"✅ TechBridge services loaded successfully from {app_services_path}")
except ImportError as e:
    # Fallback: 独立したGoogle Sheets実装を使用
    try:
        print(f"[WARN] TechBridge services import failed: {e}")
        print("[INFO] Falling back to standalone Google Sheets implementation")
        SERVICES_AVAILABLE = False
    except UnicodeEncodeError:
        print("[WARN] TechBridge services import failed - encoding error")
        SERVICES_AVAILABLE = False


class ServiceAdapter:
    """
    TechBridgeサービス層への統一アダプター
    各種外部サービスへの一貫したインターフェースを提供
    """
    
    def __init__(self):
        self.google_sheets = None
        self.slack_service = None
        self.github_client = None
        
        if SERVICES_AVAILABLE:
            self._initialize_services()
    
    def _initialize_services(self):
        """サービスの初期化"""
        try:
            # Google Sheets Service
            if hasattr(settings, 'GOOGLE_SHEETS_ID') and settings.GOOGLE_SHEETS_ID:
                self.google_sheets = GoogleSheetsService()
                print("✅ Google Sheets Service initialized")
                
            # Slack Service  
            if hasattr(settings, 'SLACK_BOT_TOKEN') and settings.SLACK_BOT_TOKEN:
                self.slack_service = SlackService()
                print("✅ Slack Service initialized")
                
            # GitHub Service
            if hasattr(settings, 'GITHUB_TOKEN') and settings.GITHUB_TOKEN:
                self.github_client = GitHubService()
                print("✅ GitHub Service initialized")
            
        except Exception as e:
            print(f"❌ サービス初期化エラー: {e}")
            
    def is_available(self, service: str) -> bool:
        """サービスが利用可能かチェック"""
        service_map = {
            'google_sheets': self.google_sheets,
            'slack': self.slack_service, 
            'github': self.github_client
        }
        return service_map.get(service) is not None
        
    async def get_project_info(self, n_code: str) -> Optional[Dict[str, Any]]:
        """N-codeからプロジェクト情報を取得"""
        if not self.google_sheets:
            print(f"❌ Google Sheetsサービスが利用できません")
            return None
            
        try:
            project_info = self.google_sheets.search_n_code(n_code)
            if not project_info:
                print(f"❌ Nコード {n_code} のプロジェクト情報が見つかりません")
                return None
            return project_info
        except Exception as e:
            print(f"❌ プロジェクト情報取得エラー: {e}")
            return None
            
    def _get_mock_project_info(self, n_code: str) -> Optional[Dict[str, Any]]:
        """モックプロジェクト情報を生成（サービス利用不可時のフォールバック）"""
        # 既知のテストデータ
        mock_data = {
            "N02280": {
                "n_code": "N02280",
                "book_title": "Pythonではじめる機械学習入門",
                "author": "山田太郎",
                "publisher": "技術評論社",
                "status": "企画中",
                "slack_channel": "#book-n02280",
                "repository_name": "ml-python-intro"
            },
            "N09999": {
                "n_code": "N09999",
                "book_title": "テスト書籍データ",
                "author": "テスト著者",
                "publisher": "テスト出版社", 
                "status": "テスト中",
                "slack_channel": "#book-n09999",
                "repository_name": "test-book"
            },
            "N0271VG": {
                "n_code": "N0271VG",
                "book_title": "Claude AIを活用した開発効率化",
                "author": "AI開発者",
                "publisher": "未来技術出版",
                "status": "執筆中",
                "slack_channel": "#book-n0271vg",
                "repository_name": "claude-dev-efficiency"
            }
        }
        
        if n_code in mock_data:
            print(f"[INFO] モックデータを返します: {n_code}")
            return mock_data[n_code]
        else:
            print(f"[WARN] Nコード {n_code} のデータが見つかりません（モックデータ）")
            # デフォルトのモックデータを生成
            return {
                "n_code": n_code,
                "book_title": f"書籍 {n_code}",
                "author": "不明",
                "publisher": "未定",
                "status": "企画中",
                "slack_channel": f"#book-{n_code.lower()}",
                "repository_name": f"book-{n_code.lower()}"
            }
            
    async def create_slack_channel(self, channel_name: str) -> Optional[str]:
        """Slackチャンネルを作成"""
        if not self.slack_service:
            return None
            
        try:
            channel_id = await self._run_in_executor(
                self.slack_service.create_channel, channel_name
            )
            return channel_id
        except Exception as e:
            print(f"❌ Slackチャンネル作成エラー: {e}")
            return None
            
    async def invite_to_slack_channel(self, channel_id: str, user_email: str) -> bool:
        """Slackチャンネルにユーザーを招待"""
        if not self.slack_service:
            return False
            
        try:
            success = await self._run_in_executor(
                self.slack_service.invite_user, channel_id, user_email
            )
            return success
        except Exception as e:
            print(f"❌ Slack招待エラー: {e}")
            return False
            
    async def create_github_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        """GitHubリポジトリを作成"""
        if not self.github_client:
            print("⚠️ GitHub client not available")
            return None
            
        try:
            # GitHubサービス経由でリポジトリを作成
            repo_url = await self._run_in_executor(
                self.github_client.create_repository,
                repo_name, description, False, True  # private=False, auto_init=True
            )
            return repo_url
        except Exception as e:
            print(f"❌ GitHubリポジトリ作成エラー: {e}")
            return None
        
    async def _run_in_executor(self, func, *args, **kwargs):
        """同期関数を非同期で実行"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
        

# Factory pattern for service creation
def create_service_adapter() -> ServiceAdapter:
    """ServiceAdapterのファクトリー関数"""
    return ServiceAdapter()


# Legacy compatibility layer
class GoogleSheetsClient:
    """Legacy GoogleSheetsClient compatibility"""
    
    def __init__(self, service_account_path: str = None):
        """
        Legacy互換性のため、service_account_pathパラメータを受け取るが、
        実際の設定はPJINITSettingsから読み込む
        """
        self.service_account_path = service_account_path
        self.adapter = create_service_adapter()
        
        # Legacy warning
        if service_account_path:
            print(f"[INFO] GoogleSheetsClient: service_account_path={service_account_path} (設定は PJINITSettings から読み込まれます)")
        
    async def get_project_info(self, planning_sheet_id: str = None, n_code: str = None) -> Optional[Dict[str, Any]]:
        """Legacy compatibility: プロジェクト情報取得
        
        オリジナル版互換性のため、planning_sheet_idとn_codeの両方を受け取る
        実際の処理はn_codeのみを使用
        """
        # 引数の順序対応: get_project_info(planning_sheet_id, n_code)
        if planning_sheet_id is not None and n_code is None:
            # 単一引数の場合はn_codeとして扱う
            actual_n_code = planning_sheet_id
        else:
            # 2引数の場合は2番目をn_codeとして使用
            actual_n_code = n_code
            
        if planning_sheet_id and n_code:
            print(f"[INFO] GoogleSheetsClient.get_project_info: sheet_id={planning_sheet_id}, n_code={n_code}")
            
        return await self.adapter.get_project_info(actual_n_code)
    
    async def get_book_url_from_purchase_list(self, purchase_sheet_id: str = None, n_code: str = None) -> Optional[str]:
        """Legacy compatibility: 購入リストからBook URLを取得
        
        オリジナル版互換性のため、purchase_sheet_idとn_codeの両方を受け取る
        実際の処理はn_codeのみを使用
        """
        # 引数の順序対応: get_book_url_from_purchase_list(purchase_sheet_id, n_code)
        if purchase_sheet_id is not None and n_code is None:
            # 単一引数の場合はn_codeとして扱う
            actual_n_code = purchase_sheet_id
        else:
            # 2引数の場合は2番目をn_codeとして使用
            actual_n_code = n_code
            
        if purchase_sheet_id and n_code:
            print(f"[INFO] GoogleSheetsClient.get_book_url_from_purchase_list: sheet_id={purchase_sheet_id}, n_code={n_code}")
        
        # モックデータを返す（実装準備中）
        mock_urls = {
            "N02280": "https://techbook.example.com/books/n02280",
            "N09999": "https://techbook.example.com/books/n09999", 
            "N0271VG": "https://techbook.example.com/books/n0271vg"
        }
        
        if actual_n_code and actual_n_code in mock_urls:
            print(f"[INFO] モック書籍URLを返します: {actual_n_code}")
            return mock_urls[actual_n_code]
        else:
            print(f"[WARN] Nコード {actual_n_code} の書籍URLが見つかりません（モックデータ）")
            return f"https://techbook.example.com/books/{actual_n_code.lower()}" if actual_n_code else None
    
    async def update_book_url(self, n_code: str, book_url: str) -> bool:
        """Legacy compatibility: Book URL更新"""
        # 現在はプレースホルダー実装
        print(f"[WARN] update_book_url({n_code}, {book_url}) - Not implemented yet")
        return False
    
    async def add_manual_task_record(self, n_code: str, task_description: str) -> bool:
        """Legacy compatibility: 手動タスク記録追加"""
        # 現在はプレースホルダー実装
        print(f"[WARN] add_manual_task_record({n_code}, {task_description}) - Not implemented yet")
        return False
        

class SlackClient:
    """Legacy SlackClient compatibility"""
    
    def __init__(self):
        self.adapter = create_service_adapter()
        
    async def create_channel(self, channel_name: str) -> Optional[str]:
        return await self.adapter.create_slack_channel(channel_name)
        
    async def invite_user(self, channel_id: str, user_email: str) -> bool:
        return await self.adapter.invite_to_slack_channel(channel_id, user_email)


class GitHubClient:
    """Legacy GitHubClient compatibility"""
    
    def __init__(self):
        self.adapter = create_service_adapter()
        
    async def create_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        return await self.adapter.create_github_repo(repo_name, description)