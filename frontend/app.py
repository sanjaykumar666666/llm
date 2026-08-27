"""
Aiera AI — Privacy-Aware AI Workspace & Zero-Trust Gateway.
File: frontend/app.py
"""

import sys
import os
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Page Configuration — AI Privacy Shield
logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
st.set_page_config(
    page_title="AI Privacy Shield — Multimodal Security Gateway",
    page_icon=str(logo_path) if logo_path.exists() else "🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Custom CSS & Theme Injector
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.session_state.get("theme") == "light":
    st.markdown(
        """
        <style>
        :root {
            --bg-void: #F8FAFC;
            --bg-surface: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-card2: #F1F5F9;
            --bg-card3: #E2E8F0;
            --bg-input: #FFFFFF;
            --text-pure: #0F172A;
            --text-muted: #64748B;
            --border: rgba(203, 213, 225, 0.7);
            --border-blue: rgba(59, 130, 246, 0.35);
            --border-cyan: rgba(6, 182, 212, 0.4);
            --bg-sidebar: #FFFFFF;
            --bg-sidebar-base: #FFFFFF;
            --border-sidebar: #E2E8F0;
            --shadow-sidebar: 2px 0 20px rgba(0, 0, 0, 0.04);
            --btn-sidebar-bg: #F8FAFC;
            --btn-sidebar-color: #334155;
            --btn-sidebar-border: #E2E8F0;
            --btn-sidebar-hover-bg: #EFF6FF;
            --btn-sidebar-hover-color: #1D4ED8;
            --btn-sidebar-hover-border: #93C5FD;
        }
        html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main, .main {
            background: #F8FAFC !important;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        .stApp::before {
            display: none !important;
        }
        div[data-testid="stSidebarNav"],
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div:first-child,
        div[data-testid="stSidebarContent"],
        div[data-testid="stSidebarUserContent"],
        div[data-testid="stSidebarHeader"],
        [data-testid="stSidebar"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
            box-shadow: 2px 0 20px rgba(0, 0, 0, 0.03) !important;
        }
        section[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
        div[data-testid="stSidebar"] button,
        div[data-testid="stSidebar"] .stButton button {
            background: #F8FAFC !important;
            background-color: #F8FAFC !important;
            color: #334155 !important;
            border: 1px solid #E2E8F0 !important;
        }
        section[data-testid="stSidebar"] button:hover,
        div[data-testid="stSidebar"] button:hover {
            background: #EFF6FF !important;
            color: #1D4ED8 !important;
            border-color: #93C5FD !important;
        }
        section[data-testid="stSidebar"] [data-testid="baseButton-primary"],
        section[data-testid="stSidebar"] button[kind="primary"],
        div[data-testid="stSidebar"] [data-testid="baseButton-primary"],
        div[data-testid="stSidebar"] button[kind="primary"] {
            background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid #2563EB !important;
            border-left: 4px solid #1D4ED8 !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25) !important;
        }
        .stTextArea textarea,
        .stTextInput input {
            background: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
        }
        div[data-testid="stExpander"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
        }
        code, pre {
            background: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            color: #1E40AF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        :root {
            --bg-void: #050914;
            --bg-surface: #08111F;
            --bg-card: rgba(13, 23, 41, 0.85);
            --bg-card2: #101C31;
            --bg-card3: #111D34;
            --bg-input: #0A1324;
            --text-pure: #F8FAFC;
            --text-muted: #94A3B8;
            --border: rgba(255, 255, 255, 0.09);
            --border-blue: rgba(59, 130, 246, 0.30);
            --border-cyan: rgba(6, 182, 212, 0.40);
            --bg-sidebar: linear-gradient(180deg, #050d1e 0%, #08162d 40%, #0b1c38 100%);
            --bg-sidebar-base: #050d1e;
            --border-sidebar: rgba(59, 130, 246, 0.20);
            --shadow-sidebar: 4px 0 40px rgba(0, 0, 0, 0.6);
            --btn-sidebar-bg: rgba(10, 25, 48, 0.65);
            --btn-sidebar-color: #94A3B8;
            --btn-sidebar-border: rgba(59, 130, 246, 0.14);
            --btn-sidebar-hover-bg: rgba(6, 182, 212, 0.14);
            --btn-sidebar-hover-color: #F8FAFC;
            --btn-sidebar-hover-border: rgba(6, 182, 212, 0.45);
        }
        html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main, .main {
            background: #050914 !important;
            background-color: #050914 !important;
            color: #F8FAFC !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Import Sidebar
from frontend.components.sidebar import render_sidebar

# Import Views
from frontend.views.dashboard import render_dashboard_view
from frontend.views.chatbot import render_chatbot_view
from frontend.views.projects_view import render_projects_view
from frontend.views.tools_catalog import render_tools_catalog_view
from frontend.views.trust_center import render_trust_center_view
from frontend.views.pipeline_view import render_pipeline_view
from frontend.views.text_analyzer import render_text_analyzer_view
from frontend.views.image_analyzer import render_image_analyzer_view
from frontend.views.video_analyzer import render_video_analyzer_view
from frontend.views.youtube_analyzer import render_youtube_analyzer_view
from frontend.views.injection_detector import render_injection_detector_view
from frontend.views.text_summarizer import render_text_summarizer_view
from frontend.views.explainability import render_explainability_view
from frontend.views.trust_receipts import render_trust_receipts_view
from frontend.views.history import render_history_view
from frontend.views.documents import render_documents_view
from frontend.views.settings import render_settings_view
from frontend.views.profile_view import render_profile_view


def main():
    selected_page = render_sidebar()

    # Override check
    forced_page = st.session_state.pop("force_page", None)
    if forced_page:
        selected_page = forced_page

    # ── Canonical Navigation Routing ──────────────────────────────────────────
    page = selected_page.lower().strip()

    # 1. SYSTEM: Dashboard Control Center
    if page == "dashboard":
        render_dashboard_view()

    # 2. CHAT: AI Trust Chat & Multi-Modal Execution
    elif page in ("chat", "privacy chat", "ai trust chat"):
        render_chatbot_view()

    # 3. WORKSPACE: Projects
    elif page in ("projects", "workspace"):
        render_projects_view()

    # 4. TOOLS: Catalog & Specialized Views
    elif page in ("tools", "all tools", "all tools catalog"):
        render_tools_catalog_view()
    elif page in ("web search", "deep research", "data analysis", "code", "code workspace"):
        # Map active tool and route to chat engine
        if page == "web search":
            st.session_state["active_tool"] = "🔎 Web Search"
        elif page == "deep research":
            st.session_state["active_tool"] = "🧠 Deep Research"
        elif page == "data analysis":
            st.session_state["active_tool"] = "📊 Data Analysis"
        elif page in ("code", "code workspace"):
            st.session_state["active_tool"] = "💻 Code Workspace"
        render_chatbot_view()

    elif page in ("files", "files parser", "documents"):
        render_documents_view()
    elif page in ("text privacy", "text analysis", "text"):
        render_text_analyzer_view()
    elif page in ("image privacy", "image analysis", "image"):
        render_image_analyzer_view()
    elif page in ("video privacy", "video analysis", "video"):
        render_video_analyzer_view()
    elif page in ("youtube analyzer", "youtube", "youtube privacy"):
        render_youtube_analyzer_view()
    elif page in ("canvas", "canvas editor", "canvas workspace", "ai summarizer", "summarizer"):
        st.session_state["active_tool"] = "✍️ Canvas"
        render_text_summarizer_view()

    # 5. AI TRUST: Trust Center, Pipeline, Security, Explainability, Receipts
    elif page in ("trust center", "ai trust", "trust"):
        render_trust_center_view()
    elif page in ("prompt security", "security", "injection"):
        render_injection_detector_view()
    elif page in ("pipeline", "architecture", "architecture & pipeline"):
        render_pipeline_view()
    elif page in ("explainability", "xai", "explainability (xai)"):
        render_explainability_view()
    elif page in ("audit receipts", "receipts", "trust receipts"):
        render_trust_receipts_view()

    # 6. SYSTEM: History, Settings, Profile
    elif page in ("history", "audit history", "audit log"):
        render_history_view()
    elif page == "settings":
        render_settings_view()
    elif page == "profile":
        render_profile_view()

    # Fallback to Dashboard
    else:
        render_dashboard_view()


if __name__ == "__main__":
    main()
