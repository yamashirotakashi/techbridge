"""Slack integration service."""

import logging
from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.core.config import settings
from app.models.workflow import WorkflowStatus

logger = logging.getLogger(__name__)


class SlackService:
    """Service for Slack integrations."""

    def __init__(self, client: Optional[WebClient] = None):
        self.client = client or WebClient(token=settings.SLACK_BOT_TOKEN)

    async def send_status_update(
        self,
        channel: str,
        n_number: str,
        old_status: Optional[WorkflowStatus],
        new_status: WorkflowStatus,
        updated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send status update notification to Slack channel."""
        try:
            # Status emoji mapping
            status_emoji = {
                WorkflowStatus.DISCOVERED: "=",
                WorkflowStatus.PURCHASED: "=°",
                WorkflowStatus.MANUSCRIPT_REQUESTED: "=Ý",
                WorkflowStatus.MANUSCRIPT_RECEIVED: "=è",
                WorkflowStatus.FIRST_PROOF: "=Ö",
                WorkflowStatus.SECOND_PROOF: "=Ú",
                WorkflowStatus.COMPLETED: "",
            }

            emoji = status_emoji.get(new_status, "S")
            
            # Build message
            text = f"{emoji} *{n_number}* n¹Æü¿¹Lô°UŒ~W_"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{n_number} ¹Æü¿¹ô°",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*°WD¹Æü¿¹:*\n{emoji} {new_status.value}",
                        },
                    ],
                },
            ]

            if old_status:
                old_emoji = status_emoji.get(old_status, "S")
                blocks[1]["fields"].insert(0, {
                    "type": "mrkdwn",
                    "text": f"*åMn¹Æü¿¹:*\n{old_emoji} {old_status.value}",
                })

            if updated_by:
                blocks[1]["fields"].append({
                    "type": "mrkdwn",
                    "text": f"*ô°:*\n<@{updated_by}>",
                })

            if metadata:
                # Add relevant metadata as context
                context_elements = []
                if "book_title" in metadata:
                    context_elements.append(f"=Ö {metadata['book_title']}")
                if "author" in metadata:
                    context_elements.append(f" {metadata['author']}")
                
                if context_elements:
                    blocks.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": " | ".join(context_elements),
                            }
                        ],
                    })

            # Send message
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
            )
            
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    async def send_completion_notification(
        self,
        channel: str,
        n_number: str,
        repository_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send completion notification to Slack channel."""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"<‰ {n_number} 6\Œ†",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{n_number}* n6\LŒ†W~W_\n\n"
                            f"*êÝ¸Èê:* `{repository_name}`"
                        ),
                    },
                },
            ]

            if metadata:
                # Add metadata fields
                fields = []
                if "pdf_url" in metadata:
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*PDF:* <{metadata['pdf_url']}|À¦óíüÉ>",
                    })
                if "epub_url" in metadata:
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*EPUB:* <{metadata['epub_url']}|À¦óíüÉ>",
                    })
                
                if fields:
                    blocks.append({
                        "type": "section",
                        "fields": fields,
                    })

            # Add celebration
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "J²ŒU~gW_ <Š",
                },
            })

            response = self.client.chat_postMessage(
                channel=channel,
                text=f"<‰ {n_number} 6\Œ†",
                blocks=blocks,
            )
            
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    async def get_channel_id(self, channel_name: str) -> Optional[str]:
        """Get channel ID from channel name."""
        try:
            # Remove # if present
            channel_name = channel_name.lstrip("#")
            
            # Get all channels
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=1000,
            )
            
            for channel in response["channels"]:
                if channel["name"] == channel_name:
                    return channel["id"]
            
            return None
            
        except SlackApiError as e:
            logger.error(f"Failed to get channel ID: {e.response['error']}")
            return None