#!/usr/bin/env python3
"""
Test script for CORRECTED PJINIT Specification Implementation
Tests the corrected RealGoogleSheetsService class with the correct sheet structure
"""

import sys
import asyncio
from pathlib import Path
from pprint import pprint

# Add project path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from clients.service_adapter import ServiceAdapter, create_service_adapter

async def test_corrected_specification():
    """Test the corrected PJINIT specification implementation"""
    
    print("=" * 60)
    print("CORRECTED PJINIT SPECIFICATION TEST")
    print("=" * 60)
    print()
    
    # Create service adapter
    print("[1] Creating ServiceAdapter...")
    adapter = create_service_adapter()
    
    if not adapter.google_sheets:
        print("[ERROR] Google Sheets service not available - cannot test")
        return False
    
    print("[OK] Google Sheets service initialized")
    print()
    
    # Test data retrieval from correct sheets
    test_n_codes = ["N02413", "N02280", "N09999"]
    
    print("[2] Testing data retrieval from CORRECT sheets...")
    print("-" * 40)
    
    for n_code in test_n_codes:
        print(f"\n[TEST] N-code: {n_code}")
        print("-" * 20)
        
        # Test main sheet data retrieval (A,C,H,K,M,T columns)
        print("📊 Main sheet data (A,C,H,K,M,T columns):")
        project_info = await adapter.get_project_info(n_code)
        if project_info:
            print(f"  ✅ Found: {n_code}")
            print(f"  📝 Repository/Channel: {project_info.get('repository_name', 'N/A')}")
            print(f"  📖 Book Title: {project_info.get('book_title', 'N/A')}")
            print(f"  💬 Author Slack ID: {project_info.get('author_slack_id', 'N/A')}")
            print(f"  🐙 Author GitHub ID: {project_info.get('author_github_id', 'N/A')}")
            print(f"  📧 Author Email: {project_info.get('author_email', 'N/A')}")
        else:
            print(f"  ❌ Not found: {n_code}")
        
        # Test purchase list data retrieval (M,D columns)
        print("🛒 Purchase list data (M=N番号, D=書籍URL):")
        try:
            book_url = adapter.google_sheets.get_book_url_from_purchase_list(n_code)
            if book_url:
                print(f"  ✅ Book URL found: {book_url}")
            else:
                print(f"  ❌ Book URL not found for {n_code}")
        except Exception as e:
            print(f"  ⚠️ Error retrieving book URL: {e}")
        
        # Test task management sheet (A-J columns)
        print("📋 Task management data (A-J columns):")
        task_info = await adapter.get_task_info(n_code)
        if task_info:
            print(f"  ✅ Found {len(task_info)} task records")
            for i, task in enumerate(task_info[:2], 1):  # Show first 2 tasks
                print(f"    Task {i}: {task.get('status', 'N/A')} at {task.get('execution_time', 'N/A')}")
        else:
            print(f"  ℹ️ No task records found for {n_code}")
    
    print()
    print("[3] Testing URL synchronization between purchase list and main sheet...")
    print("-" * 50)
    
    # Test URL sync from purchase list to main sheet E column
    try:
        sync_result = await adapter.sync_purchase_list_urls(
            purchase_sheet_id="1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c",
            purchase_sheet_name="技術書典18"
        )
        
        if sync_result.get('success', False):
            print("✅ URL synchronization successful")
            print(f"   📊 Mappings found: {sync_result.get('mappings_found', 0)}")
            print(f"   🔄 Updates performed: {sync_result.get('updates_performed', 0)}")
        else:
            print(f"❌ URL synchronization failed: {sync_result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"⚠️ URL synchronization error: {e}")
    
    print()
    print("[4] Testing task record creation...")
    print("-" * 30)
    
    # Test task record creation in task management sheet
    test_n_code = "N02413"
    try:
        success = await adapter.create_task_record(
            n_code=test_n_code,
            status="Testing - Corrected Spec",
            slack_channel="test-channel",
            github_repo="test-repo",
            content="Testing corrected PJINIT specification"
        )
        
        if success:
            print(f"✅ Task record created for {test_n_code}")
        else:
            print(f"❌ Failed to create task record for {test_n_code}")
    
    except Exception as e:
        print(f"⚠️ Task record creation error: {e}")
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ Data Retrieval Sheets:")
    print("  - Main sheet: 発行計画（山城） sheet '2020.10-' (A,C,H,K,M,T)")
    print("  - Purchase list: 技術書典購入リスト sheet '技術書典18' (M,D)")
    print()
    print("✅ Data Writing Sheets:")
    print("  - Main sheet '2020.10-' E列: 書籍URL（購入リスト）")
    print("  - Task management '手動タスク管理' A-J列: execution logs")
    print()
    print("🚫 EXCLUDED sheets (no longer referenced):")
    print("  - 発行リスト作成用")
    print("  - 著者情報転記")
    print("  - Any other sheets not specified in correct specification")
    print()
    
    return True

if __name__ == "__main__":
    asyncio.run(test_corrected_specification())