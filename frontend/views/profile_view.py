"""
AI Trust Chat — Profile & Role Management View.
Demonstrates RBAC with session-based role switching.
File: frontend/views/profile_view.py
"""

import streamlit as st
import datetime
from backend.services.rag_engine import ROLE_ACCESS

ROLE_DESCRIPTIONS = {
    "USER": {
        "label": "Standard User",
        "color": "#06B6D4",
        "bg": "rgba(6,182,212,0.12)",
        "permissions": [
            "✅ Chat with AI Trust Chat",
            "✅ Upload and query PUBLIC/INTERNAL documents",
            "✅ View own Trust Receipts",
            "❌ Cannot access CONFIDENTIAL/RESTRICTED documents",
            "❌ Cannot modify policies",
            "❌ Cannot view all security events",
        ],
    },
    "MANAGER": {
        "label": "Manager",
        "color": "#A78BFA",
        "bg": "rgba(167,139,250,0.12)",
        "permissions": [
            "✅ Chat with AI Trust Chat",
            "✅ Upload and query PUBLIC/INTERNAL/CONFIDENTIAL documents",
            "✅ View team Trust Receipts",
            "✅ View security dashboard",
            "❌ Cannot access RESTRICTED documents",
            "❌ Cannot modify policies",
        ],
    },
    "AUDITOR": {
        "label": "Security Auditor",
        "color": "#F59E0B",
        "bg": "rgba(245,158,11,0.12)",
        "permissions": [
            "✅ Chat with AI Trust Chat",
            "✅ Access PUBLIC/INTERNAL/CONFIDENTIAL documents",
            "✅ View ALL Trust Receipts",
            "✅ View ALL security events",
            "✅ Export audit data",
            "❌ Cannot modify policies",
            "❌ Cannot access RESTRICTED documents",
        ],
    },
    "ADMIN": {
        "label": "Administrator",
        "color": "#10B981",
        "bg": "rgba(16,185,129,0.12)",
        "permissions": [
            "✅ Full access to all features",
            "✅ Access ALL document classifications (including RESTRICTED)",
            "✅ Create, edit, delete policies",
            "✅ View ALL security events and receipts",
            "✅ Export all data",
            "✅ Reset system settings",
        ],
    },
    "SECURITY_ADMIN": {
        "label": "Security Administrator",
        "color": "#EF4444",
        "bg": "rgba(239,68,68,0.12)",
        "permissions": [
            "✅ Full security management access",
            "✅ Manage all policies and rules",
            "✅ Access all document classifications",
            "✅ View all audit data",
            "✅ Override security decisions",
        ],
    },
}

DEMO_USERS = [
    ("Employee-001", "USER", "Standard user — general AI assistant access"),
    ("Employee-247", "MANAGER", "Manager — can access confidential documents"),
    ("Auditor-012", "AUDITOR", "Auditor — full visibility into security events"),
    ("Admin-001", "ADMIN", "Administrator — full system access"),
    ("SecAdmin-001", "SECURITY_ADMIN", "Security Admin — full policy control"),
]


def render_profile_view() -> None:
    current_role = st.session_state.get("user_role", "USER")
    current_user = st.session_state.get("user_id", "Employee-001")

    st.markdown(
        "<h1 style='margin-bottom:4px;'>👤 Profile & Role Management</h1>"
        "<p style='color:#94A3B8; font-size:14px; margin-top:0;'>"
        "Manage your identity and role. Role-based access control governs all AI Trust Chat features.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Current user card ──────────────────────────────────────────────────────
    role_info = ROLE_DESCRIPTIONS.get(current_role, ROLE_DESCRIPTIONS["USER"])
    role_color = role_info["color"]
    role_bg = role_info["bg"]

    st.markdown(
        f"<div style='background:rgba(11,39,66,0.6); border:1px solid rgba(59,130,246,0.2); "
        f"border-radius:16px; padding:24px; margin-bottom:24px;'>"
        f"<div style='display:flex; align-items:center; gap:16px;'>"
        f"<div style='width:64px; height:64px; border-radius:50%; background:rgba(59,130,246,0.2); "
        f"border:2px solid rgba(59,130,246,0.4); display:flex; align-items:center; justify-content:center; "
        f"font-size:28px;'>👤</div>"
        f"<div>"
        f"<h3 style='color:#E2E8F0; margin:0; font-size:20px;'>{current_user}</h3>"
        f"<span style='background:{role_bg}; border:1px solid {role_color}44; color:{role_color}; "
        f"font-size:12px; font-weight:700; padding:3px 12px; border-radius:20px; display:inline-block; margin-top:6px;'>"
        f"{current_role} — {role_info['label']}</span>"
        f"</div></div>"
        f"<div style='margin-top:16px; font-size:13px; color:#64748B;'>"
        f"Session started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Permissions list ───────────────────────────────────────────────────────
    col_perms, col_access = st.columns([1, 1])

    with col_perms:
        st.subheader("Your Permissions")
        for perm in role_info["permissions"]:
            color = "#10B981" if perm.startswith("✅") else "#EF4444"
            st.markdown(f"<div style='color:{color}; font-size:13px; margin-bottom:4px;'>{perm}</div>", unsafe_allow_html=True)

    with col_access:
        st.subheader("Document Access")
        from backend.services.rag_engine import ROLE_ACCESS
        accessible = ROLE_ACCESS.get(current_role.upper(), ["PUBLIC"])
        all_levels = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
        cls_colors = {
            "PUBLIC": "#10B981", "INTERNAL": "#06B6D4",
            "CONFIDENTIAL": "#F59E0B", "RESTRICTED": "#EF4444",
        }
        for lvl in all_levels:
            has_access = lvl in accessible
            color = cls_colors[lvl]
            icon = "✅" if has_access else "🔒"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:8px; margin-bottom:6px;'>"
                f"<span style='background:{color}11; border:1px solid {color}33; color:{color}; "
                f"font-size:11px; font-weight:700; padding:2px 10px; border-radius:12px; min-width:110px; "
                f"text-align:center;'>{lvl}</span>"
                f"<span style='font-size:13px;'>{icon} {'Accessible' if has_access else 'Restricted'}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Role Switcher (Demo) ───────────────────────────────────────────────────
    st.subheader("🎭 Switch Demo Profile")
    st.markdown(
        "<p style='color:#94A3B8; font-size:13px;'>Switch between user profiles to demonstrate "
        "role-based access control. In production, roles are assigned by administrators.</p>",
        unsafe_allow_html=True,
    )

    for user_id, role, description in DEMO_USERS:
        ri = ROLE_DESCRIPTIONS.get(role, ROLE_DESCRIPTIONS["USER"])
        is_current = (user_id == current_user)

        col_u, col_d, col_btn = st.columns([2, 3, 1.5])
        with col_u:
            st.markdown(
                f"<div style='padding-top:8px;'>"
                f"<strong style='color:#E2E8F0; font-size:14px;'>{user_id}</strong><br>"
                f"<span style='background:{ri['bg']}; border:1px solid {ri['color']}44; color:{ri['color']}; "
                f"font-size:10px; font-weight:700; padding:2px 8px; border-radius:12px;'>{role}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_d:
            st.markdown(f"<div style='padding-top:12px; color:#94A3B8; font-size:13px;'>{description}</div>", unsafe_allow_html=True)
        with col_btn:
            if is_current:
                st.markdown("<div style='padding-top:8px; color:#10B981; font-size:12px; font-weight:700;'>● Active</div>", unsafe_allow_html=True)
            else:
                if st.button(f"Switch", key=f"switch_{user_id}", use_container_width=True):
                    st.session_state["user_id"] = user_id
                    st.session_state["user_role"] = role
                    st.success(f"Switched to {user_id} ({role})")
                    st.rerun()

        st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin:4px 0;'>", unsafe_allow_html=True)
