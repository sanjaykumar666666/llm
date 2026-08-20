"""
FastAPI Router for Model Context Protocol (MCP) Integration.
File: backend/routes/mcp.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from mcp_engine.mcp_client import MCPClientManager

router = APIRouter()

# Global MCP Client Manager instance
mcp_manager = MCPClientManager(enable_default_servers=True)


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = {}
    server_id: Optional[str] = None


@router.get("/mcp/servers")
def get_mcp_servers():
    """
    Returns list of registered MCP Servers and their capabilities.
    """
    return {
        "success": True,
        "servers": mcp_manager.list_servers()
    }


@router.get("/mcp/tools")
def get_mcp_tools():
    """
    Returns all tools exposed by registered MCP Servers.
    """
    return {
        "success": True,
        "tools": mcp_manager.list_all_tools()
    }


@router.get("/mcp/resources")
def get_mcp_resources():
    """
    Returns all resources exposed by registered MCP Servers.
    """
    return {
        "success": True,
        "resources": mcp_manager.list_all_resources()
    }


@router.post("/mcp/call_tool")
def call_mcp_tool(req: ToolCallRequest):
    """
    Executes an MCP tool with Privacy Firewall interception & output sanitization.
    """
    if not req.tool_name:
        raise HTTPException(status_code=400, detail="tool_name is required.")

    res = mcp_manager.execute_tool_guarded(
        tool_name=req.tool_name,
        arguments=req.arguments or {},
        server_id=req.server_id
    )

    return res
