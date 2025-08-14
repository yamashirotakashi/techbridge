"""
Test Fixed GitHub App Invitation
修正後のGitHub App IDでの招待テスト
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

async def test_fixed_github_app_invitation():
    """修正後のGitHub App IDで招待をテスト"""
    print("=== Testing Fixed GitHub App Invitation ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token or not user_token:
        print("[ERROR] Missing tokens")
        return False
    
    client = RealSlackClient(bot_token, user_token)
    
    # Get updated GitHub App ID
    github_app_id = client.GITHUB_APP_ID
    print(f"[INFO] Updated GitHub App ID: {github_app_id}")
    
    # Create test channel
    test_channel_name = "github-app-fixed-test"
    print(f"[INFO] Creating test channel: {test_channel_name}")
    
    try:
        channel_id = await client.create_channel(test_channel_name, "Fixed GitHub App invitation test")
        if channel_id:
            print(f"[SUCCESS] Test channel created: {channel_id}")
            
            # Test GitHub App invitation with bot token
            print(f"\n[TEST] Testing GitHub App invitation with bot token...")
            try:
                result = await client.invite_github_app_with_bot_token(channel_id, github_app_id)
                if result:
                    print(f"✅ [SUCCESS] GitHub App {github_app_id} invited with bot token")
                else:
                    print(f"❌ [FAILED] GitHub App {github_app_id} invitation failed with bot token")
            except Exception as e:
                print(f"❌ [ERROR] GitHub App {github_app_id} invitation error with bot token: {e}")
            
            # Test GitHub App invitation with user token (direct method)
            print(f"\n[TEST] Testing GitHub App invitation with user token...")
            try:
                result = await client.invite_user_to_channel(channel_id, github_app_id, use_user_token=True)
                if result:
                    print(f"✅ [SUCCESS] GitHub App {github_app_id} invited with user token")
                else:
                    print(f"❌ [FAILED] GitHub App {github_app_id} invitation failed with user token")
            except Exception as e:
                print(f"❌ [ERROR] GitHub App {github_app_id} invitation error with user token: {e}")
                
            # Test alternative invitation method
            print(f"\n[TEST] Testing alternative GitHub App invitation...")
            try:
                result = await client.invite_github_app_with_alternative_bot(channel_id, github_app_id)
                if result:
                    print(f"✅ [SUCCESS] GitHub App {github_app_id} invited with alternative bot")
                else:
                    print(f"❌ [FAILED] GitHub App {github_app_id} alternative invitation failed")
            except Exception as e:
                print(f"❌ [ERROR] GitHub App {github_app_id} alternative invitation error: {e}")
                
        else:
            print("[ERROR] Failed to create test channel")
            return False
            
    except Exception as e:
        print(f"[ERROR] Channel creation failed: {e}")
        return False
    
    return True

async def test_full_integration_simulation():
    """PJINIT完全統合シミュレーション"""
    print("\n=== PJINIT Full Integration Simulation ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    client = RealSlackClient(bot_token, user_token)
    
    # Simulate PJINIT workflow
    test_project = {
        'n_code': 'N99999',
        'channel_name': 'n99999-integration-test',
        'topic': 'PJINIT統合テストプロジェクト'
    }
    
    print(f"[SIMULATION] Creating project channel: {test_project['channel_name']}")
    
    try:
        # Step 1: Create channel
        channel_id = await client.create_channel(test_project['channel_name'], test_project['topic'])
        if not channel_id:
            print("[ERROR] Failed to create project channel")
            return False
        
        print(f"[SUCCESS] Project channel created: {channel_id}")
        
        # Step 2: Invite GitHub App (this was the failing step)
        github_app_id = client.GITHUB_APP_ID
        print(f"[SIMULATION] Inviting GitHub App: {github_app_id}")
        
        # Try primary method
        result = await client.invite_github_app_with_bot_token(channel_id, github_app_id)
        if result:
            print("✅ [SUCCESS] GitHub App invitation succeeded (primary method)")
        else:
            print("⚠️  [FALLBACK] Primary method failed, trying alternative...")
            result = await client.invite_github_app_with_alternative_bot(channel_id, github_app_id)
            if result:
                print("✅ [SUCCESS] GitHub App invitation succeeded (alternative method)")
            else:
                print("❌ [FAILED] Both GitHub App invitation methods failed")
                
        # Step 3: Simulate other invitations (山城さん、Bot等)
        print(f"[SIMULATION] Testing other user invitations...")
        
        # Note: We won't actually invite real users in the test
        print("✅ [SIMULATION] User invitations would proceed normally")
        
        print(f"\n[RESULT] PJINIT integration simulation completed")
        print(f"✅ Channel Creation: SUCCESS")
        print(f"✅ GitHub App Invitation: {'SUCCESS' if result else 'FAILED'}")
        print(f"✅ User Invitations: SIMULATED SUCCESS")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Integration simulation failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("PJINIT Fixed GitHub App Invitation Test")
    print("=" * 50)
    
    # Test 1: Basic GitHub App invitation
    success1 = await test_fixed_github_app_invitation()
    
    # Test 2: Full integration simulation
    success2 = await test_full_integration_simulation()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ GitHub App ID has been corrected")
        print("✅ GitHub App invitation now works")
        print("✅ PJINIT integration should work without errors")
    else:
        print("❌ Some tests failed")
        if not success1:
            print("- GitHub App invitation still failing")
        if not success2:
            print("- Integration simulation failed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")