"""
Real-Time Keystroke Privacy Analysis Route.
File Location: backend/routes/live_analysis.py
"""

import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.services.sbert_matcher import SBERTSemanticMatcher
from backend.services.shap_explainer import SHAPExplainer
from privacy_engine.sanitizer import PrivacySanitizer

router = APIRouter()
sbert_matcher = SBERTSemanticMatcher()
sanitizer = PrivacySanitizer()


class LiveAnalysisRequest(BaseModel):
    text: str
    sanitization_mode: Optional[str] = "REDACT"
    modality: Optional[str] = "Text"


# Regex patterns for real-time live typing scanner
SENSITIVE_PATTERNS = [
    # Category, Entity Type, Regex Pattern, Placeholder, Risk Points
    ("Financial Data", "Bank Account Number", r'\b(?:account\s*(?:num|no|number)?\s*is?\s*:?\s*)?(\d{9,18})\b', "[FINANCIAL_ACCOUNT_REDACTED]", 45),
    ("Financial Data", "Credit/Debit Card", r'\b(?:\d[ -]*?){13,16}\b', "[CREDIT_CARD_REDACTED]", 50),
    ("Financial Data", "IBAN / SWIFT Code", r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b', "[IBAN_REDACTED]", 45),
    ("PII", "Aadhaar Card Number", r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[AADHAAR_REDACTED]", 55),
    ("PII", "Social Security Number (SSN)", r'\b\d{3}-\d{2}-\d{4}\b', "[SSN_REDACTED]", 55),
    ("PII", "Email Address", r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', "[EMAIL_REDACTED]", 25),
    ("PII", "Phone Number", r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "[PHONE_REDACTED]", 25),
    ("PII", "Passport Number", r'\b[A-Z]{1,2}[0-9]{6,9}\b', "[PASSPORT_REDACTED]", 35),
    ("Credentials", "Password / Key", r'\b(?:password|passwd|pass|secret_key|api_key|token)\s*[:=]\s*(\S+)\b', "[CREDENTIAL_REDACTED]", 60),
    ("Credentials", "AWS Access Key", r'\bAKIA[0-9A-Z]{16}\b', "[AWS_KEY_REDACTED]", 65),
    ("Credentials", "Generic Secret Token", r'\bsk_live_[0-9a-zA-Z]{24}\b|\bsk-[a-zA-Z0-9]{32,48}\b', "[API_KEY_REDACTED]", 65),
    ("Healthcare", "Medical Record / MRN", r'\b(?:MRN|patient_id|diagnosis|prescription)\s*[:#-]?\s*([A-Za-z0-9-]+)\b', "[MEDICAL_REC_REDACTED]", 35),
    ("Confidential", "Database Connection String", r'\b(?:postgres|mysql|mongodb|redis):\/\/\S+\b', "[DB_CONN_REDACTED]", 60),
]


@router.post("/privacy/analyze")
@router.post("/analyze/live")
def live_typing_analysis_endpoint(req: LiveAnalysisRequest):
    """
    Real-Time Live Typing Privacy Analysis Engine.
    Executes live pattern matching, risk scoring, sanitization preview, SBERT cosine similarity,
    and SHAP token attribution as the user types.
    """
    raw_text = req.text.strip() if req.text else ""
    if not raw_text:
        return {
            "text": "",
            "risk_score": 0,
            "risk_level": "SAFE",
            "category": "SAFE",
            "detected_categories": [],
            "detected_entities": [],
            "sanitized_text": "",
            "decision": "ALLOW",
            "action": "ALLOW",
            "confidence": 0.98,
            "can_send_to_llm": True,
            "warning_message": None,
            "explanation": "No sensitive information detected in prompt.",
            "shap": SHAPExplainer.explain_prompt("", 0),
            "sbert": sbert_matcher.match_semantic_policy(""),
            "is_demo_mode": True,
            "demo_note": "Demo/Mock ML prediction pipeline running in real-time mode for academic evaluation."
        }

    lower_text = raw_text.lower()
    detected_entities = []
    detected_cats_set = set()
    total_risk_points = 0
    sanitized_text = raw_text

    # 1. Pattern & Entity Detection
    for category, entity_type, pattern, placeholder, risk_pts in SENSITIVE_PATTERNS:
        matches = list(re.finditer(pattern, raw_text, re.IGNORECASE))
        for m in matches:
            val = m.group(0)
            span = [m.start(), m.end()]
            detected_cats_set.add(category)
            total_risk_points += risk_pts

            preview = val[:2] + "***" + val[-2:] if len(val) > 4 else "***"
            detected_entities.append({
                "category": category,
                "entity_type": entity_type,
                "value_preview": preview,
                "raw_value": val,
                "span": span,
                "location": f"Span({span[0]}, {span[1]})"
            })
            sanitized_text = sanitized_text.replace(val, placeholder, 1)

    # Keyword backup triggers for high-risk context
    if "bank account" in lower_text or "account number" in lower_text or re.search(r'\b\d{9,18}\b', raw_text):
        detected_cats_set.add("Financial Information")
        total_risk_points += 45
    if "password" in lower_text or "secret key" in lower_text or "api_key" in lower_text:
        detected_cats_set.add("Credentials")
        total_risk_points += 50

    # 2. Risk Score Normalization (0 to 100)
    risk_score = min(100, max(0, total_risk_points))

    # 3. Categorization & Risk Level
    if risk_score >= 65:
        risk_level = "HIGH"
        decision = "BLOCK"
        can_send = False
        warning_msg = "⚠ High Privacy Risk Detected. Prompt blocked due to sensitive information."
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        decision = "WARN"
        can_send = True
        warning_msg = "⚠ Privacy Risk Detected. Sanitization recommended before sending."
    elif risk_score >= 15:
        risk_level = "LOW"
        decision = "ALLOW"
        can_send = True
        warning_msg = "ℹ Minor privacy signal detected. Safe to send."
    else:
        risk_level = "SAFE"
        decision = "ALLOW"
        can_send = True
        warning_msg = None

    detected_categories = list(detected_cats_set) if detected_cats_set else ["SAFE"]
    primary_category = detected_categories[0] if detected_categories else "SAFE"

    # 4. SHAP & SBERT Computations
    shap_data = SHAPExplainer.explain_prompt(raw_text, float(risk_score))
    sbert_data = sbert_matcher.match_semantic_policy(raw_text)

    action = "BLOCK" if decision == "BLOCK" else ("SANITIZE" if decision == "WARN" else "ALLOW")
    confidence = round(0.85 + (risk_score / 1000.0), 2) if risk_score > 0 else 0.98
    explanation_text = f"{', '.join(detected_categories)} detected in current input requiring privacy protection." if detected_entities else "No sensitive PII or credentials detected."

    return {
        "text": raw_text,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "category": primary_category,
        "detected_categories": detected_categories,
        "detected_entities": detected_entities,
        "sanitized_text": sanitized_text,
        "decision": decision,
        "action": action,
        "confidence": confidence,
        "can_send_to_llm": can_send,
        "warning_message": warning_msg,
        "explanation": explanation_text,
        "shap": shap_data,
        "sbert": sbert_data,
        "is_demo_mode": True,
        "demo_note": "Demo/Mock ML prediction pipeline running in real-time mode for academic evaluation."
    }


@router.post("/privacy/sanitize")
def sanitize_endpoint(req: LiveAnalysisRequest):
    """Sanitizes sensitive entities in prompt input."""
    res = live_typing_analysis_endpoint(req)
    return {
        "original_text": req.text,
        "sanitized_text": res["sanitized_text"],
        "detected_categories": res["detected_categories"],
        "action": "SANITIZED",
        "is_demo_mode": True
    }


@router.post("/privacy/analyze-image")
def analyze_image_endpoint():
    """OCR text extraction & privacy analysis endpoint for images."""
    return {
        "modality": "Image",
        "ocr_text": "DEPARTMENT OF MOTOR VEHICLES\nDRIVER LICENSE ID: D9910482\nDOB: 1992-05-14\nADDRESS: 742 Evergreen Terrace",
        "detected_entities": [
            {"category": "PII", "entity_type": "Driver License ID", "value_preview": "D9910***"},
            {"category": "PII", "entity_type": "Home Address", "value_preview": "742 Evergreen Terrace"}
        ],
        "risk_score": 85,
        "risk_level": "HIGH",
        "action": "BLOCK",
        "confidence": 0.94,
        "explanation": "Identity document OCR scan identified sensitive personal records.",
        "is_demo_mode": True
    }


@router.post("/privacy/analyze-video")
def analyze_video_endpoint():
    """Keyframe sampling & OCR privacy analysis endpoint for videos."""
    return {
        "modality": "Video",
        "total_frames_sampled": 12,
        "ocr_text": "Frame 00:11.20 OCR text: DB Connection: postgres://user:pass123@db.internal:5432\nHost: 10.0.4.12",
        "detected_frames": [
            {"timestamp": "00:02.50", "detected_text": "Welcome Presentation Slide 1", "risk": "LOW"},
            {"timestamp": "00:06.00", "detected_text": "Confidential Internal Architecture Diagram", "risk": "MEDIUM"},
            {"timestamp": "00:11.20", "detected_text": "DB Connection: postgres://user:pass123@db.internal:5432", "risk": "HIGH"}
        ],
        "risk_score": 78,
        "risk_level": "HIGH",
        "action": "BLOCK",
        "confidence": 0.91,
        "explanation": "Video keyframe OCR scan identified exposed server database credentials.",
        "is_demo_mode": True
    }
