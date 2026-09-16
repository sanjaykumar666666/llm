import base64
from pathlib import Path
import streamlit as st


def _get_logo_b64() -> str:
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except Exception:
            pass
    return ""


from frontend.utils.theme_manager import COLOR_THEMES, get_current_theme, get_current_theme_key


def render_sidebar() -> str:
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "Dashboard"

    theme = get_current_theme()
    is_dark = theme.get("is_dark", True)
    title_gradient = theme.get("gradient", "linear-gradient(135deg, #FF007A 0%, #00D9F6 100%)")
    sub_color = theme.get("accent_secondary", "#00D9F6")
    footer_bg = theme.get("badge_bg", "rgba(0, 217, 246, 0.12)")
    footer_border = theme.get("badge_border", "rgba(0, 217, 246, 0.35)")
    footer_sub = theme.get("text_muted", "#94A3B8")
    divider_color = theme.get("gradient", "linear-gradient(90deg, transparent, #FF007A, #00D9F6, transparent)")
    logo_b64 = _get_logo_b64()

    with st.sidebar:
        # ── BRAND HEADER WITH OFFICIAL LOGO ──────────────────────────────────
        logo_html = f"""<img src="{logo_b64}" style="width:48px; height:48px; border-radius:14px; object-fit:contain; box-shadow:{theme['glow']}; border:1.5px solid rgba(255,255,255,0.4); flex-shrink:0; background:rgba(15,23,42,0.8);" alt="AI Privacy Shield" />""" if logo_b64 else f"""<div style="background: {theme['gradient']}; width:46px; height:46px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:22px; box-shadow:{theme['glow']};">🛡️</div>"""

        st.markdown(
            f"""
            <div style="padding: 12px 6px 14px 6px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    {logo_html}
                    <div>
                        <div style="
                            font-size:16px; font-weight:900;
                            letter-spacing:0.6px; line-height:1.15;
                            color: #FFFFFF;
                            text-shadow: 0 2px 10px rgba(0,0,0,0.6);
                        ">AI PRIVACY SHIELD</div>
                        <div style="
                            color: {sub_color};
                            font-size:10px; font-weight:900;
                            letter-spacing:1.3px; margin-top:3px;
                            text-transform: uppercase;
                        ">MULTIMODAL SECURITY</div>
                    </div>
                </div>
            </div>
            <div style="height:2px; background: {divider_color}; margin: 0 6px 12px 6px; border-radius:2px;"></div>
            """,
            unsafe_allow_html=True,
        )

        # ── COLOR PALETTE SELECTOR ────────────────────────────────────────────
        theme_keys = list(COLOR_THEMES.keys())
        current_theme_key = get_current_theme_key()
        current_idx = theme_keys.index(current_theme_key) if current_theme_key in theme_keys else 0

        selected_theme = st.selectbox(
            "🎨 Color Theme:",
            theme_keys,
            index=current_idx,
            key="sb_color_theme_select"
        )
        if selected_theme != current_theme_key:
            st.session_state["color_theme"] = selected_theme
            st.rerun()

        st.markdown(f"<div style='height:1px; background:rgba(255,255,255,0.08); margin: 8px 6px 14px 6px;'></div>", unsafe_allow_html=True)

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
            ("Research & Benchmarks", "📊"),
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
            <div style="height:2px; background: {divider_color}; margin: 0 6px 14px 6px; border-radius:2px;"></div>
            <div style="
                padding:12px 14px;
                background: {footer_bg};
                border:1px solid {footer_border};
                border-radius:13px;
                text-align:center;
                backdrop-filter: blur(12px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.35), inset 0 0 15px rgba(255,255,255,0.05);
            ">
                <div style="font-size:12px; font-weight:900; color:{theme['accent_quaternary']}; display:flex; align-items:center; justify-content:center; gap:7px;">
                    <span style="font-size:10px; animation:soc-pulse-green 2s infinite;">●</span> SYSTEM ONLINE
                </div>
                <div style="color:{footer_sub}; font-size:9.5px; margin-top:3px; font-weight:700; letter-spacing:0.5px;">{theme['name']} Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.get("selected_page", "Dashboard")
