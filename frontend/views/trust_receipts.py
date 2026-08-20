"""
AI Trust Chat — Trust Receipts View.
File: frontend/views/trust_receipts.py
"""

import streamlit as st
from backend.services.trust_receipt import get_all_receipts, format_receipt_text

RISK_COLORS = {
    "LOW":      "#10B981",
    "MEDIUM":   "#F59E0B",
    "HIGH":     "#EF4444",
    "CRITICAL": "#DC2626",
}

ACTION_COLORS = {
    "ALLOW":    "#10B981",
    "MASK":     "#06B6D4",
    "REDACT":   "#F59E0B",
    "BLOCK":    "#EF4444",
    "DENY":     "#DC2626",
}


def render_trust_receipts_view() -> None:
    st.markdown(
        "<h1 style='margin-bottom:4px;'>🧾 AI Trust Receipts</h1>"
        "<p style='color:#94A3B8; font-size:14px; margin-top:0;'>"
        "Privacy-preserving security audit trail for every AI request. "
        "Raw prompts are <strong style='color:#10B981;'>never stored</strong>.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    receipts = get_all_receipts()

    if not receipts:
        st.info("No Trust Receipts generated yet. Start chatting and receipts will appear here automatically.")
        return

    # ── Summary strip ──────────────────────────────────────────────────────────
    total = len(receipts)
    pii_count = sum(1 for r in receipts if r["security"]["pii_detected"])
    inj_count = sum(1 for r in receipts if r["security"]["prompt_injection"])
    blocked = sum(1 for r in receipts if r["policy"]["overall_action"] in ("BLOCK", "DENY"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Receipts", total)
    c2.metric("PII Events", pii_count)
    c3.metric("Injection Attempts", inj_count)
    c4.metric("Blocked Requests", blocked)

    st.markdown(
        "<div style='background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); "
        "border-radius:10px; padding:10px 16px; margin:12px 0;'>"
        "<strong style='color:#10B981;'>🔒 Privacy Guarantee</strong> — "
        "<span style='color:#94A3B8; font-size:13px;'>No raw prompt text is ever stored in these receipts. "
        "Only security metadata (PII type, risk category, action taken) is logged.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Receipt cards ──────────────────────────────────────────────────────────
    for receipt in receipts:
        sec = receipt["security"]
        pol = receipt["policy"]
        out = receipt["output"]
        risk_level = sec["risk_level"]
        risk_color = RISK_COLORS.get(risk_level, "#94A3B8")
        action_color = ACTION_COLORS.get(pol["overall_action"], "#94A3B8")

        with st.container():
            col_info, col_badges, col_expand = st.columns([3, 2, 1])

            with col_info:
                st.markdown(
                    f"<div style='padding:4px 0;'>"
                    f"<code style='color:#06B6D4; font-size:12px;'>{receipt['receipt_id']}</code> "
                    f"<span style='color:#64748B; font-size:12px;'>· {receipt['timestamp']}</span><br>"
                    f"<span style='color:#94A3B8; font-size:13px;'>"
                    f"👤 {receipt['user']} · 🤖 {receipt['model']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_badges:
                pii_txt = "PII ✓" if sec["pii_detected"] else "PII ✗"
                inj_txt = "INJECTION ✓" if sec["prompt_injection"] else "INJECTION ✗"
                pii_color = "#F59E0B" if sec["pii_detected"] else "#10B981"
                inj_color = "#EF4444" if sec["prompt_injection"] else "#10B981"
                st.markdown(
                    f"<div style='display:flex; gap:6px; flex-wrap:wrap; padding-top:4px;'>"
                    f"<span style='border:1px solid {risk_color}44; color:{risk_color}; background:{risk_color}11; "
                    f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{risk_level} {sec['risk_score']}/100</span>"
                    f"<span style='border:1px solid {pii_color}44; color:{pii_color}; background:{pii_color}11; "
                    f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{pii_txt}</span>"
                    f"<span style='border:1px solid {inj_color}44; color:{inj_color}; background:{inj_color}11; "
                    f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{inj_txt}</span>"
                    f"<span style='border:1px solid {action_color}44; color:{action_color}; background:{action_color}11; "
                    f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{pol['overall_action']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_expand:
                if st.button("🧾 View", key=f"view_receipt_{receipt['receipt_id']}"):
                    st.session_state[f"expand_receipt_{receipt['receipt_id']}"] = \
                        not st.session_state.get(f"expand_receipt_{receipt['receipt_id']}", False)

        if st.session_state.get(f"expand_receipt_{receipt['receipt_id']}"):
            st.code(format_receipt_text(receipt), language="text")

        st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin:4px 0;'>", unsafe_allow_html=True)
