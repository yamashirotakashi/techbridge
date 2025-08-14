import sys
sys.path.insert(0, '.')
from clients.service_adapter import create_service_adapter
import asyncio

async def test_real_google_sheets_after_enable():
    print('[INFO] Testing Google Sheets integration after API enablement...')
    adapter = create_service_adapter()
    
    if adapter.google_sheets:
        print('[OK] Google Sheets service is available')
        
        # Test the connection
        if hasattr(adapter.google_sheets, 'test_connection'):
            connection_ok = adapter.google_sheets.test_connection()
            print(f'[INFO] Connection test: {connection_ok}')
        
        # Test with N02413
        project_info = await adapter.get_project_info('N02413')
        if project_info:
            print('[SUCCESS] Project data retrieved:')
            print(f'  N-code: {project_info.get("n_code")}')
            print(f'  Repository Name: {project_info.get("repository_name")}')
            print(f'  Channel Name: {project_info.get("channel_name")}')
            print(f'  Row: {project_info.get("row")}')
            
            # Check if real data
            if project_info.get('repository_name', '').startswith('test-repo-'):
                print('[WARN] Still mock data - API may need more time or not enabled')
            else:
                print('[SUCCESS] ✅ REAL Google Sheets data confirmed!')
        else:
            print('[WARN] No project info found for N02413')
    else:
        print('[ERROR] Google Sheets service not available')

# Run the test
asyncio.run(test_real_google_sheets_after_enable())
