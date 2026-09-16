"""
Unit and Integration Tests for Privacy Chat Files & Photos Upload/Update Engine.
File: tests/test_privacy_chat_attachments.py
"""

import io
import json
import base64
import pytest
from PIL import Image, ImageDraw

from backend.services.tools_ecosystem import (
    analyze_image_bytes,
    process_file_content,
    analyze_dataset,
    execute_tool_with_ai_trust
)
from backend.services.evidence_risk import run_full_analysis
from privacy_engine.sanitizer import PrivacySanitizer


def _create_synthetic_id_image() -> bytes:
    img = Image.new("RGB", (500, 300), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (490, 290)], outline=(56, 189, 248), width=2)
    draw.text((20, 20), "DEMO EMPLOYEE ID", fill=(248, 250, 252))
    draw.text((20, 60), "Name: Alex Smith", fill=(248, 250, 252))
    draw.text((20, 90), "Aadhaar: 9918-4019-2011", fill=(248, 250, 252))
    draw.text((20, 120), "Phone: +91 98765-43210", fill=(248, 250, 252))
    draw.text((20, 150), "Email: alex.smith@company.org", fill=(248, 250, 252))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_attachment_processing_and_privacy():
    img_bytes = _create_synthetic_id_image()
    assert len(img_bytes) > 0

    img_res = analyze_image_bytes(img_bytes)
    assert "exif_stripped" in img_res
    assert img_res["exif_stripped"] is True
    assert "privacy_scan" in img_res
    assert "image_format" in img_res


def test_document_attachment_processing_and_sanitization():
    doc_text = (
        "CONFIDENTIAL MEDICAL INTAKE\n"
        "Patient: John Doe\n"
        "Aadhaar: 9918-4019-2011\n"
        "Email: john.doe@healthcorp.com\n"
        "Diagnosis: Type 2 Diabetes\n"
        "Prescription: Metformin 500mg daily"
    )
    doc_bytes = doc_text.encode("utf-8")
    doc_res = process_file_content(doc_bytes, "patient_intake.txt")

    assert doc_res["parsing_status"] == "SUCCESS"
    assert doc_res["total_char_length"] > 0

    sanitizer = PrivacySanitizer()
    sanitized = sanitizer.sanitize_text(doc_res["extracted_text_preview"], mode="REDACT")
    san_text = sanitized["sanitized_text"]

    assert "9918-4019-2011" not in san_text
    assert "john.doe@healthcorp.com" not in san_text
    assert "[AADHAAR_REDACTED]" in san_text or "REDACTED" in san_text


def test_csv_data_attachment_processing():
    csv_data = (
        "Quarter,Region,Revenue,Contact_Email\n"
        "Q1,North America,1200000,sales-na@cloud.org\n"
        "Q2,APAC,1450000,sales-apac@cloud.org\n"
        "Q3,EMEA,1100000,sales-emea@cloud.org"
    )
    csv_bytes = csv_data.encode("utf-8")
    data_res = analyze_dataset(csv_bytes, "sales_q3.csv")

    assert data_res["rows"] == 3
    assert "Revenue" in data_res["columns"]
    assert len(data_res["preview_records"]) == 3


def test_multimodal_grounded_tool_execution():
    query = "Analyze the attached customer records and identify key revenue figures"
    doc_payload = "Customer: ACME Corp | Revenue: $50,000 | Contact: contact@acme.com"

    # Verify tool execution wrapper with trust receipt
    result = execute_tool_with_ai_trust("📎 Files Parser", process_file_content, doc_payload.encode("utf-8"), "acme.txt")
    assert result["status"] == "SUCCESS"
    assert result["decision"] in ("ALLOW", "WARN", "SANITIZE", "PENDING_USER_DECISION", "BLOCKED")
    assert "trust_receipt" in result
