"""
Configuration Constants Module

This module contains application-wide constants that were previously
hardcoded throughout the application. This separation improves
maintainability and follows the DRY principle.

Constants to be migrated here include:
- DEFAULT_PLANNING_SHEET_ID
- SUPPORTED_TOKEN_TYPES
- Other hardcoded configuration values

This file is part of PJINIT v2.0 Phase 2B Step 2 refactoring.
"""

# Default Google Sheets IDs
DEFAULT_PLANNING_SHEET_ID = "17DKsMGQ6krbhY7GIcX0iaeN-y8HcGGVkXt3d4oOckyQ"
DEFAULT_PURCHASE_SHEET_ID = "1JJ_C3z0txlJWiyEDl0c6OoVD5Ym_IoZJMMf5o76oV4c"

# Supported Token Types for environment variables
SUPPORTED_TOKEN_TYPES = [
    'SLACK_BOT_TOKEN',
    'SLACK_USER_TOKEN',
    'SLACK_INVITATION_BOT_TOKEN',
    'SLACK_SIGNING_SECRET',
    'GITHUB_TOKEN',
    'GITHUB_ORG_TOKEN',
    'GOOGLE_SERVICE_ACCOUNT_KEY',
    'PLANNING_SHEET_ID',
    'PURCHASE_SHEET_ID'
]

# Environment Variable Keys
ENV_KEYS = {
    'SLACK_BOT_TOKEN': 'SLACK_BOT_TOKEN',
    'SLACK_USER_TOKEN': 'SLACK_USER_TOKEN',
    'SLACK_INVITATION_BOT_TOKEN': 'SLACK_INVITATION_BOT_TOKEN',
    'SLACK_SIGNING_SECRET': 'SLACK_SIGNING_SECRET',
    'GITHUB_TOKEN': 'GITHUB_TOKEN',
    'GITHUB_ORG_TOKEN': 'GITHUB_ORG_TOKEN',
    'GOOGLE_SERVICE_ACCOUNT_KEY': 'GOOGLE_SERVICE_ACCOUNT_KEY',
    'PLANNING_SHEET_ID': 'PLANNING_SHEET_ID',
    'PURCHASE_SHEET_ID': 'PURCHASE_SHEET_ID'
}

# Task Types
TASK_TYPES = {
    'GITHUB_APP_INVITATION': 'github_app_invitation',
    'SLACK_CHANNEL_CREATE': 'create_slack_channel'
}

# Unicode Replacement for Windows CP932 compatibility
UNICODE_REPLACEMENTS = {
    "✅": "[OK]",
    "✗": "[ERROR]",
    "⚠️": "[WARN]",
    "🔧": "[CONFIG]",
    "📊": "[DATA]"
}

# Characterization Testing Function Names
CHARACTERIZATION_TEST_FUNCTIONS = [
    'setup_characterization_tests',
    'setup_gui_characterization_tests', 
    'setup_cli_characterization_tests',
    'run_characterization_tests',
    'setup_phase1_complete'
]

# Compliance Metrics
CONSTRAINTS_COMPLIANCE_RATE = "100%"