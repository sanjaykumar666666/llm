"""
Privacy Decision Engine & Policy Threshold Evaluator.
File Location: privacy_engine/evaluator.py
"""

from typing import Dict, Any, List, Optional, Union
import config

CRITICAL_SECRET_TYPES = {
    "AWS_KEY", "AWS_ACCESS_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "GENERIC_SECRET_KEY",
    "JWT_TOKEN", "PRIVATE_KEY_BLOCK", "CREDENTIAL_PASSWORD", "DATABASE_CONNECTION_STRING",
    "GOOGLE_CLOUD_API_KEY", "SENDGRID_API_KEY", "SLACK_BOT_TOKEN", "BEARER_TOKEN",
    "PROMPT_INJECTION", "PROMPT_INJECTION_OVERRIDE", "AUTHENTICATION_SECRET",
    "CREDENTIAL_OTP", "CREDENTIAL_PIN", "CREDENTIAL_AUTH_TOKEN",
    "CREDENTIAL_SECRET_KEY", "CREDENTIAL_BANK_LOGIN",
}


from enum import Enum

class PolicyMode(str, Enum):
    STRICT = "STRICT"
    BALANCED = "BALANCED"
    UTILITY = "UTILITY"


class PrivacyEvaluator:
    """
    Intelligent Policy-Based Privacy Decision Engine.
    Evaluates Hybrid ML risk scores, detected entity categories, and policy modes
    to produce ALLOW, REDACT, WARN, or BLOCK decisions.
    """

    POLICY_PRESETS = {
        "STRICT": {
            "threshold_low": 0.15,
            "threshold_high": 0.50,
            "block_on_any_pii": True,
            "description": "Strict Privacy Mode — Aggressively redacts PII and blocks medium-to-high risk prompts.",
        },
        "BALANCED": {
            "threshold_low": 0.30,
            "threshold_high": 0.75,
            "block_on_any_pii": False,
            "description": "Balanced Privacy Mode — Redacts standard PII while blocking critical credentials & prompt injections.",
        },
        "UTILITY": {
            "threshold_low": 0.45,
            "threshold_high": 0.88,
            "block_on_any_pii": False,
            "description": "Utility-Focused Mode — Maximizes task context, redacting PII only when critical secrets are present.",
        },
    }

    def __init__(self, policy_mode: Union[str, PolicyMode] = "BALANCED", custom_high_threshold: Optional[float] = None):
        if isinstance(policy_mode, PolicyMode):
            policy_mode = policy_mode.value
        self.policy_mode = str(policy_mode).upper() if policy_mode else "BALANCED"
        preset = self.POLICY_PRESETS.get(self.policy_mode, self.POLICY_PRESETS["BALANCED"])

        self.threshold_low = preset["threshold_low"]
        self.threshold_high = custom_high_threshold if custom_high_threshold is not None else preset["threshold_high"]

    def evaluate_decision(
        self,
        risk_score: float,
        detected_entities: List[str],
        contains_regex_pii: bool = False,
        max_severity: float = 0.0,
        policy_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Maps numerical risk score and entity types to policy-based security decision.
        """
        active_mode = (policy_mode.upper() if policy_mode else self.policy_mode)
        preset = self.POLICY_PRESETS.get(active_mode, self.POLICY_PRESETS["BALANCED"])
        low_t = preset["threshold_low"]
        high_t = self.threshold_high if policy_mode is None else preset["threshold_high"]

        norm_score = risk_score / 100.0 if risk_score > 1.0 else risk_score
        has_critical_secret = any(ent in CRITICAL_SECRET_TYPES for ent in detected_entities)

        # 1. Critical Secrets, Passwords, API keys, Govt IDs -> BLOCKED
        if has_critical_secret or norm_score >= high_t or max_severity >= 0.90 or (active_mode == "STRICT" and (len(detected_entities) >= 1 or norm_score >= low_t)):
            risk_level = "CRITICAL" if (has_critical_secret or norm_score >= 0.80) else "HIGH"
            action = "BLOCKED"
            if has_critical_secret:
                reason = f"[{active_mode} MODE] Critical security risk: exposed authentication credential, secret API key, or card CVV."
            else:
                reason = f"[{active_mode} MODE] Critical risk score ({int(norm_score*100)}%) exceeded block threshold ({int(high_t*100)}%)."

        # 2. Ordinary Personal & Health Info -> PENDING_USER_DECISION
        elif contains_regex_pii or norm_score >= low_t or len(detected_entities) >= 1:
            risk_level = "MEDIUM" if norm_score < 0.60 else "HIGH"
            action = "PENDING_USER_DECISION"
            reason = f"[{active_mode} MODE] Sensitive personal information detected. User confirmation required before LLM transmission."

        # 3. Neutral General Queries -> ALLOW
        else:
            risk_level = "LOW"
            action = "ALLOW"
            reason = f"[{active_mode} MODE] Content evaluated as safe for direct LLM reasoning."


        res_dict = {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "action": action,
            "decision": action,
            "reason": reason,
            "policy_mode": active_mode,
            "detected_entities_count": len(detected_entities),
            "has_critical_secret": has_critical_secret,
            "calculation_source": "evidence_based_risk_engine",
        }
        return res_dict

    def evaluate_policy(
        self,
        risk_score: float,
        is_risk: bool = False,
        detected_entities: Union[List[str], Dict[str, Any]] = None,
        canonical_class: str = "SAFE",
        **kwargs,
    ) -> Dict[str, Any]:
        """Unified policy evaluation interface returning decision (ALLOW, REDACT, WARN, BLOCK)."""
        if isinstance(detected_entities, dict):
            ent_list = list(detected_entities.keys())
        elif isinstance(detected_entities, list):
            ent_list = detected_entities
        else:
            ent_list = []

        contains_pii = is_risk or (canonical_class != "SAFE")
        res = self.evaluate_decision(
            risk_score=risk_score,
            detected_entities=ent_list,
            contains_regex_pii=contains_pii,
        )
        res["decision"] = res.get("action", "ALLOW")
        return res



# Alias for backward compatibility
AutomatedDecisionGate = PrivacyEvaluator
PolicyEvaluator = PrivacyEvaluator


