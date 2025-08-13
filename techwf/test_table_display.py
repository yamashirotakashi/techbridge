#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テーブル表示テスト
DataBindingManagerがテーブルにデータを正しく表示するかテスト
"""
import sys
import os

# パス設定
sys.path.insert(0, os.path.abspath('.'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QPushButton, QLabel
from PySide6.QtCore import Qt
from src.gui.data_binding_manager import DataBindingManager, WorkflowData
from src.repositories.publication_repository import PublicationRepository
from src.services.config_service import get_config_service
from src.controllers.workflow_controller import WorkflowController
from src.gui.ui_state_manager import UIStateManager

class TestTableWindow(QMainWindow):
    """テーブル表示テスト用ウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechWF Table Display Test")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 情報ラベル
        self.info_label = QLabel("テーブル表示テスト")
        layout.addWidget(self.info_label)
        
        # ワークフローテーブル
        self.workflow_table = QTableWidget()
        self.workflow_table.setColumnCount(5)
        self.workflow_table.setHorizontalHeaderLabels([
            "N番号", "書名", "著者", "ステータス", "更新日"
        ])
        layout.addWidget(self.workflow_table)
        
        # テストボタン
        self.load_button = QPushButton("サンプルデータ読み込み")
        self.load_button.clicked.connect(self.load_test_data)
        layout.addWidget(self.load_button)
        
        self.manual_button = QPushButton("手動でテーブルに追加")
        self.manual_button.clicked.connect(self.add_manual_data)
        layout.addWidget(self.manual_button)
        
        # コンポーネント初期化
        self.setup_components()
        
    def setup_components(self):
        """必要なコンポーネントを初期化"""
        try:
            # データベース・サービス初期化
            self.repository = PublicationRepository("data/test_techwf.db")
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
            self.data_binding_manager.data_changed.connect(self.on_data_changed)
            
            self.info_label.setText("✅ 初期化完了 - ボタンをクリックしてテストしてください")
            
        except Exception as e:
            self.info_label.setText(f"❌ 初期化エラー: {e}")
            print(f"Setup error: {e}")
    
    def load_test_data(self):
        """DataBindingManager経由でテストデータを読み込み"""
        try:
            self.info_label.setText("🔄 DataBindingManager経由でデータ読み込み中...")
            self.data_binding_manager.load_initial_data()
        except Exception as e:
            self.info_label.setText(f"❌ データ読み込みエラー: {e}")
            print(f"Load error: {e}")
    
    def add_manual_data(self):
        """手動でテーブルにデータを追加（DataBindingManager無し）"""
        try:
            self.info_label.setText("🔄 手動でテーブルにデータ追加中...")
            
            # テーブルをクリア
            self.workflow_table.setRowCount(0)
            
            # サンプルデータを手動で追加
            sample_data = [
                ["N11111", "手動追加書籍1", "手動著者A", "手動ステータス", "2025-01-10"],
                ["N22222", "手動追加書籍2", "手動著者B", "手動完成", "2025-01-11"]
            ]
            
            self.workflow_table.setRowCount(len(sample_data))
            
            for row, row_data in enumerate(sample_data):
                for col, cell_data in enumerate(row_data):
                    from PySide6.QtWidgets import QTableWidgetItem
                    item = QTableWidgetItem(str(cell_data))
                    self.workflow_table.setItem(row, col, item)
            
            self.info_label.setText(f"✅ 手動追加完了: {len(sample_data)}行")
            
        except Exception as e:
            self.info_label.setText(f"❌ 手動追加エラー: {e}")
            print(f"Manual add error: {e}")
    
    def on_data_loaded(self, workflows):
        """データ読み込み完了コールバック"""
        try:
            self.info_label.setText(f"✅ DataBindingManager経由でデータ読み込み完了: {len(workflows)}行")
            print(f"Data loaded callback: {len(workflows)} workflows")
            print(f"Table rows after loading: {self.workflow_table.rowCount()}")
            
            # テーブル内容を確認
            for row in range(self.workflow_table.rowCount()):
                row_data = []
                for col in range(self.workflow_table.columnCount()):
                    item = self.workflow_table.item(row, col)
                    row_data.append(item.text() if item else "None")
                print(f"Row {row}: {row_data}")
                
        except Exception as e:
            self.info_label.setText(f"❌ データ読み込みコールバックエラー: {e}")
            print(f"Callback error: {e}")
    
    def on_data_changed(self):
        """データ変更コールバック"""
        print("Data changed signal received")
        self.info_label.setText(f"🔄 データ変更通知 - テーブル行数: {self.workflow_table.rowCount()}")

def main():
    """メイン実行"""
    app = QApplication(sys.argv)
    
    try:
        window = TestTableWindow()
        window.show()
        
        print("テーブル表示テストウィンドウが開きました")
        print("以下の操作をテストしてください:")
        print("1. 'サンプルデータ読み込み' ボタン - DataBindingManager経由でデータを読み込み")
        print("2. '手動でテーブルに追加' ボタン - 直接テーブルにデータを追加")
        print("3. テーブルにデータが表示されるかを確認")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"アプリケーションエラー: {e}")
        return 1

if __name__ == "__main__":
    main()