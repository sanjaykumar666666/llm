"""
AI Privacy Shield — Enterprise Navigation Sidebar (Dual Theme Aware).
File: frontend/components/sidebar.py

Premium sidebar with glowing shield icon, gradient active state,
and hover animations. 280px width, deep navy / pearl ice dual styling.
"""

import streamlit as st


def render_sidebar() -> str:
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "Dashboard"
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    is_dark = st.session_state.get("theme", "dark") == "dark"
    title_gradient = "linear-gradient(135deg, #FFFFFF 0%, #93C5FD 100%)" if is_dark else "linear-gradient(135deg, #0F172A 0%, #1E40AF 100%)"
    sub_color = "#06B6D4" if is_dark else "#2563EB"
    footer_bg = "rgba(16,185,129,0.08)" if is_dark else "rgba(16,185,129,0.12)"
    footer_border = "rgba(16,185,129,0.25)" if is_dark else "rgba(16,185,129,0.35)"
    footer_sub = "#94A3B8" if is_dark else "#64748B"
    divider_color = "rgba(59,130,246,0.15)" if is_dark else "rgba(203,213,225,0.6)"

    with st.sidebar:
        # ── PREMIUM BRAND HEADER WITH GLOWING SHIELD ──────────────────────────
        st.markdown(
            f"""
            <div style="padding: 12px 6px 20px 6px;">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="
                        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 50%, #06B6D4 100%);
                        width:46px; height:46px; border-radius:13px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:22px;
                        box-shadow: 0 0 25px rgba(37,99,235,0.55), 0 0 45px rgba(139,92,246,0.35), 0 4px 14px rgba(0,0,0,0.35);
                        border: 1.5px solid rgba(147,197,253,0.45);
                        animation: soc-glow-pulse 3s ease-in-out infinite;
                        position: relative; flex-shrink: 0;
                    ">
                        🛡️
                    </div>
                    <div>
                        <div style="
                            font-size:16.5px; font-weight:900;
                            letter-spacing:0.6px; line-height:1.15;
                            background: {title_gradient};
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            background-clip: text;
                        ">AI PRIVACY SHIELD</div>
                        <div style="
                            color:{sub_color}; font-size:10px; font-weight:800;
                            letter-spacing:1.3px; margin-top:3px;
                            text-transform: uppercase;
                        ">MULTIMODAL SECURITY</div>
                    </div>
                </div>
            </div>
            <div style="height:1px; background: linear-gradient(90deg, transparent, {divider_color}, transparent); margin: 0 6px 14px 6px;"></div>
            """,
            unsafe_allow_html=True,
        )

        current_page = st.session_state.get("selected_page", "Dashboard")

        # ── NAVIGATION ITEMS ──────────────────────────────────────────────────
        nav_items = [
            ("Dashboard", "🏠"),
            ("Privacy Chat", "💬"),
            ("Text Analysis", "📄"),
            ("Image Analysis", "🖼️"),
            ("Video Analysis", "🎥"),
            ("YouTube Analyzer", "▶️"),
            ("Prompt Security", "🛡️"),
            ("AI Summarizer", "✨"),
            ("Audit History", "🕘"),
            ("Settings", "⚙️"),
        ]

        for name, icon in nav_items:
            is_active = (current_page.lower() == name.lower())
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {name}", key=f"sb_nav_{name.lower().replace(' ', '_')}", use_container_width=True, type=btn_type):
                st.session_state["selected_page"] = name
                st.rerun()

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # ── SYSTEM STATUS FOOTER ──────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="height:1px; background: linear-gradient(90deg, transparent, {divider_color}, transparent); margin: 0 6px 14px 6px;"></div>
            <div style="
                padding:12px 14px;
                background: linear-gradient(135deg, {footer_bg}, rgba(6,182,212,0.06));
                border:1px solid {footer_border};
                border-radius:13px;
                text-align:center;
                backdrop-filter: blur(8px);
            ">
                <div style="color:#10B981; font-size:11.5px; font-weight:800; display:flex; align-items:center; justify-content:center; gap:7px;">
                    <span style="font-size:9px; animation:soc-pulse-green 2s infinite;">●</span> SYSTEM ONLINE
                </div>
                <div style="color:{footer_sub}; font-size:9.5px; margin-top:3px; font-weight:600;">Multimodal Protection Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.get("selected_page", "Dashboard")
