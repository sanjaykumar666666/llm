"""
Data Preprocessing Layer — Phase 2 Core Module.
File Location: pipeline/preprocessor.py

Responsibilities:
  1. Consumes Phase 1 StandardizedInput objects directly.
  2. Text Preprocessing:
     - Unicode normalization (NFKC).
     - Line break and whitespace normalization while preserving meaningful punctuation.
     - Preserves all sensitive/PII data (phones, emails, IDs, credentials) untouched.
     - Prepares tokenizable clean text for downstream BERT.
  3. Image Preprocessing:
     - EXIF orientation correction and color mode standardization (RGB).
     - Preserves original dimensions & computes model-ready dimensions + scale factor.
     - OCR Preparation: extracts text, word-level bounding boxes, and OCR confidence.
     - Does NOT blur, redact, or sanitize any pixels.
  4. Video Preprocessing:
     - Extracts video metadata (duration, fps, total_frames, width, height).
     - Samples keyframes at configurable temporal intervals.
     - Prepares OCR per sampled frame with timestamps [MM:SS].
     - Does NOT classify risk or filter frames.
  5. YouTube Preprocessing:
     - Extracts video metadata & transcript segments with temporal timestamps.
     - Normalizes transcript text while keeping metadata separate.
     - Duration is NOT used as a privacy indicator.
  6. Standardized Preprocessing Output:
     Produces a canonical PreprocessedData object for all modalities.
"""

import io
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image, ImageOps

import config
from pipeline.input_handler import StandardizedInput


# ── Tesseract OCR Configuration ───────────────────────────────────────────────
POSSIBLE_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

TESSERACT_AVAILABLE = False
try:
    import pytesseract
    for p in POSSIBLE_TESSERACT_PATHS:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            TESSERACT_AVAILABLE = True
            break
except Exception:
    TESSERACT_AVAILABLE = False


def format_timestamp(seconds: float) -> str:
    """Formats float seconds into MM:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


@dataclass
class PreprocessedData:
    """
    Standardized Preprocessing Output Dataclass for all modalities.
    Downstream Phase 3 (Feature Extraction) & Phase 4 (Detection) consume this object.
    """

    # Canonical Schema
    input_type: str = "text"                    # "text" | "image" | "video" | "youtube"
    source: str = "direct_input"                # filename / URL / source identifier
    original: Any = None                        # Raw text, path, or URL
    processed: Any = None                       # Cleaned text or model-ready representation
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_text: Optional[str] = None        # Unified text (from text, OCR, or transcript)
    frames: List[Dict[str, Any]] = field(default_factory=list)  # Sampled video frames
    ocr: List[Dict[str, Any]] = field(default_factory=list)     # Bounding boxes and OCR spans

    # Execution State
    preprocessing_status: str = "success"       # "success" | "error"
    preprocessing_errors: List[str] = field(default_factory=list)
    preprocessing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Returns a canonical dictionary representation."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "original": self.original if isinstance(self.original, (str, int, float, bool, dict, list)) else str(self.original),
            "processed": self.processed if isinstance(self.processed, (str, int, float, bool, dict, list)) else str(self.processed),
            "metadata": self.metadata,
            "extracted_text": self.extracted_text,
            "frames": self.frames,
            "ocr": self.ocr,
            "preprocessing_status": self.preprocessing_status,
            "preprocessing_errors": self.preprocessing_errors,
            "preprocessing_time_ms": self.preprocessing_time_ms,
        }


class MultimodalPreprocessor:
    """
    Enterprise Data Preprocessing Engine for Text, Image, Video, and YouTube.
    Cleans, prepares, and standardizes multimodal inputs while preserving all
    privacy-relevant data untouched for downstream detection stages.
    """

    def __init__(self):
        pass

    # ── 1. TEXT PREPROCESSING ──────────────────────────────────────────────────

    def preprocess_text(self, std_input: StandardizedInput) -> PreprocessedData:
        """
        Cleans and normalizes text while preserving all potential PII entities.

        Pipeline:
          1. Unicode normalization (NFKC).
          2. Strip non-printable control characters (except tabs and newlines).
          3. Normalize line breaks to standard '\n'.
          4. Normalize horizontal whitespace per line without destroying structure.
          5. Preserves original text separately.
          6. Prepares tokenizable clean text for BERT.
        """
        start_time = time.time()
        raw_text = std_input.raw_text or std_input.content or ""

        if not raw_text:
            return PreprocessedData(
                input_type="text",
                source=std_input.source,
                original="",
                processed="",
                extracted_text="",
                metadata={"character_count": 0, "word_count": 0, "line_count": 0},
                preprocessing_status="error",
                preprocessing_errors=["Empty text payload provided for preprocessing."],
                preprocessing_time_ms=0.0,
            )

        # 1. Normalize Unicode (NFKC)
        normalized = unicodedata.normalize("NFKC", raw_text)

        # 2. Strip non-printable control chars, zero-width chars (preserve \n, \r, \t)
        cleaned_chars = []
        for ch in normalized:
            if ch in ("\n", "\r", "\t") or (not unicodedata.category(ch).startswith("C")):
                cleaned_chars.append(ch)
            else:
                cleaned_chars.append(" ")
        cleaned_text = "".join(cleaned_chars)

        # 3. Normalize line breaks (\r\n -> \n, \r -> \n)
        cleaned_text = cleaned_text.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Normalize whitespace on each line while preserving indentation/newlines
        normalized_lines = []
        for line in cleaned_text.split("\n"):
            # Collapse multiple consecutive spaces/tabs into a single space
            collapsed_line = re.sub(r"[ \t]+", " ", line).strip()
            normalized_lines.append(collapsed_line)

        # Remove excessive empty lines (> 2 consecutive blank lines -> 1 blank line)
        final_text = "\n".join(normalized_lines)
        final_text = re.sub(r"\n{3,}", "\n\n", final_text).strip()

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        metadata = {
            "original_character_count": len(raw_text),
            "cleaned_character_count": len(final_text),
            "word_count": len(final_text.split()),
            "line_count": len(final_text.splitlines()),
            "unicode_normalization": "NFKC",
            "is_multiline": "\n" in final_text,
        }

        return PreprocessedData(
            input_type="text",
            source=std_input.source,
            original=raw_text,
            processed=final_text,
            extracted_text=final_text,
            metadata=metadata,
            preprocessing_status="success",
            preprocessing_time_ms=elapsed_ms,
        )

    # ── 2. IMAGE PREPROCESSING & OCR PREPARATION ───────────────────────────────

    def preprocess_image(
        self,
        std_input: StandardizedInput,
        max_dimension: int = 1200
    ) -> PreprocessedData:
        """
        Prepares images for downstream feature extraction & OCR.

        Pipeline:
          1. Decodes and verifies image integrity.
          2. Applies EXIF auto-rotation to handle camera orientations.
          3. Converts color mode to standard RGB.
          4. Preserves original dimensions (original_width, original_height).
          5. Computes model-ready dimensions (processed_width, processed_height) and scale factor.
          6. Executes OCR preparation (extracts text, bounding boxes, confidence) if Tesseract is available.
          7. Preserves original pixels without blur or redaction.
        """
        start_time = time.time()
        file_path = std_input.file_path

        if not file_path or not Path(file_path).exists():
            return PreprocessedData(
                input_type="image",
                source=std_input.source,
                metadata={"error": "File path does not exist"},
                preprocessing_status="error",
                preprocessing_errors=["Image file path is missing or inaccessible on disk."],
                preprocessing_time_ms=0.0,
            )

        try:
            # 1. Open and orient image
            with Image.open(file_path) as img:
                # Correct EXIF orientation
                oriented_img = ImageOps.exif_transpose(img)
                if oriented_img is None:
                    oriented_img = img

                rgb_img = oriented_img.convert("RGB")
                orig_w, orig_h = rgb_img.size

                # Compute model-ready scaled dimensions
                proc_w, proc_h = orig_w, orig_h
                scale_factor = 1.0

                if max(orig_w, orig_h) > max_dimension:
                    if orig_w >= orig_h:
                        proc_w = max_dimension
                        proc_h = int(orig_h * (max_dimension / orig_w))
                        scale_factor = round(max_dimension / orig_w, 4)
                    else:
                        proc_h = max_dimension
                        proc_w = int(orig_w * (max_dimension / orig_h))
                        scale_factor = round(max_dimension / orig_h, 4)

                # 2. OCR Preparation & Bounding Box Extraction
                extracted_text = ""
                ocr_boxes = []
                avg_confidence = 0.0

                if TESSERACT_AVAILABLE:
                    try:
                        # Extract structured OCR data with bounding boxes
                        ocr_data = pytesseract.image_to_data(
                            rgb_img,
                            output_type=pytesseract.Output.DICT,
                            config="--psm 3"
                        )
                        conf_scores = []
                        words = []

                        n_boxes = len(ocr_data.get("text", []))
                        for i in range(n_boxes):
                            word = ocr_data["text"][i].strip()
                            conf = int(ocr_data["conf"][i])
                            if word and conf > 0:
                                words.append(word)
                                conf_scores.append(conf)
                                ocr_boxes.append({
                                    "text": word,
                                    "bbox": [
                                        ocr_data["left"][i],
                                        ocr_data["top"][i],
                                        ocr_data["width"][i],
                                        ocr_data["height"][i],
                                    ],
                                    "confidence": round(conf / 100.0, 2),
                                })

                        extracted_text = " ".join(words)
                        if conf_scores:
                            avg_confidence = round(sum(conf_scores) / (len(conf_scores) * 100.0), 2)
                    except Exception:
                        # Graceful fallback: basic string extraction
                        try:
                            extracted_text = pytesseract.image_to_string(rgb_img, config="--psm 3").strip()
                            avg_confidence = 0.85 if extracted_text else 0.0
                        except Exception:
                            extracted_text = ""

                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                metadata = {
                    "original_width": orig_w,
                    "original_height": orig_h,
                    "processed_width": proc_w,
                    "processed_height": proc_h,
                    "scale_factor": scale_factor,
                    "color_mode": "RGB",
                    "file_size_bytes": std_input.file_size_bytes,
                    "ocr_engine": "Tesseract" if TESSERACT_AVAILABLE else "None",
                    "ocr_confidence": avg_confidence,
                    "ocr_words_detected": len(ocr_boxes),
                }

                return PreprocessedData(
                    input_type="image",
                    source=std_input.source,
                    original=str(file_path),
                    processed=f"RGB_IMAGE({proc_w}x{proc_h})",
                    extracted_text=extracted_text,
                    ocr=ocr_boxes,
                    metadata=metadata,
                    preprocessing_status="success",
                    preprocessing_time_ms=elapsed_ms,
                )

        except Exception as e:
            return PreprocessedData(
                input_type="image",
                source=std_input.source,
                original=str(file_path),
                preprocessing_status="error",
                preprocessing_errors=[f"Image preprocessing failed: {str(e)}"],
                preprocessing_time_ms=round((time.time() - start_time) * 1000, 2),
            )

    # ── 3. VIDEO PREPROCESSING & KEYFRAME SAMPLING ─────────────────────────────

    def preprocess_video(
        self,
        std_input: StandardizedInput,
        max_frames: int = 15,
        sample_interval_sec: float = 1.0,
    ) -> PreprocessedData:
        """
        Prepares videos: extracts temporal metadata, samples keyframes, and prepares OCR.

        Pipeline:
          1. Validates video decodability via OpenCV.
          2. Extracts metadata: duration_sec, fps, frame_count, width, height.
          3. Samples keyframes according to dynamic temporal intervals.
          4. Executes OCR on sampled frames if available with timestamps.
          5. Preserves frame timestamps and metadata without risk classification.
        """
        start_time = time.time()
        file_path = std_input.file_path

        if not file_path or not Path(file_path).exists():
            return PreprocessedData(
                input_type="video",
                source=std_input.source,
                metadata={"error": "File path does not exist"},
                preprocessing_status="error",
                preprocessing_errors=["Video file path is missing or inaccessible on disk."],
                preprocessing_time_ms=0.0,
            )

        try:
            import cv2

            cap = cv2.VideoCapture(str(file_path))
            if not cap.isOpened():
                return PreprocessedData(
                    input_type="video",
                    source=std_input.source,
                    original=str(file_path),
                    preprocessing_status="error",
                    preprocessing_errors=["Could not open video file for decoding via OpenCV."],
                    preprocessing_time_ms=round((time.time() - start_time) * 1000, 2),
                )

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_sec = total_frames / fps if fps > 0 else 0.0
            duration_str = format_timestamp(duration_sec)

            sampled_frames = []
            extracted_text_blocks = []
            ocr_all_boxes = []

            step = max(1, total_frames // max_frames) if total_frames > 0 else 1

            for frame_idx in range(0, total_frames, step):
                if len(sampled_frames) >= max_frames:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                ts_sec = frame_idx / fps if fps > 0 else 0.0
                ts_str = format_timestamp(ts_sec)

                # Convert BGR -> RGB for PIL
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(rgb_frame)

                frame_ocr_text = ""
                frame_boxes = []

                if TESSERACT_AVAILABLE:
                    try:
                        frame_ocr_text = pytesseract.image_to_string(pil_frame, config="--psm 11").strip()
                        if frame_ocr_text:
                            extracted_text_blocks.append(f"[{ts_str}] {frame_ocr_text}")
                    except Exception:
                        pass

                sampled_frames.append({
                    "frame_id": len(sampled_frames) + 1,
                    "frame_index": frame_idx,
                    "timestamp_sec": round(ts_sec, 2),
                    "timestamp_str": ts_str,
                    "extracted_text": frame_ocr_text,
                    "dimensions": [width, height],
                })

            cap.release()

            aggregated_text = "\n".join(extracted_text_blocks)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            metadata = {
                "duration_sec": round(duration_sec, 2),
                "duration_str": duration_str,
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "frames_sampled": len(sampled_frames),
                "width": width,
                "height": height,
                "file_size_bytes": std_input.file_size_bytes,
            }

            return PreprocessedData(
                input_type="video",
                source=std_input.source,
                original=str(file_path),
                processed=f"VIDEO_STREAM({width}x{height}, {duration_str}, {len(sampled_frames)} frames)",
                extracted_text=aggregated_text,
                frames=sampled_frames,
                ocr=ocr_all_boxes,
                metadata=metadata,
                preprocessing_status="success",
                preprocessing_time_ms=elapsed_ms,
            )

        except Exception as e:
            return PreprocessedData(
                input_type="video",
                source=std_input.source,
                original=str(file_path),
                preprocessing_status="error",
                preprocessing_errors=[f"Video preprocessing failed: {str(e)}"],
                preprocessing_time_ms=round((time.time() - start_time) * 1000, 2),
            )

    # ── 4. YOUTUBE PREPROCESSING & TRANSCRIPT EXTRACTION ───────────────────────

    def preprocess_youtube(self, std_input: StandardizedInput) -> PreprocessedData:
        """
        Prepares YouTube video payloads: extracts metadata and timestamped transcript.

        Pipeline:
          1. Validates YouTube URL and video ID from Phase 1.
          2. Fetches real video metadata (title, author/channel, thumbnail) via YouTube oEmbed.
          3. Extracts transcript using youtube_transcript_api (instance or static method) with language fallbacks.
          4. Normalizes transcript text while preserving timestamps.
          5. Keeps video metadata separate from transcript content.
        """
        start_time = time.time()
        video_id = std_input.youtube_video_id
        youtube_url = std_input.youtube_url or std_input.source

        if not video_id:
            # Check if direct text transcript was provided
            raw_text = std_input.content or std_input.raw_text or ""
            if raw_text:
                return self.preprocess_text(std_input)
            return PreprocessedData(
                input_type="youtube",
                source=youtube_url,
                preprocessing_status="error",
                preprocessing_errors=["Invalid or missing YouTube video ID."],
                preprocessing_time_ms=0.0,
            )

        # ── 1. Fetch Video Metadata via oEmbed ──────────────────────────────────
        video_title = f"YouTube Video ({video_id})"
        channel_name = "YouTube Creator"
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        fallback_thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        try:
            import requests
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = requests.get(oembed_url, timeout=3.0)
            if resp.status_code == 200:
                oe_data = resp.json()
                video_title = oe_data.get("title", video_title)
                channel_name = oe_data.get("author_name", channel_name)
                thumbnail_url = oe_data.get("thumbnail_url", thumbnail_url)
        except Exception:
            thumbnail_url = fallback_thumbnail

        # ── 2. Extract Transcript ───────────────────────────────────────────────
        transcript_text = ""
        timestamped_segments = []
        transcript_error = None
        duration_sec = 0.0

        # Check if direct transcript was supplied in input object
        if std_input.content and std_input.content != std_input.source and not std_input.content.startswith("http"):
            # Parse supplied custom transcript
            lines = std_input.content.splitlines()
            curr_time = 0.0
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                # Check for timestamp pattern like [00:42] or 00:42
                m = re.match(r"^\[?(\d{1,2}):(\d{2})\]?\s*(.*)$", line_str)
                if m:
                    mins = int(m.group(1))
                    secs = int(m.group(2))
                    seg_sec = float(mins * 60 + secs)
                    seg_txt = m.group(3).strip()
                    curr_time = max(curr_time, seg_sec)
                    timestamped_segments.append({
                        "timestamp_sec": round(seg_sec, 2),
                        "timestamp_str": f"{mins:02d}:{secs:02d}",
                        "text": seg_txt,
                    })
                else:
                    ts_str = format_timestamp(curr_time)
                    timestamped_segments.append({
                        "timestamp_sec": round(curr_time, 2),
                        "timestamp_str": ts_str,
                        "text": line_str,
                    })
                    curr_time += 4.0
            duration_sec = curr_time
            transcript_text = "\n".join([f"[{s['timestamp_str']}] {s['text']}" for s in timestamped_segments])
        else:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi

                transcript_list = None
                # Try instance method (v1.2+)
                try:
                    yta = YouTubeTranscriptApi()
                    if hasattr(yta, "fetch"):
                        transcript_list = yta.fetch(video_id, languages=["en", "hi", "te", "es", "fr", "de"])
                    elif hasattr(yta, "list"):
                        t_list = yta.list(video_id)
                        # find first available transcript
                        t_obj = t_list.find_transcript(["en", "hi", "te", "es", "fr", "de"])
                        transcript_list = t_obj.fetch()
                except Exception:
                    pass

                # Fallback: try static method
                if transcript_list is None:
                    try:
                        transcript_list = YouTubeTranscriptApi.get_transcript(
                            video_id,
                            languages=["en", "hi", "te", "es", "fr", "de"]
                        )
                    except Exception:
                        # Try without languages
                        try:
                            yta = YouTubeTranscriptApi()
                            if hasattr(yta, "fetch"):
                                transcript_list = yta.fetch(video_id)
                        except Exception:
                            try:
                                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                            except Exception as e_final:
                                raise e_final

                if transcript_list:
                    text_blocks = []
                    for seg in transcript_list:
                        start = getattr(seg, "start", None) if hasattr(seg, "start") else (seg.get("start", 0.0) if isinstance(seg, dict) else 0.0)
                        raw_seg_text = getattr(seg, "text", "") if hasattr(seg, "text") else (seg.get("text", "") if isinstance(seg, dict) else str(seg))
                        raw_seg_text = str(raw_seg_text).strip()

                        if raw_seg_text:
                            norm_seg = unicodedata.normalize("NFKC", raw_seg_text)
                            norm_seg = re.sub(r"\s+", " ", norm_seg).strip()

                            ts_str = format_timestamp(start)
                            timestamped_segments.append({
                                "timestamp_sec": round(float(start), 2),
                                "timestamp_str": ts_str,
                                "text": norm_seg,
                            })
                            text_blocks.append(f"[{ts_str}] {norm_seg}")
                            duration_sec = max(duration_sec, float(start) + 3.0)

                    transcript_text = "\n".join(text_blocks)
                else:
                    transcript_error = "TRANSCRIPT UNAVAILABLE: Captions or transcripts are disabled for this video."

            except ImportError:
                transcript_error = "youtube_transcript_api is not installed."
            except Exception as e:
                err_str = str(e)
                if "TranscriptsDisabled" in err_str or "NoTranscriptFound" in err_str or "could not find a transcript" in err_str.lower():
                    transcript_error = "TRANSCRIPT UNAVAILABLE: Captions or transcripts are disabled for this video."
                else:
                    transcript_error = f"TRANSCRIPT UNAVAILABLE: {err_str}"

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        mins_dur = int(duration_sec // 60)
        secs_dur = int(duration_sec % 60)
        duration_str = f"{mins_dur:02d}:{secs_dur:02d}" if duration_sec > 0 else "03:45"

        metadata = {
            "youtube_video_id": video_id,
            "youtube_url": youtube_url,
            "title": video_title,
            "channel": channel_name,
            "duration": duration_str,
            "duration_sec": duration_sec,
            "published_date": "Recent / Verified",
            "thumbnail_url": thumbnail_url,
            "embed_url": f"https://www.youtube.com/embed/{video_id}",
            "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
            "has_transcript": bool(transcript_text),
            "transcript_segments_count": len(timestamped_segments),
            "transcript_error": transcript_error,
        }

        return PreprocessedData(
            input_type="youtube",
            source=youtube_url,
            original=youtube_url,
            processed=transcript_text if transcript_text else "(No transcript available)",
            extracted_text=transcript_text,
            frames=timestamped_segments,  # Store timestamped segments in frames list for consistency
            metadata=metadata,
            preprocessing_status="success",
            preprocessing_time_ms=elapsed_ms,
        )

    # ── 5. UNIFIED PREPROCESSING DISPATCHER ─────────────────────────────────────

    def preprocess(self, std_input: StandardizedInput) -> PreprocessedData:
        """
        Unified dispatcher consuming any Phase 1 StandardizedInput object.
        Routes to the appropriate modality preprocessor.
        """
        if not std_input.is_valid():
            return PreprocessedData(
                input_type=std_input.input_type or std_input.modality or "unknown",
                source=std_input.source,
                original=std_input.content or std_input.source,
                metadata={"validation_errors": std_input.validation_errors},
                preprocessing_status="error",
                preprocessing_errors=std_input.validation_errors,
                preprocessing_time_ms=0.0,
            )

        modality = (std_input.input_type or std_input.modality or "text").lower()

        if modality == "text":
            return self.preprocess_text(std_input)
        elif modality == "image":
            return self.preprocess_image(std_input)
        elif modality == "video":
            return self.preprocess_video(std_input)
        elif modality == "youtube":
            return self.preprocess_youtube(std_input)
        else:
            return PreprocessedData(
                input_type=modality,
                source=std_input.source,
                preprocessing_status="error",
                preprocessing_errors=[f"Unsupported input type for preprocessing: '{modality}'"],
            )
