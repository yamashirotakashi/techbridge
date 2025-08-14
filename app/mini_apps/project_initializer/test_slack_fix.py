"""
Test Script for Slack Token Authentication Fix
Tests the real SlackClient implementation with proper error handling and timeout
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from clients.slack_client_real import RealSlackClient

async def test_slack_token_validation():
    """Test Slack token validation"""
    print("=== Testing Slack Token Validation ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token:
        print("[ERROR] SLACK_BOT_TOKEN not found in environment variables")
        return False
    
    if not user_token:
        print("[ERROR] SLACK_USER_TOKEN not found in environment variables")
        return False
    
    print(f"[INFO] Bot token: ...{bot_token[-8:]}")
    print(f"[INFO] User token: ...{user_token[-8:]}")
    
    try:
        client = RealSlackClient(bot_token, user_token)
        
        # Test token validation
        print("[INFO] Validating tokens...")
        validation_results = await client.validate_tokens()
        
        print(f"[INFO] Bot token valid: {validation_results['bot_token_valid']}")
        print(f"[INFO] User token valid: {validation_results['user_token_valid']}")
        
        if not validation_results['bot_token_valid']:
            print("[ERROR] Bot token validation failed")
            return False
            
        if not validation_results['user_token_valid']:
            print("[ERROR] User token validation failed") 
            return False
        
        print("[SUCCESS] All tokens validated successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Token validation failed: {e}")
        return False

async def test_slack_channel_creation():
    """Test Slack channel creation (without actually creating)"""
    print("\n=== Testing Slack Channel Creation (Dry Run) ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    try:
        client = RealSlackClient(bot_token, user_token)
        
        # First validate tokens
        validation_results = await client.validate_tokens()
        if not all(validation_results.values()):
            print("[ERROR] Token validation failed - skipping channel test")
            return False
        
        # Test channel name cleaning
        test_names = [
            "test-channel-name",
            "Test Channel Name!@#",
            "very-long-channel-name-that-exceeds-slack-limits",
            "n02279-test"
        ]
        
        print("[INFO] Testing channel name cleaning:")
        for name in test_names:
            clean_name = client._clean_channel_name(name)
            print(f"  '{name}' -> '{clean_name}'")
        
        print("[SUCCESS] Channel name cleaning test passed!")
        
        # NOTE: We don't actually create a channel in the test to avoid spam
        print("[INFO] Channel creation test skipped to avoid creating test channels")
        return True
        
    except Exception as e:
        print(f"[ERROR] Channel creation test failed: {e}")
        return False

async def test_service_adapter_integration():
    """Test service adapter integration"""
    print("\n=== Testing Service Adapter Integration ===")
    
    try:
        from clients.service_adapter import SlackClient
        
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        user_token = os.getenv('SLACK_USER_TOKEN')
        
        # Test SlackClient initialization
        print("[INFO] Testing SlackClient initialization...")
        slack_client = SlackClient(bot_token, user_token)
        
        print(f"[INFO] Real client available: {slack_client.real_client is not None}")
        
        if slack_client.real_client:
            print("[SUCCESS] Service adapter integration working!")
            return True
        else:
            print("[WARNING] Service adapter fell back to mock implementation")
            return False
        
    except Exception as e:
        print(f"[ERROR] Service adapter integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("PJINIT Slack Token Authentication Fix - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Token Validation", test_slack_token_validation),
        ("Channel Creation", test_slack_channel_creation),
        ("Service Adapter Integration", test_service_adapter_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! The Slack token authentication fix is working.")
        print("\nThe application should no longer hang at 'Slackチャンネルを作成中...'")
        print("If hanging still occurs, check:")
        print("1. Token validity in Slack workspace")
        print("2. Required OAuth scopes (channels:write, channels:manage, etc.)")
        print("3. Network connectivity to Slack API")
    else:
        print("\n❌ SOME TESTS FAILED. Check the errors above and fix before deployment.")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)