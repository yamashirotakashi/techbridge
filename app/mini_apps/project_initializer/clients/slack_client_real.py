"""
Real Slack Client Implementation with Proper API Calls and Error Handling
Fixes the hanging issue by using actual slack-sdk with timeout and validation
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
import time
import logging

# Import Slack SDK
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    print("[ERROR] slack_sdk not available. Install with: pip install slack-sdk")

class RealSlackClient:
    """Real Slack Client with proper API integration and error handling"""
    
    # TechZip PDF Bot ID (App ID as specified by user - ULTRATHINK corrected)
    TECHZIP_PDF_BOT_ID = "A097K6HTULW"
    
    # Invitation Bot ID for inviting TechZip Bot (provided by user)
    INVITATION_BOT_ID = "A097NKP77EE"
    
    # GitHub App ID for channel invitations
    GITHUB_APP_ID = "UA8BZ8ENT"  # GitHub App user ID (github)
    
    def __init__(self, bot_token: str = None, user_token: str = None):
        """
        Initialize with proper Slack tokens
        
        Args:
            bot_token: Slack Bot Token (xoxb-...)
            user_token: Slack User Token (xoxp-...)
        """
        if not SLACK_SDK_AVAILABLE:
            raise Exception("slack_sdk is not installed. Please install it with: pip install slack-sdk")
            
        self.bot_token = bot_token
        self.user_token = user_token
        
        # Initialize clients
        self.bot_client = None
        self.user_client = None
        
        if bot_token:
            self.bot_client = WebClient(token=bot_token)
            print(f"[INFO] Bot client initialized with token ending in ...{bot_token[-8:]}")
        
        if user_token:
            self.user_client = WebClient(token=user_token)
            print(f"[INFO] User client initialized with token ending in ...{user_token[-8:]}")
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def validate_tokens(self) -> Dict[str, bool]:
        """
        Validate both bot and user tokens before use
        Returns dict with validation results
        """
        results = {
            "bot_token_valid": False,
            "user_token_valid": False
        }
        
        # Validate bot token
        if self.bot_client:
            try:
                self.logger.info("Validating bot token...")
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.bot_client.auth_test
                    ),
                    timeout=10.0  # 10 second timeout
                )
                
                if response.get("ok"):
                    results["bot_token_valid"] = True
                    self.logger.info(f"Bot token valid - User: {response.get('user')}, Team: {response.get('team')}")
                else:
                    self.logger.error(f"Bot token invalid: {response.get('error', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                self.logger.error("Bot token validation timed out after 10 seconds")
            except SlackApiError as e:
                self.logger.error(f"Bot token validation failed: {e.response['error']}")
            except Exception as e:
                self.logger.error(f"Bot token validation error: {e}")
        
        # Validate user token
        if self.user_client:
            try:
                self.logger.info("Validating user token...")
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.user_client.auth_test
                    ),
                    timeout=10.0  # 10 second timeout
                )
                
                if response.get("ok"):
                    results["user_token_valid"] = True
                    self.logger.info(f"User token valid - User: {response.get('user')}, Team: {response.get('team')}")
                else:
                    self.logger.error(f"User token invalid: {response.get('error', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                self.logger.error("User token validation timed out after 10 seconds")
            except SlackApiError as e:
                self.logger.error(f"User token validation failed: {e.response['error']}")
            except Exception as e:
                self.logger.error(f"User token validation error: {e}")
        
        return results
    
    async def create_channel(self, channel_name: str, topic: str = None, use_user_token: bool = True) -> Optional[str]:
        """
        Create a private Slack channel with proper error handling and timeout
        
        Args:
            channel_name: Name of the channel to create
            topic: Optional topic/purpose for the channel  
            use_user_token: Whether to use user token (required for private channels)
        
        Returns:
            Channel ID if successful, None if failed
        """
        
        if not self.bot_client and not self.user_client:
            self.logger.error("No Slack clients available")
            return None
        
        # Choose the appropriate client
        client = self.user_client if use_user_token and self.user_client else self.bot_client
        client_type = "user" if use_user_token and self.user_client else "bot"
        
        if not client:
            self.logger.error(f"No {client_type} client available for channel creation")
            return None
        
        try:
            self.logger.info(f"Creating private channel '{channel_name}' using {client_type} token...")
            
            # Validate tokens first
            validation_results = await self.validate_tokens()
            if use_user_token and not validation_results.get("user_token_valid"):
                self.logger.error("User token validation failed - cannot create private channel")
                return None
            elif not use_user_token and not validation_results.get("bot_token_valid"):
                self.logger.error("Bot token validation failed - cannot create channel")
                return None
            
            # Clean channel name (remove invalid characters)
            clean_name = self._clean_channel_name(channel_name)
            self.logger.info(f"Cleaned channel name: '{clean_name}'")
            
            # Create private channel with timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.conversations_create(
                        name=clean_name,
                        is_private=True  # Always create private channels
                    )
                ),
                timeout=30.0  # 30 second timeout
            )
            
            if response.get("ok"):
                channel_info = response.get("channel", {})
                channel_id = channel_info.get("id")
                
                self.logger.info(f"Channel created successfully - ID: {channel_id}")
                
                # Set topic if provided
                if topic and channel_id:
                    await self._set_channel_topic(channel_id, topic, client)
                
                return channel_id
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"Channel creation failed: {error_msg}")
                
                # Handle specific errors
                if error_msg == "invalid_name":
                    self.logger.error("Invalid channel name format")
                elif error_msg == "invalid_auth":
                    self.logger.error("Authentication failed - check token permissions")
                
                return None
                
        except asyncio.TimeoutError:
            self.logger.error(f"Channel creation timed out after 30 seconds")
            return None
        except SlackApiError as e:
            # Handle SlackApiError with specific name_taken logic
            error_msg = e.response.get('error', 'Unknown error')
            self.logger.error(f"Slack API error during channel creation: {error_msg}")
            
            if error_msg == "name_taken":
                self.logger.warning("Channel name already exists - attempting to find existing channel")
                existing_channel = await self._find_existing_channel(clean_name)
                if existing_channel:
                    self.logger.info(f"Found existing channel for reuse: {existing_channel}")
                    return existing_channel
                else:
                    # If we can't find the existing channel (due to permission issues),
                    # assume it exists and try to create a unique variant
                    self.logger.warning("Cannot find existing channel (possibly due to missing groups:read scope)")
                    self.logger.info("Attempting to create channel with timestamp suffix to avoid collision")
                    
                    import time
                    timestamp_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
                    
                    # Ensure unique name doesn't exceed 21 character limit
                    max_base_length = 21 - 1 - len(timestamp_suffix)  # 21 - hyphen - timestamp
                    base_name = clean_name[:max_base_length] if len(clean_name) > max_base_length else clean_name
                    unique_name = f"{base_name}-{timestamp_suffix}"
                    
                    self.logger.info(f"Generated unique channel name: '{clean_name}' -> '{unique_name}' (length: {len(unique_name)})")
                    
                    try:
                        # Try creating with unique suffix
                        response_retry = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: client.conversations_create(
                                    name=unique_name,
                                    is_private=True
                                )
                            ),
                            timeout=30.0
                        )
                        
                        if response_retry.get("ok"):
                            channel_info = response_retry.get("channel", {})
                            channel_id = channel_info.get("id")
                            self.logger.info(f"Created channel with unique name: {unique_name} -> {channel_id}")
                            
                            # Set topic if provided
                            if topic and channel_id:
                                await self._set_channel_topic(channel_id, topic, client)
                            
                            return channel_id
                        else:
                            self.logger.error(f"Failed to create unique channel: {response_retry.get('error')}")
                            
                    except Exception as e:
                        self.logger.error(f"Error creating unique channel: {e}")
                        
                    # Last resort: return None but log the issue clearly
                    self.logger.error("Unable to create or find channel due to permission/conflict issues")
            
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during channel creation: {e}")
            return None
    
    async def invite_user_to_channel(self, channel_id: str, user_id: str, use_user_token: bool = True) -> bool:
        """
        Invite a user to a channel with proper error handling
        
        Args:
            channel_id: ID of the channel
            user_id: ID of the user to invite
            use_user_token: Whether to use user token (required for private channels)
        
        Returns:
            True if successful, False if failed
        """
        
        # Choose the appropriate client
        client = self.user_client if use_user_token and self.user_client else self.bot_client
        client_type = "user" if use_user_token and self.user_client else "bot"
        
        if not client:
            self.logger.error(f"No {client_type} client available for user invitation")
            return False
        
        try:
            self.logger.info(f"Inviting user {user_id} to channel {channel_id} using {client_type} token...")
            
            # Invite user with timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.conversations_invite(
                        channel=channel_id,
                        users=user_id
                    )
                ),
                timeout=15.0  # 15 second timeout
            )
            
            if response.get("ok"):
                self.logger.info(f"User {user_id} invited successfully to channel {channel_id}")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"User invitation failed: {error_msg}")
                
                # Handle specific errors
                if error_msg == "user_not_found":
                    self.logger.error("User ID not found in workspace")
                elif error_msg == "already_in_channel":
                    self.logger.warning("User is already in the channel")
                    return True  # Consider this a success
                elif error_msg == "cant_invite_self":
                    self.logger.warning("Cannot invite self to channel")
                elif error_msg == "channel_not_found":
                    self.logger.error("Channel not found")
                
                return False
                
        except asyncio.TimeoutError:
            self.logger.error(f"User invitation timed out after 15 seconds")
            return False
        except SlackApiError as e:
            self.logger.error(f"Slack API error during user invitation: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during user invitation: {e}")
            return False
    
    async def _set_channel_topic(self, channel_id: str, topic: str, client: WebClient) -> bool:
        """Set channel topic/purpose"""
        try:
            self.logger.info(f"Setting topic for channel {channel_id}: {topic}")
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.conversations_setTopic(
                        channel=channel_id,
                        topic=topic
                    )
                ),
                timeout=10.0
            )
            
            if response.get("ok"):
                self.logger.info("Channel topic set successfully")
                return True
            else:
                self.logger.error(f"Failed to set channel topic: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting channel topic: {e}")
            return False
    
    async def _find_existing_channel(self, channel_name: str) -> Optional[str]:
        """Find existing channel by name"""
        if not self.user_client:
            return None
            
        try:
            self.logger.info(f"Searching for existing channel: {channel_name}")
            
            # Get list of private channels
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.user_client.conversations_list(
                        types="private_channel",
                        limit=1000
                    )
                ),
                timeout=15.0
            )
            
            if response.get("ok"):
                channels = response.get("channels", [])
                for channel in channels:
                    if channel.get("name") == channel_name:
                        channel_id = channel.get("id")
                        self.logger.info(f"Found existing channel: {channel_name} -> {channel_id}")
                        return channel_id
            
            self.logger.warning(f"Existing channel not found: {channel_name}")
            return None
            
        except Exception as e:
            error_msg = str(e)
            if "missing_scope" in error_msg and "groups:read" in error_msg:
                self.logger.warning("Cannot search for existing channels: User token missing 'groups:read' scope")
                self.logger.info("This is expected if the Slack app doesn't have permission to list private channels")
            else:
                self.logger.error(f"Error searching for existing channel: {e}")
            return None
    
    async def find_user_by_email(self, email: str) -> Optional[str]:
        """
        Find Slack user by email address
        
        Args:
            email: User's email address
        
        Returns:
            User ID if found, None if not found
        """
        if not self.bot_client and not self.user_client:
            self.logger.error("No Slack clients available for user lookup")
            return None
        
        # Try both clients - user client first for better permissions
        for client_name, client in [("user", self.user_client), ("bot", self.bot_client)]:
            if not client:
                continue
                
            try:
                self.logger.info(f"Looking up user by email: {email} using {client_name} token")
                
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: client.users_lookupByEmail(email=email)
                    ),
                    timeout=15.0  # 15 second timeout
                )
                
                if response.get("ok"):
                    user_info = response.get("user", {})
                    user_id = user_info.get("id")
                    user_name = user_info.get("name")
                    
                    if user_id:
                        self.logger.info(f"Found user: {email} -> {user_name} ({user_id})")
                        return user_id
                else:
                    error_msg = response.get("error", "Unknown error")
                    self.logger.warning(f"User lookup failed with {client_name} client: {error_msg}")
                    
                    if error_msg in ["users_not_found", "user_not_found"]:
                        self.logger.info(f"User not found in workspace: {email}")
                        return None
                    
            except asyncio.TimeoutError:
                self.logger.error(f"User lookup timed out after 15 seconds with {client_name} client")
            except SlackApiError as e:
                error_msg = e.response.get('error', 'Unknown error')
                self.logger.warning(f"Slack API error during user lookup with {client_name} client: {error_msg}")
                
                if error_msg in ["users_not_found", "user_not_found"]:
                    self.logger.info(f"User not found in workspace: {email}")
                    return None
                elif error_msg == "invalid_email":
                    self.logger.error(f"Invalid email format: {email}")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Unexpected error during user lookup with {client_name} client: {e}")
        
        self.logger.warning(f"Could not find user with email: {email}")
        return None

    async def find_workflow_channel(self) -> Optional[str]:
        """
        Find the workflow management channel (usually #techzip-workflow or similar)
        
        Returns:
            Channel ID if found, None if not found
        """
        if not self.user_client:
            self.logger.error("User client not available for channel search")
            return None
            
        try:
            self.logger.info("Searching for workflow management channel...")
            
            # Search for workflow-related channels
            workflow_channel_patterns = [
                "techzip-workflow",
                "workflow",
                "project-management", 
                "admin",
                "general"  # Fallback to general
            ]
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.user_client.conversations_list(
                        types="public_channel,private_channel",
                        limit=1000
                    )
                ),
                timeout=20.0
            )
            
            if response.get("ok"):
                channels = response.get("channels", [])
                
                # Try to find workflow channel by pattern matching
                for pattern in workflow_channel_patterns:
                    for channel in channels:
                        channel_name = channel.get("name", "").lower()
                        if pattern in channel_name:
                            channel_id = channel.get("id")
                            self.logger.info(f"Found workflow channel: #{channel_name} -> {channel_id}")
                            return channel_id
                
                self.logger.warning("No workflow management channel found, workflow guidance will be skipped")
                return None
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"Failed to list channels: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            if "missing_scope" in error_msg:
                self.logger.warning("Cannot list channels: Missing required scopes for channel listing")
            else:
                self.logger.error(f"Error searching for workflow channel: {e}")
            return None

    async def post_workflow_guidance(self, channel_id: str, project_info: dict, manual_tasks: list, 
                                   execution_summary: dict, sheet_id: str) -> bool:
        """
        Post comprehensive workflow guidance to the workflow management channel
        
        Args:
            channel_id: Target channel ID
            project_info: Project information dictionary
            manual_tasks: List of manual tasks that need attention
            execution_summary: Summary of what was completed automatically
            sheet_id: Google Sheets ID for reference
            
        Returns:
            True if message posted successfully, False otherwise
        """
        if not self.bot_client and not self.user_client:
            self.logger.error("No Slack clients available for posting workflow guidance")
            return False
            
        # Prefer bot client for posting messages
        client = self.bot_client if self.bot_client else self.user_client
        client_type = "bot" if self.bot_client else "user"
        
        try:
            self.logger.info(f"Posting workflow guidance to channel {channel_id} using {client_type} token")
            
            # Build workflow guidance message
            n_code = project_info.get('n_code', 'Unknown')
            book_title = project_info.get('book_title', 'Unknown Title')
            author = project_info.get('author', 'Unknown Author')
            slack_channel = project_info.get('slack_channel', 'N/A')
            
            # Create formatted message
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 新規プロジェクト初期化完了: {n_code}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*書籍タイトル:* {book_title}\n*著者:* {author}\n*Slackチャンネル:* #{slack_channel}"
                    }
                },
                {
                    "type": "divider"
                }
            ]
            
            # Add execution summary
            if execution_summary:
                summary_text = []
                if execution_summary.get('slack_channel_created'):
                    summary_text.append("✅ Slackチャンネル作成")
                if execution_summary.get('github_repo_created'):
                    summary_text.append("✅ GitHubリポジトリ作成")
                if execution_summary.get('google_sheets_updated'):
                    summary_text.append("✅ Google Sheets更新")
                
                if summary_text:
                    message_blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*自動処理完了項目:*\n{chr(10).join(summary_text)}"
                        }
                    })
            
            # Add manual tasks if any
            if manual_tasks:
                task_text = "\n".join([f"• {task}" for task in manual_tasks])
                message_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*手動対応が必要な項目:*\n{task_text}"
                    }
                })
            
            # Add reference link
            if sheet_id:
                message_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*参考リンク:*\n<https://docs.google.com/spreadsheets/d/{sheet_id}|発行計画シート>"
                    }
                })
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat_postMessage(
                        channel=channel_id,
                        blocks=message_blocks,
                        text=f"新規プロジェクト初期化完了: {n_code} - {book_title}"
                    )
                ),
                timeout=15.0
            )
            
            if response.get("ok"):
                message_ts = response.get("ts")
                self.logger.info(f"Workflow guidance posted successfully: {message_ts}")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"Failed to post workflow guidance: {error_msg}")
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("Workflow guidance posting timed out after 15 seconds")
            return False
        except SlackApiError as e:
            self.logger.error(f"Slack API error during workflow guidance posting: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during workflow guidance posting: {e}")
            return False

    async def invite_github_app_with_bot_token(self, channel_id: str, github_app_id: str) -> bool:
        """
        Invite GitHub App to channel using primary bot token
        
        Args:
            channel_id: Target channel ID
            github_app_id: GitHub App user ID (usually starts with U)
            
        Returns:
            True if invitation successful, False otherwise
        """
        if not self.bot_client:
            self.logger.error("Bot client not available for GitHub App invitation")
            return False
            
        try:
            self.logger.info(f"Inviting GitHub App {github_app_id} to channel {channel_id} using bot token")
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.bot_client.conversations_invite(
                        channel=channel_id,
                        users=github_app_id
                    )
                ),
                timeout=15.0
            )
            
            if response.get("ok"):
                self.logger.info(f"GitHub App invited successfully to channel {channel_id}")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.warning(f"GitHub App invitation failed with bot token: {error_msg}")
                
                if error_msg == "already_in_channel":
                    self.logger.info("GitHub App is already in the channel")
                    return True
                    
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("GitHub App invitation timed out after 15 seconds")
            return False
        except SlackApiError as e:
            error_msg = e.response.get('error', 'Unknown error')
            self.logger.warning(f"Slack API error during GitHub App invitation with bot token: {error_msg}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during GitHub App invitation with bot token: {e}")
            return False

    async def invite_github_app_with_alternative_bot(self, channel_id: str, github_app_id: str) -> bool:
        """
        Invite GitHub App to channel using alternative invitation bot token
        
        Args:
            channel_id: Target channel ID  
            github_app_id: GitHub App user ID (usually starts with U)
            
        Returns:
            True if invitation successful, False otherwise
        """
        # Create a separate client with invitation bot token if available
        invitation_token = os.getenv('SLACK_INVITATION_BOT_TOKEN')
        if not invitation_token:
            self.logger.warning("No invitation bot token available for alternative GitHub App invitation")
            return False
            
        try:
            # Create temporary client for invitation
            invitation_client = WebClient(token=invitation_token)
            
            self.logger.info(f"Inviting GitHub App {github_app_id} to channel {channel_id} using invitation bot token")
            
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: invitation_client.conversations_invite(
                        channel=channel_id,
                        users=github_app_id
                    )
                ),
                timeout=15.0
            )
            
            if response.get("ok"):
                self.logger.info(f"GitHub App invited successfully using alternative bot token")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"GitHub App invitation failed with alternative bot token: {error_msg}")
                
                if error_msg == "already_in_channel":
                    self.logger.info("GitHub App is already in the channel")
                    return True
                    
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("GitHub App invitation with alternative token timed out after 15 seconds")
            return False
        except SlackApiError as e:
            error_msg = e.response.get('error', 'Unknown error')
            self.logger.error(f"Slack API error during GitHub App invitation with alternative token: {error_msg}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during GitHub App invitation with alternative token: {e}")
            return False

    async def invite_techzip_bot_with_invitation_bot(self, channel_id: str) -> bool:
        """
        PJINIT v1.2 Exact Implementation: Invite TechZip PDF Bot using 招待Bot
        
        招待Bot (A097NKP77EE) User Token Scopes:
        - admin.usergroups:read, channels:read, channels:write
        - groups:read, groups:write, users:read
        - 招待のためのパーミッションが与えられている
        
        Method: Use invitation bot User Token to invite TechZip Bot (A097K6HTULW)
        
        Args:
            channel_id: Target channel ID
            
        Returns:
            True if invitation successful, False otherwise
        """
        # Get invitation bot User Token (xoxp prefix)
        invitation_token = os.getenv('SLACK_INVITATION_BOT_TOKEN')
        if not invitation_token:
            self.logger.error("No SLACK_INVITATION_BOT_TOKEN available for TechZip Bot invitation")
            return False
            
        # Validate token format
        if not invitation_token.startswith('xoxp-'):
            self.logger.error(f"Invalid invitation bot token format - should be User Token (xoxp-), got: {invitation_token[:10]}...")
            return False
            
        try:
            # Create temporary client with invitation bot User Token
            invitation_client = WebClient(token=invitation_token)
            
            self.logger.info(f"PJINIT v1.2 Method: Inviting TechZip Bot {self.TECHZIP_PDF_BOT_ID} using 招待Bot (A097NKP77EE) User Token")
            
            # Direct invitation using conversations_invite with invitation bot authority
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: invitation_client.conversations_invite(
                        channel=channel_id,
                        users=self.TECHZIP_PDF_BOT_ID  # A097K6HTULW
                    )
                ),
                timeout=15.0
            )
            
            if response.get("ok"):
                self.logger.info(f"✅ TechZip Bot {self.TECHZIP_PDF_BOT_ID} invited successfully using 招待Bot (A097NKP77EE)")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                self.logger.error(f"TechZip Bot invitation failed: {error_msg}")
                
                if error_msg == "already_in_channel":
                    self.logger.info("TechZip Bot is already in the channel")
                    return True
                elif error_msg == "user_not_found":
                    self.logger.error("TechZip Bot ID A097K6HTULW not found in workspace")
                elif error_msg == "cant_invite":
                    self.logger.error("Cannot invite TechZip Bot - permission denied")
                    
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("TechZip Bot invitation timed out after 15 seconds")
            return False
        except SlackApiError as e:
            error_msg = e.response.get('error', 'Unknown error')
            self.logger.error(f"Slack API error during TechZip Bot invitation: {error_msg}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during TechZip Bot invitation: {e}")
            return False

    async def invite_user_by_email(self, channel_id: str, email: str, use_user_token: bool = True) -> bool:
        """
        Invite user by email address to channel (convenience wrapper)
        
        Args:
            channel_id: Target channel ID
            email: User's email address
            use_user_token: Whether to use user token for invitations
            
        Returns:
            True if invitation successful, False otherwise
        """
        try:
            self.logger.info(f"Inviting user by email {email} to channel {channel_id}")
            
            # First find the user by email
            user_id = await self.find_user_by_email(email)
            if not user_id:
                self.logger.error(f"Cannot find user with email: {email}")
                return False
            
            # Then invite the user to channel
            return await self.invite_user_to_channel(channel_id, user_id, use_user_token)
            
        except Exception as e:
            self.logger.error(f"Unexpected error during user invitation by email: {e}")
            return False

    def _clean_channel_name(self, name: str) -> str:
        """Clean channel name to meet Slack requirements"""
        import re
        
        # Convert to lowercase
        clean_name = name.lower()
        
        # Replace invalid characters with hyphens
        clean_name = re.sub(r'[^a-z0-9\-_]', '-', clean_name)
        
        # Remove multiple consecutive hyphens
        clean_name = re.sub(r'-+', '-', clean_name)
        
        # Remove leading/trailing hyphens
        clean_name = clean_name.strip('-')
        
        # Ensure name is not too long (Slack limit is 21 characters)
        if len(clean_name) > 21:
            clean_name = clean_name[:21]
            
        return clean_name

# Legacy compatibility - replace the mock implementation
SlackClient = RealSlackClient