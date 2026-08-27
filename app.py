"""
Streamlit Frontend Interface Entry Point.
File Location: app.py
"""

from pathlib import Path
import streamlit as st

logo_path = Path(__file__).resolve().parent / "frontend" / "assets" / "logo.png"

# Guarantee wide layout from the very first frame
try:
    st.set_page_config(
        page_title="AI Privacy Shield — Multimodal Security Gateway",
        page_icon=str(logo_path) if logo_path.exists() else "🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

import frontend.app

if __name__ == "__main__":
    frontend.app.main()
