import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.workflow import WorkflowService
from app.services.slack import SlackService
from app.services.google_sheets import GoogleSheetsService
from app.models.enums import WorkflowStatus


@pytest.mark.asyncio
async def test_workflow_service_create_or_update(db_session):
    """WorkflowServiceのcreate_or_updateメソッドのテスト"""
    service = WorkflowService(db_session)
    
    # 新規作成
    item_data = {
        "n_number": "N99999",
        "book_id": "tbf17-test001",
        "title": "テスト技術書",
        "author": "テスト著者",
        "status": WorkflowStatus.DISCOVERED,
        "repository_name": "n99999-test-book",
        "slack_channel": "#test-channel"
    }
    
    item = await service.create_or_update(**item_data)
    assert item.n_number == "N99999"
    assert item.status == WorkflowStatus.DISCOVERED
    
    # 更新
    update_data = {
        "n_number": "N99999",
        "status": WorkflowStatus.PURCHASED,
        "assigned_editor": "editor@example.com"
    }
    
    updated_item = await service.create_or_update(**update_data)
    assert updated_item.id == item.id  # 同じアイテムが更新されている
    assert updated_item.status == WorkflowStatus.PURCHASED
    assert updated_item.assigned_editor == "editor@example.com"


@pytest.mark.asyncio
async def test_workflow_service_get_by_n_number(db_session):
    """WorkflowServiceのget_by_n_numberメソッドのテスト"""
    service = WorkflowService(db_session)
    
    # アイテムを作成
    await service.create_or_update(
        n_number="N99999",
        book_id="tbf17-test001",
        title="テスト技術書",
        author="テスト著者",
        status=WorkflowStatus.DISCOVERED,
        repository_name="n99999-test-book",
        slack_channel="#test-channel"
    )
    
    # 取得
    item = await service.get_by_n_number("N99999")
    assert item is not None
    assert item.n_number == "N99999"
    
    # 存在しないN番号
    not_found = await service.get_by_n_number("N00000")
    assert not_found is None


@pytest.mark.asyncio
async def test_slack_service_send_status_update():
    """SlackServiceのsend_status_updateメソッドのテスト"""
    with patch('app.services.slack.WebClient') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.chat_postMessage.return_value = {"ok": True}
        
        service = SlackService("test-token")
        result = await service.send_status_update(
            channel="#test-channel",
            n_number="N99999",
            title="テスト技術書",
            old_status=WorkflowStatus.DISCOVERED,
            new_status=WorkflowStatus.PURCHASED
        )
        
        assert result is True
        mock_instance.chat_postMessage.assert_called_once()
        
        # 送信されたメッセージの内容を確認
        call_args = mock_instance.chat_postMessage.call_args
        assert call_args.kwargs["channel"] == "#test-channel"
        assert "N99999" in call_args.kwargs["text"]
        assert "購入完了" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_slack_service_send_completion_notification():
    """SlackServiceのsend_completion_notificationメソッドのテスト"""
    with patch('app.services.slack.WebClient') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.chat_postMessage.return_value = {"ok": True}
        
        service = SlackService("test-token")
        result = await service.send_completion_notification(
            channel="#test-channel",
            n_number="N99999",
            repository_name="n99999-test-book",
            metadata={"pages": 100, "format": "PDF"}
        )
        
        assert result is True
        mock_instance.chat_postMessage.assert_called_once()
        
        # 送信されたメッセージの内容を確認
        call_args = mock_instance.chat_postMessage.call_args
        assert call_args.kwargs["channel"] == "#test-channel"
        assert "完了" in call_args.kwargs["text"]
        assert "N99999" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_google_sheets_service_get_channel_name():
    """GoogleSheetsServiceのget_channel_nameメソッドのテスト"""
    with patch('app.services.google_sheets.build') as mock_build:
        # Google Sheets APIのモック
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_values = MagicMock()
        
        mock_build.return_value = mock_service
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.values.return_value = mock_values
        
        # スプレッドシートのデータ
        mock_values.get.return_value.execute.return_value = {
            "values": [
                ["N番号", "タイトル", "チャンネル名"],
                ["N99999", "テスト技術書", "#test-channel"],
                ["N99998", "別の技術書", "#another-channel"]
            ]
        }
        
        service = GoogleSheetsService(
            credentials_dict={"test": "credentials"},
            spreadsheet_id="test-sheet-id"
        )
        
        # 存在するN番号
        channel = await service.get_channel_name("N99999")
        assert channel == "#test-channel"
        
        # 存在しないN番号
        channel = await service.get_channel_name("N00000")
        assert channel == "#general"  # デフォルトチャンネル


@pytest.mark.asyncio
async def test_google_sheets_service_update_status():
    """GoogleSheetsServiceのupdate_statusメソッドのテスト"""
    with patch('app.services.google_sheets.build') as mock_build:
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_values = MagicMock()
        
        mock_build.return_value = mock_service
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.values.return_value = mock_values
        
        # 現在のデータを返す
        mock_values.get.return_value.execute.return_value = {
            "values": [
                ["N番号", "タイトル", "ステータス", "更新日時"],
                ["N99999", "テスト技術書", "発見", "2025-01-29 10:00:00"]
            ]
        }
        
        # 更新操作
        mock_values.update.return_value.execute.return_value = {
            "updatedCells": 2
        }
        
        service = GoogleSheetsService(
            credentials_dict={"test": "credentials"},
            spreadsheet_id="test-sheet-id"
        )
        
        result = await service.update_status(
            n_number="N99999",
            status=WorkflowStatus.PURCHASED
        )
        
        assert result is True
        
        # updateが呼ばれたことを確認
        mock_values.update.assert_called_once()
        update_args = mock_values.update.call_args
        assert "購入完了" in str(update_args)  # ステータスが日本語に変換されている