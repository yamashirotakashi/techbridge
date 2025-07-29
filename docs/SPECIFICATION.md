# TechBridge システム仕様書
バージョン: 1.0  
作成日: 2025-07-29

## 1. システム概要

### 1.1 目的
技術の泉シリーズの編集ワークフローにおいて、[tech]プロジェクト（書籍選定・購入管理）と[techzip]プロジェクト（ReVIEW→Word変換）間の連携を自動化し、編集者の作業効率を向上させる。

### 1.2 背景
現在の課題：
- [tech]での書籍購入完了から[techzip]での作業開始まで手動連携
- Slackでの進捗管理が属人的
- N番号とリポジトリ名の対応確認が手動
- 編集フェーズの状態管理が不十分

### 1.3 解決アプローチ
Progress Bridge（統合API）とSlack Bot Interface により、イベント駆動の自動ワークフローを実現する。

## 2. システム要件

### 2.1 機能要件

#### 2.1.1 コア機能
- **F001**: [tech]の購入完了イベントを自動検知
- **F002**: N番号によるGoogle Sheets連携（リポジトリ名取得）
- **F003**: Slackチャンネル自動振り分け（チャンネル名=リポジトリ名）
- **F004**: 編集フェーズの状態管理（原稿依頼→受領→校正→完成）
- **F005**: [techzip]完了イベントとの統合

#### 2.1.2 Slack Interface
- **F101**: 自動進捗通知（購入完了、原稿依頼等）
- **F102**: `/status N番号` コマンド（進捗確認）
- **F103**: `/update N番号 ステータス` コマンド（手動更新）
- **F104**: 編集者への作業依頼通知
- **F105**: 著者への進捗共有

#### 2.1.3 管理機能
- **F201**: 全体進捗ダッシュボード
- **F202**: 遅延アラート機能
- **F203**: 統計レポート生成

### 2.2 非機能要件

#### 2.2.1 性能要件
- **NF001**: Webhook応答時間 < 3秒
- **NF002**: Slack通知遅延 < 10秒
- **NF003**: 同時処理 100リクエスト/秒

#### 2.2.2 可用性要件
- **NF101**: システム稼働率 99.5%以上
- **NF102**: 障害時自動復旧機能
- **NF103**: エラー発生時のSlack通知

#### 2.2.3 セキュリティ要件
- **NF201**: Webhook署名検証
- **NF202**: Slack token secure storage
- **NF203**: Google Service Account key保護

## 3. システム設計

### 3.1 全体アーキテクチャ

```mermaid
graph TD
    A[tech Project] -->|Webhook| B[Progress Bridge]
    C[techzip Project] -->|Completion Event| B
    B -->|Google Sheets API| D[Spreadsheet]
    B -->|Slack Web API| E[Slack Workspace]
    B -->|PostgreSQL| F[(Database)]
    B -->|Redis| G[(Cache)]
    
    E --> H[Author Channels]
    E --> I[Editor Channels]
    E --> J[Management Channel]
```

### 3.2 Progress Bridge API設計

#### 3.2.1 エンドポイント一覧

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | `/webhook/tech/status-change` | [tech]からのステータス変更 |
| POST | `/webhook/techzip/completion` | [techzip]からの完了通知 |
| GET | `/api/progress/{n_number}` | 進捗状況取得 |
| POST | `/api/progress/{n_number}/update` | ステータス手動更新 |
| GET | `/api/dashboard/overview` | 全体進捗概要 |
| POST | `/slack/commands/status` | Slackステータスコマンド |
| POST | `/slack/commands/update` | Slack更新コマンド |

#### 3.2.2 データスキーマ

```sql
-- 進捗管理テーブル
CREATE TABLE workflow_items (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) UNIQUE NOT NULL,
    book_id VARCHAR(100),  -- [tech] book_id
    repository_name VARCHAR(100),
    slack_channel VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    assigned_editor VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- ステータス履歴テーブル  
CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) REFERENCES workflow_items(n_number),
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW(),
    comment TEXT
);

-- 通知履歴テーブル
CREATE TABLE notification_history (
    id SERIAL PRIMARY KEY,
    n_number VARCHAR(10) REFERENCES workflow_items(n_number),
    channel VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN DEFAULT false
);
```

### 3.3 外部システム連携

#### 3.3.1 [tech]プロジェクト連携

**必要な改修（最小限）:**
```python
# [tech] 側の追加実装
class WorkflowEventExtended(WorkflowEvent):
    n_number: Optional[str] = None  # 管理画面で入力
    
def send_webhook_on_purchase_complete(book_id: str, n_number: str):
    payload = {
        "book_id": book_id,
        "old_status": "wishlisted",
        "new_status": "purchased", 
        "n_number": n_number,
        "timestamp": datetime.now().isoformat()
    }
    requests.post(TECHBRIDGE_WEBHOOK_URL, json=payload)
```

#### 3.3.2 Google Sheets連携

**活用する既存機能:**
- [techzip]の`GoogleSheetClient.search_n_code()`を参考実装
- N番号（A列）→ リポジトリ名（C列）のマッピング
- エラーハンドリングとリトライ機能

#### 3.3.3 Slack API連携

**使用するAPI:**
- `chat.postMessage`: 通知送信
- `conversations.list`: チャンネル一覧取得
- `app_mentions`: メンション監視
- `slash_commands`: コマンド処理

## 4. 状態管理設計

### 4.1 状態遷移図

```mermaid
stateDiagram-v2
    [*] --> DISCOVERED: [tech] scraping
    DISCOVERED --> PURCHASED: [tech] purchase
    PURCHASED --> MANUSCRIPT_REQUESTED: auto notification
    MANUSCRIPT_REQUESTED --> MANUSCRIPT_RECEIVED: manual update
    MANUSCRIPT_RECEIVED --> FIRST_PROOF: [techzip] conversion
    FIRST_PROOF --> SECOND_PROOF: editor review
    SECOND_PROOF --> COMPLETED: final approval
    COMPLETED --> [*]
```

### 4.2 通知ルール

| 状態遷移 | 通知先 | メッセージ |
|----------|--------|------------|
| DISCOVERED → PURCHASED | 管理チャンネル | "📚 N{n_number}の購入が完了しました" |
| PURCHASED → MANUSCRIPT_REQUESTED | 著者チャンネル | "✍️ 原稿の準備をお願いします（締切: {deadline}）" |
| MANUSCRIPT_RECEIVED → FIRST_PROOF | 編集者チャンネル | "📝 N{n_number}の初校をお願いします" |
| SECOND_PROOF → COMPLETED | 全チャンネル | "🎉 N{n_number}が完成しました！" |

## 5. 実装計画

### 5.1 Phase 1: MVP (4週間)

#### Week 1: 基盤構築
- [ ] FastAPI プロジェクト初期化
- [ ] Docker開発環境構築
- [ ] PostgreSQL スキーマ作成
- [ ] 基本的なCRUD API実装

#### Week 2: Slack統合
- [ ] Slack Bot アプリ作成
- [ ] Webhook受信機能実装
- [ ] 基本的な通知機能実装
- [ ] スラッシュコマンド実装

#### Week 3: 外部システム統合
- [ ] Google Sheets API統合
- [ ] [tech] Webhook受信実装
- [ ] 状態管理ロジック実装
- [ ] チャンネル自動振り分け機能

#### Week 4: 完成とテスト
- [ ] [techzip] 完了通知統合
- [ ] エンドツーエンドテスト
- [ ] エラーハンドリング強化
- [ ] デプロイメント準備

### 5.2 Phase 2: 機能拡張 (2週間)

#### Week 5: 管理機能
- [ ] ダッシュボード画面実装
- [ ] 統計レポート機能
- [ ] 遅延アラート機能

#### Week 6: 運用改善
- [ ] ログ・監視強化
- [ ] パフォーマンス最適化
- [ ] ドキュメント整備

## 6. テスト戦略

### 6.1 テスト分類

#### 6.1.1 Unit Tests
- API エンドポイント単体テスト
- ビジネスロジック単体テスト
- 外部API連携のモックテスト

#### 6.1.2 Integration Tests  
- データベース連携テスト
- Redis キャッシュテスト
- 外部API実連携テスト

#### 6.1.3 E2E Tests
- Webhook → Slack通知の全フロー
- スラッシュコマンドの動作確認
- 複数N番号の並行処理テスト

### 6.2 テスト環境

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://test:test@db:5432/testdb
      - SLACK_BOT_TOKEN=xoxb-test-token
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      
  redis:
    image: redis:7-alpine
```

## 7. 運用・保守

### 7.1 監視項目
- API応答時間
- Webhook処理成功率
- Slack通知送信成功率
- データベース接続状況
- Redis接続状況

### 7.2 ログ設計
```python
# 構造化ログ例
{
    "timestamp": "2025-07-29T10:00:00Z",
    "level": "INFO",
    "message": "Status updated successfully",
    "n_number": "N02345",
    "old_status": "manuscript_requested", 
    "new_status": "manuscript_received",
    "user": "editor@example.com",
    "correlation_id": "req-123456"
}
```

### 7.3 エラー処理
- Webhook処理失敗時のリトライ機能
- Slack API エラー時のフォールバック
- Google Sheets API制限対応
- データベース接続エラー時の復旧

## 8. セキュリティ考慮事項

### 8.1 認証・認可
- Slack Webhook署名検証
- Google Service Account最小権限設定
- 環境変数による秘匿情報管理

### 8.2 データ保護
- データベース暗号化（TDE）
- 通信経路暗号化（TLS 1.3）
- ログの個人情報マスキング

## 9. パフォーマンス要件

### 9.1 応答時間
- Webhook処理: 3秒以内
- Slack通知: 10秒以内  
- ダッシュボード表示: 5秒以内

### 9.2 スケーラビリティ
- 同時処理: 100リクエスト/秒
- データ容量: 10,000件のN番号
- 保存期間: 2年間

## 10. 移行計画

### 10.1 段階的導入
1. **Phase 0**: 開発環境での検証
2. **Phase 1**: 1つのN番号での実証実験
3. **Phase 2**: 5つのN番号での小規模運用
4. **Phase 3**: 全N番号での本格運用

### 10.2 ロールバック計画
- データベースバックアップ
- 旧手動フローへの即時復帰手順
- 既存システムへの影響最小化

---

**承認者**: プロジェクトマネージャー  
**レビュー**: 技術リード、編集責任者  
**次回レビュー**: Phase 1完了時