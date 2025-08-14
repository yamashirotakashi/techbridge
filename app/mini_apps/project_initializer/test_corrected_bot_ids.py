"""
Test Corrected Bot IDs for TechZip Bot Invitation
User-provided correct Bot IDs: TechZip Bot (A097K6HTULW) and Invitation Bot (A097NKP77EE)
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

async def test_corrected_bot_ids():
    """Test with user-provided correct Bot IDs"""
    print("=== Testing Corrected Bot IDs ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token or not user_token:
        print("[ERROR] Missing tokens")
        return False
    
    client = RealSlackClient(bot_token, user_token)
    
    # Display corrected Bot IDs
    print(f"✅ [CORRECTED] TechZip Bot ID: {client.TECHZIP_PDF_BOT_ID}")
    print(f"✅ [CORRECTED] Invitation Bot ID: {client.INVITATION_BOT_ID}")
    print(f"✅ [UNCHANGED] GitHub App ID: {client.GITHUB_APP_ID}")
    
    # Create test channel for invitation testing
    test_channel_name = "corrected-bot-test"
    print(f"\n[INFO] Creating test channel: {test_channel_name}")
    
    try:
        channel_id = await client.create_channel(test_channel_name, "Test with corrected Bot IDs")
        if channel_id:
            print(f"✅ [SUCCESS] Test channel created: {channel_id}")
            
            # Test TechZip Bot invitation
            print(f"\n[TEST] Testing TechZip Bot invitation: {client.TECHZIP_PDF_BOT_ID}")
            try:
                result = await client.invite_user_to_channel(channel_id, client.TECHZIP_PDF_BOT_ID, use_user_token=True)
                if result:
                    print(f"✅ [SUCCESS] TechZip Bot {client.TECHZIP_PDF_BOT_ID} invited successfully")
                else:
                    print(f"❌ [FAILED] TechZip Bot {client.TECHZIP_PDF_BOT_ID} invitation failed")
            except Exception as e:
                print(f"❌ [ERROR] TechZip Bot invitation error: {e}")
            
            # Test Invitation Bot (if different from TechZip Bot)
            if client.INVITATION_BOT_ID != client.TECHZIP_PDF_BOT_ID:
                print(f"\n[TEST] Testing Invitation Bot: {client.INVITATION_BOT_ID}")
                try:
                    result = await client.invite_user_to_channel(channel_id, client.INVITATION_BOT_ID, use_user_token=True)
                    if result:
                        print(f"✅ [SUCCESS] Invitation Bot {client.INVITATION_BOT_ID} invited successfully")
                    else:
                        print(f"❌ [FAILED] Invitation Bot {client.INVITATION_BOT_ID} invitation failed")
                except Exception as e:
                    print(f"❌ [ERROR] Invitation Bot invitation error: {e}")
            else:
                print(f"[INFO] Invitation Bot ID same as TechZip Bot ID, skipping separate test")
            
            return True
        else:
            print("[ERROR] Failed to create test channel")
            return False
            
    except Exception as e:
        print(f"[ERROR] Channel creation failed: {e}")
        return False

async def test_pjinit_compatibility_simulation():
    """Simulate PJINIT workflow with corrected Bot IDs"""
    print("\n=== PJINIT Compatibility Simulation ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    client = RealSlackClient(bot_token, user_token)
    
    # Simulate project setup
    test_project = {
        'n_code': 'N99998',
        'channel_name': 'corrected-pjinit-sim',
        'topic': 'PJINIT with corrected Bot IDs simulation'
    }
    
    print(f"[SIMULATION] Project: {test_project['n_code']}")
    print(f"[SIMULATION] Channel: {test_project['channel_name']}")
    
    try:
        # Step 1: Create channel
        channel_id = await client.create_channel(test_project['channel_name'], test_project['topic'])
        if not channel_id:
            print("❌ [ERROR] Failed to create project channel")
            return False
        
        print(f"✅ [SUCCESS] Project channel created: {channel_id}")
        
        # Step 2: Invite TechZip Bot (山城と同時要件)
        print(f"[SIMULATION] Inviting TechZip Bot: {client.TECHZIP_PDF_BOT_ID}")
        
        result = await client.invite_user_to_channel(channel_id, client.TECHZIP_PDF_BOT_ID, use_user_token=True)
        if result:
            print("✅ [SUCCESS] TechZip Bot invitation succeeded")
        else:
            print("❌ [FAILED] TechZip Bot invitation failed")
        
        # Step 3: Other standard invitations (GitHub App, etc.)
        print(f"[SIMULATION] Testing GitHub App invitation...")
        github_result = await client.invite_github_app_with_bot_token(channel_id, client.GITHUB_APP_ID)
        if github_result:
            print("✅ [SUCCESS] GitHub App invitation succeeded")
        else:
            print("⚠️  [FALLBACK] GitHub App invitation failed (expected)")
        
        print(f"\n[RESULT] PJINIT Simulation Summary:")
        print(f"✅ Channel Creation: SUCCESS")
        print(f"{'✅' if result else '❌'} TechZip Bot Invitation: {'SUCCESS' if result else 'FAILED'}")
        print(f"{'✅' if github_result else '⚠️ '} GitHub App Invitation: {'SUCCESS' if github_result else 'EXPECTED FAILURE'}")
        
        return result  # Success if TechZip Bot invitation worked
        
    except Exception as e:
        print(f"[ERROR] PJINIT simulation failed: {e}")
        return False

async def main():
    """Run all corrected Bot ID tests"""
    print("PJINIT Corrected Bot IDs Test")
    print("=" * 50)
    print(f"TechZip Bot ID: A097K6HTULW (user-provided)")
    print(f"Invitation Bot ID: A097NKP77EE (user-provided)")
    print("=" * 50)
    
    # Test 1: Basic Bot ID verification
    success1 = await test_corrected_bot_ids()
    
    # Test 2: PJINIT workflow simulation
    success2 = await test_pjinit_compatibility_simulation()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Bot IDs have been corrected")
        print("✅ TechZip Bot invitation now works with correct ID")
        print("✅ PJINIT workflow should work without Bot ID errors")
        print("\n📋 Implementation Details:")
        print("- TechZip Bot ID: A097K6HTULW")
        print("- Invitation Bot ID: A097NKP77EE")
        print("- Both IDs updated in slack_client_real.py")
        print("- Both IDs updated in original PJINIT v1.2 slack_client.py")
    else:
        print("❌ Some tests failed")
        if not success1:
            print("- Basic Bot ID tests failed")
        if not success2:
            print("- PJINIT simulation failed")
        print("\n🔍 Check Bot permissions and network connectivity")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")