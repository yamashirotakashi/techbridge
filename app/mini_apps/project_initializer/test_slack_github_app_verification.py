"""
Slack GitHub App ID Verification Test
GitHub App ID の正確性を検証し、正しい ID を特定する
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

async def verify_github_app_in_slack():
    """Slack ワークスペース内の GitHub App を検索し、正しい ID を特定"""
    print("=== Slack GitHub App ID Verification ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token or not user_token:
        print("[ERROR] Missing tokens")
        return False
    
    client = RealSlackClient(bot_token, user_token)
    
    # Test current GitHub App ID
    current_github_app_id = "U06QXGWNLP5"
    print(f"[INFO] Current GitHub App ID: {current_github_app_id}")
    
    # Try to find GitHub-related users in the workspace
    print("\n[INFO] Searching for GitHub-related users in workspace...")
    
    # Use both bot and user clients to list users
    for client_name, client_obj in [("bot", client.bot_client), ("user", client.user_client)]:
        if not client_obj:
            continue
            
        try:
            print(f"\n[INFO] Listing users with {client_name} token...")
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client_obj.users_list(limit=1000)
                ),
                timeout=20.0
            )
            
            if response.get("ok"):
                members = response.get("members", [])
                print(f"[INFO] Found {len(members)} members in workspace")
                
                # Look for GitHub-related users
                github_users = []
                for member in members:
                    user_id = member.get("id")
                    real_name = member.get("real_name", "")
                    display_name = member.get("profile", {}).get("display_name", "")
                    name = member.get("name", "")
                    is_bot = member.get("is_bot", False)
                    
                    # Check if this looks like a GitHub user
                    if any(keyword.lower() in str(field).lower() for field in [real_name, display_name, name] 
                           for keyword in ["github", "git", "app"]) or is_bot:
                        github_users.append({
                            "id": user_id,
                            "name": name,
                            "real_name": real_name,
                            "display_name": display_name,
                            "is_bot": is_bot
                        })
                
                if github_users:
                    print(f"\n[FOUND] Potential GitHub-related users:")
                    for user in github_users:
                        print(f"  ID: {user['id']} | Name: {user['name']} | Real Name: {user['real_name']} | Display: {user['display_name']} | Bot: {user['is_bot']}")
                    
                    # Try to find the exact GitHub App
                    for user in github_users:
                        if user['id'] == current_github_app_id:
                            print(f"✅ [CONFIRMED] GitHub App ID {current_github_app_id} found in workspace!")
                            return True
                    
                    print(f"❌ [NOT FOUND] GitHub App ID {current_github_app_id} NOT found in workspace")
                    
                    # Suggest alternative IDs
                    bot_users = [user for user in github_users if user['is_bot']]
                    if bot_users:
                        print(f"\n[SUGGESTION] Possible GitHub App candidates:")
                        for user in bot_users:
                            print(f"  ID: {user['id']} | Name: {user['name']} | Real Name: {user['real_name']}")
                else:
                    print("[INFO] No GitHub-related users found")
                    
                break  # Successfully got user list, don't try other client
                
            else:
                error_msg = response.get("error", "Unknown error")
                print(f"[ERROR] Failed to list users with {client_name} token: {error_msg}")
                
        except Exception as e:
            print(f"[ERROR] Exception listing users with {client_name} token: {e}")
    
    return False

async def test_github_app_invitation():
    """Test GitHub App invitation with different methods"""
    print("\n=== Testing GitHub App Invitation Methods ===")
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    client = RealSlackClient(bot_token, user_token)
    
    # Create a test channel for GitHub App invitation testing
    test_channel_name = "github-app-test"
    print(f"[INFO] Creating test channel: {test_channel_name}")
    
    try:
        channel_id = await client.create_channel(test_channel_name, "GitHub App invitation test")
        if channel_id:
            print(f"[SUCCESS] Test channel created: {channel_id}")
            
            # Test different GitHub App IDs
            github_app_ids_to_test = [
                "U06QXGWNLP5",  # Current ID
                # Add other potential IDs here if found during verification
            ]
            
            for app_id in github_app_ids_to_test:
                print(f"\n[TEST] Testing GitHub App invitation: {app_id}")
                
                # Test with bot token
                try:
                    result = await client.invite_github_app_with_bot_token(channel_id, app_id)
                    if result:
                        print(f"✅ [SUCCESS] GitHub App {app_id} invited with bot token")
                    else:
                        print(f"❌ [FAILED] GitHub App {app_id} invitation failed with bot token")
                except Exception as e:
                    print(f"❌ [ERROR] GitHub App {app_id} invitation error with bot token: {e}")
                
                # Test with user token (direct invitation)
                try:
                    result = await client.invite_user_to_channel(channel_id, app_id, use_user_token=True)
                    if result:
                        print(f"✅ [SUCCESS] GitHub App {app_id} invited with user token")
                    else:
                        print(f"❌ [FAILED] GitHub App {app_id} invitation failed with user token")
                except Exception as e:
                    print(f"❌ [ERROR] GitHub App {app_id} invitation error with user token: {e}")
                    
        else:
            print("[ERROR] Failed to create test channel")
            return False
            
    except Exception as e:
        print(f"[ERROR] Channel creation failed: {e}")
        return False
    
    return True

async def main():
    """Run GitHub App verification tests"""
    print("PJINIT GitHub App Slack Integration Verification")
    print("=" * 60)
    
    # Step 1: Verify GitHub App exists in workspace
    app_found = await verify_github_app_in_slack()
    
    # Step 2: Test invitation methods
    if app_found:
        await test_github_app_invitation()
    else:
        print("\n[WARNING] GitHub App not found in workspace - invitation tests skipped")
        print("\n[SOLUTION] To fix this issue:")
        print("1. Install GitHub App in your Slack workspace")
        print("2. Find the correct GitHub App ID from the user list above")
        print("3. Update the GITHUB_APP_ID constant in slack_client_real.py")
    
    print("\n" + "=" * 60)
    print("GitHub App verification complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nVerification interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")