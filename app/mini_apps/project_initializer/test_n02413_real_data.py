#!/usr/bin/env python3
"""
Test N02413 with real Google Sheets data integration
"""
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

from clients.service_adapter import create_service_adapter

async def test_n02413_real_data():
    print('[INFO] Testing N02413 with real Google Sheets data...')
    
    # Create service adapter
    adapter = create_service_adapter()
    
    if not adapter.google_sheets:
        print('[ERROR] Google Sheets service not available')
        return
    
    print('[OK] Google Sheets service is available')
    
    # Test N02413 project info retrieval
    print('\n[TEST] Retrieving project info for N02413...')
    try:
        project_info = await adapter.get_project_info('N02413')
        if project_info:
            print('[SUCCESS] Project data retrieved:')
            for key, value in project_info.items():
                print(f'  {key}: {value}')
                
            # Check if this is real data (not mock)
            repository_name = project_info.get('repository_name', '')
            if repository_name.startswith('test-repo-'):
                print('[WARN] Still receiving mock data')
                return False
            else:
                print('[SUCCESS] Real Google Sheets data confirmed!')
                
                # Test additional functionality
                print('\n[TEST] Testing book URL retrieval...')
                # Legacy compatibility test
                from clients.service_adapter import GoogleSheetsClient
                
                legacy_client = GoogleSheetsClient()
                book_url = await legacy_client.get_book_url_from_purchase_list('N02413')
                
                print(f'[INFO] Book URL: {book_url}')
                
                print('\n[SUCCESS] N02413 integration test completed successfully!')
                print('[INFO] All services are working with real data')
                return True
        else:
            print('[ERROR] No project info found for N02413')
            return False
            
    except Exception as e:
        print(f'[ERROR] Error retrieving project info: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_n02413_real_data())
    if success:
        print('\n[RESULT] ✅ N02413 Real Data Integration: PASSED')
    else:
        print('\n[RESULT] ❌ N02413 Real Data Integration: FAILED')
        sys.exit(1)