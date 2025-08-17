"""Slack Service - Slack API操作サービス"""
import logging
import time
from typing import Optional, Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

class SlackService:
    """Slack API操作を担当するサービスクラス"""
    
    def __init__(self, slack_token: Optional[str] = None, 
                 slack_bot_token: Optional[str] = None,
                 alternative_bot_token: Optional[str] = None):
        """Slackサービスの初期化
        
        Args:
            slack_token: Slack APIトークン（ユーザートークン）
            slack_bot_token: Slack Botトークン
            alternative_bot_token: 代替Botトークン
        """
        self.slack_token = slack_token
        self.slack_bot_token = slack_bot_token
        self.alternative_bot_token = alternative_bot_token
        
        self.slack_client = None
        self.slack_bot_client = None
        self.alternative_bot_client = None
        
        if slack_token:
            try:
                self.slack_client = WebClient(token=slack_token)
            except Exception as e:
                logger.error(f"Slack client initialization failed: {e}")
                
        if slack_bot_token:
            try:
                self.slack_bot_client = WebClient(token=slack_bot_token)
            except Exception as e:
                logger.error(f"Slack bot client initialization failed: {e}")
                
        if alternative_bot_token:
            try:
                self.alternative_bot_client = WebClient(token=alternative_bot_token)
            except Exception as e:
                logger.error(f"Alternative bot client initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Slackサービスの利用可能状態を確認"""
        return self.slack_client is not None
    
    def create_slack_channel(self, channel_name: str, is_private: bool = False) -> Optional[Dict[str, Any]]:
        """Slackチャンネルを作成
        
        Args:
            channel_name: チャンネル名
            is_private: プライベートチャンネルフラグ
            
        Returns:
            作成されたチャンネル情報、または失敗時はNone
        """
        if not self.slack_client:
            logger.warning("Slack client not initialized")
            return None
            
        try:
            result = self.slack_client.conversations_create(
                name=channel_name,
                is_private=is_private
            )
            logger.info(f"Slack channel created: {channel_name}")
            return result.data if result else None
        except SlackApiError as e:
            logger.error(f"Slack channel creation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Slack channel creation: {e}")
            return None
    
    def invite_to_slack_channel(self, channel_id: str, user_ids: List[str]) -> bool:
        """Slackチャンネルにユーザーを招待
        
        Args:
            channel_id: チャンネルID
            user_ids: 招待するユーザーIDのリスト
            
        Returns:
            成功時True、失敗時False
        """
        if not self.slack_client:
            logger.warning("Slack client not initialized")
            return False
            
        try:
            result = self.slack_client.conversations_invite(
                channel=channel_id,
                users=",".join(user_ids)
            )
            logger.info(f"Users invited to channel {channel_id}")
            return result.get('ok', False) if result else False
        except SlackApiError as e:
            logger.error(f"Slack invite failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Slack invite: {e}")
            return False
    
    def find_user_by_email(self, email: str) -> Optional[str]:
        """メールアドレスからSlackユーザーIDを検索
        
        Args:
            email: メールアドレス
            
        Returns:
            ユーザーID、見つからない場合はNone
        """
        if not self.slack_client:
            logger.warning("Slack client not initialized")
            return None
            
        try:
            result = self.slack_client.users_lookupByEmail(email=email)
            if result and result.get('ok') and result.get('user'):
                return result['user']['id']
            return None
        except SlackApiError as e:
            logger.error(f"Slack user lookup failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Slack user lookup: {e}")
            return None
    
    def find_workflow_channel(self, project_name: str) -> Optional[str]:
        """ワークフローチャンネルを検索
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            チャンネルID、見つからない場合はNone
        """
        if not self.slack_client:
            logger.warning("Slack client not initialized")
            return None
            
        try:
            # プロジェクト名からチャンネル名を生成
            potential_names = [
                f"wf-{project_name}",
                f"workflow-{project_name}",
                project_name
            ]
            
            # パブリックチャンネルとプライベートチャンネルの両方を検索
            for channel_type in ['public_channel', 'private_channel']:
                result = self.slack_client.conversations_list(
                    types=channel_type,
                    limit=1000
                )
                
                if result and result.get('channels'):
                    for channel in result['channels']:
                        if channel['name'] in potential_names:
                            return channel['id']
                            
            return None
        except SlackApiError as e:
            logger.error(f"Slack channel search failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Slack channel search: {e}")
            return None
    
    def post_workflow_guidance(self, channel_id: str, message: str) -> bool:
        """ワークフローガイダンスメッセージを投稿
        
        Args:
            channel_id: チャンネルID
            message: 投稿するメッセージ
            
        Returns:
            成功時True、失敗時False
        """
        if not self.slack_client:
            logger.warning("Slack client not initialized")
            return False
            
        try:
            result = self.slack_client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            logger.info(f"Workflow guidance posted to channel {channel_id}")
            return result.get('ok', False) if result else False
        except SlackApiError as e:
            logger.error(f"Slack message post failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Slack message post: {e}")
            return False
    
    def invite_github_app_with_bot_token(self, channel_id: str) -> bool:
        """GitHub AppをBotトークンで招待
        
        Args:
            channel_id: チャンネルID
            
        Returns:
            成功時True、失敗時False
        """
        if not self.slack_bot_client:
            logger.warning("Slack bot client not initialized")
            return False
            
        try:
            # GitHub Appを招待（ボットトークンを使用）
            result = self.slack_bot_client.conversations_join(channel=channel_id)
            
            if result and result.get('ok'):
                logger.info(f"GitHub App invited to channel {channel_id} with bot token")
                return True
            return False
        except SlackApiError as e:
            logger.error(f"GitHub App invite with bot token failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in GitHub App invite: {e}")
            return False
    
    def invite_github_app_with_alternative_bot(self, channel_id: str) -> bool:
        """GitHub Appを代替Botトークンで招待
        
        Args:
            channel_id: チャンネルID
            
        Returns:
            成功時True、失敗時False
        """
        if not self.alternative_bot_client:
            logger.warning("Alternative bot client not initialized")
            return False
            
        try:
            # GitHub Appを招待（代替ボットトークンを使用）
            result = self.alternative_bot_client.conversations_join(channel=channel_id)
            
            if result and result.get('ok'):
                logger.info(f"GitHub App invited to channel {channel_id} with alternative bot")
                return True
            return False
        except SlackApiError as e:
            logger.error(f"GitHub App invite with alternative bot failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in GitHub App invite with alternative bot: {e}")
            return False
    
    def invite_user_by_email(self, channel_id: str, email: str) -> bool:
        """メールアドレスでユーザーをチャンネルに招待
        
        Args:
            channel_id: チャンネルID
            email: ユーザーのメールアドレス
            
        Returns:
            成功時True、失敗時False
        """
        user_id = self.find_user_by_email(email)
        if not user_id:
            logger.warning(f"User not found for email: {email}")
            return False
            
        return self.invite_to_slack_channel(channel_id, [user_id])