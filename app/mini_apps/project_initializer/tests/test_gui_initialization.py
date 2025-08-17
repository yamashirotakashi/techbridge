"""
PJINIT v2.0 Phase 1: GUI初期化 Characterization Testing

ProjectInitializerWindowクラスの初期化動作を記録
制約条件: 実際のGUI起動は行わず、初期化パラメータのみ記録
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock

# テスト対象モジュールのインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProjectInitializerWindowCharacterization(unittest.TestCase):
    """ProjectInitializerWindowクラスの特性記録テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.mock_app = Mock()
    
    @patch('main.pyqt6_available', True)
    @patch('main.QApplication')
    @patch('main.ProjectInitializerWindow')
    def test_gui_initialization_parameters(self, mock_window, mock_qapp):
        """GUI初期化パラメータの記録"""
        from main import main
        
        # QApplication初期化パラメータの記録
        mock_app_instance = Mock()
        mock_qapp.return_value = mock_app_instance
        mock_window_instance = Mock()
        mock_window.return_value = mock_window_instance
        
        # WSL環境ではない場合のテスト（GUI初期化パス）
        with patch('main.is_wsl', False):
            with patch('sys.argv', ['main.py']):  # コマンドライン引数をクリア
                try:
                    main()
                except SystemExit:
                    pass  # app.exec()のSystemExitは正常
        
        # QApplication初期化が呼ばれることを記録
        mock_qapp.assert_called_once_with(sys.argv)
        mock_app_instance.setStyle.assert_called_once_with("Fusion")
        
        # ProjectInitializerWindow初期化が呼ばれることを記録
        mock_window.assert_called_once()
        mock_window_instance.show.assert_called_once()
    
    @patch('main.pyqt6_available', False)
    @patch('main.run_cli_mode')
    def test_gui_fallback_to_cli(self, mock_run_cli):
        """PyQt6無効時のCLIフォールバック記録"""
        from main import main
        
        with patch('main.is_wsl', False):  # WSL以外でもPyQt6がない場合
            main()
        
        # CLI mode起動が呼ばれることを記録
        mock_run_cli.assert_called_once()
    
    @patch('main.is_wsl', True)
    @patch('main.run_cli_mode')
    def test_wsl_environment_cli_mode(self, mock_run_cli):
        """WSL環境でのCLIモード強制起動記録"""
        from main import main
        
        main()
        
        # WSL環境ではCLI mode強制起動を記録
        mock_run_cli.assert_called_once()
    
    @patch('main.pyqt6_available', True)
    @patch('main.QApplication')
    @patch('main.ProjectInitializerWindow')
    @patch('main.QEventLoop')
    def test_event_loop_setup_characterization(self, mock_qeventloop, mock_window, mock_qapp):
        """イベントループ設定の特性記録"""
        from main import main
        import asyncio
        
        mock_app_instance = Mock()
        mock_qapp.return_value = mock_app_instance
        mock_window_instance = Mock()
        mock_window.return_value = mock_window_instance
        mock_loop = Mock()
        mock_qeventloop.return_value = mock_loop
        
        with patch('main.is_wsl', False):
            with patch('sys.argv', ['main.py']):
                with patch('asyncio.set_event_loop') as mock_set_loop:
                    try:
                        main()
                    except SystemExit:
                        pass
        
        # asyncqtイベントループ設定が呼ばれることを記録
        mock_qeventloop.assert_called_once_with(mock_app_instance)
        mock_set_loop.assert_called_once_with(mock_loop)


class TestMainFunctionCharacterization(unittest.TestCase):
    """main関数の実行パス特性記録"""
    
    def test_service_status_reporting(self):
        """サービス状況レポート機能の記録"""
        with patch('main.pjinit_settings') as mock_settings:
            mock_settings.get_service_status.return_value = {
                'Google Sheets': True,
                'Slack': False,
                'GitHub': True
            }
            
            with patch('main.safe_print') as mock_print:
                with patch('main.is_wsl', False):
                    with patch('main.pyqt6_available', False):
                        with patch('main.run_cli_mode') as mock_cli:
                            from main import main
                            main()
            
            # サービス状況の取得が呼ばれることを記録
            mock_settings.get_service_status.assert_called_once()
            
            # サービス状況の表示が行われることを記録
            self.assertTrue(mock_print.called)
            # 3つのサービス状況（✅×2, ⚠️×1）が表示されることを期待
            self.assertEqual(mock_print.call_count, 3)


if __name__ == '__main__':
    print("=== GUI Initialization Characterization Testing ===")
    unittest.main(verbosity=2)
