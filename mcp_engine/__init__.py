"""
Model Context Protocol (MCP) Integration Engine Package.
File: mcp_engine/__init__.py
"""

from mcp_engine.mcp_server import BaseMCPServer, SystemMetricsMCPServer, PrivacyAuditMCPServer, KnowledgeBaseMCPServer
from mcp_engine.web_search_server import WebSearchMCPServer
from mcp_engine.web_search_router import WebSearchRouter
from mcp_engine.mcp_client import MCPClientManager
from mcp_engine.privacy_mcp_wrapper import PrivacyMCPWrapper

__all__ = [
    "BaseMCPServer",
    "SystemMetricsMCPServer",
    "PrivacyAuditMCPServer",
    "KnowledgeBaseMCPServer",
    "WebSearchMCPServer",
    "WebSearchRouter",
    "MCPClientManager",
    "PrivacyMCPWrapper"
]
