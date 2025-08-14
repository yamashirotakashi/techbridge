"""
Test Channel Creation with name_taken Error Reproduction
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

async def test_channel_creation_with_existing():
    """Test channel creation that will trigger name_taken error"""
    print("=== Testing Channel Creation with Existing Channel ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token or not user_token:
        print("[ERROR] Missing tokens")
        return
    
    print(f"[INFO] Bot token: ...{bot_token[-8:]}")
    print(f"[INFO] User token: ...{user_token[-8:]}")
    
    client = RealSlackClient(bot_token, user_token)
    
    # First validate tokens
    print("[INFO] Validating tokens...")
    validation_results = await client.validate_tokens()
    print(f"[INFO] Bot token valid: {validation_results['bot_token_valid']}")
    print(f"[INFO] User token valid: {validation_results['user_token_valid']}")
    
    if not all(validation_results.values()):
        print("[ERROR] Token validation failed")
        return
    
    # Test with a common channel name that might exist
    test_channel_name = "n02279-test-channel"
    print(f"\n[INFO] Attempting to create channel: {test_channel_name}")
    
    try:
        channel_id = await client.create_channel(test_channel_name, "Test Topic - Delete Me")
        
        if channel_id:
            print(f"[SUCCESS] Channel created or found: {channel_id}")
        else:
            print("[ERROR] Channel creation failed - returned None")
            
    except Exception as e:
        print(f"[ERROR] Channel creation exception: {e}")

async def test_channel_search_directly():
    """Test the channel search functionality directly"""
    print("\n=== Testing Channel Search Directly ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    client = RealSlackClient(bot_token, user_token)
    
    # Test channel search
    test_channel_name = "n02279-test-channel"
    print(f"[INFO] Searching for existing channel: {test_channel_name}")
    
    try:
        existing_channel = await client._find_existing_channel(test_channel_name)
        
        if existing_channel:
            print(f"[SUCCESS] Found existing channel: {existing_channel}")
        else:
            print("[INFO] No existing channel found")
            
    except Exception as e:
        print(f"[ERROR] Channel search exception: {e}")

async def main():
    """Run channel creation tests"""
    print("PJINIT Channel Creation Test - name_taken Error Investigation")
    print("=" * 70)
    
    await test_channel_creation_with_existing()
    await test_channel_search_directly()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")