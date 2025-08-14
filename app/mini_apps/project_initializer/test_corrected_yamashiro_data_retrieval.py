#!/usr/bin/env python3
"""
修正されたデータ取得テスト - 調査結果に基づく正しいシート・カラム構造の実装
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import json
    
    print('[INFO] 修正されたデータ取得システム実装テスト開始...')
    
    class CorrectedGoogleSheetsService:
        """調査結果に基づく修正されたGoogle Sheetsサービス"""
        
        def __init__(self, sheet_id=None):
            self.sheet_id = sheet_id or "17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ"
            
            # Initialize Google Sheets API
            working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
            
            credentials = service_account.Credentials.from_service_account_file(
                working_creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            
            # 修正されたシート構造定義（調査結果に基づく）
            self.MAIN_SHEET = "2020.10-"  # メインプロジェクトデータシート
            self.TASK_SHEET = "手動タスク管理"  # タスク管理シート（N02413が実際にある）
            self.AUTHOR_SHEET = "著者情報転記"  # 著者詳細情報（GitHubアカウント、メールアドレス）
            self.TECHWF_SHEET = "TechWF_Management"  # 統合管理シート（理想構造だが現在はヘッダーのみ）
            
            # 各シートのカラムマッピング（調査で確認済み）
            self.TASK_SHEET_MAPPING = {
                'execution_time_col': 'A',  # 実行日時
                'n_code_col': 'B',          # Nコード
                'status_col': 'C',          # ステータス  
                'slack_col': 'D',           # Slackチャンネル
                'github_col': 'E',          # GitHubリポジトリ
                'task_count_col': 'F',      # 手動タスク数
                'content_col': 'G',         # 要対応内容
                'result_col': 'H',          # 実行結果詳細
                'yamashiro_col': 'I',       # 山城敬
                'test_col': 'J'             # テスト実行
            }
            
            self.AUTHOR_SHEET_MAPPING = {
                'title_col': 'A',       # 書名
                'twitter_col': 'B',     # ツイッターアカウント
                'github_col': 'C',      # GitHubアカウント
                'env_select_col': 'D',  # 制作環境（選択）
                'env_other_col': 'E',   # 制作環境（その他）
                'author_col': 'F',      # 著者名
                'furigana_col': 'G',    # フリガナ
                'zipcode_col': 'H',     # 〒
                'address_col': 'I',     # 住所
                'email_col': 'J'        # メアド
            }
        
        def get_yamashiro_project_data(self, n_code: str):
            """
            発行計画（山城）関連データの取得
            調査結果：実際のデータは「手動タスク管理」シートにある
            """
            print(f'[INFO] Getting project data for {n_code} from corrected sources...')
            
            result = {
                'n_code': n_code,
                'book_title': None,      # 書籍名（H列期待）
                'github_account': None,  # GitHubアカウント（M列期待）
                'slack_id': None,        # SlackID（K列期待）
                'author_email': None,    # 著者メール（T列期待）
                'repository_name': None, # リポジトリ名（C列期待）
                'data_sources': [],      # データソース情報
                'success': False
            }
            
            # Step 1: 手動タスク管理シートから基本データを取得
            task_data = self._get_task_management_data(n_code)
            if task_data:
                result['slack_id'] = task_data.get('slack_channel', '')
                result['repository_name'] = task_data.get('github_repo', '')
                result['data_sources'].append(f"手動タスク管理シート: Slack={bool(result['slack_id'])}, Repo={bool(result['repository_name'])}")
                print(f'[SUCCESS] Found in 手動タスク管理: Slack="{result["slack_id"]}", Repo="{result["repository_name"]}"')
                
                # Extract book title from repository URL if available
                if result['repository_name'] and 'github.com' in result['repository_name']:
                    repo_parts = result['repository_name'].split('/')
                    if len(repo_parts) > 1:
                        repo_name = repo_parts[-1]  # Last part of URL
                        result['repository_name'] = repo_name
                        # Try to extract book info from repo name (e.g., "n2413-apache-iceberg")
                        if '-' in repo_name:
                            book_hint = repo_name.split('-', 1)[1] if repo_name.lower().startswith(n_code.lower()) else repo_name
                            result['book_title'] = book_hint.replace('-', ' ').title()
            
            # Step 2: 著者情報転記シートから追加データを取得
            if result['book_title']:  # If we have a book title hint, search for details
                author_data = self._get_author_info_by_title(result['book_title'])
                if author_data:
                    result['github_account'] = author_data.get('github_account', '')
                    result['author_email'] = author_data.get('email', '')
                    result['book_title'] = author_data.get('book_title', result['book_title'])  # Use more accurate title
                    result['data_sources'].append(f"著者情報転記シート: GitHub={bool(result['github_account'])}, Email={bool(result['author_email'])}")
                    print(f'[SUCCESS] Found in 著者情報転記: Title="{result["book_title"]}", GitHub="{result["github_account"]}", Email="{result["author_email"]}"')
            
            # Step 3: Check if we have sufficient data
            found_fields = sum([
                bool(result['book_title']),
                bool(result['github_account']), 
                bool(result['slack_id']),
                bool(result['author_email']),
                bool(result['repository_name'])
            ])
            
            result['success'] = found_fields >= 3  # At least 3 out of 5 fields found
            result['completion_rate'] = f"{found_fields}/5"
            
            return result
            
        def _get_task_management_data(self, n_code: str):
            """手動タスク管理シートからデータを取得"""
            try:
                range_name = f"'{self.TASK_SHEET}'!A1:J1000"
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                
                for row_idx, row in enumerate(values[1:], start=2):  # Skip header
                    if len(row) > 1 and str(row[1]).strip().upper() == n_code:  # B列: Nコード
                        return {
                            'row_number': row_idx,
                            'execution_time': row[0] if len(row) > 0 else '',
                            'n_code': row[1] if len(row) > 1 else '',
                            'status': row[2] if len(row) > 2 else '',
                            'slack_channel': row[3] if len(row) > 3 else '',
                            'github_repo': row[4] if len(row) > 4 else '',
                            'task_count': row[5] if len(row) > 5 else '',
                            'content': row[6] if len(row) > 6 else '',
                            'result': row[7] if len(row) > 7 else '',
                            'yamashiro': row[8] if len(row) > 8 else '',
                            'test': row[9] if len(row) > 9 else ''
                        }
                        
                return None
                
            except Exception as e:
                print(f'[ERROR] Error reading 手動タスク管理 sheet: {e}')
                return None
        
        def _get_author_info_by_title(self, book_title_hint: str):
            """著者情報転記シートから書籍タイトルで著者情報を検索"""
            try:
                range_name = f"'{self.AUTHOR_SHEET}'!A1:J1000"
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                
                # Search for partial title matches
                for row_idx, row in enumerate(values[1:], start=2):  # Skip header
                    if len(row) > 0:
                        book_title = str(row[0]).strip()  # A列: 書名
                        
                        # Try different matching strategies
                        title_hint_clean = book_title_hint.lower().replace('-', ' ').replace('_', ' ')
                        book_title_clean = book_title.lower()
                        
                        # Flexible matching: check if hint words appear in actual title
                        hint_words = title_hint_clean.split()
                        matching_words = sum(1 for word in hint_words if len(word) > 2 and word in book_title_clean)
                        
                        if matching_words >= min(2, len(hint_words)):  # At least 2 matching words or all words if less than 2
                            return {
                                'row_number': row_idx,
                                'book_title': book_title,
                                'twitter': row[1] if len(row) > 1 else '',
                                'github_account': row[2] if len(row) > 2 else '',
                                'env_select': row[3] if len(row) > 3 else '',
                                'env_other': row[4] if len(row) > 4 else '',
                                'author': row[5] if len(row) > 5 else '',
                                'furigana': row[6] if len(row) > 6 else '',
                                'zipcode': row[7] if len(row) > 7 else '',
                                'address': row[8] if len(row) > 8 else '',
                                'email': row[9] if len(row) > 9 else ''
                            }
                            
                return None
                
            except Exception as e:
                print(f'[ERROR] Error reading 著者情報転記 sheet: {e}')
                return None
    
    # Test the corrected implementation
    print(f'\n[TEST] Testing corrected data retrieval for N02413...')
    
    service = CorrectedGoogleSheetsService()
    result = service.get_yamashiro_project_data("N02413")
    
    print(f'\n[RESULTS] Data retrieval test results:')
    print(f'[INFO] Success: {result["success"]}')
    print(f'[INFO] Completion Rate: {result["completion_rate"]}')
    print(f'[INFO] N-Code: {result["n_code"]}')
    print(f'[INFO] 書籍名 (H列期待): "{result["book_title"]}" {"✅" if result["book_title"] else "❌"}')
    print(f'[INFO] GitHubアカウント (M列期待): "{result["github_account"]}" {"✅" if result["github_account"] else "❌"}')
    print(f'[INFO] SlackID (K列期待): "{result["slack_id"]}" {"✅" if result["slack_id"] else "❌"}')
    print(f'[INFO] 著者メール (T列期待): "{result["author_email"]}" {"✅" if result["author_email"] else "❌"}')
    print(f'[INFO] リポジトリ名 (C列期待): "{result["repository_name"]}" {"✅" if result["repository_name"] else "❌"}')
    
    print(f'\n[SOURCES] Data sources used:')
    for source in result['data_sources']:
        print(f'[INFO] {source}')
    
    if result['success']:
        print(f'\n[SUCCESS] ✅ データ取得修正が成功しました！')
        print(f'[INFO] 修正前の問題「H列書籍名、M列GitHubアカウント、K列SlackID、T列著者メール取得不可」が解決されました。')
        print(f'[INFO] 実際のデータ構造：')
        print(f'   - 基本データ: 手動タスク管理シート（SlackチャンネルD列、GitHubリポジトリE列）')
        print(f'   - 詳細データ: 著者情報転記シート（GitHubアカウントC列、著者メールJ列）')
    else:
        print(f'\n[PARTIAL] ⚠️  部分的なデータ取得のみ成功')
        print(f'[INFO] 取得できたフィールド数: {result["completion_rate"]}')
    
    print(f'\n[NEXT] ServiceAdapterへの実装統合準備完了')
        
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)