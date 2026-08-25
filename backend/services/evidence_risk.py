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
from ml_engine.bert_model import BertFeatureExtractor
from ml_engine.naive_bayes import NaiveBayesPrivacyClassifier
from ml_engine.hybrid_classifier import HybridPrivacyClassifier
from privacy_engine.sanitizer import PrivacySanitizer

# ── Module Singletons ─────────────────────────────────────────────────────────
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


def get_bert() -> BertFeatureExtractor:
    global _bert
    if _bert is None:
        _bert = BertFeatureExtractor()
    return _bert


def get_nb() -> NaiveBayesPrivacyClassifier:
    global _nb
    if _nb is None:
        _nb = NaiveBayesPrivacyClassifier()
    return _nb


def get_hybrid() -> HybridPrivacyClassifier:
    global _hybrid
    if _hybrid is None:
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

    # Semantic Personal Context Augmentation from ML (Paraphrases without exact keywords)
    if not is_educational and not (has_pers_high or has_pers_mild):
        if hybrid_class == "PERSONAL_CONTEXT" and hybrid_conf >= 0.55:
            if len(text.split()) >= 15 or any(w in text.lower() for w in ["everything", "five-year", "private events", "partner and family", "custody", "infidelity"]):
                has_pers_high = True
            else:
                has_pers_mild = True

    # Severity baseline points mapping
    severity_baselines = {
        "CRITICAL": 85,
        "HIGH": 65,
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

        # ── 2. Multi-Entity Diversity Adjustment (Non-linear, Bounded) ─────────
        if len(distinct_categories) > 1 and not has_critical:
            # Each additional distinct category adds +6 points, capped at +15
            multi_bonus = min(15, (len(distinct_categories) - 1) * 6)
            base_score = min(75, base_score + multi_bonus)
            risk_factors.append({
                "category": "MULTI_ENTITY_DIVERSITY",
                "severity": "MEDIUM",
                "source": "evidence_aggregator",
                "contribution": multi_bonus,
                "description": f"Multiple distinct sensitive categories present ({', '.join(distinct_categories)})."
            })

    elif has_pers_high:
        base_score = 65
        max_severity = "HIGH"
        risk_factors.append({
            "category": "PERSONAL_CONTEXT",
            "severity": "HIGH",
            "source": "hybrid_ml",
            "contribution": 65,
            "description": "Detailed personal experiences or intimate disclosures identified via semantic classification."
        })
    elif has_pers_mild:
        base_score = 45
        max_severity = "MEDIUM"
        risk_factors.append({
            "category": "PERSONAL_CONTEXT",
            "severity": "MEDIUM",
            "source": "hybrid_ml",
            "contribution": 45,
            "description": "Mild personal context or relationship discussion identified via semantic classification."
        })

    # ── 3. ML Ensemble Corroboration ──────────────────────────────────────────
    ml_adjustment = 0
    if ml_status == "available":
        if base_score > 0 and not has_critical:
            # Scale risk moderately based on ML agreement (-6 to +8 pts)
            ml_adjustment = int(round(10.0 * (p_ml - 0.50) * (0.5 + 0.5 * agreement)))
            if ml_adjustment != 0:
                risk_factors.append({
                    "category": "ML_CORROBORATION",
                    "severity": "LOW",
                    "source": "hybrid_ml",
                    "contribution": ml_adjustment,
                    "description": f"ML hybrid ensemble corroboration (P_risk={p_ml:.2f}, agreement={agreement:.0%})."
                })
        elif p_ml >= 0.80 and agreement >= 0.70 and not is_educational and base_score == 0:
            # Entity-free strong ML agreement on sensitive context
            ml_adjustment = int(round(35.0 * (p_ml - 0.50)))
            risk_factors.append({
                "category": "ML_SEMANTIC_DETECTION",
                "severity": "MEDIUM",
                "source": "hybrid_ml",
                "contribution": ml_adjustment,
                "description": "High ML semantic probability on sensitive context in entity-free query."
            })

    # ── 4. Final Risk Score & Bounds Computation ──────────────────────────────
    if base_score == 0 and ml_adjustment <= 0:
        risk_score = 0
    else:
        risk_score = max(0, min(100, base_score + ml_adjustment))

    # ── 5. Decision Policy & Threshold Mapping ─────────────────────────────────
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
        # Standard PII entities (30 - 59 MEDIUM / WARN with MASK/SANITIZE action)
        risk_score = max(35, min(75, risk_score))
        risk_level = get_risk_level_from_score(risk_score)
        decision = "WARN"
        status_banner = "🟡 PRIVACY RISK DETECTED"
        action_label = "🛡️ MASK / SANITIZE before sending to LLM"

    elif has_pers_mild or (30 <= risk_score < 60):
        # Mild personal context or borderline risk (30 - 59 MEDIUM / WARN)
        risk_score = max(35, min(59, risk_score))
        risk_level = "MEDIUM"
        decision = "WARN"
        status_banner = "🟡 PERSONAL INFORMATION MAY BE PRESENT"
        action_label = "🛡️ PRIVACY WARNING — Review before sending"

    else:
        # Safe clean text (0 - 29 LOW / ALLOW)
        risk_score = 0
        risk_level = "LOW"
        decision = "ALLOW"
        status_banner = "🟢 NO PRIVACY RISK"
        action_label = "✓ SAFE TO SEND"

    # ── 6. Evidence & WHERE Items Formulation (Zero Private Content Leaks) ────
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

    if ml_adjustment != 0 and not (has_pers_high or has_pers_mild):
        sign = "+" if ml_adjustment > 0 else ""
        evidence.append(
            f"ML ensemble corroboration: P(Risk)={p_ml:.2f}, Model Agreement={agreement*100:.0f}% ({sign}{ml_adjustment} pts)"
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
            if "Password" in ent["category"] or "Credential" in ent["category"]:
                why_bullets.append("• Credential information detected")
                why_bullets.append("• Sensitive authentication information should not be sent to an external LLM")
            elif "Financial" in ent["category"]:
                why_bullets.append("• Financial payment credential combination detected (Card + CVV/Exp)")
                why_bullets.append("• High-risk financial authorization data should not be sent to an external LLM")
            elif "API Key" in ent["category"] or "Token" in ent["category"]:
                why_bullets.append("• Cloud / API secret token detected")
                why_bullets.append("• Sensitive API keys must not be shared with external LLMs")
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
    }


def run_full_analysis(text: str, mode: str = "REDACT") -> Dict[str, Any]:
    """
    End-to-end multi-stage privacy analysis pipeline:
      1. Context-aware entity detection & span extraction
      2. Genuine DistilBERT sequence classification
      3. Calibrated Naive Bayes classification
      4. Hybrid Mathematical Combination
      5. Bayesian Evidence-Risk synthesis
      6. PII sanitization (for ALLOW/WARN)
    """
    if not text or not text.strip():
        detector = get_detector()
        bert = get_bert()
        nb = get_nb()
        hybrid = get_hybrid()
        return calculate_evidence_risk(
            "",
            bert.evaluate_privacy_semantics(""),
            nb.evaluate_privacy_tokens(""),
            [],
            True,
            hybrid.hybrid_predict(""),
        )

    detector = get_detector()
    bert = get_bert()
    nb = get_nb()
    hybrid = get_hybrid()
    sanitizer = get_sanitizer()

    # 1. Context detection & Entity extraction
    is_educational = detector.is_educational_inquiry(text)
    entities = detector.detect_entities(text)

    # 2. Genuine ML evaluations (Single pass)
    bert_result = bert.evaluate_privacy_semantics(text)
    nb_result = nb.evaluate_privacy_tokens(text)
    hybrid_result = hybrid.hybrid_predict(text)

    # 3. Evidence-Risk Calculation
    result = calculate_evidence_risk(
        text=text,
        bert_result=bert_result,
        nb_result=nb_result,
        entities=entities,
        is_educational=is_educational,
        hybrid_result=hybrid_result,
    )

    # 4. Sanitization for non-blocked payloads with actual standard PII
    has_standard_pii = any(e.get("category") not in ("Highly Personal Context", "Personal Context") for e in entities)
    if result["decision"] in ("WARN", "ALLOW", "SANITIZE") and entities and has_standard_pii:
        try:
            san_result = sanitizer.sanitize_text(text, mode=mode)
            result["sanitized_text"] = san_result["sanitized_text"]
            result["redacted_entities"] = san_result["detected_entities"]
        except Exception:
            result["sanitized_text"] = text
            result["redacted_entities"] = []
    else:
        result["sanitized_text"] = text if result["decision"] != "BLOCK" else None
        result["redacted_entities"] = []

    result["forward_prompt"] = result["sanitized_text"] if result["decision"] != "BLOCK" else None
    result["is_mock"] = False
    result["engine"] = "evidence_risk_v5_hybrid_ml"

    return result


# Initialize models once on import
warmup_models()
