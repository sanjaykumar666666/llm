"""
AI Trust Chat — Security Event Logger
Logs security events to an in-memory timeline (and audit log file).
File: backend/services/security_events.py
"""

import datetime
import uuid
from typing import Dict, Any, List, Optional

# In-memory event store
_events: List[Dict[str, Any]] = []

# Seed with realistic demo events
_events = [
    {
        "id": "evt_001",
        "timestamp": "2026-08-19 10:21:05",
        "type": "PII_DETECTED",
        "severity": "HIGH",
        "message": "Phone number detected and masked in user prompt",
        "user": "Employee-247",
        "model": "Gemini 2.0 Flash",
        "action_taken": "MASK",
        "risk_score": 65,
    },
    {
        "id": "evt_002",
        "timestamp": "2026-08-19 10:22:13",
        "type": "INJECTION_BLOCKED",
        "severity": "CRITICAL",
        "message": "Prompt injection attempt blocked — 'ignore previous instructions' pattern",
        "user": "Employee-103",
        "model": "N/A (Blocked)",
        "action_taken": "BLOCK",
        "risk_score": 94,
    },
    {
        "id": "evt_003",
        "timestamp": "2026-08-19 10:25:44",
        "type": "DOC_ACCESS_DENIED",
        "severity": "HIGH",
        "message": "Access denied to RESTRICTED document — user lacks HR role",
        "user": "Employee-312",
        "model": "N/A (Denied)",
        "action_taken": "DENY",
        "risk_score": 80,
    },
    {
        "id": "evt_004",
        "timestamp": "2026-08-19 10:29:02",
        "type": "SAFE_REQUEST",
        "severity": "LOW",
        "message": "Safe query processed — 'Explain machine learning'",
        "user": "Employee-247",
        "model": "Gemini 2.0 Flash",
        "action_taken": "ALLOW",
        "risk_score": 5,
    },
    {
        "id": "evt_005",
        "timestamp": "2026-08-19 10:31:18",
        "type": "OUTPUT_REDACTED",
        "severity": "MEDIUM",
        "message": "Sensitive data redacted from LLM response — email address found",
        "user": "Employee-089",
        "model": "Gemini 2.5 Flash",
        "action_taken": "REDACT",
        "risk_score": 45,
    },
]

EVENT_COLORS = {
    "LOW":      "#10B981",
    "MEDIUM":   "#F59E0B",
    "HIGH":     "#EF4444",
    "CRITICAL": "#DC2626",
}

EVENT_ICONS = {
    "PII_DETECTED":      "🔍",
    "INJECTION_BLOCKED": "🚫",
    "DOC_ACCESS_DENIED": "🔒",
    "DOC_ACCESS_GRANTED":"📄",
    "SAFE_REQUEST":      "✅",
    "OUTPUT_REDACTED":   "✂️",
    "SECRET_BLOCKED":    "🔑",
    "POLICY_TRIGGERED":  "⚖️",
    "MASK_APPLIED":      "🛡️",
}


def log_event(
    event_type: str,
    severity: str,
    message: str,
    user: str = "Anonymous",
    model: str = "Unknown",
    action_taken: str = "ALLOW",
    risk_score: int = 0,
) -> Dict[str, Any]:
    """Log a new security event."""
    event = {
        "id": f"evt_{uuid.uuid4().hex[:6]}",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "severity": severity,
        "message": message,
        "user": user,
        "model": model,
        "action_taken": action_taken,
        "risk_score": risk_score,
    }
    _events.append(event)

    # Keep last 1000 events
    if len(_events) > 1000:
        _events.pop(0)

    return event


def get_all_events(
    filter_type: Optional[str] = None,
    filter_severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return events with optional filtering (newest first)."""
    results = list(reversed(_events))

    if filter_type and filter_type != "ALL":
        results = [e for e in results if e["type"] == filter_type]

    if filter_severity and filter_severity != "ALL":
        results = [e for e in results if e["severity"] == filter_severity]

    if search:
        search_lower = search.lower()
        results = [e for e in results if search_lower in e["message"].lower()
                   or search_lower in e["user"].lower()]

    return results[:limit]


def get_event_summary() -> Dict[str, Any]:
    """Return summary statistics for the dashboard."""
    total = len(_events)
    by_severity = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    by_action = {}
    by_type = {}

    for e in _events:
        sev = e.get("severity", "LOW")
        by_severity[sev] = by_severity.get(sev, 0) + 1

        act = e.get("action_taken", "ALLOW")
        by_action[act] = by_action.get(act, 0) + 1

        etype = e.get("type", "UNKNOWN")
        by_type[etype] = by_type.get(etype, 0) + 1

    return {
        "total_events": total,
        "by_severity": by_severity,
        "by_action": by_action,
        "by_type": by_type,
        "blocked": by_action.get("BLOCK", 0) + by_action.get("DENY", 0),
        "high_risk": by_severity.get("HIGH", 0) + by_severity.get("CRITICAL", 0),
    }


def get_event_color(severity: str) -> str:
    return EVENT_COLORS.get(severity, "#94A3B8")


def get_event_icon(event_type: str) -> str:
    return EVENT_ICONS.get(event_type, "📋")
