# Phase 4: Service Layer分離実装計画 - 2025-08-17

## 🎯 実装概要
**目的**: service_adapter.py（972行）のService Layer抽象化
**戦略**: GitHub/Slack/Sheets各サービスの分離実装
**手法**: 既確立のStrangler Pattern + 依存性注入継続

## 📋 実装ステップ

### Step 1: GitHubService分離（実装中）
**対象**: GitHub関連メソッド（1メソッド）
- `create_github_repo()` → GitHubService.create_github_repo()

**実装方針**:
1. clients/services/github_service.py - GitHubServiceクラス実装
2. 必要なimport文とパス設定の継承
3. エラーハンドリング・リトライロジック完全保持
4. _run_in_executor()の内部実装

### Step 2: SlackService分離 
**対象**: Slack関連メソッド（8メソッド）
- `create_slack_channel()`
- `invite_to_slack_channel()`
- `find_user_by_email()`
- `find_workflow_channel()`
- `post_workflow_guidance()`
- `invite_github_app_with_bot_token()`
- `invite_github_app_with_alternative_bot()`
- `invite_user_by_email()`

### Step 3: SheetsService分離
**対象**: Google Sheets関連メソッド（4メソッド）
- `get_project_info()`
- `get_task_info()`
- `create_task_record()`
- `sync_project_tasks()`
- `sync_purchase_list_urls()`

### Step 4: ServiceUtils共通機能
**対象**: 共通ユーティリティ
- `_run_in_executor()` → ServiceUtils.run_in_executor()
- 共通エラーハンドリング
- ログ処理

### Step 5: ServiceAdapter薄型化
**対象**: service_adapter.py自体の委譲パターン化
- 各サービスのインスタンス管理
- メソッドは各サービスへの委譲のみ
- 初期化ロジックの保持

### Step 6: __init__.py更新
**対象**: 各サービスクラスのエクスポート追加

## 🛡️ 制約条件確認
- ✅ 外部APIインターフェース完全維持
- ✅ 非同期処理・スレッド安全性維持  
- ✅ 既存のテストが全て通過すること
- ✅ エラーハンドリング・リトライロジック完全保持

## 📊 期待効果
- service_adapter.py: 972行 → 300行（69%削減）
- 真のMVCパターン完成
- Service Layer抽象化実現
- 保守性・テスタビリティ大幅向上

## 🚀 次回継続ポイント
**実装中**: GitHubService分離（Step 1）
**完了後**: SlackService分離（Step 2）