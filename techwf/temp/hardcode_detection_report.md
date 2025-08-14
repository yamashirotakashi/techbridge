# TechBridge ハードコード値検出レポート
**検出日時**: 2025-08-14  
**Phase 1**: 完全検出・分類結果

## 📊 検出概要

### 検出統計
- **カラーコード**: 42件（16進数）
- **寸法・スタイル値**: 28件（px, em, %等）
- **ファイルパス**: 12件（絶対パス、相対パス）
- **ポート番号・タイムアウト**: 8件
- **その他数値**: 15件

**総計**: 105件のハードコード値を検出

## 🎨 カラーコード（42件）

### theme.py内カラーコード（33件）
```
#ffffff (白背景)
#333333 (濃いグレー前景)
#0078d4 (プライマリブルー)
#6c757d (セカンダリグレー)
#28a745 (アクセントグリーン)
#ffc107 (警告イエロー)
#dc3545 (エラーレッド)
#f8f9fa (ヘッダー背景)
#e3f2fd (選択状態背景)
#dee2e6 (境界線色)
#2b2b2b (ダーク背景)
#404040 (ダークヘッダー)
#1e3a8a (ダーク選択状態)
#555555 (ダーク境界線)
#fafafa (ライト背景)
#212529 (ライト前景)
#007bff (ライトプライマリ)
#e9ecef (ライトヘッダー)
#cce5ff (ライト選択状態)
#ced4da (入力フィールド境界)
```

### theme_applicator.py内（9件）
```
#999999 (無効状態テキスト)
#17a2b8 (情報カラー)
#6c757d (ミュートカラー)
```

## 📐 寸法・スタイル値（28件）

### CSS寸法値
```
border-radius: 4px (角丸半径)
padding: 8px 16px (ボタンパディング)
padding: 5px (テーブルセルパディング)
padding: 8px (ヘッダーパディング)
padding: 4px 8px (メニューアイテム)
padding: 10px (テーマ適用パディング)
border: 1px solid (境界線太さ)
border-bottom: 1px solid (下境界線)
border-right: 1px solid (右境界線)
border-bottom: 2px solid (太い下境界線)
border-radius: 3px (プログレスバー角丸)
border-radius: 2px (チャンク角丸)
min-height: 30px (最小高さ)
min-width: 80px (最小幅)
font-size: 14px (フォントサイズ)
```

### 分割比率・パーセント
```
テーブル: 70% / 詳細: 30% (画面分割比率)
最大90%まで (進捗バー制限)
```

## 🗂️ ファイルパス（12件）

### 絶対パス（危険度: 高）
```
/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool/dist/TechZip.exe
/mnt/c/Users/tky99/dev/technical-fountain-series-support-tool/main.py
/mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer/dist/PJinit.1.1.exe
/mnt/c/Users/tky99/dev/techbridge/app/mini_apps/project_initializer/main.py
```

### 設定ファイル名
```
ui_state.json (UI状態保存)
config.json (設定ファイル)
```

### 相対パス
```
/projects/{n_number}
/output/{n_number}.pdf
/dist/{n_number}
/dist/{n_number}/final
```

## 🔢 ポート番号・タイムアウト（8件）

```
port = 8888 (ソケットサーバー)
timeout=5.0 (スレッド結合タイムアウト)
timeout値: 100, 50 (イベント処理間隔)
sheet_id: 0 (Google Sheets)
row_count: 100 (シート行数)
```

## 📈 その他数値（15件）

### イベント統計初期値
```
processed: 0
failed: 0  
filtered: 0
```

### JSON設定値
```
indent=2 (JSON整形)
token_usage: input: 0, output: 0
token_usage: input: 150, output: 300
progress: 100 (完了状態)
```

### バリデーション値
```
len(errors) == 0 (エラーチェック)
```

## 🎯 優先度別分類

### 🔴 CRITICAL（緊急対応）
1. **絶対ファイルパス** (4件) - 環境依存、移植性に重大な影響
2. **ポート番号** (1件) - 競合リスク
3. **セキュリティ関連数値** (タイムアウト等)

### 🟡 HIGH（高優先度）
1. **カラーコード** (42件) - テーマ管理統合の必要性
2. **CSS寸法値** (28件) - レスポンシブ対応の必要性
3. **設定ファイル名** (2件) - 設定管理の一元化

### 🟢 MEDIUM（中優先度）
1. **統計初期値** (9件) - 設定可能にする必要性
2. **JSON設定値** (4件) - フォーマット設定の外部化

## 🛠️ 推奨対応方針

### 即座対応（Phase 2で実装）
1. **config/theme_config.yaml** - 全カラーコードの外部化
2. **config/ui_config.yaml** - 寸法・スタイル値の外部化
3. **config/paths.yaml** - パス設定の動的化
4. **config/server.yaml** - ポート・タイムアウト設定

### 設定管理システム設計
```yaml
# config/theme_config.yaml
themes:
  light:
    colors:
      background: "#ffffff"
      primary: "#0078d4"
      # ... 他のカラー
  dark:
    colors:
      background: "#2b2b2b"
      # ... ダークテーマ設定
```

### 環境変数フォールバック
```python
# 環境変数優先、設定ファイル次位、デフォルト値最終
SOCKET_PORT = os.getenv('TECHWF_SOCKET_PORT', config.get('server.port', 8888))
```

---

**次フェーズ**: 【Phase 2】設定管理システムの詳細設計
**推定工数**: 1-2人日（69件→105件に増加のため調整）