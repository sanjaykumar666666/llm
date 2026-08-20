"""
Aiera AI — Dedicated Trust Center View.
File: frontend/views/trust_center.py
"""

import streamlit as st


def render_trust_center_view() -> None:
    st.markdown(
        """
        <div style="padding: 10px 0 18px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="color:#0F172A; font-size:28px; font-weight:900; margin:0 0 6px 0;">
                        🛡️ AI Trust & Security Center
                    </h1>
                    <p style="color:#475569; font-size:14px; font-weight:500; margin:0;">
                        Enterprise-grade zero-trust privacy gateway, neural explainability, and compliance auditing.
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.35); font-size:12px; font-weight:800; padding:6px 14px; border-radius:20px;">
                        ● System Protected
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # ── 1. SUMMARY METRICS ROW ────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:16px; text-align:center;">
                <div style="color:#94A3B8; font-size:11px; font-weight:700; text-transform:uppercase;">Total Analyses</div>
                <div style="color:#FFFFFF; font-size:28px; font-weight:900; margin:4px 0;">247</div>
                <div style="color:#10B981; font-size:11px; font-weight:600;">↑ 12% vs last week</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(16,185,129,0.25); border-radius:14px; padding:16px; text-align:center;">
                <div style="color:#94A3B8; font-size:11px; font-weight:700; text-transform:uppercase;">Safe Requests</div>
                <div style="color:#10B981; font-size:28px; font-weight:900; margin:4px 0;">193</div>
                <div style="color:#94A3B8; font-size:11px;">78.1% of total traffic</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(245,158,11,0.25); border-radius:14px; padding:16px; text-align:center;">
                <div style="color:#94A3B8; font-size:11px; font-weight:700; text-transform:uppercase;">Sanitized Payloads</div>
                <div style="color:#F59E0B; font-size:28px; font-weight:900; margin:4px 0;">40</div>
                <div style="color:#94A3B8; font-size:11px;">PII masked before egress</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(239,68,68,0.25); border-radius:14px; padding:16px; text-align:center;">
                <div style="color:#94A3B8; font-size:11px; font-weight:700; text-transform:uppercase;">Blocked Threats</div>
                <div style="color:#EF4444; font-size:28px; font-weight:900; margin:4px 0;">14</div>
                <div style="color:#94A3B8; font-size:11px;">Jailbreaks & secret leaks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ── 2. TWO-COLUMN LAYOUT: RISK DISTRIBUTION & SECURITY EVENTS ─────────────
    c_left, c_right = st.columns([1, 1.2])

    with c_left:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:18px; height:100%;">
                <h3 style="color:#FFFFFF; font-size:16px; font-weight:800; margin:0 0 14px 0;">Risk Distribution</h3>
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                            <span style="color:#10B981; font-weight:700;">🟢 Low Risk (0–30%)</span>
                            <span style="color:#FFFFFF; font-weight:800;">78% (193)</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
                            <div style="background:#10B981; width:78%; height:100%;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                            <span style="color:#38BDF8; font-weight:700;">🔵 Medium Risk (31–60%)</span>
                            <span style="color:#FFFFFF; font-weight:800;">16% (40)</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
                            <div style="background:#38BDF8; width:16%; height:100%;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                            <span style="color:#F59E0B; font-weight:700;">🟡 High Risk (61–85%)</span>
                            <span style="color:#FFFFFF; font-weight:800;">5% (11)</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
                            <div style="background:#F59E0B; width:5%; height:100%;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                            <span style="color:#EF4444; font-weight:700;">🔴 Critical Risk (86–100%)</span>
                            <span style="color:#FFFFFF; font-weight:800;">1% (3)</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
                            <div style="background:#EF4444; width:1%; height:100%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_right:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:18px;">
                <h3 style="color:#FFFFFF; font-size:16px; font-weight:800; margin:0 0 14px 0;">Recent Security Events</h3>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); border-radius:8px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between;">
                        <div>
                            <div style="color:#FCA5A5; font-size:12.5px; font-weight:700;">Prompt Injection Attack Detected</div>
                            <div style="color:#94A3B8; font-size:11px;">DAN mode override directive intercepted</div>
                        </div>
                        <span style="background:#EF4444; color:#FFFFFF; font-size:10px; font-weight:800; padding:2px 8px; border-radius:6px;">BLOCK</span>
                    </div>
                    <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); border-radius:8px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between;">
                        <div>
                            <div style="color:#FCA5A5; font-size:12.5px; font-weight:700;">API Credential Leakage Vector</div>
                            <div style="color:#94A3B8; font-size:11px;">GCP Service Account Private Key detected</div>
                        </div>
                        <span style="background:#EF4444; color:#FFFFFF; font-size:10px; font-weight:800; padding:2px 8px; border-radius:6px;">BLOCK</span>
                    </div>
                    <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); border-radius:8px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between;">
                        <div>
                            <div style="color:#FDE68A; font-size:12.5px; font-weight:700;">PII Disclosure in Customer Query</div>
                            <div style="color:#94A3B8; font-size:11px;">Aadhaar & Email sanitized with Presidio</div>
                        </div>
                        <span style="background:#F59E0B; color:#000000; font-size:10px; font-weight:800; padding:2px 8px; border-radius:6px;">SANITIZE</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # ── 3. TRUST CENTER NAVIGATION BUTTONS ────────────────────────────────────
    st.markdown(
        "<div style='color:#94A3B8; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:10px;'>Trust Center Deep Dives</div>",
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.columns(3)

    with t1:
        if st.button("🏗️ Inspect Architecture & Pipeline →", key="tc_to_pipeline", use_container_width=True):
            st.session_state["selected_page"] = "Pipeline"
            st.rerun()

    with t2:
        if st.button("✨ Model Explainability (SHAP/LIME) →", key="tc_to_xai", use_container_width=True):
            st.session_state["selected_page"] = "Explainability"
            st.rerun()

    with t3:
        if st.button("📜 Cryptographic Audit Receipts →", key="tc_to_receipts", use_container_width=True):
            st.session_state["selected_page"] = "Audit Receipts"
            st.rerun()
