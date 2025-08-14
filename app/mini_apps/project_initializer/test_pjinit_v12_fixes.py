#!/usr/bin/env python3
"""
PJINIT v1.2 Fix Verification Test
Tests all the critical fixes implemented for PJINIT v1.2 compatibility

Fixed Issues:
1. TechZip Bot ID corrected to A097K6HTULW (App ID)
2. GitHub service changed from Mock to Real implementation
3. GitHub organization mode disabled (personal token mode)
4. Invitation Bot token changed from Bot Token to User Token
5. PJINIT v1.2 exact invitation mechanism implemented
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_env_configuration():
    """Test 1: Verify .env file has correct configuration"""
    logger.info("🔍 Test 1: Checking .env configuration...")
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    results = {
        "github_org_disabled": False,
        "invitation_bot_token_format": False,
        "github_token_present": False
    }
    
    # Check if GITHUB_ORG is commented out (personal token mode)
    if "# GITHUB_ORG=irdtechbook" in env_content:
        results["github_org_disabled"] = True
        logger.info("✅ GITHUB_ORG is disabled (personal token mode)")
    else:
        logger.error("❌ GITHUB_ORG should be disabled for personal token")
    
    # Check if SLACK_INVITATION_BOT_TOKEN is User Token format
    for line in env_content.split('\n'):
        if line.startswith('SLACK_INVITATION_BOT_TOKEN='):
            token = line.split('=', 1)[1]
            if token.startswith('xoxp-'):
                results["invitation_bot_token_format"] = True
                logger.info("✅ SLACK_INVITATION_BOT_TOKEN is User Token (xoxp-)")
            else:
                logger.error(f"❌ SLACK_INVITATION_BOT_TOKEN should be User Token, got: {token[:10]}...")
                
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1]
            if token and len(token) > 10:
                results["github_token_present"] = True
                logger.info("✅ GITHUB_TOKEN is configured")
    
    return results

def test_techzip_bot_ids():
    """Test 2: Verify TechZip Bot ID is correct in all files"""
    logger.info("🔍 Test 2: Checking TechZip Bot ID consistency...")
    
    files_to_check = [
        'clients/slack_client_real.py',
        'clients/slack_client.py'
    ]
    
    results = {"files_checked": [], "correct_ids": 0, "total_files": len(files_to_check)}
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            results["files_checked"].append(file_path)
            
            if 'TECHZIP_PDF_BOT_ID = "A097K6HTULW"' in content:
                results["correct_ids"] += 1
                logger.info(f"✅ {file_path}: TechZip Bot ID is correct (A097K6HTULW)")
            else:
                logger.error(f"❌ {file_path}: TechZip Bot ID is incorrect or missing")
                
        except FileNotFoundError:
            logger.warning(f"⚠️  {file_path}: File not found")
    
    return results

def test_github_service_import():
    """Test 3: Verify GitHub service uses Real implementation"""
    logger.info("🔍 Test 3: Checking GitHub service implementation...")
    
    try:
        with open('clients/service_adapter.py', 'r') as f:
            content = f.read()
        
        # Check if RealGitHubService is imported and assigned (PJINIT v1.2 actual patterns)
        has_real_import = "from app.services.github import GitHubService as RealGitHubService" in content
        has_real_assignment = "GitHubService = RealGitHubService" in content
        has_instantiation = "self.github_client = GitHubService()" in content
        
        if has_real_import and has_real_assignment and has_instantiation:
            logger.info("✅ service_adapter.py: Using RealGitHubService (PJINIT v1.2 pattern)")
            return {"status": "real", "mock_removed": True}
        else:
            logger.error("❌ service_adapter.py: Still using MockGitHubService")
            if not has_real_import:
                logger.error("  Missing: Real GitHub import")
            if not has_real_assignment:
                logger.error("  Missing: GitHubService = RealGitHubService assignment")
            if not has_instantiation:
                logger.error("  Missing: GitHubService() instantiation")
            return {"status": "mock", "mock_removed": False}
            
    except FileNotFoundError:
        logger.error("❌ service_adapter.py: File not found")
        return {"status": "error", "mock_removed": False}

async def test_slack_client_invitation_method():
    """Test 4: Verify RealSlackClient has PJINIT v1.2 invitation method"""
    logger.info("🔍 Test 4: Checking Slack client invitation implementation...")
    
    try:
        # Import the real Slack client
        sys.path.append('clients')
        from slack_client_real import RealSlackClient
        
        # Check if the method exists
        has_invitation_method = hasattr(RealSlackClient, 'invite_techzip_bot_with_invitation_bot')
        
        if has_invitation_method:
            logger.info("✅ RealSlackClient: invite_techzip_bot_with_invitation_bot method exists")
            
            # Test method signature and docstring
            method = getattr(RealSlackClient, 'invite_techzip_bot_with_invitation_bot')
            docstring = method.__doc__ or ""
            
            pjinit_mentioned = "PJINIT v1.2" in docstring
            invitation_bot_mentioned = "招待Bot" in docstring
            
            if pjinit_mentioned and invitation_bot_mentioned:
                logger.info("✅ Method documentation mentions PJINIT v1.2 and 招待Bot")
                return {"method_exists": True, "documentation_correct": True}
            else:
                logger.warning("⚠️ Method exists but documentation may be incomplete")
                return {"method_exists": True, "documentation_correct": False}
        else:
            logger.error("❌ RealSlackClient: invite_techzip_bot_with_invitation_bot method missing")
            return {"method_exists": False, "documentation_correct": False}
            
    except ImportError as e:
        logger.error(f"❌ Cannot import RealSlackClient: {e}")
        return {"method_exists": False, "documentation_correct": False}

def test_github_service_functionality():
    """Test 5: Test GitHub service personal token functionality"""
    logger.info("🔍 Test 5: Testing GitHub service with personal token...")
    
    try:
        # Add TechBridge app path for GitHub service import
        techbridge_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        if techbridge_app_path not in sys.path:
            sys.path.insert(0, techbridge_app_path)
        
        # Import GitHub service from TechBridge app
        from app.services.github import GitHubService
        
        # Initialize service (this will test authentication)
        try:
            github_service = GitHubService()
            logger.info("✅ GitHub service initialized successfully")
            
            # Test connection
            connection_test = github_service.test_connection()
            if connection_test:
                logger.info("✅ GitHub service connection test passed")
                return {"init_success": True, "connection_test": True}
            else:
                logger.warning("⚠️ GitHub service connection test failed (token may be invalid)")
                return {"init_success": True, "connection_test": False}
                
        except Exception as e:
            logger.error(f"❌ GitHub service initialization failed: {e}")
            return {"init_success": False, "connection_test": False}
            
    except ImportError as e:
        logger.warning(f"⚠️ Cannot import GitHubService from TechBridge app: {e}")
        logger.info("This may be expected in test environment - checking if service_adapter.py has correct imports")
        return {"init_success": False, "connection_test": False}

def main():
    """Run all PJINIT v1.2 fix verification tests"""
    print("🚀 PJINIT v1.2 Fix Verification Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests_results = {}
    
    # Test 1: Environment configuration
    tests_results["env_config"] = test_env_configuration()
    
    # Test 2: TechZip Bot IDs
    tests_results["bot_ids"] = test_techzip_bot_ids()
    
    # Test 3: GitHub service implementation
    tests_results["github_service"] = test_github_service_import()
    
    # Test 4: Slack client invitation method (async)
    tests_results["slack_invitation"] = asyncio.run(test_slack_client_invitation_method())
    
    # Test 5: GitHub service functionality
    tests_results["github_functionality"] = test_github_service_functionality()
    
    # Summary
    print()
    print("📊 PJINIT v1.2 Fix Verification Summary")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Env config summary
    env_results = tests_results["env_config"]
    env_passed = sum([
        env_results["github_org_disabled"],
        env_results["invitation_bot_token_format"],
        env_results["github_token_present"]
    ])
    total_tests += 3
    passed_tests += env_passed
    print(f"Environment Configuration: {env_passed}/3 ✅")
    
    # Bot IDs summary
    bot_results = tests_results["bot_ids"]
    total_tests += bot_results["total_files"]
    passed_tests += bot_results["correct_ids"]
    print(f"TechZip Bot ID Consistency: {bot_results['correct_ids']}/{bot_results['total_files']} ✅")
    
    # GitHub service summary
    github_results = tests_results["github_service"]
    github_passed = 1 if github_results["mock_removed"] else 0
    total_tests += 1
    passed_tests += github_passed
    print(f"GitHub Service Implementation: {github_passed}/1 ✅")
    
    # Slack invitation summary
    slack_results = tests_results["slack_invitation"]
    slack_passed = sum([
        slack_results["method_exists"],
        slack_results["documentation_correct"]
    ])
    total_tests += 2
    passed_tests += slack_passed
    print(f"Slack Invitation Method: {slack_passed}/2 ✅")
    
    # GitHub functionality summary
    github_func_results = tests_results["github_functionality"]
    github_func_passed = sum([
        github_func_results["init_success"],
        github_func_results["connection_test"]
    ])
    total_tests += 2
    passed_tests += github_func_passed
    print(f"GitHub Service Functionality: {github_func_passed}/2 ✅")
    
    print(f"\nOverall Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All PJINIT v1.2 fixes verified successfully!")
        print("✅ Ready for production use")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} issues remaining")
        print("❌ Additional fixes may be required")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)