"""
Aiera AI — Dedicated Tools Catalog View.
File: frontend/views/tools_catalog.py
"""

import streamlit as st


TOOLS_REGISTRY = [
    {
        "id": "web_search",
        "icon": "🔎",
        "name": "Web Search",
        "desc": "Search live web sources and generate answers with grounded citations.",
        "status": "AVAILABLE",
        "target_page": "Chat",
        "active_tool": "🔎 Web Search",
        "category": "Information & Research",
    },
    {
        "id": "deep_research",
        "icon": "🧠",
        "name": "Deep Research",
        "desc": "Autonomous multi-source research agent generating comprehensive reports.",
        "status": "AVAILABLE",
        "target_page": "Chat",
        "active_tool": "🧠 Deep Research",
        "category": "Information & Research",
    },
    {
        "id": "files",
        "icon": "📎",
        "name": "Files & Documents",
        "desc": "Parse, redact, and extract intelligence from PDFs, TXT, and enterprise documents.",
        "status": "AVAILABLE",
        "target_page": "Files",
        "active_tool": "📎 Files Parser",
        "category": "Data & Analysis",
    },
    {
        "id": "data_analysis",
        "icon": "📊",
        "name": "Data Analysis",
        "desc": "Analyze CSV datasets, compute statistics, and render interactive charts.",
        "status": "AVAILABLE",
        "target_page": "Chat",
        "active_tool": "📊 Data Analysis",
        "category": "Data & Analysis",
    },
    {
        "id": "text_privacy",
        "icon": "📝",
        "name": "Text Privacy Analyzer",
        "desc": "Detect PII, calculate risk scores, and sanitize raw textual prompts.",
        "status": "AVAILABLE",
        "target_page": "Text Privacy",
        "active_tool": "Text Privacy",
        "category": "Privacy & Security",
    },
    {
        "id": "image_privacy",
        "icon": "🖼️",
        "name": "Image Privacy",
        "desc": "Optical character recognition (OCR) and facial redaction with Gaussian blur.",
        "status": "AVAILABLE",
        "target_page": "Image Privacy",
        "active_tool": "Image Privacy",
        "category": "Privacy & Security",
    },
    {
        "id": "video_privacy",
        "icon": "🎥",
        "name": "Video Privacy",
        "desc": "Frame-by-frame multimodal video privacy inspection and timeline analysis.",
        "status": "AVAILABLE",
        "target_page": "Video Privacy",
        "active_tool": "Video Privacy",
        "category": "Privacy & Security",
    },
    {
        "id": "youtube_analyzer",
        "icon": "▶️",
        "name": "YouTube Analyzer",
        "desc": "Spoken transcript privacy auditing with timestamp timeline and XAI attribution.",
        "status": "AVAILABLE",
        "target_page": "YouTube Analyzer",
        "active_tool": "YouTube Analyzer",
        "category": "Privacy & Security",
    },
    {
        "id": "canvas",
        "icon": "✍️",
        "name": "Canvas Workspace",
        "desc": "Interactive Markdown workspace for drafting, summarizing, and expanding content.",
        "status": "AVAILABLE",
        "target_page": "Canvas",
        "active_tool": "Canvas",
        "category": "Productivity",
    },
    {
        "id": "code_workspace",
        "icon": "💻",
        "name": "Code Workspace",
        "desc": "Generate, test, and safely execute Python scripts in a sandboxed runtime.",
        "status": "AVAILABLE",
        "target_page": "Chat",
        "active_tool": "💻 Code Workspace",
        "category": "Productivity",
    },
]


def render_tools_catalog_view() -> None:
    st.markdown(
        """
        <div style="padding: 10px 0 18px 0;">
            <h1 style="color:#0F172A; font-size:28px; font-weight:900; margin:0 0 6px 0;">
                🛠️ Tools & Integrations Catalog
            </h1>
            <p style="color:#475569; font-size:14px; font-weight:500; margin:0;">
                Launch specialized privacy-preserving tools, multimodal agents, and workspaces.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # Categories
    categories = ["All", "Information & Research", "Privacy & Security", "Data & Analysis", "Productivity"]
    selected_cat = st.radio("Filter Category:", categories, horizontal=True, label_visibility="collapsed")

    filtered_tools = TOOLS_REGISTRY if selected_cat == "All" else [t for t in TOOLS_REGISTRY if t["category"] == selected_cat]

    st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    # Grid of 2 columns
    for i in range(0, len(filtered_tools), 2):
        c1, c2 = st.columns(2)
        
        with c1:
            t = filtered_tools[i]
            _render_tool_card(t)

        if i + 1 < len(filtered_tools):
            with c2:
                t2 = filtered_tools[i + 1]
                _render_tool_card(t2)


def _render_tool_card(tool: dict) -> None:
    status_col = "#10B981" if tool["status"] == "AVAILABLE" else "#64748B"
    status_bg = "rgba(16,185,129,0.12)" if tool["status"] == "AVAILABLE" else "rgba(100,116,139,0.12)"
    status_border = "rgba(16,185,129,0.3)" if tool["status"] == "AVAILABLE" else "rgba(100,116,139,0.3)"

    st.markdown(
        f"""
        <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:18px; margin-bottom:14px; box-shadow:0 4px 16px rgba(0,0,0,0.25); min-height:140px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:22px;">{tool['icon']}</span>
                        <span style="color:#FFFFFF; font-size:16px; font-weight:800;">{tool['name']}</span>
                    </div>
                    <span style="background:{status_bg}; color:{status_col}; border:1px solid {status_border}; font-size:10px; font-weight:800; padding:2px 8px; border-radius:10px;">
                        ● {tool['status']}
                    </span>
                </div>
                <p style="color:#94A3B8; font-size:12.5px; line-height:1.4; margin:0 0 12px 0;">
                    {tool['desc']}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(f"Launch {tool['name']} →", key=f"launch_tool_{tool['id']}", use_container_width=True, type="primary"):
        st.session_state["selected_page"] = tool["target_page"]
        if tool.get("active_tool"):
            st.session_state["active_tool"] = tool["active_tool"]
        st.rerun()
