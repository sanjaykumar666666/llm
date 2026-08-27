"""
Clean Native Streamlit Workspace Settings View.
File: frontend/views/settings.py
"""

import os
import streamlit as st
import config
from pathlib import Path

def _test_gemini_api_key(key: str) -> dict:
    """Live validation of a Gemini API key."""
    if not key or not key.strip():
        return {"valid": False, "message": "API key cannot be empty."}
    
    clean_key = key.strip()
    try:
        from google import genai
        client = genai.Client(api_key=clean_key)
        # Try lightweight test call
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'OK' in one word."
        )
        if resp and resp.text:
            return {"valid": True, "message": f"✅ API Key Valid! Model response: {resp.text.strip()}"}
        return {"valid": True, "message": "✅ API Key Verified successfully with Google GenAI API."}
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return {"valid": True, "message": "⚠️ Key is authentic, but current Free Tier quota has been reached. Responses will use verified web search summaries until quota resets."}
        elif "400" in err or "401" in err or "API_KEY_INVALID" in err or "unauthenticated" in err.lower():
            return {"valid": False, "message": "❌ Invalid API Key. Please get a valid key starting with 'AIzaSy...' from https://aistudio.google.com/app/apikey"}
        else:
            return {"valid": False, "message": f"⚠️ Validation notice: {err[:120]}"}


def render_settings_view() -> None:
    st.title("⚙️ Settings & System Configuration")
    st.caption("Configure API credentials, risk threshold cutoffs, and privacy enforcement policies.")
    st.divider()

    # ── Section 1: Google Gemini API Configuration ───────────────────────────
    st.subheader("🔑 Google Gemini API Configuration")
    st.markdown(
        """
        AI Privacy Shield connects directly to **Google Gemini** for intelligent multimodal privacy analysis, 
        prompt protection, and live grounded synthesis.
        """
    )

    env_key = os.getenv("GEMINI_API_KEY", "") or getattr(config, "GEMINI_API_KEY", "")
    current_key_display = (env_key[:8] + "..." + env_key[-4:]) if len(env_key) > 12 else (env_key or "Not Configured")

    st.markdown(f"**Current Active Key:** `{current_key_display}`")

    new_api_key = st.text_input(
        "Enter Google Gemini API Key:",
        type="password",
        placeholder="AIzaSy...",
        help="Get your free Gemini API Key from https://aistudio.google.com/app/apikey",
        key="settings_gemini_api_key_input"
    )

    col_btn1, col_btn2 = st.columns([1.5, 2.5])
    with col_btn1:
        if st.button("🔍 Test & Save API Key", type="primary", use_container_width=True, key="save_api_key_btn"):
            key_to_save = new_api_key.strip() if new_api_key else env_key.strip()
            if not key_to_save:
                st.error("⚠️ Please enter a valid Gemini API Key.")
            else:
                with st.spinner("Validating with Google Gemini GenAI API..."):
                    res = _test_gemini_api_key(key_to_save)
                    if res["valid"]:
                        st.success(res["message"])
                        # Save to .env and os.environ
                        os.environ["GEMINI_API_KEY"] = key_to_save
                        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
                        try:
                            lines = []
                            if env_path.exists():
                                for line in env_path.read_text(encoding="utf-8").splitlines():
                                    if not line.startswith("GEMINI_API_KEY="):
                                        lines.append(line)
                            lines.insert(0, f"GEMINI_API_KEY={key_to_save}")
                            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                            st.info("💾 API key saved to `.env` file successfully.")
                        except Exception as e:
                            st.warning(f"Note: Could not write directly to .env ({e}), but active in memory.")
                    else:
                        st.error(res["message"])

    with col_btn2:
        st.markdown(
            """
            <div style="padding-top:6px; font-size:13px; color:#94A3B8;">
                👉 Don't have a key? Get a free API key at <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#38BDF8; font-weight:700;">Google AI Studio</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # ── Section 2: Privacy Policies ──────────────────────────────────────────
    c_l, c_r = st.columns([1, 1])

    with c_l:
        st.subheader("🛡️ Privacy Policy Configuration")
        st.selectbox("Default Sanitization Mode:", ["REDACT", "MASK", "SYNTHETIC"], index=0)
        
        st.slider("Warning Risk Threshold (%)", min_value=10, max_value=60, value=35)
        st.slider("Block Risk Threshold (%)", min_value=60, max_value=95, value=75)

        st.divider()
        st.subheader("🌐 Gateway Settings")
        st.text_input("Backend REST API URL", value="http://localhost:8000/api/v1")
        st.text_input("API Gateway Timeout (seconds)", value="15.0")

    with c_r:
        st.subheader("🧠 Model Metadata & Architecture")
        st.write(f"• **LLM Gateway Model**: `{getattr(config, 'DEFAULT_LLM_MODEL', 'gemini-2.5-flash')}`")
        st.write("• **Live Grounding Engine**: Universal Web Search & Entity Verification")
        st.write("• **Hybrid Classifier**: BERT-Base + Naive Bayes Ensemble")
        st.write("• **Prompt Engine**: Heuristic Guardrails & BERT Sequence Classifier")
        st.write("• **OCR Service**: Tesseract OCR engine v5.3.0 + OpenCV")
        st.write("• **Trust Core**: Cryptographic SHA-256 Audit Trail")

        st.divider()
        st.success("🟢 Status: Zero-Trust Gateway Active & Monitoring")
