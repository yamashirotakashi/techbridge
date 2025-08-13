#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataBindingManagerテスト - テーブルデータ表示の確認
"""
import sys
import os
import logging

# パス設定
sys.path.insert(0, os.path.abspath('.'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget
from src.gui.data_binding_manager import DataBindingManager
from src.controllers.workflow_controller import WorkflowController
from src.repositories.publication_repository import PublicationRepository
from src.services.config_service import get_config_service
from src.gui.ui_state_manager import UIStateManager

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMainWindow(QMainWindow):
    """テスト用メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataBindingManager Test")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # ワークフローテーブル
        self.workflow_table = QTableWidget()
        self.workflow_table.setColumnCount(5)
        self.workflow_table.setHorizontalHeaderLabels([
            "N番号", "書名", "著者", "ステータス", "更新日"
        ])
        layout.addWidget(self.workflow_table)
        
        # データベース・サービス初期化
        self.repository = PublicationRepository("data/techwf.db")
        self.config_service = get_config_service()
        self.ui_manager = UIStateManager("test_ui_state.json")
        
        # WorkflowController初期化
        self.controller = WorkflowController(
            repository=self.repository,
            config_service=self.config_service,
            sheets_service=None,
            slack_service=None,
            progress_callback=None
        )
        
        # DataBindingManager初期化
        self.data_binding_manager = DataBindingManager(
            main_window=self,
            workflow_controller=self.controller,
            ui_state_manager=self.ui_manager,
            parent=self
        )
        
        # シグナル接続
        self.data_binding_manager.data_loaded.connect(self.on_data_loaded)
        
        logger.info("Test window initialized")
    
    def on_data_loaded(self, workflows):
        """データ読み込み完了"""
        logger.info(f"Data loaded: {len(workflows)} items")
        print(f"テーブル行数: {self.workflow_table.rowCount()}")
        for row in range(self.workflow_table.rowCount()):
            row_data = []
            for col in range(self.workflow_table.columnCount()):
                item = self.workflow_table.item(row, col)
                row_data.append(item.text() if item else "None")
            print(f"Row {row}: {row_data}")
    
    def load_test_data(self):
        """テストデータを読み込み"""
        logger.info("Loading test data...")
        self.data_binding_manager.load_initial_data()

def main():
    """メイン実行"""
    app = QApplication(sys.argv)
    
    try:
        # テストウィンドウ作成
        window = TestMainWindow()
        window.show()
        
        # テストデータ読み込み
        window.load_test_data()
        
        logger.info("DataBindingManager test started")
        print("GUIが表示されました。テーブルにデータが表示されているか確認してください。")
        print("ウィンドウを閉じるとテストが終了します。")
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"テストエラー: {e}")
        return 1

if __name__ == "__main__":
    main()