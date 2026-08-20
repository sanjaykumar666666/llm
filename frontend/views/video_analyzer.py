"""
Clean Native Streamlit Video Privacy Workspace View — Phase 1 Input Layer.
File: frontend/views/video_analyzer.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel


def render_video_analyzer_view() -> None:
    c_main, c_panel = st.columns([2.5, 1])

    with c_main:
        st.header("Video Frame Investigation")
        st.caption("Temporal keyframe sampling and frame-level privacy risk tracking")
        st.divider()

        video_file = st.file_uploader("Upload Video File:", type=["mp4", "mov", "avi", "mkv", "webm"])

        if video_file is not None:
            st.video(video_file)
            file_bytes = video_file.getvalue()
            file_name = video_file.name
            st.info(f"📎 Loaded Video: **{file_name}** ({len(file_bytes) / (1024*1024):.2f} MB)")
            vid_res = APIClient.analyze_video(file_name, file_bytes)
        else:
            st.info("ℹ️ Upload a video above to inspect keyframes and analyze privacy risk.")
            # Default placeholder state
            vid_res = {
                "risk_score": 0,
                "status": "AWAITING_INPUT",
                "action": "ALLOW",
                "risk_level": "LOW",
                "detected_entities": [],
                "detected_risks": [],
                "evidence": ["Waiting for video upload..."],
                "reason": "Please upload a video file to begin analysis.",
                "why_bullets": ["✓ No file uploaded yet."],
            }

        st.divider()
        st.subheader("Video Timeline & Risk Markers")

        timeline = vid_res.get("timeline_frames", [])
        if timeline:
            for frame in timeline:
                ts = frame.get("timestamp_str", "00:00")
                txt = frame.get("extracted_text", "")
                if txt:
                    st.write(f"• **{ts}** — {txt}")
        else:
            st.caption("Timeline frames will appear here after video processing.")

        std_inp = vid_res.get("standardized_input")
        if std_inp:
            st.divider()
            st.subheader("Standardized Input Object (Phase 1)")
            st.json(std_inp)

    with c_panel:
        render_live_analysis_panel(vid_res)
