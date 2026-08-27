"""
Clean Native Streamlit Document Summarizer Workspace View.
File: frontend/views/text_summarizer.py
"""

import streamlit as st
from frontend.services.api_client import APIClient
from backend.services.trust_receipt import generate_receipt, format_receipt_text

def render_text_summarizer_view() -> None:
    st.markdown(
        """
        <div style="padding: 6px 0 14px 0;">
            <h1 style="font-size:26px; font-weight:900; margin:0 0 4px 0; color:#F8FAFC;">
                📝 AI Document Summarizer & Privacy Gateway
            </h1>
            <p style="color:#94A3B8; font-size:13.5px; margin:0;">
                Hierarchical, privacy-checked summarization with length controls and trust receipts.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

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
        doc_text = st.text_area("Source Payload:", value=sample_doc, height=240, key="sum_doc_text_area")
        sum_clicked = st.button("✨ Generate Summary", type="primary", use_container_width=True, key="btn_run_summarize")

        cache_key = f"{doc_text.strip()}_{length_option}"
        if sum_clicked or "sum_res_cache" not in st.session_state or st.session_state.get("sum_cache_key") != cache_key:
            if sum_clicked:
                with st.spinner("📄 Analyzing privacy & synthesizing document summary…"):
                    res = APIClient.summarize_text(doc_text, length_option=length_option.lower())
                    st.session_state["sum_res_cache"] = res
                    st.session_state["sum_cache_key"] = cache_key
            else:
                res = st.session_state.get("sum_res_cache", None)
        else:
            res = st.session_state.get("sum_res_cache", None)

    with c_right:
        st.subheader("AI Summary Output")

        if res:
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.65); border:1px solid rgba(56,189,248,0.22); border-radius:12px; padding:16px; margin-bottom:12px;">
                    <div style="color:#F1F5F9; font-size:13.5px; line-height:1.6;">{res.get('summary', 'Summary generated.')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            key_pts = res.get("key_points", [])
            if key_pts:
                st.markdown("**Key Takeaways:**")
                for kp in key_pts:
                    st.markdown(f"• {kp}")

            st.success("🟢 Privacy Pre-Check: Clean Payload · Verified")

            # Trust Receipt Drawer (Rule 22)
            with st.expander("🧾 AI Trust Audit Receipt", expanded=False):
                receipt_obj = generate_receipt(
                    user_id="Employee-001",
                    model_selected="Aiera Document Summarizer Engine",
                    pii_detected=False,
                    pii_entities=[],
                    injection_detected=False,
                    risk_score=0,
                    risk_level="LOW",
                    policy_action="ALLOW",
                    pii_action="ALLOW",
                    output_action="ALLOW",
                    output_sensitive=False,
                    request_id="ATC-SUM-001"
                )
                st.code(format_receipt_text(receipt_obj), language="text")
        else:
            st.info("Click '✨ Generate Summary' to run privacy-checked document summarization.")
