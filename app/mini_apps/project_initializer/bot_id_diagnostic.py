"""
Bot ID Diagnostic Tool
Comprehensive bot identification and ID format analysis

This tool helps identify correct Bot IDs for TechZip Bot and Invitation Bot
by searching the Slack workspace and analyzing available bots.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from clients.slack_client_real import RealSlackClient

class BotIDDiagnostic:
    """Diagnostic tool for Bot ID identification"""
    
    def __init__(self, bot_token: str, user_token: str):
        self.client = RealSlackClient(bot_token, user_token)
        self.results = {}
    
    async def analyze_workspace_bots(self) -> Dict:
        """Analyze all bots in the workspace"""
        print("🔍 Analyzing workspace bots...")
        
        try:
            # Get workspace users including bots
            if self.client.user_client:
                client = self.client.user_client
            else:
                client = self.client.bot_client
                
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.users_list()
                ),
                timeout=30.0
            )
            
            if response.get("ok"):
                members = response.get("members", [])
                bots = []
                users = []
                
                for member in members:
                    if member.get("is_bot", False) or member.get("is_app_user", False):
                        bots.append({
                            "id": member.get("id"),
                            "name": member.get("name"),
                            "real_name": member.get("real_name"),
                            "display_name": member.get("profile", {}).get("display_name"),
                            "is_bot": member.get("is_bot", False),
                            "is_app_user": member.get("is_app_user", False),
                            "deleted": member.get("deleted", False)
                        })
                    else:
                        users.append({
                            "id": member.get("id"),
                            "name": member.get("name"),
                            "real_name": member.get("real_name"),
                            "deleted": member.get("deleted", False)
                        })
                
                self.results["bots"] = bots
                self.results["users"] = users
                self.results["total_members"] = len(members)
                
                print(f"✅ Found {len(bots)} bots and {len(users)} users in workspace")
                return self.results
            else:
                error_msg = response.get("error", "Unknown error")
                print(f"❌ Failed to list workspace members: {error_msg}")
                return {}
                
        except Exception as e:
            print(f"❌ Error analyzing workspace bots: {e}")
            return {}
    
    def search_techzip_bots(self) -> List[Dict]:
        """Search for TechZip-related bots"""
        print("\n🔍 Searching for TechZip-related bots...")
        
        if not self.results.get("bots"):
            print("❌ No bot data available")
            return []
        
        techzip_keywords = [
            "techzip", "tech_zip", "pdf", "泉", "fountain", 
            "technical", "book", "series", "bot"
        ]
        
        matches = []
        for bot in self.results["bots"]:
            if bot.get("deleted"):
                continue
                
            # Check all name fields
            search_fields = [
                bot.get("name", "").lower(),
                bot.get("real_name", "").lower(),
                bot.get("display_name", "").lower()
            ]
            
            for keyword in techzip_keywords:
                if any(keyword in field for field in search_fields if field):
                    matches.append(bot)
                    break
        
        print(f"✅ Found {len(matches)} potential TechZip-related bots")
        return matches
    
    def analyze_bot_id_formats(self) -> Dict:
        """Analyze Bot ID format patterns"""
        print("\n📊 Analyzing Bot ID format patterns...")
        
        if not self.results.get("bots"):
            return {}
        
        format_analysis = {
            "U_prefix": [],  # User IDs (U...)
            "A_prefix": [],  # Application IDs (A...)
            "B_prefix": [],  # Bot IDs (B...)
            "other": []
        }
        
        for bot in self.results["bots"]:
            bot_id = bot.get("id", "")
            if bot_id.startswith("U"):
                format_analysis["U_prefix"].append(bot)
            elif bot_id.startswith("A"):
                format_analysis["A_prefix"].append(bot)
            elif bot_id.startswith("B"):
                format_analysis["B_prefix"].append(bot)
            else:
                format_analysis["other"].append(bot)
        
        print(f"📈 Format Analysis:")
        print(f"  - U prefix (User IDs): {len(format_analysis['U_prefix'])}")
        print(f"  - A prefix (App IDs): {len(format_analysis['A_prefix'])}")
        print(f"  - B prefix (Bot IDs): {len(format_analysis['B_prefix'])}")
        print(f"  - Other formats: {len(format_analysis['other'])}")
        
        return format_analysis
    
    async def test_provided_bot_ids(self) -> Dict:
        """Test the user-provided Bot IDs to understand the error"""
        print("\n🧪 Testing user-provided Bot IDs...")
        
        test_results = {}
        provided_ids = {
            "TechZip Bot": "A097K6HTULW",
            "Invitation Bot": "A097NKP77EE"
        }
        
        # Create a test channel first
        try:
            channel_id = await self.client.create_channel("diagnostic-test", "Bot ID diagnostic test")
            if not channel_id:
                print("❌ Failed to create diagnostic test channel")
                return {}
            
            print(f"✅ Created diagnostic test channel: {channel_id}")
            
            for bot_name, bot_id in provided_ids.items():
                print(f"\n[TEST] Testing {bot_name} (ID: {bot_id})")
                
                try:
                    # Test user lookup by email (if it's an app, this should fail)
                    # Test direct invitation
                    result = await self.client.invite_user_to_channel(
                        channel_id, bot_id, use_user_token=True
                    )
                    
                    test_results[bot_name] = {
                        "id": bot_id,
                        "invitation_success": result,
                        "error": None
                    }
                    
                    if result:
                        print(f"✅ {bot_name} invitation successful")
                    else:
                        print(f"❌ {bot_name} invitation failed")
                        
                except Exception as e:
                    test_results[bot_name] = {
                        "id": bot_id,
                        "invitation_success": False,
                        "error": str(e)
                    }
                    print(f"❌ {bot_name} invitation error: {e}")
            
            return test_results
            
        except Exception as e:
            print(f"❌ Error during Bot ID testing: {e}")
            return {}
    
    def generate_recommendations(self, techzip_matches: List[Dict], format_analysis: Dict) -> List[str]:
        """Generate recommendations for correct Bot IDs"""
        print("\n💡 Generating Bot ID recommendations...")
        
        recommendations = []
        
        # Check if we found any TechZip-related bots
        if techzip_matches:
            recommendations.append("🎯 Found TechZip-related bot candidates:")
            for i, bot in enumerate(techzip_matches[:5], 1):  # Show top 5
                name_info = bot.get("name", "Unknown")
                real_name = bot.get("real_name", "")
                display_name = bot.get("display_name", "")
                
                name_display = f"{name_info}"
                if real_name and real_name != name_info:
                    name_display += f" ({real_name})"
                if display_name and display_name != real_name and display_name != name_info:
                    name_display += f" [{display_name}]"
                
                recommendations.append(f"   {i}. ID: {bot.get('id')} - {name_display}")
        
        # Analyze ID format patterns
        if format_analysis:
            recommendations.append("\n🔍 ID Format Analysis:")
            
            if format_analysis["U_prefix"]:
                recommendations.append(f"   - {len(format_analysis['U_prefix'])} bots use U-prefix (standard User IDs)")
                recommendations.append("     → Most likely format for bot invitations")
            
            if format_analysis["A_prefix"]:
                recommendations.append(f"   - {len(format_analysis['A_prefix'])} bots use A-prefix (Application IDs)")
                recommendations.append("     → These might be apps, not directly invitable users")
            
            if format_analysis["B_prefix"]:
                recommendations.append(f"   - {len(format_analysis['B_prefix'])} bots use B-prefix (Bot IDs)")
        
        # Current issue analysis
        recommendations.append("\n🚨 Current Issue Analysis:")
        recommendations.append("   - User-provided IDs (A097K6HTULW, A097NKP77EE) start with 'A'")
        recommendations.append("   - 'A' prefix typically indicates Application IDs, not User IDs")
        recommendations.append("   - Slack API conversations_invite expects User IDs (usually U-prefix)")
        recommendations.append("   - Need to find corresponding User IDs for these applications")
        
        # Action items
        recommendations.append("\n📋 Recommended Actions:")
        recommendations.append("   1. Look for User IDs (U-prefix) that correspond to TechZip bots")
        recommendations.append("   2. Check if A097K6HTULW/A097NKP77EE are app IDs that need different invite methods")
        recommendations.append("   3. Test U-prefix IDs from TechZip bot candidates above")
        recommendations.append("   4. Consider using Slack App installation instead of user invitation")
        
        return recommendations

async def main():
    """Main diagnostic routine"""
    print("Bot ID Diagnostic Tool")
    print("=" * 50)
    
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    user_token = os.getenv('SLACK_USER_TOKEN')
    
    if not bot_token or not user_token:
        print("❌ Missing SLACK_BOT_TOKEN or SLACK_USER_TOKEN")
        return
    
    diagnostic = BotIDDiagnostic(bot_token, user_token)
    
    # Step 1: Analyze all workspace bots
    await diagnostic.analyze_workspace_bots()
    
    # Step 2: Search for TechZip-related bots
    techzip_matches = diagnostic.search_techzip_bots()
    
    # Step 3: Analyze Bot ID format patterns
    format_analysis = diagnostic.analyze_bot_id_formats()
    
    # Step 4: Test provided Bot IDs
    test_results = await diagnostic.test_provided_bot_ids()
    
    # Step 5: Generate recommendations
    recommendations = diagnostic.generate_recommendations(techzip_matches, format_analysis)
    
    # Display comprehensive results
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC RESULTS SUMMARY")
    print("=" * 50)
    
    if techzip_matches:
        print("\n🎯 TechZip Bot Candidates:")
        for i, bot in enumerate(techzip_matches, 1):
            status = "🟢 Active" if not bot.get("deleted") else "🔴 Deleted"
            print(f"   {i}. {bot.get('id')} - {bot.get('name')} {status}")
    
    if test_results:
        print("\n🧪 User-Provided ID Test Results:")
        for bot_name, result in test_results.items():
            success = "✅ Success" if result["invitation_success"] else "❌ Failed"
            error = f" ({result['error']})" if result.get("error") else ""
            print(f"   {bot_name} ({result['id']}): {success}{error}")
    
    print("\n💡 RECOMMENDATIONS:")
    for recommendation in recommendations:
        print(recommendation)
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete!")
    print("💡 Use the candidate User IDs above to replace A-prefixed IDs")
    print("🔧 Update slack_client.py and slack_client_real.py with correct IDs")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")