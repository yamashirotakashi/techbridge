#!/usr/bin/env python3
"""
Integration test for GitHub URL processing in the service adapter
Simulates the actual Google Sheets data flow
"""

import sys
sys.path.insert(0, '.')
from clients.service_adapter import clean_github_id

def test_simulated_google_sheets_processing():
    """Test simulated Google Sheets row processing with GitHub URLs"""
    print("Testing integrated GitHub URL processing:")
    print("=" * 60)
    
    # Simulate Google Sheets rows (M column = index 12)
    test_rows = [
        # Row 1: N-code with full GitHub URL in M column
        ["N4275FM", "", "repo-n4275fm", "", "", "", "", "Course Book Title", "", "", "author_slack_id", "", "https://github.com/ShogoAkiyama", "", "", "", "", "", "", "author@example.com"],
        
        # Row 2: N-code with just username in M column  
        ["N4276XX", "", "repo-n4276xx", "", "", "", "", "Another Book", "", "", "another_slack_id", "", "JustUsername", "", "", "", "", "", "", "another@example.com"],
        
        # Row 3: N-code with URL containing whitespace
        ["N4277YY", "", "repo-n4277yy", "", "", "", "", "Third Book", "", "", "third_slack", "", "  https://github.com/WhitespaceUser  ", "", "", "", "", "", "", "third@example.com"],
        
        # Row 4: N-code with empty GitHub ID
        ["N4278ZZ", "", "repo-n4278zz", "", "", "", "", "Fourth Book", "", "", "fourth_slack", "", "", "", "", "", "", "", "", "fourth@example.com"],
    ]
    
    expected_results = [
        ("N4275FM", "ShogoAkiyama"),
        ("N4276XX", "JustUsername"),
        ("N4277YY", "WhitespaceUser"),
        ("N4278ZZ", ""),
    ]
    
    print("Simulating Google Sheets row processing:")
    print()
    
    all_passed = True
    
    for i, (row, (expected_n_code, expected_github_id)) in enumerate(zip(test_rows, expected_results), 1):
        # Simulate the actual processing logic from service_adapter.py
        n_code = row[0].strip().upper()  # A列: N番号
        raw_github_id = row[12] if len(row) > 12 and row[12] else ""  # M列: 著者GithubID
        processed_github_id = clean_github_id(raw_github_id)
        
        # Verify results
        n_code_ok = n_code == expected_n_code
        github_id_ok = processed_github_id == expected_github_id
        test_passed = n_code_ok and github_id_ok
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"Test {i}: {status}")
        print(f"  N-Code: {n_code} ({'✓' if n_code_ok else '✗'})")
        print(f"  Raw GitHub ID:        {repr(raw_github_id)}")
        print(f"  Expected GitHub ID:   {repr(expected_github_id)}")
        print(f"  Processed GitHub ID:  {repr(processed_github_id)} ({'✓' if github_id_ok else '✗'})")
        print()
        
        if not test_passed:
            all_passed = False
    
    print("=" * 60)
    
    # Test the actual service adapter mock
    print("Testing MockGoogleSheetsService integration:")
    from clients.service_adapter import MockGoogleSheetsService
    
    mock_service = MockGoogleSheetsService()
    mock_result = mock_service.search_n_code("N1234")
    
    print(f"Mock service result: {mock_result}")
    print(f"Mock GitHub ID: {repr(mock_result.get('author_github_id'))}")
    print()
    
    if all_passed:
        print("🎉 All integration tests passed!")
        print("✅ GitHub URL cleaning is working correctly in the service layer")
    else:
        print("❌ Some integration tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_simulated_google_sheets_processing()
    sys.exit(0 if success else 1)