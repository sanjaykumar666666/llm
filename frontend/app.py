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

# Page Configuration — Aiera AI
st.set_page_config(
    page_title="Aiera AI — Privacy-Aware AI Workspace",
    page_icon="🛡️",
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
            --bg-void: #f8fbff;
            --bg-surface: #FFFFFF;
            --bg-card: rgba(255,255,255,0.78);
            --bg-input: #F1F5F9;
            --text-pure: #0F172A;
            --text-muted: #64748B;
            --border: rgba(203, 213, 225, 0.6);
            --border-blue: rgba(59, 130, 246, 0.25);
            --border-cyan: rgba(6, 182, 212, 0.35);
        }
        .stApp {
            background:
                radial-gradient(circle at 10% 10%, rgba(110,180,255,0.16), transparent 30%),
                radial-gradient(circle at 90% 20%, rgba(180,120,255,0.14), transparent 30%),
                radial-gradient(circle at 50% 80%, rgba(255,160,200,0.08), transparent 40%),
                radial-gradient(circle at 30% 60%, rgba(100,220,220,0.06), transparent 35%),
                linear-gradient(135deg, #f8fbff 0%, #f4f1ff 50%, #fdf2f8 100%) !important;
            background-color: #f8fbff !important;
            color: #0F172A !important;
        }
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(300px circle at 20% 30%, rgba(110,180,255,0.08), transparent),
                radial-gradient(250px circle at 80% 60%, rgba(180,120,255,0.06), transparent);
            pointer-events: none;
            z-index: 0;
            animation: soc-float-blob 20s ease-in-out infinite;
        }
        div[data-testid="stSidebarNav"],
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div:first-child,
        div[data-testid="stSidebarContent"],
        div[data-testid="stSidebarUserContent"],
        div[data-testid="stSidebarHeader"],
        [data-testid="stSidebar"],
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-6qob1r,
        .st-emotion-cache-12fmwca,
        .st-emotion-cache-1r6slb0 {
            background: linear-gradient(180deg, #FFFFFF 0%, #F0F4FF 40%, #F8F6FF 100%) !important;
            background-color: #FFFFFF !important;
            border-right: 1px solid rgba(203, 213, 225, 0.5) !important;
            box-shadow: 2px 0 24px rgba(15, 23, 42, 0.06), inset -1px 0 0 rgba(203,213,225,0.3) !important;
        }
        section[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
        div[data-testid="stSidebar"] button,
        div[data-testid="stSidebar"] .stButton button {
            background: rgba(241, 245, 249, 0.85) !important;
            background-color: rgba(241, 245, 249, 0.85) !important;
            color: #475569 !important;
            border: 1px solid rgba(203, 213, 225, 0.5) !important;
        }
        section[data-testid="stSidebar"] button:hover,
        div[data-testid="stSidebar"] button:hover {
            background: rgba(59, 130, 246, 0.08) !important;
            color: #0F172A !important;
            border-color: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 0 16px rgba(59, 130, 246, 0.15) !important;
        }
        section[data-testid="stSidebar"] [data-testid="baseButton-primary"],
        div[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%) !important;
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(147,197,253,0.5) !important;
            border-left: 3.5px solid #2563EB !important;
            box-shadow: 0 4px 18px rgba(37, 99, 235, 0.3), 0 0 20px rgba(139,92,246,0.15) !important;
        }
        .stTextArea textarea,
        .stTextInput input {
            background: rgba(255,255,255,0.9) !important;
            color: #0F172A !important;
            border: 1px solid rgba(203, 213, 225, 0.7) !important;
            backdrop-filter: blur(8px) !important;
        }
        div.stButton > button[data-testid="baseButton-primary"]:not(
            section[data-testid="stSidebar"] *
        ) {
            background: linear-gradient(135deg, #2563EB, #7C3AED) !important;
            box-shadow: 0 4px 16px rgba(37,99,235,0.25) !important;
        }
        div.stButton > button[data-testid="baseButton-secondary"]:not(
            section[data-testid="stSidebar"] *
        ) {
            background: rgba(241,245,249,0.8) !important;
            color: #475569 !important;
            border: 1px solid rgba(203,213,225,0.6) !important;
        }
        div[data-testid="stExpander"] {
            background: rgba(241,245,249,0.7) !important;
            border: 1px solid rgba(203,213,225,0.5) !important;
        }
        code, pre {
            background: #F1F5F9 !important;
            border: 1px solid rgba(203,213,225,0.5) !important;
            color: #1E40AF !important;
        }
        div[data-testid="stChatInput"],
        div[data-testid="stChatInputContainer"],
        .stChatInputContainer {
            background: rgba(255,255,255,0.85) !important;
            border: 1px solid rgba(59,130,246,0.25) !important;
            box-shadow: 0 4px 16px rgba(15,23,42,0.06) !important;
        }
        div[data-testid="stChatInput"] textarea,
        .stChatInputContainer textarea {
            background: rgba(255,255,255,0.85) !important;
            color: #0F172A !important;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.8) !important;
            border: 1px solid rgba(203,213,225,0.5) !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0F172A !important;
        }
        div[data-testid="stAlert"][kind="warning"],
        div.stAlert[data-baseweb="notification"][kind="warning"] {
            background: rgba(255,251,235,0.8) !important;
            color: #92400E !important;
        }
        div[data-testid="stAlert"][kind="error"],
        div.stAlert[data-baseweb="notification"][kind="error"] {
            background: rgba(254,242,242,0.8) !important;
            color: #991B1B !important;
        }
        div[data-testid="stAlert"][kind="success"] {
            background: rgba(236,253,245,0.8) !important;
            color: #065F46 !important;
        }
        div[data-testid="stInfo"] {
            background: rgba(239,246,255,0.8) !important;
            color: #1E40AF !important;
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
