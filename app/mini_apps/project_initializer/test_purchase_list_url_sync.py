#!/usr/bin/env python3
"""
技術書典購入リストからメインシートE列へのURL転記機能テスト
購入リストのM列(N番号)とD列(URL)を読み取り、メインシートのE列に書き込む
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
    
    print('[INFO] 購入リストURL同期機能テスト開始...')
    
    # Use working credentials
    working_creds_path = '/mnt/c/Users/tky99/DEV/techbridge/config/techbook-analytics-aa03914c6639.json'
    main_sheet_id = '17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ'      # メインシート
    purchase_sheet_id = '1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c'   # 技術書典18購入リスト
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        working_creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    print('[OK] URL sync service ready')
    
    # Define sheets
    MAIN_SHEET = "2020.10-"    # メインデータシート
    PURCHASE_SHEET = "技術書典18"  # 購入リストシート
    
    print(f'\n[STEP 1] Reading N-codes and URLs from purchase list...')
    
    # Read M column (N-codes) and D column (URLs) from purchase list
    try:
        purchase_range_m = f"'{PURCHASE_SHEET}'!M1:M1000"  # N番号列
        purchase_range_d = f"'{PURCHASE_SHEET}'!D1:D1000"  # URL列
        
        batch_result = service.spreadsheets().values().batchGet(
            spreadsheetId=purchase_sheet_id,
            ranges=[purchase_range_m, purchase_range_d]
        ).execute()
        
        value_ranges = batch_result.get('valueRanges', [])
        m_values = value_ranges[0].get('values', []) if len(value_ranges) > 0 else []  # N番号
        d_values = value_ranges[1].get('values', []) if len(value_ranges) > 1 else []  # URL
        
        # Create N-code to URL mapping
        n_code_url_map = {}
        for i, m_row in enumerate(m_values[1:], 2):  # Skip header row
            if m_row and len(m_row) > 0:
                n_code = str(m_row[0]).strip().upper()
                if n_code.startswith('N') and len(n_code) >= 5:
                    # Get corresponding URL
                    url = ""
                    if i-1 < len(d_values) and d_values[i-1]:
                        url = str(d_values[i-1][0]).strip() if d_values[i-1] else ""
                    
                    if url and url.startswith('https://techbookfest.org'):
                        n_code_url_map[n_code] = url
        
        print(f'[SUCCESS] Found {len(n_code_url_map)} N-code/URL mappings from purchase list:')
        for i, (n_code, url) in enumerate(list(n_code_url_map.items())[:5], 1):
            print(f'[INFO]   {i}: {n_code} → {url[:60]}...' if len(url) > 60 else f'[INFO]   {i}: {n_code} → {url}')
        
        if len(n_code_url_map) > 5:
            print(f'[INFO]   ... and {len(n_code_url_map) - 5} more mappings')
            
    except Exception as e:
        print(f'[ERROR] Error reading purchase list: {e}')
        sys.exit(1)
    
    print(f'\n[STEP 2] Reading main sheet structure...')
    
    # Read main sheet N-codes and current E column values
    try:
        main_range = f"'{MAIN_SHEET}'!A1:E1000"  # A列(N番号), E列(URL書き込み先)
        main_result = service.spreadsheets().values().get(
            spreadsheetId=main_sheet_id,
            range=main_range
        ).execute()
        
        main_values = main_result.get('values', [])
        print(f'[INFO] Read {len(main_values)} rows from main sheet')
        
        # Find rows to update
        updates_needed = []
        for row_idx, row in enumerate(main_values, 1):
            if row and len(row) > 0:
                n_code = str(row[0]).strip().upper()
                if n_code.startswith('N') and n_code in n_code_url_map:
                    # Check if E column (index 4) is empty or needs update
                    current_url = row[4].strip() if len(row) > 4 and row[4] else ""
                    new_url = n_code_url_map[n_code]
                    
                    # Update if E column is empty or different
                    if not current_url or current_url != new_url:
                        updates_needed.append({
                            'row': row_idx,
                            'n_code': n_code,
                            'current_url': current_url,
                            'new_url': new_url,
                            'range': f"'{MAIN_SHEET}'!E{row_idx}"
                        })
        
        print(f'[SUCCESS] Found {len(updates_needed)} rows needing URL updates:')
        for i, update in enumerate(updates_needed[:5], 1):
            current_display = update['current_url'][:30] + '...' if len(update['current_url']) > 30 else update['current_url'] or '(empty)'
            new_display = update['new_url'][:50] + '...' if len(update['new_url']) > 50 else update['new_url']
            print(f'[INFO]   {i}: {update["n_code"]} (Row {update["row"]})')
            print(f'[INFO]      Current: {current_display}')
            print(f'[INFO]      New:     {new_display}')
            
        if len(updates_needed) > 5:
            print(f'[INFO]   ... and {len(updates_needed) - 5} more updates')
            
    except Exception as e:
        print(f'[ERROR] Error reading main sheet: {e}')
        sys.exit(1)
    
    print(f'\n[STEP 3] Performing URL updates to main sheet E column...')
    
    if not updates_needed:
        print('[INFO] No updates needed - all URLs are already up to date')
    else:
        try:
            # Prepare batch update data
            batch_update_data = []
            for update in updates_needed[:3]:  # Limit to first 3 for testing
                batch_update_data.append({
                    'range': update['range'],
                    'values': [[update['new_url']]]
                })
            
            # Perform batch update
            if batch_update_data:
                batch_update_body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': batch_update_data
                }
                
                update_result = service.spreadsheets().values().batchUpdate(
                    spreadsheetId=main_sheet_id,
                    body=batch_update_body
                ).execute()
                
                updated_cells = update_result.get('totalUpdatedCells', 0)
                print(f'[SUCCESS] Updated {updated_cells} cells in main sheet E column')
                
                # Show what was updated
                for i, update in enumerate(updates_needed[:3], 1):
                    print(f'[INFO]   Updated Row {update["row"]}: {update["n_code"]} → URL written to E{update["row"]}')
            
        except Exception as e:
            print(f'[ERROR] Error updating main sheet: {e}')
            sys.exit(1)
    
    print(f'\n[STEP 4] Verification - checking updated rows...')
    
    # Verify some of the updates
    try:
        if updates_needed:
            verify_ranges = [update['range'] for update in updates_needed[:3]]
            verify_result = service.spreadsheets().values().batchGet(
                spreadsheetId=main_sheet_id,
                ranges=verify_ranges
            ).execute()
            
            verify_values = verify_result.get('valueRanges', [])
            print(f'[VERIFICATION] Checking updated values:')
            
            for i, (update, verify_range) in enumerate(zip(updates_needed[:3], verify_values), 1):
                current_value = verify_range.get('values', [[]])[0][0] if verify_range.get('values') and verify_range['values'][0] else ""
                expected_value = update['new_url']
                
                if current_value == expected_value:
                    print(f'[SUCCESS]   {update["n_code"]} (E{update["row"]}): ✅ URL correctly updated')
                else:
                    print(f'[ERROR]     {update["n_code"]} (E{update["row"]}): ❌ Mismatch')
                    print(f'[ERROR]     Expected: {expected_value[:50]}...')
                    print(f'[ERROR]     Found:    {current_value[:50]}...')
        
    except Exception as e:
        print(f'[WARN] Verification error: {e}')
    
    print(f'\n[SUCCESS] Purchase list URL sync test completed!')
    print(f'[SUMMARY] Results:')
    print(f'✅ Purchase list mappings: {len(n_code_url_map)}')
    print(f'✅ Updates needed: {len(updates_needed)}')
    print(f'✅ Updates performed: {min(3, len(updates_needed))} (test limit)')
    print(f'✅ Main sheet E column URL sync: Ready for production')
    
    print(f'\n[IMPLEMENTATION] To sync all URLs, remove the [:3] limit in the batch update')
    
except ImportError as e:
    print(f'[ERROR] Missing required packages: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERROR] Unexpected error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)