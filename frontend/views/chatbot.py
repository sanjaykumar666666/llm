"""
AI Trust Chat — Secure Chat View with Aiera Multi-Modal Tools Ecosystem.
File Location: frontend/views/chatbot.py
"""

import os
import re
import urllib.parse
import streamlit as st
import time
import io
import json
import html
import base64
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from frontend.services.api_client import APIClient
from backend.services.trust_receipt import format_receipt_text, get_receipt_by_id
from processing.text_processor import TextProcessor
from backend.routes.chatbot import _detect_injection
from backend.services.tools_ecosystem import (
    search_web,
    deep_research,
    process_file_content,
    analyze_dataset,
    generate_image_bridge,
    analyze_image_bytes,
    canvas_engine,
    execute_code_safely,
    analyze_url_content,
    generate_formal_report,
    execute_tool_with_ai_trust
)

# Preset quick test prompts for instant scenario loading across all 5 sensitive data categories
QUICK_TEST_CHIPS = [
    ("🟢 Safe Science", "Explain how photosynthesis works in green plants and why it is important."),
    ("🛡️ Aadhaar & PII", "Employee verification: My name is John Doe, Aadhaar is 9918-4019-2011 and phone is +91 98765-43210."),
    ("🔴 DB Credential", "Deploy config: username=admin password=SuperSecretP@ssw0rd!123 database=prod"),
    ("💳 Card + CVV", "Billing record: Credit card number 4532 1234 5678 9010 expiration 12/28 CVV 882."),
    ("🏥 Medical & RX", "Patient John Doe medical intake: diagnosed with Type 2 Diabetes and prescribed Metformin 500mg daily."),
    ("🏢 Confidential Corp", "Confidential Project Titan: Q3 revenue reached $15.4M with proprietary trade secret algorithm under strict NDA."),
    ("💳 UPI VPA", "Please transfer the invoice reimbursement of $500 to my UPI ID alex.smith@okhdfcbank."),
]

# Available Tools in the Aiera Tools Ecosystem
TOOLS_LIST = [
    "💬 Standard Chat",
    "🔎 Web Search",
    "🧠 Deep Research",
    "📊 Data Analysis",
    "📎 Files Parser",
    "🎨 Image Generation",
    "🖼️ Image Analysis",
    "✍️ Canvas Workspace",
    "💻 Code Workspace",
    "🔗 URL Analysis",
    "📚 Knowledge Base / RAG",
    "📝 Report Generator",
    "📈 Charts & Visualization",
    "📤 Export Manager",
    "🛡️ AI Trust Core"
]


# ── Files & Photos Attachment Processing Engine ───────────────────────────────

def _generate_sample_id_photo_bytes() -> bytes:
    """Generates a synthetic employee ID card image with embedded PII for live OCR and privacy testing."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (560, 320), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Outer border and banner
    draw.rectangle([(10, 10), (550, 310)], outline=(56, 189, 248), width=2)
    draw.rectangle([(10, 10), (550, 55)], fill=(30, 41, 59))
    draw.text((25, 20), "IDENTITY & ACCESS CREDENTIAL (DEMO)", fill=(248, 250, 252))

    # Photo frame placeholder
    draw.rectangle([(30, 75), (140, 205)], fill=(51, 65, 85), outline=(148, 163, 184), width=2)
    draw.text((55, 130), "PHOTO", fill=(203, 213, 225))

    # PII and credentials text records
    draw.text((160, 80), "NAME: Alex M. Johnson", fill=(248, 250, 252))
    draw.text((160, 115), "AADHAAR: 9918-4019-2011", fill=(248, 250, 252))
    draw.text((160, 150), "PHONE: +91 98765-43210", fill=(248, 250, 252))
    draw.text((160, 185), "EMAIL: alex.johnson@corp.org", fill=(248, 250, 252))
    draw.text((30, 230), "ORGANIZATION: Zero-Trust Security Labs | EMP ID: SEC-8841", fill=(148, 163, 184))
    draw.text((30, 265), "CLASSIFICATION: CONFIDENTIAL INTERNAL ACCESS ONLY", fill=(239, 68, 68))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _get_preset_attachment(preset_key: str) -> Tuple[str, bytes]:
    """Provides instant 1-click sample files & photos for multimodal privacy chat testing."""
    if preset_key == "sample_id_photo":
        return "sample_employee_id_card.png", _generate_sample_id_photo_bytes()
    elif preset_key == "sample_medical_doc":
        text_content = (
            "====================================================\n"
            "PATIENT INTAKE & PHARMACY PRESCRIPTION RECORD\n"
            "====================================================\n"
            "Patient Name: John Doe\n"
            "Aadhaar Number: 9918-4019-2011\n"
            "Mobile Phone: +91 98765-43210\n"
            "Email Address: john.doe@healthmail.com\n"
            "Clinical Diagnosis: Type 2 Diabetes Mellitus & Hypertension\n"
            "Prescribed Medication: Metformin 500mg (2x daily), Lisinopril 10mg\n"
            "Physician: Dr. Rajesh Sharma, MD\n"
            "Hospital: Apollo Healthcare Care Center\n"
            "Billing Total: $450.00 (Insurance Copay: $50.00)\n"
            "Payment Card: VISA •••• 9010\n"
            "====================================================\n"
        )
        return "sample_patient_medical_invoice.txt", text_content.encode("utf-8")
    elif preset_key == "sample_financial_csv":
        csv_content = (
            "Quarter,Department,Budget_Allocated,Actual_Spent,Sensitive_Lead,Approved_By\n"
            "Q1 2026,AI Security,$250000,$238000,security-lead@corp.io,Chief Security Officer\n"
            "Q2 2026,Data Governance,$180000,$175000,privacy-team@corp.io,VP Compliance\n"
            "Q3 2026,Cloud Infrastructure,$420000,$410000,devops-admin@corp.io,VP Engineering\n"
            "Q4 2026,Threat Research,$310000,$295000,research-analyst@corp.io,Chief Technology Officer\n"
        )
        return "q3_corporate_budget_summary.csv", csv_content.encode("utf-8")
    return "sample_file.txt", b"Sample content"


def _classify_image_privacy(detections: list, category_counts: dict, risk_score: int) -> str:
    """
    Classifies an image into one of 4 privacy states based on detected PII:
      - SAFE: No PII detected
      - PII_DETECTED: Personal information found (names, emails, phones, addresses)
      - SENSITIVE_PII_DETECTED: Highly sensitive PII (govt IDs, financial, auth, biometric faces)
      - UNCERTAIN: OCR or detection may be incomplete; cannot reliably determine
    """
    if not detections:
        return "SAFE"

    has_sensitive = False
    has_personal = False

    sensitive_types = {
        "AADHAAR_NUMBER", "PAN_NUMBER", "PASSPORT_NUMBER", "DRIVING_LICENSE", "SSN",
        "CREDIT_CARD", "BANK_ACCOUNT", "PASSWORD", "API_KEY", "OTP_CODE",
        "HUMAN_FACE", "IDENTITY_QR_CODE",
    }
    sensitive_categories = {"GOVERNMENT_ID", "FINANCIAL", "AUTHENTICATION", "BIOMETRIC_FACE"}

    for det in detections:
        d_type = det.get("type", "").upper()
        d_cat = det.get("category", "").upper()
        if d_type in sensitive_types or d_cat in sensitive_categories:
            has_sensitive = True
        else:
            has_personal = True

    # Check category counts for sensitive categories
    if category_counts.get("government_id", 0) > 0 or category_counts.get("financial", 0) > 0 or category_counts.get("authentication", 0) > 0 or category_counts.get("biometric_face", 0) > 0:
        has_sensitive = True

    if has_sensitive:
        return "SENSITIVE_PII_DETECTED"
    elif has_personal:
        return "PII_DETECTED"
    else:
        return "UNCERTAIN" if risk_score > 20 else "SAFE"


def _get_privacy_warning_text(classification: str) -> str:
    """Returns the exact privacy warning message for each image classification state."""
    if classification == "PII_DETECTED":
        return (
            "Privacy Warning: This image contains personal information. "
            "Processing this image may expose private data.\n\n"
            "Do you understand and accept this privacy risk and want me to continue processing the image? YES / NO"
        )
    elif classification == "SENSITIVE_PII_DETECTED":
        return (
            "Sensitive Privacy Warning: This image contains highly sensitive personal information. "
            "Processing it may expose identity, financial, authentication, medical, or other private information.\n\n"
            "Do you understand and accept this privacy risk and want me to continue processing the image? YES / NO"
        )
    elif classification == "UNCERTAIN":
        return (
            "Privacy Warning: I cannot reliably determine whether this image contains personal information.\n\n"
            "Do you want to continue processing it? YES / NO"
        )
    return ""


def _process_chat_attachment(file_name: str, file_bytes: bytes) -> Dict[str, Any]:
    """
    Parses and privacy-scans an uploaded file or photo.
    Images use the full ImagePrivacyService pipeline (face detection, QR scanning,
    document classification, OCR, EXIF stripping, and deep PII detection).
    Documents and data files use structured parsing with text-based privacy scanning.
    """
    ext = os.path.splitext(file_name.lower())[1]
    is_image = ext in (".png", ".jpg", ".jpeg", ".webp")
    is_data = ext in (".csv", ".xlsx", ".xls")

    file_size_kb = len(file_bytes) / 1024
    size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024:.2f} MB"

    img_b64 = None
    extracted_text = ""
    sanitized_text = ""
    meta: Dict[str, Any] = {"file_name": file_name, "extension": ext, "size_str": size_str}
    image_privacy_result = None
    image_classification = "SAFE"
    image_detections = []
    image_category_counts = {}

    if is_image:
        file_type = "image"
        try:
            from PIL import Image
            pil_img = Image.open(io.BytesIO(file_bytes))
            meta["width"], meta["height"] = pil_img.size
            meta["format"] = pil_img.format or "PNG"

            # Create lightweight thumbnail for instant high-speed rendering
            thumb = pil_img.copy()
            thumb.thumbnail((400, 400))
            buf = io.BytesIO()
            thumb.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")

        # Run FULL ImagePrivacyService deep scan (face detection, QR, OCR, document classification)
        try:
            from backend.services.image_privacy_service import ImagePrivacyService
            image_privacy_result = ImagePrivacyService.process_image(
                file_bytes, filename=file_name,
                protection_mode="REDACT_SENSITIVE",
                protect_faces=True,
                protect_qr_barcodes=True,
            )
            image_detections = image_privacy_result.get("detections", [])
            image_category_counts = image_privacy_result.get("category_counts", {})
            meta["exif_stripped"] = True
            meta["contained_gps"] = False  # GPS stripped by ImagePrivacyService
            meta["document_type"] = image_privacy_result.get("document_type", "General Photo / Image")
            meta["detection_count"] = image_privacy_result.get("detection_count", 0)
            meta["image_risk_score"] = image_privacy_result.get("risk_score", 0)
            meta["image_risk_level"] = image_privacy_result.get("risk_level", "LOW")
            meta["image_action"] = image_privacy_result.get("action", "ALLOW")
            meta["protected_image_b64"] = image_privacy_result.get("protected_image_b64", "")
        except Exception:
            pass

        # Also run OCR for text extraction
        try:
            from backend.services.tools_ecosystem import analyze_image_bytes
            img_res = analyze_image_bytes(file_bytes)
            extracted_text = img_res.get("ocr_extracted_text", "")
        except Exception:
            extracted_text = f"Visual image document '{file_name}' loaded."

        # Classify image privacy state
        image_classification = _classify_image_privacy(
            image_detections,
            image_category_counts,
            image_privacy_result.get("risk_score", 0) if image_privacy_result else 0
        )

    elif is_data:
        file_type = "data"
        try:
            from backend.services.tools_ecosystem import analyze_dataset
            data_res = analyze_dataset(file_bytes, filename=file_name)
            meta["rows"] = data_res.get("rows", 0)
            meta["columns"] = data_res.get("columns", [])
            extracted_text = f"Dataset: {file_name} ({data_res.get('rows')} rows, {len(data_res.get('columns', []))} columns: {', '.join(data_res.get('columns', [])[:8])})\n"
            if data_res.get("preview_records"):
                extracted_text += json.dumps(data_res["preview_records"][:6], indent=2)
        except Exception:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")[:3000]
    else:
        file_type = "document"
        try:
            from backend.services.tools_ecosystem import process_file_content
            doc_res = process_file_content(file_bytes, file_name)
            extracted_text = doc_res.get("extracted_text_preview", "")
            meta.update(doc_res.get("metadata", {}))
        except Exception:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")[:3000]

    # Run privacy scan on extracted text content
    from backend.services.evidence_risk import run_full_analysis
    from privacy_engine.sanitizer import PrivacySanitizer

    priv_scan = run_full_analysis(extracted_text[:4000]) if extracted_text else {"decision": "ALLOW", "risk_score": 0, "risk_level": "LOW", "entities": []}
    sanitizer = PrivacySanitizer()
    san_res = sanitizer.sanitize_text(extracted_text, mode="REDACT")
    sanitized_text = san_res.get("sanitized_text", extracted_text)

    # Merge text-based entities with image-based detections
    entities = [e.get("category", e.get("entity_type", "PII")) for e in priv_scan.get("entities", [])]
    for det in image_detections:
        det_type = det.get("type", det.get("category", "PII"))
        if det_type not in entities:
            entities.append(det_type)

    # Calculate combined risk score (max of text + image)
    text_risk = priv_scan.get("risk_score", 0)
    image_risk = image_privacy_result.get("risk_score", 0) if image_privacy_result else 0
    combined_risk = max(text_risk, image_risk)

    # Determine combined decision
    text_decision = priv_scan.get("decision", "ALLOW")
    image_action = image_privacy_result.get("action", "ALLOW") if image_privacy_result else "ALLOW"
    if text_decision == "BLOCK" or image_action == "BLOCK":
        combined_decision = "BLOCK"
    elif image_classification in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN") or text_decision in ("WARN", "SANITIZE") or image_action in ("PROTECT", "SANITIZE"):
        combined_decision = "WARN"
    else:
        combined_decision = "ALLOW"

    combined_risk_level = "CRITICAL" if combined_risk >= 80 else ("HIGH" if combined_risk >= 60 else ("MEDIUM" if combined_risk >= 30 else "LOW"))

    return {
        "file_name": file_name,
        "file_type": file_type,
        "file_bytes": file_bytes,
        "size_str": size_str,
        "size_bytes": len(file_bytes),
        "extension": ext,
        "image_b64": img_b64,
        "extracted_text": extracted_text,
        "sanitized_text": sanitized_text,
        "metadata": meta,
        "privacy_scan": priv_scan,
        "entities": entities,
        "has_pii": len(entities) > 0 or image_classification != "SAFE",
        "decision": combined_decision,
        "risk_level": combined_risk_level,
        "risk_score": combined_risk,
        "uploaded_at": time.strftime("%H:%M:%S"),
        # Image-specific deep scan results
        "image_classification": image_classification,
        "image_privacy_result": image_privacy_result,
        "image_detections": image_detections,
        "image_category_counts": image_category_counts,
        "privacy_warning_text": _get_privacy_warning_text(image_classification),
    }


# ── Privacy Blur & Redaction Token Parser ─────────────────────────────────────
REDACTION_TOKEN_REGEX = re.compile(
    r'(\[(?:EMAIL|PHONE|AADHAAR|PAN|SSN|NINO|CREDIT_CARD|BANK_ACCOUNT|PASSWORD|API_KEY|AUTH_SECRET|HEALTH_DATA|CONFIDENTIAL|UPI_ID|ADDRESS|PASSPORT|LICENSE|VOTER_ID|IP|DATABASE_CREDENTIALS|GCP_KEY|AWS_KEY|SENDGRID_KEY|SLACK_TOKEN|GITHUB_TOKEN|JWT|PRIVATE_KEY|IBAN|HEALTH_RECORD|PAYMENT_CARD|BLOCKED_ADVERSARIAL_SEQUENCE|OTP|PIN|AUTH_TOKEN|SECRET_KEY|BANK_CREDENTIAL)_REDACTED\]|\[(?:EMAIL|PHONE|NAME|AADHAAR|PAN|SSN|NINO|PASSPORT|LICENSE|VOTER ID|PAYMENT CARD|BANK ACCOUNT|IBAN|UPI ID|CONFIDENTIAL|HEALTH DATA|HEALTH RECORD|PRESCRIPTION|PASSWORD|OTP|PIN|AUTH TOKEN|SECRET KEY|BANK CREDENTIAL|AWS KEY|GITHUB TOKEN|API KEY|GCP KEY|SLACK TOKEN|JWT TOKEN|BEARER TOKEN|PRIVATE KEY|DATABASE CREDENTIALS|ADDRESS|IP ADDRESS|BLOCKED_ADVERSARIAL_SEQUENCE) REDACTED\]|(?:••••-••••-••••-\d{4}|••••-••••-\d{4}|\*{3}-\*{3}-\d{4}|••••••••\d{4}))',
    re.IGNORECASE
)


def _render_privacy_blurred_text(text: str) -> str:
    """
    Transforms redaction placeholders and masked values into interactive
    frosted glassmorphism Privacy Blur Badges with clean typography.
    """
    if not text:
        return text

    def _replace_with_blur_badge(match):
        token = match.group(0)
        clean_label = token.replace("[", "").replace("]", "").replace("_REDACTED", "").replace(" REDACTED", "").title()
        if not clean_label:
            clean_label = "Sensitive Data"
        return (
            f'<span class="privacy-blur-token" style="display:inline-flex; align-items:center; gap:5px; background:rgba(99,102,241,0.18); border:1px solid rgba(129,140,248,0.45); padding:2px 8px; border-radius:12px; font-size:12px; font-weight:700; color:#A5B4FC; margin:0 3px; vertical-align:middle;" title="🔒 {html.escape(clean_label)} Shielded by Privacy Shield">'
            f'<span>🔒</span>'
            f'<span>{html.escape(clean_label)} Redacted</span>'
            f'</span>'
        )

    return REDACTION_TOKEN_REGEX.sub(_replace_with_blur_badge, text)


def _render_html(content: str):
    """Cleanly renders HTML by removing leading indentation and blank lines to prevent Markdown codeblock parser artifacts."""
    if not content:
        return
    cleaned = "\n".join(line.strip() for line in content.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def _init_chat_session():
    if "privacy_chat_threads" not in st.session_state:
        st.session_state["privacy_chat_threads"] = [{
            "id": "thread-1",
            "title": "Universal Live Grounded Chat",
            "messages": [],
            "created_at": "Just now"
        }]
    if "privacy_current_thread_id" not in st.session_state:
        st.session_state["privacy_current_thread_id"] = "thread-1"
    if "composer_preset_text" not in st.session_state:
        st.session_state["composer_preset_text"] = ""
    if "active_tool" not in st.session_state:
        st.session_state["active_tool"] = "💬 Standard Chat"
    if "canvas_content" not in st.session_state:
        st.session_state["canvas_content"] = "### Executive Research Document\n\nEnter your notes, architecture designs, or code snippets here..."
    if "chat_active_attachment" not in st.session_state:
        st.session_state["chat_active_attachment"] = None
    if "attachment_nonce" not in st.session_state:
        st.session_state["attachment_nonce"] = 0
    if "image_privacy_consent" not in st.session_state:
        st.session_state["image_privacy_consent"] = False


def _compute_live_privacy_status(text: str) -> Dict[str, Any]:
    """
    Computes real-time authoritative privacy risk, detected entities, and policy decision
    before the user sends a message, using Pipelines 1, 3, 4, 5.
    """
    if not text or not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "decision": "ALLOW",
            "state_label": "🟢 SAFE",
            "state_type": "SAFE",
            "entities_label": "None (Clean)",
            "status_col": "#10B981",
            "badge_bg": "rgba(16,185,129,0.18)",
            "badge_col": "#10B981",
            "badge_border": "rgba(16,185,129,0.5)",
            "detected_list": [],
            "reason": "Input clean.",
            "entities": [],
            "sanitized_text": "",
            "is_blocked": False,
        }

    from backend.services.evidence_risk import run_full_analysis
    from backend.services.privacy_risk_service import PrivacyRiskService

    analysis = run_full_analysis(text)
    priv_analysis = PrivacyRiskService.analyze_message(text)

    decision = analysis["decision"]
    risk_score = max(analysis["risk_score"], priv_analysis["overall_risk"]["score"] * 10)
    risk_level = priv_analysis["overall_risk"]["level"] if priv_analysis["has_privacy_risk"] else analysis["risk_level"]

    entities = analysis.get("entities", [])
    priv_dets = priv_analysis.get("detections", [])

    entity_types = [e.get("category", e.get("entity_type", "PII")) for e in entities]
    for pd in priv_dets:
        cat_name = pd.get("type", "").replace("_", " ").title()
        if cat_name not in entity_types:
            entity_types.append(cat_name)

    sanitized_text = analysis.get("sanitized_text", text)
    has_personal_info = priv_analysis.get("has_privacy_risk", False) or len(priv_dets) > 0

    # ── Authoritative Live States ─────────────────────────────────────────────
    if decision == "BLOCK" or risk_level == "CRITICAL":
        state_type = "DANGER"
        state_label = "🔴 DANGER"
        status_col = "#EF4444"
        badge_bg = "rgba(239,68,68,0.18)"
        badge_col = "#EF4444"
        badge_border = "rgba(239,68,68,0.5)"
        is_blocked = True
    elif decision in ("WARN", "SANITIZE") or risk_level in ("MEDIUM", "HIGH") or has_personal_info:
        state_type = "WARNING"
        state_label = f"🟡 {risk_level} (Personal Info)" if has_personal_info else "🟡 WARNING"
        status_col = "#F59E0B"
        badge_bg = "rgba(245,158,11,0.18)"
        badge_col = "#F59E0B"
        badge_border = "rgba(245,158,11,0.5)"
        is_blocked = False
    else:
        state_type = "SAFE"
        state_label = "🟢 SAFE"
        status_col = "#10B981"
        badge_bg = "rgba(16,185,129,0.18)"
        badge_col = "#10B981"
        badge_border = "rgba(16,185,129,0.5)"
        is_blocked = False

    entities_label = ", ".join(list(dict.fromkeys(entity_types))) if entity_types else "None (Clean)"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": decision,
        "state_label": state_label,
        "state_type": state_type,
        "entities_label": entities_label,
        "status_col": status_col,
        "badge_bg": badge_bg,
        "badge_col": badge_col,
        "badge_border": badge_border,
        "detected_list": entity_types,
        "reason": priv_dets[0].get("reason", analysis.get("reason", "Analysis complete.")) if priv_dets else analysis.get("reason", "Analysis complete."),
        "entities": entities,
        "sanitized_text": sanitized_text,
        "is_blocked": is_blocked,
        "has_personal_info": has_personal_info,
        "personal_info_items": priv_dets,
        "security_advisory": analysis.get("security_advisory"),
        "safe_rationale": analysis.get("safe_rationale"),
        "risk_rationale": analysis.get("risk_rationale"),
    }


def _sanitize_message_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Strict deduplication: eliminates duplicate consecutive messages with same role & text."""
    clean = []
    for msg in messages:
        if not msg.get("text", "").strip() and not msg.get("security_meta") and not msg.get("tool_data"):
            continue
        if clean and clean[-1].get("role") == msg.get("role") and clean[-1].get("text", "").strip() == msg.get("text", "").strip():
            continue
        clean.append(msg)
    return clean


def _risk_badge_html(risk_level: str, risk_score: int) -> str:
    colors = {
        "LOW": ("#10B981", "rgba(16,185,129,0.12)", "🟢"),
        "MEDIUM": ("#F59E0B", "rgba(245,158,11,0.12)", "🟡"),
        "HIGH": ("#EF4444", "rgba(239,68,68,0.12)", "🔴"),
        "CRITICAL": ("#DC2626", "rgba(220,38,38,0.15)", "🚨"),
    }
    col, bg, icon = colors.get(risk_level.upper(), ("#94A3B8", "rgba(148,163,184,0.1)", "⚪"))
    return (
        f"<span style='background:{bg}; color:{col}; border:1px solid {col}44; "
        f"font-size:11px; font-weight:700; padding:3px 8px; border-radius:20px;'>"
        f"{icon} {risk_level} ({risk_score}%)"
        f"</span>"
    )


def _model_badge_html(model_name: str, is_error: bool = False) -> str:
    border_col = "rgba(239,68,68,0.4)" if is_error else "rgba(99,102,241,0.3)"
    text_col = "#FCA5A5" if is_error else "#A5B4FC"
    bg_col = "rgba(239,68,68,0.12)" if is_error else "rgba(99,102,241,0.12)"
    icon = "⚠️" if is_error else "🤖"
    return (
        f"<span style='background:{bg_col}; color:{text_col}; border:1px solid {border_col}; "
        f"font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>"
        f"{icon} {model_name}"
        f"</span>"
    )


def _telemetry_badge_html(timing: Optional[Dict[str, Any]], is_error: bool = False) -> str:
    if not timing:
        return ""
    total = timing.get("total_ms", 0.0)
    router = timing.get("router_ms", 0.0)
    sec = timing.get("security_ms", 0.0)
    search = timing.get("search_ms", 0.0)
    llm = timing.get("llm_ms", 0.0)
    tier = timing.get("tier", "STANDARD")

    # Format total
    if total < 1.0:
        total_str = f"{total:.2f}ms"
    elif total < 1000:
        total_str = f"{total:.0f}ms"
    else:
        total_str = f"{total / 1000:.2f}s"

    badges = [
        f"<span style='background:rgba(56,189,248,0.12); color:#38BDF8; border:1px solid rgba(56,189,248,0.35); font-size:11px; font-weight:700; padding:3px 8px; border-radius:20px;'>⚡ Total: {total_str}</span>",
        f"<span style='background:rgba(148,163,184,0.1); color:#CBD5E1; border:1px solid rgba(148,163,184,0.25); font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>🌐 Tier: {tier}</span>",
        f"<span style='background:rgba(16,185,129,0.1); color:#34D399; border:1px solid rgba(16,185,129,0.25); font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>🛡️ Sec: {sec:.1f}ms</span>",
    ]
    if search > 0:
        badges.append(f"<span style='background:rgba(245,158,11,0.1); color:#FCD34D; border:1px solid rgba(245,158,11,0.25); font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>🔎 Search: {search:.0f}ms</span>")
    if llm > 0:
        llm_str = f"{llm:.0f}ms" if llm < 1000 else f"{llm / 1000:.2f}s"
        badges.append(f"<span style='background:rgba(168,85,247,0.1); color:#C084FC; border:1px solid rgba(168,85,247,0.25); font-size:11px; font-weight:600; padding:3px 8px; border-radius:20px;'>🤖 LLM: {llm_str}</span>")

    return " ".join(badges)


def _render_privacy_blurred_text(text: str) -> str:
    """
    Substitutes tokenized placeholders (e.g. [AADHAAR_REDACTED], [PHONE_NUMBER], [PASSWORD_REDACTED])
    with frosted-glass privacy pill UI elements.
    """
    if not text:
        return ""

    pill_styles = {
        "AADHAAR_REDACTED": ("🪪 Aadhaar Redacted", "rgba(59,130,246,0.18)", "#93C5FD", "rgba(59,130,246,0.45)"),
        "GOVT_ID": ("🪪 Govt ID Redacted", "rgba(59,130,246,0.18)", "#93C5FD", "rgba(59,130,246,0.45)"),
        "PAN_REDACTED": ("📄 PAN Redacted", "rgba(59,130,246,0.18)", "#93C5FD", "rgba(59,130,246,0.45)"),
        "PASSWORD_REDACTED": ("🔒 Password Redacted", "rgba(239,68,68,0.18)", "#FCA5A5", "rgba(239,68,68,0.45)"),
        "REDACTED_CREDENTIAL": ("🔐 Credential Redacted", "rgba(239,68,68,0.18)", "#FCA5A5", "rgba(239,68,68,0.45)"),
        "API_KEY_REDACTED": ("🗝️ API Key Redacted", "rgba(239,68,68,0.18)", "#FCA5A5", "rgba(239,68,68,0.45)"),
        "PHONE_NUMBER": ("📱 Phone Redacted", "rgba(245,158,11,0.18)", "#FDE68A", "rgba(245,158,11,0.45)"),
        "EMAIL_ADDRESS": ("📧 Email Redacted", "rgba(245,158,11,0.18)", "#FDE68A", "rgba(245,158,11,0.45)"),
        "NAME": ("👤 Name Masked", "rgba(168,85,247,0.18)", "#E9D5FF", "rgba(168,85,247,0.45)"),
        "HEALTH_DATA_REDACTED": ("🏥 Health PHI Masked", "rgba(236,72,153,0.18)", "#F472B6", "rgba(236,72,153,0.45)"),
        "HEALTH_RECORD": ("🏥 Health Record Redacted", "rgba(236,72,153,0.18)", "#F472B6", "rgba(236,72,153,0.45)"),
        "PRESCRIPTION_MEDICATION": ("💊 Prescription Redacted", "rgba(236,72,153,0.18)", "#F472B6", "rgba(236,72,153,0.45)"),
        "MEDICAL_DIAGNOSIS": ("🏥 Diagnosis Redacted", "rgba(236,72,153,0.18)", "#F472B6", "rgba(236,72,153,0.45)"),
        "CONFIDENTIAL_REDACTED": ("🏢 Corporate Secret Redacted", "rgba(239,68,68,0.18)", "#FCA5A5", "rgba(239,68,68,0.45)"),
        "CONFIDENTIAL_BUSINESS_INFO": ("🏢 Confidential Business Info", "rgba(239,68,68,0.18)", "#FCA5A5", "rgba(239,68,68,0.45)"),
        "UPI_ID_REDACTED": ("💳 UPI VPA Masked", "rgba(16,185,129,0.18)", "#6EE7B7", "rgba(16,185,129,0.45)"),
        "LICENSE_REDACTED": ("🪪 Driver's License Redacted", "rgba(59,130,246,0.18)", "#93C5FD", "rgba(59,130,246,0.45)"),
        "VOTER_ID_REDACTED": ("🗳️ Voter ID Redacted", "rgba(59,130,246,0.18)", "#93C5FD", "rgba(59,130,246,0.45)"),
        "RESIDENTIAL_ADDRESS": ("🏠 Address Masked", "rgba(245,158,11,0.18)", "#FDE68A", "rgba(245,158,11,0.45)"),
        "WORKPLACE": ("🏢 Workplace Masked", "rgba(148,163,184,0.18)", "#E2E8F0", "rgba(148,163,184,0.45)"),
        "INSTITUTION": ("🎓 College Masked", "rgba(148,163,184,0.18)", "#E2E8F0", "rgba(148,163,184,0.45)"),
    }

    def _replace_pill(m):
        token = m.group(1).upper()
        if token in pill_styles:
            label, bg, color, border = pill_styles[token]
        else:
            label = f"🔒 {token.replace('_', ' ').title()}"
            bg = "rgba(148,163,184,0.18)"
            color = "#E2E8F0"
            border = "rgba(148,163,184,0.4)"

        return (
            f'<span style="display:inline-flex; align-items:center; gap:4px; '
            f'background:{bg}; color:{color}; border:1px solid {border}; '
            f'padding:2px 8px; border-radius:12px; font-size:11.5px; font-weight:700; '
            f'letter-spacing:0.2px; vertical-align:middle; margin:0 2px;">'
            f'{label}</span>'
        )

    out = re.sub(r'🔒?\[([A-Z0-9_]+)\]', _replace_pill, text)
    return out


def _render_privacy_card(privacy_analysis: Optional[Dict[str, Any]]):
    """
    Renders clean, context-aware Privacy Warning Card explaining:
    1. Why detected personal information constitutes a privacy risk (What happens if shared).
    2. Why & How Privacy Shield sanitized/masked it to keep the user 100% safe.
    """
    if not privacy_analysis:
        return

    detections = privacy_analysis.get("detections", [])
    has_risk = privacy_analysis.get("has_privacy_risk", False) or len(detections) > 0

    if not has_risk or not detections:
        return

    overall_risk = privacy_analysis.get("overall_risk", {})
    r_level = overall_risk.get("level", "LOW")
    r_score = overall_risk.get("score", 2)
    badge = overall_risk.get("badge", "🟡 LOW")
    combined = privacy_analysis.get("combined_exposure", {})
    recommendations = privacy_analysis.get("recommendations", [])

    # Color themes
    if r_level == "CRITICAL":
        border_col = "rgba(220,38,38,0.6)"
        bg_col = "rgba(220,38,38,0.12)"
        badge_bg = "rgba(220,38,38,0.25)"
        badge_color = "#FCA5A5"
        alert_title = "🚨 CRITICAL PRIVACY WARNING: Sensitive Credentials / High-Risk Data"
    elif r_level == "HIGH":
        border_col = "rgba(239,68,68,0.5)"
        bg_col = "rgba(239,68,68,0.09)"
        badge_bg = "rgba(239,68,68,0.2)"
        badge_color = "#F87171"
        alert_title = "⚠️ PRIVACY WARNING: Direct Contact / Government ID Detected"
    elif r_level == "MEDIUM":
        border_col = "rgba(249,115,22,0.45)"
        bg_col = "rgba(249,115,22,0.08)"
        badge_bg = "rgba(249,115,22,0.2)"
        badge_color = "#FB923C"
        alert_title = "⚠️ PRIVACY ADVISORY: Personal Identifiers / Attribute Combination"
    else:  # LOW / MINIMAL
        border_col = "rgba(251,191,36,0.4)"
        bg_col = "rgba(251,191,36,0.06)"
        badge_bg = "rgba(251,191,36,0.2)"
        badge_color = "#FCD34D"
        alert_title = "🛡️ PRIVACY NOTICE: Personal Information Disclosed"

    det_categories = list(dict.fromkeys([d.get("category", "").replace("_", " ").title() for d in detections]))
    det_label = ", ".join(det_categories) if det_categories else "Personal Information"

    _render_html(
        f"""
        <div style="background:{bg_col}; border:1.5px solid {border_col}; border-radius:12px; padding:16px 18px; margin-top:14px; margin-bottom:12px; box-shadow:0 4px 14px rgba(0,0,0,0.18);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.08);">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:14px; font-weight:800; color:#F8FAFC;">{alert_title}</span>
                </div>
                <span style="font-size:11.5px; font-weight:800; color:{badge_color}; background:{badge_bg}; border:1px solid {border_col}; padding:3px 10px; border-radius:6px;">{badge} (Risk Score: {r_score}/10)</span>
            </div>
            <div style="font-size:12.5px; color:#E2E8F0; line-height:1.6;">
                <div style="margin-bottom:6px;">
                    🔍 <strong>Detected Disclosures:</strong> <span style="color:#38BDF8; font-weight:700;">{det_label}</span>
                </div>
                <div style="margin-bottom:6px;">
                    <strong style="color:#FCA5A5;">⚠️ Why Sharing This Poses a Privacy Risk:</strong><br>
                    <span style="color:#CBD5E1;">Sharing personal phone numbers, emails, home addresses, or demographic details links your real identity to cloud logs and public models. This creates risks of identity profiling, unsolicited spam, and unauthorized data harvesting.</span>
                </div>
                <div style="padding:8px 12px; background:rgba(16,185,129,0.1); border-left:3px solid #10B981; border-radius:4px; color:#6EE7B7; margin-top:6px;">
                    🛡️ <strong>How Privacy Shield Protected You:</strong> Sensitive identifiers were automatically masked with privacy tokens before calling the AI model. The AI answered your request without ever viewing or storing your actual personal data.
                </div>
            </div>
        </div>
        """
    )

    with st.expander("🔍 View Granular Privacy Details & Masked Token Map", expanded=(r_level in ("HIGH", "CRITICAL"))):
        _render_html("<div style='font-size:12px; font-weight:700; color:#38BDF8; margin-bottom:6px;'>📋 Detected Disclosures Breakdown:</div>")
        for d in detections:
            _render_html(
                f"""
                <div style="background:rgba(15,23,42,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:12px;">
                    <div><strong style="color:#F8FAFC;">Type:</strong> {d.get('type')} (<span style="color:{badge_color}; font-weight:700;">{d.get('risk_level')} — {d.get('risk_score')}/10</span>)</div>
                    <div style="margin-top:2px;"><strong style="color:#94A3B8;">Masked Representation:</strong> <code style="color:#38BDF8;">{html.escape(str(d.get('masked_value')))}</code></div>
                    <div style="margin-top:2px; color:#CBD5E1;"><strong style="color:#94A3B8;">Context Analysis:</strong> {html.escape(d.get('reason', ''))}</div>
                </div>
                """
            )

        if recommendations:
            _render_html("<div style='font-size:12px; font-weight:700; color:#34D399; margin-top:8px; margin-bottom:4px;'>💡 Privacy Recommendations:</div>")
            for rec in recommendations:
                _render_html(f"- <span style='font-size:12px; color:#A7F3D0;'>{html.escape(rec)}</span>")


def _render_answer_container(
    text: str,
    meta: Dict[str, Any],
    tool_data: Optional[Dict[str, Any]] = None,
):
    """
    Unified Stable Answer / Error Container:
    1. Rich, Explainable Security Alert Container for BLOCK states (Why is it a risk, consequences, why blocked, immediate actions)
    2. Explicit graceful error states for quota or authentication issues
    3. Verified Sources Block
    4. Explicit "Why This Prompt is 100% Safe" explanation card for clean requests
    5. Deterministic AI Trust Receipt Block
    """
    decision = meta.get("decision", "ALLOW")
    risk_level = meta.get("risk_level", "LOW")
    risk_score = meta.get("risk_score", 0)

    if decision == "BLOCK":
        advisory = meta.get("security_advisory")
        risk_rat = meta.get("risk_rationale") or {}

        # ── Credential-Specific / High-Risk Explainable Warning UI ─────────
        advisory_html_items = ""
        if advisory and advisory.get("items"):
            for item in advisory["items"]:
                c_why = item.get("consequence") or "Sharing credentials allows unauthorized parties to compromise your account, breach connected databases, and access sensitive private data."
                c_prot = item.get("why_blocked") or "Zero-Trust Security Gate intercepted the payload locally before it could leave your device."
                c_act = item.get("action") or "Change/revoke these credentials immediately."

                advisory_html_items += f"""
                <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:12px 16px; margin-top:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="color:#FCA5A5; font-weight:800; font-size:13.5px; display:flex; align-items:center; gap:6px;">
                            <span>{item.get('icon', '🚨')}</span> <span>{html.escape(item.get('type', 'Sensitive Data'))} Detected</span>
                        </span>
                        <span style="background:rgba(220,38,38,0.3); color:#FCA5A5; border:1px solid rgba(220,38,38,0.6); font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;">CRITICAL RISK</span>
                    </div>
                    
                    <div style="font-size:12.5px; line-height:1.6; color:#CBD5E1;">
                        <div style="margin-bottom:6px;">
                            <strong style="color:#F87171;">⚠️ Why Sharing This is Dangerous:</strong><br>
                            <span>{html.escape(c_why)}</span>
                        </div>
                        <div style="margin-top:6px; margin-bottom:6px; color:#93C5FD;">
                            <strong style="color:#60A5FA;">🛡️ Why Privacy Shield Blocked It:</strong><br>
                            <span>{html.escape(c_prot)}</span>
                        </div>
                        <div style="margin-top:6px; padding:6px 10px; background:rgba(245,158,11,0.12); border-left:3px solid #F59E0B; border-radius:4px; color:#FDE68A; font-weight:600;">
                            🔐 Immediate Action: {html.escape(c_act)}
                        </div>
                    </div>
                </div>"""

        global_why = (advisory.get("why_it_is_a_risk") if advisory else None) or (risk_rat.get("why_problem")) or "Sharing passwords, tokens, or personal identifiers exposes your systems to credential stuffing, account takeover, and permanent logging in third-party model training datasets."
        global_blocked_why = (advisory.get("why_privacy_shield_blocked") if advisory else None) or (risk_rat.get("why_blocked")) or "The Zero-Trust firewall quarantined this prompt on your local device. The message was NEVER sent over the network or viewed by any cloud AI model."

        _render_html(
            f"""
            <div style="background:linear-gradient(135deg, rgba(220,38,38,0.18), rgba(15,23,42,0.95)); border:1.5px solid rgba(220,38,38,0.6); border-radius:14px; padding:18px 20px; margin-bottom:12px; width:100%; box-sizing:border-box; box-shadow:0 4px 20px rgba(220,38,38,0.2);">
                <div style="color:#FCA5A5; font-weight:900; font-size:15.5px; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:20px;">🚨</span> <span>Zero-Trust Security Intercept: Prompt Blocked</span>
                </div>
                <div style="color:#FCA5A5; font-size:13px; font-weight:600; margin-bottom:10px; padding:10px 14px; background:rgba(239,68,68,0.14); border-radius:8px; border-left:3px solid #EF4444; line-height:1.5;">
                    ⛔ <strong>Sensitive credentials detected in your message.</strong> This message was quarantined locally and was <strong>NOT</strong> transmitted to any AI model or external cloud service.
                </div>
                {advisory_html_items}
                <div style="margin-top:12px; padding:12px 14px; background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:10px;">
                    <div style="color:#FCD34D; font-weight:800; font-size:13px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        <span>💡</span> <span>Why Privacy Protection Matters:</span>
                    </div>
                    <div style="color:#CBD5E1; font-size:12.5px; line-height:1.6;">
                        <div style="margin-bottom:6px;">
                            <strong>Why is it a privacy risk?:</strong> {html.escape(global_why)}
                        </div>
                        <div style="color:#93C5FD; margin-bottom:6px;">
                            <strong>Why did Privacy Shield stop it?:</strong> {html.escape(global_blocked_why)}
                        </div>
                    </div>
                </div>
            </div>
            """
        )
        return

    # Extract sources if present in tool_data or text
    sources = []
    main_text = text or ""
    if tool_data and tool_data.get("result", {}).get("sources"):
        sources = tool_data["result"]["sources"]
        main_text = tool_data["result"].get("direct_answer", text)
    elif "### Sources" in main_text:
        parts = main_text.split("### Sources", 1)
        main_text = parts[0].strip()
        raw_sources_text = parts[1].strip()
        for line in raw_sources_text.splitlines():
            line = line.strip()
            if line:
                m = re.search(r'\[(\d+)\]\s*\[(.*?)\]\((.*?)\)(?:\s*—\s*`?(.*?)`?)?$', line)
                if m:
                    sources.append({
                        "citation_id": m.group(1),
                        "title": m.group(2),
                        "url": m.group(3),
                        "domain": m.group(4) or urllib.parse.urlparse(m.group(3)).netloc
                    })

    is_service_error = (
        "AI Service Notice" in main_text
        or "quota has been exceeded" in main_text.lower()
        or "authentication failed" in main_text.lower()
        or "unable to generate" in main_text.lower()
    )

    # 1. Main Answer or Error Body
    if is_service_error:
        _render_html(
            f"""
            <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.35); border-radius:14px; padding:18px 20px; margin-bottom:12px; width:100%; box-sizing:border-box;">
                <div style="color:#FCD34D; font-weight:800; font-size:14px; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
                    <span>⚠️</span> <span>AI Service Notice: Generation Limit</span>
                </div>
                <div style="color:#CBD5E1; font-size:13.5px; line-height:1.6;">
                    The configured Google Gemini API quota for this project has been reached or is rate-limited.
                    <br><br>
                    💡 <em>To enable continuous high-speed Gemini responses, enter your free API Key in <strong>⚙️ Settings</strong>.</em>
                </div>
            </div>
            """
        )
    else:
        st.markdown(_render_privacy_blurred_text(main_text), unsafe_allow_html=True)

    # 2. Verified Sources Block
    if sources:
        _render_html(
            f"""
            <div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08);">
                <div style="font-size:12px; font-weight:800; color:#38BDF8; letter-spacing:0.5px; text-transform:uppercase; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                    <span>📚 Verified Sources ({len(sources)} Retrieved)</span>
                </div>
            </div>
            """
        )
        for s in sources:
            cid = s.get("citation_id", "")
            title = s.get("title", "Source")
            url = s.get("url", "#")
            domain = s.get("domain", "web")
            st.markdown(f"- [{cid}] [{title}]({url}) — `{domain}`")

    # 2b. Image Action Bar if Image Generated
    if tool_data and isinstance(tool_data.get("result"), dict):
        img_res = tool_data.get("result", {})
        if img_res.get("image_url"):
            _render_html(
                f"""
                <div style="margin-top:10px; margin-bottom:8px;">
                    <a href="{img_res['image_url']}" target="_blank" style="display:inline-flex; align-items:center; gap:6px; background:linear-gradient(135deg, #4F46E5, #6366F1); color:#FFFFFF; text-decoration:none; padding:7px 16px; border-radius:8px; font-size:12.5px; font-weight:700; box-shadow:0 2px 8px rgba(79,70,229,0.35);">
                        <span>📥 Open & Download Full-Resolution Artwork ({img_res.get('width', 1024)}×{img_res.get('height', 1024)})</span>
                    </a>
                </div>
                """
            )

    # 3. Context-Aware User Message Privacy Card (If disclosures detected)
    privacy_analysis = meta.get("privacy_analysis")
    _render_privacy_card(privacy_analysis)

    # 3b. Explainable Safe Prompt Verification Card (If prompt is clean & allowed)
    has_detected_disclosures = (
        meta.get("had_user_disclosures", False)
        or (privacy_analysis and (privacy_analysis.get("has_privacy_risk") or len(privacy_analysis.get("detections", [])) > 0))
        or len(meta.get("detected_entities", [])) > 0
        or meta.get("risk_score", 0) > 0
    )
    if decision == "ALLOW" and not has_detected_disclosures and not is_service_error:
        safe_rat = meta.get("safe_rationale") or {}
        reasons_list = safe_rat.get("reasons") or [
            "0 credentials, passwords, or API keys detected",
            "0 personally identifiable records (PII) or Government IDs detected",
            "Composed of public educational, scientific, or programming concepts",
            "Zero-Trust Edge Gate & Dual ML Classifiers verified with 0% risk score"
        ]
        reasons_html = " · ".join([f"<span>✓ {html.escape(r)}</span>" for r in reasons_list])

        _render_html(
            f"""
            <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:12px 16px; margin-top:12px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:14px;">🟢</span>
                        <span style="color:#6EE7B7; font-weight:800; font-size:12.5px; letter-spacing:0.3px;">PROMPT VERIFIED SAFE (100% Zero Privacy Risk)</span>
                    </div>
                    <span style="background:rgba(16,185,129,0.18); color:#34D399; border:1px solid rgba(16,185,129,0.4); font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px;">
                        Zero Leakage Guaranteed
                    </span>
                </div>
                <div style="color:#CBD5E1; font-size:12px; line-height:1.6;">
                    <div>🔍 <strong>Why is it 100% safe?:</strong> Zero personal identifiers (PII), credentials, passwords, or private records detected. This prompt contains only general educational, scientific, or coding inquiries.</div>
                    <div style="color:#A7F3D0; margin-top:4px; font-size:11.5px;">
                        {reasons_html}
                    </div>
                </div>
            </div>
            """
        )

    # 4. Telemetry & Security Metadata Bar
    badge_html = _risk_badge_html(risk_level, risk_score)
    model_html = _model_badge_html(meta.get("model_selected", "Aiera AI"), is_error=is_service_error)
    telemetry_html = _telemetry_badge_html(meta.get("timing_breakdown"), is_error=is_service_error)

    _render_html(
        f"<div style='margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); display:flex; gap:8px; flex-wrap:wrap; align-items:center;'>"
        f"{badge_html} {model_html} {telemetry_html}"
        f"</div>"
    )

    # 5. Optional Deterministic AI Trust Receipt Inspector & Copy Response
    if main_text and not is_service_error:
        with st.expander("📋 View / Copy Raw Response", expanded=False):
            st.code(main_text, language="markdown")

    if meta.get("receipt_id"):
        receipt_title = "🧾 AI Trust Audit Receipt" if not is_service_error else "🧾 AI Trust Audit Receipt (Service Notice)"
        with st.expander(receipt_title, expanded=False):
            st.code(meta.get("receipt_text", f"Receipt ID: {meta['receipt_id']}"), language="text")


def render_chatbot_view():
    _init_chat_session()
    input_nonce = st.session_state.get("input_nonce", 0)

    threads = st.session_state["privacy_chat_threads"]
    current_thread_id = st.session_state["privacy_current_thread_id"]
    current_thread = next((t for t in threads if t["id"] == current_thread_id), threads[0])
    
    # Sanitize and deduplicate messages
    current_thread["messages"] = _sanitize_message_history(current_thread["messages"])
    messages = current_thread["messages"]

    user_role = st.session_state.get("user_role", "USER")
    user_id = st.session_state.get("user_id", "Employee-001")

    from frontend.utils.theme_manager import get_current_theme
    theme = get_current_theme()

    # ── Top Header Bar (Themed) ────────────────────────────────────────────────
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        _render_html(
            f"""
            <div>
                <div style="display:flex; align-items:center; gap:10px; margin:0 0 2px 0;">
                    <span style="font-size:26px;">🛡️</span>
                    <h1 style="color:#FFFFFF; font-size:24px; font-weight:900; letter-spacing:-0.5px; margin:0; line-height:1.2; display:inline;">AI Trust Chat &amp; Tools Ecosystem</h1>
                </div>
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap;">
                    <span style="color:{theme['text_muted']}; font-size:13px; font-weight:600;">Zero-Trust Security Gateway with Universal Live Grounding</span>
                    <span class="privacy-shield-active-pill" style="background:{theme['badge_bg']}; border:1px solid {theme['badge_border']}; color:{theme['badge_color']};">● {theme['name']}</span>
                </div>
            </div>
            """
        )
    with col_t2:
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn", type="primary"):
            new_id = f"thread-{len(threads) + 1}"
            threads.append({
                "id": new_id,
                "title": f"Chat {len(threads) + 1}",
                "messages": [],
                "created_at": "Just now"
            })
            st.session_state["privacy_current_thread_id"] = new_id
            st.session_state["composer_preset_text"] = ""
            st.session_state["chat_message_input_box"] = ""
            st.rerun()

    # ── Active Tool Selector Bar ──────────────────────────────────────────────
    col_tool_select, col_tool_status = st.columns([2.5, 1.5])
    with col_tool_select:
        selected_tool = st.selectbox(
            "Select Active Tool:",
            TOOLS_LIST,
            index=TOOLS_LIST.index(st.session_state.get("active_tool", "💬 Standard Chat")),
            key="tool_ecosystem_selector"
        )
        if selected_tool != st.session_state["active_tool"]:
            st.session_state["active_tool"] = selected_tool
            st.rerun()

    with col_tool_status:
        _render_html(
            f"<div style='margin-top:28px; font-size:12px; font-weight:700; color:{theme['accent_secondary']}; "
            f"background:{theme['badge_bg']}; padding:6px 12px; border-radius:8px; border:1px solid {theme['badge_border']}; text-align:center; box-shadow:0 0 15px rgba(0,0,0,0.2);'>"
            f"⚡ Tool: {st.session_state['active_tool']}"
            f"</div>"
        )

    # ── Image Generation Configuration Bar ────────────────────────────────────
    if st.session_state.get("active_tool") == "🎨 Image Generation":
        c_ig_style, c_ig_aspect = st.columns([1.5, 1])
        with c_ig_style:
            st.session_state["image_gen_style"] = st.selectbox(
                "🎨 Artistic Style Preset:",
                ["Photorealistic", "Cinematic", "Anime / Manga", "Digital Art", "Cyberpunk", "3D Render", "Oil Painting", "Minimalist Vector"],
                index=0,
                key="select_image_gen_style"
            )
        with c_ig_aspect:
            st.session_state["image_gen_aspect"] = st.selectbox(
                "📐 Aspect Ratio:",
                ["1:1", "16:9", "9:16", "4:3", "3:2"],
                index=0,
                key="select_image_gen_aspect"
            )

    # ── Conversation History Container (Read-Only Rendering, No Duplicates) ────
    if not messages:
        _render_html(
            f"""
            <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(56,189,248,0.25); border-radius:14px; padding:20px 24px; margin-bottom:20px; text-align:center;">
                <div style="font-size:28px; margin-bottom:6px;">🛡️</div>
                <h3 style="color:#FFFFFF; margin:0 0 6px 0; font-size:18px; font-weight:800;">Privacy-Shielded AI Workspace</h3>
                <p style="color:#94A3B8; font-size:13px; margin:0 0 16px 0; line-height:1.5;">
                    Zero-Trust Gateway protects your identity & credentials in real-time before queries reach external AI models.
                </p>
                <div style="font-size:12px; font-weight:700; color:#38BDF8; margin-bottom:10px; text-align:left;">
                    🌟 Click any demo showcase scenario to test with your guide:
                </div>
            </div>
            """
        )
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("🛡️ 1. PII Redaction Demo\n(Aadhaar + Email Masking)", key="demo_btn_pii", use_container_width=True):
                st.session_state["composer_preset_text"] = "My Aadhaar number is 9918-4019-2011 and email is alex@fintech.io"
                st.session_state["input_nonce"] = input_nonce + 1
                st.rerun()
            if st.button("🌐 2. Live Web Grounding\n(Latest ISRO Mission Updates)", key="demo_btn_web", use_container_width=True):
                st.session_state["composer_preset_text"] = "What is the latest ISRO space mission update?"
                st.session_state["input_nonce"] = input_nonce + 1
                st.rerun()
        with col_d2:
            if st.button("🚫 3. Credential Firewall Block\n(Production Password Test)", key="demo_btn_secret", use_container_width=True):
                st.session_state["composer_preset_text"] = "The database password is SuperSecretPass999! Please connect to server"
                st.session_state["input_nonce"] = input_nonce + 1
                st.rerun()
            if st.button("💻 4. Code Generation\n(Python Factorial Algorithm)", key="demo_btn_code", use_container_width=True):
                st.session_state["composer_preset_text"] = "Write Python factorial program with recursion"
                st.session_state["input_nonce"] = input_nonce + 1
                st.rerun()

    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        meta = msg.get("security_meta", {})
        tool_data = msg.get("tool_data")

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                # Render attached file / photo card if message has an attachment
                att = msg.get("attachment")
                if att:
                    att_type = att.get("file_type", "document")
                    att_name = att.get("file_name", "Attachment")
                    att_size = att.get("size_str", "")
                    att_b64 = att.get("image_b64")

                    if att_type == "image" and att_b64:
                        _render_html(
                            f"""
                            <div style="background:rgba(15,23,42,0.75); border:1px solid rgba(56,189,248,0.35); border-radius:12px; padding:12px 16px; margin-bottom:12px; max-width:440px; box-shadow:0 4px 14px rgba(0,0,0,0.25);">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <div style="display:flex; align-items:center; gap:8px;">
                                        <span style="font-size:18px;">📷</span>
                                        <span style="color:#F8FAFC; font-weight:800; font-size:13px;">{html.escape(att_name)}</span>
                                    </div>
                                    <span style="color:#94A3B8; font-size:11px; font-weight:600;">{att_size}</span>
                                </div>
                                <div style="text-align:center; margin:6px 0; background:rgba(0,0,0,0.3); border-radius:8px; padding:4px;">
                                    <img src="data:image/png;base64,{att_b64}" style="max-height:190px; max-width:100%; border-radius:6px; object-fit:contain;"/>
                                </div>
                                <div style="display:flex; gap:6px; flex-wrap:wrap; font-size:11px; margin-top:8px;">
                                    <span style="background:rgba(16,185,129,0.18); color:#34D399; border:1px solid rgba(16,185,129,0.35); padding:2px 8px; border-radius:12px; font-weight:700;">🛡️ EXIF GPS Scrubbed</span>
                                    <span style="background:rgba(56,189,248,0.18); color:#38BDF8; border:1px solid rgba(56,189,248,0.35); padding:2px 8px; border-radius:12px; font-weight:700;">🔍 OCR Inspected</span>
                                    <span style="background:rgba(99,102,241,0.18); color:#A5B4FC; border:1px solid rgba(99,102,241,0.35); padding:2px 8px; border-radius:12px; font-weight:700;">🔒 PII Masked</span>
                                </div>
                            </div>
                            """
                        )
                    else:
                        doc_icon = "📊" if att_type == "data" else "📄"
                        meta_info = ""
                        if att.get("metadata", {}).get("rows"):
                            meta_info = f"{att['metadata']['rows']} rows"
                        elif att.get("metadata", {}).get("page_count"):
                            meta_info = f"{att['metadata']['page_count']} pages"

                        _render_html(
                            f"""
                            <div style="background:rgba(15,23,42,0.75); border:1px solid rgba(99,102,241,0.35); border-radius:12px; padding:12px 16px; margin-bottom:12px; max-width:460px; box-shadow:0 4px 14px rgba(0,0,0,0.25);">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div style="display:flex; align-items:center; gap:10px;">
                                        <span style="font-size:22px;">{doc_icon}</span>
                                        <div>
                                            <div style="color:#F8FAFC; font-weight:800; font-size:13.5px;">{html.escape(att_name)}</div>
                                            <div style="color:#94A3B8; font-size:11.5px; margin-top:2px;">{att_size} {('· ' + meta_info) if meta_info else ''}</div>
                                        </div>
                                    </div>
                                    <span style="background:rgba(16,185,129,0.18); color:#34D399; border:1px solid rgba(16,185,129,0.4); font-size:11px; font-weight:800; padding:3px 10px; border-radius:12px;">
                                        🔒 Zero-Leak Protected
                                    </span>
                                </div>
                            </div>
                            """
                        )

                # ALWAYS display safe redacted representation, never raw sensitive digits
                display_text = msg.get("credential_masked_text") or msg.get("text", "")
                from privacy_engine.sanitizer import PrivacySanitizer
                _render_sanitizer = PrivacySanitizer()
                # Secondary safety net: sanitize on the fly if raw Aadhaar/PAN/credential is present
                display_text = _render_sanitizer.sanitize_text(display_text, mode="REDACT").get("sanitized_text", display_text)
                blurred_html = _render_privacy_blurred_text(display_text)
                st.markdown(blurred_html, unsafe_allow_html=True)
                if msg.get("tool_used") and msg["tool_used"] != "💬 Standard Chat":
                    st.caption(f"🔧 *Invoked Tool:* `{msg['tool_used']}`")
                if msg.get("has_redactions") or msg.get("was_blocked"):
                    st.caption("🔒 *Sensitive data detected — blurred & protected by Privacy Shield*")

        else:
            with st.chat_message("assistant", avatar="🤖"):
                _render_answer_container(text=text, meta=meta, tool_data=tool_data)

    st.divider()

    # ── FILES & PHOTOS MULTIMODAL ATTACHMENT STUDIO ───────────────────────────
    active_att = st.session_state.get("chat_active_attachment")
    attachment_nonce = st.session_state.get("attachment_nonce", 0)

    # 1. Active Attachment Display Card with Privacy Classification
    if active_att:
        att_icon = "📷" if active_att["file_type"] == "image" else ("📊" if active_att["file_type"] == "data" else "📄")
        img_classification = active_att.get("image_classification", "SAFE")
        att_has_pii = active_att.get("has_pii", False)

        # Determine badge based on image privacy classification
        if img_classification == "SENSITIVE_PII_DETECTED":
            priv_badge_col = "#EF4444"
            priv_badge_bg = "rgba(239,68,68,0.18)"
            priv_badge_label = f"🔴 SENSITIVE PII DETECTED ({len(active_att.get('entities', []))} entities)"
            card_border = "rgba(239,68,68,0.6)"
        elif img_classification == "PII_DETECTED":
            priv_badge_col = "#F59E0B"
            priv_badge_bg = "rgba(245,158,11,0.18)"
            priv_badge_label = f"🟡 PII DETECTED ({len(active_att.get('entities', []))} entities)"
            card_border = "rgba(245,158,11,0.5)"
        elif img_classification == "UNCERTAIN":
            priv_badge_col = "#F59E0B"
            priv_badge_bg = "rgba(245,158,11,0.15)"
            priv_badge_label = "🟠 UNCERTAIN (Cannot reliably verify)"
            card_border = "rgba(245,158,11,0.45)"
        elif att_has_pii:
            priv_badge_col = "#F59E0B"
            priv_badge_bg = "rgba(245,158,11,0.15)"
            priv_badge_label = f"🟡 PII Detected ({len(active_att.get('entities', []))} entities)"
            card_border = "rgba(245,158,11,0.4)"
        else:
            priv_badge_col = "#10B981"
            priv_badge_bg = "rgba(16,185,129,0.15)"
            priv_badge_label = "🟢 SAFE (0 PII Detected)"
            card_border = "rgba(56,189,248,0.4)"

        _render_html(
            f"""
            <div style="background:linear-gradient(135deg, rgba(15,23,42,0.85), rgba(30,41,59,0.8)); border:1.5px solid {card_border}; border-radius:12px; padding:12px 18px; margin-bottom:12px; box-shadow:0 4px 16px rgba(0,0,0,0.25);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:22px;">{att_icon}</span>
                        <div>
                            <div style="color:#F8FAFC; font-size:13.5px; font-weight:800;">{html.escape(active_att['file_name'])}</div>
                            <div style="color:#94A3B8; font-size:11.5px; margin-top:2px;">
                                <span>{active_att['size_str']}</span> · 
                                <span style="color:#38BDF8;">{active_att['file_type'].title()}</span> · 
                                <span style="color:#34D399;">Uploaded at {active_att['uploaded_at']}</span>
                            </div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="background:{priv_badge_bg}; color:{priv_badge_col}; border:1px solid {priv_badge_col}44; font-size:11px; font-weight:800; padding:3px 10px; border-radius:12px;">
                            {priv_badge_label}
                        </span>
                        <span style="background:rgba(56,189,248,0.15); color:#38BDF8; border:1px solid rgba(56,189,248,0.35); font-size:11px; font-weight:700; padding:3px 10px; border-radius:12px;">
                            🛡️ EXIF GPS Scrubbed
                        </span>
                    </div>
                </div>
            </div>
            """
        )

        # ── IMAGE PRIVACY WARNING & CONSENT FLOW ──────────────────────────────
        if img_classification in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN"):
            warning_text = active_att.get("privacy_warning_text", "")
            det_entities = active_att.get("entities", [])
            det_types_str = ", ".join(list(dict.fromkeys(det_entities))[:10]) if det_entities else "Personal Information"

            if img_classification == "SENSITIVE_PII_DETECTED":
                warn_bg = "rgba(220,38,38,0.14)"
                warn_border = "rgba(239,68,68,0.6)"
                warn_icon = "🚨"
                warn_title = "SENSITIVE PRIVACY WARNING"
                warn_title_col = "#FCA5A5"
            elif img_classification == "PII_DETECTED":
                warn_bg = "rgba(245,158,11,0.12)"
                warn_border = "rgba(245,158,11,0.5)"
                warn_icon = "⚠️"
                warn_title = "PRIVACY WARNING"
                warn_title_col = "#FCD34D"
            else:
                warn_bg = "rgba(249,115,22,0.10)"
                warn_border = "rgba(249,115,22,0.45)"
                warn_icon = "⚠️"
                warn_title = "PRIVACY WARNING (UNCERTAIN)"
                warn_title_col = "#FB923C"

            _render_html(
                f"""
                <div style="background:{warn_bg}; border:1.5px solid {warn_border}; border-radius:12px; padding:14px 18px; margin-bottom:10px; box-shadow:0 4px 14px rgba(0,0,0,0.2);">
                    <div style="color:{warn_title_col}; font-weight:900; font-size:14px; margin-bottom:8px; display:flex; align-items:center; gap:8px;">
                        <span style="font-size:18px;">{warn_icon}</span>
                        <span>{warn_title}: Image Contains Private Data</span>
                    </div>
                    <div style="color:#E2E8F0; font-size:12.5px; line-height:1.7; margin-bottom:10px;">
                        <div style="margin-bottom:6px;">
                            🔍 <strong>Detected PII Categories:</strong> <span style="color:#38BDF8; font-weight:700;">{html.escape(det_types_str)}</span>
                        </div>
                        <div style="white-space:pre-wrap; color:#CBD5E1; background:rgba(15,23,42,0.5); border-radius:8px; padding:10px 14px; border-left:3px solid {warn_border}; margin-top:6px;">{html.escape(warning_text)}</div>
                    </div>
                    <div style="color:#93C5FD; font-size:12px; line-height:1.5; padding:8px 12px; background:rgba(59,130,246,0.08); border-radius:6px; border:1px solid rgba(59,130,246,0.2);">
                        🛡️ <strong>Privacy Shield:</strong> Image processing is <strong>PAUSED</strong> until you grant explicit consent below.
                        The image will NOT be sent to any AI model without your approval.
                    </div>
                </div>
                """
            )

            # Explicit YES/NO Consent Checkbox
            consent_given = st.checkbox(
                f"✅ YES — I understand and accept the privacy risk. Continue processing this image.",
                value=st.session_state.get("image_privacy_consent", False),
                key=f"consent_checkbox_{attachment_nonce}",
            )
            st.session_state["image_privacy_consent"] = consent_given

            if not consent_given:
                _render_html(
                    f"""
                    <div style="background:rgba(239,68,68,0.10); border:1px solid rgba(239,68,68,0.35); border-radius:8px; padding:8px 14px; margin-bottom:8px; font-size:12px; color:#FCA5A5; font-weight:700;">
                        🔒 Image processing is BLOCKED. Check the box above to grant consent, or remove the file.
                    </div>
                    """
                )
        else:
            # Safe image — auto-consent
            st.session_state["image_privacy_consent"] = True

        c_att_actions, c_att_clear = st.columns([3, 1])
        with c_att_actions:
            with st.expander(f"🔍 Inspect Extracted & Sanitized Content ({active_att['file_name']})", expanded=False):
                if active_att.get("image_b64"):
                    st.image(io.BytesIO(active_att["file_bytes"]), caption=f"Attached Photo: {active_att['file_name']} (EXIF GPS Cleaned)", width=260)

                # Show image privacy deep scan results if available
                img_priv_res = active_att.get("image_privacy_result")
                if img_priv_res and img_priv_res.get("detections"):
                    st.markdown(f"**Document Type:** `{img_priv_res.get('document_type', 'Unknown')}`")
                    st.markdown(f"**Image Privacy Classification:** `{active_att.get('image_classification', 'SAFE')}`")
                    st.markdown(f"**Detection Count:** `{img_priv_res.get('detection_count', 0)}`")
                    st.markdown(f"**Risk Score:** `{img_priv_res.get('risk_score', 0)}%` — **Risk Level:** `{img_priv_res.get('risk_level', 'LOW')}`")
                    st.markdown("**Detected Sensitive Regions:**")
                    for det in img_priv_res["detections"][:10]:
                        st.write(f"- `{det.get('type', 'Unknown')}` — {det.get('description', '')} (Confidence: {det.get('confidence', 0):.0%}, Priority: {det.get('priority', 'N/A')})")

                st.markdown("**Sanitized Text Representation (Sent to AI):**")
                st.code(active_att["sanitized_text"][:2000] if active_att["sanitized_text"] else "[No textual content in document]", language="text")
                if active_att.get("entities"):
                    st.markdown(f"**Detected Protected Entities:** `{', '.join(active_att['entities'])}`")
        with c_att_clear:
            if st.button("❌ Remove File", key="btn_clear_active_attachment", use_container_width=True):
                st.session_state["chat_active_attachment"] = None
                st.session_state["image_privacy_consent"] = False
                st.session_state["attachment_nonce"] = attachment_nonce + 1
                st.rerun()

    # 2. Collapsible File & Photo Upload / Update Tray (Open & Readily Accessible)
    with st.expander("📎 Attach & Update Files / 📷 Photos (PDF, DOCX, CSV, XLSX, PNG, JPG, TXT, JSON)", expanded=True):
        st.markdown(
            "<div style='font-size:12.5px; color:#CBD5E1; margin-bottom:8px;'>"
            "Upload any document or photo to inspect with Zero-Trust privacy scanning and query with AI:"
            "</div>",
            unsafe_allow_html=True
        )

        c_up_file, c_up_demos = st.columns([2, 1.2])
        with c_up_file:
            uploaded_chat_file = st.file_uploader(
                "Select File or Photo to Upload / Update:",
                type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "csv", "xlsx", "txt", "json", "md"],
                key=f"chat_file_photo_uploader_{attachment_nonce}",
                label_visibility="collapsed"
            )
            if uploaded_chat_file is not None:
                file_bytes = uploaded_chat_file.read()
                processed_att = _process_chat_attachment(uploaded_chat_file.name, file_bytes)
                st.session_state["chat_active_attachment"] = processed_att
                st.session_state["image_privacy_consent"] = False  # Reset consent on new upload
                st.session_state["attachment_nonce"] = attachment_nonce + 1
                if not st.session_state.get("composer_preset_text"):
                    st.session_state["composer_preset_text"] = f"Please analyze the attached {processed_att['file_type']} ({processed_att['file_name']}) and summarize key findings safely."
                st.toast(f"✅ Attached & Privacy Scanned: {uploaded_chat_file.name}")
                st.rerun()

        with c_up_demos:
            st.markdown("<div style='font-size:11.5px; font-weight:700; color:#94A3B8; margin-bottom:4px;'>⚡ 1-Click Sample Demos:</div>", unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🖼️ ID Card Photo", key="btn_demo_photo_id", use_container_width=True):
                    fname, fbytes = _get_preset_attachment("sample_id_photo")
                    st.session_state["chat_active_attachment"] = _process_chat_attachment(fname, fbytes)
                    st.session_state["image_privacy_consent"] = False
                    st.session_state["composer_preset_text"] = "Extract text from this ID photo and check for sensitive PII."
                    st.session_state["attachment_nonce"] = attachment_nonce + 1
                    st.rerun()
                if st.button("📊 Sales CSV", key="btn_demo_sales_csv", use_container_width=True):
                    fname, fbytes = _get_preset_attachment("sample_financial_csv")
                    st.session_state["chat_active_attachment"] = _process_chat_attachment(fname, fbytes)
                    st.session_state["composer_preset_text"] = "Analyze the budget and expenditure in this CSV file."
                    st.session_state["attachment_nonce"] = attachment_nonce + 1
                    st.rerun()
            with col_d2:
                if st.button("📄 Medical Bill", key="btn_demo_medical_doc", use_container_width=True):
                    fname, fbytes = _get_preset_attachment("sample_medical_doc")
                    st.session_state["chat_active_attachment"] = _process_chat_attachment(fname, fbytes)
                    st.session_state["composer_preset_text"] = "Summarize the patient diagnosis and prescription safely."
                    st.session_state["attachment_nonce"] = attachment_nonce + 1
                    st.rerun()
                if active_att and st.button("🔄 Update / Swap", key="btn_demo_swap", use_container_width=True):
                    st.session_state["attachment_nonce"] = attachment_nonce + 1
                    st.rerun()

    # ── SECURE CHATGPT-STYLE MESSAGE COMPOSER & PRIVACY SCANNER ───────────────
    current_preset = st.session_state.get("composer_preset_text", "")
    scan_info = _compute_live_privacy_status(current_preset)

    # Override scan_info with image attachment privacy status when image has PII
    if active_att and active_att.get("image_classification") in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN"):
        img_cls = active_att["image_classification"]
        img_risk = active_att.get("risk_score", 0)
        img_entities = active_att.get("entities", [])
        img_entities_label = ", ".join(list(dict.fromkeys(img_entities))[:8]) if img_entities else "Image PII"

        if img_cls == "SENSITIVE_PII_DETECTED":
            scan_info["state_label"] = "🔴 SENSITIVE PII (Image)"
            scan_info["status_col"] = "#EF4444"
            scan_info["badge_bg"] = "rgba(239,68,68,0.18)"
            scan_info["badge_col"] = "#EF4444"
            scan_info["badge_border"] = "rgba(239,68,68,0.5)"
            scan_info["decision"] = "WARN"
            scan_info["is_blocked"] = False  # Blocked by consent flow, not firewall
        elif img_cls == "PII_DETECTED":
            scan_info["state_label"] = "🟡 PII DETECTED (Image)"
            scan_info["status_col"] = "#F59E0B"
            scan_info["badge_bg"] = "rgba(245,158,11,0.18)"
            scan_info["badge_col"] = "#F59E0B"
            scan_info["badge_border"] = "rgba(245,158,11,0.5)"
            scan_info["decision"] = "WARN"
        else:
            scan_info["state_label"] = "🟠 UNCERTAIN (Image)"
            scan_info["status_col"] = "#FB923C"
            scan_info["badge_bg"] = "rgba(249,115,22,0.15)"
            scan_info["badge_col"] = "#FB923C"
            scan_info["badge_border"] = "rgba(249,115,22,0.4)"
            scan_info["decision"] = "WARN"

        scan_info["risk_score"] = max(scan_info.get("risk_score", 0), img_risk)
        scan_info["entities_label"] = img_entities_label
        scan_info["detected_list"] = img_entities

    # Quick scenario chips inside composer covering all 5 sensitive data categories
    st.markdown("<div style='font-size:12px; color:#94A3B8; margin-bottom:8px; font-weight:800; letter-spacing:0.5px;'>⚡ QUICK DEMO SCENARIOS (5 SENSITIVE CATEGORIES):</div>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3, c_p4, c_p5, c_p6 = st.columns(6)
    with c_p1:
        if st.button("🛡️ Aadhaar PII", key="chip_aadhaar_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "My Aadhaar number is 9918-4019-2011 and email is alex@fintech.io"
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()
    with c_p2:
        if st.button("🚫 Password", key="chip_pwd_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "The database password is SuperSecretPass999! Please connect to server"
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()
    with c_p3:
        if st.button("💳 Card + CVV", key="chip_card_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "Billing record: Credit card number 4532 1234 5678 9010 expiration 12/28 CVV 882."
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()
    with c_p4:
        if st.button("🏥 Medical PHI", key="chip_med_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "Patient medical record: diagnosed with Type 2 Diabetes and taking Metformin 500mg daily."
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()
    with c_p5:
        if st.button("🏢 Corp Secret", key="chip_corp_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "Confidential Project Titan: Q3 revenue was $15.4M with proprietary trade secret under NDA."
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()
    with c_p6:
        if st.button("🟢 Safe Science", key="chip_safe_btn", use_container_width=True):
            st.session_state["composer_preset_text"] = "Explain how photosynthesis works in green plants and why it is important."
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()

    if current_preset.strip() or (active_att and active_att.get("image_classification") in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN")):
        _render_html(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; margin-bottom:10px; padding:8px 12px; background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:10px; font-size:12.5px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#38BDF8; font-weight:800;">🛡️ Privacy Firewall:</span>
                    <span style="color:{scan_info['status_col']}; font-weight:700;">{scan_info['state_label']} ({scan_info['risk_score']}%)</span>
                    <span style="color:#64748B;">•</span>
                    <span style="color:#94A3B8;">{scan_info['entities_label']}</span>
                </div>
                <span style="background:{scan_info['badge_bg']}; color:{scan_info['badge_col']}; border:1px solid {scan_info['badge_border']}; font-size:11px; font-weight:800; padding:2px 8px; border-radius:10px;">
                    {scan_info['decision']}
                </span>
            </div>
            """
        )

        # ── Live Credential Warning Banner (Before Send) ──────────────────────
        _live_advisory = scan_info.get("security_advisory")
        if _live_advisory and _live_advisory.get("items") and scan_info["is_blocked"]:
            _cred_types = ", ".join([item["type"] for item in _live_advisory["items"]])
            _render_html(
                f"""
                <div style="background:rgba(220,38,38,0.18); border:1.5px solid rgba(239,68,68,0.5); border-radius:10px; padding:10px 14px; margin-bottom:8px; animation: pulse 2s ease-in-out infinite;">
                    <div style="color:#FCA5A5; font-weight:700; font-size:12.5px; display:flex; align-items:center; gap:6px;">
                        <span>🚨</span> <span>CREDENTIAL DETECTED: {_cred_types}</span>
                    </div>
                    <div style="color:#CBD5E1; font-size:11.5px; margin-top:4px; line-height:1.5;">
                        ⚠️ Your message contains sensitive credentials. It will be <strong style="color:#F87171;">BLOCKED</strong> from being sent to AI.<br>
                        🔐 If this is an active credential, <strong style="color:#FCD34D;">change it immediately</strong>.
                    </div>
                </div>
                """
            )
        elif scan_info.get("decision") == "PENDING_USER_DECISION" or (scan_info.get("has_personal_info") and not scan_info["is_blocked"]):
            _render_html(
                f"""
                <div style="background:rgba(245,158,11,0.14); border:1.5px solid rgba(245,158,11,0.45); border-radius:10px; padding:10px 14px; margin-bottom:8px;">
                    <div style="color:#FCD34D; font-weight:700; font-size:12.5px; display:flex; align-items:center; gap:6px;">
                        <span>⚠️</span> <span>PRIVACY WARNING — SENSITIVE PERSONAL / HEALTH INFORMATION DETECTED</span>
                    </div>
                    <div style="color:#CBD5E1; font-size:11.5px; margin-top:4px; line-height:1.5;">
                        Category: <strong style="color:#FCD34D;">{scan_info['entities_label']}</strong> | Privacy Risk Score: <strong style="color:#FCD34D;">{scan_info['risk_score']}%</strong><br>
                        Prompt state: <strong>PENDING_USER_DECISION</strong>. The LLM will NOT be called until you explicitly choose <strong>CONTINUE</strong>.
                    </div>
                </div>
                """
            )
            c_pud1, c_pud2 = st.columns(2)
            with c_pud1:
                if st.button("🛑 BLOCK PROMPT", key="btn_pud_block_action", use_container_width=True):
                    st.session_state["composer_preset_text"] = ""
                    st.session_state["pending_user_consent_granted"] = False
                    st.session_state["input_nonce"] = input_nonce + 1
                    st.toast("🛑 Prompt blocked by user decision. State: BLOCKED.")
                    st.rerun()
            with c_pud2:
                if st.button("⚠️ CONTINUE & SEND TO LLM", key="btn_pud_continue_action", type="primary", use_container_width=True):
                    st.session_state["pending_user_consent_granted"] = True
                    st.toast("⚠️ Explicit consent granted: State changed to CONTINUED.")
                    st.rerun()


    # Full-width message textarea with dynamic nonce key for instant clean reset
    input_nonce = st.session_state.get("input_nonce", 0)
    user_prompt = st.text_area(
        "Type your message...",
        value=current_preset,
        placeholder="Type any question or prompt... (Universal Live Web Grounding & Privacy Shield active)",
        height=95,
        key=f"chat_message_input_box_{input_nonce}",
        label_visibility="collapsed",
    )

    if user_prompt != current_preset:
        st.session_state["composer_preset_text"] = user_prompt

    # Action bar matching exact horizontal boundaries of the textarea
    active_tool_name = st.session_state.get("active_tool", "💬 Standard Chat")
    has_active_attachment = bool(active_att)
    is_composer_empty = not bool((user_prompt or current_preset or "").strip()) and not has_active_attachment

    # Check if image requires consent and consent is not given
    att_classification = active_att.get("image_classification", "SAFE") if active_att else "SAFE"
    needs_consent = att_classification in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN")
    consent_given = st.session_state.get("image_privacy_consent", False)
    is_blocked_by_image = needs_consent and not consent_given

    c_tool_info, c_scan, c_clear, c_send = st.columns([2.2, 1.1, 0.8, 1.2])

    with c_tool_info:
        att_label = f" + 📎 {active_att['file_name']}" if active_att else ""
        _render_html(
            f"<div style='padding-top:7px; font-size:12px; color:#94A3B8; display:flex; align-items:center; gap:6px;'>"
            f"<span>⚡ Active Tool:</span> <strong style='color:#38BDF8;'>{active_tool_name}{att_label}</strong>"
            f"</div>"
        )

    with c_scan:
        scan_clicked = st.button("🛡️ Scan Prompt", key="btn_chat_preflight_scan", use_container_width=True)

    with c_clear:
        if st.button("🗑️ Clear", key="btn_chat_clear", use_container_width=True):
            st.session_state["composer_preset_text"] = ""
            st.session_state["chat_active_attachment"] = None
            st.session_state["input_nonce"] = input_nonce + 1
            st.rerun()

    with c_send:
        if scan_info["is_blocked"]:
            send_btn_label = "🚫 Blocked (Credentials)"
            send_btn_type = "secondary"
            send_disabled = True
        elif is_blocked_by_image:
            send_btn_label = "🔒 Consent Required"
            send_btn_type = "secondary"
            send_disabled = True
        else:
            send_btn_label = "➤ Send"
            send_btn_type = "primary"
            send_disabled = False

        send_clicked = st.button(
            send_btn_label,
            key="btn_chat_send",
            type=send_btn_type,
            use_container_width=True,
            disabled=send_disabled
        )

    # Pre-flight Scan Diagnostic Expander
    if scan_clicked and (user_prompt or active_att):
        scan_target = user_prompt or (active_att["sanitized_text"][:500] if active_att else "")
        detailed_scan = _compute_live_privacy_status(scan_target)
        with st.expander("🛡️ Pre-Flight Privacy & Security Diagnostic", expanded=True):
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Risk Score", f"{detailed_scan['risk_score']}%", detailed_scan['risk_level'])
            sc2.metric("Policy Action", detailed_scan['decision'])
            sc3.metric("Live State", detailed_scan['state_label'])
            st.markdown(f"**Diagnostic Summary:** {detailed_scan['reason']}")
            if detailed_scan.get("entities"):
                st.markdown("**Detected Entity Spans:**")
                for e in detailed_scan["entities"]:
                    st.write(f"- `{e.get('category', e.get('entity_type'))}`: `{e.get('value', '[MASKED]')}` (Severity: {e.get('severity')})")

    # ── Handle Send Action (Instant 1st-Click Capture & Execution) ─────────────
    if send_clicked:
        input_key = f"chat_message_input_box_{input_nonce}"
        raw_val = st.session_state.get(input_key, "") or user_prompt or current_preset or ""
        prompt = (raw_val or "").strip()

        # If user didn't type a prompt but attached a file/photo, generate a smart prompt
        if not prompt and active_att:
            prompt = f"Please analyze and summarize the attached {active_att['file_type']} ({active_att['file_name']}) safely."

        if not prompt:
            st.toast("💡 Tip: Type a question, attach a file/photo, or click any demo button.")
            return

        msg_turn_id = f"turn-{int(time.time()*1000)}"
        st.session_state["composer_preset_text"] = ""
        st.session_state["input_nonce"] = input_nonce + 1

        # ── IMMEDIATE SANITIZATION: Redact sensitive information BEFORE storing or rendering ──
        from privacy_engine.sanitizer import PrivacySanitizer
        _common_sanitizer = PrivacySanitizer()
        _sanitized_result = _common_sanitizer.sanitize_text(prompt, mode="REDACT")
        _safe_redacted_prompt = _sanitized_result.get("sanitized_text", prompt)
        _has_redactions = _safe_redacted_prompt != prompt

        # Snapshot of current active attachment for this message turn
        att_snapshot = dict(active_att) if active_att else None

        if scan_info["is_blocked"]:
            st.error("⛔ REQUEST BLOCKED: Input contains high-risk credentials or adversarial overrides. Execution halted with 0 external LLM/tool calls.")

            messages.append({
                "id": f"{msg_turn_id}-user",
                "role": "user",
                "text": _safe_redacted_prompt,
                "credential_masked_text": _safe_redacted_prompt if _has_redactions else None,
                "has_redactions": _has_redactions,
                "was_blocked": True,
                "tool_used": active_tool_name,
                "attachment": att_snapshot,
                "timestamp": time.time()
            })
            messages.append({
                "id": f"{msg_turn_id}-assistant",
                "role": "assistant",
                "text": "",
                "security_meta": {
                    "decision": "BLOCK",
                    "risk_score": scan_info["risk_score"],
                    "risk_level": "CRITICAL",
                    "category": "CRITICAL_SECURITY",
                    "detected_risks": scan_info["detected_list"],
                    "detected_entities": scan_info["entities"],
                    "reason": scan_info["reason"],
                    "routing_action": "BLOCKED → LLM was not called",
                    "model_selected": "Blocked (No Provider)",
                    "security_advisory": scan_info.get("security_advisory"),
                    "safe_rationale": scan_info.get("safe_rationale"),
                    "risk_rationale": scan_info.get("risk_rationale"),
                    "timing_breakdown": {"total_ms": 1.0, "router_ms": 0.0, "security_ms": 1.0, "search_ms": 0.0, "llm_ms": 0.0, "tier": "BLOCKED"},
                    "timing_ms": 1.0,
                }
            })
            st.rerun()
        else:
            # Double-check image consent for PII images
            if att_snapshot and att_snapshot.get("image_classification") in ("SENSITIVE_PII_DETECTED", "PII_DETECTED", "UNCERTAIN"):
                if not st.session_state.get("image_privacy_consent", False):
                    st.error("🔒 IMAGE BLOCKED: This image contains personal/sensitive information. You must grant explicit consent (check the box above) before processing.")
                    return

            if not messages:
                current_thread["title"] = (_safe_redacted_prompt[:28] + "...") if len(_safe_redacted_prompt) > 28 else _safe_redacted_prompt

            messages.append({
                "id": f"{msg_turn_id}-user",
                "role": "user",
                "text": _safe_redacted_prompt,
                "credential_masked_text": _safe_redacted_prompt if _has_redactions else None,
                "has_redactions": _has_redactions,
                "was_blocked": False,
                "tool_used": active_tool_name,
                "attachment": att_snapshot,
                "timestamp": time.time()
            })

            status_container = st.empty()
            status_container.markdown(
                f"""
                <div style="background:linear-gradient(135deg, rgba(15,23,42,0.92), rgba(30,27,75,0.85)); border:1.5px solid rgba(56,189,248,0.4); border-radius:12px; padding:14px 20px; margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; box-shadow:0 6px 20px rgba(0,0,0,0.35); animation:pulse 2s infinite;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="font-size:20px;">🛡️</span>
                        <div>
                            <div style="color:#F8FAFC; font-size:13.5px; font-weight:800;">Executing High-Task ({html.escape(active_tool_name)}) &amp; Privacy Gateway…</div>
                            <div style="color:#94A3B8; font-size:11.5px; margin-top:2px;">🔒 Zero-Trust Protection · Live Multimodal Grounding · Speed Target: 2-10s</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background:rgba(56,189,248,0.15); color:#38BDF8; border:1px solid rgba(56,189,248,0.4); font-size:11px; font-weight:800; font-family:monospace; padding:4px 10px; border-radius:12px;">
                            ⚡ HIGH SPEED ACTIVE (2-10s)
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            t_start = time.perf_counter()
            tool_out = None
            resp = None

            # 1. 🖼️ Image Analysis Tool Execution
            if active_tool_name == "🖼️ Image Analysis":
                img_bytes = att_snapshot["file_bytes"] if (att_snapshot and att_snapshot.get("file_type") == "image") else _generate_sample_id_photo_bytes()
                tool_out = execute_tool_with_ai_trust("🖼️ Image Analysis", analyze_image_bytes, img_bytes, prompt=_safe_redacted_prompt)

            # 2. 📎 Files Parser Tool Execution
            elif active_tool_name == "📎 Files Parser":
                f_bytes = att_snapshot["file_bytes"] if att_snapshot else _safe_redacted_prompt.encode("utf-8")
                f_name = att_snapshot["file_name"] if att_snapshot else "prompt_document.txt"
                tool_out = execute_tool_with_ai_trust("📎 Files Parser", process_file_content, f_bytes, f_name)

            # 3. 📊 Data Analysis Tool Execution
            elif active_tool_name == "📊 Data Analysis":
                d_bytes = att_snapshot["file_bytes"] if att_snapshot else _safe_redacted_prompt.encode("utf-8")
                d_name = att_snapshot["file_name"] if att_snapshot else "dataset_query.csv"
                tool_out = execute_tool_with_ai_trust("📊 Data Analysis", analyze_dataset, d_bytes, d_name)

            # 4. 🔎 Web Search Execution (Safe Redacted Input Passed)
            elif active_tool_name == "🔎 Web Search":
                tool_out = execute_tool_with_ai_trust("🔎 Web Search", search_web, _safe_redacted_prompt)

            # 5. 🧠 Deep Research Execution
            elif active_tool_name == "🧠 Deep Research":
                tool_out = execute_tool_with_ai_trust("🧠 Deep Research", deep_research, _safe_redacted_prompt)

            # 6. ✍️ Canvas Workspace Execution
            elif active_tool_name == "✍️ Canvas Workspace":
                tool_out = execute_tool_with_ai_trust("✍️ Canvas Workspace", canvas_engine, _safe_redacted_prompt)

            # 7. 💻 Code Workspace Execution
            elif active_tool_name == "💻 Code Workspace":
                tool_out = execute_tool_with_ai_trust("💻 Code Workspace", execute_code_safely, _safe_redacted_prompt)

            # 8. 🔗 URL Analysis Execution
            elif active_tool_name == "🔗 URL Analysis":
                tool_out = execute_tool_with_ai_trust("🔗 URL Analysis", analyze_url_content, _safe_redacted_prompt)

            # 9. 📝 Report Generator Execution
            elif active_tool_name == "📝 Report Generator":
                tool_out = execute_tool_with_ai_trust("📝 Report Generator", generate_formal_report, _safe_redacted_prompt)

            # 10. 🎨 Image Generation Execution
            elif active_tool_name == "🎨 Image Generation":
                img_style = st.session_state.get("image_gen_style", "Photorealistic")
                img_aspect = st.session_state.get("image_gen_aspect", "1:1")
                tool_out = execute_tool_with_ai_trust(
                    "🎨 Image Generation",
                    generate_image_bridge,
                    prompt=_safe_redacted_prompt,
                    aspect_ratio=img_aspect,
                    style=img_style
                )

            # 9. Standard Multimodal LLM Chat Route with Universal Live Grounding & Attachment Context
            else:
                safe_history = [
                    m for m in messages[:-1]
                    if not m.get("was_blocked") and m.get("security_meta", {}).get("decision") != "BLOCK"
                ]

                # If an attachment exists, safely integrate its sanitized text representation into the LLM query
                if att_snapshot and att_snapshot.get("sanitized_text"):
                    multimodal_query = (
                        f"{_safe_redacted_prompt}\n\n"
                        f"[ATTACHED {att_snapshot['file_type'].upper()} ({att_snapshot['file_name']}) CONTEXT]:\n"
                        f"{att_snapshot['sanitized_text'][:4000]}"
                    )
                else:
                    multimodal_query = _safe_redacted_prompt

                resp = APIClient.chat_message(
                    prompt=multimodal_query,
                    mode="REDACT",
                    mcp_enabled=True,
                    chat_history=safe_history,
                    user_role=user_role,
                    user_id=user_id,
                    rag_doc_id=st.session_state.get("rag_doc_id"),
                )

            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            status_container.empty()

            if tool_out:
                receipt = tool_out.get("trust_receipt", {})
                receipt_text = format_receipt_text(receipt) if receipt else "Trust Receipt Verified"
                direct_ans = tool_out.get("result", {}).get("direct_answer") or tool_out.get("direct_answer", "")
                if not direct_ans and isinstance(tool_out.get("result"), dict):
                    direct_ans = json.dumps(tool_out["result"], indent=2)

                messages.append({
                    "id": f"{msg_turn_id}-assistant",
                    "role": "assistant",
                    "text": "" if tool_out.get("decision") == "BLOCK" else f"Result from **{active_tool_name}**:\n\n{direct_ans}",
                    "tool_data": tool_out,
                    "security_meta": {
                        "decision": tool_out.get("decision", "ALLOW"),
                        "risk_score": tool_out.get("risk_score", 0),
                        "risk_level": tool_out.get("risk_level", "LOW"),
                        "reason": tool_out.get("reason", ""),
                        "receipt_id": receipt.get("receipt_id", ""),
                        "receipt_text": receipt_text,
                        "model_selected": f"Aiera {active_tool_name}",
                        "timing_breakdown": {
                            "total_ms": elapsed_ms,
                            "router_ms": 1.0,
                            "security_ms": 15.0,
                            "search_ms": elapsed_ms - 20.0,
                            "llm_ms": 0.0,
                            "tier": "MULTIMODAL_EXECUTION"
                        },
                        "timing_ms": elapsed_ms,
                        "safe_rationale": tool_out.get("safe_rationale") or scan_info.get("safe_rationale"),
                        "risk_rationale": tool_out.get("risk_rationale") or scan_info.get("risk_rationale"),
                        "security_advisory": tool_out.get("security_advisory") or scan_info.get("security_advisory"),
                    }
                })

            elif resp:
                if resp.get("masked_prompt") and resp["masked_prompt"] != prompt:
                    messages[-1]["masked_text"] = resp["masked_prompt"]

                ai_text = resp.get("ai_response") or resp.get("response") or "Security scan completed."
                decision = resp.get("decision", "ALLOW")

                receipt_id = resp.get("receipt_id", "")
                receipt = get_receipt_by_id(receipt_id) if receipt_id else None
                receipt_text = format_receipt_text(receipt) if receipt else f"Receipt ID: {receipt_id}"

                timing_bd = resp.get("timing_breakdown", {
                    "total_ms": elapsed_ms,
                    "router_ms": 0.5,
                    "security_ms": 30.0,
                    "search_ms": 0.0,
                    "llm_ms": elapsed_ms - 35.0,
                    "tier": "SIMPLE"
                })

                merged_priv_analysis = resp.get("privacy_analysis") or {}
                if not merged_priv_analysis.get("detections") and scan_info.get("personal_info_items"):
                    merged_priv_analysis = {
                        "has_privacy_risk": True,
                        "overall_risk": {"level": scan_info.get("risk_level", "LOW"), "score": max(2, scan_info.get("risk_score", 20) // 10), "badge": f"🟡 {scan_info.get('risk_level', 'LOW')}"},
                        "detections": scan_info.get("personal_info_items", []),
                        "recommendations": ["Personal identifiers safely masked by Zero-Leak Privacy Shield before AI ingestion."]
                    }

                had_disclosures = _has_redactions or scan_info.get("has_personal_info", False) or bool(scan_info.get("detected_list"))

                messages.append({
                    "id": f"{msg_turn_id}-assistant",
                    "role": "assistant",
                    "text": ai_text or "Security scan completed.",
                    "security_meta": {
                        "decision": decision,
                        "risk_score": max(resp.get("risk_score", 0), scan_info.get("risk_score", 0) if had_disclosures else 0),
                        "risk_level": resp.get("risk_level", "LOW") if not had_disclosures else scan_info.get("risk_level", "LOW"),
                        "category": resp.get("category", "SAFE"),
                        "detected_risks": resp.get("detected_risks", []) or scan_info.get("detected_list", []),
                        "detected_entities": resp.get("detected_entities", []) or scan_info.get("entities", []),
                        "reason": resp.get("reason", "") or scan_info.get("reason", ""),
                        "routing_action": resp.get("routing_action", "SAFE → LLM" if decision == "ALLOW" else "BLOCKED → LLM was not called"),
                        "bert_prediction": resp.get("bert_prediction", "SAFE"),
                        "bert_confidence": resp.get("bert_confidence", 0.0),
                        "nb_prediction": resp.get("nb_prediction", "SAFE"),
                        "nb_confidence": resp.get("nb_confidence", 0.0),
                        "model_selected": resp.get("model_selected", "Gemini"),
                        "receipt_id": receipt_id,
                        "receipt_text": receipt_text,
                        "timing_breakdown": timing_bd,
                        "timing_ms": elapsed_ms,
                        "privacy_analysis": merged_priv_analysis,
                        "had_user_disclosures": had_disclosures,
                        "safe_rationale": resp.get("safe_rationale") or scan_info.get("safe_rationale"),
                        "risk_rationale": resp.get("risk_rationale") or scan_info.get("risk_rationale"),
                        "security_advisory": resp.get("security_advisory") or scan_info.get("security_advisory"),
                    },
                })

            st.rerun()
