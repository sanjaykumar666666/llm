"""
Privacy Decision Engine & Policy Threshold Evaluator.
File Location: privacy_engine/evaluator.py
"""

from typing import Dict, Any, List
import config

CRITICAL_SECRET_TYPES = {
    "AWS_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "GENERIC_SECRET_KEY",
    "JWT_TOKEN", "PRIVATE_KEY_BLOCK", "CREDENTIAL_PASSWORD"
}


class PrivacyEvaluator:
    """
    Evaluates ML privacy risk scores, entity severity weights, and security policies to enforce
    ALLOW, SANITIZE, or BLOCK decisions.
    """

    def __init__(self):
        self.threshold_low = config.THRESHOLD_LOW_RISK    # Default 0.30
        self.threshold_high = config.THRESHOLD_HIGH_RISK  # Default 0.75

    def evaluate_decision(
        self,
        risk_score: float,
        detected_entities: List[str],
        contains_regex_pii: bool = False,
        max_severity: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Maps numerical risk score and entity types to a security decision.
        """
        has_critical_secret = any(ent in CRITICAL_SECRET_TYPES for ent in detected_entities)

        # Rule override: Critical authentication secrets or multiple PII entities force high risk (BLOCK)
        if has_critical_secret or len(detected_entities) >= 2 or risk_score >= self.threshold_high or max_severity >= 0.90:
            risk_level = "HIGH"
            action = "BLOCK"
            if has_critical_secret:
                reason = "High security risk detected: exposed authentication credential or secret API key."
            elif len(detected_entities) >= 2:
                reason = "High privacy risk detected: multiple sensitive PII entities present in payload."
            else:
                reason = "High privacy risk score output by hybrid ML classifier."

        # Moderate risk or single PII entity trigger SANITIZE
        elif contains_regex_pii or risk_score >= self.threshold_low or len(detected_entities) == 1:
            risk_level = "MEDIUM"
            action = "SANITIZE"
            reason = "Moderate privacy risk: sensitive entity detected. Redaction/Sanitization required before LLM transmission."

        else:
            risk_level = "LOW"
            action = "ALLOW"
            reason = "Low privacy risk: content evaluated as safe for direct LLM processing."

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "action": action,
            "reason": reason,
            "detected_entities_count": len(detected_entities),
            "has_critical_secret": has_critical_secret,
        }


# Alias for backward compatibility
AutomatedDecisionGate = PrivacyEvaluator
