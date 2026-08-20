"""
Status Badges & Risk Display Components.
File: frontend/components/status_badges.py
"""

import streamlit as st

def render_status_badge(status: str) -> None:
    """Renders visual status badges for Safe / Warning / Block / Suspicious states."""
    s = str(status).upper()
    if s in ["SAFE", "ALLOW", "CLEAN"]:
        st.markdown('<span class="badge-safe">🛡️ SAFE / ALLOWED</span>', unsafe_allow_html=True)
    elif s in ["WARNING", "WARN", "SUSPICIOUS"]:
        st.markdown('<span class="badge-warning">⚠️ WARNING / SANITIZED</span>', unsafe_allow_html=True)
    elif s in ["BLOCK", "CRITICAL", "MALICIOUS"]:
        st.markdown('<span class="badge-block">⛔ CRITICAL / BLOCKED</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-suspicious">⚡ {s}</span>', unsafe_allow_html=True)

def render_risk_gauge(score: float, label: str = "Privacy Risk Score") -> None:
    """Renders a progress bar risk gauge with color coding."""
    st.markdown(f"**{label}**: `{score:.1f}%`")
    
    # Progress color mapping
    if score < 35:
        st.progress(int(score) / 100.0)
        st.caption("🟢 Low Risk Level - Clean payload")
    elif score < 70:
        st.progress(int(score) / 100.0)
        st.caption("🟡 Moderate Risk Level - Sanitization recommended")
    else:
        st.progress(int(score) / 100.0)
        st.caption("🔴 High Risk Level - Action Block recommended")
