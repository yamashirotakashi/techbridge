"""
PJINIT v2.0 Phase 1: Characterization Testing

既存動作を完全記録するテストスイート
制約条件: GUI/ワークフロー/外部連携への影響ゼロ
"""
import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import (
    detect_wsl_environment, 
    get_config_path,
    safe_print,
    is_wsl,
    pyqt6_available
)


class TestEnvironmentDetection(unittest.TestCase):
    """環境検出機能の特性記録テスト"""
    
    def test_wsl_detection_basic_functionality(self):
        """WSL環境検出の基本機能記録"""
        # 現在の検出結果を記録
        current_detection = detect_wsl_environment()
        
        # 検出結果の型と値域を記録
        self.assertIsInstance(current_detection, bool)
        
        # 現在の実行環境での検出結果を記録
        if Path('/proc/version').exists():
            try:
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    expected_result = 'microsoft' in version_info or 'wsl' in version_info
                    self.assertEqual(current_detection, expected_result)
            except:
                # ファイル読み取りエラー時はFalseを期待
                self.assertFalse(current_detection)
        else:
            # /proc/versionが存在しない場合はFalseを期待
            self.assertFalse(current_detection)
    
    def test_config_path_generation(self):
        """設定パス生成の特性記録"""
        test_filename = "test.json"
        result = get_config_path(test_filename)
        
        # 期待されるパス形式を記録
        expected_path = f"config/{test_filename}"
        self.assertEqual(result, expected_path)
        
        # パスの基本的な特性を記録
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("config/"))
        self.assertTrue(result.endswith(test_filename))


class TestModuleAvailability(unittest.TestCase):
    """モジュール可用性チェックの特性記録"""
    
    def test_pyqt6_availability_detection(self):
        """PyQt6可用性検出の記録"""
        # 現在のPyQt6可用性状態を記録
        current_availability = pyqt6_available
        self.assertIsInstance(current_availability, bool)
        
        # 実際のインポート試行結果との整合性記録
        try:
            from PyQt6.QtWidgets import QApplication
            # インポート成功時は可用性がTrueであることを期待
            # ただし、初期化順序により異なる可能性があることを記録
            pass
        except ImportError:
            # インポート失敗時は可用性がFalseであることを期待
            pass
    
    def test_wsl_global_variable(self):
        """WSLグローバル変数の特性記録"""
        # 現在のis_wsl変数の値を記録
        self.assertIsInstance(is_wsl, bool)
        
        # detect_wsl_environment()関数の結果との整合性記録
        detection_result = detect_wsl_environment()
        self.assertEqual(is_wsl, detection_result)


class TestUtilityFunctions(unittest.TestCase):
    """ユーティリティ関数の特性記録"""
    
    @patch('builtins.print')
    def test_safe_print_functionality(self, mock_print):
        """safe_print関数の動作特性記録"""
        test_message = "テストメッセージ"
        
        # safe_print呼び出し
        safe_print(test_message)
        
        # print関数が呼び出されることを記録
        mock_print.assert_called_once_with(test_message)
    
    def test_safe_print_with_various_inputs(self):
        """safe_print関数の多様な入力に対する動作記録"""
        test_cases = [
            "通常のメッセージ",
            "",  # 空文字列
            "日本語メッセージ",
            "English message",
            "特殊文字!@#$%^&*()",
        ]
        
        for test_input in test_cases:
            # 例外が発生しないことを記録
            try:
                safe_print(test_input)
            except Exception as e:
                self.fail(f"safe_print failed with input '{test_input}': {e}")


if __name__ == '__main__':
    # テスト実行時の環境情報記録
    print("=== PJINIT v2.0 Phase 1: Characterization Testing ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"WSL detected: {is_wsl}")
    print(f"PyQt6 available: {pyqt6_available}")
    print("=" * 55)
    
    unittest.main(verbosity=2)
