# TechBridge 実装計画書
バージョン: 1.0  
作成日: 2025-07-29

## 1. 実装方針

### 1.1 基本戦略
- **最小改修**: 既存システム（[tech], [techzip]）への影響を最小限に抑制
- **段階的実装**: MVPから機能拡張へ段階的に構築
- **イベント駆動**: Webhook/API による疎結合アーキテクチャ
- **既存インフラ活用**: Slack, Google Sheets の既存設定を最大限活用

### 1.2 技術選択理由

| 技術 | 選択理由 |
|------|----------|
| **FastAPI** | 高性能、自動ドキュメント生成、型安全性 |
| **PostgreSQL** | 信頼性、JSONB対応、スケーラビリティ |
| **Redis** | キャッシュ、セッション管理、リアルタイム処理 |
| **Docker** | 環境統一、デプロイメント簡素化 |
| **pytest** | テストカバレッジ、非同期対応 |

## 2. 詳細実装計画

### 2.1 Phase 1: MVP実装 (4週間)

#### Week 1: 基盤構築

**Day 1-2: プロジェクト初期化**
```bash
# プロジェクト構造作成
mkdir -p {app/{api,core,models,services,integrations},tests,docs,docker,scripts}

# FastAPI初期設定
pip install fastapi[all] sqlalchemy[postgresql] redis python-multipart

# Docker環境構築
touch docker-compose.yml docker-compose.dev.yml Dockerfile
```

**実装タスク:**
- [ ] `app/main.py` - FastAPIアプリケーション初期化
- [ ] `app/core/config.py` - 設定管理（pydantic-settings）
- [ ] `app/core/database.py` - SQLAlchemy設定
- [ ] `app/models/base.py` - ベースモデル定義
- [ ] `docker-compose.dev.yml` - 開発環境設定

**Day 3-4: データモデル実装**
```python
# app/models/workflow.py
class WorkflowItem(Base):
    __tablename__ = "workflow_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    n_number: Mapped[str] = mapped_column(String(10), unique=True)
    book_id: Mapped[Optional[str]] = mapped_column(String(100))
    repository_name: Mapped[Optional[str]] = mapped_column(String(100))
    slack_channel: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus))
    assigned_editor: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
```

**実装タスク:**
- [ ] `app/models/workflow.py` - WorkflowItem, StatusHistory
- [ ] `app/models/enums.py` - ProgressStatus enum
- [ ] `alembic/versions/001_initial.py` - 初期マイグレーション
- [ ] `app/crud/workflow.py` - CRUD操作

**Day 5-7: 基本API実装**
```python
# app/api/v1/progress.py
@router.get("/{n_number}")
async def get_progress(n_number: str, db: Session = Depends(get_db)):
    item = await crud.workflow.get_by_n_number(db, n_number)
    if not item:
        raise HTTPException(404, "N番号が見つかりません")
    return item

@router.post("/{n_number}/update")
async def update_status(
    n_number: str, 
    status_update: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    # ステータス更新ロジック
    await crud.workflow.update_status(db, n_number, status_update.status)
    # Slack通知トリガー
    await notify_status_change(n_number, status_update.status)
    return {"message": "更新完了"}
```

**実装タスク:**
- [ ] `app/api/v1/progress.py` - 進捗管理API
- [ ] `app/schemas/progress.py` - Pydanticスキーマ
- [ ] `app/crud/workflow.py` - データベース操作
- [ ] `tests/api/test_progress.py` - APIテスト

#### Week 2: Slack統合

**Day 8-10: Slack Bot基盤**
```python
# app/integrations/slack.py
class SlackClient:
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
    
    async def post_message(self, channel: str, text: str, blocks: Optional[List] = None):
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return response["ts"]  # message timestamp
        except SlackApiError as e:
            logger.error(f"Slack API error: {e}")
            raise
    
    async def find_channel_by_name(self, channel_name: str) -> Optional[str]:
        # チャンネル名からチャンネルIDを取得
        pass
```

**実装タスク:**
- [ ] `app/integrations/slack.py` - Slack Web APIクライアント
- [ ] `app/services/notification.py` - 通知サービス
- [ ] `app/api/v1/slack.py` - Slackイベント処理
- [ ] `tests/integrations/test_slack.py` - Slack統合テスト

**Day 11-12: スラッシュコマンド**
```python
# app/api/v1/slack.py
@router.post("/commands/status")
async def slack_status_command(
    command: SlackCommand = Depends(verify_slack_signature),
    db: Session = Depends(get_db)
):
    # /status N02345
    text = command.text.strip()
    if not text.startswith('N'):
        return {"text": "使用方法: /status N番号"}
    
    n_number = text.upper()
    item = await crud.workflow.get_by_n_number(db, n_number)
    
    if not item:
        return {"text": f"{n_number}が見つかりません"}
    
    # 進捗表示を整形
    progress_text = format_progress_display(item)
    return {"text": progress_text}

def format_progress_display(item: WorkflowItem) -> str:
    status_icons = {
        ProgressStatus.DISCOVERED: "🔍",
        ProgressStatus.PURCHASED: "💰", 
        ProgressStatus.MANUSCRIPT_REQUESTED: "✍️",
        ProgressStatus.MANUSCRIPT_RECEIVED: "📄",
        ProgressStatus.FIRST_PROOF: "📝",
        ProgressStatus.SECOND_PROOF: "✏️",
        ProgressStatus.COMPLETED: "✅"
    }
    
    current_icon = status_icons.get(item.status, "❓")
    return f"📊 {item.n_number}の進捗\n{current_icon} {item.status.value}\n更新: {item.updated_at.strftime('%Y-%m-%d %H:%M')}"
```

**実装タスク:**
- [ ] `app/api/v1/slack.py` - スラッシュコマンド処理
- [ ] `app/core/slack_auth.py` - Slack署名検証
- [ ] `app/services/command_processor.py` - コマンド解析
- [ ] `tests/api/test_slack_commands.py` - コマンドテスト

**Day 13-14: 通知機能**
```python
# app/services/notification.py
class NotificationService:
    def __init__(self):
        self.slack = SlackClient()
        self.sheets = GoogleSheetsClient()
    
    async def notify_status_change(
        self, 
        n_number: str, 
        old_status: ProgressStatus,
        new_status: ProgressStatus
    ):
        # チャンネル決定ロジック
        channel = await self.determine_notification_channel(n_number, new_status)
        
        # メッセージ生成
        message = self.generate_status_message(n_number, old_status, new_status)
        
        # 通知送信
        await self.slack.post_message(channel, message)
        
        # 通知履歴記録
        await self.record_notification(n_number, channel, message)
    
    async def determine_notification_channel(self, n_number: str, status: ProgressStatus) -> str:
        # 状態に応じた通知先決定
        if status in [ProgressStatus.DISCOVERED, ProgressStatus.PURCHASED]:
            return settings.MANAGEMENT_CHANNEL
        else:
            # 著者チャンネルまたは編集者チャンネル
            repo_name = await self.sheets.get_repository_name(n_number)
            return f"#{repo_name}" if repo_name else settings.DEFAULT_CHANNEL
```

**実装タスク:**
- [ ] `app/services/notification.py` - 通知サービス
- [ ] `app/models/notification.py` - 通知履歴モデル
- [ ] `app/utils/message_formatter.py` - メッセージ整形
- [ ] `tests/services/test_notification.py` - 通知テスト

#### Week 3: 外部システム統合

**Day 15-17: Google Sheets連携**
```python
# app/integrations/google_sheets.py
class GoogleSheetsClient:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY),
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet_id = settings.GOOGLE_SHEETS_ID
    
    async def get_repository_name(self, n_number: str) -> Optional[str]:
        try:
            # [techzip]の既存実装を参考に実装
            result = await self._execute_with_retry(
                self._search_n_code_impl, n_number
            )
            return result['repository_name'] if result else None
        except Exception as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
    
    async def _search_n_code_impl(self, n_number: str) -> Optional[Dict]:
        range_name = 'A1:C1000'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        for row_idx, row in enumerate(values, start=1):
            if row and len(row) > 0:
                if str(row[0]).strip().upper() == n_number.upper():
                    repository_name = row[2] if len(row) > 2 else None
                    if repository_name:
                        return {
                            'row': row_idx,
                            'n_number': n_number,
                            'repository_name': repository_name.strip()
                        }
        return None
```

**実装タスク:**
- [ ] `app/integrations/google_sheets.py` - Google Sheets API
- [ ] `app/services/repository_resolver.py` - リポジトリ名解決
- [ ] `app/utils/retry.py` - リトライユーティリティ
- [ ] `tests/integrations/test_google_sheets.py` - Sheets統合テスト

**Day 18-19: [tech]Webhook統合**
```python
# app/api/v1/webhooks.py
@router.post("/tech/status-change")
async def tech_status_change(
    payload: TechStatusChangePayload,
    signature: str = Header(alias="X-Tech-Signature"),
    db: Session = Depends(get_db)
):
    # Webhook署名検証
    if not verify_tech_signature(signature, payload.json()):
        raise HTTPException(401, "Invalid signature")
    
    logger.info(f"Received tech webhook: {payload.book_id} -> {payload.new_status}")
    
    # ワークフローアイテム作成または更新
    if payload.new_status == "purchased" and payload.n_number:
        item = await crud.workflow.create_or_update(
            db,
            n_number=payload.n_number,
            book_id=payload.book_id,
            status=ProgressStatus.PURCHASED
        )
        
        # Google Sheetsからリポジトリ名取得
        sheets_client = GoogleSheetsClient()
        repo_name = await sheets_client.get_repository_name(payload.n_number)
        
        if repo_name:
            item.repository_name = repo_name
            item.slack_channel = f"#{repo_name}"
            await db.commit()
        
        # Slack通知
        await NotificationService().notify_status_change(
            payload.n_number,
            ProgressStatus.DISCOVERED,  # 前の状態（仮定）
            ProgressStatus.PURCHASED
        )
    
    return {"status": "processed"}
```

**実装タスク:**
- [ ] `app/api/v1/webhooks.py` - Webhook受信API
- [ ] `app/schemas/webhooks.py` - Webhookペイロードスキーマ
- [ ] `app/core/webhook_auth.py` - Webhook署名検証
- [ ] `tests/api/test_webhooks.py` - Webhookテスト

**Day 20-21: 状態管理とビジネスロジック**
```python
# app/services/workflow_manager.py
class WorkflowManager:
    def __init__(self):
        self.notification = NotificationService()
        self.sheets = GoogleSheetsClient()
    
    async def process_tech_purchase(
        self, 
        book_id: str, 
        n_number: str,
        db: Session
    ):
        # ワークフローアイテム作成
        item = await crud.workflow.create_or_update(
            db,
            n_number=n_number,
            book_id=book_id,
            status=ProgressStatus.PURCHASED
        )
        
        # メタデータ収集
        await self.enrich_workflow_item(item, db)
        
        # 次のステップを自動実行
        await self.trigger_next_step(item, db)
    
    async def enrich_workflow_item(self, item: WorkflowItem, db: Session):
        """ワークフローアイテムの情報を充実させる"""
        if not item.repository_name:
            repo_name = await self.sheets.get_repository_name(item.n_number)
            if repo_name:
                item.repository_name = repo_name
                item.slack_channel = f"#{repo_name}"
                await db.commit()
    
    async def trigger_next_step(self, item: WorkflowItem, db: Session):
        """次のステップを自動的にトリガー"""
        if item.status == ProgressStatus.PURCHASED:
            # 原稿依頼ステップへ自動遷移
            await self.update_status(
                item.n_number,
                ProgressStatus.MANUSCRIPT_REQUESTED,
                "system",
                db
            )
```

**実装タスク:**
- [ ] `app/services/workflow_manager.py` - ワークフロー管理
- [ ] `app/services/status_transitions.py` - 状態遷移ルール
- [ ] `app/utils/metadata_enricher.py` - メタデータ充実化
- [ ] `tests/services/test_workflow_manager.py` - ワークフロー管理テスト

#### Week 4: 完成とテスト

**Day 22-24: [techzip]統合**
```python
# app/api/v1/webhooks.py
@router.post("/techzip/completion")
async def techzip_completion(
    payload: TechzipCompletionPayload,
    signature: str = Header(alias="X-Techzip-Signature"),
    db: Session = Depends(get_db)
):
    # 署名検証
    if not verify_techzip_signature(signature, payload.json()):
        raise HTTPException(401, "Invalid signature")
    
    logger.info(f"Received techzip completion: {payload.n_number}")
    
    # ステータス更新
    await WorkflowManager().update_status(
        payload.n_number,
        ProgressStatus.FIRST_PROOF,  # またはFIRST_PROOF
        "techzip-system",
        db
    )
    
    return {"status": "processed"}

# [techzip]側の必要な改修
# core/api_processor.py への追加
async def notify_completion(self, n_number: str, success: bool):
    """変換完了時にTechBridgeに通知"""
    if success and settings.TECHBRIDGE_WEBHOOK_URL:
        payload = {
            "n_number": n_number,
            "status": "conversion_completed",
            "timestamp": datetime.now().isoformat()
        }
        try:
            response = requests.post(
                f"{settings.TECHBRIDGE_WEBHOOK_URL}/webhook/techzip/completion",
                json=payload,
                headers={"X-Techzip-Signature": generate_signature(payload)}
            )
            logger.info(f"TechBridge notification sent: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to notify TechBridge: {e}")
```

**実装タスク:**
- [ ] `app/api/v1/webhooks.py` - techzip完了webhook
- [ ] [techzip]への通知機能追加検討
- [ ] `app/schemas/webhooks.py` - techzipペイロードスキーマ
- [ ] `tests/integration/test_techzip_integration.py` - 統合テスト

**Day 25-26: エンドツーエンドテスト**
```python
# tests/e2e/test_full_workflow.py
async def test_full_workflow():
    """完全なワークフローのE2Eテスト"""
    # 1. [tech]からのWebhook受信をシミュレート
    tech_payload = {
        "book_id": "test-book-123",
        "old_status": "wishlisted",
        "new_status": "purchased",
        "n_number": "N99999",
        "timestamp": datetime.now().isoformat()
    }
    
    response = await client.post("/webhook/tech/status-change", json=tech_payload)
    assert response.status_code == 200
    
    # 2. データベース状態確認
    item = await crud.workflow.get_by_n_number(db, "N99999")
    assert item.status == ProgressStatus.PURCHASED
    
    # 3. Slack通知確認（モック）
    mock_slack.post_message.assert_called_once()
    
    # 4. 手動ステータス更新
    await client.post("/api/progress/N99999/update", json={
        "status": "manuscript_received"
    })
    
    # 5. [techzip]完了通知シミュレート
    techzip_payload = {
        "n_number": "N99999",
        "status": "conversion_completed"
    }
    
    await client.post("/webhook/techzip/completion", json=techzip_payload)
    
    # 6. 最終状態確認
    item = await crud.workflow.get_by_n_number(db, "N99999")
    assert item.status == ProgressStatus.FIRST_PROOF
```

**実装タスク:**
- [ ] `tests/e2e/test_full_workflow.py` - フルワークフローテスト
- [ ] `tests/integration/test_external_apis.py` - 外部API統合テスト
- [ ] `app/utils/test_helpers.py` - テストヘルパー
- [ ] `tests/fixtures/` - テストデータフィクスチャ

**Day 27-28: エラーハンドリングとデプロイ準備**
```python
# app/core/error_handler.py
class TechBridgeException(Exception):
    """カスタム例外基底クラス"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class SlackNotificationError(TechBridgeException):
    """Slack通知エラー"""
    pass

class GoogleSheetsError(TechBridgeException):
    """Google Sheets APIエラー"""
    pass

# app/middleware/error_middleware.py
@app.exception_handler(TechBridgeException)
async def techbridge_exception_handler(request: Request, exc: TechBridgeException):
    logger.error(f"TechBridge error: {exc.message}", extra={"details": exc.details})
    
    # 重要なエラーはSlackに通知
    if isinstance(exc, (SlackNotificationError, GoogleSheetsError)):
        await emergency_slack_notification(exc)
    
    return JSONResponse(
        status_code=500,
        content={"message": exc.message, "details": exc.details}
    )
```

**実装タスク:**
- [ ] `app/core/error_handler.py` - エラーハンドリング
- [ ] `app/middleware/error_middleware.py` - エラーミドルウェア
- [ ] `app/utils/health_check.py` - ヘルスチェック
- [ ] `docker/production.dockerfile` - 本番用Dockerfile

### 2.2 Phase 2: 機能拡張 (2週間)

#### Week 5: 管理機能

**実装予定:**
- [ ] Web Dashboard（React + FastAPI）
- [ ] 統計レポート機能
- [ ] 遅延アラート機能
- [ ] バッチ処理機能

#### Week 6: 運用改善

**実装予定:**
- [ ] Prometheus メトリクス
- [ ] Sentry エラートラッキング
- [ ] ログ集約とアラート
- [ ] パフォーマンス最適化

## 3. 技術実装詳細

### 3.1 設定管理

```python
# app/core/config.py
class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Slack
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    management_channel: str = Field("#techbridge-management", env="MANAGEMENT_CHANNEL")
    
    # Google Sheets
    google_sheets_id: str = Field(..., env="GOOGLE_SHEETS_ID")
    google_service_account_key: str = Field(..., env="GOOGLE_SERVICE_ACCOUNT_KEY")
    
    # Webhooks
    tech_webhook_secret: str = Field(..., env="TECH_WEBHOOK_SECRET")
    techzip_webhook_secret: str = Field(..., env="TECHZIP_WEBHOOK_SECRET")
    
    # Application
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3.2 データベース設計

```sql
-- 完全なスキーマ定義
CREATE TYPE progress_status AS ENUM (
    'discovered',
    'purchased',
    'manuscript_requested',
    'manuscript_received',
    'first_proof',
    'second_proof',
    'completed'
);

CREATE TABLE workflow_items (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) UNIQUE NOT NULL,
    book_id VARCHAR(100),
    repository_name VARCHAR(100),
    slack_channel VARCHAR(100),
    status progress_status NOT NULL,
    assigned_editor VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- インデックス
    INDEX idx_n_number (n_number),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
);

CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) REFERENCES workflow_items(n_number) ON DELETE CASCADE,
    old_status progress_status,
    new_status progress_status NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    comment TEXT,
    
    INDEX idx_n_number_changed_at (n_number, changed_at),
    INDEX idx_changed_at (changed_at)
);

CREATE TABLE notification_history (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) REFERENCES workflow_items(n_number) ON DELETE CASCADE,
    channel VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    
    INDEX idx_n_number_sent_at (n_number, sent_at),
    INDEX idx_sent_at (sent_at),
    INDEX idx_success (success)
);

-- トリガー: updated_at自動更新
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflow_items_updated_at 
    BEFORE UPDATE ON workflow_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.3 Docker設定

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://techbridge:password@db:5432/techbridge
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: techbridge
      POSTGRES_USER: techbridge
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/ssl:/etc/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# 非rootユーザー作成
RUN useradd --create-home --shell /bin/bash techbridge
USER techbridge

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 4. テスト戦略

### 4.1 テスト構成

```python
# conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# テスト用データベース
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """イベントループをセッションスコープで作成"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db():
    """テスト用データベースセッション"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    """テスト用FastAPIクライアント"""
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_slack():
    """Slack APIモック"""
    with patch('app.integrations.slack.SlackClient') as mock:
        yield mock

@pytest.fixture
def mock_sheets():
    """Google Sheets APIモック"""
    with patch('app.integrations.google_sheets.GoogleSheetsClient') as mock:
        yield mock
```

### 4.2 テストケース例

```python
# tests/api/test_progress.py
async def test_get_progress_success(client, db):
    # テストデータ作成
    item = WorkflowItem(
        n_number="N12345",
        book_id="book-123",
        status=ProgressStatus.PURCHASED
    )
    db.add(item)
    db.commit()
    
    # API呼び出し
    response = client.get("/api/progress/N12345")
    
    # アサーション
    assert response.status_code == 200
    data = response.json()
    assert data["n_number"] == "N12345"
    assert data["status"] == "purchased"

async def test_get_progress_not_found(client, db):
    response = client.get("/api/progress/N99999")
    assert response.status_code == 404

# tests/services/test_workflow_manager.py
async def test_process_tech_purchase(db, mock_slack, mock_sheets):
    # モック設定
    mock_sheets.get_repository_name.return_value = "test-repo"
    
    # テスト実行
    manager = WorkflowManager()
    await manager.process_tech_purchase("book-123", "N12345", db)
    
    # アサーション
    item = await crud.workflow.get_by_n_number(db, "N12345")
    assert item.book_id == "book-123"
    assert item.status == ProgressStatus.MANUSCRIPT_REQUESTED
    assert item.repository_name == "test-repo"
    
    # Slack通知確認
    mock_slack.post_message.assert_called()
```

## 5. デプロイメント

### 5.1 本番環境設定

```bash
# 本番環境デプロイスクリプト
#!/bin/bash
set -e

echo "🚀 TechBridge 本番デプロイ開始"

# 環境変数チェック
if [ -z "$DATABASE_URL" ] || [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "❌ 必要な環境変数が設定されていません"
    exit 1
fi

# Docker イメージビルド
echo "📦 Docker イメージビルド中..."
docker build -t techbridge-app:latest .

# データベースマイグレーション  
echo "🗄️ データベースマイグレーション実行中..."
docker run --rm --env-file .env techbridge-app:latest alembic upgrade head

# サービス起動
echo "🔄 サービス起動中..."
docker-compose -f docker-compose.prod.yml up -d

# ヘルスチェック
echo "🏥 ヘルスチェック実行中..."
sleep 10
curl -f http://localhost/health || exit 1

echo "✅ デプロイ完了！"
```

### 5.2 監視設定

```python
# app/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# メトリクス定義
webhook_requests_total = Counter(
    'techbridge_webhook_requests_total',
    'Total webhook requests',
    ['source', 'status']
)

status_update_duration = Histogram(
    'techbridge_status_update_duration_seconds',
    'Time spent updating status'
)

active_workflow_items = Gauge(
    'techbridge_active_workflow_items',
    'Number of active workflow items'
)

slack_notifications_total = Counter(
    'techbridge_slack_notifications_total',
    'Total Slack notifications sent',
    ['status', 'success']
)
```

## 6. 運用開始準備

### 6.1 チェックリスト

**環境準備:**
- [ ] 本番データベース設定
- [ ] Redis クラスター設定
- [ ] SSL証明書取得
- [ ] 環境変数設定
- [ ] バックアップ設定

**外部連携:**
- [ ] Slack Bot アプリ作成・承認
- [ ] Google Service Account設定
- [ ] [tech]プロジェクトへのWebhook追加
- [ ] [techzip]プロジェクトへの通知機能追加

**テスト:**
- [ ] 統合テスト実行
- [ ] 負荷テスト実行
- [ ] セキュリティテスト実行
- [ ] 障害復旧テスト実行

**ドキュメント:**
- [ ] 運用手順書作成
- [ ] トラブルシューティングガイド
- [ ] API仕様書更新
- [ ] ユーザーマニュアル作成

### 6.2 段階的ロールアウト

**Week 1: 内部テスト**
- 開発チーム向けテスト環境での動作確認
- 1つのテスト用N番号での全フロー確認

**Week 2: 限定リリース**
- 5つの実際のN番号での運用開始
- 編集者からのフィードバック収集

**Week 3: 段階的拡大**
- 20つのN番号に拡大
- パフォーマンス監視と調整

**Week 4: 全面運用**
- 全N番号での本格運用開始
- 24時間監視体制確立

---

**Next Steps:**
Phase 1完了後、この実装計画書に基づいて開発を開始します。各Weekの終了時点でレビューを実施し、必要に応じて計画を調整します。