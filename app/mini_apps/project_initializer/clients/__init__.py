"""
PJINIT Service Clients
Phase 1リファクタリング: サービス連携層
"""

from .service_adapter import (
    ServiceAdapter, 
    create_service_adapter,
    GoogleSheetsClient,
    SlackClient,
    GitHubClient
)

__all__ = [
    'ServiceAdapter',
    'create_service_adapter', 
    'GoogleSheetsClient',
    'SlackClient',
    'GitHubClient'
]