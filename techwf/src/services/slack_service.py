#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack Service - Slack連携サービス
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SlackError(Exception):
    """Slackエラー"""
    pass

class SlackMessageTemplate(Enum):
    """Slackメッセージテンプレート"""
    WORKFLOW_STATUS_UPDATE = "workflow_status_update"
    MILESTONE_NOTIFICATION = "milestone_notification"
    ERROR_ALERT = "error_alert"
    DAILY_SUMMARY = "daily_summary"

class SlackService:
    """Slack連携サービス"""
    
    def __init__(self, config_service=None):
        """
        初期化
        
        Args:
            config_service: 設定サービス
        """
        self.config_service = config_service
        self._authenticated = False
        self._bot_token = None
        self._signing_secret = None
        logger.info("SlackService initialized (stub implementation)")
    
    def authenticate(self, bot_token: str = None, signing_secret: str = None) -> bool:
        """
        認証処理
        
        Args:
            bot_token: Slack Bot Token
            signing_secret: Slack Signing Secret
        
        Returns:
            bool: 認証成功フラグ
        """
        try:
            logger.info("Authenticating with Slack API...")
            
            if bot_token:
                self._bot_token = bot_token
                logger.info("Bot token provided")
            
            if signing_secret:
                self._signing_secret = signing_secret
                logger.info("Signing secret provided")
            
            # スタブ実装 - 実際のSlack API認証は後で実装
            # from slack_sdk import WebClient
            # self.client = WebClient(token=self._bot_token)
            
            self._authenticated = True
            logger.info("Slack authentication completed (simulated)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Slack: {e}")
            raise SlackError(f"Authentication failed: {e}")
    
    def is_authenticated(self) -> bool:
        """認証状態を確認"""
        return self._authenticated
    
    def send_message(self, channel: str, text: str, blocks: List[Dict] = None) -> bool:
        """
        メッセージを送信
        
        Args:
            channel: チャンネルID or チャンネル名
            text: メッセージテキスト
            blocks: Slack Blocks UI（オプション）
        
        Returns:
            bool: 送信成功フラグ
        """
        if not self.is_authenticated():
            raise SlackError("Not authenticated")
        
        try:
            logger.info(f"Sending message to {channel}: {text[:50]}...")
            
            # スタブ実装 - メッセージ送信をシミュレート
            if blocks:
                logger.info(f"Message includes {len(blocks)} blocks")
            
            # 実際の実装では:
            # response = self.client.chat_postMessage(
            #     channel=channel,
            #     text=text,
            #     blocks=blocks
            # )
            
            logger.info("Message sent successfully (simulated)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise SlackError(f"Failed to send message: {e}")
    
    def send_workflow_status_update(self, channel: str, n_number: str, title: str, 
                                  old_status: str, new_status: str, author: str = None) -> bool:
        """
        ワークフロー状況更新メッセージを送信
        
        Args:
            channel: チャンネル
            n_number: N番号
            title: タイトル
            old_status: 旧ステータス
            new_status: 新ステータス
            author: 著者名
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # ステータス表示用の絵文字
            status_emoji = {
                'discovered': '🔍',
                'purchased': '💰',
                'manuscript_requested': '📝',
                'manuscript_received': '📄',
                'first_proof': '📋',
                'second_proof': '✏️',
                'completed': '✅'
            }
            
            old_emoji = status_emoji.get(old_status, '❓')
            new_emoji = status_emoji.get(new_status, '❓')
            
            # メッセージ本文
            text = f"📚 *{title}* のステータスが更新されました\n"
            text += f"📊 {old_emoji} `{old_status}` → {new_emoji} `{new_status}`\n"
            text += f"🔢 N番号: `{n_number}`"
            
            if author:
                text += f"\n👤 著者: {author}"
            
            # Blocks UI構築
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{new_emoji} ワークフロー進捗更新"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*タイトル:*\n{title}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*N番号:*\n`{n_number}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*旧ステータス:*\n{old_emoji} {old_status}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*新ステータス:*\n{new_emoji} {new_status}"
                        }
                    ]
                }
            ]
            
            if author:
                blocks[1]["fields"].append({
                    "type": "mrkdwn",
                    "text": f"*著者:*\n{author}"
                })
            
            return self.send_message(channel, text, blocks)
            
        except Exception as e:
            logger.error(f"Failed to send workflow status update: {e}")
            return False
    
    def send_milestone_notification(self, channel: str, milestone: str, 
                                  count: int, details: List[Dict] = None) -> bool:
        """
        マイルストーン通知を送信
        
        Args:
            channel: チャンネル
            milestone: マイルストーン名
            count: 該当件数
            details: 詳細リスト
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            text = f"🎯 *{milestone}* マイルストーンに到達しました！\n"
            text += f"📊 対象: {count}件"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎯 {milestone} マイルストーン"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{count}件* の項目が {milestone} に到達しました！"
                    }
                }
            ]
            
            # 詳細があれば追加
            if details:
                detail_text = ""
                for item in details[:5]:  # 最大5件まで表示
                    detail_text += f"• {item.get('title', 'N/A')} (`{item.get('n_number', 'N/A')}`)\n"
                
                if len(details) > 5:
                    detail_text += f"...他{len(details) - 5}件"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": detail_text
                    }
                })
            
            return self.send_message(channel, text, blocks)
            
        except Exception as e:
            logger.error(f"Failed to send milestone notification: {e}")
            return False
    
    def send_error_alert(self, channel: str, error_type: str, error_message: str, 
                        context: Dict[str, Any] = None) -> bool:
        """
        エラーアラートを送信
        
        Args:
            channel: チャンネル
            error_type: エラータイプ
            error_message: エラーメッセージ
            context: コンテキスト情報
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            text = f"🚨 *{error_type}* エラーが発生しました\n"
            text += f"💬 {error_message}"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {error_type} エラー"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{error_message}```"
                    }
                }
            ]
            
            # コンテキスト情報があれば追加
            if context:
                context_text = ""
                for key, value in context.items():
                    context_text += f"*{key}:* {value}\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": context_text
                    }
                })
            
            return self.send_message(channel, text, blocks)
            
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")
            return False
    
    def send_daily_summary(self, channel: str, summary_data: Dict[str, Any]) -> bool:
        """
        日次サマリーを送信
        
        Args:
            channel: チャンネル
            summary_data: サマリーデータ
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            text = f"📊 *{today} 日次サマリー*\n"
            text += f"合計: {summary_data.get('total', 0)}件"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {today} 日次サマリー"
                    }
                }
            ]
            
            # ステータス別の集計
            if 'status_counts' in summary_data:
                status_text = ""
                for status, count in summary_data['status_counts'].items():
                    status_text += f"• {status}: {count}件\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": status_text
                    }
                })
            
            return self.send_message(channel, text, blocks)
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    def get_channel_list(self) -> List[Dict[str, Any]]:
        """
        チャンネル一覧を取得
        
        Returns:
            List[Dict[str, Any]]: チャンネル情報リスト
        """
        if not self.is_authenticated():
            raise SlackError("Not authenticated")
        
        try:
            logger.info("Getting channel list...")
            
            # スタブ実装 - サンプルチャンネルリストを返す
            channels = [
                {
                    "id": "C1234567890",
                    "name": "general",
                    "is_channel": True,
                    "is_private": False
                },
                {
                    "id": "C2345678901",
                    "name": "techwf-notifications",
                    "is_channel": True,
                    "is_private": False
                },
                {
                    "id": "C3456789012",
                    "name": "workflow-alerts",
                    "is_channel": True,
                    "is_private": False
                }
            ]
            
            logger.info(f"Retrieved {len(channels)} channels (simulated)")
            return channels
            
        except Exception as e:
            logger.error(f"Failed to get channel list: {e}")
            raise SlackError(f"Failed to get channel list: {e}")

# ファクトリー関数
def create_slack_service(config_service=None) -> SlackService:
    """
    Slackサービスを作成
    
    Args:
        config_service: 設定サービス
        
    Returns:
        SlackService: サービスインスタンス
    """
    return SlackService(config_service)