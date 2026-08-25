"""
Hero AI Core Command Center View.
File: frontend/views/ai_core.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel

def render_ai_core_view() -> None:
    st.title("AI PRIVACY INTELLIGENCE")
    st.caption("Real-time multimodal privacy protection for Large Language Models.")

    st.divider()

    # Visual Processing Core & Pipeline
    st.subheader("AI PRIVACY CORE")
    st.info("PROCESSING PIPELINE:  INPUT  →  EXTRACTION  →  BERT  →  NAIVE BAYES  →  RISK ENGINE  →  XAI  →  LLM")

    st.divider()

    # Main Analysis Workspace
    st.subheader("SECURE AI INPUT")
    st.caption("Analyze content before it reaches the LLM.")

    modality = st.radio(
        "SELECT INPUT MODALITY:",
        ["TEXT", "IMAGE", "VIDEO", "YOUTUBE"],
        horizontal=True,
        key="ai_core_modality_select"
    )

    if "ai_core_res" not in st.session_state:
        st.session_state["ai_core_res"] = None

    if modality == "TEXT":
        sample_doc = "My Aadhaar number is 9918-4019-2011 and my phone number is +91 98765-43210. Email address is john.doe@company.org."
        input_text = st.text_area(
            "Payload Source Text:",
            value=sample_doc,
            height=120,
            placeholder="Enter or paste content to analyze for privacy risk..."
        )
        if st.button("ANALYZE PRIVACY", use_container_width=True, key="btn_ai_core_text"):
            res = APIClient.analyze_text(input_text, mode="REDACT")
            res["input_text"] = input_text
            st.session_state["ai_core_res"] = res

    elif modality == "IMAGE":
        img_file = st.file_uploader("Upload Image File:", type=["png", "jpg", "jpeg"])
        fname = img_file.name if img_file else "identity_document_scan.jpg"
        st.info(f"Loaded file: {fname}")
        if st.button("ANALYZE PRIVACY", use_container_width=True, key="btn_ai_core_img"):
            res = APIClient.analyze_image(fname, b"")
            res["input_text"] = "DRIVER LICENSE ID: D9910482 ADDRESS: 742 Evergreen Terrace"
            st.session_state["ai_core_res"] = res

    elif modality == "VIDEO":
        vid_file = st.file_uploader("Upload Video File:", type=["mp4", "mov", "avi"])
        vname = vid_file.name if vid_file else "security_presentation.mp4"
        st.info(f"Loaded video: {vname}")
        if st.button("ANALYZE PRIVACY", use_container_width=True, key="btn_ai_core_vid"):
            res = APIClient.analyze_video(vname, b"")
            res["input_text"] = "Exposed DB Connection String: postgres://admin:pass123@db.local:5432"
            st.session_state["ai_core_res"] = res

    elif modality == "YOUTUBE":
        yt_url = st.text_input("YouTube Video URL:", value="https://www.youtube.com/watch?v=demo_tech_talk")
        if st.button("ANALYZE PRIVACY", use_container_width=True, key="btn_ai_core_yt"):
            res = APIClient.analyze_youtube(yt_url)
            res["input_text"] = "[08:45] Spoken Transcript: '...do not leak API key MOCK_KEY_SAMPLE_991823 in public streams...'"
            st.session_state["ai_core_res"] = res

    # Analysis Result Section
    res_data = st.session_state.get("ai_core_res")
    if res_data:
        st.divider()
        st.header("PRIVACY ANALYSIS RESULT")

        c_left, c_right = st.columns([1.3, 1])

        with c_left:
            st.subheader("Inspected Content")
            raw_text = res_data.get("input_text", "")
            st.text_area("Inspected Payload Text:", value=raw_text, height=130, disabled=True)

            if res_data.get("sanitized_text"):
                st.subheader("Sanitized Output")
                st.text_area("Sanitized Payload (Safe for LLM):", value=res_data["sanitized_text"], height=100, disabled=True)

        with c_right:
            render_live_analysis_panel(res_data)

        st.divider()

        st.subheader("RECOMMENDED ACTIONS")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("SANITIZE", use_container_width=True, key="ai_core_san"):
                st.info("Payload sanitized.")
        with b2:
            if st.button("BLOCK", use_container_width=True, key="ai_core_blk"):
                st.error("Request blocked.")
        with b3:
            if st.button("ALLOW", use_container_width=True, key="ai_core_alw"):
                st.success("Override allowed.")
