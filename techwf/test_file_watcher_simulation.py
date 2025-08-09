#!/usr/bin/env python3
"""
FileWatcherService シミュレーションテスト
GUI起動なしでFileWatcherServiceの動作を検証
"""

import sys
import json
import logging
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.file_watcher_service import FileWatcherService
from src.services.tsv_import_service import TSVImportService

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockRepository:
    """モックリポジトリ（テスト用）"""
    def __init__(self, db_path):
        self.db_path = db_path
        
    def _get_connection(self):
        import sqlite3
        return sqlite3.connect(self.db_path)

def test_file_watcher_integration():
    """FileWatcherService統合テスト"""
    
    print("🚀 FileWatcherService 統合テスト開始")
    print("=" * 60)
    
    # Mock repository作成
    db_path = project_root / 'data' / 'techwf.db'
    repository = MockRepository(str(db_path))
    
    # TSVImportService作成
    tsv_service = TSVImportService(repository=repository)
    print("✅ TSVImportService初期化完了")
    
    # FileWatcherService作成
    watcher_service = FileWatcherService(
        tsv_import_service=tsv_service,
        watch_directory=str(project_root / 'temp' / 'imports')
    )
    print(f"✅ FileWatcherService初期化完了")
    print(f"   監視ディレクトリ: {watcher_service.watch_directory}")
    
    # テストファイルを探す
    import_dir = project_root / 'temp' / 'imports'
    test_files = list(import_dir.glob('integration_test_*.json'))
    
    if not test_files:
        print("❌ テストファイルが見つかりません")
        return False
        
    test_file = test_files[0]
    print(f"📁 テストファイル: {test_file.name}")
    
    # ファイル処理のシミュレーション（FileWatcherServiceの内部メソッドを直接呼び出し）
    try:
        # _process_import_file メソッドを直接呼び出し
        print("🔄 ファイル処理開始...")
        watcher_service._process_import_file(str(test_file))
        print("✅ ファイル処理完了!")
        
        # データベース確認
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pen_name, email, company_name, created_at FROM author_master WHERE email = ?",
                ("test@example.com",)
            )
            result = cursor.fetchone()
            
        if result:
            print("🎯 データベース確認結果:")
            print(f"   ペンネーム: {result[0]}")
            print(f"   メール: {result[1]}")
            print(f"   会社名: {result[2]}")
            print(f"   作成日時: {result[3]}")
            print("✅ 統合テスト成功!")
            return True
        else:
            print("❌ データベースにデータが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("=" * 60)
        print("📊 FileWatcherService統合テスト完了")

if __name__ == "__main__":
    success = test_file_watcher_integration()
    sys.exit(0 if success else 1)