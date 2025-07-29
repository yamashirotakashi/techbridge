import json
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_slack_status_command(
    async_client: AsyncClient,
    sample_slack_command,
    db_session
):
    """Slack /statusコマンドのテスト"""
    from app.models.workflow import WorkflowItem
    from app.models.enums import WorkflowStatus
    
    # テストデータを作成
    workflow_item = WorkflowItem(
        n_number="N99999",
        book_id="tbf17-test001",
        title="テスト技術書",
        author="テスト著者",
        repository_name="n99999-test-book",
        slack_channel="#test-channel",
        status=WorkflowStatus.MANUSCRIPT_REQUESTED,
        assigned_editor="editor@example.com"
    )
    db_session.add(workflow_item)
    await db_session.commit()
    
    # Slack署名を生成
    settings.SLACK_SIGNING_SECRET = "test-secret"
    timestamp = "1234567890"
    req_body = urlencode(sample_slack_command)
    base_string = f"v0:{timestamp}:{req_body}"
    signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    response = await async_client.post(
        "/api/v1/slack/commands/status",
        data=sample_slack_command,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "in_channel"
    assert "N99999" in data["text"]
    assert "原稿依頼" in data["text"]  # MANUSCRIPT_REQUESTEDの日本語表示
    assert "テスト技術書" in data["text"]


@pytest.mark.asyncio
async def test_slack_status_command_not_found(
    async_client: AsyncClient,
    sample_slack_command,
    db_session
):
    """存在しないN番号での/statusコマンドテスト"""
    sample_slack_command["text"] = "N00000"  # 存在しないN番号
    
    settings.SLACK_SIGNING_SECRET = "test-secret"
    timestamp = "1234567890"
    req_body = urlencode(sample_slack_command)
    base_string = f"v0:{timestamp}:{req_body}"
    signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    response = await async_client.post(
        "/api/v1/slack/commands/status",
        data=sample_slack_command,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "ephemeral"  # エラーは本人のみに表示
    assert "見つかりませんでした" in data["text"]


@pytest.mark.asyncio
async def test_slack_update_command(
    async_client: AsyncClient,
    db_session
):
    """Slack /updateコマンドのテスト"""
    from app.models.workflow import WorkflowItem
    from app.models.enums import WorkflowStatus
    
    # テストデータを作成
    workflow_item = WorkflowItem(
        n_number="N99999",
        book_id="tbf17-test001",
        title="テスト技術書",
        author="テスト著者",
        repository_name="n99999-test-book",
        slack_channel="#test-channel",
        status=WorkflowStatus.MANUSCRIPT_REQUESTED
    )
    db_session.add(workflow_item)
    await db_session.commit()
    
    # updateコマンドのペイロード
    update_command = {
        "token": "test-token",
        "team_id": "T0001",
        "team_domain": "test-team",
        "channel_id": "C0001",
        "channel_name": "test-channel",
        "user_id": "U0001",
        "user_name": "testuser",
        "command": "/update",
        "text": "N99999 first_proof",
        "response_url": "https://hooks.slack.com/commands/test",
        "trigger_id": "12345.67890"
    }
    
    settings.SLACK_SIGNING_SECRET = "test-secret"
    timestamp = "1234567890"
    req_body = urlencode(update_command)
    base_string = f"v0:{timestamp}:{req_body}"
    signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    with patch('app.api.v1.slack.SlackService') as mock_slack:
        mock_slack_instance = AsyncMock()
        mock_slack.return_value = mock_slack_instance
        mock_slack_instance.send_status_update.return_value = True
        
        response = await async_client.post(
            "/api/v1/slack/commands/update",
            data=update_command,
            headers={
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "in_channel"
    assert "更新しました" in data["text"]
    assert "初校" in data["text"]  # FIRST_PROOFの日本語表示
    
    # データベースでステータスが更新されていることを確認
    await db_session.refresh(workflow_item)
    assert workflow_item.status == WorkflowStatus.FIRST_PROOF


@pytest.mark.asyncio
async def test_slack_update_invalid_status(
    async_client: AsyncClient,
    db_session
):
    """無効なステータスでの/updateコマンドテスト"""
    update_command = {
        "token": "test-token",
        "team_id": "T0001",
        "team_domain": "test-team",
        "channel_id": "C0001",
        "channel_name": "test-channel",
        "user_id": "U0001",
        "user_name": "testuser",
        "command": "/update",
        "text": "N99999 invalid_status",
        "response_url": "https://hooks.slack.com/commands/test",
        "trigger_id": "12345.67890"
    }
    
    settings.SLACK_SIGNING_SECRET = "test-secret"
    timestamp = "1234567890"
    req_body = urlencode(update_command)
    base_string = f"v0:{timestamp}:{req_body}"
    signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    response = await async_client.post(
        "/api/v1/slack/commands/update",
        data=update_command,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "ephemeral"
    assert "無効なステータス" in data["text"]


@pytest.mark.asyncio
async def test_slack_signature_verification_failed(
    async_client: AsyncClient,
    sample_slack_command
):
    """Slack署名検証失敗のテスト"""
    settings.SLACK_SIGNING_SECRET = "test-secret"
    
    response = await async_client.post(
        "/api/v1/slack/commands/status",
        data=sample_slack_command,
        headers={
            "X-Slack-Request-Timestamp": "1234567890",
            "X-Slack-Signature": "invalid-signature",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid request signature"


# 必要なインポートを追加
import hmac
import hashlib