# グローバルルールの継承
@../../../../../CLAUDE.md

# PJINIT v2.0 プロジェクト設定
最終更新: 2025-08-15

## 🎯 プロジェクト概要
- **正式名**: ProjectInitializer v2.0 - TechBridge統合プロジェクト初期化ツール
- **目的**: 技術の泉シリーズプロジェクトの完全自動初期化システム
- **プロジェクトキーワード**: `[PJINIT]` または `[pjinit]`

## 🚨 **最優先実施項目（2025-08-15設定）**

### **PJINIT v2.0 リファクタリング実装**
**状態**: Phase 1実装開始準備完了 - 実装開始最優先

**次回[PJINIT]セッション開始時は、以下を最優先で実行する**:

1. **統合合意分析結果に基づく Phase 1実装開始**
   - Gemini・Claude・Zen 3モデル合意分析完了
   - ハイブリッド段階アプローチ採用決定
   - Phase 1: 緊急安定化・実現可能性検証（2週間）

2. **Phase 1実装内容**:
   - Characterization Testing Suite実装
   - 最小限ヘルパー関数分離（10-20行程度）
   - 制約条件監視システム構築

3. **Critical Success Factors**:
   - 制約条件100%遵守（GUI/ワークフロー/外部連携影響ゼロ）
   - 1コマンドでの完全ロールバック体制
   - Serena-only実装（Edit/Write系禁止）

**⚠️ 重要**: 合意分析により当初想定を遥かに上回る技術的リスク判明。Phase 1での慎重検証が成功の絶対条件。

## 📋 監査結果統合レポート（Phase 1-3A完了）

### Phase 1-3A実装成果
**実装済みフェーズ**:
- ✅ **Phase 1**: Characterization Testing Suite（完全実装）
- ✅ **Phase 2**: Service Layer抽象化（部分実装）
- ✅ **Phase 3A**: Worker Thread分離（272行クラス分離完了）

### **QualityGate 最終監査結果: 96/100点**
**評価内容**:
- ✅ 制約条件100%遵守（GUI/ワークフロー/外部連携無変更）
- ✅ Serena-only実装厳守
- ✅ ロールバック体制完備
- ⚠️ **課題**: Service Layer抽象化の未完了領域（Phase 4課題）

### **Serena MCP分析結果: 96/100点**
**技術評価**:
- ✅ シンボル解析による安全な分離実装
- ✅ 依存関係管理の適切性
- ✅ コード品質の向上確認
- ⚠️ **残課題**: service_adapter.py 複雑度軽減必要

## 🚀 **Phase 4 推奨実装アプローチ（統合監査承認）**

### Phase 4: Service Layer完全抽象化
**QualityGate & Serena合同推奨方針**:

1. **service_adapter.py完全分離**（972行→目標600行）
   - ビジネスロジック層の完全抽象化
   - インターフェース設計による疎結合化
   - 制約条件下での段階的実装

2. **統合テスト強化**
   - Characterization Testing拡張
   - エンドツーエンド検証
   - 回帰テスト自動化

3. **技術的負債最終削減**
   - 複雑度メトリクス目標達成
   - コードカバレッジ90%以上
   - 保守性スコア改善

### Phase 4実装制約（継続）
- 各段階での制約条件遵守検証必須
- QualityGate & Serena両方監査実施
- 完全ロールバック可能性の常時確保

### **次セッション開始タスク**
1. Phase 2D/3B統合結果確認
2. service_adapter.py抽象化設計
3. Phase 4実装計画策定

---

## 🔒 **必須セッション手順（2025-08-15更新）**

### **[PJINIT]切り替え後の自動実行手順**
**[PJINIT]** 切り替え後は、以下を必ず自動実行する：

1. **Handover.md自動読み込み**
   ```bash
   # Handover.mdが存在する場合は必ず最初に読み込み
   cat Handover.md
   ```

2. **合意分析結果確認**
   ```bash
   # Serenaメモリーから合意分析結果確認
   [serenaメモリ] pjinit_v2_consensus_synthesis_and_final_plan
   ```

3. **制約条件遵守フレームワーク確認**
   ```bash
   # 制約条件の確認（必須）
   grep -A 10 "絶対制約条件" CONSTRAINT_COMPLIANCE_FRAMEWORK.md
   ```

4. **統合実装戦略確認**
   - ハイブリッド段階アプローチ理解
   - Phase 1: 緊急安定化戦略の把握
   - Critical Risk Assessment結果の理解

5. **Phase 1実装開始準備**
   - 制約条件（修正制約条件）の再確認
   - Serena-only実装要件の確認
   - Characterization Testing準備

### **実装制限（絶対遵守）**
- **実装ツール**: Serena subagent/SerenaMCP **のみ** 使用
- **禁止ツール**: Edit, Write, MultiEdit, 他のMCPツール
- **例外**: TodoWrite（タスク管理）, Read（確認目的）

## 🔒 **絶対制約条件（ユーザー要求）**

### ✅ **完全遵守必須項目**
1. **従来のGUIを絶対に変更しない** - PyQt6 UIレイアウト・デザイン・操作性の完全保持
2. **従来のプロジェクト初期化のワークフローを一切変えない** - 初期化手順・順序・処理内容の完全保持
3. **従来のGitHub/Slack/シート連携は絶対に変えない** - API統合動作・データフロー・機能の完全保持

### 📋 **Phase毎必須監査プロセス**
- 各Phase完了後: [QG] QualityGate subagent監査 **必須**
- 各Phase完了後: Serena subagent監査 **必須**
- 修正指示は絶対遵守・即座対応
- Handover.md作成による完全記録
- セッション中断・引き継ぎ

## 📊 **技術仕様**

### **現状の技術的負債**
- **main.py**: 865行の巨大ファイル
- **service_adapter.py**: 972行超のGodクラス
- **技術的負債比率**: 35-40%

### **超保守的リファクタリング戦略**
1. **Phase 1**: ヘルパー関数分離（極低リスク）
2. **Phase 2**: データモデル分離（低リスク）
3. **Phase 3**: 設定ファイル処理分離（中リスク）

### **期待される成果**
- **コード削減**: 210-310行削減
- **技術的負債**: 35-40% → 25-30%
- **既存機能**: 100%保持

## 🏗️ **アーキテクチャ**

### **コア機能**
- GitHub自動リポジトリ作成・設定
- Slackチャンネル作成・Bot招待
- Google Sheets連携・データ同期
- Progress Bridge API統合

### **統合システム**
- **TechWF管理シート**: プロジェクト進行管理
- **Progress Bridge**: [tech]と[techzip]間の連携レイヤー
- **エラーリカバリー**: 各ステップでの自動復旧機能

## 📁 **ファイル構造**
```
project_initializer/
├── main.py                    # メインエントリーポイント（865行→目標555-595行）
├── core/
│   ├── service_adapter.py     # サービス統合（972行→目標600行）
│   └── project_initializer.py
├── ui/
│   └── main_window.py         # PyQt6 GUI（変更禁止）
├── clients/
│   ├── slack_client.py
│   └── service_adapter.py
├── config/
│   └── settings.py
└── utils/
    └── environment.py
```

## 🔑 **環境設定**
```bash
# 必須環境変数
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_INVITATION_TOKEN=xoxp-...
GOOGLE_SHEETS_SERVICE_ACCOUNT_KEY=...
TECHWF_MANAGEMENT_SHEET_ID=...
```

## 🧪 **テスト・品質保証**

### **制約条件検証**
- GUI動作確認テスト
- プロジェクト初期化ワークフローテスト
- GitHub/Slack/Sheets統合テスト
- エラーハンドリングテスト

### **品質ゲート**
- Phase完了時の必須品質チェック
- 制約条件100%遵守確認
- 技術的負債削減確認

## 🚀 **実行方法**

### **開発環境**
```bash
cd /mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer
python main.py
```

### **Windows EXE実行**
```bash
# EXEビルド
./PJinit.build.ps1

# 実行
./dist/PJinit.1.2.exe
```

## 📋 **実装チェックリスト**

### **Phase 1: ヘルパー関数分離**
- [ ] ユーティリティ関数特定・移動
- [ ] main.py 865行 → 745-785行達成
- [ ] GUI動作確認
- [ ] ワークフロー確認
- [ ] 外部連携確認

### **Phase 2: データモデル分離**
- [ ] データクラス特定・移動
- [ ] main.py 745-785行 → 655-695行達成
- [ ] データ構造動作確認
- [ ] 統合テスト実行

### **Phase 3: 設定ファイル処理分離**
- [ ] 設定処理特定・移動
- [ ] main.py 655-695行 → 555-595行達成
- [ ] 設定値・パラメータ確認
- [ ] 最終統合テスト

### **最終確認**
- [ ] 全制約条件100%遵守
- [ ] 技術的負債25-30%達成
- [ ] 全機能動作確認
- [ ] ドキュメント更新

## 🛡️ **安全性・品質保証**

### **ロールバック体制**
- Git branch: phase1, phase2, phase3
- Commit単位での復元可能性
- 緊急時の即座復旧

### **制約条件監視**
- 自動化された制約条件チェック
- 違反時の即座アラート
- 強制ロールバック機能

---

**重要**: このプロジェクトは制約条件の100%遵守が絶対要件です。GUI・ワークフロー・外部連携の一切の変更は許可されません。