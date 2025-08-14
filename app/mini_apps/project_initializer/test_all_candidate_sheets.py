#!/usr/bin/env python3
"""
すべての候補シートでN02413の検索と正確なカラム構造分析
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
    
    print('[INFO] 全候補シートでのN02413検索開始...')
    
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
    
    # Get all sheet names
    sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    
    # Planning sheet candidates based on previous investigation
    candidate_sheets = [
        "発行リスト作成用",
        "発行リスト作成用 のコピー", 
        "著者情報転記",
        "手動タスク管理",
        "中間転記用",
        "TechWF_Management"  # This one might contain project management data
    ]
    
    target_n_code = "N02413"
    found_sheet = None
    found_data = None
    
    print(f'\n[SEARCH] Searching for {target_n_code} in candidate sheets...')
    
    for sheet_name in candidate_sheets:
        print(f'\n[CHECKING] Sheet: "{sheet_name}"')
        
        try:
            # Get headers first
            header_range = f"'{sheet_name}'!A1:Z1"
            header_result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=header_range
            ).execute()
            
            headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
            print(f'[INFO] Columns in "{sheet_name}": {len(headers)}')
            
            if len(headers) > 0:
                # Show first 10 columns
                for i, header in enumerate(headers[:10]):
                    col_letter = chr(ord('A') + i)
                    print(f'[INFO]   {col_letter}: "{header}"')
            
            # Search for target N-code
            data_range = f"'{sheet_name}'!A1:Z1000"
            data_result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=data_range
            ).execute()
            
            data_values = data_result.get('values', [])
            
            # Search through all rows and columns for the N-code
            for row_idx, row in enumerate(data_values, start=1):
                for col_idx, cell in enumerate(row):
                    if str(cell).strip().upper() == target_n_code:
                        col_letter = chr(ord('A') + col_idx)
                        print(f'[FOUND] {target_n_code} found in "{sheet_name}" at {col_letter}{row_idx}')
                        found_sheet = sheet_name
                        found_data = {
                            'sheet_name': sheet_name,
                            'row': row_idx,
                            'col': col_letter,
                            'full_row': row,
                            'headers': headers
                        }
                        break
                if found_sheet:
                    break
            
            if not found_sheet and len(data_values) > 1:
                # Show sample data if not found
                print(f'[INFO] Sample data (first 3 rows):')
                for i, row in enumerate(data_values[:3], 1):
                    row_sample = row[:5] if len(row) >= 5 else row
                    print(f'[INFO]   Row {i}: {row_sample}')
                    
        except Exception as e:
            print(f'[ERROR] Error checking "{sheet_name}": {e}')
            continue
    
    if found_sheet and found_data:
        print(f'\n[SUCCESS] Found {target_n_code} in sheet: "{found_sheet}"')
        print(f'[LOCATION] Row {found_data["row"]}, Column {found_data["col"]}')
        
        # Analyze the structure where N02413 was found
        print(f'\n[STRUCTURE ANALYSIS] Full row data for {target_n_code}:')
        full_row = found_data['full_row']
        headers = found_data['headers']
        
        # Map columns to data
        max_cols = min(len(full_row), len(headers), 20)  # Limit to 20 columns for readability
        
        for i in range(max_cols):
            col_letter = chr(ord('A') + i)
            header = headers[i] if i < len(headers) else f"Column{i+1}"
            value = full_row[i] if i < len(full_row) else "N/A"
            
            print(f'[DATA] {col_letter}: "{header}" = "{value}"')
            
            # Look for relevant data types
            if any(keyword in str(header).lower() for keyword in ['書籍', 'title', 'book']):
                print(f'  --> 📖 BOOK TITLE candidate')
            elif any(keyword in str(header).lower() for keyword in ['github', 'git']):
                print(f'  --> 🔗 GITHUB candidate')
            elif any(keyword in str(header).lower() for keyword in ['slack', 'id']):
                print(f'  --> 💬 SLACK candidate')  
            elif any(keyword in str(header).lower() for keyword in ['mail', 'email', 'メール']):
                print(f'  --> 📧 EMAIL candidate')
            elif any(keyword in str(header).lower() for keyword in ['repo', 'リポジトリ']):
                print(f'  --> 📂 REPOSITORY candidate')
        
        # Generate the correct column mapping
        print(f'\n[MAPPING] Suggested column mapping for ServiceAdapter:')
        print(f'sheet_name = "{found_sheet}"')
        
        # Find the correct columns based on analysis
        for i in range(max_cols):
            col_letter = chr(ord('A') + i)
            header = headers[i] if i < len(headers) else f"Column{i+1}"
            value = full_row[i] if i < len(full_row) else "N/A"
            
            # Suggest mappings based on content analysis
            if str(header).lower() == 'n_code' or (col_letter == 'A' and target_n_code in str(value)):
                print(f'A列 (N番号): Column {col_letter} = "{header}"')
            elif any(keyword in str(header).lower() for keyword in ['title', '書籍', 'book']):
                print(f'書籍名: Column {col_letter} = "{header}"')
            elif any(keyword in str(header).lower() for keyword in ['github', 'git']):
                print(f'GitHubアカウント: Column {col_letter} = "{header}"')
            elif any(keyword in str(header).lower() for keyword in ['slack', 'id']):
                print(f'SlackID: Column {col_letter} = "{header}"')
            elif any(keyword in str(header).lower() for keyword in ['mail', 'email', 'メール']):
                print(f'著者メール: Column {col_letter} = "{header}"')
            elif any(keyword in str(header).lower() for keyword in ['repo', 'リポジトリ']):
                print(f'リポジトリ名: Column {col_letter} = "{header}"')
                
    else:
        print(f'\n[NOT FOUND] {target_n_code} was not found in any of the candidate sheets.')
        print('[INFO] This might mean:')
        print('1. The N-code is in a different sheet not in our candidate list')
        print('2. The N-code has a different format')
        print('3. The data might be in the main sheet already')
        
        print(f'\n[FALLBACK] Let\'s check if {target_n_code} exists in the main sheet (first sheet)')
        try:
            main_sheet = sheets[0]['properties']['title']  # Usually the first sheet
            print(f'[CHECKING] Main sheet: "{main_sheet}"')
            
            main_range = f"'{main_sheet}'!A1:Z1000"
            main_result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=main_range
            ).execute()
            
            main_values = main_result.get('values', [])
            for row_idx, row in enumerate(main_values, start=1):
                for col_idx, cell in enumerate(row):
                    if str(cell).strip().upper() == target_n_code:
                        col_letter = chr(ord('A') + col_idx)
                        print(f'[FOUND] {target_n_code} found in main sheet "{main_sheet}" at {col_letter}{row_idx}')
                        break
                        
        except Exception as e:
            print(f'[ERROR] Error checking main sheet: {e}')
    
    print(f'\n[SUMMARY] Investigation completed.')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)