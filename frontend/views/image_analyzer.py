"""
Real Automatic Image Privacy Protection & Redaction Workspace View.
File: frontend/views/image_analyzer.py
"""

import base64
import io
import streamlit as st
from PIL import Image
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel

def render_image_analyzer_view() -> None:
    st.title("IMAGE PRIVACY SCAN")
    st.caption("Visual inspection & automatic pixel-level redaction.")
    st.divider()

    c_left, c_right = st.columns([2.2, 1])

    with c_left:
        st.subheader("1. Select Protection Mode & Upload Payload Image")

        mode = st.selectbox(
            "PIXEL REDACTION PROTECTION MODE:",
            ["BLUR_ALL", "PIXELATE_ALL", "REDACT_ALL", "BLUR_FACES", "BLUR_TEXT"],
            index=0,
            key="img_prot_mode"
        )

        uploaded_file = st.file_uploader(
            "Upload Target Image Payload:",
            type=["png", "jpg", "jpeg"],
            key="img_file_uploader"
        )

        file_bytes = b""
        file_name = "identity_document_scan.jpg"

        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
        else:
            # Create default sample image with text payload if no file uploaded yet
            sample_img = Image.new("RGB", (600, 220), (248, 250, 252))
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(sample_img)
            draw.rectangle([(10, 10), (590, 210)], outline=(6, 182, 212), width=2)
            draw.text((25, 25), "GOVERNMENT IDENTITY CARD", fill=(15, 23, 42))
            draw.text((25, 60), "Aadhaar No: 9918-4019-2011", fill=(225, 29, 72))
            draw.text((25, 95), "Phone: +91 98765-43210", fill=(225, 29, 72))
            draw.text((25, 130), "Email: john.doe@company.org", fill=(225, 29, 72))
            draw.text((25, 165), "DOB: 1992-05-14 | DL: D9910482", fill=(15, 23, 42))
            buf = io.BytesIO()
            sample_img.save(buf, format="PNG")
            file_bytes = buf.getvalue()

        st.info(f"📁 Loaded File Payload: {file_name}")

        # Execute Real Privacy Protection Scan
        with st.spinner("SCANNING IMAGE PIXELS FOR PII & FACES..."):
            result = APIClient.analyze_image(file_name, file_bytes, mode)

        st.divider()

        # Check for Scan Success & Fail-Closed Protocol
        if not result.get("success", True):
            st.error("⛔ PRIVACY SCAN FAILED: Fail-Closed Security Enforced. Un-redacted payload blocked from LLM transmission.")
        else:
            st.success("✅ PRIVACY ANALYSIS COMPLETE — Pixel Redaction Protection Applied")

            # 2. ORIGINAL VS PROTECTED COMPARISON INTERFACE
            st.subheader("2. Spatial Image Comparison (Original vs Protected)")

            col_orig, col_prot = st.columns(2)

            with col_orig:
                st.markdown("**ORIGINAL UN-PROTECTED PAYLOAD**")
                st.image(file_bytes, use_container_width=True, caption="Source Upload Payload")

            with col_prot:
                st.markdown("**PROTECTED REDACTED PAYLOAD**")
                prot_b64 = result.get("protected_image_b64", "")
                if prot_b64.startswith("data:image"):
                    # Extract raw base64 data
                    b64_data = prot_b64.split(",")[1]
                    raw_img_bytes = base64.b64decode(b64_data)
                    st.image(raw_img_bytes, use_container_width=True, caption=f"Pixel Protection: {mode}")

                    # Download Protected Image Button
                    st.download_button(
                        label="📥 DOWNLOAD PROTECTED IMAGE",
                        data=raw_img_bytes,
                        file_name=f"protected_{file_name}",
                        mime="image/png",
                        use_container_width=True
                    )
                else:
                    st.warning("Protected image processing complete.")

            st.divider()

            # 3. LLM SAFETY GATE PROTOCOL
            st.info("🛡️ **LLM SAFETY GATE**: Sanitization verified. ONLY the protected redacted image is authorized for downstream LLM gateway processing. The un-redacted original image is strictly quarantined.")

            # 4. OCR EXTRACTED TEXT & SENSITIVE REGIONS DETECTED
            st.subheader("3. Spatial OCR & Sensitive Entity Detections")
            st.write(f"**Extracted OCR Text:** `{result.get('original_ocr_text', 'OCR Stream Scanned.')}`")

            detections = result.get("detections", [])
            if detections:
                st.warning(f"⚠️ Identified {len(detections)} Sensitive PII Regions:")
                for d in detections:
                    st.write(f"• **{d.get('type')}**: `{d.get('value')}` | Bounding Box `[x1,y1,x2,y2]`: `{d.get('bbox')}` (Confidence: `{d.get('confidence')}`)")
            else:
                st.success("✅ Zero sensitive PII regions detected.")

            std_inp = result.get("standardized_input")
            if std_inp:
                st.divider()
                st.subheader("Standardized Input Object (Phase 1)")
                st.json(std_inp)

    with c_right:
        st.subheader("PRIVACY METRICS")
        render_live_analysis_panel(result)

        st.divider()
        st.subheader("Category Breakdown")
        cat_counts = result.get("category_counts", {})
        st.write(f"👤 **Faces**: `{cat_counts.get('faces', 0)}`")
        st.write(f"📄 **Text PII**: `{cat_counts.get('text_pii', 0)}`")
        st.write(f"🆔 **Documents**: `{cat_counts.get('documents', 0)}`")
        st.write(f"📱 **QR/Barcode**: `{cat_counts.get('qr_barcode', 0)}`")
