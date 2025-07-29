import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowItem
from app.models.enums import WorkflowStatus


@pytest.mark.asyncio
async def test_create_workflow_item(db_session: AsyncSession):
    """WorkflowItemの作成テスト"""
    workflow_item = WorkflowItem(
        n_number="N99999",
        book_id="tbf17-test001",
        title="テスト技術書",
        author="テスト著者",
        repository_name="n99999-test-book",
        slack_channel="#test-channel",
        status=WorkflowStatus.DISCOVERED,
        metadata={"test": "data"}
    )
    
    db_session.add(workflow_item)
    await db_session.commit()
    await db_session.refresh(workflow_item)
    
    assert workflow_item.id is not None
    assert workflow_item.n_number == "N99999"
    assert workflow_item.book_id == "tbf17-test001"
    assert workflow_item.title == "テスト技術書"
    assert workflow_item.author == "テスト著者"
    assert workflow_item.status == WorkflowStatus.DISCOVERED
    assert workflow_item.created_at is not None
    assert workflow_item.updated_at is not None


@pytest.mark.asyncio
async def test_update_workflow_status(db_session: AsyncSession):
    """WorkflowItemのステータス更新テスト"""
    workflow_item = WorkflowItem(
        n_number="N99999",
        book_id="tbf17-test001",
        title="テスト技術書",
        author="テスト著者",
        repository_name="n99999-test-book",
        slack_channel="#test-channel",
        status=WorkflowStatus.DISCOVERED
    )
    
    db_session.add(workflow_item)
    await db_session.commit()
    
    # ステータス更新
    workflow_item.status = WorkflowStatus.PURCHASED
    workflow_item.updated_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(workflow_item)
    
    assert workflow_item.status == WorkflowStatus.PURCHASED
    assert workflow_item.updated_at > workflow_item.created_at


@pytest.mark.asyncio
async def test_workflow_item_with_editor(db_session: AsyncSession):
    """編集者割り当てのテスト"""
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
    await db_session.refresh(workflow_item)
    
    assert workflow_item.assigned_editor == "editor@example.com"


@pytest.mark.asyncio
async def test_workflow_status_transitions():
    """WorkflowStatusの遷移テスト"""
    # 正常な遷移順序
    expected_order = [
        WorkflowStatus.DISCOVERED,
        WorkflowStatus.PURCHASED,
        WorkflowStatus.MANUSCRIPT_REQUESTED,
        WorkflowStatus.MANUSCRIPT_RECEIVED,
        WorkflowStatus.FIRST_PROOF,
        WorkflowStatus.SECOND_PROOF,
        WorkflowStatus.COMPLETED
    ]
    
    # 各ステータスの値が正しい順序であることを確認
    for i in range(len(expected_order) - 1):
        current = expected_order[i]
        next_status = expected_order[i + 1]
        assert current.value < next_status.value