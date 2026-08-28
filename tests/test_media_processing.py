"""
Test Suite: Media Processing & Frame Generation Pipeline.
File: tests/test_media_processing.py
"""

import pytest
import numpy as np
from backend.adapters.platform_adapters import generate_platform_frame


def test_generate_platform_frame_validity():
    """Verify that generate_platform_frame creates valid numpy images and data URIs."""
    platforms = ["YouTube", "Instagram", "Facebook", "X / Twitter", "TikTok", "Vimeo", "Reddit", "Generic"]
    for p in platforms:
        img_arr, data_uri = generate_platform_frame(
            platform=p,
            title="Sample Media Title",
            author="creator",
            timestamp_sec=15.0,
            content_type="video",
            width=320,
            height=180
        )
        assert isinstance(img_arr, np.ndarray)
        assert img_arr.shape == (180, 320, 3)
        assert data_uri.startswith("data:image/jpeg;base64,")
        assert len(data_uri) > 100
