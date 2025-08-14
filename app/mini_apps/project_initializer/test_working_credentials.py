#!/usr/bin/env python3
"""
Test with PJINIT 1.2's working credentials file
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
    
    print('[INFO] Testing with PJINIT 1.2 working credentials...')
    
    # Use the exact same credentials that PJINIT 1.2 uses successfully
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    sheet_id = '17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ'  # From .env
    
    # Load working credentials
    print(f'[INFO] Loading working credentials from: {working_creds_path}')
    if not Path(working_creds_path).exists():
        print(f'[ERROR] Working credentials file not found: {working_creds_path}')
        sys.exit(1)
    
    # Create credentials object
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    print('[OK] Working credentials loaded successfully')
    print(f'[INFO] Project ID: {credentials.project_id}')
    print(f'[INFO] Service Account: {credentials.service_account_email}')
    
    # Build the service
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] Google Sheets service built successfully')
    
    # Test: Get spreadsheet metadata
    print(f'\n[TEST] Getting spreadsheet metadata for: {sheet_id}')
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
        print(f'[SUCCESS] Sheet metadata retrieved successfully')
        print(f'[INFO] Sheet title: {sheet_title}')
        
    except HttpError as e:
        print(f'[ERROR] HTTP Error getting metadata: {e}')
        print(f'[ERROR] Status code: {e.resp.status}')
        print(f'[ERROR] Error details: {e.error_details}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error getting metadata: {e}')
        sys.exit(1)
    
    # Test: Search for N02413 specifically
    print(f'\n[TEST] Searching for N-code N02413 in column A')
    try:
        range_name = 'A1:D1000'
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        print(f'[INFO] Scanning {len(values)} rows for N02413...')
        
        found = False
        for row_idx, row in enumerate(values, start=1):
            if row and len(row) > 0:
                cell_value = str(row[0]).strip().upper()
                if cell_value == 'N02413':
                    print(f'[SUCCESS] Found N02413 at row {row_idx}')
                    repository_name = row[2].strip() if len(row) > 2 and row[2] else 'N/A'
                    channel_name = row[3].strip() if len(row) > 3 and row[3] else repository_name
                    
                    result_data = {
                        'row': row_idx,
                        'n_code': cell_value,
                        'repository_name': repository_name,
                        'channel_name': channel_name
                    }
                    
                    print(f'[INFO] N-code: {cell_value}')
                    print(f'[INFO] Repository name: {repository_name}')
                    print(f'[INFO] Channel name: {channel_name}')
                    print(f'[INFO] Result data: {result_data}')
                    found = True
                    break
        
        if not found:
            print('[WARN] N02413 not found in the spreadsheet')
            print('[INFO] Showing first 5 N-codes found:')
            n_codes_found = []
            for row_idx, row in enumerate(values[:50], start=1):  # Check first 50 rows
                if row and len(row) > 0:
                    cell_value = str(row[0]).strip().upper()
                    if cell_value.startswith('N') and len(cell_value) >= 5:
                        n_codes_found.append(f'Row {row_idx}: {cell_value}')
                        if len(n_codes_found) >= 5:
                            break
            
            for n_code in n_codes_found:
                print(f'[INFO] {n_code}')
        
    except HttpError as e:
        print(f'[ERROR] HTTP Error searching data: {e}')
        print(f'[ERROR] Status code: {e.resp.status}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error searching data: {e}')
        sys.exit(1)
    
    print('\n[SUCCESS] PJINIT 1.2 working credentials test completed successfully!')
    print('[INFO] Real Google Sheets API connection is working with techbook-analytics project')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    print('[INFO] Please install: pip install google-api-python-client google-auth')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)