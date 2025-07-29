import json
import hmac
import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import settings


def generate_signature(payload: dict, secret: str) -> str:
    """Webhook署名を生成"""
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


@pytest.mark.asyncio
async def test_tech_webhook_success(
    async_client: AsyncClient,
    sample_tech_webhook_payload,
    db_session
):
    """[tech]からのWebhook受信成功テスト"""
    # 署名を生成
    settings.TECH_WEBHOOK_SECRET = "test-secret"
    signature = generate_signature(sample_tech_webhook_payload, settings.TECH_WEBHOOK_SECRET)
    
    # Slackサービスをモック
    with patch('app.api.v1.webhook.SlackService') as mock_slack:
        mock_slack_instance = AsyncMock()
        mock_slack.return_value = mock_slack_instance
        mock_slack_instance.send_status_update.return_value = True
        
        response = await async_client.post(
            "/api/v1/webhook/tech/status-change",
            json=sample_tech_webhook_payload,
            headers={"X-Webhook-Signature": signature}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["n_number"] == "N99999"
    
    # Slack通知が呼ばれたことを確認
    mock_slack_instance.send_status_update.assert_called_once()


@pytest.mark.asyncio
async def test_tech_webhook_invalid_signature(
    async_client: AsyncClient,
    sample_tech_webhook_payload
):
    """無効な署名でのWebhook受信テスト"""
    settings.TECH_WEBHOOK_SECRET = "test-secret"
    
    response = await async_client.post(
        "/api/v1/webhook/tech/status-change",
        json=sample_tech_webhook_payload,
        headers={"X-Webhook-Signature": "invalid-signature"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"


@pytest.mark.asyncio
async def test_tech_webhook_missing_signature(
    async_client: AsyncClient,
    sample_tech_webhook_payload
):
    """署名なしでのWebhook受信テスト"""
    response = await async_client.post(
        "/api/v1/webhook/tech/status-change",
        json=sample_tech_webhook_payload
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing signature"


@pytest.mark.asyncio
async def test_techzip_webhook_success(
    async_client: AsyncClient,
    sample_techzip_webhook_payload,
    db_session
):
    """[techzip]からのWebhook受信成功テスト"""
    settings.TECHZIP_WEBHOOK_SECRET = "test-secret"
    signature = generate_signature(sample_techzip_webhook_payload, settings.TECHZIP_WEBHOOK_SECRET)
    
    with patch('app.api.v1.webhook.SlackService') as mock_slack:
        mock_slack_instance = AsyncMock()
        mock_slack.return_value = mock_slack_instance
        mock_slack_instance.send_completion_notification.return_value = True
        
        response = await async_client.post(
            "/api/v1/webhook/techzip/completion",
            json=sample_techzip_webhook_payload,
            headers={"X-Webhook-Signature": signature}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["n_number"] == "N99999"
    
    # 完了通知が呼ばれたことを確認
    mock_slack_instance.send_completion_notification.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_with_existing_item(
    async_client: AsyncClient,
    sample_tech_webhook_payload,
    db_session
):
    """既存アイテムのステータス更新テスト"""
    from app.models.workflow import WorkflowItem
    from app.models.enums import WorkflowStatus
    
    # 既存アイテムを作成
    existing_item = WorkflowItem(
        n_number="N99999",
        book_id="tbf17-test001",
        title="既存の技術書",
        author="既存の著者",
        repository_name="n99999-existing-book",
        slack_channel="#existing-channel",
        status=WorkflowStatus.DISCOVERED
    )
    db_session.add(existing_item)
    await db_session.commit()
    
    # ステータス更新のWebhookを送信
    settings.TECH_WEBHOOK_SECRET = "test-secret"
    signature = generate_signature(sample_tech_webhook_payload, settings.TECH_WEBHOOK_SECRET)
    
    with patch('app.api.v1.webhook.SlackService') as mock_slack:
        mock_slack_instance = AsyncMock()
        mock_slack.return_value = mock_slack_instance
        mock_slack_instance.send_status_update.return_value = True
        
        response = await async_client.post(
            "/api/v1/webhook/tech/status-change",
            json=sample_tech_webhook_payload,
            headers={"X-Webhook-Signature": signature}
        )
    
    assert response.status_code == 200
    
    # データベースから更新されたアイテムを取得
    from sqlalchemy import select
    result = await db_session.execute(
        select(WorkflowItem).where(WorkflowItem.n_number == "N99999")
    )
    updated_item = result.scalar_one()
    
    assert updated_item.status == WorkflowStatus.PURCHASED
    assert updated_item.title == "テスト技術書"  # 更新されている
    assert updated_item.author == "テスト著者"  # 更新されている