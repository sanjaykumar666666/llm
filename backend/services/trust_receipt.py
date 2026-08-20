"""
AI Trust Chat — Trust Receipt Generator
Creates a privacy-preserving security receipt for every AI request.
Receipts are stored in-session and in audit logs. Raw prompts are NEVER stored.
File: backend/services/trust_receipt.py
"""

import uuid
import datetime
from typing import Dict, Any, List, Optional

# In-memory receipt store (session-scoped in production, use DB)
_receipt_store: List[Dict[str, Any]] = []


def generate_receipt(
    user_id: str,
    model_selected: str,
    pii_detected: bool,
    pii_entities: List[str],
    injection_detected: bool,
    risk_score: int,
    risk_level: str,
    policy_action: str,
    pii_action: str,
    output_action: str,
    output_sensitive: bool,
    request_id: Optional[str] = None,
    doc_accessed: Optional[str] = None,
    doc_classification: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a structured AI Trust Receipt for a single AI request.
    Raw prompt text is NEVER stored in the receipt.
    """
    receipt_id = request_id or f"ATC-{abs(uuid.uuid4().int) % 1000000:06d}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    receipt = {
        "receipt_id": receipt_id,
        "timestamp": timestamp,
        "user": user_id,
        "model": model_selected,
        "security": {
            "pii_detected": pii_detected,
            "pii_entities": pii_entities,
            "prompt_injection": injection_detected,
            "risk_score": risk_score,
            "risk_level": risk_level,
        },
        "policy": {
            "pii_action": pii_action,          # ALLOW / MASK / BLOCK
            "overall_action": policy_action,    # ALLOW / BLOCK / SANITIZE
        },
        "rag": {
            "document_accessed": doc_accessed,
            "classification": doc_classification,
        } if doc_accessed else None,
        "output": {
            "action": output_action,            # ALLOW / REDACT / BLOCK
            "sensitive_detected": output_sensitive,
        },
        "privacy": {
            "raw_prompt_retained": False,       # ALWAYS False — never store raw prompts
            "pii_values_logged": False,         # ALWAYS False — log types, never values
        },
    }

    # Store in memory
    _receipt_store.append(receipt)

    # Keep only last 500 receipts
    if len(_receipt_store) > 500:
        _receipt_store.pop(0)

    return receipt


def get_all_receipts() -> List[Dict[str, Any]]:
    """Return all stored receipts (newest first)."""
    return list(reversed(_receipt_store))


def get_receipt_by_id(receipt_id: str) -> Optional[Dict[str, Any]]:
    """Find a receipt by its ID."""
    for r in _receipt_store:
        if r["receipt_id"] == receipt_id:
            return r
    return None


def clear_receipts():
    """Clear all receipts (admin only)."""
    _receipt_store.clear()


def format_receipt_text(receipt: Dict[str, Any]) -> str:
    """Format a receipt as a human-readable text block for display."""
    sec = receipt["security"]
    pol = receipt["policy"]
    out = receipt["output"]
    priv = receipt["privacy"]

    pii_str = "YES — " + ", ".join(sec["pii_entities"]) if sec["pii_detected"] else "NO"
    inj_str = "YES ⚠️" if sec["prompt_injection"] else "NO"

    rag_section = ""
    if receipt.get("rag"):
        rag = receipt["rag"]
        rag_section = f"""
Document:     {rag.get('document_accessed', 'N/A')}
Classification: {rag.get('classification', 'N/A')}"""

    return f"""╔══════════════════════════════════════╗
║        AI TRUST RECEIPT              ║
╚══════════════════════════════════════╝

Request ID:   {receipt['receipt_id']}
Timestamp:    {receipt['timestamp']}
User:         {receipt['user']}
Model:        {receipt['model']}

── SECURITY ────────────────────────────
PII Detected:        {pii_str}
Prompt Injection:    {inj_str}
Risk Score:          {sec['risk_score']}/100 ({sec['risk_level']})

── POLICY ──────────────────────────────
PII Action:          {pol['pii_action']}
Overall Action:      {pol['overall_action']}
{rag_section}
── OUTPUT ──────────────────────────────
Output Scan:         {out['action']}
Sensitive Output:    {'YES' if out['sensitive_detected'] else 'NO'}

── PRIVACY ─────────────────────────────
Raw Prompt Retained: {'YES' if priv['raw_prompt_retained'] else 'NO'}
PII Values Logged:   {'YES' if priv['pii_values_logged'] else 'NO'}
"""
