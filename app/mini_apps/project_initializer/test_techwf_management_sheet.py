#!/usr/bin/env python3
"""
TechWF_Managementシートの詳細分析
このシートが最も包括的なデータを持っている可能性が高い
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
    
    print('[INFO] TechWF_Managementシート詳細分析開始...')
    
    # Use working credentials
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    sheet_id = '17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ'  # メインシート
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] Service ready')
    
    sheet_name = "TechWF_Management"
    target_n_code = "N02413"
    
    print(f'\n[ANALYSIS] Analyzing "{sheet_name}" sheet structure...')
    
    # Get headers first
    header_range = f"'{sheet_name}'!A1:Z1"
    header_result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=header_range
    ).execute()
    
    headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
    print(f'[INFO] Found {len(headers)} columns in "{sheet_name}"')
    
    # Show all columns
    print(f'\n[COLUMNS] Full column structure:')
    for i, header in enumerate(headers):
        col_letter = chr(ord('A') + i)
        print(f'[INFO]   {col_letter}: "{header}"')
    
    # Get all data
    data_range = f"'{sheet_name}'!A1:Z1000"
    data_result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=data_range
    ).execute()
    
    data_values = data_result.get('values', [])
    print(f'[INFO] Read {len(data_values)} rows from "{sheet_name}"')
    
    # Search for N02413
    found_row = None
    found_row_index = None
    
    for row_idx, row in enumerate(data_values, start=1):
        for col_idx, cell in enumerate(row):
            if str(cell).strip().upper() == target_n_code:
                found_row = row
                found_row_index = row_idx
                col_letter = chr(ord('A') + col_idx)
                print(f'[FOUND] {target_n_code} found at Row {row_idx}, Column {col_letter}')
                break
        if found_row:
            break
    
    if found_row:
        print(f'\n[DATA EXTRACTION] N02413 full data:')
        
        # Show full data with column mapping
        max_cols = min(len(found_row), len(headers))
        
        extracted_data = {}
        for i in range(max_cols):
            col_letter = chr(ord('A') + i)
            header = headers[i] if i < len(headers) else f"Column{i+1}"
            value = found_row[i] if i < len(found_row) else ""
            
            print(f'[INFO] {col_letter}: "{header}" = "{value}"')
            extracted_data[header] = value
            
        # Map to required fields
        print(f'\n[MAPPING] Required field mapping:')
        field_mapping = {
            'N番号': extracted_data.get('N_Number', ''),
            '書籍名': extracted_data.get('Title', ''),
            'GitHubアカウント': extracted_data.get('Repository', ''),  # This might be repo URL, not account
            'SlackID': extracted_data.get('Slack', ''),
            '著者メール': extracted_data.get('Author', ''),  # This might be author name, not email
            'リポジトリ名': extracted_data.get('Repository', '')
        }
        
        for field, value in field_mapping.items():
            status = "✅ FOUND" if value and value.strip() else "❌ MISSING"
            print(f'[RESULT] {field}: "{value}" {status}')
            
        # Check if we need to look in other sheets for missing data
        missing_fields = [field for field, value in field_mapping.items() if not (value and value.strip())]
        
        if missing_fields:
            print(f'\n[MISSING] Fields not found in TechWF_Management: {missing_fields}')
            print('[INFO] These might be available in other sheets like "著者情報転記"')
            
            # Check 著者情報転記 sheet for missing data
            print(f'\n[CROSS-REFERENCE] Checking "著者情報転記" for additional data...')
            
            author_sheet = "著者情報転記"
            author_range = f"'{author_sheet}'!A1:Z1000"
            
            try:
                author_result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=author_range
                ).execute()
                
                author_values = author_result.get('values', [])
                author_headers = author_values[0] if author_values else []
                
                print(f'[INFO] 著者情報転記 columns: {author_headers[:10]}')  # Show first 10 columns
                
                # Look for N02413 related book title in 著者情報転記
                target_title = field_mapping.get('書籍名', '').strip()
                if target_title:
                    print(f'[SEARCH] Looking for title "{target_title}" in 著者情報転記...')
                    
                    for row_idx, row in enumerate(author_values[1:], start=2):  # Skip header
                        if row and len(row) > 0:
                            book_title = str(row[0]).strip()  # A列: 書名
                            if target_title in book_title or book_title in target_title:
                                print(f'[MATCH] Found matching title at row {row_idx}: "{book_title}"')
                                
                                # Extract additional data
                                additional_data = {}
                                for i, header in enumerate(author_headers):
                                    if i < len(row):
                                        additional_data[header] = row[i]
                                
                                print(f'[ADDITIONAL] GitHub: "{additional_data.get("GitHubアカウント", "")}"')
                                print(f'[ADDITIONAL] Email: "{additional_data.get("メアド", "")}"')
                                print(f'[ADDITIONAL] Twitter: "{additional_data.get("ツイッターアカウント", "")}"')
                                break
                                
            except Exception as e:
                print(f'[ERROR] Error checking 著者情報転記: {e}')
                
        # Generate ServiceAdapter configuration
        print(f'\n[CONFIG] ServiceAdapter configuration for N02413 data retrieval:')
        print(f'# Primary data from TechWF_Management sheet:')
        print(f'primary_sheet = "TechWF_Management"')
        print(f'primary_mappings = {{')
        print(f'    "n_code_col": "A",  # N_Number')
        print(f'    "title_col": "C",   # Title') 
        print(f'    "repo_col": "G",    # Repository')
        print(f'    "slack_col": "F"    # Slack')
        print(f'}}')
        print(f'')
        print(f'# Additional data from 著者情報転記 sheet (if needed):')
        print(f'author_sheet = "著者情報転記"')
        print(f'author_mappings = {{')
        print(f'    "title_col": "A",   # 書名')
        print(f'    "github_col": "C",  # GitHubアカウント')  
        print(f'    "email_col": "J"    # メアド')
        print(f'}}')
        
    else:
        print(f'[ERROR] {target_n_code} not found in "{sheet_name}"')
        
        # Show sample data
        print(f'\n[SAMPLE] First 5 rows of data:')
        for i, row in enumerate(data_values[:5], 1):
            row_sample = row[:10] if len(row) >= 10 else row
            print(f'[INFO] Row {i}: {row_sample}')
    
    print(f'\n[SUMMARY] TechWF_Management analysis completed.')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)