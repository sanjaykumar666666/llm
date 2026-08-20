"""
Optimized Video Processing and Frame-Based OCR Pipeline with Temporal Timestamps.
File Location: processing/video_processor.py
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import cv2
import numpy as np
from PIL import Image
import pytesseract
from processing.text_processor import TextProcessor

# Auto-configure Tesseract binary path on Windows if available
POSSIBLE_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

for p in POSSIBLE_TESSERACT_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


def format_timestamp(seconds: float) -> str:
    """Formats float seconds into MM:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class VideoProcessor:
    """
    Engine to extract key frames from videos with temporal timestamps [MM:SS],
    run optimized OCR per frame, and aggregate text for PII detection.
    """

    def __init__(self, max_frames_to_sample: int = 15):
        self.max_frames_to_sample = max_frames_to_sample
        self.text_processor = TextProcessor()

    def preprocess_frame_for_ocr(self, frame_np: np.ndarray) -> Image.Image:
        """
        Preprocesses raw frame numpy array to maximize Tesseract OCR accuracy.
        1. Resizes large frames to standard width (800px) to boost speed.
        2. Converts BGR to Grayscale.
        3. Applies Otsu's thresholding for sharp text binarization.
        """
        height, width = frame_np.shape[:2]
        if width > 800:
            scale = 800.0 / width
            new_width = 800
            new_height = int(height * scale)
            frame_np = cv2.resize(frame_np, (new_width, new_height), interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
        _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binarized)

    def extract_key_frames_with_timestamps(
        self, video_path: Union[str, Path]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Extracts up to 'max_frames_to_sample' keyframes with exact timestamps [MM:SS].
        """
        frame_data_list = []
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            return frame_data_list, 0.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration_sec = total_frames / fps if (fps and fps > 0) else 0.0

        if total_frames <= 0:
            cap.release()
            return frame_data_list, duration_sec

        step = max(1, total_frames // self.max_frames_to_sample)

        for frame_idx in range(0, total_frames, step):
            if len(frame_data_list) >= self.max_frames_to_sample:
                break

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            frame_sec = frame_idx / fps if (fps and fps > 0) else 0.0
            timestamp_str = format_timestamp(frame_sec)

            processed_pil_image = self.preprocess_frame_for_ocr(frame)
            frame_data_list.append({
                "frame_index": frame_idx,
                "timestamp_sec": frame_sec,
                "timestamp_str": timestamp_str,
                "image": processed_pil_image
            })

        cap.release()
        return frame_data_list, duration_sec

    def process(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Executes complete temporal video inspection pipeline.
        """
        frame_data_list, duration_sec = self.extract_key_frames_with_timestamps(video_path)
        
        if not frame_data_list:
            return {
                "extracted_text": "",
                "character_count": 0,
                "frames_processed": 0,
                "duration_sec": 0.0,
                "duration_str": "00:00",
                "detected_entities": [],
                "detected_entity_types": [],
                "contains_regex_pii": False,
                "timeline_frames": [],
                "error": "Failed to read frames from video file.",
            }

        aggregated_text_blocks = []
        unique_text_hashes = set()
        timeline_frames = []

        for item in frame_data_list:
            ts_str = item["timestamp_str"]
            img = item["image"]
            try:
                frame_text = pytesseract.image_to_string(img, config="--psm 11")
                cleaned_frame_text = self.text_processor.clean_text(frame_text)

                if cleaned_frame_text and len(cleaned_frame_text) > 3 and cleaned_frame_text not in unique_text_hashes:
                    unique_text_hashes.add(cleaned_frame_text)
                    aggregated_text_blocks.append(f"[{ts_str}] {cleaned_frame_text}")

                timeline_frames.append({
                    "timestamp_str": ts_str,
                    "extracted_text": cleaned_frame_text
                })
            except Exception:
                timeline_frames.append({
                    "timestamp_str": ts_str,
                    "extracted_text": ""
                })

        full_aggregated_text = "\n".join(aggregated_text_blocks)
        text_analysis = self.text_processor.process(full_aggregated_text)
        duration_str = format_timestamp(duration_sec)

        return {
            "extracted_text": full_aggregated_text,
            "character_count": len(full_aggregated_text),
            "frames_processed": len(frame_data_list),
            "duration_sec": duration_sec,
            "duration_str": duration_str,
            "detected_entities": text_analysis["detected_entities"],
            "detected_entity_types": text_analysis["detected_entity_types"],
            "contains_regex_pii": text_analysis["contains_regex_pii"],
            "timeline_frames": timeline_frames
        }
