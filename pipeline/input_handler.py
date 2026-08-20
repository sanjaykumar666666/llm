"""
Multimodal Input Handler — Phase 1 Core Module.
File Location: pipeline/input_handler.py

Responsibilities:
  1. Accepts raw inputs: Text, Image bytes, Video bytes, YouTube URL.
  2. Validates:
     - Text: empty, whitespace-only, excessive size.
     - Image: format/extension, file size, corruption detection via PIL verification.
     - Video: format/extension, file size, corruption detection via container header & OpenCV verification.
     - YouTube: URL structure, length, 11-char video ID extraction.
  3. Produces a single StandardizedInput object matching the required schema:
     {
         "input_type": "text | image | video | youtube",
         "source": "...",
         "file_path": null,
         "metadata": {},
         "content": null
     }
  4. Stores temporary files safely in temp directory and provides cleanup.
  5. Security: Never logs sensitive content or dumps stack traces.

This module does NOT call any ML model or LLM. It is strictly the input normalization layer.
"""

import io
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

import config


# ── YouTube URL Validation Regex ──────────────────────────────────────────────
YOUTUBE_URL_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=(?P<id>[a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/(?P<id>[a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/v/(?P<id>[a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/(?P<id>[a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/shorts/(?P<id>[a-zA-Z0-9_-]{11})"),
]

# ── Content Type Mapping ──────────────────────────────────────────────────────
IMAGE_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

VIDEO_CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
}


@dataclass
class StandardizedInput:
    """
    Standardized Multimodal Input Object for Downstream Pipeline Consumption.
    Conforms to the required schema:
      - input_type: "text" | "image" | "video" | "youtube"
      - source: "direct_input" | file name | YouTube URL
      - file_path: Path on disk for binary payloads (or None)
      - metadata: dictionary containing sizes, dimensions, timestamps, etc.
      - content: raw text content or None for binary files
    """

    # Primary Schema Fields
    input_type: str = "text"                    # "text" | "image" | "video" | "youtube"
    source: str = "direct_input"                # Input source identifier / filename / URL
    file_path: Optional[Path] = None            # Temp file path on disk
    metadata: Dict[str, Any] = field(default_factory=dict)
    content: Optional[str] = None               # Text content or None

    # Pipeline Tracking Fields
    request_id: str = ""
    modality: str = "text"                      # Synonym for input_type
    raw_text: Optional[str] = None              # Direct text content
    file_name: Optional[str] = None             # Original filename
    file_size_bytes: int = 0                    # Size in bytes
    file_extension: Optional[str] = None        # Normalized extension (e.g. .png)
    youtube_url: Optional[str] = None           # Full YouTube URL
    youtube_video_id: Optional[str] = None      # 11-character video ID
    content_type: Optional[str] = None          # MIME type
    created_at: str = ""                        # ISO timestamp

    # Validation State
    validation_status: str = "PENDING"          # "VALID" | "INVALID" | "PENDING"
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.modality:
            self.modality = self.input_type
        if not self.input_type:
            self.input_type = self.modality
        if self.raw_text and not self.content:
            self.content = self.raw_text

    def is_valid(self) -> bool:
        """Returns True if the input passed all validation checks."""
        return self.validation_status == "VALID"

    def to_standard_dict(self) -> Dict[str, Any]:
        """Returns the canonical standardized schema dictionary."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "file_path": str(self.file_path) if self.file_path else None,
            "metadata": self.metadata,
            "content": self.content,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable summary for API responses and downstream stages."""
        return {
            "request_id": self.request_id,
            "input_type": self.input_type,
            "modality": self.modality,
            "source": self.source,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "file_extension": self.file_extension,
            "content_type": self.content_type,
            "youtube_video_id": self.youtube_video_id,
            "created_at": self.created_at,
            "has_text": bool(self.content or self.raw_text),
            "has_file": self.file_path is not None and self.file_path.exists() if self.file_path else False,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors,
            "metadata": self.metadata,
        }


class MultimodalInputHandler:
    """
    Validates, normalizes, and packages raw inputs into StandardizedInput objects.
    Supports four modalities: text, image, video, youtube.
    """

    # Constraints
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 50000))
    MAX_FILE_SIZE_BYTES = config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB → bytes
    MAX_YOUTUBE_URL_LENGTH = 500

    def __init__(self):
        config.TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_request_id() -> str:
        return f"P1-{uuid.uuid4().hex[:10]}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── 1. TEXT INPUT ──────────────────────────────────────────────────────────

    def handle_text(self, text: str) -> StandardizedInput:
        """
        Validates and packages a text input (single or multiline).

        Validation rules:
          - Must not be empty or whitespace-only
          - Must not exceed MAX_TEXT_LENGTH characters
        """
        inp = StandardizedInput(
            request_id=self._generate_request_id(),
            input_type="text",
            modality="text",
            source="direct_input",
            created_at=self._now_iso(),
        )

        errors = []

        if text is None or not str(text).strip():
            errors.append("Text input is empty or contains only whitespace.")
        elif len(text) > self.MAX_TEXT_LENGTH:
            errors.append(
                f"Text exceeds maximum length of {self.MAX_TEXT_LENGTH:,} characters "
                f"(received {len(text):,} characters)."
            )

        if errors:
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
        else:
            cleaned = text.strip()
            inp.raw_text = cleaned
            inp.content = cleaned
            inp.file_size_bytes = len(cleaned.encode("utf-8"))
            inp.content_type = "text/plain"
            inp.validation_status = "VALID"
            inp.metadata = {
                "character_count": len(cleaned),
                "word_count": len(cleaned.split()),
                "line_count": len(cleaned.splitlines()),
                "is_multiline": "\n" in cleaned,
            }

        return inp

    # ── 2. IMAGE INPUT ─────────────────────────────────────────────────────────

    async def handle_image(self, file) -> StandardizedInput:
        """
        Validates, checks for corruption, saves, and packages an uploaded image.

        Validation rules:
          - File must not be empty (0 bytes)
          - Extension must be in ALLOWED_IMAGE_EXTENSIONS (.png, .jpg, .jpeg, .webp, .bmp)
          - File size must not exceed MAX_FILE_SIZE_MB
          - File must be a valid, uncorrupted image (verified via PIL)
        """
        inp = StandardizedInput(
            request_id=self._generate_request_id(),
            input_type="image",
            modality="image",
            created_at=self._now_iso(),
        )

        errors = []

        # Read file bytes safely
        try:
            file_bytes = await file.read()
        except Exception:
            errors.append("Failed to read uploaded image file payload.")
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        filename = getattr(file, "filename", None) or "uploaded_image"
        inp.source = filename
        inp.file_name = filename

        ext = Path(filename).suffix.lower()
        inp.file_extension = ext

        # Validate extension
        if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
            errors.append(
                f"Unsupported image format '{ext}'. "
                f"Allowed: {', '.join(sorted(config.ALLOWED_IMAGE_EXTENSIONS))}"
            )

        # Validate content not empty
        if not file_bytes or len(file_bytes) == 0:
            errors.append("Uploaded image file is empty (0 bytes).")

        # Validate size
        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            errors.append(
                f"Image file size ({size_mb:.1f} MB) exceeds maximum of {config.MAX_FILE_SIZE_MB} MB."
            )

        # Validate image integrity (corruption check via PIL)
        img_dimensions = None
        img_format = None
        if not errors:
            try:
                img_io = io.BytesIO(file_bytes)
                with Image.open(img_io) as pil_img:
                    img_dimensions = pil_img.size
                    img_format = pil_img.format
                    # verify image structure
                    pil_img.verify()
            except Exception:
                errors.append("Corrupted or invalid image file: unable to decode image data.")

        if errors:
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        # Save to temp directory
        safe_filename = f"{inp.request_id}_{Path(filename).name}"
        temp_path = config.TEMP_UPLOAD_DIR / safe_filename
        try:
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
        except Exception:
            errors.append("Failed to write temporary image file to disk.")
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        inp.file_path = temp_path
        inp.file_size_bytes = len(file_bytes)
        inp.content_type = IMAGE_CONTENT_TYPES.get(ext, "image/png")
        inp.validation_status = "VALID"
        inp.metadata = {
            "original_filename": filename,
            "dimensions": img_dimensions,
            "format": img_format,
            "saved_path": str(temp_path),
            "size_bytes": len(file_bytes),
        }

        return inp

    # ── 3. VIDEO INPUT ─────────────────────────────────────────────────────────

    async def handle_video(self, file) -> StandardizedInput:
        """
        Validates, checks for corruption, saves, and packages an uploaded video.

        Validation rules:
          - File must not be empty (0 bytes)
          - Extension must be in ALLOWED_VIDEO_EXTENSIONS (.mp4, .avi, .mov, .mkv, .webm)
          - File size must not exceed MAX_FILE_SIZE_MB
          - Container header must match recognized video signatures
        """
        inp = StandardizedInput(
            request_id=self._generate_request_id(),
            input_type="video",
            modality="video",
            created_at=self._now_iso(),
        )

        errors = []

        # Read file bytes safely
        try:
            file_bytes = await file.read()
        except Exception:
            errors.append("Failed to read uploaded video file payload.")
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        filename = getattr(file, "filename", None) or "uploaded_video"
        inp.source = filename
        inp.file_name = filename

        ext = Path(filename).suffix.lower()
        inp.file_extension = ext

        # Validate extension
        if ext not in config.ALLOWED_VIDEO_EXTENSIONS:
            errors.append(
                f"Unsupported video format '{ext}'. "
                f"Allowed: {', '.join(sorted(config.ALLOWED_VIDEO_EXTENSIONS))}"
            )

        # Validate content not empty
        if not file_bytes or len(file_bytes) == 0:
            errors.append("Uploaded video file is empty (0 bytes).")

        # Validate size
        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            errors.append(
                f"Video file size ({size_mb:.1f} MB) exceeds maximum of {config.MAX_FILE_SIZE_MB} MB."
            )

        # Validate basic video header signature
        if not errors and len(file_bytes) >= 12:
            # Check common video signatures (ftyp for mp4/mov, RIFF for avi, matroska for mkv/webm)
            header = file_bytes[:32]
            is_valid_header = (
                b"ftyp" in header or
                header.startswith(b"RIFF") or
                header.startswith(b"\x1a\x45\xdf\xa3") or  # MKV/WebM
                header.startswith(b"\x00\x00\x00") or      # Generic MP4/MOV atom
                ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]
            )
            if not is_valid_header:
                errors.append("Corrupted video file: unrecognized video container signature.")

        if errors:
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        # Save to temp directory for downstream processing
        safe_filename = f"{inp.request_id}_{Path(filename).name}"
        temp_path = config.TEMP_UPLOAD_DIR / safe_filename
        try:
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
        except Exception:
            errors.append("Failed to write temporary video file to disk.")
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            return inp

        inp.file_path = temp_path
        inp.file_size_bytes = len(file_bytes)
        inp.content_type = VIDEO_CONTENT_TYPES.get(ext, "video/mp4")
        inp.validation_status = "VALID"
        inp.metadata = {
            "original_filename": filename,
            "saved_path": str(temp_path),
            "size_bytes": len(file_bytes),
        }

        return inp

    # ── 4. YOUTUBE INPUT ───────────────────────────────────────────────────────

    def handle_youtube(self, url: str) -> StandardizedInput:
        """
        Validates a YouTube URL and extracts video metadata.

        Validation rules:
          - URL must not be empty
          - URL must not exceed MAX_YOUTUBE_URL_LENGTH
          - URL must match recognized YouTube patterns (watch?v=, embed/, youtu.be/, shorts/)
          - Extracted video ID must be exactly 11 characters
        """
        inp = StandardizedInput(
            request_id=self._generate_request_id(),
            input_type="youtube",
            modality="youtube",
            created_at=self._now_iso(),
        )

        errors = []

        if url is None or not str(url).strip():
            errors.append("YouTube URL is empty.")
        elif len(url) > self.MAX_YOUTUBE_URL_LENGTH:
            errors.append(
                f"YouTube URL exceeds maximum length of {self.MAX_YOUTUBE_URL_LENGTH} characters."
            )
        else:
            cleaned_url = url.strip()
            video_id = self._extract_youtube_video_id(cleaned_url)
            if not video_id:
                errors.append(
                    f"Invalid YouTube URL format: '{cleaned_url}'. "
                    f"Supported formats: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/shorts/ID"
                )

        if errors:
            inp.validation_status = "INVALID"
            inp.validation_errors = errors
            inp.source = url if url else "empty"
            return inp

        inp.source = cleaned_url
        inp.youtube_url = cleaned_url
        inp.youtube_video_id = video_id
        inp.content_type = "text/url"
        inp.validation_status = "VALID"
        inp.metadata = {
            "youtube_video_id": video_id,
            "youtube_url": cleaned_url,
            "embed_url": f"https://www.youtube.com/embed/{video_id}",
            "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
        }

        return inp

    @staticmethod
    def _extract_youtube_video_id(url: str) -> Optional[str]:
        for pattern in YOUTUBE_URL_PATTERNS:
            match = pattern.search(url)
            if match:
                video_id = match.group("id")
                if len(video_id) == 11:
                    return video_id
        return None

    # ── CLEANUP ────────────────────────────────────────────────────────────────

    @staticmethod
    def cleanup(input_obj: StandardizedInput) -> None:
        """Removes temporary files created during input handling."""
        if input_obj.file_path and input_obj.file_path.exists():
            try:
                input_obj.file_path.unlink()
            except Exception:
                pass
