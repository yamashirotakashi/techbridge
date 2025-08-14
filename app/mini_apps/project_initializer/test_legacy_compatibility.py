#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legacy Compatibility Test Script
PJINIT Phase 1リファクタリング版の互換性テスト
"""

import sys
import asyncio
from pathlib import Path

# 現在のディレクトリをpythonpathに追加
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from clients.service_adapter import GoogleSheetsClient

async def test_legacy_compatibility():
    """Legacy互換性のテスト"""
    print("=== Legacy Compatibility Test ===")
    
    # GoogleSheetsClientの初期化
    client = GoogleSheetsClient()
    print("✅ GoogleSheetsClient initialized")
    
    # Test 1: get_project_info with 2 arguments (legacy call)
    print("\n--- Test 1: get_project_info(planning_sheet_id, n_code) ---")
    try:
        planning_sheet_id = "17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ"
        n_code = "N02280"
        
        # Legacy互換性テスト（オリジナル版の呼び出し方）
        result = await client.get_project_info(planning_sheet_id, n_code)
        
        if result:
            print("✅ get_project_info succeeded")
            print(f"   Book Title: {result.get('book_title')}")
            print(f"   Author: {result.get('author')}")
        else:
            print("❌ get_project_info returned None")
            
    except Exception as e:
        print(f"❌ get_project_info error: {e}")
    
    # Test 2: get_book_url_from_purchase_list with 2 arguments (legacy call)
    print("\n--- Test 2: get_book_url_from_purchase_list(purchase_sheet_id, n_code) ---")
    try:
        purchase_sheet_id = "1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c"
        n_code = "N02280"
        
        # Legacy互換性テスト（オリジナル版の呼び出し方）
        url = await client.get_book_url_from_purchase_list(purchase_sheet_id, n_code)
        
        if url:
            print("✅ get_book_url_from_purchase_list succeeded")
            print(f"   Book URL: {url}")
        else:
            print("❌ get_book_url_from_purchase_list returned None")
            
    except Exception as e:
        print(f"❌ get_book_url_from_purchase_list error: {e}")
    
    # Test 3: Different N-codes
    print("\n--- Test 3: Different N-codes ---")
    test_codes = ["N09999", "N0271VG", "N99999"]
    
    for test_n_code in test_codes:
        try:
            print(f"\nTesting N-code: {test_n_code}")
            
            # プロジェクト情報取得
            project_info = await client.get_project_info("dummy_sheet_id", test_n_code)
            if project_info:
                print(f"  ✅ Project info found: {project_info.get('book_title')}")
            
            # 書籍URL取得
            book_url = await client.get_book_url_from_purchase_list("dummy_sheet_id", test_n_code)
            if book_url:
                print(f"  ✅ Book URL found: {book_url}")
                
        except Exception as e:
            print(f"  ❌ Error with {test_n_code}: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_legacy_compatibility())