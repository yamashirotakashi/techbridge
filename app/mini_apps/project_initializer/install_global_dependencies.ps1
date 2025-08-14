# PJINIT v1.2 Global Dependencies Installer for Windows PowerShell
# 仮想環境を使わずにグローバルPython環境に依存関係をインストール

Write-Host "=== PJINIT v1.2 Global Dependencies Installation ===" -ForegroundColor Green
Write-Host "Installing to global Python environment (no venv)" -ForegroundColor Yellow
Write-Host ""

# Pythonバージョン確認
Write-Host "Python version:" -ForegroundColor Cyan
python --version

Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Cyan

# 必須パッケージをグローバルにインストール（1行コマンド）
$packages = @(
    "structlog",
    "pydantic",
    "pydantic-settings",
    "requests",
    "python-dotenv",
    "PyQt6",
    "qasync",
    "slack-sdk",
    "google-auth",
    "google-auth-oauthlib", 
    "google-auth-httplib2",
    "google-api-python-client",
    "PyGithub"
)

# ワンライナーコマンド生成
$oneliner = "pip install " + ($packages -join " ")

Write-Host "Execute this command:" -ForegroundColor Green
Write-Host $oneliner -ForegroundColor Yellow
Write-Host ""

# 実行確認
$confirm = Read-Host "Install now? (Y/N)"
if ($confirm -eq "Y" -or $confirm -eq "y") {
    Invoke-Expression $oneliner
    
    Write-Host ""
    Write-Host "=== Installation Complete ===" -ForegroundColor Green
    Write-Host "You can now run PJINIT directly:" -ForegroundColor Cyan
    Write-Host "  python main.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or build EXE:" -ForegroundColor Cyan
    Write-Host "  .\PJinit.build.ps1" -ForegroundColor Yellow
} else {
    Write-Host "Installation cancelled. Run this command manually:" -ForegroundColor Yellow
    Write-Host $oneliner -ForegroundColor White
}