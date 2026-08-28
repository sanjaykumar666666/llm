"""
Social Media Platform Adapter Base Class — Universal Content Analyzer Architecture.
File: backend/adapters/base_adapter.py
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np


class SocialMediaAdapter(ABC):
    """
    Abstract Base Class for all Social Media and Public Media platform adapters.
    Each adapter handles platform detection, acquisition, and metadata/media extraction.
    Analysis (privacy, copyright, frame safety) is performed by shared core services.
    """

    @abstractmethod
    def detect(self, url: str) -> bool:
        """Returns True if the given URL corresponds to this platform."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Returns the human-readable platform name (e.g., 'YouTube', 'Instagram', 'X / Twitter')."""
        pass

    @abstractmethod
    def get_content_type(self, url: str) -> str:
        """
        Determines the content type from the URL or metadata.
        Returns one of: 'video', 'reel', 'short', 'image', 'post', 'thread', 'public_media'.
        """
        pass

    @abstractmethod
    def fetch_metadata(self, url: str) -> Dict[str, Any]:
        """
        Fetches publicly accessible metadata for the content.
        Must return a standardized dictionary:
        {
            "platform": str,
            "content_type": str,
            "content_id": str,
            "title": str,
            "author": str,
            "author_url": str,
            "duration": str,
            "duration_sec": float,
            "published_date": str,
            "thumbnail_url": str,
            "canonical_url": str,
            "embed_url": str,
            "availability": str ("Public / Accessible", "Private / Inaccessible", etc.),
            "is_accessible": bool,
            "error_reason": Optional[str],
            "license": str,
            "is_creative_commons": bool,
            "categories": List[str],
            "tags": List[str],
            "caption": str,
            "media_type": str ("video" | "image" | "mixed")
        }
        """
        pass

    @abstractmethod
    def fetch_content(self, url: str, custom_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts available text/captions/transcripts and media references without bypassing DRM or auth.
        Must return:
        {
            "text": str,
            "segments": List[Dict[str, Any]],
            "has_media": bool,
            "media_path": Optional[str],
            "media_type": str
        }
        """
        pass

    @abstractmethod
    def extract_media_frames(
        self,
        url: str,
        metadata: Dict[str, Any],
        max_samples: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Extracts representative frames or image samples.
        For video/reels: samples across beginning, middle, and end intervals.
        For images/posts: returns the image frame.
        Must return list of:
        {
            "frame_index": int,
            "timestamp_sec": float,
            "timestamp_str": str,
            "image_array": np.ndarray (RGB / BGR uint8),
            "thumbnail_data_uri": str (data:image/jpeg;base64,...),
            "scene_description": str
        }
        """
        pass

    @abstractmethod
    def get_license_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts platform-specific licensing terms and rights signals.
        Must return:
        {
            "license_name": str,
            "license_status": str ("VERIFIED_OPEN", "STANDARD_PLATFORM", "PROPRIETARY", "UNKNOWN"),
            "is_creative_commons": bool,
            "safe_use_guidance": str
        }
        """
        pass

    def cleanup(self, temp_artifacts: List[str]) -> None:
        """Cleans up any temporary files created during extraction."""
        import os
        for path in temp_artifacts:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
