# PJINIT Code Structure Analysis

## ディレクトリ構造
```
project_initializer/
├── main.py (865行) - メインアプリケーション
├── clients/
│   ├── service_adapter.py (972行+) - サービス統合
│   ├── slack_client.py - Slack実装
│   └── slack_client_real.py - Real Slack実装
├── core/
│   └── project_initializer.py - 初期化ロジック
├── application/
│   └── app_controller.py - アプリ制御
├── config/ - 設定ファイル
├── data/ - データファイル
├── ui/ - UI関連
└── utils/ - ユーティリティ
```

## 主要クラス分析

### ProjectInitializerWindow (main.py: 404-865行)
- **サイズ**: 461行の巨大クラス
- **責務**: GUI、イベント処理、設定管理、初期化実行
- **メソッド数**: 14個
- **変数数**: 20個
- **問題**: 単一責任原則の重大な違反

### ServiceAdapter (service_adapter.py: 701-972行)
- **サイズ**: 271行
- **責務**: 全サービスの統合・調整
- **問題**: 過度な抽象化、複雑な依存関係

### サービス実装クラス
- MockGoogleSheetsService (46-73行)
- RealGoogleSheetsService (314-632行, 318行) 
- MockSlackService (109-122行)
- RealSlackService (124-162行)

## コード品質問題
1. **ファイルサイズ**: main.py, service_adapter.py が600行超
2. **クラスサイズ**: ProjectInitializerWindow が461行
3. **複雑な継承**: Mock→Real の複雑な関係
4. **密結合**: GUI とビジネスロジックの混在