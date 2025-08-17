"""
Project Initializer - Message Configuration
===========================================

This module centralizes all user-facing messages for the Project Initializer system.
Messages are organized into categories for better maintainability and consistency.

Created for: PJINIT v2.0 Phase 2B Step 3 - Message centralization
Author: Project Initializer Development Team
Date: 2025-08-16

Categories:
- Error messages: System errors, validation failures, operation failures
- Success messages: Successful operations, confirmations
- Warning messages: Non-critical issues, cautionary notices
- Information messages: Status updates, guidance, instructions

Usage:
    from config.messages import ERROR_MESSAGES, SUCCESS_MESSAGES
    print(ERROR_MESSAGES['INVALID_PATH'])
"""

# Error Messages
ERROR_MESSAGES = {
    'SAVE_SETTINGS_FAILED': "設定の保存に失敗しました:\n{error}",
    'NO_N_CODE': "Nコードを入力してください",
    'GOOGLE_SHEETS_UNAVAILABLE': "Google Sheets連携が利用できません",
    'N_CODE_EMPTY': "Nコードが入力されていません"
}

# Success Messages
SUCCESS_MESSAGES = {
    'PROJECT_INITIALIZATION_COMPLETE': "=== プロジェクト初期化完了 ===\n\n",
    'INFORMATION_CONFIRMED': "情報確認完了",
    'INITIALIZATION_COMPLETE': "初期化完了"
}

# Warning Messages
WARNING_MESSAGES = {
    'ERROR_GENERIC': "エラー"
}

# Information Messages
INFO_MESSAGES = {
    'GITHUB_INVITATION_REQUIRED': "- 【重要】GitHub {github_username} をリポジトリに招待してください\n",
    'SLACK_CHANNEL_INVITATION_REQUIRED': "- 【重要】{email} (ID: {user_id}) をSlackチャンネルに招待してください\n",
    'SLACK_WORKSPACE_INVITATION_REQUIRED': "- 【重要】{email} をSlackワークスペースに招待してください（新規ユーザー）\n",
    'GITHUB_APP_SETUP_REQUIRED': "- 【重要】GitHub App設定:\n"
}