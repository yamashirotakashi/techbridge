"""GitHub Service - GitHubリポジトリ操作サービス"""
import logging
from typing import Optional, Dict, Any
from github import Github
from github.GithubException import GithubException

logger = logging.getLogger(__name__)

class GitHubService:
    """GitHub API操作を担当するサービスクラス"""
    
    def __init__(self, github_token: Optional[str] = None):
        """GitHubサービスの初期化
        
        Args:
            github_token: GitHub APIトークン
        """
        self.github_token = github_token
        self.github_client = None
        if github_token:
            try:
                self.github_client = Github(github_token)
            except Exception as e:
                logger.error(f"GitHub client initialization failed: {e}")
    
    def is_available(self) -> bool:
        """GitHubサービスの利用可能状態を確認"""
        return self.github_client is not None
    
    def create_github_repo(self, project_name: str, description: str = "", 
                          private: bool = False) -> Optional[Dict[str, Any]]:
        """GitHubリポジトリを作成
        
        Args:
            project_name: プロジェクト名
            description: リポジトリの説明
            private: プライベートリポジトリフラグ
            
        Returns:
            作成されたリポジトリ情報、または失敗時はNone
        """
        if not self.github_client:
            logger.warning("GitHub client not initialized")
            return None
            
        try:
            user = self.github_client.get_user()
            repo = user.create_repo(
                name=project_name,
                description=description,
                private=private,
                auto_init=True
            )
            
            result = {
                'success': True,
                'html_url': repo.html_url,
                'ssh_url': repo.ssh_url,
                'clone_url': repo.clone_url,
                'default_branch': repo.default_branch
            }
            logger.info(f"GitHub repository created: {repo.html_url}")
            return result
            
        except GithubException as e:
            logger.error(f"GitHub repo creation failed: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in GitHub repo creation: {e}")
            return {'success': False, 'error': str(e)}