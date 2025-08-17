# PJINIT Project Overview

## プロジェクト概要
TechBridge プロジェクト初期化ツール（PJINIT）- 技術書典プロジェクトの統合管理システム

## 目的
- 技術書典プロジェクトの初期化自動化
- Google Sheets、Slack、GitHub の統合管理
- プロジェクト情報の一元化とワークフロー構築

## 技術スタック
- **GUI Framework**: PyQt6
- **言語**: Python 3.x
- **統合サービス**: 
  - Google Sheets API (プロジェクト管理)
  - Slack API (チャンネル作成・通知)
  - GitHub API (リポジトリ作成・管理)

## アーキテクチャパターン
**3層クライアント構造**:
1. **Mock Layer** - テスト・開発用モックサービス
2. **Wrapper Layer** - サービスアダプターによる統合
3. **Real Layer** - 実際のAPI実装

## 主要コンポーネント
- `main.py` (865行) - メインGUIアプリケーション
- `clients/service_adapter.py` (972行+) - サービス統合層
- `core/project_initializer.py` - プロジェクト初期化ロジック
- `application/app_controller.py` - アプリケーション制御

## 重要な品質課題
1. **大規模ファイル問題**: main.py (865行)、service_adapter.py (972行+)
2. **単一責任原則違反**: ProjectInitializerWindow クラス (461行)
3. **複雑なサービス依存関係**: 3層構造の過度な抽象化