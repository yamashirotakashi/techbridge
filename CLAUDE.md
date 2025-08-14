# グローバルルールの継承
@../CLAUDE.md

# プロジェクト名: TechBridge - 技術の泉シリーズ統合ワークフロー
最終更新: 2025-07-29

## 🎯 プロジェクト概要
- **目的**: [tech]と[techzip]プロジェクトを統合し、技術の泉シリーズの編集ワークフローを自動化
- **主要機能**: Progress Bridge APIとSlack Bot統合による一気通貫ワークフロー
- **プロジェクトキーワード**: `[techbg]` または `[techbridge]`

## 🏗️ アーキテクチャ概要

```
[tech] → Webhook → [Progress Bridge] → Slack API
                           ↓
                    Google Sheets API
                           ↓
                  Channel Name Resolution
                           ↓
              [techzip] ← 作業完了通知
```

## 📋 システム構成

### 1. Progress Bridge (FastAPI Backend)
- **役割**: [tech]と[techzip]間の統合レイヤー
- **技術**: FastAPI, SQLAlchemy, Redis
- **機能**: 
  - Webhook受信とイベント処理
  - 状態管理と進捗追跡
  - Google Sheets連携
  - Slack API統合

### 2. Slack Bot Interface
- **役割**: 編集者向けUI
- **技術**: Slack Web API, Slash Commands
- **機能**:
  - 自動進捗通知
  - スラッシュコマンド (/status, /update)
  - チャンネル自動振り分け

### 3. Integration Layer
- **役割**: 既存システム統合
- **対象**: [tech] Webhook, [techzip] 完了通知
- **機能**: 最小限改修で連携実現

## 🚀 開発計画

### Phase 1: MVP実装 (4週間)
- Week 1: Progress Bridge API基盤
- Week 2: Slack Bot基本機能
- Week 3: [tech]統合とWebhook
- Week 4: [techzip]統合とテスト

### Phase 2: 機能拡張 (2週間) 
- Advanced状態管理
- ダッシュボード機能
- 統計レポート

## 🛠️ 技術スタック
- **Backend**: FastAPI 0.104+, SQLAlchemy 2.0+
- **Database**: PostgreSQL (開発時SQLite)
- **Cache**: Redis
- **API**: Slack Web API, Google Sheets API
- **Deploy**: Docker, Docker Compose
- **Monitor**: Sentry, Prometheus

## 📁 プロジェクト構造
```
techbridge/
├── app/                    # FastAPI アプリケーション
│   ├── api/               # API エンドポイント
│   ├── core/              # 設定とセキュリティ
│   ├── models/            # データモデル
│   ├── services/          # ビジネスロジック
│   └── integrations/      # 外部API連携
├── tests/                 # テストコード
├── docs/                  # 仕様書
├── docker/               # Docker設定
└── scripts/              # ユーティリティ
```

## 🔑 環境変数
```bash
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# Google Sheets
GOOGLE_SHEETS_ID=17DKsMGQ6...
GOOGLE_SERVICE_ACCOUNT_KEY=...

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# External Systems
TECH_WEBHOOK_SECRET=...
TECHZIP_API_ENDPOINT=...
```

## 📊 データモデル

### ProgressStatus (Enum)
```python
class ProgressStatus(Enum):
    DISCOVERED = "discovered"      # [tech] 発見
    PURCHASED = "purchased"        # [tech] 購入完了
    MANUSCRIPT_REQUESTED = "manuscript_requested"  # 原稿依頼
    MANUSCRIPT_RECEIVED = "manuscript_received"    # 原稿受領
    FIRST_PROOF = "first_proof"    # 初校
    SECOND_PROOF = "second_proof"  # 再校  
    COMPLETED = "completed"        # 完成
```

### WorkflowItem
```python
@dataclass
class WorkflowItem:
    n_number: str
    book_id: str  # [tech] book_id
    repository_name: str
    slack_channel: str
    status: ProgressStatus
    assigned_editor: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
```

## 🔗 API仕様

### Webhook Endpoints
```python
POST /webhook/tech/status-change
POST /webhook/techzip/completion
```

### Slack Commands
```python
GET /slack/status/{n_number}
POST /slack/update-status
POST /slack/commands/status
POST /slack/commands/update
```

## 🧪 テスト戦略
- **Unit Tests**: pytest + pytest-asyncio
- **Integration Tests**: TestClient + Docker Compose
- **E2E Tests**: Slack API mocking

## 📈 監視・ログ
- **APM**: Sentry integration
- **Metrics**: Prometheus + Grafana
- **Logs**: Structured logging (JSON)

## 🔄 CI/CD
- **Repository**: GitHub
- **CI**: GitHub Actions
- **Deploy**: Docker + Docker Compose
- **Environment**: Development, Staging, Production

## 🚨 PJINIT v1.2 リファクタリング計画（2025-08-14）

### 現状と問題点
PJINIT v1.2の実装には以下の技術的負債が蓄積：
- **service_adapter.py**: 1200行超の巨大ファイル、複雑な条件分岐
- **3層クライアント構造**: Mock → Wrapper → Real の過度な抽象化
- **メソッド同期漏れ**: ラッパークラスと実装クラス間の不整合
- **Windows/WSL混在**: 実行環境の違いによる複雑性

### リファクタリング方針
**ブランチ戦略**: `phase2-clean`から新規ブランチ`pjinit-v2-refactor`を作成

### 実装計画
#### Phase 1: アーキテクチャ再設計（1週目）
- サービスアダプターパターンの簡素化
- 単一責任原則に基づくモジュール分割
- 明確なインターフェース定義

#### Phase 2: コア機能の再実装（2週目）
- Google Sheets統合
- Slack API統合（Bot招待含む）
- GitHub統合

#### Phase 3: Windows環境対応（3週目）
- グローバルPython環境での動作確認
- PowerShell実行スクリプトの整備
- 依存関係管理の明確化

#### Phase 4: テストとドキュメント（4週目）
- 包括的なテストスイート作成
- ユーザーマニュアル作成
- デプロイメントガイド

### 技術的決定事項
- **実行環境**: Windows PowerShell（グローバルPython）
- **エントリーポイント**: main.pyに統一
- **依存関係**: requirements.txtで明示的管理
- **エラーハンドリング**: 詳細なログ出力と復旧可能な設計

### 成功基準
- 全機能のテストカバレッジ80%以上
- service_adapter.pyを300行以下に分割
- Windows環境での安定動作
- 明確なエラーメッセージと復旧手順