"""
Clean Native Streamlit Main AI Privacy Analysis Workspace View — Phase 1 Real Inputs.
File: frontend/views/main_analysis.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel


def render_main_analysis_view() -> None:
    st.title("AI Privacy Analysis")
    st.caption("Analyze content before it reaches an LLM.")

    st.divider()

    # Modality Selector
    modality = st.radio(
        "Select Input Modality:",
        ["TEXT", "IMAGE", "VIDEO", "YOUTUBE"],
        horizontal=True,
        key="main_modality_select"
    )

    st.divider()

    if "main_analysis_result" not in st.session_state:
        st.session_state["main_analysis_result"] = None

    if modality == "TEXT":
        sample_doc = "My Aadhaar number is 9918-4019-2011 and my phone number is +91 98765-43210. Email address is john.doe@company.org."
        input_text = st.text_area(
            "Payload Source Text:",
            value=sample_doc,
            height=130,
            placeholder="Enter content to analyze..."
        )
        if st.button("🔍 Analyze Privacy", use_container_width=True, key="btn_main_analyze_text"):
            with st.spinner("Analyzing text..."):
                res = APIClient.analyze_text(input_text, mode="REDACT")
                res["input_text"] = input_text
                st.session_state["main_analysis_result"] = res

    elif modality == "IMAGE":
        img_file = st.file_uploader("Upload Image File:", type=["png", "jpg", "jpeg", "webp", "bmp"])
        if img_file:
            st.info(f"📎 Loaded image: **{img_file.name}** ({img_file.size / 1024:.1f} KB)")
        else:
            st.warning("Please upload an image file to analyze.")

        if st.button("🔍 Analyze Privacy", use_container_width=True, key="btn_main_analyze_img", disabled=not img_file):
            if img_file:
                with st.spinner("Processing image (OCR + PII detection)..."):
                    file_bytes = img_file.read()
                    res = APIClient.analyze_image(img_file.name, file_bytes)

                    # Use real extracted text from OCR
                    extracted = res.get("extracted_text", "") or res.get("ocr_text", "")
                    res["input_text"] = extracted if extracted else "(No text extracted via OCR)"
                    st.session_state["main_analysis_result"] = res

    elif modality == "VIDEO":
        vid_file = st.file_uploader("Upload Video File:", type=["mp4", "mov", "avi", "mkv", "webm"])
        if vid_file:
            st.info(f"📎 Loaded video: **{vid_file.name}** ({vid_file.size / (1024*1024):.1f} MB)")
        else:
            st.warning("Please upload a video file to analyze.")

        if st.button("🔍 Analyze Privacy", use_container_width=True, key="btn_main_analyze_vid", disabled=not vid_file):
            if vid_file:
                with st.spinner("Processing video (frame extraction + OCR)..."):
                    file_bytes = vid_file.read()
                    res = APIClient.analyze_video(vid_file.name, file_bytes)

                    # Use real extracted text from video frames
                    extracted = res.get("extracted_text", "")
                    frames = res.get("frames_processed", 0)
                    duration = res.get("duration_str", "00:00")
                    res["input_text"] = extracted if extracted else f"(No text extracted from {frames} frames, duration: {duration})"
                    st.session_state["main_analysis_result"] = res

    elif modality == "YOUTUBE":
        yt_url = st.text_input("YouTube Video URL:", value="", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("🔍 Analyze Privacy", use_container_width=True, key="btn_main_analyze_yt"):
            if yt_url and yt_url.strip():
                with st.spinner("Extracting YouTube transcript + PII scan..."):
                    res = APIClient.analyze_youtube(yt_url)

                    # Use real transcript text
                    transcript = res.get("transcript_text", "") or res.get("extracted_text", "")
                    res["input_text"] = transcript if transcript else "(No transcript available for this video)"

                    # Show transcript error if any
                    if res.get("transcript_error"):
                        st.warning(f"⚠️ Transcript note: {res['transcript_error']}")

                    st.session_state["main_analysis_result"] = res
            else:
                st.error("Please enter a valid YouTube URL.")

    # ── Analysis Report ──────────────────────────────────────────────────────
    result = st.session_state.get("main_analysis_result")
    if result:
        st.divider()

        # Show validation status if available
        std_input = result.get("standardized_input")
        if std_input:
            status = std_input.get("validation_status", "UNKNOWN")
            if status == "VALID":
                st.success(f"✅ Input Validated — Request ID: `{std_input.get('request_id', 'N/A')}`")
            elif status == "INVALID":
                st.error(f"❌ Input Validation Failed")
                for err in std_input.get("validation_errors", []):
                    st.error(f"  • {err}")
                return

        # Show error responses
        if result.get("status") == "error":
            st.error(f"⚠️ {result.get('error_message', 'Processing failed')}")
            if result.get("validation_errors"):
                for err in result["validation_errors"]:
                    st.error(f"  • {err}")
            return

        st.header("Privacy Analysis Result")

        c_left, c_right = st.columns([1.2, 1])

        with c_left:
            st.subheader("Detected Content")
            raw_text = result.get("input_text", "")
            st.text_area("Extracted Input Text:", value=raw_text, height=130, disabled=True)

            if result.get("sanitized_text"):
                st.subheader("Sanitized Output")
                st.text_area("Sanitized Text (Safe for LLM):", value=result["sanitized_text"], height=100, disabled=True)

            # Show timeline frames for video
            if result.get("timeline_frames"):
                st.subheader("📽️ Video Timeline")
                for frame in result["timeline_frames"][:10]:
                    ts = frame.get("timestamp_str", "00:00")
                    txt = frame.get("extracted_text", "")
                    if txt:
                        st.text(f"  [{ts}] {txt[:100]}")

            # Show transcript segments for YouTube
            if result.get("transcript_segments"):
                st.subheader("📝 Transcript Segments")
                for seg in result["transcript_segments"][:15]:
                    ts = seg.get("timestamp_str", "00:00")
                    txt = seg.get("text", "")
                    if txt:
                        st.text(f"  [{ts}] {txt[:120]}")

        with c_right:
            render_live_analysis_panel(result)

        st.divider()

        st.subheader("Recommended Action")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Sanitize Payload", use_container_width=True, key="main_san"):
                st.info("Sanitized.")
        with b2:
            if st.button("Block Request", use_container_width=True, key="main_blk"):
                st.error("Blocked.")
        with b3:
            if st.button("Allow Override", use_container_width=True, key="main_alw"):
                st.success("Allowed.")

