"""Security utilities."""

import hashlib
import hmac
import time
from typing import Dict


def verify_webhook_signature(
    body: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        body: Request body bytes
        signature: Signature from webhook header
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def verify_slack_request(
    body: bytes,
    headers: Dict[str, str],
    signing_secret: str,
) -> bool:
    """
    Verify Slack request signature.
    
    Args:
        body: Request body bytes
        headers: Request headers
        signing_secret: Slack signing secret
        
    Returns:
        True if request is valid
    """
    # Get timestamp and signature from headers
    timestamp = headers.get("x-slack-request-timestamp", "")
    signature = headers.get("x-slack-signature", "")
    
    if not timestamp or not signature:
        return False
    
    # Check timestamp is recent (within 5 minutes)
    try:
        request_timestamp = int(timestamp)
        current_timestamp = int(time.time())
        
        if abs(current_timestamp - request_timestamp) > 300:
            return False
    except ValueError:
        return False
    
    # Create signature base string
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    
    # Calculate expected signature
    expected_signature = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)