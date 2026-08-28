"""
Automated Tests for Social Media Privacy Gatekeeper & Instagram Post Safety Service.
File: tests/test_social_privacy_service.py
"""

import io
import pytest
from PIL import Image, ImageDraw

from backend.services.social_privacy_service import SocialPrivacyService
from backend.services.video_content_analyzer import VideoContentAnalyzer
from tests.test_granular_identity_privacy import create_synthetic_card


def test_caption_pii_detection():
    """Test caption analyzer detecting phone numbers, emails, and UPI."""
    # 1. Clean caption
    res_clean = SocialPrivacyService.analyze_caption_text("Sunset in Goa! 🌅 Loving this vacation with friends #travel")
    assert res_clean["has_caption_leaks"] is False
    assert res_clean["leak_count"] == 0

    # 2. Leaked Phone & UPI caption
    res_leaked = SocialPrivacyService.analyze_caption_text("DM me or call on 9876543210 or GPay at testuser@okaxis")
    assert res_leaked["has_caption_leaks"] is True
    assert res_leaked["leak_count"] >= 2


def test_clean_photo_post_safe_to_upload():
    """Test clean photo evaluation returns SAFE_TO_UPLOAD."""
    img = Image.new("RGB", (400, 400), (34, 197, 94))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    res = SocialPrivacyService.evaluate_social_post(
        media_bytes=raw_bytes,
        filename="travel.png",
        media_type="image",
        caption="Beautiful nature vibes! 🌿 #greenery",
        target_platform="Instagram",
        author_username="@nature_traveler"
    )

    assert res["success"] is True
    assert res["is_safe_to_upload"] is True
    assert res["verdict"] == "SAFE_TO_UPLOAD"
    assert res["privacy_score"] >= 85.0
    assert "🟢" in res["badge"]


def test_identity_leak_photo_post_blocked():
    """Test photo with leaked Aadhaar / ID card is BLOCKED with warnings."""
    raw_bytes = create_synthetic_card(has_id_num=True, has_address=True, has_name=True)

    res = SocialPrivacyService.evaluate_social_post(
        media_bytes=raw_bytes,
        filename="my_card.png",
        media_type="image",
        caption="Just received my document! #updates",
        target_platform="Instagram",
        author_username="@user_alert"
    )

    assert res["success"] is True
    assert res["is_safe_to_upload"] is False
    assert res["verdict"] in ["BLOCKED_DANGEROUS_LEAK", "WARNING_REDACTION_RECOMMENDED"]
    assert res["total_issues_found"] >= 1
    assert "DO NOT UPLOAD" in res["badge"] or "CAUTION" in res["badge"]
    assert res["sanitized_media_bytes"] is not None


def test_video_reel_evaluation():
    """Test synthetic video reel evaluated for social upload."""
    from backend.services.video_privacy_service import VideoPrivacyService
    vid_bytes, fname = VideoPrivacyService.generate_sample_video("🟢 Clean Landscape Video (Zero PII)")

    res = SocialPrivacyService.evaluate_social_post(
        media_bytes=vid_bytes,
        filename=fname,
        media_type="video",
        caption="Clean landscape reel for Instagram #reels",
        target_platform="Instagram",
        author_username="@reels_creator"
    )

    assert res["success"] is True
    assert res["media_type"] == "video"
    assert res["target_platform"] == "Instagram"
    assert res["privacy_score"] >= 50.0
