# TechBridge - 技術の泉シリーズ統合ワークフロー

![TechBridge Logo](https://img.shields.io/badge/TechBridge-v1.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

TechBridgeは、技術の泉シリーズの編集ワークフローを自動化する統合システムです。[tech]プロジェクト（書籍選定・購入管理）と[techzip]プロジェクト（ReVIEW→Word変換）間の連携を自動化し、編集者の作業効率を大幅に向上させます。

## 🎯 概要

### 解決する課題
- [tech]での書籍購入完了から[techzip]での作業開始まで手動連携が必要
- Slackでの進捗管理が属人的で見える化されていない
- N番号とリポジトリ名の対応確認が手動作業
- 編集フェーズの状態管理が不十分

### 提供する価値
- **自動化**: 購入完了→原稿依頼→変換完了まで自動通知
- **可視化**: リアルタイムな進捗管理とダッシュボード
- **効率化**: Slackコマンドによる手軽なステータス更新
- **統合**: 既存システムの最小改修で完全連携

## 🏗️ システム構成

```
[tech] → Webhook → [Progress Bridge] → Slack API
                           ↓
                    Google Sheets API
                           ↓
              [techzip] ← 作業完了通知
```

### コアコンポーネント

1. **Progress Bridge (FastAPI Backend)**
   - [tech]と[techzip]間の統合レイヤー
   - 状態管理と進捗追跡
   - 外部API連携

2. **Slack Bot Interface** 
   - 編集者向けUI
   - 自動進捗通知
   - スラッシュコマンド

3. **Integration Layer**
   - 既存システム統合
   - 最小限改修で連携実現

## 🚀 クイックスタート

### 前提条件
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### インストール

```bash
# リポジトリクローン
git clone https://github.com/your-org/techbridge.git
cd techbridge

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env ファイルを編集
```

### 環境変数設定

```bash
# .env ファイルの例
DATABASE_URL=postgresql://user:password@localhost:5432/techbridge
REDIS_URL=redis://localhost:6379/0

SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

GOOGLE_SHEETS_ID=your-google-sheets-id
GOOGLE_SERVICE_ACCOUNT_KEY={"type": "service_account", ...}

TECH_WEBHOOK_SECRET=your-tech-webhook-secret
TECHZIP_WEBHOOK_SECRET=your-techzip-webhook-secret
```

### 開発環境起動

```bash
# Docker Composeで起動
docker-compose up -d

# または手動起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

アプリケーションは http://localhost:8000 で起動します。

## 📚 API仕様

### 主要エンドポイント

#### 進捗管理
- `GET /api/v1/progress/{n_number}` - 進捗情報取得
- `POST /api/v1/progress/{n_number}/update` - ステータス更新
- `GET /api/v1/progress/` - 進捗一覧取得

#### Webhook
- `POST /api/v1/webhook/tech/status-change` - [tech]からのステータス変更
- `POST /api/v1/webhook/techzip/completion` - [techzip]からの完了通知

#### Slack連携
- `POST /api/v1/slack/commands/status` - `/status`コマンド
- `POST /api/v1/slack/commands/update` - `/update`コマンド

詳細なAPI仕様は http://localhost:8000/docs で確認できます。

## 🔧 進捗ステータス

| ステータス | 説明 | 絵文字 |
|------------|------|-------|
| `discovered` | 発見済み（[tech]でスクレイピング） | 🔍 |
| `purchased` | 購入完了（[tech]で購入） | 💰 |
| `manuscript_requested` | 原稿依頼（著者へ依頼送信） | ✍️ |
| `manuscript_received` | 原稿受領（著者から原稿受信） | 📄 |
| `first_proof` | 初校（[techzip]変換後） | 📝 |
| `second_proof` | 再校（編集者レビュー後） | ✏️ |
| `completed` | 完成（最終承認済み） | ✅ |

## 💬 Slackコマンド

### `/status N番号`
指定したN番号の進捗状況を表示

```
編集者: /status N02345
Bot: 📊 N02345の進捗
     💰 購入完了 → ✍️ 原稿依頼中 → 📄 原稿受領済み
     更新: 2025-07-29 10:30
```

### `/update N番号 ステータス`
ステータスを手動更新

```
編集者: /update N02345 first_proof
Bot: ✅ N02345を「初校中」に更新しました
```

## 🧪 テスト

```bash
# ユニットテスト実行
pytest

# カバレッジ付きテスト
pytest --cov=app --cov-report=html

# 統合テスト実行
pytest tests/integration/

# E2Eテスト実行
pytest tests/e2e/
```

## 📊 監視・メトリクス

### Prometheus メトリクス
- `techbridge_webhook_requests_total` - Webhook受信数
- `techbridge_status_update_duration_seconds` - ステータス更新処理時間
- `techbridge_slack_notifications_total` - Slack通知送信数

### ログ
構造化ログ（JSON）でSentry、CloudWatchに送信

### ヘルスチェック
- `/health` - 基本ヘルスチェック
- `/health/detailed` - 詳細な依存関係チェック

## 🔐 セキュリティ

- Webhook署名検証
- Google Service Account最小権限
- 環境変数による秘匿情報管理
- TLS 1.3による通信暗号化

## 📖 ドキュメント

- [仕様書](docs/SPECIFICATION.md) - 詳細なシステム仕様
- [実装計画](docs/IMPLEMENTATION_PLAN.md) - 段階的実装計画
- [API仕様](http://localhost:8000/docs) - OpenAPI仕様書

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🙏 謝辞

- [tech]プロジェクト - 技術書典スクレイパー
- [techzip]プロジェクト - 技術の泉シリーズ制作支援ツール
- 技術の泉シリーズ編集チーム

---

**🚀 TechBridge - 技術の泉シリーズを支える統合ワークフロー**