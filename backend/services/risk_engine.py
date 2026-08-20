"""
AI Trust Chat — Risk Engine
0-100 integer risk scoring with 4 risk levels (LOW/MEDIUM/HIGH/CRITICAL).
File: backend/services/risk_engine.py
"""

from typing import Dict, Any, List


# Risk level thresholds
RISK_LEVELS = {
    "LOW":      (0,  29),
    "MEDIUM":   (30, 59),
    "HIGH":     (60, 79),
    "CRITICAL": (80, 100),
}

RISK_COLORS = {
    "LOW":      "#10B981",
    "MEDIUM":   "#F59E0B",
    "HIGH":     "#EF4444",
    "CRITICAL": "#DC2626",
}


def get_risk_level(score: int) -> str:
    """Map 0-100 integer score to risk level string."""
    if score <= 29:
        return "LOW"
    elif score <= 59:
        return "MEDIUM"
    elif score <= 79:
        return "HIGH"
    else:
        return "CRITICAL"


def get_risk_color(risk_level: str) -> str:
    return RISK_COLORS.get(risk_level, "#94A3B8")


def calculate_risk_score(
    pii_entities: List[Dict[str, Any]],
    injection_detected: bool,
    injection_confidence: float,
    secret_detected: bool,
    doc_classification: str = "PUBLIC",
    output_sensitive: bool = False,
    base_ml_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Aggregate all security signals into a single 0-100 risk score.

    Signal weights:
      - Prompt injection (confirmed): +50
      - Injection confidence (0-1): +0 to +20 additional
      - PII detected (per entity, capped): +15 per entity, max +45
      - Secret/credential detected: +35
      - Restricted document: +30 / Confidential: +20 / Internal: +10
      - Sensitive output: +25
      - ML base score (0-1 → 0-10): +0 to +10

    Returns dict with score (int), risk_level, breakdown, color.
    """
    score = 0
    breakdown = []

    # Signal: Prompt injection
    if injection_detected:
        inj_pts = 50
        score += inj_pts
        breakdown.append({
            "signal": "Prompt Injection",
            "points": inj_pts,
            "detail": f"Injection pattern detected (confidence: {injection_confidence:.0%})"
        })
        # Bonus points for high confidence
        if injection_confidence > 0.8:
            bonus = int((injection_confidence - 0.8) * 100)
            score += bonus
            if bonus:
                breakdown.append({"signal": "Injection Confidence Bonus", "points": bonus, "detail": f"{injection_confidence:.0%}"})

    # Signal: PII entities
    pii_pts = min(len(pii_entities) * 15, 45)
    if pii_pts > 0:
        score += pii_pts
        entity_names = [e.get("entity_type", "PII") for e in pii_entities]
        breakdown.append({
            "signal": "PII Detected",
            "points": pii_pts,
            "detail": f"{len(pii_entities)} entity type(s): {', '.join(entity_names)}"
        })

    # Signal: Secret/credential
    if secret_detected:
        score += 35
        breakdown.append({"signal": "Secret/Credential Detected", "points": 35, "detail": "API key, password, or access token found"})

    # Signal: Document classification
    doc_pts_map = {"RESTRICTED": 30, "CONFIDENTIAL": 20, "INTERNAL": 10, "PUBLIC": 0}
    doc_pts = doc_pts_map.get(doc_classification.upper(), 0)
    if doc_pts > 0:
        score += doc_pts
        breakdown.append({"signal": f"Document Classification: {doc_classification}", "points": doc_pts, "detail": "RAG retrieval from sensitive document"})

    # Signal: Sensitive output
    if output_sensitive:
        score += 25
        breakdown.append({"signal": "Sensitive Output", "points": 25, "detail": "LLM response contained sensitive information"})

    # Signal: ML base score
    ml_pts = int(base_ml_score * 10)
    if ml_pts > 0:
        score += ml_pts
        breakdown.append({"signal": "ML Classifier", "points": ml_pts, "detail": f"Hybrid BERT+NaiveBayes score: {base_ml_score:.2f}"})

    # Clamp to 0-100
    score = max(0, min(100, score))
    risk_level = get_risk_level(score)

    return {
        "score": score,
        "risk_level": risk_level,
        "color": get_risk_color(risk_level),
        "breakdown": breakdown,
    }
