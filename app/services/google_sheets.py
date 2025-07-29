"""Google Sheets integration service."""

import json
import logging
from typing import Any, Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service for Google Sheets integration."""

    def __init__(self):
        self.spreadsheet_id = settings.GOOGLE_SHEETS_ID
        self.service = self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Sheets API service."""
        try:
            # Parse service account credentials
            if settings.GOOGLE_SERVICE_ACCOUNT_KEY.startswith("{"):
                # JSON string
                credentials_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY)
            else:
                # File path
                with open(settings.GOOGLE_SERVICE_ACCOUNT_KEY, "r") as f:
                    credentials_info = json.load(f)

            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            )

            service = build("sheets", "v4", credentials=credentials)
            return service

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            return None

    async def get_slack_channel(self, n_number: str) -> Optional[str]:
        """Get Slack channel name for given N-number from Google Sheets."""
        if not self.service:
            return None

        try:
            # Assuming the sheet has columns: Nj÷ | ¿¤Èë | SlackÁãóÍë
            # Adjust range based on actual sheet structure
            range_name = "Sheet1!A:C"
            
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            
            if not values:
                return None

            # Find the row with matching N-number
            # Assuming first row is header
            for row in values[1:]:
                if len(row) >= 3 and row[0] == n_number:
                    channel = row[2].strip()
                    # Ensure channel name starts with #
                    if channel and not channel.startswith("#"):
                        channel = f"#{channel}"
                    return channel

            return None

        except HttpError as e:
            logger.error(f"Google Sheets API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to get Slack channel from sheets: {str(e)}")
            return None

    async def get_all_mappings(self) -> Dict[str, str]:
        """Get all N-number to Slack channel mappings."""
        if not self.service:
            return {}

        try:
            range_name = "Sheet1!A:C"
            
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            
            if not values:
                return {}

            mappings = {}
            
            # Skip header row
            for row in values[1:]:
                if len(row) >= 3:
                    n_number = row[0].strip()
                    channel = row[2].strip()
                    if n_number and channel:
                        # Ensure channel name starts with #
                        if not channel.startswith("#"):
                            channel = f"#{channel}"
                        mappings[n_number] = channel

            return mappings

        except Exception as e:
            logger.error(f"Failed to get all mappings: {str(e)}")
            return {}

    async def update_status_in_sheet(
        self, 
        n_number: str, 
        status: str,
        column_index: int = 3,  # Assuming status is in column D (0-indexed = 3)
    ) -> bool:
        """Update status in Google Sheets (if write access is granted)."""
        if not self.service:
            return False

        try:
            # Find the row with the N-number
            range_name = "Sheet1!A:A"
            
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            
            row_index = None
            for i, row in enumerate(values):
                if row and row[0] == n_number:
                    row_index = i + 1  # 1-indexed for Sheets API
                    break

            if row_index is None:
                logger.warning(f"N-number {n_number} not found in sheet")
                return False

            # Update the status cell
            cell_range = f"Sheet1!{chr(65 + column_index)}{row_index}"
            
            body = {"values": [[status]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption="RAW",
                body=body,
            ).execute()

            logger.info(f"Updated status for {n_number} to {status}")
            return True

        except HttpError as e:
            if e.resp.status == 403:
                logger.warning("No write access to Google Sheets")
            else:
                logger.error(f"Google Sheets API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to update status in sheet: {str(e)}")
            return False