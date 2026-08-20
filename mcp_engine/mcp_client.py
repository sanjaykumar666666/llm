"""
Model Context Protocol (MCP) Client Manager.
File: mcp_engine/mcp_client.py
"""

from typing import Dict, Any, List, Optional
import logging
from mcp_engine.mcp_server import (
    BaseMCPServer,
    SystemMetricsMCPServer,
    PrivacyAuditMCPServer,
    KnowledgeBaseMCPServer,
    MCPResource
)
from mcp_engine.web_search_server import WebSearchMCPServer
from mcp_engine.privacy_mcp_wrapper import PrivacyMCPWrapper

logger = logging.getLogger("MCPClientManager")


class MCPClientManager:
    """
    Manages active MCP servers, tools discovery, resource fetching, and guarded tool execution.
    """

    def __init__(self, enable_default_servers: bool = True):
        self.servers: Dict[str, BaseMCPServer] = {}
        self.privacy_wrapper = PrivacyMCPWrapper()

        if enable_default_servers:
            self._register_default_servers()

    def _register_default_servers(self) -> None:
        self.register_server(SystemMetricsMCPServer())
        self.register_server(PrivacyAuditMCPServer())
        self.register_server(KnowledgeBaseMCPServer())
        self.register_server(WebSearchMCPServer())

    def register_server(self, server: BaseMCPServer) -> None:
        self.servers[server.server_id] = server
        logger.info(f"Registered MCP Server '{server.name}' (ID: {server.server_id})")

    def list_servers(self) -> List[Dict[str, Any]]:
        return [
            {
                "server_id": s.server_id,
                "name": s.name,
                "description": s.description,
                "tool_count": len(s.tools),
                "resource_count": len(s.resources)
            }
            for s in self.servers.values()
        ]

    def list_all_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.list_tools())
        return all_tools

    def list_all_resources(self) -> List[Dict[str, Any]]:
        all_resources = []
        for server in self.servers.values():
            all_resources.extend(server.list_resources())
        return all_resources

    def read_resource(self, uri: str) -> Dict[str, Any]:
        for server in self.servers.values():
            res = server.read_resource(uri)
            if res:
                return {
                    "success": True,
                    "uri": res.uri,
                    "name": res.name,
                    "description": res.description,
                    "mime_type": res.mime_type,
                    "content": res.content
                }
        return {"success": False, "error": f"Resource with URI '{uri}' not found."}

    def execute_tool_guarded(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an MCP tool with Privacy Firewall safety evaluation.
        """
        # 1. Evaluate tool input safety via Privacy Wrapper
        safety_check = self.privacy_wrapper.evaluate_tool_call_safety(tool_name, arguments)
        if not safety_check["safe"]:
            return {
                "success": False,
                "blocked": True,
                "tool_name": tool_name,
                "reason": safety_check["reason"],
                "risk_score": safety_check["risk_score"],
                "detected_entities": safety_check["detected_entities"]
            }

        # 2. Locate target MCP Server
        target_server = None
        if server_id and server_id in self.servers:
            target_server = self.servers[server_id]
        else:
            for s in self.servers.values():
                if tool_name in s.tools:
                    target_server = s
                    break

        if not target_server:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found on any active MCP server."
            }

        # 3. Execute tool on target MCP server
        exec_res = target_server.call_tool(tool_name, arguments)

        if exec_res.get("success"):
            # 4. Sanitize tool output if needed
            sanitized_result = self.privacy_wrapper.sanitize_tool_output(exec_res["result"])
            exec_res["result"] = sanitized_result
            exec_res["privacy_firewall_status"] = "PASSED"

        return exec_res
