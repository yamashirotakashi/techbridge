"""
Google Sheets Client - Legacy Compatibility Layer
TechBridge ServiceAdapterパターンへのブリッジ
"""

from clients.service_adapter import GoogleSheetsClient as GoogleSheetsClientAdapter

# Legacy compatibility
GoogleSheetsClient = GoogleSheetsClientAdapter