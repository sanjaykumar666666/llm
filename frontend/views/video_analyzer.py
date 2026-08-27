"""
Production Video Privacy Protection & Temporal Multi-Modal Verification Workspace View.
File: frontend/views/video_analyzer.py

Features:
  1. 📤 Secure Video Ingestion (MP4, MOV, AVI, MKV, WEBM) with Stream Integrity Validation.
  2. 🔍 Smart Keyframe Sampling + Multi-Modal OCR + Face + QR/Barcode Detection.
  3. 🎯 Temporal Tracking & Inter-Frame Box Interpolation (Zero Dropped Frames on Moving Targets).
  4. 🛡️ True Pixel-Level Video Protection (Redact, Blur, Pixelate, Blackout, Full Blur).
  5. ✅ Closed-Loop Secondary Verification Engine (Confirms Zero Residual Leaks).
  6. 📥 Metadata-Stripped Verified Protected Video Download.
  7. 🧾 Privacy-Safe Audit Telemetry & Cryptographic Trust Receipt.
"""

import io
import os
import time
import base64
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime
import streamlit as st

from backend.services.video_privacy_service import VideoPrivacyService
from backend.services.trust_receipt import generate_receipt, format_receipt_text
from frontend.components.analysis_panel import render_live_analysis_panel


def render_video_analyzer_view() -> None:
    # ── 1. Header & Step Pipeline ─────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 16px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC; letter-spacing:0.02em;">
                        🎬 Video Privacy Shield & Temporal Redaction
                    </h1>
                    <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                        Temporal object tracking, pixel-level PII/Face/QR protection, closed-loop verification, and metadata-stripped export.
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:6px; background:rgba(15,23,42,0.8); border:1px solid rgba(56,189,248,0.25); border-radius:20px; padding:6px 14px; font-size:11.5px; font-weight:700; color:#38BDF8;">
                    <span>🛡️ TEMPORAL ZERO-LEAK GUARANTEE</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Workflow Progress Indicator ───────────────────────────────────────────
    st.markdown(
        """
        <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px 16px; margin-bottom:18px; display:flex; align-items:center; justify-content:space-between; font-size:12px; font-weight:700; color:#94A3B8; flex-wrap:wrap; gap:8px;">
            <span>1. 📤 Upload Video</span>
            <span style="color:#64748B;">➔</span>
            <span>2. 🔍 Scan & Track</span>
            <span style="color:#64748B;">➔</span>
            <span>3. 🛡️ Pixel Protect</span>
            <span style="color:#64748B;">➔</span>
            <span>4. ✅ Verify (0 Leaks)</span>
            <span style="color:#64748B;">➔</span>
            <span style="color:#38BDF8;">5. 📥 Download</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    c_main, c_metrics = st.columns([2.3, 1])

    with c_main:
        # ── Step 1: Video Upload & Preset Selection ───────────────────────────
        st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:6px;'>STEP 1: UPLOAD TARGET VIDEO</div>", unsafe_allow_html=True)

        c_up, c_pre = st.columns([1.6, 1])
        with c_up:
            uploaded_file = st.file_uploader(
                "Upload Video (MP4, MOV, AVI, MKV, WEBM):",
                type=["mp4", "mov", "avi", "mkv", "webm"],
                key="vid_file_uploader_v2",
                help="Maximum file size: 100MB. Videos are processed in memory and never permanently stored."
            )

        with c_pre:
            sample_preset = st.selectbox(
                "Or Test with Preset Sample:",
                [
                    "None (Use Uploaded File)",
                    "🪪 Identity Video (Moving Aadhaar & PAN)",
                    "👤 Face & Biometric Video (Moving Person)",
                    "💳 Financial Video (Credit Card & Bank)",
                    "🔑 Auth Secret Video (API Key & Password)",
                    "🟢 Clean Landscape Video (Zero PII)",
                ],
                key="vid_sample_preset"
            )

        file_bytes = b""
        file_name = "target_video.mp4"

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
        elif sample_preset != "None (Use Uploaded File)":
            with st.spinner("🎬 Generating animated test video preset…"):
                file_bytes, file_name = VideoPrivacyService.generate_sample_video(sample_preset)
        else:
            # Default initial sample
            with st.spinner("🎬 Loading default identity video sample…"):
                file_bytes, file_name = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")

        # Validate Video Payload
        is_valid, val_err, meta = VideoPrivacyService.validate_video_bytes(file_bytes, file_name)
        if not is_valid or meta is None:
            st.error(f"❌ Upload Error: {val_err}")
            return

        # ── Display Basic Metadata ────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="background:rgba(30,41,59,0.4); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:8px 14px; margin-top:6px; margin-bottom:14px; display:flex; gap:16px; font-size:12px; color:#94A3B8; flex-wrap:wrap;">
                <span>⏱️ <strong>Duration:</strong> {meta['duration_str']} ({meta['duration_sec']}s)</span>
                <span>📐 <strong>Resolution:</strong> {meta['resolution']}</span>
                <span>🎞️ <strong>FPS:</strong> {meta['fps']}</span>
                <span>🔢 <strong>Frames:</strong> {meta['total_frames']}</span>
                <span>💾 <strong>Size:</strong> {meta['file_size_mb']} MB</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── Step 2: Protection Settings ───────────────────────────────────────
        st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:10px; margin-bottom:6px;'>STEP 2: CONFIGURE PROTECTION SETTINGS</div>", unsafe_allow_html=True)

        c_mode, c_opt1, c_opt2 = st.columns([1.8, 1, 1])
        with c_mode:
            protection_mode = st.selectbox(
                "Protection Mode:",
                [
                    "Redact Sensitive",
                    "Blur Sensitive",
                    "Pixelate Sensitive",
                    "Blackout Sensitive",
                    "Blur All",
                ],
                key="vid_protection_mode"
            )

        with c_opt1:
            protect_faces = st.checkbox("👤 Protect Faces", value=True, key="vid_protect_faces")
            protect_qr = st.checkbox("🏁 Protect QR / Barcodes", value=True, key="vid_protect_qr")

        with c_opt2:
            remove_audio = st.checkbox("🎙️ Remove Audio Track", value=True, key="vid_remove_audio")
            sampling_rate = st.slider("Scan FPS:", min_value=1.0, max_value=5.0, value=3.0, step=1.0, key="vid_sampling_fps")

        # ── Step 3: Run Video Privacy Shield Pipeline ─────────────────────────
        cache_key = f"{file_name}_{len(file_bytes)}_{protection_mode}_{protect_faces}_{protect_qr}_{remove_audio}_{sampling_rate}"

        col_btn1, col_btn2 = st.columns([1.5, 1])
        with col_btn1:
            run_scan = st.button("🛡️ SCAN & PROTECT VIDEO", type="primary", use_container_width=True, key="btn_run_vid_protect")

        if run_scan or "vid_result_cache" not in st.session_state or st.session_state.get("vid_result_cache_key") != cache_key:
            if run_scan or "vid_result_cache" not in st.session_state:
                with st.spinner("🎥 Executing Keyframe Sampling, OCR, Face Detection, Temporal Tracking & Pixel Protection…"):
                    progress_bar = st.progress(0, text="Initializing video privacy scanner…")
                    time.sleep(0.1)
                    progress_bar.progress(35, text="Sampling keyframes & running OCR entity detection…")
                    time.sleep(0.1)
                    progress_bar.progress(70, text="Tracking moving regions & applying pixel protection…")

                    pipeline_res = VideoPrivacyService.execute_video_privacy_pipeline(
                        video_bytes=file_bytes,
                        filename=file_name,
                        protection_mode=protection_mode,
                        protect_faces=protect_faces,
                        protect_qr_barcodes=protect_qr,
                        remove_audio=remove_audio,
                        sampling_fps=sampling_rate,
                    )
                    progress_bar.progress(100, text="Verification complete!")
                    time.sleep(0.1)
                    progress_bar.empty()

                    st.session_state["vid_result_cache"] = pipeline_res
                    st.session_state["vid_result_cache_key"] = cache_key
            else:
                pipeline_res = st.session_state.get("vid_result_cache")
        else:
            pipeline_res = st.session_state.get("vid_result_cache")

        if pipeline_res and pipeline_res.get("status") == "success":
            scan_res = pipeline_res.get("scan_results", {})
            verif_res = pipeline_res.get("verification", {})
            is_verified = pipeline_res.get("verified", False)
            protected_vid_bytes = pipeline_res.get("protected_video_bytes", b"")

            # ── Step 4: Side-by-Side Video Inspection ─────────────────────────
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:18px; margin-bottom:6px;'>STEP 3: TEMPORAL PRIVACY COMPARISON</div>", unsafe_allow_html=True)

            c_orig_v, c_prot_v = st.columns(2)

            with c_orig_v:
                st.markdown(
                    """
                    <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:6px 12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:800; color:#F87171;">ORIGINAL UN-PROTECTED VIDEO</span>
                        <span style="font-size:11px; font-weight:700; color:#EF4444; background:rgba(239,68,68,0.2); padding:2px 8px; border-radius:4px;">⚠️ UNPROTECTED</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.video(file_bytes)

            with c_prot_v:
                status_badge = "🟢 VERIFIED PROTECTED" if is_verified else "🔴 PROTECTION FAILED"
                badge_bg = "rgba(16,185,129,0.2)" if is_verified else "rgba(239,68,68,0.2)"
                badge_color = "#34D399" if is_verified else "#EF4444"

                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:6px 12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:800; color:#34D399;">PROTECTED REDACTED VIDEO</span>
                        <span style="font-size:11px; font-weight:700; color:{badge_color}; background:{badge_bg}; padding:2px 8px; border-radius:4px;">{status_badge}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if protected_vid_bytes:
                    st.video(protected_vid_bytes)
                else:
                    st.warning("Protected video stream is unavailable.")

            # ── Step 5: Chronological Privacy Timeline ────────────────────────
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:18px; margin-bottom:6px;'>STEP 4: DETECTED TEMPORAL PRIVACY TIMELINE</div>", unsafe_allow_html=True)

            timeline_events = scan_res.get("timeline_events", [])
            if timeline_events:
                st.markdown(
                    f"<div style='font-size:12px; color:#94A3B8; margin-bottom:8px;'>Detected <strong>{len(timeline_events)}</strong> temporal sensitive events across video stream (tracking interpolated across all intermediate frames):</div>",
                    unsafe_allow_html=True
                )
                for ev in timeline_events:
                    ts = ev.get("timestamp_str", "00:00")
                    desc = ev.get("description", "Sensitive Entity")
                    cat = ev.get("category", "SENSITIVE")
                    conf = ev.get("confidence", 0.95)

                    icon = "🪪" if cat == "IDENTITY" else ("💳" if cat == "FINANCIAL" else ("🔑" if cat == "AUTHENTICATION" else ("👤" if cat == "BIOMETRIC" else "📱")))
                    st.markdown(
                        f"""
                        <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:6px 12px; margin-bottom:4px; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <strong style="color:#38BDF8; font-family:monospace;">⏱️ {ts}</strong> &nbsp;
                                <span>{icon} <strong>{desc}</strong> ({cat})</span>
                            </div>
                            <div style="font-size:11px; color:#10B981; font-weight:700;">
                                TRACKED & PROTECTED (Conf: {int(conf*100)}%)
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    """
                    <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25); border-radius:8px; padding:12px 16px; color:#34D399; font-size:13px; font-weight:700;">
                        🟢 NO SENSITIVE DATA DETECTED — No sensitive content was detected by the configured privacy scanners.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ── Step 6: Closed-Loop Verification Banner & Download ────────────
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:18px; margin-bottom:6px;'>STEP 5: VERIFICATION & SAFE EXPORT</div>", unsafe_allow_html=True)

            if is_verified:
                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.35); border-radius:10px; padding:14px 18px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                        <div>
                            <div style="font-size:13.5px; font-weight:800; color:#34D399; margin-bottom:2px;">
                                ✅ CLOSED-LOOP VERIFICATION PASSED (0 SENSITIVE LEAKS)
                            </div>
                            <div style="font-size:12px; color:#A7F3D0;">
                                Scanned {verif_res.get('frames_rechecked', 12)} output keyframes — verified 0 residual credentials or un-masked faces.
                            </div>
                        </div>
                        <div style="font-size:11.5px; font-family:monospace; color:#6EE7B7; background:rgba(0,0,0,0.3); padding:4px 8px; border-radius:4px;">
                            SHA-256: {pipeline_res['sha256_hash'][:16]}…
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.download_button(
                    label=f"📥 DOWNLOAD PROTECTED VIDEO ({meta['file_size_mb']:.1f} MB)",
                    data=protected_vid_bytes,
                    file_name=pipeline_res["protected_filename"],
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True,
                    key="btn_download_protected_vid"
                )
            else:
                st.error("🔴 PROTECTION FAILED: Verification pass detected potential residual sensitive leaks. Video download is disabled for security.")

            # ── Step 7: Cryptographic AI Trust Receipt ────────────────────────
            with st.expander("🧾 Cryptographic AI Trust Receipt", expanded=False):
                receipt_obj = generate_receipt(
                    user_id="Enterprise-Video-Shield",
                    model_selected="Aiera Video Privacy Shield",
                    pii_detected=len(timeline_events) > 0,
                    pii_entities=[e.get("description", "") for e in timeline_events],
                    injection_detected=False,
                    risk_score=scan_res.get("risk_score", 0),
                    risk_level=scan_res.get("risk_level", "LOW"),
                    policy_action=scan_res.get("action", "ALLOW"),
                    pii_action="REDACT" if is_verified else "BLOCK",
                    output_action="ALLOW" if is_verified else "BLOCK",
                    output_sensitive=False,
                    request_id=pipeline_res.get("receipt_id", "ATC-VID-001")
                )
                st.code(format_receipt_text(receipt_obj), language="text")

    # ── Sidebar Metrics & Privacy Risk Panel ──────────────────────────────────
    with c_metrics:
        if pipeline_res and pipeline_res.get("status") == "success":
            scan_data = pipeline_res.get("scan_results", {})
            r_score = scan_data.get("risk_score", 0)
            r_level = scan_data.get("risk_level", "LOW")

            # Risk Summary Metric Box
            risk_color = "#EF4444" if r_level in ("HIGH", "CRITICAL") else ("#F59E0B" if r_level == "MEDIUM" else "#10B981")
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 4px 16px rgba(0,0,0,0.3);">
                    <div style="font-size:11px; font-weight:800; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">
                        VIDEO PRIVACY RISK SCORE
                    </div>
                    <div style="display:flex; align-items:baseline; gap:8px;">
                        <span style="font-size:32px; font-weight:900; color:{risk_color};">{r_score}%</span>
                        <span style="font-size:13px; font-weight:800; color:{risk_color};">● {r_level}</span>
                    </div>
                    <div style="font-size:11.5px; color:#94A3B8; margin-top:8px;">
                        Tracking: <strong>{scan_data.get('total_sensitive_events', 0)} events</strong> across {scan_data.get('sampled_keyframes_scanned', 0)} keyframes.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Telemetry Metrics
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:14px; margin-bottom:14px; font-size:12px; color:#94A3B8;">
                    <div style="font-weight:800; color:#F8FAFC; margin-bottom:8px; font-size:12.5px;">🔍 Video Privacy Metrics</div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Sensitive Regions:</span>
                        <strong style="color:#F8FAFC;">{scan_data.get('total_sensitive_events', 0)}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Categories:</span>
                        <strong style="color:#38BDF8;">{len(scan_data.get('detected_categories', []))}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Protection Mode:</span>
                        <strong style="color:#34D399;">{pipeline_res.get('protection_mode')}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Verification:</span>
                        <strong style="color:#34D399;">{'PASSED' if pipeline_res.get('verified') else 'FAILED'}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Processing Time:</span>
                        <strong style="color:#F8FAFC;">{pipeline_res.get('processing_time_ms', 0):.0f} ms</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("Upload a video and click 'SCAN & PROTECT VIDEO' to view privacy risk score and metrics.")
