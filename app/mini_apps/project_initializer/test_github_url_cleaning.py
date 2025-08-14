#!/usr/bin/env python3
"""
Test script for GitHub URL cleaning functionality
"""

# Import the clean_github_id function from service_adapter
import sys
sys.path.insert(0, '.')
from clients.service_adapter import clean_github_id

def test_github_url_cleaning():
    """Test various GitHub ID formats"""
    print("Testing GitHub URL cleaning functionality:")
    print("=" * 50)
    
    test_cases = [
        # Test case: Full URL
        ("https://github.com/ShogoAkiyama", "ShogoAkiyama"),
        # Test case: Just username
        ("ShogoAkiyama", "ShogoAkiyama"),
        # Test case: URL with trailing slash
        ("https://github.com/ShogoAkiyama/", "ShogoAkiyama/"),
        # Test case: Empty string
        ("", ""),
        # Test case: None value
        (None, ""),
        # Test case: Whitespace only
        ("   ", ""),
        # Test case: URL with whitespace
        ("  https://github.com/ShogoAkiyama  ", "ShogoAkiyama"),
        # Test case: Username with whitespace
        ("  ShogoAkiyama  ", "ShogoAkiyama"),
        # Test case: Different case URL
        ("HTTPS://GITHUB.COM/ShogoAkiyama", "HTTPS://GITHUB.COM/ShogoAkiyama"),  # Should NOT match
        # Test case: Partial URL
        ("github.com/ShogoAkiyama", "github.com/ShogoAkiyama"),  # Should NOT match
    ]
    
    all_passed = True
    
    for i, (input_val, expected) in enumerate(test_cases, 1):
        result = clean_github_id(input_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"Test {i:2}: {status}")
        print(f"  Input:    {repr(input_val)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")
        
        if result != expected:
            all_passed = False
        print()
    
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_github_url_cleaning()
    sys.exit(0 if success else 1)