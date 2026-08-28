"""
Dedicated Automated Tests for Granular Identity Document Privacy Detection.
File: tests/test_granular_identity_privacy.py

Covers:
  1. Synthetic identity document with address
  2. Synthetic QR code
  3. Identity number (Aadhaar / PAN / Passport)
  4. Date of Birth (DOB)
  5. Face / Biometric photo
  6. Person Name
  7. Address + PIN combination
  8. All fields together (Full Identity Card)
  9. Separate reporting of each privacy category
  10. Explicit 5-part privacy intelligence (WHAT, WHERE, WHY, POSSIBLE PROBLEM, WHAT TO DO)
"""

import io
import os
import pytest
from PIL import Image, ImageDraw
import numpy as np
import cv2

from backend.services.image_privacy_service import ImagePrivacyService


def create_synthetic_card(
    has_name=True,
    has_dob=True,
    has_id_num=True,
    has_address=True,
    has_pin=True,
    has_face=True,
    has_qr=True
) -> bytes:
    """Generates synthetic identity cards with crisp test typography and shapes."""
    width, height = 750, 450
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Document border & header
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(14, 165, 233), width=3)
    draw.text((25, 20), "GOVERNMENT OF INDIA / UNIQUE IDENTIFICATION AUTHORITY", fill=(15, 23, 42))

    # Face box
    if has_face:
        draw.rectangle([(25, 60), (160, 220)], fill=(203, 213, 225), outline=(100, 116, 139), width=2)
        # Draw a synthetic face circle & eyes
        draw.ellipse([(55, 90), (130, 165)], fill=(254, 215, 170), outline=(51, 65, 85))
        draw.ellipse([(70, 115), (85, 130)], fill=(30, 41, 59))
        draw.ellipse([(100, 115), (115, 130)], fill=(30, 41, 59))
        draw.arc([(75, 135), (110, 155)], start=0, end=180, fill=(30, 41, 59), width=2)

    # Text details
    y_off = 65
    if has_name:
        draw.text((180, y_off), "Name: Bhushan Diwakar", fill=(15, 23, 42))
        y_off += 35
    if has_dob:
        draw.text((180, y_off), "DOB: 05/07/2002 | Gender: Male", fill=(15, 23, 42))
        y_off += 35
    if has_id_num:
        draw.text((180, y_off), "Aadhaar No: 4906 5637 6032", fill=(225, 29, 72))
        y_off += 35
    if has_address:
        draw.text((180, y_off), "Address: Flat 1B, Sector-11C, Faridabad, Haryana", fill=(15, 23, 42))
        y_off += 30
    if has_pin:
        draw.text((180, y_off), "PIN: 121006 | PO: Sector 7", fill=(15, 23, 42))
        y_off += 30

    # Synthetic QR Code
    if has_qr:
        # Draw high-density QR grid simulation with finder patterns
        qr_x1, qr_y1, qr_x2, qr_y2 = 540, 220, 710, 390
        draw.rectangle([(qr_x1, qr_y1), (qr_x2, qr_y2)], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        # Finder patterns (top-left, top-right, bottom-left)
        draw.rectangle([(qr_x1 + 8, qr_y1 + 8), (qr_x1 + 45, qr_y1 + 45)], fill=(0, 0, 0))
        draw.rectangle([(qr_x1 + 16, qr_y1 + 16), (qr_x1 + 37, qr_y1 + 37)], fill=(255, 255, 255))
        draw.rectangle([(qr_x1 + 22, qr_y1 + 22), (qr_x1 + 31, qr_y1 + 31)], fill=(0, 0, 0))

        draw.rectangle([(qr_x2 - 45, qr_y1 + 8), (qr_x2 - 8, qr_y1 + 45)], fill=(0, 0, 0))
        draw.rectangle([(qr_x2 - 37, qr_y1 + 16), (qr_x2 - 16, qr_y1 + 37)], fill=(255, 255, 255))
        draw.rectangle([(qr_x2 - 31, qr_y1 + 22), (qr_x2 - 22, qr_y1 + 31)], fill=(0, 0, 0))

        draw.rectangle([(qr_x1 + 8, qr_y2 - 45), (qr_x1 + 45, qr_y2 - 8)], fill=(0, 0, 0))
        draw.rectangle([(qr_x1 + 16, qr_y2 - 37), (qr_x1 + 37, qr_y2 - 16)], fill=(255, 255, 255))
        draw.rectangle([(qr_x1 + 22, qr_y2 - 31), (qr_x1 + 31, qr_y2 - 22)], fill=(0, 0, 0))

        # QR interior noisy pattern
        for gx in range(qr_x1 + 50, qr_x2 - 50, 10):
            for gy in range(qr_y1 + 10, qr_y2 - 10, 10):
                if (gx + gy) % 20 == 0:
                    draw.rectangle([(gx, gy), (gx + 8, gy + 8)], fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── TEST 1: Synthetic Identity Document with Address ─────────────────────────

def test_synthetic_identity_document_with_address():
    raw_bytes = create_synthetic_card(has_address=True, has_id_num=False, has_face=False, has_qr=False, has_name=False, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_address.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1
    
    # Verify address is detected
    types = [d["type"] for d in res["detections"]]
    categories = [d["category"] for d in res["detections"]]
    assert "RESIDENTIAL_ADDRESS" in types or "ADDRESS" in categories
    assert res["category_counts"].get("address", 0) >= 1


# ── TEST 2: Synthetic QR Code ────────────────────────────────────────────────

def test_synthetic_qr_code():
    raw_bytes = create_synthetic_card(has_address=False, has_id_num=False, has_face=False, has_qr=True, has_name=False, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_qr.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    types = [d["type"] for d in res["detections"]]
    categories = [d["category"] for d in res["detections"]]
    assert "QR_CODE" in types or "IDENTITY_QR_CODE" in types or "QR_CODE" in categories
    assert res["category_counts"].get("qr_code", 0) >= 1


# ── TEST 3: Identity Number (Aadhaar / PAN) ──────────────────────────────────

def test_identity_number_detection():
    raw_bytes = create_synthetic_card(has_address=False, has_id_num=True, has_face=False, has_qr=False, has_name=False, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_id.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    types = [d["type"] for d in res["detections"]]
    assert "AADHAAR_NUMBER" in types or "PAN_NUMBER" in types
    assert res["category_counts"].get("government_id", 0) >= 1


# ── TEST 4: Date of Birth (DOB) ──────────────────────────────────────────────

def test_date_of_birth_detection():
    raw_bytes = create_synthetic_card(has_address=False, has_id_num=False, has_face=False, has_qr=False, has_name=False, has_dob=True)
    res = ImagePrivacyService.process_image(raw_bytes, "test_dob.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    types = [d["type"] for d in res["detections"]]
    assert "DATE_OF_BIRTH" in types
    assert res["category_counts"].get("date_of_birth", 0) >= 1


# ── TEST 5: Face / Biometric Photo ───────────────────────────────────────────

def test_face_detection():
    raw_bytes = create_synthetic_card(has_address=False, has_id_num=False, has_face=True, has_qr=False, has_name=False, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_face.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    types = [d["type"] for d in res["detections"]]
    assert "HUMAN_FACE" in types
    assert res["category_counts"].get("biometric_face", 0) >= 1


# ── TEST 6: Person Name ──────────────────────────────────────────────────────

def test_person_name_detection():
    raw_bytes = create_synthetic_card(has_address=False, has_id_num=False, has_face=False, has_qr=False, has_name=True, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_name.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    types = [d["type"] for d in res["detections"]]
    assert "PERSON_NAME" in types or any("name" in t.lower() for t in types)


# ── TEST 7: Address + PIN Combination ────────────────────────────────────────

def test_address_and_pin_combination():
    raw_bytes = create_synthetic_card(has_address=True, has_pin=True, has_id_num=False, has_face=False, has_qr=False, has_name=False, has_dob=False)
    res = ImagePrivacyService.process_image(raw_bytes, "test_addr_pin.png")
    assert res["success"] is True
    assert res["detection_count"] >= 1

    categories = [d["category"] for d in res["detections"]]
    assert "ADDRESS" in categories or "POSTAL_CODE" in categories
    assert (res["category_counts"].get("address", 0) + res["category_counts"].get("postal_code", 0)) >= 1


# ── TEST 8: All Fields Together (Full Identity Document) ─────────────────────

def test_all_fields_together_identity_document():
    raw_bytes = create_synthetic_card(
        has_name=True,
        has_dob=True,
        has_id_num=True,
        has_address=True,
        has_pin=True,
        has_face=True,
        has_qr=True
    )
    res = ImagePrivacyService.process_image(raw_bytes, "full_aadhaar_card.png")
    assert res["success"] is True
    assert res["detection_count"] >= 4
    assert res["is_verified"] is True

    # Check that each category is reported separately (not grouped into only 1-2 generic buckets)
    cat_counts = res["category_counts"]
    assert cat_counts["government_id"] >= 1
    assert cat_counts["address"] >= 1
    assert cat_counts["date_of_birth"] >= 1
    assert cat_counts["biometric_face"] >= 1
    assert cat_counts["qr_code"] >= 1

    # Check that recommendations are provided for identity documents
    assert len(res.get("recommendations", [])) >= 3

    # Check that 5-part explanations are present on every detection
    for d in res["detections"]:
        assert "where" in d
        assert "what" in d
        assert "why" in d
        assert ("possible_problem" in d or "what_could_happen" in d)
        assert "what_to_do" in d
