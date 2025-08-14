#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PJINIT - Project Initializer
プロジェクト初期化ツール メインエントリーポイント
"""

import sys
import os
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

# PyQt6インポート
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
        QCheckBox, QFileDialog, QMessageBox, QProgressBar, QTabWidget
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon
except ImportError as e:
    print(f"PyQt6 import error: {e}")
    print("Please install PyQt6: pip install PyQt6")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pjinit.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProjectConfig:
    """プロジェクト設定"""
    name: str
    path: str
    project_type: str
    template: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    git_init: bool = True
    virtual_env: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'path': self.path,
            'project_type': self.project_type,
            'template': self.template,
            'description': self.description,
            'author': self.author,
            'license': self.license,
            'git_init': self.git_init,
            'virtual_env': self.virtual_env
        }


class ProjectInitializerWorker(QThread):
    """プロジェクト初期化ワーカースレッド"""
    
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config: ProjectConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """プロジェクト初期化実行"""
        try:
            self.progress_updated.emit(10, "プロジェクトディレクトリ作成中...")
            self.create_project_structure()
            
            self.progress_updated.emit(30, "設定ファイル作成中...")
            self.create_config_files()
            
            self.progress_updated.emit(50, "テンプレートファイル作成中...")
            self.create_template_files()
            
            if self.config.git_init:
                self.progress_updated.emit(70, "Gitリポジトリ初期化中...")
                self.initialize_git()
            
            if self.config.virtual_env:
                self.progress_updated.emit(85, "仮想環境作成中...")
                self.create_virtual_env()
            
            self.progress_updated.emit(100, "完了!")
            self.finished.emit(True, "プロジェクト初期化が完了しました")
            
        except Exception as e:
            logger.error(f"プロジェクト初期化エラー: {e}")
            self.finished.emit(False, f"エラー: {str(e)}")
    
    def create_project_structure(self):
        """プロジェクト構造作成"""
        project_path = Path(self.config.path) / self.config.name
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 基本ディレクトリ構造
        directories = ['src', 'tests', 'docs', 'config', 'data', 'scripts']
        for dir_name in directories:
            (project_path / dir_name).mkdir(exist_ok=True)
    
    def create_config_files(self):
        """設定ファイル作成"""
        project_path = Path(self.config.path) / self.config.name
        
        # README.md
        readme_content = f"""# {self.config.name}

{self.config.description}

## 概要
プロジェクト種別: {self.config.project_type}
テンプレート: {self.config.template}

## セットアップ
```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリケーション実行
python src/main.py
```

## 作成者
{self.config.author}

## ライセンス
{self.config.license}
"""
        (project_path / "README.md").write_text(readme_content, encoding='utf-8')
        
        # requirements.txt
        requirements = self.get_template_requirements()
        (project_path / "requirements.txt").write_text(requirements, encoding='utf-8')
        
        # .gitignore
        gitignore_content = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/
.env
.DS_Store
*.log
*.db
*.sqlite3
.idea/
.vscode/
"""
        (project_path / ".gitignore").write_text(gitignore_content)
    
    def create_template_files(self):
        """テンプレート固有ファイル作成"""
        project_path = Path(self.config.path) / self.config.name
        
        if self.config.template == "python_app":
            # main.py
            main_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{self.config.name} - メインアプリケーション
"""

def main():
    print("Hello, {self.config.name}!")

if __name__ == "__main__":
    main()
'''
            (project_path / "src" / "main.py").write_text(main_content, encoding='utf-8')
        
        elif self.config.template == "web_app":
            # Flask/FastAPI テンプレート
            app_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{self.config.name} - Webアプリケーション
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='{self.config.name}')

if __name__ == "__main__":
    app.run(debug=True)
'''
            (project_path / "src" / "app.py").write_text(app_content, encoding='utf-8')
    
    def get_template_requirements(self) -> str:
        """テンプレート別requirements.txt"""
        if self.config.template == "python_app":
            return "requests>=2.28.0\npytest>=7.0.0\n"
        elif self.config.template == "web_app":
            return "Flask>=2.3.0\nrequests>=2.28.0\npytest>=7.0.0\n"
        elif self.config.template == "data_science":
            return "pandas>=1.5.0\nnumpy>=1.24.0\nmatplotlib>=3.6.0\njupyter>=1.0.0\n"
        return "pytest>=7.0.0\n"
    
    def initialize_git(self):
        """Git初期化"""
        project_path = Path(self.config.path) / self.config.name
        os.system(f"cd '{project_path}' && git init")
        os.system(f"cd '{project_path}' && git add .")
        os.system(f"cd '{project_path}' && git commit -m 'Initial commit'")
    
    def create_virtual_env(self):
        """仮想環境作成"""
        project_path = Path(self.config.path) / self.config.name
        os.system(f"cd '{project_path}' && python -m venv venv")


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PJINIT - Project Initializer v1.0")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """UI設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # タイトル
        title_label = QLabel("PJINIT - Project Initializer")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        
        # 基本設定タブ
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基本設定")
        
        # 詳細設定タブ
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "詳細設定")
        
        layout.addWidget(tab_widget)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton("プロジェクト作成")
        self.create_button.clicked.connect(self.create_project)
        button_layout.addWidget(self.create_button)
        
        quit_button = QPushButton("終了")
        quit_button.clicked.connect(self.close)
        button_layout.addWidget(quit_button)
        
        layout.addLayout(button_layout)
    
    def create_basic_tab(self) -> QWidget:
        """基本設定タブ作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # プロジェクト名
        name_group = QGroupBox("プロジェクト情報")
        name_layout = QVBoxLayout(name_group)
        
        name_layout.addWidget(QLabel("プロジェクト名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("my_project")
        name_layout.addWidget(self.name_edit)
        
        name_layout.addWidget(QLabel("説明:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("プロジェクトの説明を入力...")
        name_layout.addWidget(self.description_edit)
        
        layout.addWidget(name_group)
        
        # プロジェクトパス
        path_group = QGroupBox("保存場所")
        path_layout = QVBoxLayout(path_group)
        
        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setText(str(Path.home() / "Projects"))
        path_input_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("参照...")
        browse_button.clicked.connect(self.browse_path)
        path_input_layout.addWidget(browse_button)
        
        path_layout.addLayout(path_input_layout)
        layout.addWidget(path_group)
        
        # テンプレート選択
        template_group = QGroupBox("テンプレート")
        template_layout = QVBoxLayout(template_group)
        
        template_layout.addWidget(QLabel("プロジェクト種別:"))
        self.project_type_combo = QComboBox()
        self.project_type_combo.addItems([
            "Python Application",
            "Web Application", 
            "Data Science",
            "Desktop GUI",
            "CLI Tool"
        ])
        template_layout.addWidget(self.project_type_combo)
        
        template_layout.addWidget(QLabel("テンプレート:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "python_app",
            "web_app",
            "data_science",
            "gui_app",
            "cli_tool"
        ])
        template_layout.addWidget(self.template_combo)
        
        layout.addWidget(template_group)
        
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """詳細設定タブ作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 作成者情報
        author_group = QGroupBox("作成者情報")
        author_layout = QVBoxLayout(author_group)
        
        author_layout.addWidget(QLabel("作成者:"))
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Your Name")
        author_layout.addWidget(self.author_edit)
        
        author_layout.addWidget(QLabel("ライセンス:"))
        self.license_combo = QComboBox()
        self.license_combo.addItems(["MIT", "Apache 2.0", "GPL-3.0", "BSD-3-Clause", "Proprietary"])
        author_layout.addWidget(self.license_combo)
        
        layout.addWidget(author_group)
        
        # 初期化オプション
        options_group = QGroupBox("初期化オプション")
        options_layout = QVBoxLayout(options_group)
        
        self.git_check = QCheckBox("Gitリポジトリを初期化")
        self.git_check.setChecked(True)
        options_layout.addWidget(self.git_check)
        
        self.venv_check = QCheckBox("仮想環境を作成")
        self.venv_check.setChecked(True)
        options_layout.addWidget(self.venv_check)
        
        layout.addWidget(options_group)
        
        return widget
    
    def browse_path(self):
        """パス参照ダイアログ"""
        path = QFileDialog.getExistingDirectory(self, "プロジェクト保存先を選択")
        if path:
            self.path_edit.setText(path)
    
    def create_project(self):
        """プロジェクト作成実行"""
        # 入力検証
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "エラー", "プロジェクト名を入力してください")
            return
        
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "エラー", "保存先パスを指定してください")
            return
        
        # 設定作成
        config = ProjectConfig(
            name=self.name_edit.text().strip(),
            path=self.path_edit.text().strip(),
            project_type=self.project_type_combo.currentText(),
            template=self.template_combo.currentText(),
            description=self.description_edit.toPlainText().strip(),
            author=self.author_edit.text().strip(),
            license=self.license_combo.currentText(),
            git_init=self.git_check.isChecked(),
            virtual_env=self.venv_check.isChecked()
        )
        
        # 重複チェック
        project_path = Path(config.path) / config.name
        if project_path.exists():
            reply = QMessageBox.question(
                self, "確認",
                f"プロジェクト '{config.name}' は既に存在します。\n上書きしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # ワーカースレッド開始
        self.create_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = ProjectInitializerWorker(config)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.creation_finished)
        self.worker.start()
    
    def update_progress(self, value: int, message: str):
        """プログレス更新"""
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(message)
    
    def creation_finished(self, success: bool, message: str):
        """作成完了処理"""
        self.create_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().clearMessage()
        
        if success:
            QMessageBox.information(self, "完了", message)
        else:
            QMessageBox.critical(self, "エラー", message)


def print_help():
    """ヘルプ表示"""
    help_text = """
PJINIT v1.0 - Project Initializer

使用方法:
  python main.py [オプション]

オプション:
  -h, --help     このヘルプを表示
  -v, --version  バージョン情報を表示
  -c, --cli      CLIモードで起動

例:
  python main.py              # GUI/CLIモード（環境により自動選択）
  python main.py --cli        # CLIモード強制起動
  python main.py --help       # ヘルプ表示
"""
    print(help_text)


def run_cli_mode():
    """CLIモード実行"""
    print("\n=== PJINIT v1.0 - CLI Mode ===")
    
    try:
        # プロジェクト名入力
        try:
            project_name = input("プロジェクト名を入力してください: ").strip()
            if not project_name:
                print("エラー: プロジェクト名が必要です")
                return
        except EOFError:
            print("\n入力がキャンセルされました")
            return
        
        # プロジェクトパス入力
        default_path = str(Path.home() / "Projects")
        try:
            project_path = input(f"保存先パス [{default_path}]: ").strip()
            if not project_path:
                project_path = default_path
        except EOFError:
            print("\n入力がキャンセルされました")
            return
        
        # プロジェクトタイプ選択
        types = [
            "Python Application",
            "Web Application", 
            "Data Science",
            "Desktop GUI",
            "CLI Tool"
        ]
        
        print("\nプロジェクトタイプを選択してください:")
        for i, t in enumerate(types, 1):
            print(f"  {i}. {t}")
        
        while True:
            try:
                choice = int(input("選択 (1-5): "))
                if 1 <= choice <= 5:
                    project_type = types[choice - 1]
                    break
                else:
                    print("1-5の数字を入力してください")
            except ValueError:
                print("数字を入力してください")
        
        # テンプレート選択
        templates = ["python_app", "web_app", "data_science", "gui_app", "cli_tool"]
        template = templates[choice - 1]
        
        # 説明入力
        description = input("プロジェクトの説明 (オプション): ").strip()
        
        # 作成者入力
        author = input("作成者名 (オプション): ").strip()
        
        # オプション確認
        git_init = input("Gitリポジトリを初期化しますか？ [Y/n]: ").strip().lower()
        git_init = git_init != 'n'
        
        venv_create = input("仮想環境を作成しますか？ [Y/n]: ").strip().lower()
        venv_create = venv_create != 'n'
        
        # 設定確認
        print(f"\n=== 設定確認 ===")
        print(f"プロジェクト名: {project_name}")
        print(f"保存先: {project_path}")
        print(f"タイプ: {project_type}")
        print(f"テンプレート: {template}")
        print(f"説明: {description or '(なし)'}")
        print(f"作成者: {author or '(なし)'}")
        print(f"Git初期化: {'Yes' if git_init else 'No'}")
        print(f"仮想環境: {'Yes' if venv_create else 'No'}")
        
        confirm = input("\nこの設定でプロジェクトを作成しますか？ [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("キャンセルしました")
            return
        
        # プロジェクト設定作成
        config = ProjectConfig(
            name=project_name,
            path=project_path,
            project_type=project_type,
            template=template,
            description=description,
            author=author,
            license="MIT",
            git_init=git_init,
            virtual_env=venv_create
        )
        
        # プロジェクト作成実行
        print("\nプロジェクト作成中...")
        worker = ProjectInitializerWorker(config)
        
        # CLIモードでは直接実行
        print("1. プロジェクトディレクトリ作成中...")
        worker.create_project_structure()
        
        print("2. 設定ファイル作成中...")
        worker.create_config_files()
        
        print("3. テンプレートファイル作成中...")
        worker.create_template_files()
        
        if config.git_init:
            print("4. Gitリポジトリ初期化中...")
            worker.initialize_git()
        
        if config.virtual_env:
            print("5. 仮想環境作成中...")
            worker.create_virtual_env()
        
        print(f"\n✅ プロジェクト '{project_name}' の作成が完了しました！")
        print(f"📁 場所: {Path(project_path) / project_name}")
        
    except KeyboardInterrupt:
        print("\n\nキャンセルしました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        logger.error(f"CLIモードエラー: {e}")


def main():
    """メイン関数"""
    # ログディレクトリ作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.info("PJINIT v1.0 起動開始")
    
    # コマンドライン引数チェック
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print_help()
            return
        elif sys.argv[1] in ['--cli', '-c']:
            run_cli_mode()
            return
        elif sys.argv[1] in ['--version', '-v']:
            print("PJINIT v1.0 - Project Initializer")
            return
    
    # WSL環境チェック
    is_wsl = 'microsoft' in os.uname().release.lower() if hasattr(os, 'uname') else False
    display_available = 'DISPLAY' in os.environ
    
    # WSL環境では常にCLIモードを使用（X11接続が不安定なため）
    if is_wsl:
        logger.warning("WSL環境が検出されました。CLIモードで起動します。")
        print("WSL環境のため、CLIモードで起動します。")
        if display_available:
            print("（DISPLAY変数は設定されていますが、X11接続が不安定な可能性があります）")
        print("GUIを強制的に使用する場合は、別途X11サーバーの設定を確認してください。")
        run_cli_mode()
        return
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PJINIT")
        app.setApplicationVersion("1.0")
        
        # メインウィンドウ作成
        window = MainWindow()
        window.show()
        
        logger.info("GUI起動完了")
        
        # イベントループ開始
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"GUI起動に失敗: {e}")
        print(f"GUI起動に失敗しました: {e}")
        print("CLIモードで起動します...")
        run_cli_mode()


if __name__ == "__main__":
    main()