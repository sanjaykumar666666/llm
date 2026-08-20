"""
Live Explainable Privacy Detection UI Component.
Renders real-time privacy analysis, exact visual span highlighting, bulleted WHY reasons,
and action recommendations directly below the message composer.
File: frontend/components/live_privacy_detector.py
"""

import streamlit as st
from typing import Dict, Any, Optional

STATUS_THEMES = {
    "ALLOW": {
        "border": "#10B981",
        "bg": "rgba(16,185,129,0.08)",
        "badge_bg": "#10B981",
        "badge_color": "#064E3B",
        "title_color": "#34D399",
        "banner": "🟢 NO PRIVACY RISK",
        "action_icon": "✓",
    },
    "WARN": {
        "border": "#F59E0B",
        "bg": "rgba(245,158,11,0.08)",
        "badge_bg": "#F59E0B",
        "badge_color": "#78350F",
        "title_color": "#FBBF24",
        "banner": "🟡 PRIVACY RISK DETECTED",
        "action_icon": "🛡️",
    },
    "BLOCK": {
        "border": "#EF4444",
        "bg": "rgba(239,68,68,0.10)",
        "badge_bg": "#EF4444",
        "badge_color": "#450A0A",
        "title_color": "#F87171",
        "banner": "🔴 PRIVACY RISK DETECTED",
        "action_icon": "🚫",
    },
}


def render_live_privacy_detector_panel(analysis: Optional[Dict[str, Any]], prompt_text: str = "") -> None:
    """
    Renders compact, real-time explainable privacy analysis directly below the chat composer.
    """
    if not prompt_text or not prompt_text.strip():
        # Clean neutral placeholder
        st.markdown(
            "<div style='background:rgba(255,255,255,0.02); border:1px dashed rgba(255,255,255,0.12); "
            "border-radius:10px; padding:10px 14px; font-size:12px; color:#64748B; margin-top:6px;'>"
            "🛡️ <em>Live Privacy Firewall Active: Type your message to see real-time privacy & risk analysis.</em>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    if not analysis:
        return

    decision = analysis.get("decision", "ALLOW")
    theme = STATUS_THEMES.get(decision, STATUS_THEMES["ALLOW"])
    score = analysis.get("risk_score", 0)
    risk_level = analysis.get("risk_level", "LOW")
    status_banner = analysis.get("status_banner", theme["banner"])
    action_label = analysis.get("action_label", "✓ SAFE TO SEND")
    why_bullets = analysis.get("why_bullets", [])
    where_items = analysis.get("where_items", [])
    highlighted_html = analysis.get("highlighted_html", "")
    bert_pred = analysis.get("bert_prediction", "SAFE")
    bert_conf = analysis.get("bert_confidence", 1.0)
    nb_pred = analysis.get("nb_prediction", "SAFE")
    nb_conf = analysis.get("nb_confidence", 1.0)

    # Main Card Container
    card_html = (
        f"<div style='background:{theme['bg']}; border:1px solid {theme['border']}55; "
        f"border-left:4px solid {theme['border']}; border-radius:10px; padding:14px 16px; margin-top:8px;'>"
    )

    # 1. Header Bar: Status Banner + Risk Score Metric + ML Badges
    header_html = (
        f"<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;'>"
        f"<div>"
        f"<strong style='color:{theme['title_color']}; font-size:14px; letter-spacing:0.02em;'>{status_banner}</strong><br>"
        f"<span style='font-size:12px; color:#CBD5E1;'>Risk Score: <strong style='color:{theme['title_color']};'>{score}%</strong> ({risk_level} RISK)</span>"
        f"</div>"
        f"<div style='display:flex; gap:6px; font-size:11px;'>"
        f"<span style='background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:3px 8px; border-radius:6px; color:#94A3B8;'>"
        f"BERT: <strong style='color:{'#34D399' if bert_pred == 'SAFE' else '#F87171'};'>{bert_pred}</strong> ({bert_conf*100:.0f}%)"
        f"</span>"
        f"<span style='background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:3px 8px; border-radius:6px; color:#94A3B8;'>"
        f"NB: <strong style='color:{'#34D399' if nb_pred == 'SAFE' else '#F87171'};'>{nb_pred}</strong> ({nb_conf*100:.0f}%)"
        f"</span>"
        f"</div>"
        f"</div>"
    )

    # 2. WHERE IS THE RISK (Visual Highlighting & Exact Spans)
    where_html = ""
    if where_items:
        where_html += "<div style='margin-bottom:10px;'>"
        where_html += "<div style='font-size:11px; font-weight:700; color:#94A3B8; text-transform:uppercase; margin-bottom:4px;'>WHERE IS THE RISK?</div>"
        where_html += f"<div style='margin-bottom:6px;'>{highlighted_html}</div>"
        for w in where_items:
            where_html += (
                f"<div style='font-size:12px; color:#CBD5E1; margin-left:4px; margin-bottom:2px;'>"
                f"• <strong style='color:{theme['title_color']};'>Where:</strong> <code>{w['exact_value']}</code> &nbsp; "
                f"<span style='color:#94A3B8;'>| Type: <strong>{w['category']}</strong> (severity: {w['severity']})</span>"
                f"</div>"
            )
        where_html += "</div>"

    # 3. WHY IS IT RISKY (Bulleted Rationale)
    why_html = "<div style='margin-bottom:10px;'>"
    why_html += "<div style='font-size:11px; font-weight:700; color:#94A3B8; text-transform:uppercase; margin-bottom:4px;'>WHY:</div>"
    for b in why_bullets:
        bullet_color = "#34D399" if b.startswith("✓") else ("#F87171" if decision == "BLOCK" else "#FBBF24")
        why_html += f"<div style='font-size:12px; color:{bullet_color}; margin-left:4px; margin-bottom:2px;'>{b}</div>"
    why_html += "</div>"

    # 4. ACTION (Recommended System Action)
    action_box_html = (
        f"<div style='background:rgba(0,0,0,0.25); border:1px solid {theme['border']}44; border-radius:6px; padding:6px 12px; font-size:12px; display:inline-block;'>"
        f"<span style='color:#94A3B8; font-weight:700;'>ACTION: </span>"
        f"<strong style='color:{theme['title_color']};'>{action_label}</strong>"
        f"</div>"
    )

    card_html += header_html + where_html + why_html + action_box_html + "</div>"
    st.markdown(card_html, unsafe_allow_html=True)
