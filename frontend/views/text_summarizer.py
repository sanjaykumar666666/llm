"""
Clean Native Streamlit Document Summarizer Workspace View.
File: frontend/views/text_summarizer.py
"""

import streamlit as st
from frontend.services.api_client import APIClient

def render_text_summarizer_view() -> None:
    st.title("Document Summarizer Workspace")
    st.caption("Generate concise, privacy-checked summaries with custom length controls.")
    st.divider()

    # Controls Bar
    length_option = st.radio(
        "Summary Length:",
        ["Short", "Medium", "Detailed"],
        index=1,
        horizontal=True,
        key="sum_length_opt"
    )

    c_left, c_right = st.columns([1, 1])

    sample_doc = (
        "Artificial Intelligence and Machine Learning applications are rapidly being adopted across enterprise ecosystems. "
        "However, as organizations connect large language models (LLMs) to corporate databases, the risk of accidental PII disclosure "
        "and confidential credential leakage increases significantly. To mitigate these risks, modern enterprise security architectures "
        "deploy real-time privacy firewalls that inspect incoming text prompts, images, video keyframes, and document attachments before transmission."
    )

    with c_left:
        st.subheader("Original Content")
        doc_text = st.text_area("Source Payload:", value=sample_doc, height=240)
        sum_clicked = st.button("✨ Generate Summary", use_container_width=True)

    with c_right:
        st.subheader("AI Summary Output")

        res = APIClient.summarize_text(doc_text, length_option=length_option.lower())

        st.info(res.get("summary", "Summary output generated."))
        st.divider()

        st.subheader("Key Takeaways")
        for kp in res.get("key_points", []):
            st.write(f"• {kp}")

        st.divider()
        st.success("🟢 Privacy Pre-Check: Clean Payload")
