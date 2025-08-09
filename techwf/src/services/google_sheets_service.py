#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets Service Facade
=============================

This module provides a unified interface to Google Sheets operations
using the Facade pattern to coordinate specialized components.

Architecture:
- Facade Pattern implementation
- Delegates to 5 specialized modules
- Maintains backward compatibility
- Single entry point for all Sheets operations

Components:
1. sheets_constants - Configuration and constants
2. sheets_authenticator - Authentication management  
3. sheets_data_mapper - Data transformation
4. sheets_operations - API operations
5. sheets_error_handler - Error handling and retry logic
"""

import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

# Import specialized modules
from .sheets_constants import SheetsConstants
from .sheets_authenticator import GoogleSheetsAuthenticator
from .sheets_data_mapper import GoogleSheetsDataMapper
from .sheets_operations import GoogleSheetsOperations
from .sheets_error_handler import (
    GoogleSheetsError, 
    GoogleSheetsErrorHandler,
    ErrorCategory,
    ErrorSeverity
)

# Import DTOs for backward compatibility
from ..models.publication_workflow import PublicationWorkflowDTO

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Facade class for Google Sheets operations
    
    This class provides a unified interface to all Google Sheets functionality,
    delegating to specialized components while maintaining a simple API.
    
    Single Responsibility: Coordinating specialized components through Facade pattern
    """
    
    def __init__(self, credentials_path: str, spreadsheet_id: str, 
                 worksheet_name: str = 'TechWF_Progress_Management'):
        """
        Initialize Google Sheets Service Facade
        
        Args:
            credentials_path: Path to service account JSON file
            spreadsheet_id: Google Spreadsheet ID
            worksheet_name: Target worksheet name
        """
        try:
            logger.info("Initializing GoogleSheetsService Facade")
            
            # Store configuration
            self.credentials_path = Path(credentials_path)
            self.spreadsheet_id = spreadsheet_id
            self.worksheet_name = worksheet_name
            
            # Initialize components
            self._initialize_components()
            
            # Service state
            self.is_enabled = self._validate_configuration()
            
            logger.info(f"GoogleSheetsService initialized - Enabled: {self.is_enabled}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GoogleSheetsService: {e}")
            self.is_enabled = False
            # Re-raise as GoogleSheetsError for consistent error handling
            raise self.error_handler.handle_general_error(
                e, "Service initialization failed"
            )
    
    def _initialize_components(self):
        """Initialize all specialized components"""
        # Error handler (initialized first for error handling in other components)
        self.error_handler = GoogleSheetsErrorHandler(
            max_retries=SheetsConstants.MAX_RETRIES,
            initial_delay=SheetsConstants.RETRY_INITIAL_DELAY,
            max_delay=SheetsConstants.RETRY_MAX_DELAY,
            backoff_factor=SheetsConstants.RETRY_BACKOFF_FACTOR
        )
        
        # Authenticator
        self.authenticator = GoogleSheetsAuthenticator(
            credentials_path=str(self.credentials_path)
        )
        
        # Data mapper
        self.data_mapper = GoogleSheetsDataMapper()
        
        # Operations handler
        self.operations = GoogleSheetsOperations(
            authenticator=self.authenticator
        )
        
        logger.debug("All components initialized")
    
    def _validate_configuration(self) -> bool:
        """
        Validate service configuration
        
        Returns:
            True if configuration is valid and service is ready
        """
        try:
            # Check credentials file exists
            if not self.credentials_path.exists():
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                return False
            
            # Test authentication
            if not self.authenticator.test_connection(self.spreadsheet_id):
                logger.warning("Failed to authenticate with Google Sheets")
                return False
            
            # Verify worksheet exists or can be created
            worksheets = self.authenticator.list_worksheets(self.spreadsheet_id)
            if self.worksheet_name not in worksheets:
                logger.info(f"Worksheet '{self.worksheet_name}' will be created on first use")
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    # ==================== Public API Methods ====================
    
    def get_all_workflows(self) -> List[PublicationWorkflowDTO]:
        """
        Get all workflows from the sheet
        
        Returns:
            List of PublicationWorkflowDTO objects
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return []
        
        @self.error_handler.with_retry
        def _get_all():
            # Ensure worksheet exists with proper headers
            self.operations.create_or_update_worksheet(
                self.spreadsheet_id, 
                self.worksheet_name
            )
            
            # Get all data as DTOs
            dtos = self.operations.get_all_data(
                self.spreadsheet_id,
                self.worksheet_name
            )
            
            # Convert to PublicationWorkflowDTO objects
            workflows = []
            for dto in dtos:
                try:
                    workflow = self._dto_to_workflow(dto)
                    if workflow:
                        workflows.append(workflow)
                except Exception as e:
                    logger.warning(f"Failed to convert DTO: {e}")
                    continue
            
            return workflows
        
        try:
            return _get_all()
        except GoogleSheetsError:
            raise
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, "Failed to get workflows"
            )
    
    def update_workflow(self, workflow: PublicationWorkflowDTO) -> bool:
        """
        Update a workflow in the sheet
        
        Args:
            workflow: PublicationWorkflowDTO to update
            
        Returns:
            True if successful
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return False
        
        @self.error_handler.with_retry
        def _update():
            # Convert workflow to DTO
            dto = self._workflow_to_dto(workflow)
            
            # Prepare updates
            updates = {
                'title': workflow.title,
                'status': workflow.status,
                'current_status': workflow.current_status,
                'editor': workflow.editor,
                'deadline': workflow.deadline,
                'page_count': workflow.page_count,
                'github_url': workflow.github_url,
                'last_updated': datetime.now()
            }
            
            # Update row by N number
            return self.operations.update_row_by_key(
                self.spreadsheet_id,
                self.worksheet_name,
                'n_number',
                workflow.n_number,
                updates
            )
        
        try:
            return _update()
        except GoogleSheetsError:
            raise
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, f"Failed to update workflow {workflow.n_number}"
            )
    
    def batch_update_workflows(self, workflows: List[PublicationWorkflowDTO]) -> int:
        """
        Update multiple workflows in batch
        
        Args:
            workflows: List of workflows to update
            
        Returns:
            Number of successfully updated workflows
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return 0
        
        success_count = 0
        for workflow in workflows:
            try:
                if self.update_workflow(workflow):
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to update workflow {workflow.n_number}: {e}")
                continue
        
        logger.info(f"Batch updated {success_count}/{len(workflows)} workflows")
        return success_count
    
    def add_workflow(self, workflow: PublicationWorkflowDTO) -> bool:
        """
        Add a new workflow to the sheet
        
        Args:
            workflow: PublicationWorkflowDTO to add
            
        Returns:
            True if successful
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return False
        
        @self.error_handler.with_retry
        def _add():
            # Convert workflow to DTO
            dto = self._workflow_to_dto(workflow)
            
            # Map to row data
            row_data = self.data_mapper.map_dto_to_sheet_row(dto)
            
            # Append to sheet
            result = self.operations.append_rows(
                self.spreadsheet_id,
                self.worksheet_name,
                [row_data]
            )
            
            return result is not None
        
        try:
            return _add()
        except GoogleSheetsError:
            raise
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, f"Failed to add workflow {workflow.n_number}"
            )
    
    def find_workflow_by_n_number(self, n_number: str) -> Optional[PublicationWorkflowDTO]:
        """
        Find a workflow by N number
        
        Args:
            n_number: N number to search for
            
        Returns:
            PublicationWorkflowDTO if found, None otherwise
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return None
        
        @self.error_handler.with_retry
        def _find():
            # Find row by N number
            row_num = self.operations.find_row_by_value(
                self.spreadsheet_id,
                self.worksheet_name,
                SheetsConstants.COLUMN_INDICES['n_number'],
                n_number
            )
            
            if not row_num:
                return None
            
            # Read the row
            range_name = f"{self.worksheet_name}!A{row_num}:Z{row_num}"
            values = self.operations.read_range(self.spreadsheet_id, range_name)
            
            if not values:
                return None
            
            # Map to DTO
            dto = self.data_mapper.map_sheet_row_to_dto(values[0], row_num)
            
            # Convert to workflow
            return self._dto_to_workflow(dto)
        
        try:
            return _find()
        except GoogleSheetsError:
            raise
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, f"Failed to find workflow {n_number}"
            )
    
    def sync_from_sheet(self, existing_workflows: List[PublicationWorkflowDTO]) -> Dict[str, Any]:
        """
        Sync workflows from sheet to local database
        
        Args:
            existing_workflows: Current workflows in database
            
        Returns:
            Sync results dictionary with added/updated/unchanged counts
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return {'added': 0, 'updated': 0, 'unchanged': 0, 'errors': []}
        
        try:
            # Get all workflows from sheet
            sheet_workflows = self.get_all_workflows()
            
            # Create lookup for existing workflows
            existing_map = {w.n_number: w for w in existing_workflows}
            
            results = {
                'added': 0,
                'updated': 0,
                'unchanged': 0,
                'errors': []
            }
            
            # Process each sheet workflow
            for sheet_workflow in sheet_workflows:
                try:
                    if sheet_workflow.n_number not in existing_map:
                        # New workflow
                        results['added'] += 1
                    else:
                        # Check if updated
                        existing = existing_map[sheet_workflow.n_number]
                        if self._workflow_changed(existing, sheet_workflow):
                            results['updated'] += 1
                        else:
                            results['unchanged'] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing workflow {sheet_workflow.n_number}: {e}")
                    results['errors'].append(str(e))
            
            logger.info(f"Sync from sheet complete: {results}")
            return results
            
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, "Failed to sync from sheet"
            )
    
    def sync_to_sheet(self, workflows: List[PublicationWorkflowDTO]) -> Dict[str, Any]:
        """
        Sync workflows from local database to sheet
        
        Args:
            workflows: Workflows to sync to sheet
            
        Returns:
            Sync results dictionary
            
        Raises:
            GoogleSheetsError: On API errors
        """
        if not self.is_enabled:
            logger.warning("Google Sheets service is disabled")
            return {'added': 0, 'updated': 0, 'errors': []}
        
        try:
            # Get current sheet workflows
            sheet_workflows = self.get_all_workflows()
            sheet_map = {w.n_number: w for w in sheet_workflows}
            
            results = {
                'added': 0,
                'updated': 0,
                'errors': []
            }
            
            # Process each local workflow
            for workflow in workflows:
                try:
                    if workflow.n_number not in sheet_map:
                        # Add new workflow
                        if self.add_workflow(workflow):
                            results['added'] += 1
                    else:
                        # Update existing workflow
                        if self.update_workflow(workflow):
                            results['updated'] += 1
                            
                except Exception as e:
                    logger.error(f"Error syncing workflow {workflow.n_number}: {e}")
                    results['errors'].append(str(e))
            
            logger.info(f"Sync to sheet complete: {results}")
            return results
            
        except Exception as e:
            raise self.error_handler.handle_general_error(
                e, "Failed to sync to sheet"
            )
    
    # ==================== Utility Methods ====================
    
    def validate_connection(self) -> bool:
        """
        Validate connection to Google Sheets
        
        Checks if the service is enabled and tests the connection to Google Sheets.
        Handles exceptions gracefully and returns False if any issues occur.
        
        Returns:
            True if service is enabled and connection is successful, False otherwise
        """
        try:
            # Check if service is enabled
            if not self.is_enabled:
                logger.warning("Google Sheets service is disabled")
                return False
            
            # Test the connection to Google Sheets
            if not self.authenticator.test_connection(self.spreadsheet_id):
                logger.error("Failed to connect to Google Sheets")
                return False
            
            logger.debug("Google Sheets connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Google Sheets
        
        Returns:
            True if connection successful
        """
        try:
            if not self.is_enabled:
                return False
            
            return self.authenticator.test_connection(self.spreadsheet_id)
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_worksheet_url(self) -> Optional[str]:
        """
        Get URL to the worksheet
        
        Returns:
            URL string or None if service disabled
        """
        if not self.is_enabled:
            return None
        
        # Get worksheet GID
        try:
            worksheets = self.authenticator.list_worksheets(self.spreadsheet_id)
            if self.worksheet_name in worksheets:
                # Construct URL
                return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        except:
            pass
        
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
    
    def get_error_recovery_suggestion(self, error: GoogleSheetsError) -> str:
        """
        Get recovery suggestion for an error
        
        Args:
            error: GoogleSheetsError instance
            
        Returns:
            Recovery suggestion string
        """
        return self.error_handler.get_recovery_suggestion(error)
    
    # ==================== Private Helper Methods ====================
    
    def _dto_to_workflow(self, dto: Dict[str, Any]) -> Optional[PublicationWorkflowDTO]:
        """
        Convert internal DTO to PublicationWorkflowDTO
        
        Args:
            dto: Internal DTO dictionary
            
        Returns:
            PublicationWorkflowDTO or None if invalid
        """
        try:
            if not dto.get('is_valid', False):
                return None
            
            # Create workflow DTO
            workflow = PublicationWorkflowDTO(
                n_number=dto.get('n_number', ''),
                title=dto.get('title', ''),
                status=dto.get('status', 'Unknown'),
                current_status=dto.get('current_status', 'Unknown'),
                repository_url=dto.get('github_url', ''),
                slack_channel=dto.get('slack_channel', ''),
                author_name=dto.get('author_name', ''),
                editor=dto.get('editor', ''),
                page_count=dto.get('page_count', 0),
                deadline=dto.get('deadline'),
                memo=dto.get('memo', ''),
                last_updated=dto.get('last_updated', datetime.now())
            )
            
            # Set additional fields
            workflow.editor = dto.get('editor', '')
            workflow.github_url = dto.get('github_url', '')
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to convert DTO to workflow: {e}")
            return None
    
    def _workflow_to_dto(self, workflow: PublicationWorkflowDTO) -> Dict[str, Any]:
        """
        Convert PublicationWorkflowDTO to internal DTO
        
        Args:
            workflow: PublicationWorkflowDTO
            
        Returns:
            Internal DTO dictionary
        """
        return {
            'n_number': workflow.n_number,
            'title': workflow.title,
            'status': workflow.status,
            'current_status': workflow.current_status,
            'github_url': workflow.repository_url or workflow.github_url,
            'slack_channel': workflow.slack_channel,
            'author_name': workflow.author_name,
            'editor': workflow.editor or workflow.editor,
            'page_count': workflow.page_count,
            'deadline': workflow.deadline,
            'memo': workflow.memo,
            'last_updated': workflow.last_updated or datetime.now(),
            'is_valid': True
        }
    
    def _workflow_changed(self, existing: PublicationWorkflowDTO, 
                         new: PublicationWorkflowDTO) -> bool:
        """
        Check if workflow has changed
        
        Args:
            existing: Existing workflow
            new: New workflow
            
        Returns:
            True if changed
        """
        # Compare key fields
        fields_to_check = [
            'title', 'status', 'current_status', 'repository_url',
            'slack_channel', 'author_name', 'editor', 'page_count',
            'deadline', 'memo'
        ]
        
        for field in fields_to_check:
            if getattr(existing, field, None) != getattr(new, field, None):
                return True
        
        return False
    
    # ==================== Context Manager Support ====================
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Clean up resources if needed
        pass


# ==================== Module Exports ====================

__all__ = [
    'GoogleSheetsService',
    'GoogleSheetsError',
    'ErrorCategory',
    'ErrorSeverity'
]