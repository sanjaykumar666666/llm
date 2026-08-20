"""
Clean Native Streamlit Text Analyzer View — Phase 1 Input Layer.
File: frontend/views/text_analyzer.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel


def render_text_analyzer_view() -> None:
    c_main, c_panel = st.columns([2.5, 1])

    with c_main:
        st.header("Text Privacy Editor")
        st.caption("Document editor workspace with entity detection")
        st.divider()

        sample_preset = st.selectbox(
            "Load Test Sample",
            [
                "Aadhaar & Contact Payload (High Risk)",
                "API Secrets & Passwords (High Risk)",
                "Standard Query (Safe)"
            ]
        )

        default_text = "My Aadhaar number is 9918-4019-2011 and my phone number is +91 98765-43210. Email address is john.doe@company.org."
        if sample_preset == "API Secrets & Passwords (High Risk)":
            default_text = "Deploy config: AWS_KEY=AKIAIOSFODNN7EXAMPLE and DB_PASS=SecretAdminPass123!"
        elif sample_preset == "Standard Query (Safe)":
            default_text = "Explain machine learning and privacy firewalls in simple terms."

        input_text = st.text_area("Document Content:", value=default_text, height=180)
        analyze_btn = st.button("🔍 Run Privacy Analysis", use_container_width=True)

        st.divider()
        st.subheader("Document Payload Inspection")
        st.text_area("Inspected Document Text:", value=input_text, height=120, disabled=True)

        # Run analysis for right panel
        if analyze_btn or "text_analysis_res" not in st.session_state:
            analysis_res = APIClient.analyze_text(input_text, mode="REDACT")
            st.session_state["text_analysis_res"] = analysis_res

        res_data = st.session_state.get("text_analysis_res", None)
        if res_data and res_data.get("standardized_input"):
            st.divider()
            st.subheader("Standardized Input Object (Phase 1)")
            st.json(res_data["standardized_input"])

    with c_panel:
        res_data = st.session_state.get("text_analysis_res", None)
        render_live_analysis_panel(res_data)
