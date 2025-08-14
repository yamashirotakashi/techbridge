# PJINIT v1.2 - グローバルPython環境での実行
# 仮想環境を使わずに直接実行

Write-Host "=== PJINIT v1.2 - Global Python Execution ===" -ForegroundColor Green
Write-Host ""

# カレントディレクトリをプロジェクトルートに設定
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Working directory: $ProjectRoot" -ForegroundColor Cyan
Write-Host "Using global Python (no venv)" -ForegroundColor Yellow
Write-Host ""

# Pythonバージョン確認
Write-Host "Python version:" -ForegroundColor Cyan
python --version
Write-Host ""

# 依存関係チェック
Write-Host "Checking dependencies..." -ForegroundColor Cyan
$requiredPackages = @("structlog", "pydantic", "slack-sdk", "PyQt6")

$missingPackages = @()
foreach ($package in $requiredPackages) {
    $check = pip show $package 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
        Write-Host "  [$package]: MISSING" -ForegroundColor Red
    } else {
        Write-Host "  [$package]: OK" -ForegroundColor Green
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing packages detected!" -ForegroundColor Red
    Write-Host "Run this command to install:" -ForegroundColor Yellow
    Write-Host "pip install structlog pydantic pydantic-settings requests python-dotenv PyQt6 qasync slack-sdk google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyGithub" -ForegroundColor White
    Write-Host ""
    $confirm = Read-Host "Install now? (Y/N)"
    if ($confirm -eq "Y" -or $confirm -eq "y") {
        pip install structlog pydantic pydantic-settings requests python-dotenv PyQt6 qasync slack-sdk google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyGithub
    } else {
        exit 1
    }
}

Write-Host ""
Write-Host "Starting PJINIT v1.2..." -ForegroundColor Green
Write-Host ""

# グローバルPythonで実行
python main.py