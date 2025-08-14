#!/usr/bin/env python3
"""
Multi-sheet exploration test
Explore the spreadsheet structure to understand multi-sheet functionality requirements
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
    
    print('[INFO] Exploring multi-sheet functionality...')
    
    # Use working credentials
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    sheet_id = '17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ'  # From .env
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] Credentials and service ready')
    
    # Get detailed spreadsheet metadata
    print('\n[EXPLORATION] Getting detailed spreadsheet metadata...')
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
        print(f'[INFO] Spreadsheet title: {sheet_title}')
        
        # List ALL sheets with detailed info
        sheets = sheet_metadata.get('sheets', [])
        print(f'[INFO] Total number of sheets: {len(sheets)}')
        print('[INFO] Sheet details:')
        
        for i, sheet in enumerate(sheets):
            sheet_props = sheet.get('properties', {})
            sheet_name = sheet_props.get('title', f'Sheet{i+1}')
            sheet_id_internal = sheet_props.get('sheetId', 'unknown')
            grid_props = sheet_props.get('gridProperties', {})
            rows = grid_props.get('rowCount', 'unknown')
            cols = grid_props.get('columnCount', 'unknown')
            
            print(f'[INFO]   Sheet {i+1}: "{sheet_name}"')
            print(f'[INFO]     Sheet ID: {sheet_id_internal}')
            print(f'[INFO]     Dimensions: {rows} rows x {cols} columns')
            
            # Sample a few rows from each sheet to understand content
            if i < 3:  # Only sample first 3 sheets
                print(f'[INFO]     Sampling data from "{sheet_name}"...')
                try:
                    range_name = f"'{sheet_name}'!A1:D3"
                    result = service.spreadsheets().values().get(
                        spreadsheetId=sheet_id,
                        range=range_name
                    ).execute()
                    
                    values = result.get('values', [])
                    for row_idx, row in enumerate(values[:3], start=1):
                        # Truncate long values for display
                        row_display = [str(cell)[:15] + '...' if len(str(cell)) > 15 else str(cell) for cell in row[:4]]
                        print(f'[INFO]       Row {row_idx}: {row_display}')
                        
                except Exception as e:
                    print(f'[WARN]       Could not sample data from "{sheet_name}": {e}')
            print()
            
    except HttpError as e:
        print(f'[ERROR] HTTP Error getting metadata: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Unexpected error getting metadata: {e}')
        sys.exit(1)
    
    # Focus on the main sheet and identify potential secondary sheet
    print('[ANALYSIS] Multi-sheet potential analysis:')
    if len(sheets) >= 2:
        main_sheet = sheets[0]['properties']['title']
        secondary_sheets = [sheet['properties']['title'] for sheet in sheets[1:3]]  # Get next 2 sheets
        
        print(f'[INFO] Main sheet (likely primary data): "{main_sheet}"')
        print(f'[INFO] Potential secondary sheets: {secondary_sheets}')
        
        # Test N02413 search in different sheets
        print('\n[TEST] Searching for N02413 across multiple sheets...')
        for i, sheet in enumerate(sheets[:3]):  # Check first 3 sheets
            sheet_name = sheet['properties']['title']
            print(f'\n[TEST] Checking sheet: "{sheet_name}"')
            
            try:
                range_name = f"'{sheet_name}'!A1:D1000"
                result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                print(f'[INFO] Scanning {len(values)} rows in "{sheet_name}" for N02413...')
                
                found_n02413 = False
                for row_idx, row in enumerate(values, start=1):
                    if row and len(row) > 0:
                        cell_value = str(row[0]).strip().upper()
                        if cell_value == 'N02413':
                            print(f'[SUCCESS] Found N02413 in "{sheet_name}" at row {row_idx}')
                            repository_name = row[2].strip() if len(row) > 2 and row[2] else 'N/A'
                            channel_name = row[3].strip() if len(row) > 3 and row[3] else repository_name
                            print(f'[INFO] Data: N-code={cell_value}, Repo={repository_name}, Channel={channel_name}')
                            found_n02413 = True
                            break
                
                if not found_n02413:
                    print(f'[INFO] N02413 not found in "{sheet_name}"')
                    # Show what N-codes are available in this sheet
                    n_codes_sample = []
                    for row_idx, row in enumerate(values[:20], start=1):  # Check first 20 rows
                        if row and len(row) > 0:
                            cell_value = str(row[0]).strip().upper()
                            if cell_value.startswith('N') and len(cell_value) >= 5:
                                n_codes_sample.append(f'{cell_value}')
                                if len(n_codes_sample) >= 3:
                                    break
                    if n_codes_sample:
                        print(f'[INFO] Sample N-codes in "{sheet_name}": {n_codes_sample}')
                    else:
                        print(f'[INFO] No N-codes found in first 20 rows of "{sheet_name}"')
                        
            except Exception as e:
                print(f'[WARN] Error checking sheet "{sheet_name}": {e}')
        
    else:
        print('[INFO] Only one sheet found - multi-sheet functionality may not be needed')
    
    print('\n[SUCCESS] Multi-sheet exploration completed!')
    print('[RECOMMENDATION] Based on the findings above, determine multi-sheet requirements')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)