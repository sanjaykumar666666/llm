"""
Global Configuration and Hyperparameters for Privacy Shield AI.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
TEMP_UPLOAD_DIR = BASE_DIR / "temp_uploads"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Privacy Threshold Settings
# Low Risk (< 0.30): ALLOW
# Medium Risk (0.30 - 0.74): SANITIZE
# High Risk (>= 0.75): BLOCK
THRESHOLD_LOW_RISK = 0.30
THRESHOLD_HIGH_RISK = 0.75

# File Processing Constraints
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))

# Input Validation Constraints (Phase 1 — Multimodal Input)
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 50000))       # Max characters for text input
MAX_YOUTUBE_URL_LENGTH = 500                                     # Max URL length for YouTube input
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".csv", ".json", ".md", ".log"}

# Default Gemini Models
DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-3.5-flash-lite")
FALLBACK_LLM_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.1-pro-preview", "gemini-flash-latest"]
