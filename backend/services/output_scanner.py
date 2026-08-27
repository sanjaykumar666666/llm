"""
AI Trust Chat — Output Security Scanner
Scans LLM-generated responses for PII, secrets, and sensitive content
before returning to the user.
File: backend/services/output_scanner.py
"""

import re
from typing import Dict, Any, List, Tuple


# Output scan patterns (same base as input, but slightly looser for detection)
OUTPUT_SCAN_PATTERNS = [
    ("EMAIL_ADDRESS",    r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', "[EMAIL_REDACTED]"),
    ("PHONE_NUMBER",     r'\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b|\b\d{10}\b', "[PHONE_REDACTED]"),
    ("SSN",              r'\b\d{3}-\d{2}-\d{4}\b', "[SSN_REDACTED]"),
    ("CREDIT_CARD",      r'\b(?:\d[ -]*?){13,16}\b', "[CREDIT_CARD_REDACTED]"),
    ("AWS_KEY",          r'\bAKIA[0-9A-Z]{16}\b', "[AWS_KEY_REDACTED]"),
    ("GITHUB_TOKEN",     r'\b(ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}\b', "[GITHUB_TOKEN_REDACTED]"),
    ("OPENAI_KEY",       r'\bsk-[a-zA-Z0-9]{32,48}\b', "[OPENAI_KEY_REDACTED]"),
    ("GENERIC_API_KEY",  r'\bsk_live_[0-9a-zA-Z]{24}\b', "[API_KEY_REDACTED]"),
    ("JWT_TOKEN",        r'\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b', "[JWT_REDACTED]"),
    ("PRIVATE_KEY",      r'-----BEGIN [A-Z ]*PRIVATE KEY-----', "[PRIVATE_KEY_REDACTED]"),
    ("AADHAAR",          r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', "[AADHAAR_REDACTED]"),
    ("IP_ADDRESS",       r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b', "[IP_REDACTED]"),
    # Credential patterns for OTP, PIN, bank, auth tokens
    ("OTP_CODE",         r'(?:\b(?:otp|one[- ]?time[- ]?(?:password|code|pin)|verification\s+code|2fa\s+code)\s*(?:is|was|=|:)?\s*["\']?\d{4,8}["\']?)', "[OTP_REDACTED]"),
    ("PIN_CODE",         r'(?:\b(?:atm|debit|credit|bank|card|upi|mobile)?\s*pin\s*(?:is|was|=|:)?\s*["\']?\d{4,6}["\']?)', "[PIN_REDACTED]"),
    ("BANK_CREDENTIAL",  r'(?:\b(?:net\s*banking|mobile\s*banking|internet\s*banking|online\s*banking)\s+(?:password|pwd|pin|login)\s+(?:is|was|=|:)\s*["\']?[^\s"\',;]{3,}["\']?)', "[BANK_CREDENTIAL_REDACTED]"),
    ("UPI_PIN",          r'(?:\b(?:upi)\s+(?:pin|password|mpin)\s*(?:is|was|=|:)\s*["\']?\d{4,6}["\']?)', "[UPI_PIN_REDACTED]"),
    ("AUTH_TOKEN",       r'(?:\b(?:auth(?:entication)?|session|access|refresh)\s*(?:token|key)\s+(?:is|was|=|:)\s*["\']?[^\s"\',;]{8,}["\']?)', "[AUTH_TOKEN_REDACTED]"),
    ("BEARER_TOKEN",     r'[Bb]earer\s+[A-Za-z0-9\-_=.]{20,}', "[BEARER_TOKEN_REDACTED]"),
    ("DB_CONNECTION",    r'(?:postgres|postgresql|mysql|mongodb|redis|mssql|oracle)://[^\s:]+:[^\s@]+@[^\s/:]+(?::\d+)?(?:/[^\s]*)?', "[DB_CREDENTIALS_REDACTED]"),
]


def scan_output(response_text: str) -> Dict[str, Any]:
    """
    Scan LLM output for sensitive content.

    Returns:
        action: ALLOW | REDACT | BLOCK
        redacted_text: cleaned output (if REDACT)
        detected_entities: list of found entities
        is_sensitive: bool
    """
    if not response_text or not response_text.strip():
        return {
            "action": "ALLOW",
            "redacted_text": response_text,
            "detected_entities": [],
            "is_sensitive": False,
        }

    detected: List[Dict[str, Any]] = []
    redacted_text = response_text

    for entity_type, pattern, placeholder in OUTPUT_SCAN_PATTERNS:
        matches = list(re.finditer(pattern, redacted_text, re.IGNORECASE))
        for match in matches:
            val = match.group(0)
            detected.append({
                "entity_type": entity_type,
                "original_value": val[:4] + "***",  # Show preview, not full value
                "placeholder": placeholder,
            })
            redacted_text = redacted_text.replace(val, placeholder, 1)

    # Determine action
    if not detected:
        action = "ALLOW"
        is_sensitive = False
    else:
        action = "REDACT"
        is_sensitive = True

    return {
        "action": action,
        "redacted_text": redacted_text,
        "original_text": response_text,
        "detected_entities": detected,
        "is_sensitive": is_sensitive,
        "entities_count": len(detected),
    }
