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
from frontend.utils.theme_manager import inject_theme_css, get_current_theme_key

if "color_theme" not in st.session_state:
    st.session_state["color_theme"] = "🌈 Rainbow Aurora"

css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inject active theme stylesheet
inject_theme_css()

# Import Sidebar (lightweight — no heavy deps)
from frontend.components.sidebar import render_sidebar


def main():
    selected_page = render_sidebar()

    # Override check
    forced_page = st.session_state.pop("force_page", None)
    if forced_page:
        selected_page = forced_page

    # ── Canonical Navigation Routing (LAZY IMPORTS) ───────────────────────────
    page = selected_page.lower().strip()

    # 1. SYSTEM: Dashboard Control Center
    if page == "dashboard":
        from frontend.views.dashboard import render_dashboard_view
        render_dashboard_view()

    # 2. CHAT: AI Trust Chat & Multi-Modal Execution
    elif page in ("chat", "privacy chat", "ai trust chat"):
        from frontend.views.chatbot import render_chatbot_view
        render_chatbot_view()

    # 3. WORKSPACE: Projects
    elif page in ("projects", "workspace"):
        from frontend.views.projects_view import render_projects_view
        render_projects_view()

    # 4. TOOLS: Catalog & Specialized Views
    elif page in ("tools", "all tools", "all tools catalog"):
        from frontend.views.tools_catalog import render_tools_catalog_view
        render_tools_catalog_view()
    elif page in ("web search", "deep research", "data analysis", "code", "code workspace"):
        if page == "web search":
            st.session_state["active_tool"] = "🔎 Web Search"
        elif page == "deep research":
            st.session_state["active_tool"] = "🧠 Deep Research"
        elif page == "data analysis":
            st.session_state["active_tool"] = "📊 Data Analysis"
        elif page in ("code", "code workspace"):
            st.session_state["active_tool"] = "💻 Code Workspace"
        from frontend.views.chatbot import render_chatbot_view
        render_chatbot_view()

    elif page in ("files", "files parser", "documents"):
        from frontend.views.documents import render_documents_view
        render_documents_view()
    elif page in ("text privacy", "text analysis", "text"):
        from frontend.views.text_analyzer import render_text_analyzer_view
        render_text_analyzer_view()
    elif page in ("image privacy", "image analysis", "image"):
        from frontend.views.image_analyzer import render_image_analyzer_view
        render_image_analyzer_view()
    elif page in ("video privacy", "video analysis", "video"):
        from frontend.views.video_analyzer import render_video_analyzer_view
        render_video_analyzer_view()

    elif page in ("youtube analyzer", "youtube", "youtube privacy"):
        from frontend.views.youtube_analyzer import render_youtube_analyzer_view
        render_youtube_analyzer_view()
    elif page in ("canvas", "canvas editor", "canvas workspace", "ai summarizer", "summarizer"):

        st.session_state["active_tool"] = "✍️ Canvas"
        from frontend.views.text_summarizer import render_text_summarizer_view
        render_text_summarizer_view()

    # 5. AI TRUST: Trust Center, Pipeline, Security, Explainability, Receipts
    elif page in ("trust center", "ai trust", "trust"):
        from frontend.views.trust_center import render_trust_center_view
        render_trust_center_view()
    elif page in ("prompt security", "security", "injection"):
        from frontend.views.injection_detector import render_injection_detector_view
        render_injection_detector_view()
    elif page in ("research & benchmarks", "research", "ablation", "benchmarks"):
        from frontend.views.privacy_research_view import render_privacy_research_view
        render_privacy_research_view()
    elif page in ("pipeline", "architecture", "architecture & pipeline"):
        from frontend.views.pipeline_view import render_pipeline_view
        render_pipeline_view()
    elif page in ("explainability", "xai", "explainability (xai)"):
        from frontend.views.explainability import render_explainability_view
        render_explainability_view()
    elif page in ("audit receipts", "receipts", "trust receipts"):
        from frontend.views.trust_receipts import render_trust_receipts_view
        render_trust_receipts_view()

    # 6. SYSTEM: History, Settings, Profile
    elif page in ("history", "audit history", "audit log"):
        from frontend.views.history import render_history_view
        render_history_view()
    elif page == "settings":
        from frontend.views.settings import render_settings_view
        render_settings_view()
    elif page == "profile":
        from frontend.views.profile_view import render_profile_view
        render_profile_view()

    # Fallback to Dashboard
    else:
        from frontend.views.dashboard import render_dashboard_view
        render_dashboard_view()


if __name__ == "__main__":
    main()
