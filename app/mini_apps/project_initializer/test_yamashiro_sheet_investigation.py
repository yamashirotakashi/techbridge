#!/usr/bin/env python3
"""
発行計画（山城）シートの構造調査
A列のN番号をキーにして、書籍名（H列）、GitHubアカウント（M列）、SlackID（K列）、著者メール（T列）の取得状況を確認
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
    
    print('[INFO] 発行計画（山城）シート構造調査開始...')
    
    # Use working credentials
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    sheet_id = '17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ'  # メインシート
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] Yamashiro sheet investigation service ready')
    
    # Check all sheet names first
    print(f'\n[STEP 1] Getting all sheet names...')
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        print(f'[INFO] Total sheets found: {len(sheets)}')
        yamashiro_sheet = None
        
        for i, sheet in enumerate(sheets):
            sheet_props = sheet.get('properties', {})
            sheet_name = sheet_props.get('title', f'Sheet{i+1}')
            print(f'[INFO]   Sheet {i+1}: "{sheet_name}"')
            
            # Look for the Yamashiro planning sheet
            if '発行計画' in sheet_name and '山城' in sheet_name:
                yamashiro_sheet = sheet_name
                print(f'[FOUND] Target sheet identified: "{yamashiro_sheet}"')
        
        if not yamashiro_sheet:
            print('[ERROR] 発行計画（山城）sheet not found')
            # Let's check if there's a sheet with just "発行計画" or similar
            planning_sheet_candidates = []
            for sheet in sheets:
                sheet_name = sheet['properties']['title']
                if '発行' in sheet_name or 'リスト' in sheet_name or '作成' in sheet_name:
                    planning_sheet_candidates.append(sheet_name)
                    print(f'[INFO] Planning sheet candidate found: "{sheet_name}"')
            
            if planning_sheet_candidates:
                # Use the first candidate that looks like a planning sheet
                yamashiro_sheet = planning_sheet_candidates[0]
                print(f'[INFO] Using sheet: "{yamashiro_sheet}"')
            else:
                print('[ERROR] No planning sheet found. Available sheets:')
                for i, sheet in enumerate(sheets):
                    sheet_name = sheet['properties']['title']
                    print(f'[INFO]   {i+1}: "{sheet_name}"')
                print('[ERROR] Cannot continue without identifying the correct sheet. Exiting.')
                sys.exit(1)
            
    except Exception as e:
        print(f'[ERROR] Error getting sheet metadata: {e}')
        sys.exit(1)
    
    # Analyze the target sheet structure
    print(f'\n[STEP 2] Analyzing "{yamashiro_sheet}" sheet structure...')
    
    try:
        # Get headers first
        header_range = f"'{yamashiro_sheet}'!A1:Z1"
        header_result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=header_range
        ).execute()
        
        headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
        print(f'[INFO] Found {len(headers)} columns in "{yamashiro_sheet}"')
        
        # Map column letters to headers
        target_columns = {
            'A': 'N番号',
            'C': 'リポジトリ名',
            'H': '書籍名', 
            'K': 'SlackID',
            'M': 'GitHubアカウント',
            'T': '著者メール'
        }
        
        print(f'\n[ANALYSIS] Column mapping analysis:')
        for col_letter, expected_content in target_columns.items():
            col_index = ord(col_letter) - ord('A')  # A=0, B=1, etc.
            if col_index < len(headers):
                actual_header = headers[col_index]
                print(f'[INFO] {col_letter}列 (Column {col_letter}): "{actual_header}" (期待: {expected_content})')
            else:
                print(f'[WARN] {col_letter}列 (Column {col_letter}): Not found (期待: {expected_content})')
        
    except Exception as e:
        print(f'[ERROR] Error reading headers: {e}')
        sys.exit(1)
    
    # Test data retrieval with specific N-code
    print(f'\n[STEP 3] Testing data retrieval for N02413...')
    
    try:
        # Read the full range to find N02413 and get all columns
        data_range = f"'{yamashiro_sheet}'!A1:T1000"  # A to T columns, up to 1000 rows
        data_result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=data_range
        ).execute()
        
        data_values = data_result.get('values', [])
        print(f'[INFO] Read {len(data_values)} rows from "{yamashiro_sheet}"')
        
        # Find N02413
        n02413_row = None
        for row_idx, row in enumerate(data_values, start=1):
            if row and len(row) > 0:
                cell_value = str(row[0]).strip().upper()
                if cell_value == 'N02413':
                    n02413_row = row
                    print(f'[SUCCESS] Found N02413 at row {row_idx}')
                    break
        
        if n02413_row:
            print(f'\n[EXTRACTION] N02413 data extraction:')
            
            # Column mapping (0-based index)
            columns_to_check = {
                'A列 (N番号)': (0, n02413_row[0] if len(n02413_row) > 0 else "N/A"),
                'C列 (リポジトリ名)': (2, n02413_row[2] if len(n02413_row) > 2 else "N/A"),
                'H列 (書籍名)': (7, n02413_row[7] if len(n02413_row) > 7 else "N/A"),
                'K列 (SlackID)': (10, n02413_row[10] if len(n02413_row) > 10 else "N/A"),
                'M列 (GitHubアカウント)': (12, n02413_row[12] if len(n02413_row) > 12 else "N/A"),
                'T列 (著者メール)': (19, n02413_row[19] if len(n02413_row) > 19 else "N/A")
            }
            
            for col_name, (index, value) in columns_to_check.items():
                if value and value.strip() and value != "N/A":
                    print(f'[SUCCESS] {col_name}: "{value}"')
                else:
                    print(f'[ERROR]   {col_name}: EMPTY or MISSING')
            
            # Show full row structure for debugging
            print(f'\n[DEBUG] Full row structure for N02413 (first 20 columns):')
            for i, cell_value in enumerate(n02413_row[:20]):
                col_letter = chr(ord('A') + i)
                print(f'[DEBUG]   {col_letter}{i+1}: "{cell_value}"' if cell_value else f'[DEBUG]   {col_letter}{i+1}: (empty)')
                
        else:
            print('[ERROR] N02413 not found in the planning sheet')
            
            # Show sample data to understand structure
            print(f'\n[DEBUG] Sample data from planning sheet (first 5 rows, first 10 columns):')
            for i, row in enumerate(data_values[:5], 1):
                row_sample = row[:10] if len(row) >= 10 else row
                print(f'[DEBUG] Row {i}: {row_sample}')
            
    except Exception as e:
        print(f'[ERROR] Error reading planning sheet data: {e}')
        sys.exit(1)
    
    print(f'\n[SUMMARY] 発行計画（山城）シート分析結果:')
    print(f'✅ Sheet identified: "{yamashiro_sheet}"')
    print(f'📊 Data retrieval test completed')
    print(f'🔍 Column structure mapped')
    
    print(f'\n[NEXT STEPS] Based on findings:')
    print('1. Verify which columns are actually populated')
    print('2. Update service adapter to read correct column ranges')
    print('3. Implement proper error handling for missing data')
    print('4. Test with multiple N-codes to confirm pattern')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)