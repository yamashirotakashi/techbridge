"""
Slack Client - Legacy Compatibility Layer
TechBridge ServiceAdapterパターンへのブリッジ
"""

from clients.service_adapter import SlackClient as SlackClientAdapter

# Legacy compatibility
SlackClient = SlackClientAdapter