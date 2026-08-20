"""
AI Trust Chat — Policy Engine View.
File: frontend/views/policy_engine_view.py
"""

import streamlit as st
from backend.services.policy_engine import (
    get_all_policies, create_policy, delete_policy,
    toggle_policy, reset_to_defaults,
)

ACTION_COLORS = {
    "ALLOW":  ("#10B981", "rgba(16,185,129,0.12)"),
    "WARN":   ("#F97316", "rgba(249,115,22,0.12)"),
    "MASK":   ("#06B6D4", "rgba(6,182,212,0.12)"),
    "REDACT": ("#F59E0B", "rgba(245,158,11,0.12)"),
    "BLOCK":  ("#EF4444", "rgba(239,68,68,0.12)"),
    "DENY":   ("#DC2626", "rgba(220,38,38,0.12)"),
}


def render_policy_engine_view() -> None:
    user_role = st.session_state.get("user_role", "USER")

    st.markdown(
        "<h1 style='margin-bottom:4px;'>⚖️ Policy Engine</h1>"
        "<p style='color:#94A3B8; font-size:14px; margin-top:0;'>"
        "Configure security rules that govern how AI Trust Chat handles sensitive content.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    if user_role not in ("ADMIN", "SECURITY_ADMIN"):
        st.warning("⚠️ You have read-only access to policies. ADMIN or SECURITY_ADMIN role required to make changes.")

    # ── Policy Flow Diagram ────────────────────────────────────────────────────
    with st.expander("📊 Policy Evaluation Flow", expanded=False):
        st.code("""
USER PROMPT
    ↓
┌─────────────────────────────────────────────┐
│           POLICY ENGINE                     │
│                                             │
│  Rule 1: PII detected?         → MASK       │
│  Rule 2: Secret/API key?       → BLOCK      │
│  Rule 3: Injection conf >80%?  → BLOCK      │
│  Rule 4: Sensitive output?     → REDACT     │
│  Rule 5: RESTRICTED doc?       → DENY       │
│  Rule 6: Medium risk (30-59)?  → WARN       │
│                                             │
│  → Most restrictive action wins             │
└─────────────────────────────────────────────┘
    ↓
FINAL ACTION: ALLOW / WARN / MASK / REDACT / BLOCK / DENY
""", language="text")

    # ── Policy List ────────────────────────────────────────────────────────────
    policies = get_all_policies()
    st.subheader(f"Active Rules ({len(policies)} total)")

    for policy in policies:
        action = policy["action"]
        action_color, action_bg = ACTION_COLORS.get(action, ("#94A3B8", "rgba(148,163,184,0.12)"))
        is_enabled = policy.get("enabled", True)
        enabled_color = "#10B981" if is_enabled else "#64748B"
        enabled_text = "ENABLED" if is_enabled else "DISABLED"

        with st.container():
            col_info, col_action, col_status, col_btns = st.columns([4, 1.5, 1.5, 2])

            with col_info:
                opacity = "1.0" if is_enabled else "0.5"
                st.markdown(
                    f"<div style='opacity:{opacity};'>"
                    f"<strong style='color:#E2E8F0; font-size:14px;'>{policy['name']}</strong><br>"
                    f"<span style='color:#64748B; font-size:12px;'>{policy['condition_detail']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_action:
                st.markdown(
                    f"<div style='padding-top:6px;'>"
                    f"<span style='background:{action_bg}; border:1px solid {action_color}44; color:{action_color}; "
                    f"font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px;'>{action}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_status:
                st.markdown(
                    f"<div style='padding-top:6px;'>"
                    f"<span style='color:{enabled_color}; font-size:11px; font-weight:700;'>"
                    f"{'●' if is_enabled else '○'} {enabled_text}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_btns:
                if user_role in ("ADMIN", "SECURITY_ADMIN"):
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        toggle_label = "Disable" if is_enabled else "Enable"
                        if st.button(toggle_label, key=f"toggle_policy_{policy['id']}", use_container_width=True):
                            toggle_policy(policy["id"])
                            st.rerun()
                    with btn_col2:
                        if not policy["id"].startswith("policy_00"):  # Protect defaults
                            if st.button("Delete", key=f"del_policy_{policy['id']}", use_container_width=True):
                                delete_policy(policy["id"])
                                st.success(f"Policy '{policy['name']}' deleted.")
                                st.rerun()
                        else:
                            st.markdown("<span style='color:#64748B; font-size:11px;'>Default</span>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin:4px 0;'>", unsafe_allow_html=True)

    # ── Create New Policy ──────────────────────────────────────────────────────
    if user_role in ("ADMIN", "SECURITY_ADMIN"):
        st.divider()
        st.subheader("➕ Create New Policy")

        with st.form("create_policy_form"):
            p_name = st.text_input("Policy Name", placeholder="e.g., Block Name + Phone Combo")
            col_cond, col_action = st.columns(2)
            with col_cond:
                p_condition = st.selectbox("Condition", [
                    "pii_detected", "secret_detected", "injection_confidence_gt_80",
                    "sensitive_output_detected", "doc_classification_restricted",
                    "risk_score_30_to_59",
                ])
            with col_action:
                p_action = st.selectbox("Action", ["ALLOW", "WARN", "MASK", "REDACT", "BLOCK", "DENY"])

            p_detail = st.text_input("Condition Description", placeholder="Describe when this rule triggers")
            p_priority = st.number_input("Priority (lower = higher priority)", min_value=1, max_value=99, value=50)
            p_enabled = st.checkbox("Enable immediately", value=True)

            if st.form_submit_button("Create Policy", type="primary"):
                if p_name and p_detail:
                    create_policy(
                        name=p_name, condition=p_condition,
                        condition_detail=p_detail, action=p_action,
                        enabled=p_enabled, priority=int(p_priority),
                    )
                    st.success(f"✅ Policy '{p_name}' created.")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")

        st.divider()
        if st.button("🔄 Reset to Default Policies", type="secondary", key="reset_policies"):
            reset_to_defaults()
            st.success("Policies reset to defaults.")
            st.rerun()
