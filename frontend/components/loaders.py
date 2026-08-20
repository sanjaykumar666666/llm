"""
Loaders, Empty States, and Banner Components.
File: frontend/components/loaders.py
"""

import streamlit as st

def render_demo_banner(module_name: str) -> None:
    """Renders Phase 1 demonstration and architecture banner."""
    st.markdown(f"""
    <div class="demo-banner">
        <div>💡 <strong>Phase 1 Foundation</strong>: Running <code>{module_name}</code> UI with API Gateway & mock/demo response placeholders.</div>
        <div style="opacity: 0.8; font-size: 11px;">Phase 2 will plug in live BERT / Naive Bayes / OCR models.</div>
    </div>
    """, unsafe_allow_html=True)

def render_empty_state(title: str, subtitle: str, icon: str = "🔍") -> None:
    """Renders structured empty state placeholder."""
    st.markdown(f"""
    <div class="ps-empty-state">
        <div class="ps-empty-icon">{icon}</div>
        <h4 style="color: #E2E8F0; margin-bottom: 4px;">{title}</h4>
        <p style="font-size: 13px; margin: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_error_state(error_msg: str) -> None:
    """Renders structured error state box."""
    st.error(f"❌ **Processing Error**: {error_msg}\n\nPlease check system backend status or retry input parameters.")
