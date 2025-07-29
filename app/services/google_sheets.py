"""Google Sheets integration service."""

import time
import random
from typing import Optional, Dict, Any
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)


class GoogleSheetsService:
    """Google Sheets API integration service."""
    
    def __init__(self):
        """Initialize Google Sheets service."""
        self.service = None
        self.sheet_id = settings.GOOGLE_SHEETS_ID
        
        if not self.sheet_id or self.sheet_id in ["YOUR_SHEET_ID_HERE", "your-sheet-id"]:
            raise ValueError("Google Sheets ID is not configured properly")
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            service_account_info = settings.GOOGLE_SERVICE_ACCOUNT_KEY
            
            if isinstance(service_account_info, str):
                if service_account_info.endswith('.json') and Path(service_account_info).exists():
                    credentials = service_account.Credentials.from_service_account_file(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                else:
                    import json
                    service_account_dict = json.loads(service_account_info)
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_dict,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
            else:
                raise ValueError("Invalid service account configuration")
            
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API authentication successful")
            
        except Exception as e:
            logger.error("Google Sheets API authentication failed", error=str(e))
            raise ExternalServiceError(f"Google Sheets authentication failed: {e}")
    
    def search_n_code(self, n_code: str) -> Optional[Dict[str, Any]]:
        """Search for N-code and return row information."""
        return self._execute_with_retry(self._search_n_code_impl, n_code)
    
    def _search_n_code_impl(self, n_code: str) -> Optional[Dict[str, Any]]:
        """Implementation of N-code search."""
        logger.info("Starting N-code search", n_code=n_code)
        
        range_name = 'A1:D1000'
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
        except HttpError as e:
            logger.error("Google Sheets API error", error=str(e))
            raise
        
        values = result.get('values', [])
        
        if not values:
            logger.warning("No data found in spreadsheet")
            return None
        
        for row_idx, row in enumerate(values, start=1):
            if row and len(row) > 0:
                cell_value = str(row[0]).strip().upper()
                if cell_value == n_code.upper():
                    repository_name = row[2].strip() if len(row) > 2 and row[2] else None
                    
                    if not repository_name:
                        logger.warning("No repository name in column C", row=row_idx)
                        return None
                    
                    channel_name = row[3].strip() if len(row) > 3 and row[3] else None
                    
                    result_dict = {
                        'row': row_idx,
                        'n_code': n_code,
                        'repository_name': repository_name,
                        'channel_name': channel_name or repository_name
                    }
                    
                    logger.info("N-code found", **result_dict)
                    return result_dict
        
        logger.warning("N-code not found", n_code=n_code)
        return None
    
    def _execute_with_retry(self, func, *args, max_retries: int = 3, **kwargs):
        """Execute function with retry."""
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except HttpError as e:
                if self._is_retryable_error(e) and attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("Retrying API call", attempt=attempt + 1, wait_time=wait_time)
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("API call failed", error=str(e))
                    raise
                    
            except Exception as e:
                logger.error("Unexpected error", error=str(e))
                raise
    
    def _is_retryable_error(self, error: HttpError) -> bool:
        """Check if error is retryable."""
        retryable_codes = {429, 500, 502, 503, 504}
        status_code = error.resp.status if error.resp else None
        return status_code in retryable_codes
    
    def get_repository_name(self, n_code: str) -> Optional[str]:
        """Get repository name by N-code."""
        result = self.search_n_code(n_code)
        return result['repository_name'] if result else None
    
    def get_channel_name(self, n_code: str) -> Optional[str]:
        """Get Slack channel name by N-code."""
        result = self.search_n_code(n_code)
        return result['channel_name'] if result else None
    
    def get_workflow_info(self, n_code: str) -> Optional[Dict[str, str]]:
        """Get workflow information by N-code."""
        result = self.search_n_code(n_code)
        if not result:
            return None
        
        return {
            'n_code': n_code,
            'repository_name': result['repository_name'],
            'slack_channel': result['repository_name']  # リポジトリ名と同名のチャンネル
        }
    
    def test_connection(self) -> bool:
        """Test Google Sheets connection."""
        try:
            sheet_metadata = self._execute_with_retry(
                lambda: self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            )
            
            sheet_title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
            logger.info("Connection test successful", sheet_title=sheet_title)
            return True
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False
    
    def read_cell(self, n_code: str, column: str = 'G') -> Optional[str]:
        """指定したN番号の行の指定列を読み取り"""
        result = self.search_n_code(n_code)
        if not result:
            logger.warning("N-code not found for reading", n_code=n_code)
            return None
        
        row = result['row']
        range_name = f'{column}{row}'
        
        try:
            result = self._execute_with_retry(
                lambda: self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [[]])
            if values and len(values[0]) > 0:
                cell_value = values[0][0]
                logger.info("Cell read successful", n_code=n_code, column=column, row=row, value=cell_value)
                return cell_value
            else:
                logger.info("Cell is empty", n_code=n_code, column=column, row=row)
                return ""
                
        except Exception as e:
            logger.error("Failed to read cell", n_code=n_code, column=column, row=row, error=str(e))
            return None
    
    def write_cell(self, n_code: str, value: str, column: str = 'G') -> bool:
        """指定したN番号の行の指定列に値を書き込み"""
        result = self.search_n_code(n_code)
        if not result:
            logger.warning("N-code not found for writing", n_code=n_code)
            return False
        
        row = result['row']
        range_name = f'{column}{row}'
        
        try:
            self._execute_with_retry(
                lambda: self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[value]]}
                ).execute()
            )
            
            logger.info("Cell write successful", n_code=n_code, column=column, row=row, value=value)
            return True
            
        except Exception as e:
            logger.error("Failed to write cell", n_code=n_code, column=column, row=row, value=value, error=str(e))
            return False
    
    def test_read_write(self, n_code: str, test_value: str = "test_write", column: str = 'G') -> Dict[str, Any]:
        """読み書きテストを実行"""
        logger.info("Starting read-write test", n_code=n_code, test_value=test_value, column=column)
        
        # 1. 現在の値を読み取り
        original_value = self.read_cell(n_code, column)
        if original_value is None:
            return {
                "success": False,
                "error": "Failed to read original value",
                "n_code": n_code,
                "column": column
            }
        
        # 2. テスト値を書き込み
        write_success = self.write_cell(n_code, test_value, column)
        if not write_success:
            return {
                "success": False,
                "error": "Failed to write test value",
                "n_code": n_code,
                "column": column,
                "original_value": original_value
            }
        
        # 3. 書き込まれた値を読み取り確認
        written_value = self.read_cell(n_code, column)
        if written_value != test_value:
            return {
                "success": False,
                "error": "Written value does not match expected",
                "n_code": n_code,
                "column": column,
                "original_value": original_value,
                "expected": test_value,
                "actual": written_value
            }
        
        # 4. 元の値を復元
        restore_success = self.write_cell(n_code, original_value or "", column)
        if not restore_success:
            logger.warning("Failed to restore original value", n_code=n_code, original_value=original_value)
        
        return {
            "success": True,
            "n_code": n_code,
            "column": column,
            "original_value": original_value,
            "test_value": test_value,
            "written_value": written_value,
            "restored": restore_success
        }