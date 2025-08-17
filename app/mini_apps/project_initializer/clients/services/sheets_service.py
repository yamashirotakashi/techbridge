"""Google Sheets Service - Google Sheets API操作サービス"""
import logging
from typing import Optional, Dict, Any, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class SheetsService:
    """Google Sheets API操作を担当するサービスクラス"""
    
    def __init__(self, service_account_key: Optional[str] = None,
                 spreadsheet_id: Optional[str] = None):
        """Google Sheetsサービスの初期化
        
        Args:
            service_account_key: サービスアカウントキーのパス
            spreadsheet_id: 対象のスプレッドシートID
        """
        self.service_account_key = service_account_key
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service = None
        
        if service_account_key:
            try:
                creds = Credentials.from_service_account_file(
                    service_account_key,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.sheets_service = build('sheets', 'v4', credentials=creds)
                logger.info("Google Sheets service initialized successfully")
            except Exception as e:
                logger.error(f"Google Sheets service initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Google Sheetsサービスの利用可能状態を確認"""
        return self.sheets_service is not None and self.spreadsheet_id is not None
    
    def get_project_info(self, n_code: str) -> Optional[Dict[str, Any]]:
        """N-codeからプロジェクト情報を取得
        
        Args:
            n_code: プロジェクトのN-code
            
        Returns:
            プロジェクト情報の辞書、見つからない場合はNone
        """
        if not self.is_available():
            logger.warning("Google Sheets service not available")
            return None
            
        try:
            # プロジェクト情報シートから検索
            range_name = 'プロジェクト!A:Z'
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
                
            # ヘッダー行を取得
            headers = values[0]
            n_code_index = headers.index('Nコード') if 'Nコード' in headers else -1
            
            if n_code_index == -1:
                logger.error("N-code column not found in sheet")
                return None
                
            # N-codeで検索
            for row in values[1:]:
                if len(row) > n_code_index and row[n_code_index] == n_code:
                    # 行データを辞書に変換
                    project_info = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            project_info[header] = row[i]
                    return project_info
                    
            logger.info(f"Project not found for N-code: {n_code}")
            return None
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_project_info: {e}")
            return None
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスクIDからタスク情報を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク情報の辞書、見つからない場合はNone
        """
        if not self.is_available():
            logger.warning("Google Sheets service not available")
            return None
            
        try:
            # タスクシートから検索
            range_name = 'タスク!A:Z'
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
                
            # ヘッダー行を取得
            headers = values[0]
            task_id_index = headers.index('タスクID') if 'タスクID' in headers else -1
            
            if task_id_index == -1:
                logger.error("Task ID column not found in sheet")
                return None
                
            # タスクIDで検索
            for row in values[1:]:
                if len(row) > task_id_index and row[task_id_index] == task_id:
                    # 行データを辞書に変換
                    task_info = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            task_info[header] = row[i]
                    return task_info
                    
            logger.info(f"Task not found for ID: {task_id}")
            return None
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_task_info: {e}")
            return None
    
    def create_task_record(self, task_data: Dict[str, Any]) -> bool:
        """新しいタスクレコードを作成
        
        Args:
            task_data: タスクデータの辞書
            
        Returns:
            成功時True、失敗時False
        """
        if not self.is_available():
            logger.warning("Google Sheets service not available")
            return False
            
        try:
            # タスクシートのヘッダーを取得
            range_name = 'タスク!A1:Z1'
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            headers = result.get('values', [[]])[0]
            if not headers:
                logger.error("Task sheet headers not found")
                return False
                
            # データ行を作成
            row_data = []
            for header in headers:
                value = task_data.get(header, '')
                row_data.append(str(value))
                
            # 新しい行を追加
            body = {'values': [row_data]}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='タスク!A:Z',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Task record created successfully")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in create_task_record: {e}")
            return False
    
    def sync_project_tasks(self, project_id: str, task_ids: List[str]) -> bool:
        """プロジェクトとタスクの関連を同期
        
        Args:
            project_id: プロジェクトID
            task_ids: 関連付けるタスクIDのリスト
            
        Returns:
            成功時True、失敗時False
        """
        if not self.is_available():
            logger.warning("Google Sheets service not available")
            return False
            
        try:
            # プロジェクト-タスク関連シートに記録
            values = []
            for task_id in task_ids:
                values.append([project_id, task_id])
                
            body = {'values': values}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='プロジェクトタスク!A:B',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Project-task sync completed for project {project_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in sync_project_tasks: {e}")
            return False
    
    def sync_purchase_list_urls(self, project_id: str, urls: Dict[str, str]) -> bool:
        """購入リストURLを同期
        
        Args:
            project_id: プロジェクトID
            urls: ストア名とURLの辞書
            
        Returns:
            成功時True、失敗時False
        """
        if not self.is_available():
            logger.warning("Google Sheets service not available")
            return False
            
        try:
            # 購入リストシートに記録
            values = []
            for store_name, url in urls.items():
                values.append([project_id, store_name, url])
                
            body = {'values': values}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='購入リスト!A:C',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Purchase list URLs synced for project {project_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in sync_purchase_list_urls: {e}")
            return False