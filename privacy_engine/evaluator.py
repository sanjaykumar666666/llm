"""
Privacy Decision Engine & Policy Threshold Evaluator.
File Location: privacy_engine/evaluator.py
"""

from typing import Dict, Any, List
import config

CRITICAL_SECRET_TYPES = {
    "AWS_KEY", "AWS_ACCESS_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "GENERIC_SECRET_KEY",
    "JWT_TOKEN", "PRIVATE_KEY_BLOCK", "CREDENTIAL_PASSWORD", "DATABASE_CONNECTION_STRING",
    "GOOGLE_CLOUD_API_KEY", "SENDGRID_API_KEY", "SLACK_BOT_TOKEN", "BEARER_TOKEN",
    "PROMPT_INJECTION", "PROMPT_INJECTION_OVERRIDE", "AUTHENTICATION_SECRET",
    "CREDENTIAL_OTP", "CREDENTIAL_PIN", "CREDENTIAL_AUTH_TOKEN",
    "CREDENTIAL_SECRET_KEY", "CREDENTIAL_BANK_LOGIN",
}


class PrivacyEvaluator:
    """
    Evaluates ML privacy risk scores, entity severity weights, and security policies to enforce
    ALLOW, SANITIZE, or BLOCK decisions.
    """

    def __init__(self):
        self.threshold_low = config.THRESHOLD_LOW_RISK    # Default 0.30 (30 on 0-100)
        self.threshold_high = 0.80                        # 0.80 (80 on 0-100)

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
        # Normalize score to 0.0 - 1.0 if passed as 0 - 100
        norm_score = risk_score / 100.0 if risk_score > 1.0 else risk_score
        has_critical_secret = any(ent in CRITICAL_SECRET_TYPES for ent in detected_entities)

        # Rule override: Critical authentication secrets or injection force CRITICAL / BLOCK
        if has_critical_secret or norm_score >= self.threshold_high or max_severity >= 0.90:
            risk_level = "CRITICAL" if (has_critical_secret or norm_score >= 0.80) else "HIGH"
            action = "BLOCK"
            if has_critical_secret:
                reason = "High security risk detected: exposed authentication credential or secret API key."
            else:
                reason = "Critical privacy risk score output by hybrid ML classifier."

        # High risk / multiple entities trigger SANITIZE or WARN
        elif len(detected_entities) >= 2 or norm_score >= 0.60:
            risk_level = "HIGH"
            action = "SANITIZE"
            reason = "High privacy risk detected: multiple sensitive PII entities present in payload."

        # Moderate risk or single PII entity trigger SANITIZE
        elif contains_regex_pii or norm_score >= self.threshold_low or len(detected_entities) == 1:
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
            "decision": action,
            "reason": reason,
            "detected_entities_count": len(detected_entities),
            "has_critical_secret": has_critical_secret,
            "calculation_source": "evidence_based_risk_engine",
        }


# Alias for backward compatibility
AutomatedDecisionGate = PrivacyEvaluator
