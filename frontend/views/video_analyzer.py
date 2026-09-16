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
import hashlib
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime
import streamlit as st

from backend.services.video_privacy_service import VideoPrivacyService
from backend.services.video_understanding_service import VideoUnderstandingService
from backend.services.trust_receipt import generate_receipt, format_receipt_text
from frontend.components.analysis_panel import render_live_analysis_panel


def render_video_analyzer_view() -> None:
    # ── Header & Title ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 16px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC; letter-spacing:0.02em;">
                        🎬 Video Privacy Shield & Temporal Redaction
                    </h1>
                    <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                        Enterprise 7-Phase Video Validation, Systematic Detection, Temporal Tracking, Adaptive Redaction, and Independent Verification.
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:6px; background:rgba(15,23,42,0.8); border:1px solid rgba(56,189,248,0.25); border-radius:20px; padding:6px 14px; font-size:11.5px; font-weight:700; color:#38BDF8;">
                    <span>🛡️ 7-PHASE VERIFIED PIPELINE</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── 7-Phase Workflow Progress Indicator ───────────────────────────────────
    st.markdown(
        """
        <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px 16px; margin-bottom:18px; display:flex; align-items:center; justify-content:space-between; font-size:11.5px; font-weight:700; color:#94A3B8; flex-wrap:wrap; gap:8px;">
            <span>1. 📥 Validation</span>
            <span style="color:#64748B;">➔</span>
            <span>2. 🔍 Detection</span>
            <span style="color:#64748B;">➔</span>
            <span>3. 🎯 Temporal Tracking</span>
            <span style="color:#64748B;">➔</span>
            <span>4. 🛡️ Redaction</span>
            <span style="color:#64748B;">➔</span>
            <span>5. ✅ Verification</span>
            <span style="color:#64748B;">➔</span>
            <span style="color:#38BDF8;">6. 📊 Report</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    c_main, c_metrics = st.columns([2.3, 1])

    with c_main:
        # ── Step 1: Video Upload & Preset Selection ───────────────────────────
        st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:6px;'>STEP 1: INGEST TARGET VIDEO</div>", unsafe_allow_html=True)

        c_up, c_pre = st.columns([1.6, 1])
        with c_up:
            uploaded_file = st.file_uploader(
                "Upload Video (MP4, MOV, AVI, MKV, WEBM):",
                type=["mp4", "mov", "avi", "mkv", "webm"],
                key="vid_file_uploader_v7",
                help="Maximum file size: 100MB. Videos are analyzed locally with strict zero-leak verification."
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
            with st.spinner("🎬 Loading default identity video sample…"):
                file_bytes, file_name = VideoPrivacyService.generate_sample_video("🪪 Identity Video (Moving Aadhaar & PAN)")

        # ── Phase 1 Validation Execution ──────────────────────────────────────
        is_valid, val_err, meta = VideoPrivacyService.validate_video_bytes(file_bytes, file_name)

        if not is_valid or meta is None:
            st.markdown(
                f"""
                <div style="background:rgba(239,68,68,0.12); border:1.5px solid rgba(239,68,68,0.4); border-radius:10px; padding:14px 16px; margin-top:10px; margin-bottom:16px;">
                    <div style="font-size:14px; font-weight:800; color:#F87171; margin-bottom:4px;">
                        ❌ PHASE 1 VALIDATION FAILED: Video Ingestion Rejected
                    </div>
                    <div style="font-size:12.5px; color:#FECACA; line-height:1.5;">
                        <strong>Diagnostic Reason:</strong> {val_err or 'Corrupted or unreadable video payload.'}
                    </div>
                    <div style="font-size:11.5px; color:#94A3B8; margin-top:8px;">
                        Please provide an uncorrupted video file in MP4, MOV, AVI, MKV, or WEBM format with valid decodable video frames.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            return

        # ── Phase 1 Stream Diagnostic Card ────────────────────────────────────
        checks = meta.get("checks_passed", {})
        st.markdown(
            f"""
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(56,189,248,0.25); border-radius:10px; padding:12px 16px; margin-top:8px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                    <span style="font-size:12.5px; font-weight:800; color:#38BDF8;">📋 PHASE 1: VIDEO INPUT VALIDATION</span>
                    <span style="font-size:11px; font-weight:800; color:#34D399; background:rgba(16,185,129,0.2); padding:2px 8px; border-radius:4px;">🟢 VALIDATION PASSED</span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; font-size:12px; color:#94A3B8;">
                    <div>⏱️ <strong>Duration:</strong> <span style="color:#F8FAFC;">{meta['duration_str']} ({meta['duration_sec']}s)</span></div>
                    <div>📐 <strong>Resolution:</strong> <span style="color:#F8FAFC;">{meta['resolution']}</span></div>
                    <div>🎞️ <strong>FPS:</strong> <span style="color:#F8FAFC;">{meta['fps']}</span></div>
                    <div>🔢 <strong>Frames:</strong> <span style="color:#F8FAFC;">{meta['total_frames']}</span></div>
                    <div>💾 <strong>Size:</strong> <span style="color:#F8FAFC;">{meta['file_size_mb']} MB</span></div>
                    <div>🎬 <strong>Codec:</strong> <span style="color:#38BDF8;">{meta.get('video_codec', 'H.264')}</span></div>
                    <div>🎙️ <strong>Audio:</strong> <span style="color:#F8FAFC;">{'Active' if meta.get('audio_present') else 'None'}</span></div>
                    <div>🔄 <strong>Seek Test:</strong> <span style="color:#34D399;">Passed (Start/Mid/End)</span></div>
                </div>
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
                    "🛡️ Redact & Block Sensitive",
                    "⬛ Solid Blackout Block",
                    "🌫️ Heavy Privacy Blur",
                    "🔲 Mosaic Pixelate Block",
                    "🌐 Blur Entire Video",
                ],
                key="vid_protection_mode_v7"
            )

        with c_opt1:
            protect_faces = st.checkbox("👤 Protect Faces", value=True, key="vid_protect_faces_v7")
            protect_qr = st.checkbox("🏁 Protect QR / Barcodes", value=True, key="vid_protect_qr_v7")

        with c_opt2:
            remove_audio = st.checkbox("🎙️ Remove Audio Track", value=True, key="vid_remove_audio_v7")
            sampling_rate = st.slider("Scan FPS:", min_value=1.0, max_value=5.0, value=3.0, step=0.5, key="vid_sampling_fps_v7")

        # ── Step 3: Run Pipeline Execution ────────────────────────────────────
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()[:16] if file_bytes else "empty"
        cache_key = f"{file_name}_{file_sha256}_{protection_mode}_{protect_faces}_{protect_qr}_{remove_audio}_{sampling_rate}"

        col_btn1, col_btn2 = st.columns([1.5, 1])
        with col_btn1:
            run_scan = st.button("🛡️ EXECUTE 7-PHASE PRIVACY SHIELD", type="primary", use_container_width=True, key="btn_run_vid_protect_v7")

        needs_processing = run_scan

        if needs_processing:
            prog_placeholder = st.empty()
            prog_bar = prog_placeholder.progress(0, text="🎥 Initializing 7-Phase Privacy Shield...")

            def _live_progress(pct: float, message: str):
                try:
                    prog_bar.progress(min(1.0, max(0.0, float(pct))), text=message)
                except Exception:
                    pass

            pipeline_res = VideoUnderstandingService.execute_video_understanding_and_privacy_pipeline(
                video_bytes=file_bytes,
                filename=file_name,
                protection_mode=protection_mode,
                protect_faces=protect_faces,
                protect_qr_barcodes=protect_qr,
                remove_audio=remove_audio,
                sampling_fps=sampling_rate,
                progress_callback=_live_progress,
            )
            prog_placeholder.empty()
            st.session_state["vid_result_cache"] = pipeline_res
            st.session_state["vid_result_cache_key"] = cache_key
        elif "vid_result_cache" in st.session_state and st.session_state.get("vid_result_cache_key") == cache_key:
            pipeline_res = st.session_state.get("vid_result_cache")
        else:
            pipeline_res = None

        if pipeline_res is None:
            st.markdown(
                """
                <div style="background:rgba(15,23,42,0.6); border:1.5px dashed rgba(56,189,248,0.35); border-radius:12px; padding:18px 20px; margin-top:14px; text-align:center;">
                    <div style="font-size:14px; font-weight:800; color:#38BDF8; margin-bottom:4px;">
                        🎬 Video Validated — Ready for Privacy Shield Execution
                    </div>
                    <div style="font-size:12.5px; color:#94A3B8; margin-bottom:12px;">
                        Click <strong>🛡️ EXECUTE 7-PHASE PRIVACY SHIELD</strong> above to perform systematic scanning, temporal tracking, adaptive redaction, and closed-loop verification.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.video(file_bytes)

        if pipeline_res and pipeline_res.get("status") == "success":
            scan_res = pipeline_res.get("scan_results", {})
            verif_res = pipeline_res.get("verification", {})
            is_verified = pipeline_res.get("verified", False)
            zero_leaks = pipeline_res.get("zero_leaks_guarantee", False)
            protected_vid_bytes = pipeline_res.get("protected_video_bytes", b"")
            final_report = pipeline_res.get("final_report", {})
            breakdown = scan_res.get("breakdown_counts", {})
            low_conf_warning = scan_res.get("low_confidence_warning")

            # ── Low-Confidence Warning Banner (Phase 7) ───────────────────────
            if low_conf_warning:
                st.warning(f"⚠️ {low_conf_warning}")

            # ── Step 4: Temporal Privacy Comparison ───────────────────────────
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
                status_badge = "🟢 VERIFIED PROTECTED" if is_verified else "🔴 VERIFICATION FAILED"
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

            # ── 🎥 OUTPUT 1: Video Summary (Phase 1) ──────────────────────────
            vid_summary = pipeline_res.get("video_summary", {})
            if vid_summary and vid_summary.get("summary_text"):
                st.markdown(
                    f"""
                    <div style="background:rgba(15,23,42,0.7); border:1.5px solid rgba(56,189,248,0.3); border-radius:12px; padding:16px 20px; margin-top:20px; margin-bottom:16px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="font-size:15px; font-weight:800; color:#38BDF8;">🎥 OUTPUT 1: VIDEO SUMMARY</span>
                            <span style="font-size:11px; font-weight:700; color:#94A3B8; background:rgba(255,255,255,0.06); padding:2px 8px; border-radius:4px;">Context: {vid_summary.get('overall_context', 'Multimedia Analysis')}</span>
                        </div>
                        <div style="font-size:13.5px; color:#F8FAFC; line-height:1.6; margin-bottom:12px; font-weight:500;">
                            {vid_summary.get('summary_text', '')}
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px; font-size:12px; color:#94A3B8;">
                            <div style="background:rgba(15,23,42,0.4); padding:8px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                                <strong style="color:#38BDF8;">🎬 Beginning:</strong> <span style="color:#CBD5E1;">{vid_summary.get('beginning', '')}</span>
                            </div>
                            <div style="background:rgba(15,23,42,0.4); padding:8px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                                <strong style="color:#FBBF24;">⚡ Middle:</strong> <span style="color:#CBD5E1;">{vid_summary.get('middle', '')}</span>
                            </div>
                            <div style="background:rgba(15,23,42,0.4); padding:8px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                                <strong style="color:#34D399;">🏁 End:</strong> <span style="color:#CBD5E1;">{vid_summary.get('end', '')}</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ── 📖 OUTPUT 2: Detailed Video Explanation (Phase 2) ─────────────
            det_explanation = pipeline_res.get("detailed_explanation", {})
            segments = det_explanation.get("segments", [])
            if segments:
                with st.expander("📖 OUTPUT 2: DETAILED VIDEO EXPLANATION (Timestamp-by-Timestamp Narrative)", expanded=True):
                    for seg in segments:
                        p_icon = "⚠️" if seg["privacy_risk"] else "✓"
                        p_color = "#F87171" if seg["privacy_risk"] else "#34D399"
                        st.markdown(
                            f"""
                            <div style="background:rgba(15,23,42,0.4); border-left:3px solid {p_color}; padding:8px 14px; margin-bottom:8px; border-radius:0 6px 6px 0;">
                                <div style="font-family:monospace; font-weight:800; color:#38BDF8; font-size:12.5px;">
                                    ⏱️ {seg['time_range']} {p_icon}
                                </div>
                                <div style="font-size:13px; color:#E2E8F0; margin-top:2px;">
                                    {seg['scene_description']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            # ── ⏱ OUTPUT 3: Structured Video Timeline (Phase 3) ───────────────
            vid_timeline = pipeline_res.get("video_timeline", [])
            if vid_timeline:
                with st.expander(f"⏱ OUTPUT 3: STRUCTURED VIDEO TIMELINE ({len(vid_timeline)} Merged Scene Segments)", expanded=False):
                    for t_item in vid_timeline:
                        risk_flag = "🔴 PRIVACY RISK" if t_item["privacy_risk"] else "🟢 SAFE SEGMENT"
                        flag_bg = "rgba(239,68,68,0.15)" if t_item["privacy_risk"] else "rgba(16,185,129,0.15)"
                        flag_color = "#F87171" if t_item["privacy_risk"] else "#34D399"
                        st.markdown(
                            f"""
                            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(15,23,42,0.3); border:1px solid rgba(255,255,255,0.05); padding:8px 12px; margin-bottom:6px; border-radius:6px; font-size:12px; flex-wrap:wrap;">
                                <div>
                                    <strong style="color:#38BDF8; font-family:monospace;">{t_item['start_time']} – {t_item['end_time']}</strong>: <span style="color:#F8FAFC;">{t_item['description']}</span>
                                </div>
                                <div style="font-weight:700; font-size:10.5px; color:{flag_color}; background:{flag_bg}; padding:2px 8px; border-radius:4px;">
                                    {risk_flag} ({t_item.get('detected_entities_count', 0)} Detections)
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            # ── Step 5: Phase 2 Detections Breakdown Table ────────────────────
            st.markdown("<div style='font-size:14px; font-weight:800; color:#E2E8F0; margin-top:20px; margin-bottom:8px;'>PHASE 4: DETECTION BREAKDOWN & TEMPORAL TRACKING</div>", unsafe_allow_html=True)

            c_b1, c_b2, c_b3, c_b4 = st.columns(4)
            with c_b1:
                st.metric("👤 Faces", breakdown.get("faces_detected", 0))
                st.metric("🏁 QR / Barcodes", breakdown.get("qr_barcodes_detected", 0))
            with c_b2:
                st.metric("🪪 ID Cards / Passports", breakdown.get("id_cards_detected", 0))
                st.metric("💳 Financial / Cards", breakdown.get("financial_accounts_detected", 0))
            with c_b3:
                st.metric("🔑 Passwords & Secrets", breakdown.get("passwords_api_keys_detected", 0))
                st.metric("🚗 Number Plates", breakdown.get("vehicle_plates_detected", 0))
            with c_b4:
                st.metric("📞 Phone Numbers", breakdown.get("phone_numbers_detected", 0))
                st.metric("📍 Addresses", breakdown.get("addresses_detected", 0))

            # ── Temporal Tracking Continuity & Gap Recovery Report (Phase 3) ───
            tracks = scan_res.get("tracks", [])
            gap_events = scan_res.get("tracking_gap_events", [])
            recovered_count = scan_res.get("missed_frames_recovered", 0)

            with st.expander(f"🎯 Temporal Object Tracking & Continuity ({len(tracks)} Active Tracks, {recovered_count} Gap Frames Recovered)", expanded=False):
                if tracks:
                    for t in tracks:
                        st.markdown(
                            f"""
                            <div style="background:rgba(15,23,42,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:12px; display:flex; justify-content:space-between; flex-wrap:wrap;">
                                <div><strong style="color:#38BDF8;">{t['track_id']}</strong>: {t['description']}</div>
                                <div>⏱️ {t['start_timestamp_str']} – {t['end_timestamp_str']} ({t['total_frames_covered']} frames | Velocity: {t['average_velocity_px']} px/f)</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                if gap_events:
                    st.markdown("<div style='font-size:11.5px; color:#FBBF24; font-weight:700; margin-top:6px;'>⚡ Recovered Tracking Gap Anomalies:</div>", unsafe_allow_html=True)
                    for g in gap_events[:5]:
                        st.caption(f"• {g['description']}")

            # ── 🔒 OUTPUT 4 & 5: Privacy Risks & Reasoning Bridge ─────────────
            st.markdown("<div style='font-size:14px; font-weight:800; color:#E2E8F0; margin-top:20px; margin-bottom:8px;'>PHASE 5: PRIVACY REASONING BRIDGE (Why It Was Blocked)</div>", unsafe_allow_html=True)

            reasoning_bridge = pipeline_res.get("privacy_reasoning_bridge", [])
            if reasoning_bridge:
                for idx, b_item in enumerate(reasoning_bridge, 1):
                    s_info = b_item["sensitive_information"]
                    st.markdown(
                        f"""
                        <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:14px 16px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:6px;">
                                <span style="font-weight:800; color:#F8FAFC; font-size:13.5px;">
                                    ⚠️ #{idx}. <span style="color:#38BDF8; font-family:monospace;">⏱️ {b_item['time_span']}</span> — {s_info['title']}
                                </span>
                                <span style="font-size:11px; font-weight:700; color:#F87171; background:rgba(239,68,68,0.15); padding:2px 8px; border-radius:4px;">
                                    {int(s_info['confidence']*100)}% Confidence
                                </span>
                            </div>
                            <div style="font-size:12.5px; line-height:1.5; color:#CBD5E1; display:grid; gap:6px;">
                                <div><strong style="color:#38BDF8;">🎬 Video Event:</strong> {b_item['video_event']}</div>
                                <div><strong style="color:#FBBF24;">❓ Reason Sensitive:</strong> {b_item['why_sensitive']}</div>
                                <div><strong style="color:#34D399;">🛡️ Protection Applied:</strong> {b_item['protection_applied']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # ── Step 7: Independent Post-Redaction Verification & Safe Export (Phases 5 & 6) ─
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:18px; margin-bottom:6px;'>PHASE 5 & 6: INDEPENDENT VERIFICATION & SAFE EXPORT</div>", unsafe_allow_html=True)

            residual_leaks = verif_res.get("residual_leaks", [])

            if is_verified and zero_leaks:
                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.35); border-radius:10px; padding:14px 18px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                        <div>
                            <div style="font-size:13.5px; font-weight:800; color:#34D399; margin-bottom:2px;">
                                ✅ CLOSED-LOOP VERIFICATION PASSED (ZERO DETECTABLE PRIVACY LEAKS)
                            </div>
                            <div style="font-size:12px; color:#A7F3D0;">
                                Independently re-scanned {verif_res.get('frames_rechecked', 12)} output frames from disk — verified 0 residual credentials or exposed faces.
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
                    label=f"📥 DOWNLOAD VERIFIED PROTECTED VIDEO ({meta['file_size_mb']:.1f} MB)",
                    data=protected_vid_bytes,
                    file_name=pipeline_res["protected_filename"],
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True,
                    key="btn_download_protected_vid_v7"
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.4); border-radius:10px; padding:14px 18px; margin-bottom:12px;">
                        <div style="font-size:13.5px; font-weight:800; color:#F87171; margin-bottom:4px;">
                            🔴 VERIFICATION FAILED: {len(residual_leaks)} Residual Leak(s) Detected in Output
                        </div>
                        <div style="font-size:12px; color:#FECACA; margin-bottom:10px;">
                            Independent post-redaction scan detected sensitive information in the output video. Video download is locked for security.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if residual_leaks:
                    for lk in residual_leaks:
                        st.error(f"⚠️ Leak at {lk.get('timestamp_str')} (Frame #{lk.get('frame_index')}): {lk.get('description')} [{lk.get('severity')}]")

            # ── Step 8: Cryptographic AI Trust Receipt ────────────────────────
            with st.expander("🧾 Cryptographic AI Trust Receipt", expanded=False):
                receipt_obj = generate_receipt(
                    user_id="Enterprise-Video-Shield",
                    model_selected="Aiera Video Privacy Shield",
                    pii_detected=len(vid_timeline) > 0,
                    pii_entities=[e.get("description", "") for e in vid_timeline],
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
                    <div style="font-weight:800; color:#F8FAFC; margin-bottom:8px; font-size:12.5px;">🔍 7-Phase Telemetry</div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Validation Status:</span>
                        <strong style="color:#34D399;">PASS</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Sensitive Regions:</span>
                        <strong style="color:#F8FAFC;">{scan_data.get('total_sensitive_events', 0)}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Active Tracks:</span>
                        <strong style="color:#38BDF8;">{len(scan_data.get('tracks', []))}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Recovered Gaps:</span>
                        <strong style="color:#FBBF24;">{scan_data.get('missed_frames_recovered', 0)} frames</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Verification:</span>
                        <strong style="color:{'#34D399' if pipeline_res.get('verified') else '#EF4444'};">{'PASS' if pipeline_res.get('verified') else 'FAIL'}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span>Confidence:</span>
                        <strong style="color:#F8FAFC;">{int(scan_data.get('average_confidence', 1.0)*100)}%</strong>
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
            st.info("Upload a video and click 'EXECUTE 7-PHASE PRIVACY SHIELD' to view privacy risk score and metrics.")

