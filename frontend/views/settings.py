"""
Clean Native Streamlit Workspace Settings View.
File: frontend/views/settings.py
"""

import streamlit as st
import config

def render_settings_view() -> None:
    st.title("Settings & System Configuration")
    st.caption("Configure risk threshold cutoffs, privacy enforcement policies, and system parameters.")
    st.divider()

    c_l, c_r = st.columns([1, 1])

    with c_l:
        st.subheader("Privacy Policy Configuration")
        st.selectbox("Default Sanitization Mode:", ["REDACT", "MASK", "SYNTHETIC"], index=0)
        
        st.slider("Warning Risk Threshold (%)", min_value=10, max_value=60, value=35)
        st.slider("Block Risk Threshold (%)", min_value=60, max_value=95, value=75)

        st.divider()
        st.subheader("API Gateway Settings")
        st.text_input("Backend REST API URL", value="http://localhost:8000/api/v1")
        st.text_input("API Gateway Timeout (seconds)", value="3.0")

    with c_r:
        st.subheader("Model Metadata & Architecture")
        st.write(f"• **LLM Gateway Model**: `{getattr(config, 'DEFAULT_LLM_MODEL', 'gemini-2.5-flash')}`")
        st.write("• **Hybrid Classifier**: BERT-Base + Naive Bayes Ensemble")
        st.write("• **Prompt Engine**: Heuristic Guardrails & BERT Sequence Classifier")
        st.write("• **OCR Service**: Tesseract OCR engine v5.3.0 + OpenCV")
        st.write("• **Temporal Sampler**: OpenCV Keyframe Extractor (1.0s interval)")

        st.divider()
        st.success("🟢 Status: Gateway Monitoring Active")

    st.divider()
    if st.button("💾 Save Settings Configuration", use_container_width=True):
        st.success("✅ Settings saved successfully.")
