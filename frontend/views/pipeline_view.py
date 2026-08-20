"""
Aiera AI — Multimodal Architecture & Pipeline Inspection View.
File: frontend/views/pipeline_view.py
"""

import streamlit as st


def render_pipeline_view() -> None:
    st.markdown(
        """
        <div style="padding: 10px 0 18px 0;">
            <h1 style="color:#0F172A; font-size:28px; font-weight:900; margin:0 0 6px 0;">
                🏗️ Multimodal Privacy Pipeline & Architecture
            </h1>
            <p style="color:#475569; font-size:14px; font-weight:500; margin:0;">
                Deep technical inspection of the hybrid neural, probabilistic, and zero-trust security stages.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # ── PIPELINE STEPPER ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(56,189,248,0.25); border-radius:14px; padding:18px 20px; box-shadow:0 4px 16px rgba(0,0,0,0.3); margin-bottom:20px;">
            <div style="color:#38BDF8; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:14px;">End-to-End Pipeline Stages</div>
            <div style="display:flex; align-items:center; justify-content:space-between; overflow-x:auto; gap:8px; padding-bottom:8px;">
                <div style="display:flex; flex-direction:column; align-items:center; min-width:70px;">
                    <div style="background:#1E293B; border:1px solid #38BDF8; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">💻</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px;">1. Input</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:85px;">
                    <div style="background:#1E293B; border:1px solid #38BDF8; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">⚙️</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">2. Preprocess</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:95px;">
                    <div style="background:#1E293B; border:1px solid #38BDF8; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">🔍</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">3. Detection</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:105px;">
                    <div style="background:#1E293B; border:1px solid #A855F7; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">🧠</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">4. Hybrid AI<br>(BERT + NB)</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:85px;">
                    <div style="background:#1E293B; border:1px solid #F59E0B; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">⚖️</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">5. Risk Engine</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:95px;">
                    <div style="background:#1E293B; border:1px solid #10B981; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">🛡️</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">6. Protection</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:90px;">
                    <div style="background:#1E293B; border:1px solid #06B6D4; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">☁️</div>
                    <span style="color:#F8FAFC; font-size:11px; font-weight:700; margin-top:6px; text-align:center;">7. Secure LLM</span>
                </div>
                <div style="color:#64748B; font-size:16px; font-weight:900;">➔</div>
                <div style="display:flex; flex-direction:column; align-items:center; min-width:95px;">
                    <span style="background:rgba(16,185,129,0.2); color:#10B981; border:1px solid #10B981; font-size:11px; font-weight:800; padding:8px 12px; border-radius:10px; text-align:center;">
                        8. Output
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── STAGE BREAKDOWNS IN TABS ──────────────────────────────────────────────
    t_stage1, t_stage2, t_stage3, t_stage4 = st.tabs([
        "1. Detection & Extraction",
        "2. Hybrid Machine Learning",
        "3. Risk & Decision Engine",
        "4. Cryptographic Trust Receipts"
    ])

    with t_stage1:
        st.subheader("Stage 1 & 2: Multimodal Ingestion & Context Detection")
        st.write(
            """
            - **Text Ingestion**: Tokenizes inputs, cleans whitespace, strips invisible zero-width unicode characters.
            - **Presidio & Pattern Matcher**: Recognizes Aadhaar numbers, PAN, credit cards, emails, phone numbers, and API tokens.
            - **OCR Engine**: Tesseract + EasyOCR for image text extraction.
            - **Video Frame Sampler**: Keyframe extraction at 1 FPS with OpenCV facial landmark detection.
            """
        )

    with t_stage2:
        st.subheader("Stage 3 & 4: Hybrid Neural & Probabilistic Ensemble")
        st.write(
            """
            - **DistilBERT Transformer**: Fine-tuned on privacy risk datasets to capture semantic context and subtle adversarial framing.
            - **Multinomial Naive Bayes**: High-speed token frequency baseline for known entity patterns.
            - **Ensemble Fusion**: Weighted probability merge providing fast, robust predictions ($43\text{ms}$ execution latency).
            """
        )

    with t_stage3:
        st.subheader("Stage 5 & 6: Mathematical Risk Scoring & Policy Decision")
        st.write(
            """
            - **Risk Formula**: Combines Base ML Score, Entity Sensitivity Weights, Severity Penalties, and Context Multipliers ($0–100$).
            - **Policy Gateway Actions**:
              - `ALLOW (0–30)`: Transmits to LLM Gateway unmodified.
              - `SANITIZE (31–75)`: Masks sensitive tokens with `[REDACTED]` tags.
              - `BLOCK (76–100)`: Halts execution immediately; no LLM egress.
            """
        )

    with t_stage4:
        st.subheader("Stage 7 & 8: Cryptographic Receipts & Non-repudiation")
        st.write(
            """
            - **HMAC-SHA256 Signatures**: Each request generates a verifiable trust receipt storing user ID, model used, risk scores, detected entities, and policy action.
            - **Audit Trail**: Dispatched to background async logging for enterprise compliance (GDPR, HIPAA, DPDP).
            """
        )
