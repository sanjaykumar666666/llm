"""
AI Privacy Twin & Reversible Cryptographic Vault — Interactive Workspace View.
File: frontend/views/privacy_twin_view.py
"""

import io
import os
import time
import base64
from datetime import datetime
from typing import Dict, Any, Tuple
from PIL import Image
import streamlit as st

from backend.services.privacy_twin_service import PrivacyTwinService
from backend.services.image_privacy_service import ImagePrivacyService


def render_privacy_twin_view() -> None:
    # ── 1. Header & Innovation Badge ──────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 16px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC; letter-spacing:0.02em;">
                        🎭 AI Privacy Twin & Reversible Cryptographic Vault
                    </h1>
                    <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                        World-first context-preserving synthetic twin synthesis, zero-knowledge reversible AES-256 vault, and biometric liveness radar.
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:6px; background:rgba(124,58,237,0.15); border:1px solid rgba(168,85,247,0.35); border-radius:20px; padding:6px 14px; font-size:11.5px; font-weight:800; color:#C084FC;">
                    <span>✨ NEXT-GEN PRIVACY INNOVATION</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── 2. Three Interactive Innovation Modes ─────────────────────────────────
    tab_twin, tab_vault, tab_liveness = st.tabs([
        "🎭 1. Context-Preserving AI Twin",
        "🔐 2. Reversible Cryptographic Vault",
        "🛡️ 3. Liveness & Deepfake Radar"
    ])

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 1: CONTEXT-PRESERVING AI PRIVACY TWIN
    # ──────────────────────────────────────────────────────────────────────────
    with tab_twin:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px 16px; margin-bottom:14px; font-size:12.5px; color:#CBD5E1;">
                💡 <strong>Why This is Groundbreaking:</strong> Standard tools place destructive black boxes that ruin document aesthetics and break downstream AI/LLM parsing.
                <strong>The AI Privacy Twin</strong> replaces sensitive names, IDs, addresses, DOBs, QR codes, and faces with <strong>photorealistic, context-preserving synthetic fictitious data</strong> that looks 100% natural while leaking 0% real personal data!
            </div>
            """,
            unsafe_allow_html=True
        )

        c_tup, c_tpre = st.columns([1.6, 1])
        with c_tup:
            up_file = st.file_uploader(
                "Upload Document / Photo:",
                type=["png", "jpg", "jpeg", "webp"],
                key="twin_file_uploader",
                help="Upload any identity document, screenshot, or credential image."
            )
        with c_tpre:
            sample_preset = st.selectbox(
                "Or Select Test Preset:",
                [
                    "🪪 Identity Card (Aadhaar & PAN)",
                    "💳 Financial Banking Card",
                    "🔑 Production Server Secrets",
                    "None (Upload Custom File)"
                ],
                key="twin_preset_select"
            )

        # Profile Persona Switcher
        persona_name = st.selectbox(
            "Select Synthetic Twin Persona:",
            [
                "Persona 1: Arjun Sharma (Bengaluru, Karnataka)",
                "Persona 2: Priya Venkatesh (Mumbai, Maharashtra)",
                "Persona 3: Rohan Mehta (Gurugram, Haryana)",
                "Persona 4: Ananya Deshmukh (Hyderabad, Telangana)"
            ],
            key="twin_persona_select"
        )
        persona_idx = int(persona_name.split(":")[0].replace("Persona", "").strip()) - 1

        # Load file bytes
        file_bytes = b""
        file_name = "target.png"
        if up_file is not None:
            file_bytes = up_file.getvalue()
            file_name = up_file.name
        else:
            from frontend.views.image_analyzer import _generate_sample_image
            preset_map = {
                "🪪 Identity Card (Aadhaar & PAN)": "🪪 Identity Card (Aadhaar & PAN)",
                "💳 Financial Banking Card": "💳 Credit Card & Bank Account",
                "🔑 Production Server Secrets": "🔑 Server Login & API Secret",
            }
            target_preset = preset_map.get(sample_preset, "🪪 Identity Card (Aadhaar & PAN)")
            file_bytes, file_name = _generate_sample_image(target_preset)

        # Run Synthesis Button
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if st.button("🎭 GENERATE AI PRIVACY TWIN & CRYPTOGRAPHIC VAULT", type="primary", use_container_width=True, key="btn_gen_twin"):
            with st.spinner("🤖 Detecting sensitive PII, rendering synthetic persona & encrypting cryptographic vault…"):
                res_twin = PrivacyTwinService.generate_privacy_twin(
                    image_bytes=file_bytes,
                    filename=file_name,
                    seed_index=persona_idx,
                    enable_reversible_vault=True
                )
                # Also generate standard blackout for comparison
                res_blackout = ImagePrivacyService.process_image(
                    image_bytes=file_bytes,
                    filename=file_name,
                    protection_mode="BLACKOUT_SENSITIVE"
                )
                st.session_state["active_twin_res"] = res_twin
                st.session_state["active_blackout_res"] = res_blackout

        twin_res = st.session_state.get("active_twin_res")
        blackout_res = st.session_state.get("active_blackout_res")

        if twin_res and twin_res.get("success"):
            rep_count = twin_res.get("replaced_count", 0)
            proc_ms = twin_res.get("processing_ms", 0)
            vault_key = twin_res.get("session_vault_key", "")
            vault_token = twin_res.get("vault_token", "")

            # Success Banner
            st.markdown(
                f"""
                <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:12px 16px; margin-top:12px; margin-bottom:14px;">
                    <div style="color:#34D399; font-weight:800; font-size:13.5px; display:flex; align-items:center; gap:8px;">
                        <span>🟢</span> <span>AI PRIVACY TWIN SUCCESSFULLY SYNTHESIZED ({rep_count} PII Fields Replaced)</span>
                    </div>
                    <div style="color:#94A3B8; font-size:12px; margin-top:3px;">
                        Context-preserving synthetic replacement complete in <strong>{proc_ms}ms</strong> • Cryptographic Vault Session Active.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── 3-Way Comparative Visualization ───────────────────────────────
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:8px;'>3-WAY SPATIAL PRIVACY COMPARISON</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(
                    """
                    <div style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:8px; text-align:center; font-size:11.5px; font-weight:800; color:#FCA5A5; margin-bottom:6px;">
                        ⚠️ 1. ORIGINAL PAYLOAD (LEAKS REAL PII)
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.image(file_bytes, use_container_width=True)

            with c2:
                st.markdown(
                    """
                    <div style="background:rgba(100,116,139,0.2); border:1px solid rgba(100,116,139,0.4); border-radius:8px; padding:8px; text-align:center; font-size:11.5px; font-weight:800; color:#CBD5E1; margin-bottom:6px;">
                        ⬛ 2. TRADITIONAL DESTRUCTIVE BLACKOUT
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if blackout_res and blackout_res.get("protected_image_bytes"):
                    st.image(blackout_res["protected_image_bytes"], use_container_width=True)

            with c3:
                st.markdown(
                    """
                    <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); border-radius:8px; padding:8px; text-align:center; font-size:11.5px; font-weight:800; color:#34D399; margin-bottom:6px;">
                        🎭 3. AI PRIVACY TWIN (CONTEXT PRESERVED)
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if twin_res.get("twin_image_bytes"):
                    st.image(twin_res["twin_image_bytes"], use_container_width=True)

            # Download AI Twin
            st.download_button(
                label="📥 DOWNLOAD VERIFIED AI PRIVACY TWIN (PNG)",
                data=twin_res["twin_image_bytes"],
                file_name=f"privacy_twin_{file_name}",
                mime="image/png",
                type="primary",
                use_container_width=True
            )

            # Display Vault Token & Key for Tab 2
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(168,85,247,0.3); border-radius:10px; padding:12px 16px; margin-top:14px;">
                    <div style="color:#C084FC; font-weight:800; font-size:12.5px; margin-bottom:4px;">
                        🔐 REVERSIBLE CRYPTOGRAPHIC VAULT CREDENTIALS (SAVE FOR COMPLIANCE AUDIT):
                    </div>
                    <div style="font-size:11.5px; color:#E2E8F0; font-family:monospace; margin-bottom:4px;">
                        <strong>Session Private Key:</strong> <span style="color:#38BDF8;">{vault_key}</span>
                    </div>
                    <div style="font-size:11px; color:#94A3B8;">
                        Keep this key safe. Use it in <strong>Tab 2 (Reversible Cryptographic Vault)</strong> to decrypt original values on demand.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 2: REVERSIBLE CRYPTOGRAPHIC VAULT (COMPLIANCE AUDIT MODE)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_vault:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px 16px; margin-bottom:14px; font-size:12.5px; color:#CBD5E1;">
                🔐 <strong>Zero-Knowledge Compliance Unmasking:</strong> When regulators or authorized data controllers require verified inspection of the original unmasked document, they can authenticate using the zero-knowledge Cryptographic Session Key.
            </div>
            """,
            unsafe_allow_html=True
        )

        active_twin = st.session_state.get("active_twin_res", {})
        default_token = active_twin.get("vault_token", "")
        default_key = active_twin.get("session_vault_key", "")

        c_v1, c_v2 = st.columns([1, 1])
        with c_v1:
            input_key = st.text_input("Enter Vault Private Session Key:", value=default_key, placeholder="priv_vault_...", key="inp_vault_key")
        with c_v2:
            input_token = st.text_area("Encrypted Vault Token:", value=default_token, height=70, placeholder="eyJzYWx0Ijoi...", key="inp_vault_token")

        if st.button("🔓 DECRYPT & UNMASK PRIVACY VAULT", type="primary", use_container_width=True, key="btn_decrypt_vault"):
            if not input_key or not input_token:
                st.error("Please enter both the Private Session Key and the Encrypted Vault Token.")
            else:
                with st.spinner("🔐 Verifying cryptographic authentication tag and decrypting AES-256 payload…"):
                    success, decrypted_data, msg = PrivacyTwinService.decrypt_vault_payload(input_token, input_key)
                    if success and decrypted_data:
                        st.success("✅ Cryptographic Authentication Verified! Original sensitive entities successfully unmasked.")
                        st.json(decrypted_data)
                    else:
                        st.error(f"❌ Decryption Failed: {msg}")

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 3: LIVENESS & DEEPFAKE RADAR
    # ──────────────────────────────────────────────────────────────────────────
    with tab_liveness:
        st.markdown(
            """
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px 16px; margin-bottom:14px; font-size:12.5px; color:#CBD5E1;">
                🛡️ <strong>Biometric & Document Authenticity Radar:</strong> Inspects digital captures for Moire frequency interference, screen replay banding, artificial diffusion boundaries, and biometric spoofing.
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🔍 RUN LIVENESS & DEEPFAKE RADAR AUDIT", type="primary", use_container_width=True, key="btn_run_liveness"):
            with st.spinner("📡 Computing 2D FFT frequency spectrum, Moire ratio & Laplacian sharpness variance…"):
                live_res = PrivacyTwinService.analyze_liveness_and_deepfake(file_bytes)
                st.session_state["active_liveness_res"] = live_res

        live_data = st.session_state.get("active_liveness_res")
        if live_data and live_data.get("success"):
            l_score = live_data.get("liveness_score", 0)
            badge = live_data.get("badge", "")
            m_ratio = live_data.get("moire_ratio", 0)
            edge_var = live_data.get("edge_sharpness_var", 0)
            details = live_data.get("analysis_details", {})

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Authenticity Score", f"{l_score}%")
            with col_m2:
                st.metric("Moire Frequency Ratio", f"{m_ratio}")
            with col_m3:
                st.metric("Edge Sharpness Variance", f"{edge_var}")

            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(56,189,248,0.25); border-radius:10px; padding:14px 18px; margin-top:14px;">
                    <div style="font-size:14px; font-weight:800; color:#38BDF8; margin-bottom:8px;">{badge}</div>
                    <div style="font-size:12px; color:#CBD5E1; margin-bottom:4px;">
                        • <strong>Moire Frequency Spectrum:</strong> {details.get('moire_spectrum_density', 'Normal')}
                    </div>
                    <div style="font-size:12px; color:#CBD5E1; margin-bottom:4px;">
                        • <strong>Edge & Focus Quality:</strong> {details.get('edge_boundary_integrity', 'Sharp')}
                    </div>
                    <div style="font-size:12px; color:#CBD5E1;">
                        • <strong>Deepfake Boundary Gradient:</strong> {details.get('deepfake_boundary_score', 'Authentic')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
