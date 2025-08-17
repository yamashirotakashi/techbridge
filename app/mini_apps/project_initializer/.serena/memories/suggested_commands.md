# PJINIT Development Commands

## 開発環境
- **OS**: Linux (WSL2)
- **Python**: 3.x
- **仮想環境**: venv, venv_exe, venv_test, venv_windows

## 基本コマンド

### 環境準備
```bash
# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### アプリケーション実行
```bash
# GUI モード
python main.py

# CLI モード  
python main.py --cli --n-code N12345

# デバッグモード
python debug_import.py
```

### テスト実行
```bash
# 全テスト実行
python -m pytest

# 特定テスト
python test_complete_slack_integration.py
python test_github_integration.py
python test_multi_sheet_integration.py
```

### ビルド
```bash
# Windows EXE作成
powershell -File PJinit.build.ps1

# PyInstaller (直接)
pyinstaller --onefile main.py
```

### コード品質チェック
```bash
# ファイルサイズチェック
find . -name "*.py" -exec wc -l {} + | sort -n

# 複雑度チェック  
python -m mccabe --min 10 main.py
python -m mccabe --min 10 clients/service_adapter.py

# Import 分析
python debug_import.py
```

### 設定・デバッグ
```bash
# 設定テスト
python test_settings_complete.py

# 認証テスト
python test_working_credentials.py

# サービス接続テスト
python test_real_sheets_after_enable.py
```

## 重要なファイル
- `main.py` - メインエントリーポイント
- `clients/service_adapter.py` - サービス統合層
- `PJinit.build.ps1` - Windows EXE ビルドスクリプト
- `.env` - 環境変数設定