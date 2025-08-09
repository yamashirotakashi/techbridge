#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TECHWFファイルベース統合テスト
技術書典スクレイパー → TECHWF データ転送テスト
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# プロジェクトルートを設定
sys.path.insert(0, str(Path(__file__).parent))

def create_test_import_data():
    """テスト用インポートデータを作成"""
    return {
        "source": "techbook_scraper",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "book_title": "【テスト】AI時代のプログラミング実践ガイド",
            "twitter_account": "@test_author",
            "github_account": "test_author",
            "dev_environment_select": "Python, JavaScript",
            "dev_environment_other": "Docker, AWS",
            "company_name": "テスト株式会社",
            "company_name_kana": "テストカブシキガイシャ",
            "postal_code": "100-0001",
            "address": "東京都千代田区千代田1-1-1",
            "email": "test@example.com",
            "phone": "03-1234-5678",
            "mobile": "090-1234-5678",
            "business_type": "個人",
            "withholding_tax": "不要",
            "domestic_resident": "国内居住",
            "bank_name": "テスト銀行",
            "branch_name": "本店",
            "account_type": "普通",
            "account_number": "1234567",
            "account_holder": "テスト太郎",
            "account_holder_kana": "テストタロウ",
            "copyright_name_en": "Test Taro",
            "co_author_emails": "",
            "notes": "テスト用データです",
            "application_date": "2025-08-08",
            "invoice_number": "",
            "tax_status": "非課税事業者",
            "pen_name": "テストペン太郎",
            "pen_name_kana": "テストペンタロウ",
            "profile_text": "AI分野の研究開発に従事。プログラミング教育にも力を入れている。",
            "notes2": "追加備考：技術書典初参加"
        }
    }

def main():
    """メイン実行関数"""
    print("🚀 TECHWF ファイルベース統合テスト開始")
    print("=" * 60)
    
    # プロジェクトルート設定
    project_root = Path(__file__).parent
    
    # 監視ディレクトリのパス
    watch_directory = project_root / 'temp' / 'imports'
    
    # ディレクトリ作成
    watch_directory.mkdir(parents=True, exist_ok=True)
    print(f"📁 監視ディレクトリ: {watch_directory}")
    
    # テストデータ作成
    test_data = create_test_import_data()
    
    # テストファイル作成
    test_file = watch_directory / f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print(f"📄 テストファイル作成: {test_file.name}")
    print(f"📚 テスト書名: {test_data['data']['book_title']}")
    
    # JSONファイル書き出し
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ テストファイル作成完了: {test_file}")
    print()
    print("🎯 次の手順:")
    print("1. TechWF アプリケーションを起動")
    print("2. ファイル監視サービスがテストファイルを自動検出")
    print("3. データベースとGoogle Sheetsに自動保存")
    print("4. GUI画面でデータを確認")
    print()
    print("💡 テスト内容:")
    print(f"   - 書名: {test_data['data']['book_title']}")
    print(f"   - 著者: {test_data['data']['pen_name']}")
    print(f"   - メール: {test_data['data']['email']}")
    print(f"   - 作成元: {test_data['source']}")
    
    # GUI起動指示
    print()
    print("🖥️  TechWF起動コマンド:")
    print(f"   cd {project_root}")
    print("   python main.py")
    
    return test_file

if __name__ == "__main__":
    test_file = main()
    print(f"\n📋 作成されたテストファイル: {test_file}")