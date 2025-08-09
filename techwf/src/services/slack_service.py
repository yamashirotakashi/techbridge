#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechWF v0.5 Slack API サービス
技術書典商業化タブのSlack連携パターンを踏襲
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logging.warning("Slack SDKが利用できません。pip install slack-sdkを実行してください。")

from ..models.publication_workflow import (
    PublicationWorkflowDTO, 
    SlackPostHistoryDTO
)
from ..repositories.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

class SlackError(Exception):
    """Slack API 関連エラー"""
    pass

class SlackAuthError(SlackError):
    """Slack 認証エラー"""
    pass

class SlackMessageTemplate:
    """
    Slackメッセージテンプレートクラス
    技術書典商業化タブの投稿パターンを踏襲
    """
    
    # メッセージテンプレート定義
    TEMPLATES = {
        'reminder': {
            'name': '進捗確認リマインダー',
            'description': '著者への進捗確認リマインダーメッセージ',
            'template': """
📚 *{book_title}* の進捗確認

こんにちは、{author_name}さん！

現在のステータス: *{current_status}*
次のタスク: {next_task}
締切日: {due_date}

{status_message}

ご質問やサポートが必要でしたら、お気軽にお声がけください！

#TechWF自動投稿 #{n_number}
            """.strip()
        },
        
        'deadline_warning': {
            'name': '締切警告',
            'description': '締切が近い書籍への警告メッセージ',
            'template': """
⚠️ *締切注意* - {book_title}

{author_name}さん

締切まで *{days_left}日* です！

現在のステータス: *{current_status}*
締切日: *{due_date}*

{urgent_message}

サポートが必要な場合は、すぐにご連絡ください。

#TechWF自動投稿 #締切注意 #{n_number}
            """.strip()
        },
        
        'completion_congratulations': {
            'name': '制作完了祝い',
            'description': '制作完了への祝福メッセージ',
            'template': """
🎉 *制作完了おめでとうございます！* - {book_title}

{author_name}さん、お疲れ様でした！

制作完了日: {completion_date}
最終ステータス: *{current_status}*

素晴らしい作品をありがとうございました！
次のステップ（査読・編集等）に関しては、別途ご連絡いたします。

#TechWF自動投稿 #制作完了 #{n_number}
            """.strip()
        },
        
        'status_update': {
            'name': 'ステータス更新通知',
            'description': 'ステータス変更の通知メッセージ',
            'template': """
📋 *ステータス更新* - {book_title}

{author_name}さん

ステータスが更新されました：
{previous_status} → *{current_status}*

{update_message}

引き続きよろしくお願いいたします！

#TechWF自動投稿 #ステータス更新 #{n_number}
            """.strip()
        }
    }

    @classmethod
    def get_template_names(cls) -> List[str]:
        """利用可能テンプレート名一覧取得"""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template_info(cls, template_name: str) -> Optional[Dict[str, str]]:
        """テンプレート情報取得"""
        return cls.TEMPLATES.get(template_name)

    @classmethod
    def format_message(cls, template_name: str, workflow: PublicationWorkflowDTO, **kwargs) -> str:
        """
        Format message template
        
        Args:
            template_name: Template name
            workflow: Workflow DTO
            **kwargs: Additional parameters
            
        Returns:
            str: Formatted message
        """
        template_info = cls.TEMPLATES.get(template_name)
        if not template_info:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Basic parameters
        params = {
            'n_number': workflow.n_number,
            'book_title': workflow.book_title,
            'author_name': workflow.author_name,
            'current_status': workflow.current_status,
            'next_task': workflow.next_task or 'Not set',
            'due_date': workflow.due_date.strftime('%Y/%m/%d') if workflow.due_date else 'Not set',
            'days_left': workflow.days_until_due() if workflow.days_until_due() is not None else 'Not set',
            'completion_date': datetime.now().strftime('%Y/%m/%d'),
        }
        
        # テンプレートタイプ別の追加メッセージ
        if template_name == 'reminder':
            if workflow.is_overdue():
                params['status_message'] = "🚨 警告：締切を過ぎています。緊急対応が必要です。"
            elif workflow.days_until_due() and workflow.days_until_due() <= 3:
                params['status_message'] = "📅 締切が近づいています。進捗をお聞かせください。"
            else:
                params['status_message'] = "📝 現在の進捗状況をお聞かせください。"
        
        elif template_name == 'deadline_warning':
            days_left = workflow.days_until_due()
            if days_left and days_left <= 1:
                params['urgent_message'] = "🚨 明日が締切です！緊急対応をお願いします。"
            elif days_left and days_left <= 3:
                params['urgent_message'] = "⏰ 締切が迫っています。計画的な進行をお願いします。"
            else:
                params['urgent_message'] = "📊 進捗状況の確認をお願いします。"
        
        elif template_name == 'status_update':
            params['previous_status'] = kwargs.get('previous_status', '不明')
            if workflow.current_status == '制作完了':
                params['update_message'] = "🎉 制作完了です！お疲れ様でした。"
            elif '中' in workflow.current_status:
                params['update_message'] = "📝 引き続き頑張ってください！"
            else:
                params['update_message'] = "📋 新しいステータスでの作業をお願いします。"
        
        # kwargs で追加パラメータをオーバーライド
        params.update(kwargs)
        
        try:
            return template_info['template'].format(**params)
        except KeyError as e:
            raise ValueError(f"テンプレートパラメータエラー: {e}")

class SlackService:
    """
    Slack API サービスクラス
    技術書典商業化タブの投稿パターンを踏襲
    """
    
    def __init__(self, bot_token: str, default_channel: str = "#general"):
        """
        Slack サービスの初期化
        
        Args:
            bot_token: Slack Bot Token (xoxb-で始まる)
            default_channel: デフォルトチャンネル
        """
        if not SLACK_AVAILABLE:
            raise SlackError("Slack SDKがインストールされていません")
        
        if not bot_token or not bot_token.startswith('xoxb-'):
            raise SlackAuthError("無効なBot Tokenです")
        
        self.bot_token = bot_token
        self.default_channel = default_channel
        
        # Slack Web API クライアント初期化
        self.client = WebClient(token=bot_token)
        
        # レート制限対策
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1秒間隔
        
        # 初期化テスト
        self._validate_auth()
        
        logger.info("Slack サービス初期化完了")

    def _validate_auth(self):
        """
        認証情報の検証
        """
        try:
            self._rate_limit_wait()
            response = self.client.auth_test()
            
            if not response['ok']:
                raise SlackAuthError(f"認証失敗: {response.get('error', '不明なエラー')}")
            
            self.bot_info = {
                'user_id': response['user_id'],
                'team_id': response['team_id'],
                'team': response['team'],
                'user': response['user']
            }
            
            logger.info(f"Slack認証成功: {self.bot_info['user']}@{self.bot_info['team']}")
            
        except SlackApiError as e:
            logger.error(f"Slack認証エラー: {e.response['error']}")
            raise SlackAuthError(f"認証に失敗しました: {e.response['error']}")

    def _rate_limit_wait(self):
        """
        レート制限対策の待機処理
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def post_message(self, 
                    workflow: PublicationWorkflowDTO,
                    template_name: str,
                    channel: Optional[str] = None,
                    **template_kwargs) -> SlackPostHistoryDTO:
        """
        メッセージ投稿
        
        Args:
            workflow: ワークフローDTO
            template_name: テンプレート名
            channel: 投稿先チャンネル
            **template_kwargs: テンプレート追加パラメータ
            
        Returns:
            SlackPostHistoryDTO: 投稿履歴
        """
        try:
            # チャンネル決定
            target_channel = channel or workflow.slack_channel or self.default_channel
            
            # メッセージ生成
            message_text = SlackMessageTemplate.format_message(
                template_name, workflow, **template_kwargs
            )
            
            # 投稿実行
            self._rate_limit_wait()
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=message_text,
                username=f"TechWF v0.5",
                icon_emoji=":books:",
                unfurl_links=False,
                unfurl_media=False
            )
            
            # 投稿履歴作成
            history = SlackPostHistoryDTO(
                n_number=workflow.n_number,
                template_type=template_name,
                message_text=message_text,
                channel=target_channel,
                posted_at=datetime.now(),
                success=response['ok'],
                error_message=None
            )
            
            if response['ok']:
                logger.info(f"Slack post success: {workflow.n_number} -> {target_channel}")
            else:
                history.success = False
                history.error_message = response.get('error', 'Unknown error')
                logger.error(f"Slack post failed: {history.error_message}")
            
            return history
            
        except SlackApiError as e:
            error_msg = f"Slack API Error: {e.response['error']}"
            logger.error(f"Post error ({workflow.n_number}): {error_msg}")
            
            return SlackPostHistoryDTO(
                n_number=workflow.n_number,
                template_type=template_name,
                message_text=message_text if 'message_text' in locals() else '',
                channel=target_channel if 'target_channel' in locals() else '',
                posted_at=datetime.now(),
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Post error ({workflow.n_number}): {error_msg}")
            
            return SlackPostHistoryDTO(
                n_number=workflow.n_number,
                template_type=template_name,
                message_text='',
                channel='',
                posted_at=datetime.now(),
                success=False,
                error_message=error_msg
            )

    def post_batch_messages(self, 
                           workflows: List[PublicationWorkflowDTO],
                           template_name: str,
                           **template_kwargs) -> Tuple[List[SlackPostHistoryDTO], int, int]:
        """
        バッチメッセージ投稿
        
        Args:
            workflows: ワークフローリスト
            template_name: テンプレート名
            **template_kwargs: テンプレート追加パラメータ
            
        Returns:
            Tuple[List[SlackPostHistoryDTO], int, int]: (投稿履歴, 成功数, 失敗数)
        """
        histories = []
        success_count = 0
        failure_count = 0
        
        for workflow in workflows:
            # Slack投稿可否チェック
            if not workflow.can_post_to_slack():
                logger.warning(f"Slack投稿不可: {workflow.n_number} (設定不足または完了済み)")
                continue
            
            history = self.post_message(workflow, template_name, **template_kwargs)
            histories.append(history)
            
            if history.success:
                success_count += 1
            else:
                failure_count += 1
            
            # レート制限対策（バッチ投稿は長めの間隔）
            if len(workflows) > 1:
                time.sleep(2.0)
        
        logger.info(f"バッチ投稿完了: {success_count}成功, {failure_count}失敗")
        return histories, success_count, failure_count

    def get_channels(self) -> List[Dict[str, str]]:
        """
        チャンネル一覧取得
        
        Returns:
            List[Dict[str, str]]: チャンネル情報リスト
        """
        try:
            self._rate_limit_wait()
            
            # パブリックチャンネル取得
            public_response = self.client.conversations_list(
                types="public_channel",
                exclude_archived=True,
                limit=100
            )
            
            # プライベートチャンネル取得（Bot参加済みのみ）
            private_response = self.client.conversations_list(
                types="private_channel",
                exclude_archived=True,
                limit=100
            )
            
            channels = []
            
            # パブリックチャンネル処理
            if public_response['ok']:
                for channel in public_response['channels']:
                    channels.append({
                        'id': channel['id'],
                        'name': f"#{channel['name']}",
                        'type': 'public',
                        'member_count': channel.get('num_members', 0)
                    })
            
            # プライベートチャンネル処理
            if private_response['ok']:
                for channel in private_response['channels']:
                    channels.append({
                        'id': channel['id'],
                        'name': f"#{channel['name']}",
                        'type': 'private',
                        'member_count': channel.get('num_members', 0)
                    })
            
            # 名前順でソート
            channels.sort(key=lambda x: x['name'])
            
            logger.debug(f"チャンネル一覧取得: {len(channels)}件")
            return channels
            
        except SlackApiError as e:
            logger.error(f"チャンネル一覧取得エラー: {e.response['error']}")
            return []

    def test_connection(self) -> Dict[str, Any]:
        """
        接続テスト
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            self._rate_limit_wait()
            response = self.client.auth_test()
            
            result = {
                'success': response['ok'],
                'bot_info': self.bot_info if hasattr(self, 'bot_info') else {},
                'error': None
            }
            
            if response['ok']:
                # 追加情報取得
                try:
                    channels = self.get_channels()
                    result['channel_count'] = len(channels)
                except:
                    result['channel_count'] = 0
            else:
                result['error'] = response.get('error', '不明なエラー')
                
            return result
            
        except SlackApiError as e:
            return {
                'success': False,
                'bot_info': {},
                'error': e.response['error'],
                'channel_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'bot_info': {},
                'error': str(e),
                'channel_count': 0
            }

    def get_service_info(self) -> Dict[str, Any]:
        """
        サービス情報取得
        
        Returns:
            Dict[str, Any]: サービス情報
        """
        info = {
            'bot_token_prefix': self.bot_token[:12] + '...' if len(self.bot_token) > 12 else self.bot_token,
            'default_channel': self.default_channel,
            'available_templates': SlackMessageTemplate.get_template_names(),
            'rate_limit_interval': self.min_request_interval,
            'last_request': self.last_request_time
        }
        
        if hasattr(self, 'bot_info'):
            info.update(self.bot_info)
        
        return info


# ヘルパー関数
def create_slack_service(bot_token: str, default_channel: str = "#general") -> SlackService:
    """
    Slack サービス作成ヘルパー
    
    Args:
        bot_token: Bot Token
        default_channel: デフォルトチャンネル
        
    Returns:
        SlackService: 作成されたサービス
    """
    return SlackService(bot_token, default_channel)

def get_message_preview(workflow: PublicationWorkflowDTO, 
                       template_name: str,
                       **template_kwargs) -> str:
    """
    メッセージプレビュー取得
    
    Args:
        workflow: ワークフローDTO
        template_name: テンプレート名
        **template_kwargs: テンプレート追加パラメータ
        
    Returns:
        str: プレビューメッセージ
    """
    try:
        return SlackMessageTemplate.format_message(template_name, workflow, **template_kwargs)
    except Exception as e:
        return f"プレビューエラー: {e}"