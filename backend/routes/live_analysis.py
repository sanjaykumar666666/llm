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


from backend.services.evidence_risk import run_full_analysis

@router.post("/privacy/analyze")
@router.post("/analyze/live")
def live_typing_analysis_endpoint(req: LiveAnalysisRequest):
    """
    Real-Time Live Typing Privacy Analysis Engine.
    Authoritative backend privacy evaluation combining context-aware entity detection,
    DistilBERT semantics, Naive Bayes token probabilities, and continuous risk scoring.
    """
    raw_text = req.text.strip() if req.text else ""
    if not raw_text:
        return {
            "text": "",
            "risk_score": 0,
            "risk_level": "SAFE",
            "category": "SAFE",
            "detected_categories": ["SAFE"],
            "detected_entities": [],
            "sanitized_text": "",
            "decision": "ALLOW",
            "action": "ALLOW",
            "confidence": 0.98,
            "can_send_to_llm": True,
            "warning_message": None,
            "explanation": "No sensitive information detected in prompt.",
            "has_personal_context": False,
            "personal_context_level": "SAFE",
            "requires_user_confirmation": False,
            "classification_source": "rule_based_precheck",
            "trust_indicators": {
                "privacy_guard_active": True,
                "ai_has_received": False,
                "can_review_and_edit": True,
                "user_decides": True,
                "status_text": "🛡️ Privacy Guard Active",
            },
            "shap": SHAPExplainer.explain_prompt("", 0.0),
            "sbert": sbert_matcher.match_semantic_policy(""),
            "is_demo_mode": False
        }

    evidence = run_full_analysis(raw_text, mode=req.sanitization_mode or "REDACT")
    
    risk_score = evidence.get("risk_score", 0)
    risk_level = evidence.get("risk_level", "SAFE")
    decision = evidence.get("decision", "ALLOW")
    action = "BLOCK" if decision == "BLOCK" else ("SANITIZE" if decision == "WARN" else "ALLOW")
    can_send = decision != "BLOCK"
    
    detected_categories = evidence.get("detected_risks") or ["SAFE"]
    primary_category = detected_categories[0] if detected_categories else "SAFE"
    detected_entities = evidence.get("entities", [])
    sanitized_text = evidence.get("sanitized_text") or raw_text

    has_pers_ctx = evidence.get("has_personal_context", False)
    pers_level = evidence.get("personal_context_level", "SAFE")
    requires_confirmation = evidence.get("requires_user_confirmation", False)

    warning_msg = None
    trust_status = "🛡️ Privacy Guard Active"

    if decision == "BLOCK":
        warning_msg = "⚠ High Privacy Risk Detected. Prompt blocked due to sensitive credentials/secrets."
        trust_status = "🔴 Highly Sensitive Credentials Detected"
    elif pers_level == "HIGH_RISK":
        warning_msg = "This message may contain highly personal information. Consider removing details that you do not want to share with an AI system."
        trust_status = "🔴 Highly personal information detected"
    elif pers_level == "WARNING":
        warning_msg = "Personal information may be present."
        trust_status = "🟡 Personal information may be present"
    elif decision == "WARN":
        warning_msg = "⚠ Privacy Risk Detected. Sanitization recommended before sending."
        trust_status = "🟡 Privacy Risk Detected"
    elif risk_score >= 15:
        warning_msg = "ℹ Minor privacy signal detected. Safe to send."
        trust_status = "🛡️ Privacy Guard Active"

    shap_data = SHAPExplainer.explain_prompt(raw_text, float(risk_score))
    sbert_data = sbert_matcher.match_semantic_policy(raw_text)

    ml_analysis = evidence.get("ml_analysis") or {}
    confidence = ml_analysis.get("confidence") or (0.98 if risk_score == 0 else 0.90)
    explanation_text = evidence.get("reason") or (
        f"{', '.join(detected_categories)} detected in current input requiring privacy protection."
        if detected_entities else "No sensitive PII or credentials detected."
    )

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
        "has_personal_context": has_pers_ctx,
        "personal_context_level": pers_level,
        "requires_user_confirmation": requires_confirmation,
        "classification_source": evidence.get("classification_source", "rule_based_precheck"),
        "calculation_source": evidence.get("calculation_source", "evidence_based_risk_engine"),
        "risk_factors": evidence.get("risk_factors", []),
        "evidence": evidence.get("evidence", []),
        "bert_prediction": evidence.get("bert_prediction", "SAFE"),
        "bert_confidence": evidence.get("bert_confidence", 0.0),
        "nb_prediction": evidence.get("nb_prediction", "SAFE"),
        "nb_confidence": evidence.get("nb_confidence", 0.0),
        "ml_analysis": ml_analysis,
        "trust_indicators": {
            "privacy_guard_active": True,
            "ai_has_received": False,
            "can_review_and_edit": True,
            "user_decides": True,
            "status_text": trust_status,
        },
        "shap": shap_data,
        "sbert": sbert_data,
        "is_demo_mode": False
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
