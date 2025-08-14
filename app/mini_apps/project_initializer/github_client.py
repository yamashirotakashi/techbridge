"""
GitHub Client - Legacy Compatibility Layer
TechBridge ServiceAdapterパターンへのブリッジ
"""

from clients.service_adapter import GitHubClient as GitHubClientAdapter

# Legacy compatibility  
GitHubClient = GitHubClientAdapter