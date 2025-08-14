# PJINIT v1.2 Windows依存関係インストールスクリプト
# PowerShellネイティブ環境でのTechBridge統合に必要なパッケージをインストール

Write-Host "🔧 PJINIT v1.2 Windows依存関係インストール" -ForegroundColor Green
Write-Host "=" * 60

# Python環境確認
Write-Host "1. Python環境確認..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# pip確認
Write-Host "`n2. pip確認..." -ForegroundColor Yellow
$pipVersion = python -m pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ pip: $pipVersion" -ForegroundColor Green
} else {
    Write-Host "❌ pip not found." -ForegroundColor Red
    exit 1
}

# 必要な依存関係をインストール
Write-Host "`n3. TechBridge統合に必要な依存関係をインストール..." -ForegroundColor Yellow

$dependencies = @(
    "structlog",
    "pydantic>=2.0",
    "pydantic-settings",
    "requests",
    "python-dotenv"
)

foreach ($package in $dependencies) {
    Write-Host "   Installing $package..." -ForegroundColor Cyan
    $result = python -m pip install $package --user 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $package: インストール成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $package: インストール失敗" -ForegroundColor Red
        Write-Host "   Error: $result" -ForegroundColor Red
    }
}

# インストール確認
Write-Host "`n4. インストール確認..." -ForegroundColor Yellow

$testScript = @"
import sys
print('Python環境:', sys.executable)

try:
    import structlog
    print('✅ structlog: OK')
except ImportError:
    print('❌ structlog: FAILED')

try:
    import pydantic
    print(f'✅ pydantic: OK (version {pydantic.VERSION})')
except ImportError:
    print('❌ pydantic: FAILED')

try:
    import pydantic_settings
    print('✅ pydantic_settings: OK')
except ImportError:
    print('❌ pydantic_settings: FAILED')

try:
    import requests
    print('✅ requests: OK')
except ImportError:
    print('❌ requests: FAILED')

try:
    import dotenv
    print('✅ python-dotenv: OK')
except ImportError:
    print('❌ python-dotenv: FAILED')

print('\\n🎉 PJINIT v1.2 Windows依存関係確認完了')
"@

$testResult = python -c $testScript
Write-Host $testResult

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 全ての依存関係が正常にインストールされました" -ForegroundColor Green
    Write-Host "🚀 PJINIT v1.2はWindows PowerShell環境で実行可能です" -ForegroundColor Green
} else {
    Write-Host "`n❌ 一部の依存関係でエラーが発生しました" -ForegroundColor Red
    Write-Host "手動でパッケージをインストールしてください：" -ForegroundColor Yellow
    Write-Host "python -m pip install structlog pydantic>=2.0 pydantic-settings requests python-dotenv --user" -ForegroundColor Cyan
}

Write-Host "`n📋 次の手順："
Write-Host "1. .\install_windows_dependencies.ps1 を実行（このスクリプト）"
Write-Host "2. python test_pjinit_v12_fixes.py を実行してテスト確認"
Write-Host "3. PJINIT v1.2をWindows環境で使用開始"