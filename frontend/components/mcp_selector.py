"""
Streamlit Model Context Protocol (MCP) Selector & Status Component.
File: frontend/components/mcp_selector.py
"""

import streamlit as st
from typing import Dict, Any, List
from frontend.services.api_client import APIClient


def render_mcp_selector() -> bool:
    """
    Renders MCP Configuration Drawer & Server/Tool selection toggles.
    Returns boolean indicating whether MCP context integration is enabled.
    """
    with st.expander("⚙️ Model Context Protocol (MCP) Integration", expanded=False):
        mcp_enabled = st.toggle("Enable MCP Tool & Context Engine", value=True, help="Allows Chatbot to call privacy-guarded MCP tools and fetch context resources.")

        if mcp_enabled:
            st.caption("Active MCP Servers & Available Tools:")

            servers_data = APIClient.get_mcp_servers()
            servers = servers_data.get("servers", [])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Registered Servers:**")
                for s in servers:
                    st.markdown(f"- 🟢 **{s['name']}** (`{s['server_id']}`)")

            with c2:
                st.markdown("**Available Tools:**")
                tools_data = APIClient.get_mcp_tools()
                tools = tools_data.get("tools", [])
                for t in tools:
                    st.markdown(f"- 🛠️ `{t['name']}` ({t['server_id']})")

            st.info("🔒 **Privacy Guarantee**: All MCP tool parameters and outputs are continuously inspected by the BERT + Naive Bayes Decision Gate.")

    return mcp_enabled


def render_mcp_tool_execution_badge(mcp_meta: Dict[str, Any]) -> None:
    """
    Renders a visual badge showing safe MCP Tool invocation details inside chat stream.
    """
    if not mcp_meta:
        return

    tool_name = mcp_meta.get("tool_name", "mcp_tool")
    status = mcp_meta.get("status", "SUCCESS")
    color = "green" if status == "SUCCESS" else "red"

    st.markdown(f"""
    <div style="background-color: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 8px 12px; margin: 8px 0; border-radius: 4px; font-size: 13px;">
        <span style="font-weight: 600; color: #10b981;">⚡ MCP Tool Call:</span> <code>{tool_name}</code> | 
        <span style="font-weight: 600; color: {color};">[{status}]</span>
    </div>
    """, unsafe_allow_html=True)
