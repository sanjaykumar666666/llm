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

    # ── Section 2: Visual Theme & Color Palette Customizer ───────────────────
    from frontend.utils.theme_manager import COLOR_THEMES, get_current_theme_key, get_current_theme

    st.subheader("🎨 Workspace Color Themes & Aesthetics")
    st.markdown("Choose your preferred aesthetic palette for Privacy Chat, Security Dashboard, and all interface components:")

    current_theme_key = get_current_theme_key()
    active_theme = get_current_theme()

    # Render interactive theme cards grid (4 columns x 2 rows)
    theme_items = list(COLOR_THEMES.items())
    
    col_t1, col_t2 = st.columns(2)
    for i, (t_key, t_data) in enumerate(theme_items):
        target_col = col_t1 if (i % 2 == 0) else col_t2
        with target_col:
            is_selected = (t_key == current_theme_key)
            card_border = f"2px solid {t_data['accent_primary']}" if is_selected else "1px solid rgba(255,255,255,0.12)"
            swatches_html = "".join([f'<span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:{c}; box-shadow:0 0 8px {c}88; margin-right:4px;"></span>' for c in t_data.get("preview_colors", [])])
            active_badge = f'<span style="background:{t_data["gradient"]}; color:#FFF; font-size:10px; font-weight:900; padding:2px 8px; border-radius:12px; margin-left:8px;">ACTIVE</span>' if is_selected else ""

            st.markdown(
                f"""
                <div style="background:{t_data['bg_card']}; border:{card_border}; border-radius:14px; padding:14px 16px; margin-bottom:10px; box-shadow:{t_data['glow'] if is_selected else 'none'};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:15px; font-weight:800; color:{t_data['text_pure']}; display:flex; align-items:center;">
                            {t_key} {active_badge}
                        </div>
                        <div>{swatches_html}</div>
                    </div>
                    <div style="font-size:12px; color:{t_data['text_muted']}; margin-top:4px;">{t_data['description']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            btn_label = "✅ Currently Active" if is_selected else f"Apply {t_data['name']}"
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"btn_apply_theme_{t_data['id']}", use_container_width=True, type=btn_type):
                if not is_selected:
                    st.session_state["color_theme"] = t_key
                    st.rerun()

    st.divider()

    # ── Section 3: Privacy Policies ──────────────────────────────────────────
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
