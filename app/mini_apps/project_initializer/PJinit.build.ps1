# PJinit.build.ps1
# PJINIT v1.0 Windows EXE ビルドスクリプト

Write-Host "=== PJINIT v1.0 EXE ビルド開始 ===" -ForegroundColor Green

# プロジェクトディレクトリに移動
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "作業ディレクトリ: $ProjectRoot" -ForegroundColor Cyan

# 前回ビルド結果の確認
if (Test-Path "dist\PJinit.1.0.exe") {
    Write-Host "前バージョン PJinit.1.0.exe が存在します（保持されます）" -ForegroundColor Yellow
}

# 依存関係確認
Write-Host "依存関係チェック中..." -ForegroundColor Cyan

# Python環境確認
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# PyInstaller確認
$pyinstallerCheck = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstallerCheck) {
    Write-Host "PyInstaller をインストール中..." -ForegroundColor Yellow
    pip install pyinstaller
}

# PyQt6確認
python -c "import PyQt6" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyQt6 をインストール中..." -ForegroundColor Yellow
    pip install PyQt6
}

# ディレクトリ作成
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}
if (!(Test-Path "config")) {
    New-Item -ItemType Directory -Path "config" | Out-Null
}

# PyInstaller実行（グローバルPython環境を使用）
Write-Host "PyInstaller 実行中..." -ForegroundColor Cyan
Write-Host "Using global Python environment (no venv)" -ForegroundColor Yellow

$BuildCommand = "python -m PyInstaller --onefile --windowed --name=PJinit --distpath=dist --workpath=build --specpath=. main.py"
Invoke-Expression $BuildCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PyInstaller ビルド成功" -ForegroundColor Green
} else {
    Write-Error "PyInstaller ビルドエラー"
    exit 1
}

# ビルド結果確認
if (Test-Path "dist\PJinit.exe") {
    Copy-Item "dist\PJinit.exe" "dist\PJinit.1.0.exe" -Force
    
    $fileSize = (Get-Item "dist\PJinit.1.0.exe").Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
    
    Write-Host "=== ビルド完了 ===" -ForegroundColor Green
    Write-Host "出力ファイル: dist\PJinit.1.0.exe" -ForegroundColor Cyan
    Write-Host "ファイルサイズ: $fileSizeMB MB" -ForegroundColor Cyan
    
    # EXE位置記録
    $ExeLocation = Join-Path $ProjectRoot "dist"
    Write-Host "EXE位置: $ExeLocation" -ForegroundColor Yellow
    
} else {
    Write-Error "ビルド失敗: dist\PJinit.exe が作成されませんでした"
    exit 1
}

Write-Host "=== PJINIT v1.0 EXE ビルド完了 ===" -ForegroundColor Green