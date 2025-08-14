# PJINIT v1.2 - グローバルPython環境セットアップ

## 仮想環境を使わない場合のインストール手順

### 1. 必要な依存関係のワンライナーインストール

Windows PowerShellで以下のコマンドを実行：

```powershell
pip install structlog pydantic pydantic-settings requests python-dotenv PyQt6 qasync slack-sdk google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyGithub
```

### 2. 実行方法

仮想環境を使わずに直接実行：

```powershell
# プロジェクトディレクトリに移動
cd C:\Users\tky99\DEV\techbridge\app\mini_apps\project_initializer

# グローバルPythonで直接実行
python main.py
```

### 3. EXEビルド

グローバル環境でPyInstallerを使用：

```powershell
# PyInstallerをグローバルにインストール（未インストールの場合）
pip install pyinstaller

# ビルドスクリプト実行
.\PJinit.build.ps1
```

### 4. 確認コマンド

インストール済みパッケージの確認：

```powershell
pip list | Select-String "structlog|pydantic|slack-sdk|google-api|PyQt6"
```

## 注意事項

- **Python 3.10以上**が必要です
- **Windows PowerShell**を管理者権限で実行することを推奨
- グローバル環境への影響を理解した上でインストールしてください

## トラブルシューティング

### ImportError が発生する場合

```powershell
# パッケージの再インストール
pip install --upgrade --force-reinstall structlog pydantic pydantic-settings
```

### Permission エラーの場合

```powershell
# ユーザー権限でインストール
pip install --user structlog pydantic pydantic-settings requests python-dotenv PyQt6 qasync slack-sdk google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyGithub
```