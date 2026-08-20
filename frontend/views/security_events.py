"""
AI Trust Chat — Security Event Timeline View.
File: frontend/views/security_events.py
"""

import streamlit as st
import pandas as pd
from backend.services.security_events import (
    get_all_events, get_event_summary, get_event_color, get_event_icon,
)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def render_security_events_view() -> None:
    st.markdown(
        "<h1 style='margin-bottom:4px;'>🕒 Security Event Timeline</h1>"
        "<p style='color:#94A3B8; font-size:14px; margin-top:0;'>"
        "Real-time log of all security decisions made by the AI Trust Security Gateway.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Summary metrics ────────────────────────────────────────────────────────
    summary = get_event_summary()
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Events", summary["total_events"])
    with m2:
        st.metric("🚨 Critical", summary["by_severity"].get("CRITICAL", 0))
    with m3:
        st.metric("🔴 High", summary["by_severity"].get("HIGH", 0))
    with m4:
        st.metric("🚫 Blocked", summary["blocked"])
    with m5:
        st.metric("✅ Allowed", summary["by_action"].get("ALLOW", 0))

    st.divider()

    # ── Filters ────────────────────────────────────────────────────────────────
    col_search, col_type, col_sev, col_export = st.columns([3, 2, 2, 1])

    with col_search:
        search = st.text_input("🔍 Search events...", placeholder="Search by message or user", key="event_search")
    with col_type:
        event_types = ["ALL", "PII_DETECTED", "INJECTION_BLOCKED", "DOC_ACCESS_DENIED",
                       "SAFE_REQUEST", "OUTPUT_REDACTED", "SECRET_BLOCKED", "POLICY_TRIGGERED"]
        filter_type = st.selectbox("Event Type", event_types, key="event_type_filter")
    with col_sev:
        filter_severity = st.selectbox("Severity", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"], key="event_sev_filter")
    with col_export:
        st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
        export_btn = st.button("📥 Export", key="export_events")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Event timeline ─────────────────────────────────────────────────────────
    events = get_all_events(
        filter_type=filter_type if filter_type != "ALL" else None,
        filter_severity=filter_severity if filter_severity != "ALL" else None,
        search=search or None,
        limit=100,
    )

    if not events:
        st.info("No security events match your filters. Events will appear here as you use AI Trust Chat.")
        return

    st.markdown(f"<p style='color:#94A3B8; font-size:13px;'>Showing {len(events)} events</p>", unsafe_allow_html=True)

    for event in events:
        severity = event.get("severity", "LOW")
        color = get_event_color(severity)
        icon = get_event_icon(event.get("type", ""))
        action = event.get("action_taken", "ALLOW")
        risk = event.get("risk_score", 0)

        action_colors = {
            "ALLOW": "#10B981", "MASK": "#06B6D4", "REDACT": "#F59E0B",
            "BLOCK": "#EF4444", "DENY": "#DC2626", "WARN": "#F97316",
        }
        action_color = action_colors.get(action, "#94A3B8")

        st.markdown(
            f"<div style='background:rgba(11,39,66,0.5); border-left:4px solid {color}; "
            f"border-radius:0 10px 10px 0; padding:12px 16px; margin-bottom:8px; "
            f"display:flex; justify-content:space-between; align-items:start;'>"
            f"<div style='flex:1;'>"
            f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:4px;'>"
            f"<span style='font-size:18px;'>{icon}</span>"
            f"<strong style='color:#E2E8F0; font-size:14px;'>{event.get('message', '')}</strong>"
            f"</div>"
            f"<span style='font-size:11px; color:#64748B;'>"
            f"🕐 {event.get('timestamp')} · 👤 {event.get('user')} · 🤖 {event.get('model')}"
            f"</span>"
            f"</div>"
            f"<div style='display:flex; flex-direction:column; align-items:flex-end; gap:4px; margin-left:16px;'>"
            f"<span style='background:rgba(255,255,255,0.05); border:1px solid {color}33; color:{color}; "
            f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{severity}</span>"
            f"<span style='background:rgba(255,255,255,0.05); border:1px solid {action_color}33; color:{action_color}; "
            f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{action}</span>"
            f"<span style='font-size:10px; color:#64748B;'>Risk: {risk}/100</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    # ── Export CSV ─────────────────────────────────────────────────────────────
    if export_btn and events:
        df = pd.DataFrame(events)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Events CSV",
            data=csv,
            file_name="ai_trust_chat_security_events.csv",
            mime="text/csv",
            key="download_events_csv",
        )
