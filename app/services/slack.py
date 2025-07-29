"""Slackサービス"""

from typing import Optional, Dict, Any
import asyncio
import time

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import structlog

from app.models.enums import ProgressStatus as WorkflowStatus
from app.services.google_sheets import GoogleSheetsService

logger = structlog.get_logger(__name__)


class SlackService:
    """Slack API操作サービス"""
    
    def __init__(self, token: str):
        self.client = WebClient(token=token)
        self.sheets_service = None
        try:
            self.sheets_service = GoogleSheetsService()
        except Exception as e:
            logger.warning("Google Sheets service initialization failed", error=str(e))
    
    def resolve_channel_name(self, n_number: str, default_channel: str = "#general") -> str:
        """N番号からSlackチャンネル名を解決"""
        if not self.sheets_service:
            logger.warning("Google Sheets service not available, using default channel")
            return default_channel
        
        try:
            workflow_info = self.sheets_service.get_workflow_info(n_number)
            if workflow_info and workflow_info.get('slack_channel'):
                channel_name = workflow_info['slack_channel']
                # チャンネル名が#で始まっていない場合は追加
                if not channel_name.startswith('#'):
                    channel_name = f"#{channel_name}"
                logger.info("Resolved channel name", n_number=n_number, channel=channel_name)
                return channel_name
        except Exception as e:
            logger.error("Failed to resolve channel name", n_number=n_number, error=str(e))
        
        logger.warning("Using default channel", n_number=n_number, default=default_channel)
        return default_channel
    
    def get_channel_id(self, channel_name: str) -> Optional[str]:
        """チャンネル名からチャンネルIDを取得"""
        try:
            # #記号を除去
            clean_channel_name = channel_name.lstrip('#')
            
            # プライベートチャンネル一覧を取得（ページネーション対応）
            all_channels = []
            cursor = None
            
            while True:
                params = {
                    "types": "private_channel",
                    "limit": 1000
                }
                if cursor:
                    params["cursor"] = cursor
                
                result = self.client.conversations_list(**params)
                channels = result.get("channels", [])
                all_channels.extend(channels)
                
                cursor = result.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            
            channels = all_channels
            
            # チャンネル名でマッチング（Botが参加しているもののみ）
            for channel in channels:
                if channel["name"] == clean_channel_name and channel.get("is_member", False):
                    logger.info("Found channel ID", name=clean_channel_name, id=channel["id"])
                    return channel["id"]
            
            logger.warning("Channel not found", name=clean_channel_name)
            return None
            
        except SlackApiError as e:
            logger.error("Failed to get channel ID", channel_name=channel_name, error=str(e))
            return None
    
    def resolve_channel_id(self, n_number: str, default_channel: str = "#general") -> Optional[str]:
        """N番号からSlackチャンネルIDを解決"""
        channel_name = self.resolve_channel_name(n_number, default_channel)
        return self.get_channel_id(channel_name)
    
    async def send_status_update(
        self,
        channel: str,
        n_number: str,
        title: str,
        old_status: Optional[WorkflowStatus],
        new_status: WorkflowStatus,
        auto_resolve_channel: bool = True
    ) -> bool:
        """ステータス更新通知を送信"""
        # チャンネルIDの自動解決
        if auto_resolve_channel and n_number:
            resolved_channel_id = self.resolve_channel_id(n_number, channel)
            if resolved_channel_id:
                logger.info("Channel ID resolved", original=channel, resolved_id=resolved_channel_id)
                channel = resolved_channel_id
            else:
                # フォールバック: チャンネル名を使用
                resolved_channel = self.resolve_channel_name(n_number, channel)
                if resolved_channel != channel:
                    logger.info("Channel name resolved", original=channel, resolved=resolved_channel)
                    channel = resolved_channel
        
        # ステータスを日本語に変換
        status_ja = {
            WorkflowStatus.DISCOVERED: "🔍 発見",
            WorkflowStatus.PURCHASED: "💰 購入完了",
            WorkflowStatus.MANUSCRIPT_REQUESTED: "✍️ 原稿依頼",
            WorkflowStatus.MANUSCRIPT_RECEIVED: "📄 原稿受領",
            WorkflowStatus.FIRST_PROOF: "📝 初校",
            WorkflowStatus.SECOND_PROOF: "✏️ 再校",
            WorkflowStatus.COMPLETED: "✅ 完成"
        }
        
        old_status_text = status_ja.get(old_status, old_status.value) if old_status else "なし"
        new_status_text = status_ja.get(new_status, new_status.value)
        
        # メッセージを構築
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 進捗更新: {n_number}"
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
                        "text": f"*N番号:*\n{n_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*変更前:*\n{old_status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*変更後:*\n{new_status_text}"
                    }
                ]
            }
        ]
        
        # 特定のステータスに応じた追加メッセージ
        if new_status == WorkflowStatus.MANUSCRIPT_REQUESTED:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📮 *著者への原稿依頼をお忘れなく！*"
                }
            })
        elif new_status == WorkflowStatus.COMPLETED:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎉 *お疲れさまでした！編集作業が完了しました。*"
                }
            })
        
        try:
            # 非同期実行のため、同期メソッドを別スレッドで実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._send_message,
                channel,
                f"進捗更新: {n_number} - {new_status_text}",
                blocks
            )
            
            logger.info(
                "Sent status update notification",
                channel=channel,
                n_number=n_number,
                status=new_status.value
            )
            
            return True
            
        except SlackApiError as e:
            logger.error(
                "Failed to send Slack notification",
                error=str(e),
                response=e.response
            )
            return False
    
    async def send_completion_notification(
        self,
        channel: str,
        n_number: str,
        repository_name: str,
        workflow_metadata: Dict[str, Any],
        auto_resolve_channel: bool = True
    ) -> bool:
        """完了通知を送信"""
        # チャンネルIDの自動解決
        if auto_resolve_channel and n_number:
            resolved_channel_id = self.resolve_channel_id(n_number, channel)
            if resolved_channel_id:
                logger.info("Channel ID resolved for completion", original=channel, resolved_id=resolved_channel_id)
                channel = resolved_channel_id
            else:
                # フォールバック: チャンネル名を使用
                resolved_channel = self.resolve_channel_name(n_number, channel)
                if resolved_channel != channel:
                    logger.info("Channel name resolved for completion", original=channel, resolved=resolved_channel)
                    channel = resolved_channel
        
        # メッセージを構築
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎉 制作完了: {n_number}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*N番号:*\n{n_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*リポジトリ:*\n{repository_name}"
                    }
                ]
            }
        ]
        
        # メタデータから追加情報を抽出
        if workflow_metadata:
            additional_fields = []
            
            if "pages" in workflow_metadata:
                additional_fields.append({
                    "type": "mrkdwn",
                    "text": f"*ページ数:*\n{workflow_metadata['pages']}ページ"
                })
            
            if "format" in workflow_metadata:
                additional_fields.append({
                    "type": "mrkdwn",
                    "text": f"*フォーマット:*\n{workflow_metadata['format']}"
                })
            
            if "completed_by" in workflow_metadata:
                additional_fields.append({
                    "type": "mrkdwn",
                    "text": f"*完了者:*\n{workflow_metadata['completed_by']}"
                })
            
            if additional_fields:
                blocks.append({
                    "type": "section",
                    "fields": additional_fields[:2]  # 最大2フィールド
                })
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✨ *技術の泉シリーズの制作が完了しました！*\n最終確認をお願いします。"
            }
        })
        
        try:
            # 非同期実行のため、同期メソッドを別スレッドで実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._send_message,
                channel,
                f"制作完了: {n_number} - {repository_name}",
                blocks
            )
            
            logger.info(
                "Sent completion notification",
                channel=channel,
                n_number=n_number,
                repository_name=repository_name
            )
            
            return True
            
        except SlackApiError as e:
            logger.error(
                "Failed to send Slack notification",
                error=str(e),
                response=e.response
            )
            return False
    
    def _send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None
    ) -> dict:
        """同期的にメッセージを送信（内部使用）"""
        return self.client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks
        )
    
    def post_test_message(self, channel: str, message: str = "🧪 TechBridge API Test Message") -> Optional[Dict[str, Any]]:
        """テストメッセージを投稿"""
        try:
            # チャンネルIDを取得
            channel_id = self.get_channel_id(channel)
            
            if not channel_id:
                logger.error("Channel not found for test message", channel=channel)
                return None
                
            # メッセージを投稿
            result = self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{message}*"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"投稿時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            )
            
            logger.info("Test message posted successfully", channel=channel, ts=result.get("ts"))
            return {
                "success": True,
                "channel": channel,
                "channel_id": channel_id,
                "message_ts": result.get("ts"),
                "permalink": result.get("message", {}).get("permalink")
            }
            
        except SlackApiError as e:
            logger.error("Failed to post test message", channel=channel, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "channel": channel
            }
    
    def delete_message(self, channel: str, message_ts: str) -> bool:
        """メッセージを削除"""
        try:
            # チャンネルIDを取得
            channel_id = self.get_channel_id(channel)
            
            if not channel_id:
                logger.error("Channel not found for message deletion", channel=channel)
                return False
            
            # メッセージを削除
            self.client.chat_delete(
                channel=channel_id,
                ts=message_ts
            )
            
            logger.info("Message deleted successfully", channel=channel, ts=message_ts)
            return True
            
        except SlackApiError as e:
            logger.error("Failed to delete message", channel=channel, ts=message_ts, error=str(e))
            return False
    
    def test_post_and_delete(self, channel: str, test_message: str = "🧪 TechBridge 投稿・削除テスト", 
                           auto_delete_delay: int = 5) -> Dict[str, Any]:
        """投稿と削除のテストを実行"""
        import time
        
        logger.info("Starting post and delete test", channel=channel, delay=auto_delete_delay)
        
        # 1. メッセージを投稿
        post_result = self.post_test_message(channel, test_message)
        
        if not post_result or not post_result.get("success"):
            return {
                "success": False,
                "error": "Failed to post test message",
                "channel": channel,
                "post_result": post_result
            }
        
        message_ts = post_result.get("message_ts")
        if not message_ts:
            return {
                "success": False,
                "error": "No message timestamp received",
                "channel": channel,
                "post_result": post_result
            }
        
        # 2. 指定秒数待機
        logger.info("Waiting before deletion", delay=auto_delete_delay)
        time.sleep(auto_delete_delay)
        
        # 3. メッセージを削除
        delete_success = self.delete_message(channel, message_ts)
        
        return {
            "success": delete_success,
            "channel": channel,
            "message_ts": message_ts,
            "post_result": post_result,
            "delete_success": delete_success,
            "delay_seconds": auto_delete_delay
        }