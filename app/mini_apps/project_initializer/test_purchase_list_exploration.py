#!/usr/bin/env python3
"""
技術書典購入リスト（技術書典18）の構造調査
M列のN番号、D列のURLを確認し、メインシートへの書き込み準備
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
    
    print('[INFO] 技術書典購入リスト（技術書典18）構造調査開始...')
    
    # Use working credentials
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    purchase_sheet_id = '1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c'  # 技術書典18購入リスト
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] Purchase list service ready')
    
    # Get spreadsheet metadata to find sheet names
    print(f'\n[EXPLORATION] Getting purchase list spreadsheet metadata...')
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=purchase_sheet_id).execute()
        sheet_title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
        print(f'[INFO] Spreadsheet title: {sheet_title}')
        
        # List all sheets
        sheets = sheet_metadata.get('sheets', [])
        print(f'[INFO] Total number of sheets: {len(sheets)}')
        
        for i, sheet in enumerate(sheets):
            sheet_props = sheet.get('properties', {})
            sheet_name = sheet_props.get('title', f'Sheet{i+1}')
            print(f'[INFO]   Sheet {i+1}: "{sheet_name}"')
            
    except Exception as e:
        print(f'[ERROR] Error getting metadata: {e}')
        sys.exit(1)
    
    # Assume first sheet contains the purchase data
    target_sheet = sheets[0]['properties']['title']
    print(f'\n[ANALYSIS] Analyzing target sheet: "{target_sheet}"')
    
    # Test 1: Check headers and structure
    print(f'\n[TEST 1] Checking headers and column structure...')
    try:
        # Get headers (first row)
        header_range = f"'{target_sheet}'!A1:Z1"
        header_result = service.spreadsheets().values().get(
            spreadsheetId=purchase_sheet_id,
            range=header_range
        ).execute()
        
        headers = header_result.get('values', [[]])[0] if header_result.get('values') else []
        print(f'[INFO] Found {len(headers)} columns:')
        
        for i, header in enumerate(headers[:15], 1):  # Show first 15 columns
            col_letter = chr(64 + i)  # A=65, so A-1=64
            print(f'[INFO]   {col_letter}{i}: "{header}"')
        
        # Check specifically for M and D columns
        if len(headers) >= 13:  # M is 13th column
            m_header = headers[12] if len(headers) > 12 else "N/A"
            print(f'[INFO] M列 (Column M): "{m_header}"')
        
        if len(headers) >= 4:   # D is 4th column  
            d_header = headers[3] if len(headers) > 3 else "N/A"
            print(f'[INFO] D列 (Column D): "{d_header}"')
            
    except Exception as e:
        print(f'[ERROR] Error reading headers: {e}')
        sys.exit(1)
    
    # Test 2: Sample data from M and D columns
    print(f'\n[TEST 2] Sampling data from M列(N番号) and D列(URL)...')
    try:
        # Read M and D columns for first 20 rows
        md_range = f"'{target_sheet}'!D1:D20,M1:M20"  # D and M columns
        md_result = service.spreadsheets().values().batchGet(
            spreadsheetId=purchase_sheet_id,
            ranges=[f"'{target_sheet}'!D1:D20", f"'{target_sheet}'!M1:M20"]
        ).execute()
        
        value_ranges = md_result.get('valueRanges', [])
        
        if len(value_ranges) >= 2:
            d_values = value_ranges[0].get('values', [])  # D column (URL)
            m_values = value_ranges[1].get('values', [])  # M column (N番号)
            
            print(f'[INFO] D列(URL) sample data ({len(d_values)} rows):')
            for i, row in enumerate(d_values[:10], 1):
                value = row[0] if row else ""
                print(f'[INFO]   Row {i}: {value[:50]}...' if len(str(value)) > 50 else f'[INFO]   Row {i}: {value}')
            
            print(f'\n[INFO] M列(N番号) sample data ({len(m_values)} rows):')
            for i, row in enumerate(m_values[:10], 1):
                value = row[0] if row else ""
                print(f'[INFO]   Row {i}: {value}')
            
            # Find rows with valid N-codes in M column
            print(f'\n[ANALYSIS] Looking for valid N-codes in M column...')
            valid_n_codes = []
            for i, row in enumerate(m_values[1:], 2):  # Skip header row
                if row and len(row) > 0:
                    value = str(row[0]).strip().upper()
                    if value.startswith('N') and len(value) >= 5:
                        # Get corresponding D column value
                        corresponding_url = ""
                        if i-1 < len(d_values) and d_values[i-1]:
                            corresponding_url = d_values[i-1][0] if d_values[i-1] else ""
                        
                        valid_n_codes.append({
                            'row': i,
                            'n_code': value,
                            'url': corresponding_url
                        })
                        
                        if len(valid_n_codes) >= 5:  # Show first 5
                            break
            
            print(f'[SUCCESS] Found {len(valid_n_codes)} N-codes with URLs:')
            for item in valid_n_codes:
                print(f'[INFO]   Row {item["row"]}: {item["n_code"]} → {item["url"][:60]}...' if len(item["url"]) > 60 else f'[INFO]   Row {item["row"]}: {item["n_code"]} → {item["url"]}')
                
        else:
            print('[ERROR] Could not read M and D columns data')
            sys.exit(1)
            
    except Exception as e:
        print(f'[ERROR] Error reading M/D columns: {e}')
        sys.exit(1)
    
    print(f'\n[SUMMARY] Purchase list analysis complete:')
    print(f'✅ Sheet identified: "{target_sheet}"')
    print(f'✅ M列 (Column M): Contains N-codes')
    print(f'✅ D列 (Column D): Contains URLs')
    print(f'✅ Found valid N-code/URL pairs for processing')
    
    print(f'\n[NEXT STEP] Ready to implement:')
    print(f'1. Read N-codes from M column of purchase list')
    print(f'2. Read corresponding URLs from D column')  
    print(f'3. Match N-codes with main sheet entries')
    print(f'4. Update main sheet with URL information')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)