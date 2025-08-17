# PJINIT Refactoring Priorities

## 🚨 Critical Issues (最重要)

### 1. ProjectInitializerWindow の分解 (461行)
**問題**: 単一責任原則の重大な違反
**影響**: 保守性、テスト可能性、拡張性の阻害
**分解戦略**:
- UIコンポーネント作成 → UIBuilder クラス
- イベント処理 → EventHandler クラス  
- 設定管理 → SettingsManager クラス
- 初期化処理 → InitializationController クラス

### 2. service_adapter.py の機能分離 (972行+)
**問題**: 過度な抽象化、複雑な依存関係
**影響**: デバッグ困難、テスト複雑化
**分離戦略**:
- GoogleSheetsAdapter
- SlackAdapter  
- GitHubAdapter
- ServiceRegistry (サービス管理)

## 🔶 High Priority Issues

### 3. main.py の全体的リファクタリング (865行)
**問題**: モノリシック構造
**戦略**: 
- アプリケーション起動ロジックの分離
- 設定読み込みの独立化
- CLI/GUI モードの明確な分離

### 4. 3層アーキテクチャの簡素化
**問題**: 過度な抽象化レイヤー
**戦略**:
- Mock/Real の直接的な切り替え機構
- 不要な中間層の除去
- インターフェース設計の見直し

## 🔸 Medium Priority Issues

### 5. エラーハンドリングの統一化
- 例外処理の標準化
- ログ出力の一元化
- ユーザーフィードバックの改善

### 6. 設定管理の改善
- 設定ファイルの構造化
- 環境別設定の対応
- 設定検証ロジックの追加

## リファクタリング実行順序
1. ProjectInitializerWindow の段階的分解
2. ServiceAdapter の機能別分離
3. main.py の構造改善
4. アーキテクチャ全体の最適化