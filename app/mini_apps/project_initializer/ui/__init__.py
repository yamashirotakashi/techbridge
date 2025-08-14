"""
PJINIT User Interface
Phase 1リファクタリング: UI層
"""

try:
    from .main_window import ProjectInitializerWindow
    __all__ = ['ProjectInitializerWindow']
except ImportError:
    # PyQt6が利用できない環境では無視
    __all__ = []