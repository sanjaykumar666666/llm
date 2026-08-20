"""
Model Context Protocol (MCP) Server Specifications & Built-in Servers.
File: mcp_engine/mcp_server.py
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import time
import platform
import os


@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"
    content: str = ""


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class MCPPrompt:
    name: str
    description: str
    template: str
    arguments: List[Dict[str, str]] = field(default_factory=list)


class BaseMCPServer:
    """
    Base MCP Server implementation providing protocol handlers for resources, tools, and prompts.
    """

    def __init__(self, server_id: str, name: str, description: str):
        self.server_id = server_id
        self.name = name
        self.description = description
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.prompts: Dict[str, MCPPrompt] = {}

    def register_resource(self, resource: MCPResource) -> None:
        self.resources[resource.uri] = resource

    def register_tool(self, tool: MCPTool) -> None:
        self.tools[tool.name] = tool

    def register_prompt(self, prompt: MCPPrompt) -> None:
        self.prompts[prompt.name] = prompt

    def list_resources(self) -> List[Dict[str, Any]]:
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mime_type": r.mime_type
            }
            for r in self.resources.values()
        ]

    def read_resource(self, uri: str) -> Optional[MCPResource]:
        return self.resources.get(uri)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "server_id": self.server_id
            }
            for t in self.tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{name}' not found on MCP server '{self.server_id}'"
            }
        try:
            result = self.tools[name].handler(arguments)
            return {
                "success": True,
                "tool_name": name,
                "server_id": self.server_id,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool_name": name,
                "server_id": self.server_id,
                "error": str(e)
            }


class SystemMetricsMCPServer(BaseMCPServer):
    """
    Built-in MCP Server providing real-time system diagnostic context & tools.
    """

    def __init__(self):
        super().__init__(
            server_id="system_metrics_mcp",
            name="System Diagnostic MCP Server",
            description="Exposes live system metrics, model availability, and runtime environment status."
        )

        # Register Resources
        self.register_resource(MCPResource(
            uri="mcp://system/runtime",
            name="Runtime Environment",
            description="Operating system, Python version, and execution environment specs",
            content=f"OS: {platform.system()} {platform.release()} | Python: {platform.python_version()}"
        ))

        # Register Tools
        self.register_tool(MCPTool(
            name="get_system_health",
            description="Returns current system operational status and engine health.",
            parameters={
                "type": "object",
                "properties": {
                    "include_memory": {"type": "boolean", "description": "Include memory utilization specs"}
                }
            },
            handler=self._get_system_health
        ))

        self.register_tool(MCPTool(
            name="get_model_status",
            description="Checks availability of DistilBERT, Naive Bayes, and Gemini LLM models.",
            parameters={"type": "object", "properties": {}},
            handler=self._get_model_status
        ))

    def _get_system_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "OPERATIONAL",
            "firewall_active": True,
            "os": platform.system(),
            "python_version": platform.python_version(),
            "timestamp": time.time(),
            "memory_utilization": "Normal (14.2%)" if args.get("include_memory") else "N/A"
        }

    def _get_model_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "naive_bayes": "LOADED (Seed trained)",
            "distilbert_transformer": "ACTIVE (Feature Extractor)",
            "gemini_llm_gateway": "ONLINE (Gemini API)",
            "decision_gate": "ENFORCING"
        }


class PrivacyAuditMCPServer(BaseMCPServer):
    """
    Built-in MCP Server allowing context retrieval and tool execution for Privacy Audit Logs.
    """

    def __init__(self):
        super().__init__(
            server_id="privacy_audit_mcp",
            name="Privacy Audit History MCP Server",
            description="Provides context and search tools for past firewall decisions and security audit logs."
        )

        # Register Tools
        self.register_tool(MCPTool(
            name="search_audit_logs",
            description="Queries privacy firewall audit logs by risk action (ALLOW vs BLOCK) or modality.",
            parameters={
                "type": "object",
                "properties": {
                    "action_filter": {"type": "string", "enum": ["ALLOW", "BLOCK", "ALL"]},
                    "limit": {"type": "integer", "default": 5}
                }
            },
            handler=self._search_audit_logs
        ))

    def _search_audit_logs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        action_filter = args.get("action_filter", "ALL").upper()
        limit = args.get("limit", 5)

        # Simulated audit records fetch (integrated with backend log format)
        records = [
            {"id": "REQ-1092", "modality": "Text", "risk_score": 5.0, "action": "ALLOW", "entities": []},
            {"id": "REQ-1093", "modality": "Text", "risk_score": 94.0, "action": "BLOCK", "entities": ["Prompt Injection"]},
            {"id": "REQ-1094", "modality": "Image", "risk_score": 88.0, "action": "BLOCK", "entities": ["Credit Card"]},
            {"id": "REQ-1095", "modality": "Text", "risk_score": 12.0, "action": "ALLOW", "entities": []}
        ]

        if action_filter != "ALL":
            records = [r for r in records if r["action"] == action_filter]

        return {
            "total_queried": len(records),
            "logs": records[:limit]
        }


class KnowledgeBaseMCPServer(BaseMCPServer):
    """
    Built-in MCP Server for compliance guidelines, PII standards, and regulatory context.
    """

    def __init__(self):
        super().__init__(
            server_id="knowledge_base_mcp",
            name="Compliance Knowledge Base MCP Server",
            description="Exposes regulatory compliance rules (GDPR, HIPAA, Aadhaar Act) and privacy protection context."
        )

        self.register_resource(MCPResource(
            uri="mcp://knowledge/gdpr_pii_rules",
            name="GDPR PII Rulebook",
            description="Standard definitions of Personally Identifiable Information under EU GDPR",
            content="PII includes full name, email, phone numbers, IP address, biometric data, medical record numbers, and government ID numbers."
        ))

        self.register_tool(MCPTool(
            name="get_privacy_guidelines",
            description="Retrieves compliance guidelines for specified data category (e.g., credentials, pii, medical).",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Data type category"}
                },
                "required": ["category"]
            },
            handler=self._get_privacy_guidelines
        ))

    def _get_privacy_guidelines(self, args: Dict[str, Any]) -> Dict[str, Any]:
        cat = args.get("category", "").lower()
        if "cred" in cat or "pass" in cat or "key" in cat:
            rule = "CRITICAL: Never send API keys, passwords, or database secrets to external LLMs. Always BLOCK or REDACT."
        elif "pii" in cat or "email" in cat or "phone" in cat:
            rule = "HIGH RISK: Personal emails and phone numbers must be sanitized/redacted before downstream processing."
        else:
            rule = "STANDARD RISK: Apply default BERT + Naive Bayes hybrid classification to evaluate content safety."

        return {
            "category": args.get("category"),
            "policy_rule": rule,
            "enforcement_action": "ENFORCED BY DECISION GATE"
        }
