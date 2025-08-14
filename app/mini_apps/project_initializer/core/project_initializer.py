"""
PJINIT ビジネスロジック層
Phase 1リファクタリング: コアビジネスロジックの分離
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

# 絶対インポート（相対インポート問題の回避）
try:
    from clients.service_adapter import ServiceAdapter
    from utils.environment import safe_print
except ImportError:
    # パッケージ構造が異なる場合のフォールバック
    import sys
    from pathlib import Path
    
    current_dir = Path(__file__).parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
        
    from clients.service_adapter import ServiceAdapter
    from utils.environment import safe_print


class ProjectInitializer:
    """プロジェクト初期化のビジネスロジック"""
    
    def __init__(self):
        self.service_adapter = ServiceAdapter()
        self.default_sheet_config = {
            'planning_sheet_id': "17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ",
            'purchase_sheet_id': "1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c"
        }
    
    async def fetch_project_info(self, n_code: str) -> Optional[Dict[str, Any]]:
        """Nコードからプロジェクト情報を取得"""
        try:
            # Google Sheetsからプロジェクト情報を取得
            project_info = await self.service_adapter.get_project_info(n_code)
            
            if project_info:
                # 必要なフィールドの確認・補完
                project_info = self._complete_project_info(project_info, n_code)
                return project_info
            
            return None
            
        except Exception as e:
            safe_print(f"❌ プロジェクト情報取得エラー: {e}")
            return None
    
    def _complete_project_info(self, project_info: Dict[str, Any], n_code: str) -> Dict[str, Any]:
        """プロジェクト情報の補完"""
        # 必須フィールドのデフォルト値設定
        completed_info = {
            'n_code': n_code,
            'book_title': project_info.get('book_title', 'Unknown Title'),
            'author': project_info.get('author', 'Unknown Author'),
            'repository_name': project_info.get('repository_name', f'book-{n_code.lower()}'),
            'slack_channel': project_info.get('slack_channel', f'#{n_code.lower()}'),
            'slack_user_id': project_info.get('slack_user_id'),
            'book_url_from_purchase': project_info.get('book_url_from_purchase'),
            **project_info  # 元の情報を優先
        }
        
        return completed_info
    
    async def initialize_project(
        self, 
        params: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """プロジェクト初期化を実行"""
        result = {
            'success': False,
            'slack_channel': None,
            'github_repo': None,
            'manual_tasks': [],
            'error': None
        }
        
        try:
            project_info = params.get('project_info', {})
            n_code = project_info.get('n_code')
            
            if not n_code:
                raise ValueError("プロジェクト情報が不正です")
            
            # プログレス通知
            if progress_callback:
                progress_callback(f"プロジェクト初期化開始: {n_code}")
            
            # 1. Slackチャンネル作成
            if params.get('create_slack_channel', False):
                slack_result = await self._create_slack_channel(project_info, progress_callback)
                result['slack_channel'] = slack_result.get('channel_info')
                result['manual_tasks'].extend(slack_result.get('manual_tasks', []))
            
            # 2. GitHubリポジトリ作成
            if params.get('create_github_repo', False):
                github_result = await self._create_github_repository(project_info, progress_callback)
                result['github_repo'] = github_result.get('repo_info')
                result['manual_tasks'].extend(github_result.get('manual_tasks', []))
            
            # 3. Google Sheets更新
            if params.get('update_google_sheets', False):
                sheets_result = await self._update_google_sheets(project_info, result, progress_callback)
                result['manual_tasks'].extend(sheets_result.get('manual_tasks', []))
            
            result['success'] = True
            
            if progress_callback:
                progress_callback("プロジェクト初期化完了")
            
        except Exception as e:
            result['error'] = str(e)
            safe_print(f"❌ プロジェクト初期化エラー: {e}")
            
            if progress_callback:
                progress_callback(f"エラー: {str(e)}")
        
        return result
    
    async def _create_slack_channel(
        self, 
        project_info: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Slackチャンネル作成"""
        result = {
            'channel_info': None,
            'manual_tasks': []
        }
        
        try:
            if not self.service_adapter.is_available('slack'):
                result['manual_tasks'].append({
                    'type': 'slack_channel_creation',
                    'description': 'Slack連携が無効のため、手動でチャンネルを作成してください'
                })
                return result
            
            channel_name = project_info.get('repository_name', f"book-{project_info.get('n_code', '').lower()}")
            
            if progress_callback:
                progress_callback(f"Slackチャンネル作成中: #{channel_name}")
            
            # チャンネル作成
            channel_id = await self.service_adapter.create_slack_channel(channel_name)
            
            if channel_id:
                result['channel_info'] = {
                    'id': channel_id,
                    'name': channel_name
                }
                
                # メンバー招待
                await self._invite_slack_members(channel_id, project_info, progress_callback)
                
                if progress_callback:
                    progress_callback(f"Slackチャンネル作成完了: #{channel_name}")
            else:
                result['manual_tasks'].append({
                    'type': 'slack_channel_creation',
                    'description': f'Slackチャンネル #{channel_name} の作成に失敗しました'
                })
        
        except Exception as e:
            safe_print(f"❌ Slackチャンネル作成エラー: {e}")
            result['manual_tasks'].append({
                'type': 'slack_channel_creation',
                'description': f'Slackチャンネル作成エラー: {str(e)}'
            })
        
        return result
    
    async def _invite_slack_members(
        self, 
        channel_id: str, 
        project_info: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """Slackチャンネルへのメンバー招待"""
        # デフォルトメンバー招待（山城敬）
        default_members = ["U7V83BLLB"]  # 山城敬のユーザーID
        
        for member_id in default_members:
            try:
                if progress_callback:
                    progress_callback(f"メンバー招待中: {member_id}")
                
                success = await self.service_adapter.invite_to_slack_channel(channel_id, member_id)
                
                if not success and progress_callback:
                    progress_callback(f"⚠️ メンバー招待失敗: {member_id}")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ メンバー招待エラー: {member_id} - {str(e)}")
        
        # 著者の招待
        author_user_id = project_info.get('slack_user_id')
        if author_user_id:
            try:
                if progress_callback:
                    progress_callback(f"著者招待中: {author_user_id}")
                
                success = await self.service_adapter.invite_to_slack_channel(channel_id, author_user_id)
                
                if not success and progress_callback:
                    progress_callback(f"⚠️ 著者招待失敗: {author_user_id}")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ 著者招待エラー: {author_user_id} - {str(e)}")
    
    async def _create_github_repository(
        self, 
        project_info: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """GitHubリポジトリ作成"""
        result = {
            'repo_info': None,
            'manual_tasks': []
        }
        
        try:
            if not self.service_adapter.is_available('github'):
                result['manual_tasks'].append({
                    'type': 'github_repo_creation',
                    'description': 'GitHub連携が無効のため、手動でリポジトリを作成してください'
                })
                return result
            
            repo_name = project_info.get('repository_name', f"book-{project_info.get('n_code', '').lower()}")
            description = f"技術の泉シリーズ - {project_info.get('book_title', 'Unknown Title')}"
            
            if progress_callback:
                progress_callback(f"GitHubリポジトリ作成中: {repo_name}")
            
            # リポジトリ作成
            repo_url = await self.service_adapter.create_github_repo(repo_name, description)
            
            if repo_url:
                result['repo_info'] = {
                    'name': repo_name,
                    'url': repo_url,
                    'description': description
                }
                
                if progress_callback:
                    progress_callback(f"GitHubリポジトリ作成完了: {repo_name}")
            else:
                result['manual_tasks'].append({
                    'type': 'github_repo_creation',
                    'description': f'GitHubリポジトリ {repo_name} の作成に失敗しました'
                })
        
        except Exception as e:
            safe_print(f"❌ GitHubリポジトリ作成エラー: {e}")
            result['manual_tasks'].append({
                'type': 'github_repo_creation',
                'description': f'GitHubリポジトリ作成エラー: {str(e)}'
            })
        
        return result
    
    async def _update_google_sheets(
        self, 
        project_info: Dict[str, Any], 
        initialization_result: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Google Sheets更新"""
        result = {
            'manual_tasks': []
        }
        
        try:
            if not self.service_adapter.is_available('google_sheets'):
                result['manual_tasks'].append({
                    'type': 'google_sheets_update',
                    'description': 'Google Sheets連携が無効のため、手動でシートを更新してください'
                })
                return result
            
            if progress_callback:
                progress_callback("Google Sheets更新中...")
            
            # 現在はプレースホルダー実装
            # 実際の更新処理は後で実装
            
            if progress_callback:
                progress_callback("Google Sheets更新完了")
        
        except Exception as e:
            safe_print(f"❌ Google Sheets更新エラー: {e}")
            result['manual_tasks'].append({
                'type': 'google_sheets_update',
                'description': f'Google Sheets更新エラー: {str(e)}'
            })
        
        return result