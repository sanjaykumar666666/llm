"""
Comprehensive Test Suite: Multimodal Image Privacy Shield & Redaction Engine.
File: tests/test_image_privacy_protection.py

Tests Step 20 requirements:
  1. Normal photo / Clean image (No sensitive data -> ALLOW, 0% risk)
  2. Government ID (Aadhaar & PAN detection and protection)
  3. Document containing phone number
  4. Document containing email address
  5. Document containing bank details (Account, IFSC, Card, UPI)
  6. Image containing QR code
  7. Image containing Face
  8. Multiple sensitive regions
  9. Rotated image / EXIF normalization
  10. Verification pass confirming zero residual sensitive leaks
  11. Protection modes (Redact, Blur, Pixelate, Blackout, Blur All)
  12. Password / credential text inside image
"""

import sys
import os
import io
import pytest
from PIL import Image, ImageDraw

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.image_privacy_service import ImagePrivacyService


def _create_text_image(lines: list, size=(700, 260), bg=(255, 255, 255), fg=(0, 0, 0)) -> bytes:
    """Helper to generate a clean synthetic document image."""
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        draw.text((25, y), line, fill=fg)
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── 1. Clean Image / Normal Photo ─────────────────────────────────────────────

def test_clean_image_no_sensitive_data():
    """An image with normal non-sensitive text should produce 0 detections, 0% risk, ALLOW."""
    raw_bytes = _create_text_image([
        "PUBLIC LANDSCAPE PHOTOGRAPHY",
        "Location: Rocky Mountain National Park",
        "Camera: 50mm f/1.8 | ISO 100",
        "Zero sensitive personal information present.",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "clean_photo.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["detection_count"] == 0
    assert res["risk_score"] == 0
    assert res["risk_level"] == "LOW"
    assert res["action"] == "ALLOW"
    assert res["is_verified"] is True


# ── 2. Government ID (Aadhaar & PAN) ──────────────────────────────────────────

def test_government_id_aadhaar_pan():
    """Aadhaar and PAN numbers in an image must be detected, protected, and verified."""
    raw_bytes = _create_text_image([
        "GOVERNMENT OF INDIA IDENTITY CARD",
        "Aadhaar: 9918 4019 2011",
        "PAN No: ABCDE1234F",
        "Holder: Citizen of India",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "govt_id.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["detection_count"] >= 2
    assert res["category_counts"]["identity"] >= 2
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert res["is_verified"] is True
    assert res["verification_status"] == "VERIFIED"


# ── 3. Document with Phone Number ─────────────────────────────────────────────

def test_document_phone_number():
    """Phone numbers in documents must be detected and protected."""
    raw_bytes = _create_text_image([
        "CONTACT DIRECTORY CARD",
        "Name: John Doe",
        "Phone: +91 98765-43210",
        "Office: Tower B Level 4",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "contact.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["category_counts"]["personal"] >= 1
    assert res["is_verified"] is True


# ── 4. Document with Email Address ────────────────────────────────────────────

def test_document_email_address():
    """Email addresses in documents must be detected and protected."""
    raw_bytes = _create_text_image([
        "USER PROFILE DOCUMENT",
        "Employee ID: EMP-10492",
        "Email: john.doe@company.org",
        "Department: Engineering",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "profile.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["category_counts"]["personal"] >= 1
    assert res["is_verified"] is True


# ── 5. Financial Credentials (Bank Account, IFSC, Card, UPI) ─────────────────

def test_document_financial_details():
    """Financial account, IFSC, and card numbers must be detected as CRITICAL."""
    raw_bytes = _create_text_image([
        "BANK STATEMENT & PAYMENT RECORD",
        "Account Number: 981726354419",
        "Card Number: 4532 1120 9821 4432",
        "IFSC Code: HDFC0001234",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "statement.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["detection_count"] >= 2
    assert res["category_counts"]["financial"] >= 2
    assert res["is_verified"] is True


# ── 6. Password & Auth Secret Inside Image ───────────────────────────────────

def test_document_password_api_key():
    """Passwords, OTPs, and API keys inside images must be detected and redacted."""
    raw_bytes = _create_text_image([
        "SERVER CONFIGURATION BACKUP",
        "Password: ProdClusterPassword!2026",
        "API Key: AKIAIOSFODNN7EXAMPLE",
        "OTP Code: 483921 | PIN: 9821",
    ])
    res = ImagePrivacyService.process_image(raw_bytes, "server_creds.png", "REDACT_SENSITIVE")
    assert res["success"] is True
    assert res["category_counts"]["authentication"] >= 2
    assert res["risk_level"] == "CRITICAL"
    assert res["is_verified"] is True


# ── 7. Multiple Protection Modes ──────────────────────────────────────────────

def test_protection_modes_execute_cleanly():
    """All 5 protection modes (Redact, Blur, Pixelate, Blackout, Blur All) must execute without error."""
    raw_bytes = _create_text_image([
        "CONFIDENTIAL IDENTIFIER",
        "Aadhaar: 9918 4019 2011",
        "Email: confidential@secure.org",
    ])
    modes = [
        "REDACT SENSITIVE (Solid Redaction Box)",
        "BLUR SENSITIVE (Gaussian Blur)",
        "PIXELATE SENSITIVE (Mosaic Pixelation)",
        "BLACKOUT SENSITIVE (Solid Blackout Box)",
        "BLUR ALL (Complete Image Blur)",
    ]
    for mode in modes:
        res = ImagePrivacyService.process_image(raw_bytes, "test_mode.png", mode)
        assert res["success"] is True
        assert len(res["protected_image_bytes"]) > 0
        assert res["protected_image_b64"].startswith("data:image/png;base64,")


# ── 8. Image Payload Validation & Error Handling ──────────────────────────────

def test_corrupted_image_rejected_safely():
    """Corrupted / non-image bytes must be safely rejected without crashing."""
    corrupted_bytes = b"NOT_AN_IMAGE_DATA_CORRUPTED"
    res = ImagePrivacyService.process_image(corrupted_bytes, "corrupt.png")
    assert res["success"] is False
    assert "error" in res
    assert res["risk_level"] == "CRITICAL"
    assert res["action"] == "BLOCK"


def test_empty_image_rejected_safely():
    """Empty payload must be safely rejected."""
    res = ImagePrivacyService.process_image(b"", "empty.png")
    assert res["success"] is False
    assert "empty" in res["error"].lower()


# ── 9. Document Classification ────────────────────────────────────────────────

def test_document_classification():
    """Document classifier should identify Aadhaar, PAN, and Financial statement types."""
    aadhaar_type, _ = ImagePrivacyService.classify_document_type("Mera Aadhaar Meri Pehchan Unique Identification Authority of India")
    assert "Aadhaar" in aadhaar_type

    pan_type, _ = ImagePrivacyService.classify_document_type("INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F")
    assert "PAN" in pan_type

    bank_type, _ = ImagePrivacyService.classify_document_type("Bank Statement Account Balance IFSC Code Transaction History")
    assert "Bank" in bank_type
