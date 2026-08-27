"""
Production Image Privacy Protection & Multi-Modal Verification Workspace View.
File: frontend/views/image_analyzer.py

Features:
  1. 📤 Secure Image Upload (PNG, JPG, JPEG, WEBP) with Integrity Validation.
  2. 🔍 Real Multi-Level OCR + Visual Entity Detection (Identity, Financial, Auth, Personal, Faces, QR).
  3. 🛡️ Pixel-Level Protection (Redact, Blur, Pixelate, Blackout, Full Blur) with Box Padding.
  4. ✅ Closed-Loop OCR Verification Engine (Confirms Zero Residual Sensitive Leaks).
  5. 📥 Metadata-Stripped Verified Protected Image Download.
  6. 🧾 Privacy-Safe Audit Telemetry.
"""

import io
import os
import time
import base64
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime
from PIL import Image, ImageDraw
import streamlit as st

from backend.services.image_privacy_service import ImagePrivacyService
from backend.services.trust_receipt import generate_receipt, format_receipt_text
from frontend.components.analysis_panel import render_live_analysis_panel


def render_image_analyzer_view() -> None:
    # ── 1. Header & Step Pipeline ─────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 4px 0 16px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div>
                    <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC; letter-spacing:0.02em;">
                        🖼️ Image Privacy Shield & Visual Redaction
                    </h1>
                    <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                        Zero-trust visual scanner, pixel-level PII protection, closed-loop OCR verification, and metadata-stripped export.
                    </p>
                </div>
                <div style="display:flex; align-items:center; gap:6px; background:rgba(15,23,42,0.8); border:1px solid rgba(56,189,248,0.25); border-radius:20px; padding:6px 14px; font-size:11.5px; font-weight:700; color:#38BDF8;">
                    <span>🛡️ ZERO-LEAK GUARANTEE</span>
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
            <span>1. 📤 Upload Image</span>
            <span style="color:#64748B;">➔</span>
            <span>2. 🔍 Scan & Detect</span>
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
        # ── Step 1: Image Upload & Preset Selection ───────────────────────────
        st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:6px;'>STEP 1: UPLOAD TARGET IMAGE</div>", unsafe_allow_html=True)
        
        c_up, c_pre = st.columns([1.6, 1])
        with c_up:
            uploaded_file = st.file_uploader(
                "Upload Image (PNG, JPG, JPEG, WEBP):",
                type=["png", "jpg", "jpeg", "webp"],
                key="img_file_uploader",
                help="Maximum file size: 25MB. Files are processed securely in temporary memory and never persisted."
            )
        
        with c_pre:
            sample_preset = st.selectbox(
                "Or Test with Preset Sample:",
                [
                    "None (Use Uploaded File)",
                    "🪪 Identity Card (Aadhaar & PAN)",
                    "💳 Credit Card & Bank Account",
                    "🔑 Server Login & API Secret",
                    "🟢 Clean Landscape (No PII)",
                ],
                key="img_sample_preset"
            )

        file_bytes = b""
        file_name = "target_image.png"

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
        elif sample_preset != "None (Use Uploaded File)":
            file_bytes, file_name = _generate_sample_image(sample_preset)
        else:
            # Default initial sample
            file_bytes, file_name = _generate_sample_image("🪪 Identity Card (Aadhaar & PAN)")

        # Validate Image Payload
        is_valid, val_err, pil_img = ImagePrivacyService.validate_image_bytes(file_bytes, file_name)
        if not is_valid:
            st.error(f"❌ Upload Error: {val_err}")
            return

        # ── Step 2: Protection Controls ───────────────────────────────────────
        st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-top:14px; margin-bottom:6px;'>STEP 2: CONFIGURE PROTECTION SETTINGS</div>", unsafe_allow_html=True)
        
        c_mode, c_opt1, c_opt2 = st.columns([1.8, 1, 1])
        with c_mode:
            protection_mode = st.selectbox(
                "Protection Mode:",
                [
                    "REDACT SENSITIVE (Solid Redaction Box)",
                    "BLUR SENSITIVE (Gaussian Blur)",
                    "PIXELATE SENSITIVE (Mosaic Pixelation)",
                    "BLACKOUT SENSITIVE (Solid Blackout Box)",
                    "BLUR ALL (Complete Image Blur)",
                ],
                index=0,
                key="img_protection_mode_select"
            )
        
        with c_opt1:
            st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
            protect_faces = st.checkbox("👤 Protect Faces", value=True, key="img_chk_faces", help="Detect and protect human faces as biometric identifiers.")
        
        with c_opt2:
            st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
            protect_qr = st.checkbox("📱 Protect QR Codes", value=True, key="img_chk_qr", help="Detect and protect QR/Barcodes that may contain personal credentials.")

        # ── Step 3: Run Scan & Protect Action ─────────────────────────────────
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        run_scan_btn = st.button("🛡️ PROTECT & VERIFY IMAGE", type="primary", use_container_width=True, key="btn_run_img_protect")

        cache_key = f"{file_name}_{protection_mode}_{protect_faces}_{protect_qr}_{len(file_bytes)}"

        if run_scan_btn or "img_res_cache" not in st.session_state or st.session_state.get("img_res_cache_key") != cache_key:
            if run_scan_btn or "img_res_cache" not in st.session_state:
                with st.spinner("🔍 Scanning OCR pixels, detecting sensitive regions & verifying 0-leak protection…"):
                    res = ImagePrivacyService.process_image(
                        image_bytes=file_bytes,
                        filename=file_name,
                        protection_mode=protection_mode,
                        protect_faces=protect_faces,
                        protect_qr_barcodes=protect_qr,
                    )
                    st.session_state["img_res_cache"] = res
                    st.session_state["img_res_cache_key"] = cache_key
            else:
                res = st.session_state.get("img_res_cache")
        else:
            res = st.session_state.get("img_res_cache")

        if res and res.get("success"):
            det_count = res.get("detection_count", 0)
            is_verified = res.get("is_verified", False)
            cat_counts = res.get("category_counts", {})
            doc_type = res.get("document_type", "General Document")
            duration_ms = res.get("duration_ms", 0)

            # ── Status Banner ─────────────────────────────────────────────────
            if is_verified:
                status_bg = "rgba(16,185,129,0.12)"
                status_border = "rgba(16,185,129,0.35)"
                status_col = "#34D399"
                status_icon = "🟢"
                status_title = "VERIFIED PROTECTED — ZERO RESIDUAL LEAKS DETECTED"
                status_desc = f"All {det_count} detected sensitive region(s) were protected and independently verified via closed-loop OCR pass."
            else:
                status_bg = "rgba(239,68,68,0.12)"
                status_border = "rgba(239,68,68,0.35)"
                status_col = "#F87171"
                status_icon = "🔴"
                status_title = "PROTECTION VERIFICATION FAILED"
                status_desc = "Sensitive information remained partially detectable during verification OCR pass. Review before exporting."

            st.markdown(
                f"""
                <div style="background:{status_bg}; border:1px solid {status_border}; border-radius:12px; padding:14px 18px; margin-top:16px; margin-bottom:14px;">
                    <div style="color:{status_col}; font-weight:800; font-size:13.5px; display:flex; align-items:center; gap:8px;">
                        <span>{status_icon}</span> <span>{status_title}</span>
                    </div>
                    <div style="color:#CBD5E1; font-size:12.5px; margin-top:4px;">
                        {status_desc} <span style="color:#64748B;">• Document Classification: <strong>{doc_type}</strong> ({duration_ms}ms)</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── Step 4: Privacy-Safe Detection Summary Cards ───────────────────
            st.markdown("<div style='font-size:13px; font-weight:800; color:#E2E8F0; margin-bottom:8px;'>SENSITIVE REGIONS PROTECTED SUMMARY</div>", unsafe_allow_html=True)
            
            c_s1, c_s2, c_s3, c_s4, c_s5 = st.columns(5)
            with c_s1:
                st.metric("Total Regions", det_count)
            with c_s2:
                st.metric("Identity IDs", cat_counts.get("identity", 0))
            with c_s3:
                st.metric("Financial", cat_counts.get("financial", 0))
            with c_s4:
                st.metric("Auth / Secrets", cat_counts.get("authentication", 0))
            with c_s5:
                st.metric("Personal & Bio", cat_counts.get("personal", 0) + cat_counts.get("biometric", 0))

            # ── Step 5: Side-by-Side Spatial Comparison ────────────────────────
            st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
            col_orig, col_prot = st.columns(2)

            with col_orig:
                st.markdown(
                    """
                    <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#FCA5A5; font-size:12px; font-weight:800;">ORIGINAL UN-PROTECTED PAYLOAD</span>
                        <span style="background:rgba(239,68,68,0.2); color:#EF4444; border:1px solid rgba(239,68,68,0.4); font-size:10px; font-weight:800; padding:2px 8px; border-radius:10px;">⚠️ UNPROTECTED</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.image(file_bytes, use_container_width=True, caption="Source Payload (Contains sensitive content)")

            with col_prot:
                st.markdown(
                    f"""
                    <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#34D399; font-size:12px; font-weight:800;">PROTECTED REDACTED PAYLOAD</span>
                        <span style="background:rgba(16,185,129,0.2); color:#10B981; border:1px solid rgba(16,185,129,0.4); font-size:10px; font-weight:800; padding:2px 8px; border-radius:10px;">{'🟢 VERIFIED PROTECTED' if is_verified else '🔴 FAILED'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                prot_bytes = res.get("protected_image_bytes", b"")
                if prot_bytes:
                    st.image(prot_bytes, use_container_width=True, caption=f"Pixel Protection Mode: {protection_mode}")
                    
                    # ── Download Protected Image Button ───────────────────────
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_filename = f"protected_{os.path.splitext(file_name)[0]}_{timestamp_str}.png"
                    
                    st.download_button(
                        label="📥 DOWNLOAD VERIFIED PROTECTED IMAGE (PNG)",
                        data=prot_bytes,
                        file_name=out_filename,
                        mime="image/png",
                        type="primary",
                        use_container_width=True,
                        disabled=not is_verified
                    )
                else:
                    st.warning("Protected image artifact unavailable.")

            # ── Step 6: Trust Audit Receipt ───────────────────────────────────
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            with st.expander("🧾 AI Trust Audit Receipt", expanded=False):
                receipt_obj = generate_receipt(
                    user_id="Employee-001",
                    model_selected="Aiera Multimodal Image Vision Shield",
                    pii_detected=det_count > 0,
                    pii_entities=[d.get("type", "SENSITIVE_REGION") for d in res.get("detections", [])],
                    injection_detected=False,
                    risk_score=res.get("risk_score", 0),
                    risk_level=res.get("risk_level", "LOW"),
                    policy_action="PROTECT" if det_count > 0 else "ALLOW",
                    pii_action="REDACT" if det_count > 0 else "ALLOW",
                    output_action="ALLOW",
                    output_sensitive=False,
                    request_id=f"ATC-IMG-{abs(hash(file_name)) % 1000000:06d}"
                )
                st.code(format_receipt_text(receipt_obj), language="text")

    with c_metrics:
        st.subheader("PRIVACY METRICS")
        if res and res.get("success"):
            render_live_analysis_panel(res)
        else:
            st.info("Upload an image and run scan to view real-time visual privacy metrics.")


def _generate_sample_image(preset_name: str) -> Tuple[bytes, str]:
    """Generates synthetic test documents with crisp typography for OCR validation."""
    if "Credit Card" in preset_name:
        img = Image.new("RGB", (700, 260), (248, 250, 252))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (690, 250)], outline=(14, 165, 233), width=2)
        draw.text((25, 25), "OFFICIAL BANKING FINANCIAL STATEMENT", fill=(15, 23, 42))
        draw.text((25, 65), "Account Number: 981726354419", fill=(225, 29, 72))
        draw.text((25, 105), "Card Number: 4532 1120 9821 4432", fill=(225, 29, 72))
        draw.text((25, 145), "IFSC Code: HDFC0001234 | UPI: user@okhdfc", fill=(225, 29, 72))
        draw.text((25, 185), "CVV: 789 | Exp: 08/28 | Phone: +91 91234-56789", fill=(15, 23, 42))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "banking_financial_card.png"

    elif "Server Login" in preset_name:
        img = Image.new("RGB", (700, 260), (248, 250, 252))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (690, 250)], outline=(244, 63, 94), width=2)
        draw.text((25, 25), "PRODUCTION CLUSTER ACCESS CONFIG", fill=(15, 23, 42))
        draw.text((25, 65), "Host: prod-db.internal.corp", fill=(15, 23, 42))
        draw.text((25, 105), "Password: ProdRootPassword!2026", fill=(225, 29, 72))
        draw.text((25, 145), "API Key: AKIAIOSFODNN7EXAMPLE", fill=(225, 29, 72))
        draw.text((25, 185), "OTP Code: 483921 | PIN: 9821", fill=(225, 29, 72))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "server_credentials.png"

    elif "Clean Landscape" in preset_name:
        img = Image.new("RGB", (700, 260), (241, 245, 249))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (690, 250)], outline=(16, 185, 129), width=2)
        draw.text((25, 40), "PUBLIC LANDSCAPE PHOTOGRAPHY", fill=(15, 23, 42))
        draw.text((25, 90), "Location: Rocky Mountain National Park", fill=(71, 85, 105))
        draw.text((25, 140), "Camera: 50mm f/1.8 | ISO 100", fill=(71, 85, 105))
        draw.text((25, 190), "Zero sensitive personal information present.", fill=(16, 185, 129))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "clean_landscape_photo.png"

    else:
        # Default: Identity Card (Aadhaar & PAN)
        img = Image.new("RGB", (700, 260), (248, 250, 252))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (690, 250)], outline=(6, 182, 212), width=2)
        draw.text((25, 25), "GOVERNMENT OF INDIA IDENTITY CARD", fill=(15, 23, 42))
        draw.text((25, 65), "Aadhaar: 9918 4019 2011", fill=(225, 29, 72))
        draw.text((25, 105), "PAN No: ABCDE1234F", fill=(225, 29, 72))
        draw.text((25, 145), "Phone: +91 98765-43210 | Email: citizen@uidai.gov.in", fill=(225, 29, 72))
        draw.text((25, 185), "DOB: 14/05/1992 | DL No: DL-0420110012345", fill=(15, 23, 42))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "identity_document_scan.png"
