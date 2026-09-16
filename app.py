import os
import sys
from pathlib import Path

# Suppress low-level C++ FFmpeg and OpenCV DNN notices
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
try:
    import cv2
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
    pass

import streamlit as st

# Anchor root directory in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logo_path = ROOT_DIR / "frontend" / "assets" / "logo.png"

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
