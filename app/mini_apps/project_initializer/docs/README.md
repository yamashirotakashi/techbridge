# PJINIT (Project Initializer) ドキュメント

**バージョン**: 1.1  
**最終更新**: 2025-08-14  
**統合状態**: TechBridge統合完了・復旧済み

## 📋 プロジェクト概要

PJINITは技術書執筆プロジェクトの初期化を自動化するPythonアプリケーションです。TechBridge統合ワークフロー内で動作し、GitHub・Slack・Google Sheetsとの連携によりシームレスなプロジェクト立ち上げを実現します。

### 主要機能
- 📁 **プロジェクトディレクトリ自動生成**
- 🔗 **GitHub リポジトリ自動作成・設定**
- 📊 **Google Sheets プロジェクト管理表自動更新**  
- 💬 **Slack チャンネル作成・通知**
- 🏗️ **TechBridge統合ワークフロー連携**

---

## 📁 ドキュメント構成

このディレクトリには以下のドキュメントが含まれています：

### 📖 基本ドキュメント
- **[README.md](README.md)** - このファイル（プロジェクト概要）
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - システムアーキテクチャと設計思想
- **[API_REFERENCE.md](API_REFERENCE.md)** - API仕様・関数リファレンス
- **[USER_GUIDE.md](USER_GUIDE.md)** - ユーザー操作ガイド

### 🔧 技術ドキュメント  
- **[INSTALLATION.md](INSTALLATION.md)** - インストール・環境構築手順
- **[CONFIGURATION.md](CONFIGURATION.md)** - 設定ファイル・環境変数
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - 開発環境・コントリビューションガイド
- **[TESTING.md](TESTING.md)** - テスト戦略・テスト実行方法

### 📊 統合・運用ドキュメント
- **[TECHBRIDGE_INTEGRATION.md](TECHBRIDGE_INTEGRATION.md)** - TechBridge統合仕様
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - トラブルシューティングガイド  
- **[CHANGELOG.md](CHANGELOG.md)** - 変更履歴・リリースノート
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - デプロイ・配布手順

### 🚨 重要通知
- **[IMPACT_ASSESSMENT.md](IMPACT_ASSESSMENT.md)** - TechBridge実装影響評価報告書

---

## 🚀 クイックスタート

### 基本的な使用方法
```bash
# TechBridgeワークフロー内での起動
cd /mnt/c/Users/tky99/dev/techbridge
python techwf/src/gui/main.py
# → "PJINIT起動" ボタンをクリック

# 直接起動（スタンドアロン）
cd /mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer
python main.py
```

### EXE実行
```bash
# Windows EXE起動
./dist/PJinit.1.1.exe

# WSL環境からの起動
/mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer/dist/PJinit.1.1.exe
```

---

## 🏗️ システム統合

### TechBridge統合アーキテクチャ
```
TechBridge統合ワークフロー
├── techwf/src/gui/event_handler_service.py
│   └── handle_launch_pjinit()  # PJINIT起動処理
├── config/paths_config.yaml
│   └── external_tools.pjinit   # パス設定外部化
└── app/mini_apps/project_initializer/
    ├── dist/PJinit.1.1.exe     # 実行ファイル
    └── main.py                 # メインアプリケーション
```

### 統合の利点
- **一気通貫ワークフロー**: [tech]→[Progress Bridge]→[PJINIT]→[techzip]
- **設定一元管理**: TechBridge設定システムによる統合管理
- **状態同期**: プロジェクト進捗の自動追跡・更新

---

## ⚠️ 重要な注意事項

### TechBridge実装影響について
2025年8月14日のTechBridgeハードコード外部化実装により、PJINITに一時的な機能損傷が発生しました：

- **影響期間**: Phase 1-5実装期間中
- **症状**: 起動パス解決の失敗、統合ワークフロー断絶
- **対応状況**: 復旧作業完了（2025-08-14時点）
- **詳細情報**: [IMPACT_ASSESSMENT.md](IMPACT_ASSESSMENT.md) を参照

### 復旧対応
- ✅ **パス設定外部化**: ハードコードパス→YAML設定への移行完了
- ✅ **統合テスト**: TechBridge→PJINIT連携の動作確認完了
- ✅ **エラーハンドリング**: 起動失敗時のフォールバック処理実装
- ✅ **ドキュメント更新**: 全ドキュメントの最新化完了

---

## 🔗 関連プロジェクト

### TechBridge エコシステム
- **[TechBridge Core](/mnt/c/Users/tky99/dev/techbridge/)** - 統合ワークフローシステム
- **[TECHZIP](/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool/)** - 技術書制作支援
- **[TechBookFest Scraper](/mnt/c/Users/tky99/dev/techbookfest_scraper/)** - 技術書典データ取得

### 統合フロー
```
[techbookfest_scraper] → Webhook → [TechBridge] → [PJINIT] → [TECHZIP]
```

---

## 📞 サポート・コントリビューション

### 問題報告
- GitHub Issues（該当する場合）
- 統合問題は [TechBridge Issues](link-to-techbridge-issues)

### 開発参加
詳細は [DEVELOPMENT.md](DEVELOPMENT.md) を参照してください。

### ドキュメント更新
ドキュメントの追加・修正は各MDファイルを直接編集してください。

---

**最終検証日**: 2025-08-14  
**検証者**: AI Assistant (Claude Code) + TechBridge統合テスト  
**次回更新予定**: TechBridge Phase 6実装時