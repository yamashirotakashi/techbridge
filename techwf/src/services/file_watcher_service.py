"""
ファイル監視サービス - 外部システム統合
技術書典スクレイパーなどの外部システムからのJSONファイルを監視し、自動的にTSVImportServiceに転送
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, QFileSystemWatcher, QTimer, Signal
from datetime import datetime

logger = logging.getLogger(__name__)


class FileWatcherService(QObject):
    """外部システム連携用ファイル監視サービス"""
    
    # シグナル定義
    file_imported = Signal(str, dict)  # file_path, data
    import_error = Signal(str, str)    # file_path, error_message
    import_started = Signal(str)       # file_path
    
    def __init__(self, watch_directory: str = None, tsv_import_service=None):
        super().__init__()
        
        # 監視ディレクトリの設定（デフォルト: プロジェクト/temp/imports）
        if watch_directory is None:
            project_root = Path(__file__).parent.parent.parent
            watch_directory = project_root / 'temp' / 'imports'
        
        self.watch_directory = Path(watch_directory)
        self.tsv_import_service = tsv_import_service
        
        # ファイル監視設定
        self.file_watcher = QFileSystemWatcher()
        self.processed_files = set()  # 重複処理防止
        
        # 処理遅延タイマー（ファイル書き込み完了待ち）
        self.process_timer = QTimer()
        self.process_timer.setSingleShot(True)
        self.process_timer.timeout.connect(self._process_pending_files)
        self.pending_files = []
        
        # 監視ディレクトリ作成
        self._ensure_watch_directory()
        
        # 監視開始
        self._start_watching()
        
    def _ensure_watch_directory(self):
        """監視ディレクトリの存在確認・作成"""
        try:
            self.watch_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"ファイル監視ディレクトリ準備完了: {self.watch_directory}")
        except Exception as e:
            logger.error(f"監視ディレクトリ作成エラー: {e}")
            
    def _start_watching(self):
        """ファイル監視開始"""
        try:
            # ディレクトリを監視対象に追加
            if self.file_watcher.addPath(str(self.watch_directory)):
                logger.info(f"ファイル監視開始: {self.watch_directory}")
            else:
                logger.error(f"ファイル監視開始失敗: {self.watch_directory}")
                
            # シグナル接続
            self.file_watcher.directoryChanged.connect(self._on_directory_changed)
            self.file_watcher.fileChanged.connect(self._on_file_changed)
            
        except Exception as e:
            logger.error(f"ファイル監視サービス開始エラー: {e}")
            
    def _on_directory_changed(self, directory_path: str):
        """ディレクトリ変更イベント"""
        logger.debug(f"ディレクトリ変更検出: {directory_path}")
        self._scan_directory()
        
    def _on_file_changed(self, file_path: str):
        """ファイル変更イベント"""
        logger.debug(f"ファイル変更検出: {file_path}")
        self._queue_file_for_processing(file_path)
        
    def _scan_directory(self):
        """ディレクトリスキャン（新規ファイル検出）"""
        try:
            for file_path in self.watch_directory.glob("*.json"):
                if str(file_path) not in self.processed_files:
                    self._queue_file_for_processing(str(file_path))
                    
        except Exception as e:
            logger.error(f"ディレクトリスキャンエラー: {e}")
            
    def _queue_file_for_processing(self, file_path: str):
        """ファイルを処理キューに追加"""
        if file_path not in self.pending_files:
            self.pending_files.append(file_path)
            logger.debug(f"処理キューに追加: {file_path}")
            
        # 処理遅延タイマー再開始（書き込み完了待ち）
        self.process_timer.start(1000)  # 1秒後に処理
        
    def _process_pending_files(self):
        """キューされたファイルを処理"""
        files_to_process = list(self.pending_files)
        self.pending_files.clear()
        
        for file_path in files_to_process:
            self._process_import_file(file_path)
            
    def _process_import_file(self, file_path: str):
        """インポートファイルを処理"""
        try:
            file_path = Path(file_path)
            
            # ファイル存在確認
            if not file_path.exists():
                logger.warning(f"処理対象ファイルが存在しません: {file_path}")
                return
                
            # 重複処理チェック
            if str(file_path) in self.processed_files:
                logger.debug(f"既に処理済み: {file_path}")
                return
                
            # JSON拡張子チェック
            if file_path.suffix.lower() != '.json':
                logger.debug(f"JSON以外のファイルをスキップ: {file_path}")
                return
                
            logger.info(f"外部システム連携ファイル処理開始: {file_path}")
            self.import_started.emit(str(file_path))
            
            # JSONファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            # データ検証
            if not self._validate_import_data(import_data):
                error_msg = f"インポートデータ形式が不正: {file_path}"
                logger.error(error_msg)
                self.import_error.emit(str(file_path), error_msg)
                return
                
            # TSVImportServiceでの処理
            if self.tsv_import_service:
                success = self._process_with_tsv_service(import_data)
                if success:
                    self.file_imported.emit(str(file_path), import_data)
                    self._mark_as_processed(file_path)
                else:
                    error_msg = f"TSVImportService処理失敗: {file_path}"
                    self.import_error.emit(str(file_path), error_msg)
            else:
                logger.warning("TSVImportServiceが設定されていません")
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON形式エラー: {e}"
            logger.error(f"{error_msg} - {file_path}")
            self.import_error.emit(str(file_path), error_msg)
            
        except Exception as e:
            error_msg = f"ファイル処理エラー: {e}"
            logger.error(f"{error_msg} - {file_path}")
            self.import_error.emit(str(file_path), error_msg)
            
    def _validate_import_data(self, data: Dict[str, Any]) -> bool:
        """インポートデータの検証"""
        try:
            # 基本構造チェック
            if not isinstance(data, dict):
                return False
                
            # 必須フィールドチェック
            required_fields = ['source', 'timestamp', 'data']
            for field in required_fields:
                if field not in data:
                    logger.error(f"必須フィールド不足: {field}")
                    return False
                    
            # データ部分の検証
            data_section = data['data']
            if not isinstance(data_section, dict):
                return False
                
            # 著者データの最小要件（書名は必須）
            if 'book_title' not in data_section or not data_section['book_title']:
                logger.error("書名が設定されていません")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            return False
            
    def _process_with_tsv_service(self, import_data: Dict[str, Any]) -> bool:
        """TSVImportServiceでデータを処理"""
        try:
            # JSONデータから著者データを抽出
            author_data = import_data['data']
            
            # メタデータ追加
            author_data['imported_at'] = datetime.now().isoformat()
            author_data['import_source'] = import_data.get('source', 'external_system')
            
            # TSVImportServiceの_save_to_database メソッドを直接呼び出し
            if hasattr(self.tsv_import_service, '_save_to_database'):
                self.tsv_import_service._save_to_database(author_data)
                logger.info(f"データベース保存完了: {author_data.get('book_title')}")
                
                # Google Sheets同期（オプション）
                if hasattr(self.tsv_import_service, '_sync_to_sheets'):
                    try:
                        self.tsv_import_service._sync_to_sheets(author_data)
                        logger.info(f"Sheets同期完了: {author_data.get('book_title')}")
                    except Exception as e:
                        logger.warning(f"Sheets同期でエラー（処理は継続）: {e}")
                        
                return True
                
            else:
                logger.error("TSVImportServiceに_save_to_databaseメソッドがありません")
                return False
                
        except Exception as e:
            logger.error(f"TSVImportService処理エラー: {e}")
            return False
            
    def _mark_as_processed(self, file_path: Path):
        """ファイルを処理済みとしてマーク"""
        try:
            # 処理済みセットに追加
            self.processed_files.add(str(file_path))
            
            # 処理済みファイルを別ディレクトリに移動
            processed_dir = self.watch_directory / 'processed'
            processed_dir.mkdir(exist_ok=True)
            
            processed_file_path = processed_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
            file_path.rename(processed_file_path)
            
            logger.info(f"処理済みファイル移動: {processed_file_path}")
            
        except Exception as e:
            logger.error(f"処理済みファイル移動エラー: {e}")
            
    def set_tsv_import_service(self, service):
        """TSVImportServiceの設定"""
        self.tsv_import_service = service
        logger.info("TSVImportService設定完了")
        
    def get_watch_directory(self) -> Path:
        """監視ディレクトリパスを取得"""
        return self.watch_directory
        
    def get_processed_count(self) -> int:
        """処理済みファイル数を取得"""
        return len(self.processed_files)
        
    def cleanup(self):
        """サービス終了時のクリーンアップ"""
        try:
            if self.file_watcher:
                self.file_watcher.removePaths(self.file_watcher.directories())
                self.file_watcher.removePaths(self.file_watcher.files())
            logger.info("ファイル監視サービス終了")
        except Exception as e:
            logger.error(f"サービス終了エラー: {e}")


# 使用例とテスト用ヘルパー関数
def create_test_import_file(watch_directory: Path, author_data: Dict[str, Any]) -> Path:
    """テスト用インポートファイルを作成"""
    import_data = {
        'source': 'techbook_scraper',
        'timestamp': datetime.now().isoformat(),
        'data': author_data
    }
    
    test_file = watch_directory / f"import_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(import_data, f, ensure_ascii=False, indent=2)
        
    return test_file