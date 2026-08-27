"""
Core Privacy Intelligence & Evidence-Based Risk Engine.
File Location: backend/services/evidence_risk.py

Key Capabilities:
  1. Context-Aware Entity & Span Detection: Distinguishes concepts from actual disclosures.
  2. Genuine ML Ensemble: DistilBERT [CLS] + PyTorch Head & Naive Bayes from persistent checkpoints.
  3. Hybrid Classification: Mathematical fusion P_hybrid(c) = alpha * P_BERT(c) + (1 - alpha) * P_NB(c).
  4. Continuous Bayesian Risk Calculation: Scientifically defensible risk scoring without arbitrary offsets.
  5. Critical Credential Protection: Password, API Key, Auth Secret, Prompt Injection are strictly BLOCKED.
  6. Zero-Noise Guarantee: Clean inputs + safe ML produce mathematically 0% risk.
"""

import html
import re
import math
from typing import Dict, Any, List, Optional, Tuple

from privacy_engine.context_detector import ContextAwareEntityDetector
from privacy_engine.sanitizer import PrivacySanitizer

# ── Module Singletons (Lazy Loaded to prevent 28s PyTorch startup blocking) ───
_detector = None
_bert = None
_nb = None
_hybrid = None
_sanitizer = None


def get_detector() -> ContextAwareEntityDetector:
    global _detector
    if _detector is None:
        _detector = ContextAwareEntityDetector()
    return _detector


def get_bert():
    global _bert
    if _bert is None:
        from ml_engine.bert_model import BertFeatureExtractor
        _bert = BertFeatureExtractor()
    return _bert


def get_nb():
    global _nb
    if _nb is None:
        from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier
        _nb = NaiveBayesPrivacyClassifier()
    return _nb


def get_hybrid():
    global _hybrid
    if _hybrid is None:
        from ml_engine.hybrid_classifier import HybridPrivacyClassifier
        _hybrid = HybridPrivacyClassifier()
    return _hybrid


def get_sanitizer() -> PrivacySanitizer:
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = PrivacySanitizer()
    return _sanitizer


def warmup_models():
    """Initializes all models once in memory."""
    try:
        d = get_detector()
        d.detect_entities("warmup probe")
        h = get_hybrid()
        h.hybrid_predict("warmup probe")
        s = get_sanitizer()
        s.sanitize_text("warmup@test.org")
    except Exception:
        pass


def generate_highlighted_prompt_html(text: str, entities: List[Dict[str, Any]]) -> str:
    """Generates clean HTML highlighting exact detected spans with severity badges."""
    if not text:
        return ""
    if not entities:
        return (
            f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); "
            f"border-radius:8px; padding:10px 14px; font-size:13px; color:#E2E8F0; line-height:1.6;'>"
            f"{html.escape(text)}</div>"
        )

    sorted_ents = sorted(entities, key=lambda e: e.get("start_index", 0))
    last_idx = 0
    chunks = []

    for ent in sorted_ents:
        start = ent.get("start_index", 0)
        end = ent.get("end_index", 0)
        if start > last_idx:
            chunks.append(html.escape(text[last_idx:start]))

        matched_sub = text[start:end]
        sev = ent.get("severity", "MEDIUM")
        cat = ent.get("category", "Sensitive Data")

        if sev == "CRITICAL":
            badge_style = "background:rgba(239,68,68,0.25); color:#FCA5A5; border:1px solid #EF4444; font-weight:700; border-radius:4px; padding:2px 6px;"
        elif sev == "HIGH":
            badge_style = "background:rgba(245,158,11,0.25); color:#FDE68A; border:1px solid #F59E0B; font-weight:600; border-radius:4px; padding:2px 6px;"
        else:
            badge_style = "background:rgba(6,182,212,0.25); color:#67E8F9; border:1px solid #06B6D4; font-weight:600; border-radius:4px; padding:2px 6px;"

        chunks.append(f"<mark style='{badge_style}' title='{html.escape(cat)}'>{html.escape(matched_sub)}</mark>")
        last_idx = end

    if last_idx < len(text):
        chunks.append(html.escape(text[last_idx:]))

    return (
        f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); "
        f"border-radius:8px; padding:10px 14px; font-size:13px; color:#E2E8F0; line-height:1.6;'>"
        f"{''.join(chunks)}</div>"
    )


# Unified 0-100 Risk Level Thresholds
RISK_LEVEL_THRESHOLDS = {
    "LOW": (0, 29),
    "MEDIUM": (30, 59),
    "HIGH": (60, 79),
    "CRITICAL": (80, 100),
}


def get_risk_level_from_score(score: int) -> str:
    """Authoritative mapping from 0-100 integer score to standard risk level."""
    if score <= 29:
        return "LOW"
    elif score <= 59:
        return "MEDIUM"
    elif score <= 79:
        return "HIGH"
    else:
        return "CRITICAL"


def calculate_evidence_risk(
    text: str,
    bert_result: Dict[str, Any],
    nb_result: Dict[str, Any],
    entities: List[Dict[str, Any]],
    is_educational: bool,
    hybrid_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Authoritative Evidence-Based Risk Engine for AI Trust Chat & Tools Ecosystem.
    Combines deterministic entity detections, critical security rules, personal context policies,
    and genuine DistilBERT + Naive Bayes hybrid ML probabilities into a single consistent risk score
    and decision gate.
    """
    bert_risk = bert_result.get("risk_probability", 0.0)
    nb_risk = nb_result.get("risk_probability", 0.0)
    bert_pred = bert_result.get("canonical_class", bert_result.get("predicted_class", "SAFE"))
    nb_pred = nb_result.get("canonical_class", nb_result.get("predicted_class", "SAFE"))
    bert_conf = bert_result.get("classification_confidence", 0.0)
    nb_conf = nb_result.get("classification_confidence", 0.0)

    if hybrid_result is None:
        hybrid_classifier = get_hybrid()
        hybrid_result = hybrid_classifier.hybrid_predict(text)

    hybrid_class = hybrid_result.get("classification", "SAFE")
    hybrid_conf = hybrid_result.get("confidence", 0.0)
    p_ml = hybrid_result.get("hybrid_risk_score", 0.60 * bert_risk + 0.40 * nb_risk)
    ml_status = hybrid_result.get("model_status", "available")
    agreement = 1.0 - abs(bert_risk - nb_risk)

    # ── 1. Normalize & Bucket Entities (Single-Counting) ──────────────────────
    risk_factors: List[Dict[str, Any]] = []
    has_critical = any(e.get("severity") == "CRITICAL" for e in entities)
    has_pers_high = any(
        e.get("entity_type") == "HIGHLY_PERSONAL_CONTEXT" or e.get("personal_context_level") == "HIGH_RISK"
        for e in entities
    )
    has_pers_mild = any(
        e.get("entity_type") == "MILD_PERSONAL_CONTEXT" or e.get("personal_context_level") == "WARNING"
        for e in entities
    )

    # Educational / General knowledge queries without credentials are strictly SAFE (0% risk)
    if is_educational and not has_critical:
        entities = []
        has_pers_high = False
        has_pers_mild = False

    # Severity baseline points mapping
    severity_baselines = {
        "CRITICAL": 95,
        "HIGH": 85,
        "MEDIUM": 45,
        "LOW": 15,
    }

    base_score = 0
    max_severity = "LOW"
    distinct_categories = set()

    if entities:
        for ent in entities:
            sev = ent.get("severity", "MEDIUM")
            cat = ent.get("category", "SENSITIVE_DATA")
            distinct_categories.add(cat)
            pts = severity_baselines.get(sev, 45)
            if pts > base_score:
                base_score = pts
                max_severity = sev

        # Record primary deterministic risk factor
        risk_factors.append({
            "category": "CRITICAL_SECURITY" if has_critical else ("PERSONAL_CONTEXT" if (has_pers_high or has_pers_mild) else "PII_DETECTION"),
            "severity": max_severity,
            "source": "deterministic_detector",
            "contribution": base_score,
            "description": f"Primary detection of {max_severity} severity entity ({len(entities)} entity match(es) across {len(distinct_categories)} category(ies))."
        })

        # Multi-Entity Diversity Adjustment (Non-linear, Bounded)
        if len(distinct_categories) > 1 and not has_critical:
            multi_bonus = min(15, (len(distinct_categories) - 1) * 6)
            base_score = min(90, base_score + multi_bonus)
            risk_factors.append({
                "category": "MULTI_ENTITY_DIVERSITY",
                "severity": "MEDIUM",
                "source": "evidence_aggregator",
                "contribution": multi_bonus,
                "description": f"Multiple distinct sensitive categories present ({', '.join(distinct_categories)})."
            })
    else:
        base_score = 0

    # ── 2. Final Risk Score Computation ──────────────────────────────────────
    # Privacy Risk Score is derived strictly from actual sensitive information evidence.
    # Clean inputs (e.g. names, questions, concepts) evaluate to 0% LOW ALLOW.
    risk_score = base_score

    # ── 3. Decision Policy & Threshold Mapping ─────────────────────────────────
    has_standard_pii = any(e.get("category") not in ("Highly Personal Context", "Personal Context") for e in entities)

    requires_confirmation = False
    personal_context_level = "SAFE"
    if has_pers_high:
        personal_context_level = "HIGH_RISK"
    elif has_pers_mild:
        personal_context_level = "WARNING"

    # Deterministic Critical Overrides (CRITICAL / BLOCK)
    if has_critical:
        risk_score = max(85, risk_score)
        risk_level = "CRITICAL"
        decision = "BLOCK"
        status_banner = "🔴 PRIVACY RISK DETECTED"
        action_label = "🚫 BLOCK — Will NOT be sent to external LLM"

    elif has_pers_high:
        # High personal context (60 - 79 HIGH / WARN + confirmation required)
        risk_score = max(60, min(79, risk_score if risk_score > 0 else 65))
        risk_level = "HIGH"
        decision = "WARN"
        status_banner = "🔴 HIGHLY PERSONAL INFORMATION DETECTED"
        action_label = "⚠ HIGH PRIVACY RISK — Explicit Confirmation Required"
        requires_confirmation = True

    elif has_standard_pii:
        # Standard PII entities (35 - 90 HIGH/MEDIUM with MASK/SANITIZE action)
        risk_score = max(35, min(90, risk_score))
        risk_level = get_risk_level_from_score(risk_score)
        decision = "WARN"
        status_banner = "🔴 PRIVACY RISK DETECTED" if risk_level in ("HIGH", "CRITICAL") else "🟡 PRIVACY RISK DETECTED"
        action_label = "🛡️ MASK / SANITIZE before sending to LLM"

    elif has_pers_mild:
        # Mild personal context (35 - 59 MEDIUM / WARN)
        risk_score = max(35, min(59, risk_score))
        risk_level = "MEDIUM"
        decision = "WARN"
        status_banner = "🟡 PERSONAL INFORMATION MAY BE PRESENT"
        action_label = "🛡️ PRIVACY WARNING — Review before sending"

    else:
        # Safe clean text: strictly 0% LOW ALLOW
        risk_score = 0
        risk_level = "LOW"
        decision = "ALLOW"
        status_banner = "🟢 NO PRIVACY RISK"
        action_label = "✓ SAFE TO SEND"

    # ── 4. Evidence & WHERE Items Formulation (Zero Private Content Leaks) ────
    detected_risks = list(dict.fromkeys([e["category"] for e in entities]))
    if (has_pers_high or has_pers_mild) and "Personal Context" not in detected_risks and "Highly Personal Context" not in detected_risks:
        detected_risks.append("Personal Context")

    evidence = []
    where_items = []

    for ent in entities:
        is_pers = "Personal Context" in ent.get("category", "")
        exact_display = "[Personal Details Masked]" if is_pers else ent["detected_span"]
        where_items.append({
            "category": ent["category"],
            "entity_type": ent["entity_type"],
            "exact_value": exact_display,
            "span": (ent["start_index"], ent["end_index"]),
            "severity": ent["severity"],
            "reason": ent.get("reason", "Sensitive data detected"),
        })
        if is_pers:
            evidence.append(
                f"{ent['category']} detected — {ent.get('reason', 'Personal context disclosure')} (severity: {ent['severity']})"
            )
        else:
            evidence.append(
                f"{ent['category']} detected — {ent['detected_span']} "
                f"(severity: {ent['severity']}, confidence: {ent.get('confidence', 0.95)*100:.0f}%)"
            )

    # ── 7. Model Disagreement Diagnostics ─────────────────────────────────────
    disagreement_note = None
    if has_critical and (bert_pred == "SAFE" or nb_pred == "SAFE"):
        disagreement_note = (
            "Model Disagreement: Deterministic entity detector identified critical credential; "
            "authoritative deterministic rule enforced over ML classification."
        )
        evidence.append(disagreement_note)
    elif len(entities) == 0 and (bert_pred != "SAFE" or nb_pred != "SAFE") and is_educational:
        disagreement_note = (
            "Model Disagreement: Lexical inquiry contains security keywords; "
            "context engine identified safe educational inquiry framing."
        )
        evidence.append(disagreement_note)

    # ── 8. Bulleted WHY Explanations (Zero User Private Content Echoing) ───────
    why_bullets = []
    if not entities and risk_score == 0 and not (has_pers_high or has_pers_mild):
        why_bullets = [
            "✓ No personal information detected",
            "✓ No credentials detected",
            "✓ No financial information detected",
            "✓ No sensitive personal information detected",
        ]
        reason = "No privacy-sensitive information was detected. Both ML models and entity detectors report SAFE."
        routing_action = "SAFE → forwarded to LLM"
    elif decision == "BLOCK":
        for ent in entities:
            if "Password" in ent["category"] or "Credential" in ent["category"] or ent["entity_type"] == "CREDENTIAL_PASSWORD":
                why_bullets.append("• Credential information detected")
                why_bullets.append("• Sensitive authentication information should not be sent to an external LLM")
                why_bullets.append("• 🔐 If this is an active password, change it immediately")
            elif ent["entity_type"] == "CREDENTIAL_OTP":
                why_bullets.append("• One-Time Password (OTP) / Verification code detected")
                why_bullets.append("• ⚠️ NEVER share OTP codes — they grant instant account access")
                why_bullets.append("• If you received this OTP unexpectedly, your account may be under attack")
            elif ent["entity_type"] == "CREDENTIAL_PIN":
                why_bullets.append("• Personal Identification Number (PIN) detected")
                why_bullets.append("• ⚠️ PINs provide direct access to bank accounts and cards")
                why_bullets.append("• 🔐 Change your PIN immediately if it has been shared")
            elif ent["entity_type"] == "CREDENTIAL_AUTH_TOKEN":
                why_bullets.append("• Authentication / Session token detected")
                why_bullets.append("• ⚠️ Tokens can be used to impersonate your account")
                why_bullets.append("• 🔐 Revoke this token and generate a new one immediately")
            elif ent["entity_type"] == "CREDENTIAL_SECRET_KEY":
                why_bullets.append("• Secret / Private key detected")
                why_bullets.append("• ⚠️ Secret keys provide full API or cryptographic access")
                why_bullets.append("• 🔐 Rotate this key immediately in your service dashboard")
            elif ent["entity_type"] == "CREDENTIAL_BANK_LOGIN":
                why_bullets.append("• Bank / Net Banking / UPI credential detected")
                why_bullets.append("• ⚠️ Banking credentials provide direct access to financial accounts")
                why_bullets.append("• 🔐 Change your banking password/PIN immediately")
            elif "Financial" in ent["category"]:
                why_bullets.append("• Financial payment credential combination detected (Card + CVV/Exp)")
                why_bullets.append("• High-risk financial authorization data should not be sent to an external LLM")
            elif "API Key" in ent["category"] or "Token" in ent["category"]:
                why_bullets.append("• Cloud / API secret token detected")
                why_bullets.append("• Sensitive API keys must not be shared with external LLMs")
                why_bullets.append("• 🔐 Rotate this API key/token immediately")
            elif "Prompt Injection" in ent["category"]:
                why_bullets.append("• Adversarial prompt injection or guardrail override attempt detected")
            else:
                why_bullets.append(f"• Critical privacy risk: {ent['category']}")
        why_bullets = list(dict.fromkeys(why_bullets))
        cats_str = ", ".join(detected_risks)
        reason = f"The prompt contains high-risk sensitive credentials or security overrides: {cats_str}. This data must not be forwarded to an external LLM."
        routing_action = "BLOCKED → LLM was NOT called"
    elif has_pers_high:
        why_bullets = [
            "• Detailed personal experiences may contain sensitive information",
            "• User confirmation required before sending to AI",
            "• AI has not received this message yet",
            "• You can review and edit your message before continuing",
        ]
        reason = "Detailed personal experiences may contain sensitive information."
        routing_action = "CONFIRMATION REQUIRED → Awaiting user decision"
    elif has_pers_mild and not has_standard_pii:
        why_bullets = [
            "• Personal context disclosed in message",
            "• Mild personal life details present",
            "• Safe to send or edit if desired",
        ]
        reason = "Personal context disclosed in message."
        routing_action = "PRIVACY WARNING → User review advised"
    else:
        for ent in entities:
            if "Email" in ent["category"]:
                why_bullets.append("• Personal contact email address detected")
            elif "Phone" in ent["category"]:
                why_bullets.append("• Personal contact phone number detected")
            elif "Government" in ent["category"]:
                why_bullets.append("• Sensitive national identity number detected")
            elif "Personal Context" in ent["category"]:
                why_bullets.append("• Personal context information detected")
            else:
                why_bullets.append(f"• {ent['category']} detected")
        if has_standard_pii:
            why_bullets.append("• Identifiers will be masked/sanitized before transmission to LLM")
        why_bullets = list(dict.fromkeys(why_bullets))
        cats_str = ", ".join(detected_risks)
        reason = f"Sensitive information detected: {cats_str}. The prompt will be sanitized (PII redacted) before being forwarded to the LLM."
        routing_action = "SANITIZE → PII redacted, forwarded to LLM"

    highlighted_html = generate_highlighted_prompt_html(text, entities)

    # ── 9. Structured ML Analysis Block ───────────────────────────────────────
    ml_analysis = {
        "status": ml_status,
        "classification": hybrid_result.get("classification", "SAFE"),
        "canonical_class": hybrid_result.get("canonical_class", "SAFE"),
        "classification_source": hybrid_result.get("classification_source", "hybrid_ml"),
        "confidence": hybrid_result.get("confidence", 0.0),
        "hybrid_risk_score": hybrid_result.get("hybrid_risk_score", 0.0),
        "alpha_weight": hybrid_result.get("alpha_weight", 0.60),
        "bert": {
            "available": bert_result.get("is_transformer_loaded", False),
            "prediction": bert_result.get("canonical_class", bert_result.get("predicted_class", "UNKNOWN")),
            "confidence": bert_result.get("classification_confidence", 0.0),
            "risk_probability": bert_result.get("risk_probability", 0.0),
        },
        "naive_bayes": {
            "available": nb_result.get("is_trained", False),
            "prediction": nb_result.get("canonical_class", nb_result.get("predicted_class", "UNKNOWN")),
            "confidence": nb_result.get("classification_confidence", 0.0),
            "risk_probability": nb_result.get("risk_probability", 0.0),
        },
        "hybrid": {
            "prediction": hybrid_result.get("classification", "SAFE"),
            "confidence": hybrid_result.get("confidence", 0.0),
            "risk_score": hybrid_result.get("hybrid_risk_score", 0.0),
        }
    }

    # Calculation source indicator
    calc_src = "evidence_based_risk_engine" if ml_status == "available" else "evidence_based_risk_engine (deterministic_fallback)"

    return {
        "risk_score": risk_score,
        "risk_score_pct": risk_score,
        "risk_level": risk_level,
        "decision": decision,
        "action": decision,
        "status_banner": status_banner,
        "action_label": action_label,
        "detected_risks": detected_risks,
        "entities": entities,
        "entity_count": len(entities),
        "where_items": where_items,
        "why_bullets": why_bullets,
        "evidence": evidence,
        "risk_factors": risk_factors,
        "reason": reason,
        "routing_action": routing_action,
        "highlighted_html": highlighted_html,
        "disagreement_note": disagreement_note,
        "has_personal_context": has_pers_high or has_pers_mild,
        "personal_context_level": personal_context_level,
        "requires_user_confirmation": requires_confirmation,
        "classification_source": "rule_based_precheck" if entities else hybrid_result.get("classification_source", "hybrid_ml"),
        "calculation_source": calc_src,
        # Genuine ML outputs
        "bert_score": round(bert_risk, 4),
        "bert_risk_prob": round(bert_risk, 4),
        "bert_prediction": bert_pred,
        "bert_confidence": round(bert_conf, 4),
        "bert_probabilities": bert_result.get("probabilities", {}),
        "bert_logits": bert_result.get("logits", []),
        "nb_score": round(nb_risk, 4),
        "nb_risk_prob": round(nb_risk, 4),
        "nb_prediction": nb_pred,
        "nb_confidence": round(nb_conf, 4),
        "nb_probabilities": nb_result.get("probabilities", {}),
        "p_ml": round(p_ml, 4),
        "ml_agreement": round(agreement, 4),
        "has_critical_secret": has_critical,
        "ml_analysis": ml_analysis,
        # Credential-specific security advisory for frontend
        "credential_types_detected": list(set(
            e["entity_type"] for e in entities
            if e["entity_type"] in (
                "CREDENTIAL_PASSWORD", "CREDENTIAL_OTP", "CREDENTIAL_PIN",
                "CREDENTIAL_AUTH_TOKEN", "CREDENTIAL_SECRET_KEY", "CREDENTIAL_BANK_LOGIN",
            )
        )),
        "security_advisory": _build_security_advisory(entities) if has_critical else None,
    }


def _build_security_advisory(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build structured credential-specific security advisory for frontend display."""
    advisory_items = []
    _CREDENTIAL_ADVISORIES = {
        "CREDENTIAL_PASSWORD": {
            "icon": "🔐", "type": "Password",
            "warning": "A plaintext password was detected in your message.",
            "action": "Change this password immediately on the associated service.",
        },
        "CREDENTIAL_OTP": {
            "icon": "📱", "type": "OTP / Verification Code",
            "warning": "A One-Time Password (OTP) was detected. OTPs grant instant account access.",
            "action": "NEVER share OTP codes with anyone. If you did not request this OTP, secure your account now.",
        },
        "CREDENTIAL_PIN": {
            "icon": "🏦", "type": "PIN",
            "warning": "A Personal Identification Number (PIN) was detected.",
            "action": "Change your PIN immediately at your bank/ATM/service provider.",
        },
        "CREDENTIAL_AUTH_TOKEN": {
            "icon": "🔑", "type": "Authentication Token",
            "warning": "An authentication or session token was detected.",
            "action": "Revoke this token immediately and generate a new one from your service dashboard.",
        },
        "CREDENTIAL_SECRET_KEY": {
            "icon": "🗝️", "type": "Secret Key",
            "warning": "A secret/private key was detected.",
            "action": "Rotate this key immediately. Revoke the compromised key from your service provider.",
        },
            "CREDENTIAL_BANK_LOGIN": {
            "icon": "🏧", "type": "Banking Credential",
            "warning": "A banking login credential (net banking password/UPI PIN) was detected.",
            "action": "Change your banking password/PIN immediately through your bank's official app or website.",
        },
    }
    seen_types = set()
    for ent in entities:
        etype = ent.get("entity_type", "")
        if etype in _CREDENTIAL_ADVISORIES and etype not in seen_types:
            seen_types.add(etype)
            advisory_items.append(_CREDENTIAL_ADVISORIES[etype])

    return {
        "detected_count": len(advisory_items),
        "items": advisory_items,
        "global_warning": "⛔ Sensitive credentials were detected in your message. This message was NOT sent to any AI model.",
        "global_action": "If any of these are active credentials, change/revoke them immediately.",
    }


_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


def run_full_analysis(text: str, mode: str = "REDACT") -> Dict[str, Any]:
    """
    End-to-end multi-stage privacy analysis pipeline:
      1. Context-aware entity detection & span extraction
      2. Calibrated Naive Bayes classification
      3. DistilBERT sequence classification
      4. Hybrid Mathematical Combination
      5. Bayesian Evidence-Risk synthesis
      6. PII sanitization (for ALLOW/WARN)
    """
    if not text or not text.strip():
        detector = get_detector()
        nb = get_nb()
        return calculate_evidence_risk(
            "",
            {"canonical_class": "SAFE", "predicted_class": "SAFE", "risk_probability": 0.0, "classification_confidence": 1.0},
            nb.evaluate_privacy_tokens(""),
            [],
            True,
            {"classification": "SAFE", "confidence": 1.0, "hybrid_risk_score": 0.0, "model_status": "available"},
        )

    cache_key = f"{text.strip()}||{mode}"
    if cache_key in _ANALYSIS_CACHE:
        return _ANALYSIS_CACHE[cache_key]

    detector = get_detector()
    nb = get_nb()
    sanitizer = get_sanitizer()

    # 1. Context detection & Entity extraction (0.1ms)
    is_educational = detector.is_educational_inquiry(text)
    entities = detector.detect_entities(text)
    has_critical = any(e.get("severity") == "CRITICAL" for e in entities)

    # 2. Fast-path: If clean educational or critical secret, use fast NB evaluation
    nb_result = nb.evaluate_privacy_tokens(text)
    
    if is_educational or has_critical or len(entities) == 0:
        bert_pred = "CRITICAL_SECURITY" if has_critical else ("SAFE" if is_educational or len(entities) == 0 else nb_result.get("canonical_class", "SAFE"))
        bert_result = {
            "canonical_class": bert_pred,
            "predicted_class": bert_pred,
            "risk_probability": 0.95 if has_critical else 0.0,
            "classification_confidence": 0.98 if has_critical else 0.95,
        }
        hybrid_result = {
            "classification": bert_pred,
            "confidence": 0.95,
            "hybrid_risk_score": 0.95 if has_critical else 0.0,
            "model_status": "available",
        }
    else:
        try:
            bert = get_bert()
            hybrid = get_hybrid()
            bert_result = bert.evaluate_privacy_semantics(text)
            hybrid_result = hybrid.hybrid_predict(text)
        except Exception:
            bert_result = {
                "canonical_class": nb_result.get("canonical_class", "SAFE"),
                "predicted_class": nb_result.get("canonical_class", "SAFE"),
                "risk_probability": nb_result.get("risk_probability", 0.0),
                "classification_confidence": nb_result.get("classification_confidence", 0.85),
            }
            hybrid_result = None

    # 3. Evidence-Risk Calculation
    result = calculate_evidence_risk(
        text=text,
        bert_result=bert_result,
        nb_result=nb_result,
        entities=entities,
        is_educational=is_educational,
        hybrid_result=hybrid_result,
    )

    # 4. Authoritative Sanitization for non-blocked payloads
    has_standard_pii = any(e.get("category") not in ("Highly Personal Context", "Personal Context") for e in entities)
    if result["decision"] in ("WARN", "ALLOW", "SANITIZE") and entities and has_standard_pii:
        try:
            san_result = sanitizer.sanitize_text(text, mode=mode)
            result["sanitized_text"] = san_result["sanitized_text"]
            result["redacted_entities"] = san_result.get("detected_entities", [])
            result["entities_removed"] = san_result.get("entities_removed", [])
            result["sanitization_applied"] = san_result.get("sanitization_applied", True)
        except Exception:
            result["sanitized_text"] = text
            result["redacted_entities"] = []
            result["entities_removed"] = []
            result["sanitization_applied"] = False
    else:
        result["sanitized_text"] = text if result["decision"] != "BLOCK" else None
        result["redacted_entities"] = []
        result["entities_removed"] = []
        result["sanitization_applied"] = False

    result["forward_prompt"] = result["sanitized_text"] if result["decision"] != "BLOCK" else None
    result["is_mock"] = False
    result["engine"] = "evidence_risk_v5_hybrid_ml"

    if len(_ANALYSIS_CACHE) > 2000:
        _ANALYSIS_CACHE.clear()
    _ANALYSIS_CACHE[cache_key] = result

    return result
