"""
PJINIT 環境ユーティリティ
Phase 1リファクタリング: 環境関連機能の分離
"""

import sys
import os
from pathlib import Path
from typing import Optional


def detect_wsl_environment() -> bool:
    """WSL環境を正確に検出"""
    try:
        # /proc/version の存在とマイクロソフト文字列の存在をチェック
        if Path('/proc/version').exists():
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                return 'microsoft' in version_info or 'wsl' in version_info
        return False
    except:
        # Windowsネイティブ環境では /proc/version が存在しない
        return False


def safe_print(text: str):
    """Unicode文字を安全に出力 - Windows CP932対応強化"""
    try:
        # Windows環境でCP932エンコーディング問題に対応
        if sys.platform.startswith('win'):
            # Unicode絵文字を安全な文字に置換
            safe_text = (text.replace("✅", "[OK]")
                            .replace("✗", "[ERROR]")
                            .replace("⚠️", "[WARN]")
                            .replace("🔧", "[CONFIG]")
                            .replace("📊", "[DATA]"))
            try:
                print(safe_text.encode('cp932', 'ignore').decode('cp932'))
            except (UnicodeEncodeError, UnicodeDecodeError):
                print(safe_text.encode('ascii', 'ignore').decode('ascii'))
        else:
            print(text)
    except Exception:
        # 最後の手段: ASCII文字のみで出力
        ascii_text = text.encode('ascii', 'ignore').decode('ascii')
        print(ascii_text)


def check_pyqt6_availability() -> bool:
    """PyQt6の利用可能性をチェック"""
    try:
        from PyQt6.QtWidgets import QApplication
        return True
    except ImportError:
        return False


def check_asyncio_integration() -> Optional[str]:
    """asyncio統合ライブラリの利用可能性をチェック"""
    # asyncqtを優先して試行
    try:
        from asyncqt import QEventLoop
        return "asyncqt"
    except ImportError:
        pass
    
    # qasyncを次に試行
    try:
        import qasync
        from qasync import QEventLoop
        return "qasync"
    except ImportError:
        pass
    
    return None


def get_config_path(filename: str) -> Path:
    """設定ファイルのパスを取得"""
    # 現在のスクリプトの親ディレクトリにconfigフォルダがあると仮定
    current_dir = Path(__file__).parent.parent
    config_dir = current_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir / filename


def is_service_available(service_name: str) -> bool:
    """外部サービスの利用可能性をチェック"""
    service_checks = {
        'google_sheets': lambda: _check_google_sheets(),
        'slack': lambda: _check_slack(),
        'github': lambda: _check_github(),
    }
    
    check_func = service_checks.get(service_name)
    if check_func:
        return check_func()
    return False


# ServiceAdapter キャッシュインスタンス (HIGH問題解決: 重複インスタンス化防止)
_service_adapter_cache = None

def _get_cached_service_adapter():
    """ServiceAdapterの共有インスタンスを取得（キャッシュ機構）"""
    global _service_adapter_cache
    if _service_adapter_cache is None:
        try:
            # 絶対インポート（相対インポート問題の回避）
            try:
                from clients.service_adapter import ServiceAdapter
            except ImportError:
                # パスを追加してリトライ
                import sys
                from pathlib import Path
                current_dir = Path(__file__).parent.parent
                if str(current_dir) not in sys.path:
                    sys.path.insert(0, str(current_dir))
                from clients.service_adapter import ServiceAdapter
            
            _service_adapter_cache = ServiceAdapter()
        except ImportError:
            return None
    return _service_adapter_cache

def _check_google_sheets() -> bool:
    """Google Sheets連携の利用可能性"""
    adapter = _get_cached_service_adapter()
    if adapter is None:
        return False
    return adapter.is_available('google_sheets')


def _check_slack() -> bool:
    """Slack連携の利用可能性"""
    adapter = _get_cached_service_adapter()
    if adapter is None:
        return False
    return adapter.is_available('slack')


def _check_github() -> bool:
    """GitHub連携の利用可能性"""
    adapter = _get_cached_service_adapter()
    if adapter is None:
        return False
    return adapter.is_available('github')


def get_environment_info() -> dict:
    """環境情報を取得"""
    return {
        'platform': sys.platform,
        'is_wsl': detect_wsl_environment(),
        'python_version': sys.version,
        'pyqt6_available': check_pyqt6_availability(),
        'asyncio_integration': check_asyncio_integration(),
        'services': {
            'google_sheets': is_service_available('google_sheets'),
            'slack': is_service_available('slack'),
            'github': is_service_available('github'),
        }
    }


# モジュールレベルでの環境チェック
is_wsl = detect_wsl_environment()
pyqt6_available = check_pyqt6_availability()
asyncio_integration = check_asyncio_integration()