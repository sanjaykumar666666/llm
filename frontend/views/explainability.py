"""
Clean Native Streamlit AI Explainability Workspace View.
File: frontend/views/explainability.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from frontend.components.analysis_panel import render_live_analysis_panel

def render_explainability_view() -> None:
    c_main, c_panel = st.columns([2.5, 1])

    with c_main:
        st.header("AI Explainability Workspace")
        st.caption("Research-level model feature weight attribution and privacy explanation")
        st.divider()

        exp_data = APIClient.get_explainability("Text")

        # Tabs: Overview, Feature Importance, Privacy, Why This?
        tab_over, tab_feat, tab_priv, tab_why = st.tabs([
            "Overview",
            "Feature Importance",
            "Privacy Breakdown",
            "Why This?"
        ])

        with tab_over:
            st.subheader("Evaluation Summary")
            st.write(exp_data.get("affected_features", "High-risk PII entities detected."))

        with tab_feat:
            st.subheader("Original Input & Key Features")
            raw_doc = "My Aadhaar number is 9918-4019-2011 and my phone number is +91 98765-43210. Email address is john.doe@company.org."
            st.text_area("Extracted Input Text:", value=raw_doc, height=90, disabled=True)

            st.divider()
            st.subheader("Feature Contribution")

            contribs = exp_data.get("feature_contributions", [
                {"type": "Supporting", "feature": "Personal Information", "weight": 0.1513, "is_risk": False},
                {"type": "Supporting", "feature": "Phone Number", "weight": 0.1483, "is_risk": False},
                {"type": "Risk Factor", "feature": "Credential Information", "weight": 0.1022, "is_risk": True}
            ])

            for item in contribs:
                w = item.get("weight", 0.1)
                st.progress(min(w * 5, 1.0), text=f"{item.get('feature')} (+{w:.4f})")

        with tab_priv:
            st.subheader("Privacy Breakdown Matrix")
            st.write("**Personal Information:** High Risk")
            st.write("**Credentials:** High Risk")
            st.write("**Financial Content:** Medium Risk")
            st.write("**Confidential Data:** Low Risk")

        with tab_why:
            st.subheader("Why Was This Input Flagged?")
            st.write(exp_data.get("why_explanation", "Input contains sensitive personal and credential information."))

    with c_panel:
        render_live_analysis_panel(exp_data)
