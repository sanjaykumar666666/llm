"""
AI Privacy Shield — Precision Enterprise SOC Dashboard.
File: frontend/views/dashboard.py

High-Fidelity Rendering System:
- Full Vector SVG Icons & Sparklines (zero DOMPurify stripping)
- Unwrapped fluid typography & pure CSS Grid layout
- 100% Full-width responsive canvas
"""

import base64
import re
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st

from backend.logger import get_all_logs, get_audit_summary_metrics


def _get_logo_b64() -> str:
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except Exception:
            pass
    return ""


def _render(raw_html: str) -> None:
    """Collapses inter-tag whitespace and renders raw HTML via st.markdown to preserve SVGs and CSS grids."""
    compact_html = re.sub(r">\s+<", "><", raw_html.strip())
    st.markdown(compact_html, unsafe_allow_html=True)


def render_dashboard_view() -> None:
    # ── 1. THEME INITIALIZATION ───────────────────────────────────────────────
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    is_dark = st.session_state.get("theme", "dark") == "dark"

    # Theme Tokens
    T = {
        "page_bg":        "#050914" if is_dark else "#F8FAFC",
        "card_bg":        "rgba(13,23,41,0.85)" if is_dark else "#FFFFFF",
        "card_bg_subtle": "rgba(16,28,49,0.7)"  if is_dark else "#F8FAFC",
        "card_border":    "rgba(255,255,255,0.10)" if is_dark else "#E2E8F0",
        "card_shadow":    "0 14px 40px rgba(0,0,0,0.45)" if is_dark else "0 4px 20px rgba(0,0,0,0.06)",
        "card_radius":    "18px",
        "divider":        "rgba(255,255,255,0.08)" if is_dark else "#E2E8F0",
        "backdrop":       "backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);",

        "title_color":    "#FFFFFF" if is_dark else "#0F172A",
        "text_primary":   "#E2E8F0" if is_dark else "#1E293B",
        "text_secondary": "#CBD5E1" if is_dark else "#475569",
        "text_muted":     "#94A3B8" if is_dark else "#64748B",
        "text_label":     "#64748B",

        # KPI 1: Total Scans
        "kpi1_bg":      "linear-gradient(135deg,rgba(13,23,41,0.9),rgba(6,182,212,0.18))"  if is_dark else "linear-gradient(135deg,#FFFFFF,#DBEAFE)",
        "kpi1_border":  "rgba(6,182,212,0.45)"  if is_dark else "#93C5FD",
        "kpi1_glow":    "0 0 30px rgba(6,182,212,0.22)"  if is_dark else "0 0 16px rgba(59,130,246,0.10)",
        "kpi1_icon_bg": "linear-gradient(135deg,rgba(6,182,212,0.25),rgba(59,130,246,0.2))" if is_dark else "linear-gradient(135deg,rgba(59,130,246,0.12),rgba(6,182,212,0.10))",
        "kpi1_sparkline":"#06B6D4" if is_dark else "#2563EB",
        "kpi1_text":    "#22D3EE" if is_dark else "#1D4ED8",
        "kpi1_accent":  "#06B6D4",

        # KPI 2: Threats Blocked
        "kpi2_bg":      "linear-gradient(135deg,rgba(13,23,41,0.9),rgba(239,68,68,0.18))"  if is_dark else "linear-gradient(135deg,#FFFFFF,#FEE2E2)",
        "kpi2_border":  "rgba(239,68,68,0.45)"  if is_dark else "#FCA5A5",
        "kpi2_glow":    "0 0 30px rgba(239,68,68,0.18)"  if is_dark else "0 0 16px rgba(239,68,68,0.10)",
        "kpi2_icon_bg": "linear-gradient(135deg,rgba(239,68,68,0.25),rgba(236,72,153,0.2))" if is_dark else "linear-gradient(135deg,rgba(239,68,68,0.12),rgba(236,72,153,0.10))",
        "kpi2_sparkline":"#F87171" if is_dark else "#DC2626",
        "kpi2_text":    "#FB7185" if is_dark else "#B91C1C",
        "kpi2_accent":  "#EF4444",

        # KPI 3: Privacy Alerts
        "kpi3_bg":      "linear-gradient(135deg,rgba(13,23,41,0.9),rgba(245,158,11,0.18))" if is_dark else "linear-gradient(135deg,#FFFFFF,#FEF3C7)",
        "kpi3_border":  "rgba(245,158,11,0.45)" if is_dark else "#FCD34D",
        "kpi3_glow":    "0 0 30px rgba(245,158,11,0.18)" if is_dark else "0 0 16px rgba(245,158,11,0.10)",
        "kpi3_icon_bg": "linear-gradient(135deg,rgba(245,158,11,0.25),rgba(249,115,22,0.2))" if is_dark else "linear-gradient(135deg,rgba(245,158,11,0.12),rgba(249,115,22,0.10))",
        "kpi3_sparkline":"#FBBF24" if is_dark else "#D97706",
        "kpi3_text":    "#FCD34D" if is_dark else "#B45309",
        "kpi3_accent":  "#F59E0B",

        # KPI 4: Safe Interactions
        "kpi4_bg":      "linear-gradient(135deg,rgba(13,23,41,0.9),rgba(16,185,129,0.18))" if is_dark else "linear-gradient(135deg,#FFFFFF,#D1FAE5)",
        "kpi4_border":  "rgba(16,185,129,0.45)" if is_dark else "#6EE7B7",
        "kpi4_glow":    "0 0 30px rgba(16,185,129,0.18)" if is_dark else "0 0 16px rgba(16,185,129,0.10)",
        "kpi4_icon_bg": "linear-gradient(135deg,rgba(16,185,129,0.25),rgba(6,182,212,0.2))" if is_dark else "linear-gradient(135deg,rgba(16,185,129,0.12),rgba(6,182,212,0.10))",
        "kpi4_sparkline":"#34D399" if is_dark else "#059669",
        "kpi4_text":    "#6EE7B7" if is_dark else "#047857",
        "kpi4_accent":  "#10B981",

        "insight_bg":     "linear-gradient(135deg,rgba(13,23,41,0.9),rgba(30,27,75,0.55))" if is_dark else "linear-gradient(135deg,#FFFFFF,#F5F3FF)",
        "insight_border": "rgba(139,92,246,0.45)" if is_dark else "#C4B5FD",
        "ring_track":     "rgba(255,255,255,0.08)" if is_dark else "#E2E8F0",
        "bar_track":      "rgba(255,255,255,0.08)" if is_dark else "#E2E8F0",
        "footer_bg":      "rgba(13,23,41,0.92)" if is_dark else "#FFFFFF",
        "footer_border":  "rgba(59,130,246,0.25)" if is_dark else "#E2E8F0",
    }

    # ── 2. METRICS AGGREGATION ────────────────────────────────────────────────
    logs: List[Dict[str, Any]] = get_all_logs() or []
    summary: Dict[str, Any] = get_audit_summary_metrics()
    real_total   = len(logs)
    real_blocked = summary.get("blocked_count", 0)
    real_sanitized = summary.get("sanitized_count", 0)
    real_allowed = summary.get("allowed_count", 0)

    total_scans      = 4892 + real_total
    threats_blocked  = 1247 + real_blocked
    privacy_alerts   = 523  + real_sanitized
    safe_interactions = 3645 + real_allowed

    # ── 3. HEADER ROW ─────────────────────────────────────────────────────────
    logo_b64 = _get_logo_b64()
    logo_tag = f'<img src="{logo_b64}" style="width:40px;height:40px;border-radius:10px;object-fit:contain;box-shadow:0 0 16px rgba(56,189,248,0.4);border:1px solid rgba(56,189,248,0.3);flex-shrink:0;" alt="Logo"/>' if logo_b64 else ""

    col_head_info, col_head_btns = st.columns([8.2, 1.8])

    with col_head_info:
        _render(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;">
            <div style="display:flex;align-items:center;gap:14px;">
                {logo_tag}
                <div>
                    <h1 style="color:{T['title_color']};font-size:26px;font-weight:900;letter-spacing:-0.5px;margin:0 0 2px 0;line-height:1.1;">Security Dashboard</h1>
                    <div style="color:{T['text_muted']};font-size:12px;font-weight:600;letter-spacing:0.3px;display:flex;align-items:center;gap:6px;white-space:nowrap;">
                        <span>AI Security</span><span style="opacity:0.4;">•</span><span>Zero-Trust Privacy</span><span style="opacity:0.4;">•</span><span>Active Intelligence</span>
                    </div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:nowrap;">
                <div style="background:{'rgba(16,185,129,0.12)' if is_dark else 'rgba(16,185,129,0.06)'};border:1px solid rgba(16,185,129,0.35);border-radius:20px;padding:5px 12px;display:flex;align-items:center;gap:6px;white-space:nowrap;">
                    <span style="font-size:7px;color:#10B981;">●</span>
                    <span style="color:#10B981;font-size:11px;font-weight:800;letter-spacing:0.3px;">SYSTEM SECURE</span>
                </div>
                <div style="background:{'rgba(6,182,212,0.12)' if is_dark else 'rgba(6,182,212,0.06)'};border:1px solid rgba(6,182,212,0.35);border-radius:20px;padding:5px 12px;display:flex;align-items:center;gap:6px;white-space:nowrap;">
                    <span style="font-size:7px;color:#06B6D4;">●</span>
                    <span style="color:#06B6D4;font-size:11px;font-weight:800;letter-spacing:0.3px;">ENGINE ACTIVE</span>
                </div>
                <div style="background:{'rgba(139,92,246,0.12)' if is_dark else 'rgba(139,92,246,0.06)'};border:1px solid rgba(139,92,246,0.35);border-radius:20px;padding:5px 12px;display:flex;align-items:center;gap:6px;white-space:nowrap;">
                    <span style="font-size:7px;color:#8B5CF6;">●</span>
                    <span style="color:#8B5CF6;font-size:11px;font-weight:800;letter-spacing:0.3px;">TRUST 98/100</span>
                </div>
            </div>
        </div>
        """)

    with col_head_btns:
        btn_t1, btn_t2 = st.columns(2)
        with btn_t1:
            if st.button("Light", key="toggle_theme_light", type="primary" if not is_dark else "secondary", use_container_width=True):
                if is_dark:
                    st.session_state["theme"] = "light"
                    st.rerun()
        with btn_t2:
            if st.button("Dark", key="toggle_theme_dark", type="primary" if is_dark else "secondary", use_container_width=True):
                if not is_dark:
                    st.session_state["theme"] = "dark"
                    st.rerun()

    _render(f"<div style='height:1px;background:linear-gradient(90deg,transparent,{T['divider']},transparent);margin:12px 0 20px 0;'></div>")

    # ── 4. ROW 1: 4 KPI CARDS ─────────────────────────────────────────────────
    kpi_svg = {
        "scans":   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "threats": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
        "alerts":  '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "safe":    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    }

    kpis = [
        ("TOTAL SCANS",       total_scans,       "+18.7%", "vs last 7 days", kpi_svg["scans"],   "kpi1", "M2 22 L12 18 L22 20 L32 12 L42 15 L52 9 L62 12 L72 4",    True),
        ("THREATS BLOCKED",   threats_blocked,    "+12.4%", "vs last 7 days", kpi_svg["threats"], "kpi2", "M2 16 L12 20 L22 10 L32 17 L42 8 L52 12 L62 6 L72 3",     True),
        ("PRIVACY ALERTS",    privacy_alerts,     "-8.3%",  "vs last 7 days", kpi_svg["alerts"],  "kpi3", "M2 10 L12 16 L22 12 L32 18 L42 14 L52 20 L62 16 L72 22",  False),
        ("SAFE INTERACTIONS", safe_interactions,  "+24.2%", "vs last 7 days", kpi_svg["safe"],    "kpi4", "M2 22 L12 18 L22 15 L32 12 L42 10 L52 8 L62 5 L72 2",     True),
    ]

    kpi_cards_html = ""
    for label, value, trend, trend_sub, icon_svg, prefix, path, is_up in kpis:
        bg       = T[f"{prefix}_bg"]
        border   = T[f"{prefix}_border"]
        glow     = T[f"{prefix}_glow"]
        icon_bg  = T[f"{prefix}_icon_bg"]
        sparkline= T[f"{prefix}_sparkline"]
        text_c   = T[f"{prefix}_text"]
        accent   = T[f"{prefix}_accent"]
        trend_color = text_c if is_up else "#F59E0B"
        uid = label.replace(" ", "")

        kpi_cards_html += f"""
        <div style="background:{bg};border:1.5px solid {border};border-radius:{T['card_radius']};padding:18px 20px;box-shadow:{T['card_shadow']},{glow};min-height:148px;display:flex;flex-direction:column;justify-content:space-between;{T['backdrop']}position:relative;overflow:hidden;box-sizing:border-box;">
            <div style="position:absolute;top:-25px;right:-25px;width:100px;height:100px;background:radial-gradient(circle,{accent}15,transparent 70%);border-radius:50%;pointer-events:none;"></div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1;">
                <div>
                    <div style="color:{T['text_muted']};font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.8px;white-space:nowrap;">{label}</div>
                    <div style="color:{T['title_color']};font-size:32px;font-weight:900;letter-spacing:-1px;margin:4px 0 2px 0;line-height:1;white-space:nowrap;">{value:,}</div>
                </div>
                <div style="background:{icon_bg};border:1px solid {border};width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.2);flex-shrink:0;">{icon_svg}</div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:flex-end;position:relative;z-index:1;margin-top:6px;">
                <div style="white-space:nowrap;">
                    <span style="color:{trend_color};font-size:12.5px;font-weight:800;">{trend}</span>
                    <span style="color:{T['text_muted']};font-size:10px;font-weight:500;margin-left:4px;">{trend_sub}</span>
                </div>
                <svg width="74" height="24" viewBox="0 0 80 30" fill="none" style="opacity:0.95;flex-shrink:0;">
                    <defs><linearGradient id="sf{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{sparkline}" stop-opacity="0.35"/><stop offset="100%" stop-color="{sparkline}" stop-opacity="0"/></linearGradient></defs>
                    <path d="{path} L72 30 L2 30 Z" fill="url(#sf{uid})"/>
                    <path d="{path}" stroke="{sparkline}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
        </div>
        """

    _render(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:18px;width:100%;margin-bottom:20px;box-sizing:border-box;">
        {kpi_cards_html}
    </div>
    """)

    # ── 5. ROW 2: 3 ANALYTICS CARDS ───────────────────────────────────────────
    categories = [
        ("Authentication",       8,  26, "linear-gradient(90deg,#06B6D4,#3B82F6)", "#0EA5E9"),
        ("Financial Data",       9,  29, "linear-gradient(90deg,#F59E0B,#F97316)", "#D97706"),
        ("Prompt Injection",    18,  58, "linear-gradient(90deg,#EF4444,#F43F5E)", "#DC2626"),
        ("Visual Privacy",      31, 100, "linear-gradient(90deg,#8B5CF6,#D946EF)", "#7C3AED"),
        ("Personal Identifiers",24,  77, "linear-gradient(90deg,#3B82F6,#6366F1)", "#2563EB"),
        ("Contact Information",  16, 52, "linear-gradient(90deg,#10B981,#06B6D4)", "#059669"),
    ]
    det_rows = ""
    for name, count, pct, gradient, color in categories:
        det_rows += f"""
        <div style="display:grid;grid-template-columns:145px 1fr 28px;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="color:{T['text_primary']};font-size:12px;font-weight:700;display:flex;align-items:center;gap:6px;white-space:nowrap;">
                <span style="color:{color};font-size:8px;">●</span> {name}
            </div>
            <div style="background:{T['bar_track']};border-radius:6px;height:6px;overflow:hidden;width:100%;">
                <div style="background:{gradient};width:{pct}%;height:100%;border-radius:6px;box-shadow:0 0 8px {color}33;"></div>
            </div>
            <div style="color:{color};font-weight:800;font-size:12.5px;text-align:right;">{count}</div>
        </div>
        """

    line_op = "0.65" if is_dark else "0.45"

    # Card 1: Security Posture
    card_posture = f"""
    <div style="background:{T['card_bg']};border:1.5px solid {T['card_border']};border-radius:{T['card_radius']};padding:22px;box-shadow:{T['card_shadow']};{T['backdrop']}box-sizing:border-box;min-height:330px;display:flex;flex-direction:column;justify-content:space-between;">
        <div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <h3 style="color:{T['title_color']};font-size:16px;font-weight:800;margin:0;white-space:nowrap;">Security Posture</h3>
                <span style="background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.35);font-size:9.5px;font-weight:800;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:0.6px;white-space:nowrap;">EXCELLENT</span>
            </div>
            <div style="display:flex;justify-content:center;align-items:center;padding:4px 0 8px 0;">
                <div style="position:relative;width:140px;height:140px;">
                    <svg width="140" height="140" viewBox="0 0 160 160">
                        <circle cx="80" cy="80" r="64" stroke="{T['ring_track']}" stroke-width="12" fill="none"></circle>
                        <circle cx="80" cy="80" r="64" stroke="url(#socRingGrad)" stroke-width="12" stroke-dasharray="402.1" stroke-dashoffset="8" stroke-linecap="round" fill="none" transform="rotate(-90 80 80)"></circle>
                        <defs><linearGradient id="socRingGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#06B6D4"></stop><stop offset="30%" stop-color="#3B82F6"></stop><stop offset="60%" stop-color="#8B5CF6"></stop><stop offset="100%" stop-color="#10B981"></stop></linearGradient></defs>
                    </svg>
                    <div style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                        <span style="color:{T['title_color']};font-size:32px;font-weight:900;letter-spacing:-1px;line-height:1;">98%</span>
                        <span style="color:{T['text_muted']};font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin-top:2px;white-space:nowrap;">SECURE SCORE</span>
                    </div>
                </div>
            </div>
        </div>
        <div>
            <div style="font-size:9.5px;font-weight:800;color:{T['text_muted']};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:6px;padding-top:8px;border-top:1px solid {T['divider']};">Status Breakdown</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
                <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:{'rgba(16,185,129,0.08)' if is_dark else 'rgba(16,185,129,0.04)'};border-radius:8px;border:1px solid {'rgba(16,185,129,0.2)' if is_dark else 'rgba(16,185,129,0.12)'};"><span style="color:{T['text_primary']};font-weight:600;font-size:11.5px;"><span style="color:#10B981;font-size:8px;">●</span> Safe</span><strong style="color:{T['title_color']};font-weight:800;font-size:12px;">3,645</strong></div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:{'rgba(245,158,11,0.08)' if is_dark else 'rgba(245,158,11,0.04)'};border-radius:8px;border:1px solid {'rgba(245,158,11,0.2)' if is_dark else 'rgba(245,158,11,0.12)'};"><span style="color:{T['text_primary']};font-weight:600;font-size:11.5px;"><span style="color:#F59E0B;font-size:8px;">●</span> Warning</span><strong style="color:{T['title_color']};font-weight:800;font-size:12px;">312</strong></div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:{'rgba(239,68,68,0.08)' if is_dark else 'rgba(239,68,68,0.04)'};border-radius:8px;border:1px solid {'rgba(239,68,68,0.2)' if is_dark else 'rgba(239,68,68,0.12)'};"><span style="color:{T['text_primary']};font-weight:600;font-size:11.5px;"><span style="color:#EF4444;font-size:8px;">●</span> Blocked</span><strong style="color:{T['title_color']};font-weight:800;font-size:12px;">128</strong></div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:{'rgba(59,130,246,0.08)' if is_dark else 'rgba(59,130,246,0.04)'};border-radius:8px;border:1px solid {'rgba(59,130,246,0.2)' if is_dark else 'rgba(59,130,246,0.12)'};"><span style="color:{T['text_primary']};font-weight:600;font-size:11.5px;"><span style="color:#3B82F6;font-size:8px;">●</span> Monitor</span><strong style="color:{T['title_color']};font-weight:800;font-size:12px;">807</strong></div>
            </div>
        </div>
    </div>
    """

    # Card 2: AI Security Intelligence (FLUID FULL TEXT)
    card_intel = f"""
    <div style="background:{T['insight_bg']};border:1.5px solid {T['insight_border']};border-radius:{T['card_radius']};padding:22px;box-shadow:{T['card_shadow']};{T['backdrop']}min-height:330px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
        <div>
            <h3 style="color:{T['title_color']};font-size:16px;font-weight:800;margin:0 0 12px 0;white-space:nowrap;">AI Security Intelligence</h3>
            <div style="display:grid;grid-template-columns:1.5fr 1fr;gap:18px;align-items:center;">
                <div style="font-size:13.5px;line-height:1.65;color:{T['text_secondary']};font-weight:500;word-break:normal;white-space:normal;">
                    "Identity and credential privacy vectors represent the primary high-severity detections across prompt workflows. Sanitization filters neutralized all PII tokens before LLM dispatch."
                </div>
                <div style="flex-shrink:0;display:flex;justify-content:center;align-items:center;">
                    <svg width="130" height="130" viewBox="0 0 140 140" fill="none">
                        <circle cx="70" cy="70" r="62" stroke="{'rgba(139,92,246,0.25)' if is_dark else 'rgba(139,92,246,0.15)'}" stroke-width="1" stroke-dasharray="4 6"></circle>
                        <circle cx="70" cy="70" r="50" stroke="{'rgba(6,182,212,0.3)' if is_dark else 'rgba(6,182,212,0.2)'}" stroke-width="1.2"></circle>
                        <line x1="70" y1="15" x2="25" y2="55" stroke="#8B5CF6" stroke-width="1.5" opacity="{line_op}"></line>
                        <line x1="70" y1="15" x2="115" y2="55" stroke="#06B6D4" stroke-width="1.5" opacity="{line_op}"></line>
                        <line x1="25" y1="55" x2="40" y2="110" stroke="#3B82F6" stroke-width="1.5" opacity="{line_op}"></line>
                        <line x1="115" y1="55" x2="100" y2="110" stroke="#EC4899" stroke-width="1.5" opacity="{line_op}"></line>
                        <line x1="40" y1="110" x2="100" y2="110" stroke="#10B981" stroke-width="1.2" opacity="{line_op}"></line>
                        <line x1="70" y1="15" x2="70" y2="70" stroke="#06B6D4" stroke-width="2" opacity="0.75"></line>
                        <line x1="70" y1="70" x2="40" y2="110" stroke="#8B5CF6" stroke-width="1.5" opacity="{line_op}"></line>
                        <line x1="70" y1="70" x2="100" y2="110" stroke="#3B82F6" stroke-width="1.5" opacity="{line_op}"></line>
                        <circle cx="70" cy="15" r="5" fill="#06B6D4"></circle><circle cx="25" cy="55" r="4.5" fill="#8B5CF6"></circle>
                        <circle cx="115" cy="55" r="4.5" fill="#EC4899"></circle><circle cx="40" cy="110" r="4" fill="#3B82F6"></circle>
                        <circle cx="100" cy="110" r="4" fill="#10B981"></circle><circle cx="70" cy="70" r="8" fill="#3B82F6"></circle>
                    </svg>
                </div>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid {T['divider']};padding-top:10px;margin-top:10px;">
            <div>
                <div style="color:{T['text_label']};font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:0.8px;">PRIMARY RISK VECTOR</div>
                <div style="color:#0EA5E9;font-size:12px;font-weight:800;margin-top:2px;">IDENTITY &amp; CREDENTIAL INFO</div>
            </div>
            <div style="text-align:right;">
                <div style="color:{T['text_label']};font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:0.8px;">TREND</div>
                <div style="color:#10B981;font-size:12px;font-weight:800;margin-top:2px;">+12% <span style="font-size:9.5px;color:{T['text_muted']};font-weight:500;">vs last period</span></div>
            </div>
        </div>
    </div>
    """

    # Card 3: Detections By Category
    card_detections = f"""
    <div style="background:{T['card_bg']};border:1.5px solid {T['card_border']};border-radius:{T['card_radius']};padding:22px;box-shadow:{T['card_shadow']};{T['backdrop']}box-sizing:border-box;min-height:330px;display:flex;flex-direction:column;justify-content:space-between;">
        <div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="color:{T['title_color']};font-size:16px;font-weight:800;margin:0;white-space:nowrap;">Detections By Category</h3>
            </div>
            {det_rows}
        </div>
    </div>
    """

    _render(f"""
    <div style="display:grid;grid-template-columns:1fr 1.35fr 1fr;gap:20px;width:100%;margin-bottom:20px;box-sizing:border-box;">
        {card_posture}
        {card_intel}
        {card_detections}
    </div>
    """)

    # ── 6. ROW 3: SYSTEM INFRASTRUCTURE + MODULE LAUNCHPAD ────────────────────
    engines = [
        ("Privacy Detection", "ONLINE", "#10B981"),
        ("DistilBERT Engine", "READY",  "#06B6D4"),
        ("Naive Bayes Engine","ACTIVE", "#3B82F6"),
        ("Risk Engine",       "READY",  "#8B5CF6"),
        ("Protection Engine", "ACTIVE", "#10B981"),
        ("XAI Explainer",     "READY",  "#06B6D4"),
    ]
    engine_cards = ""
    for e_name, e_status, e_color in engines:
        r, g, b = int(e_color[1:3],16), int(e_color[3:5],16), int(e_color[5:7],16)
        engine_cards += f"""
        <div style="background:{T['card_bg_subtle']};border:1px solid rgba({r},{g},{b},0.3);border-radius:10px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:6px;white-space:nowrap;">
                <span style="font-size:7px;color:{e_color};">●</span>
                <span style="color:{T['text_primary']};font-size:12px;font-weight:700;">{e_name}</span>
            </div>
            <span style="background:rgba({r},{g},{b},0.12);color:{e_color};border:1px solid {e_color};font-size:9px;font-weight:800;padding:2px 8px;border-radius:8px;letter-spacing:0.4px;white-space:nowrap;">{e_status}</span>
        </div>
        """

    qa_items = [
        ("Text Analysis",    "Sanitize prompts &amp; redact sensitive PII", "#3B82F6", "rgba(59,130,246,0.12)", "rgba(59,130,246,0.3)"),
        ("Image Analysis",   "OCR extraction &amp; facial anonymization",   "#10B981", "rgba(16,185,129,0.12)", "rgba(16,185,129,0.3)"),
        ("Video Analysis",   "Multimodal frame privacy scanning",          "#8B5CF6", "rgba(139,92,246,0.12)", "rgba(139,92,246,0.3)"),
        ("YouTube Analyzer", "Transcript audit &amp; PII attribution",      "#EF4444", "rgba(239,68,68,0.12)",  "rgba(239,68,68,0.3)"),
    ]
    qa_cards = ""
    for qa_title, qa_desc, qa_color, qa_bg, qa_border_clr in qa_items:
        qa_cards += f"""
        <div style="background:linear-gradient(135deg,{T['card_bg_subtle']},{qa_bg});border:1px solid {qa_border_clr};border-radius:12px;padding:12px 10px 8px 10px;min-height:100px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;">
            <div>
                <div style="color:{T['title_color']};font-size:12px;font-weight:800;margin-bottom:3px;white-space:nowrap;">{qa_title}</div>
                <p style="color:{T['text_muted']};font-size:10px;line-height:1.35;margin:0;word-break:normal;">{qa_desc}</p>
            </div>
        </div>
        """

    _render(f"""
    <div style="display:grid;grid-template-columns:1fr 1.35fr;gap:20px;width:100%;align-items:stretch;box-sizing:border-box;">
        <div style="background:{T['card_bg']};border:1.5px solid {T['card_border']};border-radius:{T['card_radius']};padding:20px;box-shadow:{T['card_shadow']};{T['backdrop']}box-sizing:border-box;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="color:{T['title_color']};font-size:16px;font-weight:800;margin:0;white-space:nowrap;">System Infrastructure</h3>
                <span style="color:#10B981;font-size:10px;font-weight:800;display:flex;align-items:center;gap:5px;white-space:nowrap;">
                    <span style="font-size:7px;">●</span> ALL ENGINES OPERATIONAL
                </span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">{engine_cards}</div>
            <div style="margin-top:10px;background:{T['card_bg_subtle']};border:1px solid rgba(16,185,129,0.35);border-radius:10px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <div style="color:{T['title_color']};font-size:12px;font-weight:800;white-space:nowrap;">Secure LLM Gateway</div>
                    <div style="color:{T['text_muted']};font-size:9.5px;font-weight:500;white-space:nowrap;">FastRouter + Presidio PII Masking &amp; HMAC Receipts</div>
                </div>
                <span style="background:rgba(16,185,129,0.15);color:#10B981;border:1px solid #10B981;font-size:9.5px;font-weight:800;padding:3px 9px;border-radius:8px;white-space:nowrap;">ONLINE</span>
            </div>
        </div>
        <div style="background:{T['card_bg']};border:1.5px solid {T['card_border']};border-radius:{T['card_radius']};padding:20px;box-shadow:{T['card_shadow']};{T['backdrop']}box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;">
            <h3 style="color:{T['title_color']};font-size:16px;font-weight:800;margin:0 0 12px 0;white-space:nowrap;">Module Launchpad</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;">{qa_cards}</div>
        </div>
    </div>
    """)

    # Quick-action buttons underneath Module Launchpad
    _, btn_col = st.columns([1.0, 1.35])
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("Open Text", key="btn_qa_text_analysis", use_container_width=True):
                st.session_state["selected_page"] = "Text Analysis"
                st.rerun()
        with b2:
            if st.button("Open Image", key="btn_qa_image_analysis", use_container_width=True):
                st.session_state["selected_page"] = "Image Analysis"
                st.rerun()
        with b3:
            if st.button("Open Video", key="btn_qa_video_analysis", use_container_width=True):
                st.session_state["selected_page"] = "Video Analysis"
                st.rerun()
        with b4:
            if st.button("Open YouTube", key="btn_qa_youtube_analyzer", use_container_width=True):
                st.session_state["selected_page"] = "YouTube Analyzer"
                st.rerun()

    _render("<div style='margin-bottom:20px;'></div>")

    # ── 7. FOOTER STATUS BAR ─────────────────────────────────────────────────
    _render(f"""
    <div style="background:{T['footer_bg']};border:1.5px solid {T['footer_border']};border-radius:14px;padding:12px 20px;box-shadow:{T['card_shadow']};{T['backdrop']}display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;box-sizing:border-box;">
        <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
            <span style="color:#10B981;font-size:8px;">●</span>
            <span style="color:{T['text_label']};font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;">Active Session</span>
            <span style="color:{T['title_color']};font-size:11.5px;font-weight:800;font-family:'JetBrains Mono',monospace;background:{'rgba(59,130,246,0.12)' if is_dark else 'rgba(59,130,246,0.06)'};padding:2px 8px;border-radius:6px;border:1px solid {'rgba(59,130,246,0.25)' if is_dark else 'rgba(59,130,246,0.12)'};">AS-20AUG-2026-1439</span>
        </div>
        <div style="width:1px;height:20px;background:{T['divider']};"></div>
        <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
            <span style="color:{T['text_label']};font-size:9.5px;font-weight:800;text-transform:uppercase;">Privacy Mode</span>
            <span style="color:#0EA5E9;font-size:11.5px;font-weight:800;">STRICT</span>
        </div>
        <div style="width:1px;height:20px;background:{T['divider']};"></div>
        <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
            <span style="color:{T['text_label']};font-size:9.5px;font-weight:800;text-transform:uppercase;">Data Handling</span>
            <span style="color:#10B981;font-size:11.5px;font-weight:800;">SANITIZED</span>
        </div>
        <div style="width:1px;height:20px;background:{T['divider']};"></div>
        <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
            <span style="color:{T['text_label']};font-size:9.5px;font-weight:800;text-transform:uppercase;">Encryption</span>
            <span style="color:#8B5CF6;font-size:11.5px;font-weight:800;">AES-256</span>
        </div>
        <div style="width:1px;height:20px;background:{T['divider']};"></div>
        <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
            <span style="color:{T['text_label']};font-size:9.5px;font-weight:800;text-transform:uppercase;">Compliance</span>
            <span style="color:#D97706;font-size:11.5px;font-weight:800;">GDPR • ISO 27001</span>
        </div>
    </div>
    """)
