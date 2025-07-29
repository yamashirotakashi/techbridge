"""Test endpoints for Google Sheets and Slack integration."""

from typing import Optional
from fastapi import APIRouter, HTTPException
import structlog

from app.services.google_sheets import GoogleSheetsService
from app.services.slack import SlackService
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/sheets/connection")
async def test_google_sheets_connection():
    """Test Google Sheets connection."""
    try:
        sheets_service = GoogleSheetsService()
        is_connected = sheets_service.test_connection()
        
        return {
            "service": "Google Sheets",
            "connected": is_connected,
            "sheet_id": settings.GOOGLE_SHEETS_ID
        }
    except Exception as e:
        logger.error("Google Sheets connection test failed", error=str(e))
        return {
            "service": "Google Sheets",
            "connected": False,
            "error": str(e)
        }


@router.get("/sheets/search/{n_code}")
async def test_n_code_search(n_code: str):
    """Test N-code search in Google Sheets."""
    try:
        sheets_service = GoogleSheetsService()
        result = sheets_service.search_n_code(n_code)
        
        return {
            "n_code": n_code,
            "found": result is not None,
            "data": result
        }
    except Exception as e:
        logger.error("N-code search failed", n_code=n_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sheets/workflow/{n_code}")
async def test_workflow_info(n_code: str):
    """Test workflow information retrieval."""
    try:
        sheets_service = GoogleSheetsService()
        workflow_info = sheets_service.get_workflow_info(n_code)
        
        return {
            "n_code": n_code,
            "found": workflow_info is not None,
            "workflow_info": workflow_info
        }
    except Exception as e:
        logger.error("Workflow info retrieval failed", n_code=n_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sheets/read-cell/{n_code}")
async def test_read_cell(n_code: str, column: str = "G"):
    """Test reading a specific cell."""
    try:
        sheets_service = GoogleSheetsService()
        cell_value = sheets_service.read_cell(n_code, column)
        
        return {
            "n_code": n_code,
            "column": column,
            "value": cell_value,
            "success": cell_value is not None
        }
    except Exception as e:
        logger.error("Cell read failed", n_code=n_code, column=column, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sheets/write-cell/{n_code}")
async def test_write_cell(n_code: str, value: str, column: str = "G"):
    """Test writing to a specific cell."""
    try:
        sheets_service = GoogleSheetsService()
        success = sheets_service.write_cell(n_code, value, column)
        
        return {
            "n_code": n_code,
            "column": column,
            "value": value,
            "success": success
        }
    except Exception as e:
        logger.error("Cell write failed", n_code=n_code, column=column, value=value, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sheets/test-read-write/{n_code}")
async def test_sheets_read_write(n_code: str, test_value: str = "test_write", column: str = "G"):
    """Test complete read-write cycle."""
    try:
        sheets_service = GoogleSheetsService()
        result = sheets_service.test_read_write(n_code, test_value, column)
        
        return result
    except Exception as e:
        logger.error("Read-write test failed", n_code=n_code, test_value=test_value, column=column, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/channel-resolve/{n_code}")
async def test_slack_channel_resolve(n_code: str, default_channel: Optional[str] = "#general"):
    """Test Slack channel name resolution."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        resolved_channel = slack_service.resolve_channel_name(n_code, default_channel)
        resolved_channel_id = slack_service.resolve_channel_id(n_code, default_channel)
        
        return {
            "n_code": n_code,
            "default_channel": default_channel,
            "resolved_channel": resolved_channel,
            "resolved_channel_id": resolved_channel_id,
            "sheets_available": slack_service.sheets_service is not None
        }
    except Exception as e:
        logger.error("Slack channel resolution failed", n_code=n_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/channel-id/{channel_name}")
async def test_get_channel_id(channel_name: str):
    """Test getting channel ID from channel name."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        channel_id = slack_service.get_channel_id(channel_name)
        
        return {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "found": channel_id is not None
        }
    except Exception as e:
        logger.error("Channel ID lookup failed", channel_name=channel_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slack/channels")
async def test_list_channels():
    """Test listing available Slack channels."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        
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
            
            result = slack_service.client.conversations_list(**params)
            channels_batch = result.get("channels", [])
            all_channels.extend(channels_batch)
            
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        channels = all_channels
        channel_info = []
        
        # Botが参加しているプライベートチャンネルのみ
        for channel in channels:
            if channel.get("is_member", False):
                channel_info.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel.get("is_private", True),
                    "is_member": True
                })
        
        return {
            "total_channels": len(channel_info),
            "channels": channel_info,  # 全チャンネル表示
            "bot_permissions": "conversations_list",
            "repo_channels": [ch for ch in channel_info if 'n2279' in ch['name'] or 'python' in ch['name']]
        }
    except Exception as e:
        logger.error("Channel listing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/post-message/{channel_name}")
async def test_post_message(channel_name: str, message: str = "🧪 TechBridge API Test Message"):
    """Test posting a message to Slack channel."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        result = slack_service.post_test_message(channel_name, message)
        
        return result
    except Exception as e:
        logger.error("Message posting failed", channel=channel_name, message=message, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/slack/delete-message/{channel_name}/{message_ts}")
async def test_delete_message(channel_name: str, message_ts: str):
    """Test deleting a message from Slack channel."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        success = slack_service.delete_message(channel_name, message_ts)
        
        return {
            "success": success,
            "channel": channel_name,
            "message_ts": message_ts
        }
    except Exception as e:
        logger.error("Message deletion failed", channel=channel_name, ts=message_ts, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/test-post-delete/{channel_name}")
async def test_post_and_delete_message(channel_name: str, 
                                     message: str = "🧪 TechBridge 投稿・削除テスト",
                                     delay_seconds: int = 5):
    """Test posting and auto-deleting a message."""
    try:
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        result = slack_service.test_post_and_delete(channel_name, message, delay_seconds)
        
        return result
    except Exception as e:
        logger.error("Post and delete test failed", channel=channel_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/integration/{n_code}")
async def test_full_integration(n_code: str):
    """Test full integration workflow."""
    try:
        results = {}
        
        # Test Google Sheets
        try:
            sheets_service = GoogleSheetsService()
            sheets_result = sheets_service.search_n_code(n_code)
            results["sheets"] = {
                "success": True,
                "data": sheets_result
            }
        except Exception as e:
            results["sheets"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Slack channel resolution
        try:
            slack_service = SlackService(settings.SLACK_BOT_TOKEN)
            resolved_channel = slack_service.resolve_channel_name(n_code)
            resolved_channel_id = slack_service.resolve_channel_id(n_code)
            results["slack"] = {
                "success": True,
                "resolved_channel": resolved_channel,
                "resolved_channel_id": resolved_channel_id
            }
        except Exception as e:
            results["slack"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "n_code": n_code,
            "integration_test": results,
            "overall_success": all(r.get("success", False) for r in results.values())
        }
    except Exception as e:
        logger.error("Full integration test failed", n_code=n_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))