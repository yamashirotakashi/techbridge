# core/worker_thread.py作成内容

```python
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
from typing import Dict, Any
import os

# クライアント依存関係
from clients.google_sheets_client import GoogleSheetsClient
from clients.slack_client import SlackClient
from clients.github_client import GitHubClient

# 設定・ユーティリティ
from config.config_manager import get_config_path
from utils.availability_checker import (
    google_sheets_available,
    slack_client_available,
    github_client_available
)


class WorkerThread(QThread):
    """非同期処理用のワーカースレッド"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, params: Dict[str, Any]):
        super().__init__()
        self.task_type = task_type
        self.params = params
    
    def run(self):
        """タスクを実行"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.task_type == "initialize_project":
                result = loop.run_until_complete(self._initialize_project())
            elif self.task_type == "check_project":
                result = loop.run_until_complete(self._check_project_info())
            else:
                raise ValueError(f"Unknown task type: {self.task_type}")
                
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
    
    async def _check_project_info(self):
        """プロジェクト情報を確認"""
        self.progress.emit("Google Sheetsから情報を取得中...")
        
        if not google_sheets_available:
            raise ValueError("Google Sheets連携が利用できません")
        
        # Google Sheets クライアント初期化
        service_account_path = get_config_path("service_account.json")
        sheets_client = GoogleSheetsClient(str(service_account_path))
        
        # プロジェクト情報取得
        project_info = await sheets_client.get_project_info(
            self.params["planning_sheet_id"],
            self.params["n_code"]
        )
        
        if not project_info:
            raise ValueError(f"Nコード {self.params['n_code']} が見つかりません")
        
        # 購入リストから書籍URL取得
        self.progress.emit("購入リストから書籍URLを検索中...")
        book_url = await sheets_client.get_book_url_from_purchase_list(
            self.params["purchase_sheet_id"],
            self.params["n_code"]
        )
        
        project_info["book_url_from_purchase"] = book_url
        
        return project_info
    
    async def _initialize_project(self):
        """プロジェクト初期化を実行"""
        result = {
            "slack_channel": None,
            "github_repo": None,
            "manual_tasks": []
        }
        
        # 1. プロジェクト情報取得
        project_info = await self._check_project_info()
        result["project_info"] = project_info
        
        # 2. Slackチャンネル作成
        if self.params.get("create_slack_channel") and slack_client_available:
            self.progress.emit("Slackチャンネルを作成中...")
            
            slack_client = SlackClient(
                self.params["slack_token"],
                self.params.get("slack_user_token", os.getenv("SLACK_USER_TOKEN"))
            )
            # チャンネル名はリポジトリ名と同じにする
            channel_name = project_info["repository_name"]
            book_title = project_info.get("book_title")
            
            # チャンネル作成（書籍名をトピックに設定）
            channel_id = await slack_client.create_channel(channel_name, book_title)
            if channel_id:
                result["slack_channel"] = {
                    "id": channel_id,
                    "name": channel_name
                }
                
                # チャンネル作成後の安定化待機（時間を延長）
                await asyncio.sleep(3.0)
                
                # デフォルトメンバー招待（User Token使用）
                self.progress.emit("山城敬を招待中...")
                invite_success = await slack_client.invite_user_to_channel(
                    channel_id,
                    "U7V83BLLB",  # 山城敬
                    use_user_token=True  # プライベートチャンネルのためUser Token使用
                )
                if not invite_success:
                    self.progress.emit("[WARN] 山城敬の招待に失敗しました")
                
                # Bot招待（PJINIT v1.2方式: 招待Bot A097NKP77EE を使用）
                self.progress.emit("TechZip PDF Botを招待中（招待Bot使用）...")
                bot_invite_success = await slack_client.invite_techzip_bot_with_invitation_bot(channel_id)
                if not bot_invite_success:
                    self.progress.emit("[WARN] TechZip PDF Botの招待に失敗しました（招待Bot経由）")
                
                # GitHub App招待は手動作業として扱う
                self.progress.emit("GitHub App招待は手動タスクに追加...")
                result["manual_tasks"].append({
                    "type": "github_app_invitation",
                    "repository_name": project_info["repository_name"],
                    "channel_name": channel_name,
                    "description": f"GitHub Appを#{channel_name}に設定してください"
                })
                self.progress.emit("✅ GitHub App招待タスクを手動タスクリストに追加")
                
                # 著者の招待処理（エラーハンドリング付き）
                if project_info.get("author_slack_id"):
                    # 既存ユーザー
                    self.progress.emit("著者を招待中...")
                    author_invite_success = await slack_client.invite_user_to_channel(
                        channel_id,
                        project_info["author_slack_id"],
                        use_user_token=True  # プライベートチャンネルのためUser Token使用
                    )
                    if not author_invite_success:
                        self.progress.emit("[WARN] 著者の招待に失敗しました")
                        # 手動タスクとして記録
                        result["manual_tasks"].append({
                            "type": "slack_invitation",
                            "user_id": project_info["author_slack_id"],
                            "email": project_info.get("author_email", "不明"),
                            "description": f"著者 {project_info.get('author_email', project_info['author_slack_id'])} をSlackチャンネルに招待してください"
                        })
                elif project_info.get("author_email"):
                    # メールで検索
                    self.progress.emit("著者をメールで検索中...")
                    user_id = await slack_client.find_user_by_email(
                        project_info["author_email"]
                    )
                    if user_id:
                        self.progress.emit("著者を招待中...")
                        author_invite_success = await slack_client.invite_user_to_channel(
                            channel_id, 
                            user_id,
                            use_user_token=True  # プライベートチャンネルのためUser Token使用
                        )
                        if not author_invite_success:
                            self.progress.emit("[WARN] 著者の招待に失敗しました")
                            # 手動タスクとして記録
                            result["manual_tasks"].append({
                                "type": "slack_invitation",
                                "user_id": user_id,
                                "email": project_info["author_email"],
                                "description": f"著者 {project_info['author_email']} をSlackチャンネルに招待してください"
                            })
                    else:
                        # 手動タスク作成
                        self.progress.emit("著者が見つからないため手動タスクを作成...")
                        result["manual_tasks"].append({
                            "type": "slack_invitation",
                            "email": project_info["author_email"],
                            "description": f"著者 {project_info['author_email']} をSlackワークスペースに招待してください"
                        })
        
        # 3. GitHubリポジトリ作成
        if self.params.get("create_github_repo") and github_client_available:
            self.progress.emit("GitHubリポジトリを作成中...")
            self.progress.emit("yamashirotakashi（編集者）とコラボレーター設定も実行...")
            
            github_client = GitHubClient()
            
            # 書籍名をdescriptionに設定（書籍名がある場合は書籍名のみ）
            book_title = project_info.get("book_title")
            if book_title and book_title != "技術の泉シリーズ":
                description = book_title  # 書籍名のみ
            else:
                description = f"{self.params['n_code']} - 技術の泉シリーズ"
            
            repo_info = await github_client.setup_repository(
                n_code=self.params["n_code"],
                repo_name=project_info["repository_name"],
                github_username=project_info.get("author_github_id"),
                description=description,
                book_title=book_title
            )
            
            if repo_info:
                result["github_repo"] = repo_info
                
                # GitHubリポジトリ招待失敗の場合は手動タスクに追加
                if repo_info.get("invitation_failed"):
                    result["manual_tasks"].append({
                        "type": "github_invitation",
                        "github_username": repo_info.get("failed_github_username", "不明"),
                        "repository_url": repo_info.get("html_url", "不明"),
                        "description": f"GitHub {repo_info.get('failed_github_username', '不明')} をリポジトリに招待してください"
                    })
        
        # 4. Google Sheets更新
        if self.params.get("update_sheets") and google_sheets_available:
            self.progress.emit("Google Sheetsを更新中...")
            
            # 書籍URLの転記
            if project_info.get("book_url_from_purchase"):
                service_account_path = get_config_path("service_account.json")
                sheets_client = GoogleSheetsClient(str(service_account_path))
                await sheets_client.update_book_url(
                    self.params["planning_sheet_id"],
                    self.params["n_code"],
                    project_info["book_url_from_purchase"]
                )
        
        # 5. ワークフロー管理統合（全実行結果を投稿）
        if slack_client_available:
            self.progress.emit("ワークフロー管理システムを統合中...")
            
            slack_client = SlackClient(
                self.params["slack_token"],
                self.params.get("slack_user_token", os.getenv("SLACK_USER_TOKEN"))
            )
            
            # ワークフロー管理チャンネルを検索（常に管理チャンネルIDが返される）
            workflow_channel_id = await slack_client.find_workflow_channel()
            
            # ワークフローガイダンスを投稿（全ての実行結果）
            await slack_client.post_workflow_guidance(
                workflow_channel_id,
                project_info,
                result.get("manual_tasks", []),
                execution_summary=result,  # 全実行結果を含める
                sheet_id=self.params["planning_sheet_id"]  # 発行計画シートID
            )
            
            # 手動タスク管理シートに記録を追加
            if self.params.get("update_sheets") and google_sheets_available:
                service_account_path = get_config_path("service_account.json")
                sheets_client = GoogleSheetsClient(str(service_account_path))
                
                status = "手動タスクあり" if result.get("manual_tasks") else "初期化完了"
                additional_info = {
                    "slack_channel": result.get("slack_channel", {}).get("name", "未作成"),
                    "github_repo": result.get("github_repo", {}).get("html_url", "未作成"),
                    "manual_tasks_count": len(result.get("manual_tasks", []))
                }
                
                # 手動タスク管理シートに記録を追加
                try:
                    await sheets_client.add_manual_task_record(
                        self.params["planning_sheet_id"],
                        self.params["n_code"],
                        status,
                        additional_info
                    )
                    self.progress.emit("手動タスク管理シートに記録を追加しました")
                    result["workflow_posted"] = True
                except Exception as e:
                    self.progress.emit(f"[WARN] 手動タスク管理シート更新に失敗: {str(e)}")
                    result["workflow_posted"] = False
            else:
                # Google Sheets更新が無効でも管理チャンネルには投稿済み
                result["workflow_posted"] = True
        
        self.progress.emit("完了！")
        return result
```

このファイルをcore/worker_thread.pyとして作成する必要があります。