"""
AI Trust Chat — Policy Engine
Configurable security policy rules with CRUD operations.
Stored in-memory (session state) — can be persisted to file/DB in production.
File: backend/services/policy_engine.py
"""

from typing import Dict, Any, List, Optional
import datetime
import uuid

# Default security policies
DEFAULT_POLICIES = [
    {
        "id": "policy_001",
        "name": "Mask PII Data",
        "condition": "pii_detected",
        "condition_detail": "Any PII entity detected in user input",
        "action": "MASK",
        "enabled": True,
        "priority": 1,
        "created_at": "2026-08-01 09:00:00",
    },
    {
        "id": "policy_002",
        "name": "Block API Keys",
        "condition": "secret_detected",
        "condition_detail": "API key, access token, or credential detected",
        "action": "BLOCK",
        "enabled": True,
        "priority": 2,
        "created_at": "2026-08-01 09:00:00",
    },
    {
        "id": "policy_003",
        "name": "Block High-Confidence Injection",
        "condition": "injection_confidence_gt_80",
        "condition_detail": "Prompt injection confidence score > 80%",
        "action": "BLOCK",
        "enabled": True,
        "priority": 3,
        "created_at": "2026-08-01 09:00:00",
    },
    {
        "id": "policy_004",
        "name": "Redact Sensitive Output",
        "condition": "sensitive_output_detected",
        "condition_detail": "LLM response contains PII or sensitive data",
        "action": "REDACT",
        "enabled": True,
        "priority": 4,
        "created_at": "2026-08-01 09:00:00",
    },
    {
        "id": "policy_005",
        "name": "Deny Restricted Documents",
        "condition": "doc_classification_restricted",
        "condition_detail": "User requests access to RESTRICTED document without authorization",
        "action": "DENY",
        "enabled": True,
        "priority": 5,
        "created_at": "2026-08-01 09:00:00",
    },
    {
        "id": "policy_006",
        "name": "Warn on Medium Risk",
        "condition": "risk_score_30_to_59",
        "condition_detail": "Risk score between 30-59 (MEDIUM risk)",
        "action": "WARN",
        "enabled": True,
        "priority": 6,
        "created_at": "2026-08-01 09:00:00",
    },
]

# In-memory store
_policies: List[Dict[str, Any]] = list(DEFAULT_POLICIES)


def get_all_policies() -> List[Dict[str, Any]]:
    """Return all policies sorted by priority."""
    return sorted(_policies, key=lambda p: p.get("priority", 99))


def get_enabled_policies() -> List[Dict[str, Any]]:
    """Return only enabled policies."""
    return [p for p in get_all_policies() if p.get("enabled", True)]


def get_policy_by_id(policy_id: str) -> Optional[Dict[str, Any]]:
    for p in _policies:
        if p["id"] == policy_id:
            return p
    return None


def create_policy(
    name: str,
    condition: str,
    condition_detail: str,
    action: str,
    enabled: bool = True,
    priority: int = 99,
) -> Dict[str, Any]:
    """Create a new policy rule."""
    new_policy = {
        "id": f"policy_{uuid.uuid4().hex[:6]}",
        "name": name,
        "condition": condition,
        "condition_detail": condition_detail,
        "action": action,
        "enabled": enabled,
        "priority": priority,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _policies.append(new_policy)
    return new_policy


def update_policy(policy_id: str, **updates) -> Optional[Dict[str, Any]]:
    """Update an existing policy."""
    for p in _policies:
        if p["id"] == policy_id:
            p.update(updates)
            return p
    return None


def delete_policy(policy_id: str) -> bool:
    """Delete a policy by ID."""
    global _policies
    before = len(_policies)
    _policies = [p for p in _policies if p["id"] != policy_id]
    return len(_policies) < before


def toggle_policy(policy_id: str) -> Optional[Dict[str, Any]]:
    """Toggle a policy's enabled state."""
    for p in _policies:
        if p["id"] == policy_id:
            p["enabled"] = not p.get("enabled", True)
            return p
    return None


def evaluate_policies(
    pii_detected: bool,
    secret_detected: bool,
    injection_detected: bool,
    injection_confidence: float,
    output_sensitive: bool,
    risk_score: int,
    doc_classification: str = "PUBLIC",
    user_role: str = "USER",
) -> Dict[str, Any]:
    """
    Evaluate all enabled policies against the current request context.
    Returns the most restrictive action and the triggering policies.
    """
    triggered = []
    action_priority = {"ALLOW": 0, "WARN": 1, "MASK": 2, "REDACT": 3, "DENY": 4, "BLOCK": 5}
    final_action = "ALLOW"

    enabled = get_enabled_policies()

    for policy in enabled:
        cond = policy["condition"]
        triggered_flag = False

        if cond == "pii_detected" and pii_detected:
            triggered_flag = True
        elif cond == "secret_detected" and secret_detected:
            triggered_flag = True
        elif cond == "injection_confidence_gt_80" and injection_detected and injection_confidence >= 0.8:
            triggered_flag = True
        elif cond == "sensitive_output_detected" and output_sensitive:
            triggered_flag = True
        elif cond == "doc_classification_restricted" and doc_classification == "RESTRICTED":
            if user_role not in ("ADMIN", "SECURITY_ADMIN"):
                triggered_flag = True
        elif cond == "risk_score_30_to_59" and 30 <= risk_score <= 59:
            triggered_flag = True

        if triggered_flag:
            triggered.append(policy)
            if action_priority.get(policy["action"], 0) > action_priority.get(final_action, 0):
                final_action = policy["action"]

    return {
        "final_action": final_action,
        "triggered_policies": triggered,
        "policies_evaluated": len(enabled),
    }


def reset_to_defaults():
    """Reset policies to defaults."""
    global _policies
    _policies = list(DEFAULT_POLICIES)
