# PJINIT v2.0 制約条件完全遵守フレームワーク

最終更新: 2025-08-15
監査基盤: Serena厳格監査結果

## 🔒 **制約条件定義（ユーザー絶対要求）**

### 1. **従来のGUIを絶対に変更しない**
```python
# 変更禁止項目
- UIレイアウト・デザイン
- ボタン・フィールドの配置
- プログレス表示の内容・タイミング
- エラーメッセージの表示方法
- 画面遷移・ダイアログ表示
- ユーザー操作フロー
```

### 2. **従来のプロジェクト初期化のワークフローを一切変えない**
```python
# 変更禁止項目
- 初期化手順の順序
- 各ステップの処理内容
- エラー発生時の復旧手順
- 設定値・パラメータの形式
- 完了通知・メッセージ
- 中間状態の保存・復元
```

### 3. **従来のGitHub/Slack/シート連携は絶対に変えない**
```python
# 変更禁止項目
- API呼び出しのタイミング
- 認証フロー・ユーザー体験
- データの読み書き・同期処理
- エラーハンドリング・復旧処理
- Bot機能・通知動作
- データ形式・構造
```

---

## 🚨 **Serena監査による違反リスク検出**

### **高危険度違反リスク**
1. **ProjectInitializerWindow分解** → GUI動作変更確実
2. **Service Adapter分離** → 外部連携動作変更可能性
3. **ワークフロー順序変更** → 初期化手順変更リスク

### **変更禁止領域 (RED ZONE)**
```python
# 絶対変更禁止
class ProjectInitializerWindow:
    def setup_ui(self)           # UIレイアウト
    def setup_connections(self)  # シグナル/スロット接続
    def update_progress(self)    # プログレス表示
    def show_error(self)         # エラー表示
    def create_project(self)     # メインワークフロー順序
    
    # イベントハンドラー（UI操作性保持）
    def on_create_clicked(self)
    def on_settings_changed(self)
    def on_cancel_clicked(self)
    
    # 外部連携メソッド（統合動作保持）
    def setup_github_integration(self)
    def setup_slack_integration(self)
    def setup_sheets_integration(self)
```

---

## ✅ **制約条件遵守確認メカニズム**

### **段階別遵守チェック**

#### **Phase実装前チェック**
```python
class PreImplementationCheck:
    """実装前の制約条件確認"""
    
    def verify_change_scope(self, changed_files):
        """変更範囲が許可領域内かチェック"""
        forbidden_patterns = [
            "ProjectInitializerWindow.*setup_ui",
            "ProjectInitializerWindow.*setup_connections", 
            "ProjectInitializerWindow.*create_project",
            "setup_github_integration",
            "setup_slack_integration",
            "setup_sheets_integration"
        ]
        
        for file_path in changed_files:
            for pattern in forbidden_patterns:
                if self.contains_pattern(file_path, pattern):
                    raise ConstraintViolationError(f"Forbidden change: {pattern}")
    
    def verify_interface_preservation(self, old_interface, new_interface):
        """インターフェース保持確認"""
        assert old_interface == new_interface, "Interface must remain identical"
```

#### **Phase実装後チェック**
```python
class PostImplementationCheck:
    """実装後の制約条件確認"""
    
    def verify_gui_unchanged(self):
        """GUI変更なし確認"""
        # 1. UIレイアウト確認
        assert self.check_ui_layout() == self.baseline_ui_layout
        
        # 2. ボタン・フィールド動作確認
        assert self.check_button_behavior() == self.baseline_button_behavior
        
        # 3. プログレス表示確認
        assert self.check_progress_display() == self.baseline_progress_display
        
        # 4. エラーメッセージ確認
        assert self.check_error_messages() == self.baseline_error_messages
    
    def verify_workflow_unchanged(self):
        """ワークフロー変更なし確認"""
        # 1. 初期化手順順序確認
        actual_sequence = self.capture_initialization_sequence()
        assert actual_sequence == self.baseline_sequence
        
        # 2. 各ステップ処理内容確認
        for step in self.initialization_steps:
            assert self.check_step_behavior(step) == self.baseline_step_behavior[step]
        
        # 3. エラー復旧確認
        assert self.check_error_recovery() == self.baseline_error_recovery
    
    def verify_integrations_unchanged(self):
        """外部連携変更なし確認"""
        # 1. GitHub統合確認
        assert self.check_github_integration() == self.baseline_github
        
        # 2. Slack統合確認
        assert self.check_slack_integration() == self.baseline_slack
        
        # 3. Sheets統合確認
        assert self.check_sheets_integration() == self.baseline_sheets
```

### **自動化検証スクリプト**
```python
# constraint_verification.py
def run_full_constraint_check():
    """全制約条件の自動検証"""
    
    print("=== CONSTRAINT COMPLIANCE VERIFICATION ===")
    
    # 1. GUI遵守確認
    gui_check = GUIComplianceChecker()
    gui_result = gui_check.verify_all()
    print(f"GUI Compliance: {'✅ PASS' if gui_result else '❌ FAIL'}")
    
    # 2. ワークフロー遵守確認
    workflow_check = WorkflowComplianceChecker()
    workflow_result = workflow_check.verify_all()
    print(f"Workflow Compliance: {'✅ PASS' if workflow_result else '❌ FAIL'}")
    
    # 3. 外部連携遵守確認
    integration_check = IntegrationComplianceChecker()
    integration_result = integration_check.verify_all()
    print(f"Integration Compliance: {'✅ PASS' if integration_result else '❌ FAIL'}")
    
    # 総合判定
    overall_result = gui_result and workflow_result and integration_result
    print(f"Overall Compliance: {'✅ PASS' if overall_result else '❌ FAIL'}")
    
    if not overall_result:
        raise ConstraintViolationError("制約条件違反が検出されました")
    
    return overall_result
```

---

## 🧪 **実装段階での制約条件保証**

### **Phase 1: ヘルパー関数分離 制約条件保証**

#### **実装前確認**
```bash
# 1. 変更対象確認
grep -n "def validate_project_settings\|def format_log_message\|DEFAULT_SETTINGS" main.py
# → ヘルパー関数のみが対象であることを確認

# 2. GUI関連コード非接触確認
grep -n "setup_ui\|setup_connections\|update_progress\|show_error" main.py
# → これらが変更されていないことを確認
```

#### **実装中確認**
```python
# 移動前のインターフェース記録
original_validate = validate_project_settings
original_format = format_log_message
original_defaults = DEFAULT_SETTINGS

# 移動後のインターフェース確認
from utils.validators import validate_project_settings
from utils.logger import format_log_message  
from utils.constants import DEFAULT_SETTINGS

# インターフェース同一性確認
assert validate_project_settings.__name__ == original_validate.__name__
assert format_log_message.__name__ == original_format.__name__
assert DEFAULT_SETTINGS == original_defaults
```

#### **実装後検証**
```bash
# 1. GUI動作確認
python main.py
# → UI表示・操作・プログレス表示が完全同一

# 2. ワークフロー確認
python test_project_initialization.py
# → 初期化手順が完全同一

# 3. 外部連携確認
python test_full_integration.py
# → GitHub/Slack/Sheets統合が完全同一
```

### **Phase 2: データモデル分離 制約条件保証**

#### **実装前確認**
```bash
# 1. データクラス特定
grep -n "@dataclass\|class.*Config\|class.*Settings" main.py
# → データクラスのみが対象であることを確認

# 2. GUI・ワークフロー関連コード非接触確認
grep -n "create_project\|setup_.*integration" main.py
# → これらが変更されていないことを確認
```

#### **実装中確認**
```python
# データクラス移動前後の同一性確認
original_config = ProjectConfig("test", "test", "test")
from models.project_config import ProjectConfig as NewProjectConfig
new_config = NewProjectConfig("test", "test", "test")

# 構造同一性確認
assert type(original_config).__dict__ == type(new_config).__dict__
assert original_config.__dict__ == new_config.__dict__
```

#### **実装後検証**
```bash
# 制約条件完全遵守確認
python constraint_verification.py
# → 全制約条件PASS確認
```

### **Phase 3: 設定ファイル処理分離 制約条件保証**

#### **実装前確認**
```bash
# 1. 設定ファイル処理特定
grep -n "load_config\|save_config\|\.env\|environ" main.py
# → 設定ファイルI/Oのみが対象であることを確認

# 2. GUI・ワークフロー・外部連携非接触確認
grep -n "setup_ui\|create_project\|setup_.*integration" main.py
# → これらが変更されていないことを確認
```

#### **実装中確認**
```python
# 設定ファイル処理の同一性確認
original_config = load_config_file(".env")
from config.file_manager import load_config_file as new_load_config
new_config = new_load_config(".env")

# 結果同一性確認
assert original_config == new_config
```

#### **実装後検証**
```bash
# 最終制約条件完全遵守確認
python constraint_verification.py
# → 全制約条件PASS確認

# 統合動作確認
python test_complete_workflow.py
# → 全機能完全同一動作確認
```

---

## 🔒 **制約条件違反防止メカニズム**

### **コード変更監視**
```python
class ChangeMonitor:
    """変更監視システム"""
    
    FORBIDDEN_PATTERNS = [
        r"class ProjectInitializerWindow.*:",
        r"def setup_ui\(",
        r"def setup_connections\(",
        r"def create_project\(",
        r"def setup_.*_integration\(",
        r"self\..*_progress\(",
        r"self\.show_error\("
    ]
    
    def check_file_changes(self, file_path):
        """ファイル変更の制約条件チェック"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content):
                violations = re.findall(pattern, content)
                if self.is_modified(file_path, pattern):
                    raise ConstraintViolationError(
                        f"Forbidden modification detected: {pattern}"
                    )
```

### **自動ロールバック**
```python
class AutoRollback:
    """制約条件違反時の自動ロールバック"""
    
    def __init__(self):
        self.checkpoints = []
        
    def create_checkpoint(self, phase_name):
        """チェックポイント作成"""
        checkpoint = {
            'phase': phase_name,
            'timestamp': datetime.now(),
            'commit_hash': self.get_current_commit()
        }
        self.checkpoints.append(checkpoint)
        
    def rollback_to_checkpoint(self, phase_name):
        """指定フェーズへのロールバック"""
        checkpoint = self.find_checkpoint(phase_name)
        if checkpoint:
            subprocess.run(['git', 'checkout', checkpoint['commit_hash']])
            print(f"Rolled back to {phase_name}")
```

---

## 📊 **制約条件遵守レポート**

### **自動レポート生成**
```python
def generate_compliance_report():
    """制約条件遵守レポート生成"""
    
    report = {
        'timestamp': datetime.now(),
        'gui_compliance': check_gui_compliance(),
        'workflow_compliance': check_workflow_compliance(),
        'integration_compliance': check_integration_compliance(),
        'violations': [],
        'warnings': []
    }
    
    # 違反項目の詳細記録
    if not report['gui_compliance']['passed']:
        report['violations'].extend(report['gui_compliance']['violations'])
    
    if not report['workflow_compliance']['passed']:
        report['violations'].extend(report['workflow_compliance']['violations'])
        
    if not report['integration_compliance']['passed']:
        report['violations'].extend(report['integration_compliance']['violations'])
    
    # レポート出力
    with open('constraint_compliance_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report
```

### **レポート項目**
```json
{
  "gui_compliance": {
    "ui_layout_unchanged": true,
    "button_behavior_unchanged": true,
    "progress_display_unchanged": true,
    "error_display_unchanged": true,
    "overall_passed": true
  },
  "workflow_compliance": {
    "initialization_sequence_unchanged": true,
    "step_processing_unchanged": true,
    "error_recovery_unchanged": true,
    "settings_format_unchanged": true,
    "overall_passed": true
  },
  "integration_compliance": {
    "github_integration_unchanged": true,
    "slack_integration_unchanged": true,
    "sheets_integration_unchanged": true,
    "api_timing_unchanged": true,
    "overall_passed": true
  }
}
```

---

## ✅ **最終制約条件認定基準**

### **必須達成項目**
- [ ] **GUI完全保持**: UIレイアウト・操作性・表示内容100%同一
- [ ] **ワークフロー完全保持**: 初期化手順・順序・処理内容100%同一
- [ ] **外部連携完全保持**: GitHub/Slack/Sheets統合動作100%同一
- [ ] **設定・パラメータ完全保持**: 全設定値・形式100%同一
- [ ] **エラーハンドリング完全保持**: エラー処理・復旧手順100%同一

### **制約条件認定プロセス**
1. **段階別チェック**: 各Phase完了時の制約条件確認
2. **自動検証**: constraint_verification.py による全項目チェック
3. **統合テスト**: 実際のプロジェクト初期化による動作確認
4. **最終認定**: 全必須項目100%達成の確認

---

## 🔄 **セッション中断・引き継ぎプロセス（2025-08-15追加）**

### **Phaseごとのセッション管理**

#### **セッション中断の必須手順**
```bash
# Phase完了後の必須プロセス
1. QualityGate subagent監査実行
2. Serena subagent監査実行  
3. 修正指示への対応完了
4. Handover.md作成
5. セッション中断
```

#### **Handover.md記録項目**
```markdown
# PJINIT v2.0 Phase[N] 実装記録

## 🎯 **実装完了事項**
- [実装した機能・分離・移動]
- [達成した品質基準]
- [通過した品質ゲート]

## 🔄 **手戻り・修正事項**
- [監査で指摘された問題]
- [修正・改善した内容]
- [対応に要した時間]

## 🚨 **重要な技術的決定**
- [実装中に行った重要な判断]
- [制約条件遵守のための工夫]
- [将来のPhaseに影響する決定]

## 📋 **次Phaseへの引き継ぎ**
- [現在のファイル状態]
- [修正済み問題の一覧]
- [次Phase開始時の注意事項]

## 🛡️ **制約条件遵守確認**
- [ ] GUI完全維持確認済み
- [ ] ワークフロー完全維持確認済み
- [ ] 外部連携完全維持確認済み
```

#### **セッション再開時の手順**
```bash
# [PJINIT]切り替え後の必須プロセス
1. Handover.md自動読み込み（CLAUDE.md設定による）
2. 制約条件遵守フレームワーク文書確認
3. 超保守的リファクタリング計画確認
4. 現在Phase状況の把握
5. Serena subagentによる実装再開
```

### **実装ツール制限の技術的保証**

#### **Serena-Only実装の強制**
```python
# 実装時の必須確認事項
ALLOWED_TOOLS = [
    "mcp__serena__*",           # Serenaツール群のみ
    "TodoWrite",                # タスク管理のみ
    "Read"                      # 確認目的のみ
]

FORBIDDEN_TOOLS = [
    "Edit",                     # 通常の編集コマンド禁止
    "Write",                    # ファイル書き込み禁止
    "MultiEdit",                # 複数編集禁止
    "mcp__filesystem__*",       # 他のMCPツール禁止
    "mcp__github__*",           # GitHub MCP禁止
    "mcp__*"                    # その他MCP禁止（Serena以外）
]
```

#### **実装違反の検出メカニズム**
```python
class ImplementationComplianceChecker:
    """実装ツール使用の制約条件チェック"""
    
    def verify_tool_usage(self, used_tools):
        """使用ツールの制約条件確認"""
        for tool in used_tools:
            if tool in self.FORBIDDEN_TOOLS:
                raise ConstraintViolationError(
                    f"Forbidden tool used: {tool}. Only Serena MCP allowed."
                )
    
    def enforce_serena_only(self):
        """Serena専用実装の強制確認"""
        return all([
            self.check_no_edit_commands(),
            self.check_no_filesystem_mcp(),
            self.check_serena_mcp_only()
        ])
```

---

**この制約条件遵守フレームワークにより、ユーザー要求の100%遵守を技術的に保証し、安全で確実なリファクタリングを実現します。**