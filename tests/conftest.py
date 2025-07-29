import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# テスト用データベースURL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "sqlite+aiosqlite:///:memory:"
)

# テスト用エンジンとセッション
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """イベントループのフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションのフィクスチャ"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    """依存性注入のオーバーライド"""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db) -> TestClient:
    """同期テストクライアント"""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """非同期テストクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_slack_token():
    """Slackトークンのモック"""
    return "xoxb-test-token"


@pytest.fixture
def mock_google_credentials():
    """Google認証情報のモック"""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    }


@pytest.fixture
def sample_tech_webhook_payload():
    """[tech]からのWebhookペイロードサンプル"""
    return {
        "event": "status_change",
        "book_id": "tbf17-test001",
        "n_number": "N99999",
        "title": "テスト技術書",
        "author": "テスト著者",
        "status": "purchased",
        "timestamp": "2025-01-29T10:00:00Z",
        "metadata": {
            "circle": "テストサークル",
            "url": "https://techbookfest.org/product/test001"
        }
    }


@pytest.fixture
def sample_techzip_webhook_payload():
    """[techzip]からのWebhookペイロードサンプル"""
    return {
        "event": "completion",
        "n_number": "N99999",
        "repository_name": "n99999-test-book",
        "status": "completed",
        "timestamp": "2025-01-29T15:00:00Z",
        "metadata": {
            "pages": 100,
            "format": "PDF",
            "completed_by": "editor@example.com"
        }
    }


@pytest.fixture
def sample_slack_command():
    """Slackコマンドのサンプル"""
    return {
        "token": "test-token",
        "team_id": "T0001",
        "team_domain": "test-team",
        "channel_id": "C0001",
        "channel_name": "test-channel",
        "user_id": "U0001",
        "user_name": "testuser",
        "command": "/status",
        "text": "N99999",
        "response_url": "https://hooks.slack.com/commands/test",
        "trigger_id": "12345.67890"
    }