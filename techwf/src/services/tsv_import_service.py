"""
TSVインポートサービス
著者詳細情報のTSVファイルをインポートし、データベースとGoogle Sheetsに反映
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class TSVImportService(QObject):
    """TSVファイルインポートサービス"""
    
    # シグナル定義
    import_started = Signal()
    import_progress = Signal(int, int)  # current, total
    import_completed = Signal(int)  # imported_count
    import_error = Signal(str)
    
    # TSVカラム定義（31項目）
    TSV_COLUMNS = [
        'book_title',                   # 書名
        'twitter_account',               # ツイッターアカウント
        'github_account',                # GitHubアカウント
        'dev_environment_select',        # 制作環境（選択）
        'dev_environment_other',         # 制作環境（その他）
        'company_name',                  # 取引先名
        'company_name_kana',             # 取引先（読み）
        'postal_code',                   # 〒
        'address',                       # 住所
        'email',                         # メアド
        'phone',                         # 電話番号
        'mobile',                        # ケータイ番号
        'business_type',                 # 法人or個人
        'withholding_tax',               # 源泉徴収
        'domestic_resident',             # 国内居住？
        'bank_name',                     # 銀行名
        'branch_name',                   # 支店名
        'account_type',                  # 預金種別
        'account_number',                # 口座番号
        'account_holder',                # 口座名義
        'account_holder_kana',           # 口座名義（半角カナ）
        'copyright_name_en',             # 著作権表示する場合の英語表記
        'co_author_emails',              # 共著者メールアドレス
        'notes',                         # 備考
        'application_date',              # 申請日
        'invoice_number',                # インボイス番号
        'tax_status',                    # 課税事業者か非か税業者か
        'pen_name',                      # ペンネーム
        'pen_name_kana',                 # ペンネーム（ふりがな）
        'profile_text',                  # 書籍巻末掲載のプロフィール文
        'notes2'                         # 備考2
    ]
    
    # Google Sheets列マッピング（L列から開始、書名は除外）
    SHEET_COLUMN_MAPPING = {
        'twitter_account': 'L',
        'github_account': 'M',
        'dev_environment_select': 'N',
        'dev_environment_other': 'O',
        'company_name': 'P',
        'company_name_kana': 'Q',
        'postal_code': 'R',
        'address': 'S',
        'email': 'T',
        'phone': 'U',
        'mobile': 'V',
        'business_type': 'W',
        'withholding_tax': 'X',
        'domestic_resident': 'Y',
        'bank_name': 'Z',
        'branch_name': 'AA',
        'account_type': 'AB',
        'account_number': 'AC',
        'account_holder': 'AD',
        'account_holder_kana': 'AE',
        'copyright_name_en': 'AF',
        'co_author_emails': 'AG',
        'notes': 'AH',
        'application_date': 'AI',
        'invoice_number': 'AJ',
        'tax_status': 'AK',
        'pen_name': 'AL',
        'pen_name_kana': 'AM',
        'profile_text': 'AN',
        'notes2': 'AO'
    }
    
    def __init__(self, repository=None, sheets_service=None):
        super().__init__()
        self.repository = repository
        self.sheets_service = sheets_service
        
    def import_tsv(self, file_path: str) -> Tuple[bool, str, List[Dict]]:
        """
        TSVファイルをインポート
        
        Args:
            file_path: TSVファイルパス
            
        Returns:
            (成功フラグ, メッセージ, インポートデータリスト)
        """
        try:
            self.import_started.emit()
            
            # ファイル存在確認
            if not Path(file_path).exists():
                error_msg = f"ファイルが見つかりません: {file_path}"
                self.import_error.emit(error_msg)
                return False, error_msg, []
                
            # TSV読み込み
            authors_data = self._parse_tsv(file_path)
            if not authors_data:
                error_msg = "TSVファイルが空または形式が不正です"
                self.import_error.emit(error_msg)
                return False, error_msg, []
                
            # データ処理 - バッチトランザクション対応
            processed_count = 0
            total_count = len(authors_data)
            
            # データベース保存はバッチトランザクション内で実行
            if self.repository:
                try:
                    # 全データをバッチトランザクション内で処理
                    with self.repository._get_connection() as conn:
                        for idx, author_data in enumerate(authors_data):
                            # 進捗通知
                            self.import_progress.emit(idx + 1, total_count)
                            
                            # データベース保存（既存の接続を使用）
                            self._save_to_database_with_connection(author_data, conn)
                            processed_count += 1
                            
                        # バッチコミット（withブロック終了時に自動実行）
                        logger.info(f"バッチトランザクション完了: {processed_count}件の著者データを保存")
                        
                except Exception as e:
                    # バッチ全体のロールバック（withブロックで自動実行）
                    logger.error(f"バッチトランザクションエラー: {e}")
                    raise
            
            # Google Sheets同期は個別に実行（外部APIのため）
            if self.sheets_service:
                sheets_success_count = 0
                for idx, author_data in enumerate(authors_data):
                    try:
                        self._sync_to_sheets(author_data)
                        sheets_success_count += 1
                    except Exception as e:
                        logger.warning(f"行{author_data.get('source_row', idx)}のSheets同期でエラー: {e}")
                        # Sheets同期エラーは処理継続
                        continue
                        
                logger.info(f"Sheets同期完了: {sheets_success_count}/{len(authors_data)}件成功")
                
            # 完了通知
            self.import_completed.emit(processed_count)
            success_msg = f"{processed_count}件のデータをインポートしました"
            return True, success_msg, authors_data
            
        except Exception as e:
            error_msg = f"インポートエラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.import_error.emit(error_msg)
            return False, error_msg, []
            
    def _parse_tsv(self, file_path: str) -> List[Dict]:
        """
        TSVファイルをパース
        
        Args:
            file_path: TSVファイルパス
            
        Returns:
            パースしたデータのリスト
        """
        authors_data = []
        
        try:
            # UTF-8 BOM付きで読み込み
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                for row_num, row in enumerate(reader, start=2):  # ヘッダー行を1行目とする
                    try:
                        # データ変換
                        author_data = self._convert_row_data(row, row_num)
                        if author_data:
                            authors_data.append(author_data)
                    except Exception as e:
                        logger.warning(f"行{row_num}の処理でエラー: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"TSVファイル読み込みエラー: {e}")
            raise
            
        return authors_data
        
    def _convert_row_data(self, row: Dict, row_num: int) -> Optional[Dict]:
        """
        TSV行データを内部形式に変換
        
        Args:
            row: TSV行データ
            row_num: 行番号（エラー報告用）
            
        Returns:
            変換後のデータ（エラーの場合None）
        """
        try:
            # ヘッダー名の正規化（TSVのヘッダーと内部カラム名のマッピング）
            header_mapping = {
                '書名': 'book_title',
                'ツイッターアカウント': 'twitter_account',
                'GitHubアカウント': 'github_account',
                '制作環境（選択）': 'dev_environment_select',
                '制作環境（その他）': 'dev_environment_other',
                '取引先名': 'company_name',
                '取引先（読み）': 'company_name_kana',
                '〒': 'postal_code',
                '住所': 'address',
                'メアド': 'email',
                '電話番号': 'phone',
                'ケータイ番号': 'mobile',
                '法人or個人': 'business_type',
                '源泉徴収': 'withholding_tax',
                '国内居住？': 'domestic_resident',
                '銀行名': 'bank_name',
                '支店名': 'branch_name',
                '預金種別': 'account_type',
                '口座番号': 'account_number',
                '口座名義': 'account_holder',
                '口座名義（半角カナ）': 'account_holder_kana',
                '著作権表示する場合の英語表記': 'copyright_name_en',
                '共著者メールアドレス': 'co_author_emails',
                '備考': 'notes',
                '申請日': 'application_date',
                'インボイス番号：Tを加えた12桁の数字（課税事業者のみ）': 'invoice_number',
                '課税事業者か非か税業者か': 'tax_status',
                'ペンネーム': 'pen_name',
                'ペンネーム（ふりがな）': 'pen_name_kana',
                '書籍巻末掲載のプロフィール文（200字程度）': 'profile_text',
            }
            
            # データ変換
            author_data = {}
            for tsv_header, internal_name in header_mapping.items():
                value = row.get(tsv_header, '').strip()
                author_data[internal_name] = value
                
            # 備考2の処理（同じヘッダー名が2つある場合）
            if '備考' in row:
                # 2番目の備考を備考2として扱う
                notes_values = [v for k, v in row.items() if k == '備考']
                if len(notes_values) > 1:
                    author_data['notes2'] = notes_values[1].strip()
                else:
                    author_data['notes2'] = ''
                    
            # バリデーション
            if not self._validate_author_data(author_data, row_num):
                return None
                
            # メタデータ追加
            author_data['imported_at'] = datetime.now().isoformat()
            author_data['source_row'] = row_num
            
            return author_data
            
        except Exception as e:
            logger.error(f"行{row_num}のデータ変換エラー: {e}")
            return None
            
    def _validate_author_data(self, data: Dict, row_num: int) -> bool:
        """
        著者データのバリデーション
        
        Args:
            data: 著者データ
            row_num: 行番号
            
        Returns:
            検証成功フラグ
        """
        # 必須項目チェック（書名は必須）
        if not data.get('book_title'):
            logger.warning(f"行{row_num}: 書名が未入力です")
            return False
            
        # メールアドレス形式チェック
        email = data.get('email', '')
        if email and '@' not in email:
            logger.warning(f"行{row_num}: 不正なメールアドレス形式: {email}")
            
        # 郵便番号形式チェック
        postal_code = data.get('postal_code', '')
        if postal_code:
            # ハイフンを除去して数字のみに
            postal_code_digits = postal_code.replace('-', '').replace('〒', '')
            if not postal_code_digits.isdigit() or len(postal_code_digits) != 7:
                logger.warning(f"行{row_num}: 不正な郵便番号形式: {postal_code}")
                
        # インボイス番号形式チェック
        invoice_number = data.get('invoice_number', '')
        if invoice_number:
            if not invoice_number.startswith('T') or len(invoice_number) != 13:
                logger.warning(f"行{row_num}: 不正なインボイス番号形式: {invoice_number}")
                
        return True
        
    def _save_to_database_with_connection(self, author_data: Dict, conn):
        """
        データベースに保存（既存の接続を使用）
        
        Args:
            author_data: 著者データ
            conn: 既存のデータベース接続
        """
        try:
            # バリデーション - 必須フィールドチェック
            if not author_data.get('book_title'):
                raise ValueError("書名が設定されていません")
                
            # author_masterテーブルへのUPSERT処理
            # SQLite UPSERT文を使用してINSERT OR UPDATE
            sql = """
                INSERT INTO author_master (
                    twitter_account, github_account, dev_environment_select, dev_environment_other,
                    company_name, company_name_kana, postal_code, address, email, phone, mobile,
                    business_type, withholding_tax, domestic_resident, bank_name, branch_name,
                    account_type, account_number, account_holder, account_holder_kana,
                    copyright_name_en, co_author_emails, notes, application_date, invoice_number,
                    tax_status, pen_name, pen_name_kana, profile_text, notes2,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(email) DO UPDATE SET
                    twitter_account = excluded.twitter_account,
                    github_account = excluded.github_account,
                    dev_environment_select = excluded.dev_environment_select,
                    dev_environment_other = excluded.dev_environment_other,
                    company_name = excluded.company_name,
                    company_name_kana = excluded.company_name_kana,
                    postal_code = excluded.postal_code,
                    address = excluded.address,
                    phone = excluded.phone,
                    mobile = excluded.mobile,
                    business_type = excluded.business_type,
                    withholding_tax = excluded.withholding_tax,
                    domestic_resident = excluded.domestic_resident,
                    bank_name = excluded.bank_name,
                    branch_name = excluded.branch_name,
                    account_type = excluded.account_type,
                    account_number = excluded.account_number,
                    account_holder = excluded.account_holder,
                    account_holder_kana = excluded.account_holder_kana,
                    copyright_name_en = excluded.copyright_name_en,
                    co_author_emails = excluded.co_author_emails,
                    notes = excluded.notes,
                    application_date = excluded.application_date,
                    invoice_number = excluded.invoice_number,
                    tax_status = excluded.tax_status,
                    pen_name = excluded.pen_name,
                    pen_name_kana = excluded.pen_name_kana,
                    profile_text = excluded.profile_text,
                    notes2 = excluded.notes2,
                    updated_at = datetime('now')
            """
            
            # パラメータ準備
            params = (
                author_data.get('twitter_account', ''),
                author_data.get('github_account', ''),
                author_data.get('dev_environment_select', ''),
                author_data.get('dev_environment_other', ''),
                author_data.get('company_name', ''),
                author_data.get('company_name_kana', ''),
                author_data.get('postal_code', ''),
                author_data.get('address', ''),
                author_data.get('email', ''),
                author_data.get('phone', ''),
                author_data.get('mobile', ''),
                author_data.get('business_type', ''),
                author_data.get('withholding_tax', ''),
                author_data.get('domestic_resident', ''),
                author_data.get('bank_name', ''),
                author_data.get('branch_name', ''),
                author_data.get('account_type', ''),
                author_data.get('account_number', ''),
                author_data.get('account_holder', ''),
                author_data.get('account_holder_kana', ''),
                author_data.get('copyright_name_en', ''),
                author_data.get('co_author_emails', ''),
                author_data.get('notes', ''),
                author_data.get('application_date', ''),
                author_data.get('invoice_number', ''),
                author_data.get('tax_status', ''),
                author_data.get('pen_name', ''),
                author_data.get('pen_name_kana', ''),
                author_data.get('profile_text', ''),
                author_data.get('notes2', '')
            )
            
            # 既存の接続を使用して実行
            cursor = conn.cursor()
            cursor.execute(sql, params)
            
            # 挿入されたレコードのIDを取得
            if cursor.lastrowid:
                logger.debug(f"著者データ保存完了 (ID: {cursor.lastrowid}): {author_data.get('book_title')}")
            else:
                logger.debug(f"著者データ更新完了: {author_data.get('book_title')}")
                
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
            # エラー情報をより詳細に記録
            logger.error(f"Failed to save author data: {author_data.get('book_title', 'Unknown')}")
            logger.error(f"Error details: {str(e)}", exc_info=True)
            raise
        
    def _save_to_database(self, author_data: Dict):
        """
        データベースに保存
        
        Args:
            author_data: 著者データ
        """
        try:
            if not self.repository:
                logger.warning("Repository is not configured, skipping database save")
                return
                
            # バリデーション - 必須フィールドチェック
            if not author_data.get('book_title'):
                raise ValueError("書名が設定されていません")
                
            # author_masterテーブルへのUPSERT処理
            # SQLite UPSERT文を使用してINSERT OR UPDATE
            sql = """
                INSERT INTO author_master (
                    twitter_account, github_account, dev_environment_select, dev_environment_other,
                    company_name, company_name_kana, postal_code, address, email, phone, mobile,
                    business_type, withholding_tax, domestic_resident, bank_name, branch_name,
                    account_type, account_number, account_holder, account_holder_kana,
                    copyright_name_en, co_author_emails, notes, application_date, invoice_number,
                    tax_status, pen_name, pen_name_kana, profile_text, notes2,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(email) DO UPDATE SET
                    twitter_account = excluded.twitter_account,
                    github_account = excluded.github_account,
                    dev_environment_select = excluded.dev_environment_select,
                    dev_environment_other = excluded.dev_environment_other,
                    company_name = excluded.company_name,
                    company_name_kana = excluded.company_name_kana,
                    postal_code = excluded.postal_code,
                    address = excluded.address,
                    phone = excluded.phone,
                    mobile = excluded.mobile,
                    business_type = excluded.business_type,
                    withholding_tax = excluded.withholding_tax,
                    domestic_resident = excluded.domestic_resident,
                    bank_name = excluded.bank_name,
                    branch_name = excluded.branch_name,
                    account_type = excluded.account_type,
                    account_number = excluded.account_number,
                    account_holder = excluded.account_holder,
                    account_holder_kana = excluded.account_holder_kana,
                    copyright_name_en = excluded.copyright_name_en,
                    co_author_emails = excluded.co_author_emails,
                    notes = excluded.notes,
                    application_date = excluded.application_date,
                    invoice_number = excluded.invoice_number,
                    tax_status = excluded.tax_status,
                    pen_name = excluded.pen_name,
                    pen_name_kana = excluded.pen_name_kana,
                    profile_text = excluded.profile_text,
                    notes2 = excluded.notes2,
                    updated_at = datetime('now')
            """
            
            # パラメータ準備
            params = (
                author_data.get('twitter_account', ''),
                author_data.get('github_account', ''),
                author_data.get('dev_environment_select', ''),
                author_data.get('dev_environment_other', ''),
                author_data.get('company_name', ''),
                author_data.get('company_name_kana', ''),
                author_data.get('postal_code', ''),
                author_data.get('address', ''),
                author_data.get('email', ''),
                author_data.get('phone', ''),
                author_data.get('mobile', ''),
                author_data.get('business_type', ''),
                author_data.get('withholding_tax', ''),
                author_data.get('domestic_resident', ''),
                author_data.get('bank_name', ''),
                author_data.get('branch_name', ''),
                author_data.get('account_type', ''),
                author_data.get('account_number', ''),
                author_data.get('account_holder', ''),
                author_data.get('account_holder_kana', ''),
                author_data.get('copyright_name_en', ''),
                author_data.get('co_author_emails', ''),
                author_data.get('notes', ''),
                author_data.get('application_date', ''),
                author_data.get('invoice_number', ''),
                author_data.get('tax_status', ''),
                author_data.get('pen_name', ''),
                author_data.get('pen_name_kana', ''),
                author_data.get('profile_text', ''),
                author_data.get('notes2', '')
            )
            
            # トランザクション内で実行
            with self.repository._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                
                # 挿入されたレコードのIDを取得
                if cursor.lastrowid:
                    logger.debug(f"著者データ保存完了 (ID: {cursor.lastrowid}): {author_data.get('book_title')}")
                else:
                    logger.debug(f"著者データ更新完了: {author_data.get('book_title')}")
                
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
            # エラー情報をより詳細に記録
            logger.error(f"Failed to save author data: {author_data.get('book_title', 'Unknown')}")
            logger.error(f"Error details: {str(e)}", exc_info=True)
            raise
            
    def _sync_to_sheets(self, author_data: Dict):
        """
        Google Sheetsに同期
        
        Args:
            author_data: 著者データ
        """
        try:
            if not self.sheets_service:
                logger.warning("Sheets service is not configured, skipping sheets sync")
                return
                
            # サービスが有効かチェック
            if not getattr(self.sheets_service, 'is_enabled', True):
                logger.warning("Google Sheets service is disabled, skipping sync")
                return
                
            # 書名を使って既存行を検索
            book_title = author_data.get('book_title', '')
            if not book_title:
                logger.warning("書名が空のためSheets同期をスキップします")
                return
                
            # エラーハンドリング付きでシート操作を実行
            def _perform_sync():
                # L列以降にデータを転記（書名は除外）
                row_data = []
                for column_name, sheet_column in self.SHEET_COLUMN_MAPPING.items():
                    value = author_data.get(column_name, '')
                    # 空文字の場合は明示的に空文字列を設定
                    row_data.append(str(value) if value is not None else '')
                
                # 書名で既存行を検索（A列と仮定）
                existing_row = None
                try:
                    # sheets_serviceがfind_row_by_valueメソッドを持つ場合
                    if hasattr(self.sheets_service, 'operations') and hasattr(self.sheets_service.operations, 'find_row_by_value'):
                        existing_row = self.sheets_service.operations.find_row_by_value(
                            self.sheets_service.spreadsheet_id,
                            self.sheets_service.worksheet_name,
                            1,  # A列（1列目）で書名を検索
                            book_title
                        )
                except Exception as e:
                    logger.debug(f"既存行検索でエラー（新規行として処理）: {e}")
                    
                # データ更新/追加処理
                if existing_row:
                    # 既存行を更新
                    try:
                        # L列からAO列までの範囲を更新
                        range_name = f"{getattr(self.sheets_service, 'worksheet_name', 'Sheet1')}!L{existing_row}:AO{existing_row}"
                        if hasattr(self.sheets_service, 'operations') and hasattr(self.sheets_service.operations, 'update_range'):
                            self.sheets_service.operations.update_range(
                                self.sheets_service.spreadsheet_id,
                                range_name,
                                [row_data]
                            )
                            logger.info(f"Sheets行更新完了 (行{existing_row}): {book_title}")
                    except Exception as e:
                        logger.error(f"Sheets行更新エラー: {e}")
                        raise
                else:
                    # 新規行を追加
                    try:
                        # 書名を含む全データ行を準備（A列から）
                        full_row_data = [book_title] + [''] * 10 + row_data  # A列書名 + B-K列空白 + L-AO列データ
                        if hasattr(self.sheets_service, 'operations') and hasattr(self.sheets_service.operations, 'append_rows'):
                            self.sheets_service.operations.append_rows(
                                self.sheets_service.spreadsheet_id,
                                getattr(self.sheets_service, 'worksheet_name', 'Sheet1'),
                                [full_row_data]
                            )
                            logger.info(f"Sheets新規行追加完了: {book_title}")
                    except Exception as e:
                        logger.error(f"Sheets新規行追加エラー: {e}")
                        raise
                        
            # リトライ機能付きで実行
            if hasattr(self.sheets_service, 'error_handler') and hasattr(self.sheets_service.error_handler, 'with_retry'):
                # エラーハンドラーのリトライ機能を使用
                retry_wrapper = self.sheets_service.error_handler.with_retry
                retry_wrapper(_perform_sync)()
            else:
                # 直接実行
                _perform_sync()
                
        except Exception as e:
            logger.error(f"Sheets同期エラー: {e}")
            logger.error(f"Failed to sync to sheets: {author_data.get('book_title', 'Unknown')}")
            logger.error(f"Error details: {str(e)}", exc_info=True)
            # Sheets同期エラーは警告として扱い、処理は継続
            logger.warning("Sheets同期に失敗しましたが、処理を継続します")