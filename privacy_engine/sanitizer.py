"""
Authoritative Privacy Sanitizer, Masking & Safe Transformation Engine.
File Location: privacy_engine/sanitizer.py

Pipeline 5 Core Module:
  1. Position-Safe Character Interval Merging & Reconstruction.
  2. Complete Canonical Entity Replacement Taxonomy.
  3. Absolute Idempotency (sanitizing already-sanitized text is a no-op).
  4. Robust Unicode, Multi-byte & Newline Resilience.
  5. Zero Raw Sensitive Value Leakage Guarantee.
"""

import re
from typing import Tuple, List, Dict, Any, Optional

# ── Canonical Replacement Tokens ──────────────────────────────────────────────
# Standardized non-disclosing placeholders
TOKEN_MAP: Dict[str, str] = {
    "EMAIL_ADDRESS": "[EMAIL_REDACTED]",
    "PHONE_NUMBER": "[PHONE_REDACTED]",
    "MEDICAL_PATIENT_RECORD": "[HEALTH_DATA_REDACTED]",
    "PHYSICAL_STREET_ADDRESS": "[ADDRESS_REDACTED]",
    "GOVERNMENT_ID_SSN": "[SSN_REDACTED]",
    "GOVERNMENT_ID_AADHAAR": "[AADHAAR_REDACTED]",
    "GOVERNMENT_ID_PAN": "[PAN_REDACTED]",
    "GOVERNMENT_ID_NINO": "[NINO_REDACTED]",
    "CREDIT_CARD": "[CREDIT_CARD_REDACTED]",
    "CREDIT_CARD_NUMBER": "[CREDIT_CARD_REDACTED]",
    "BANK_ACCOUNT_NUMBER": "[BANK_ACCOUNT_REDACTED]",
    "BANK_ROUTING_ACCOUNT": "[BANK_ACCOUNT_REDACTED]",
    "IBAN_ACCOUNT": "[BANK_ACCOUNT_REDACTED]",
    "CREDENTIAL_PASSWORD": "[PASSWORD_REDACTED]",
    "CREDENTIAL_OTP": "[OTP_REDACTED]",
    "CREDENTIAL_PIN": "[PIN_REDACTED]",
    "CREDENTIAL_AUTH_TOKEN": "[AUTH_TOKEN_REDACTED]",
    "CREDENTIAL_SECRET_KEY": "[SECRET_KEY_REDACTED]",
    "CREDENTIAL_BANK_LOGIN": "[BANK_CREDENTIAL_REDACTED]",
    "AWS_KEY": "[API_KEY_REDACTED]",
    "AWS_ACCESS_KEY": "[API_KEY_REDACTED]",
    "GOOGLE_CLOUD_KEY": "[API_KEY_REDACTED]",
    "GOOGLE_CLOUD_API_KEY": "[API_KEY_REDACTED]",
    "SENDGRID_KEY": "[API_KEY_REDACTED]",
    "SENDGRID_API_KEY": "[API_KEY_REDACTED]",
    "SLACK_TOKEN": "[AUTH_SECRET_REDACTED]",
    "SLACK_BOT_TOKEN": "[AUTH_SECRET_REDACTED]",
    "GITHUB_TOKEN": "[API_KEY_REDACTED]",
    "OPENAI_API_KEY": "[API_KEY_REDACTED]",
    "GENERIC_SECRET_KEY": "[API_KEY_REDACTED]",
    "GENERIC_API_SECRET": "[API_KEY_REDACTED]",
    "JWT_TOKEN": "[AUTH_SECRET_REDACTED]",
    "BEARER_TOKEN": "[AUTH_SECRET_REDACTED]",
    "PRIVATE_KEY_BLOCK": "[AUTH_SECRET_REDACTED]",
    "DATABASE_CONNECTION_STRING": "[DATABASE_CREDENTIALS_REDACTED]",
    "PASSPORT_NUMBER": "[PASSPORT_REDACTED]",
    "IP_ADDRESS": "[IP_REDACTED]",
}

# ── Pattern Taxonomy (Entity Type, Regex Pattern, Severity, Default Placeholder)
PII_PATTERNS: List[Tuple[str, str, str, str]] = [
    (
        "EMAIL_ADDRESS",
        r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b',
        "MEDIUM",
        "[EMAIL_REDACTED]",
    ),
    (
        "PHONE_NUMBER",
        r'(?i)(?:\b(?:my|the|our|contact)?\s*(?:phone|mobile|cell|tel|telephone|whatsapp)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?((?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}|\+?1[\s.-]?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10})["\']?)',
        "MEDIUM",
        "[PHONE_REDACTED]",
    ),
    (
        "PHONE_NUMBER",
        r'(?<!\d)(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)|\b(?:\+91[\s-]?)?[6-9]\d{4}[-\s]?\d{5}\b|\b(?:\+91[\s-]?)?[6-9]\d{9}\b|\+44[\s.-]?(?:\d[\s.-]?){9,11}\b',
        "MEDIUM",
        "[PHONE_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_AADHAAR",
        r'(?i)(?:\b(?:my|the|our|user|citizen|customer)?\s*(?:aadhaar|aadhar|uidai|adhaar|adhar)\s*(?:card)?\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?(\d{4}[-\s]?\d{4}[-\s]?(?:\d{4}|\d{2,4})|\d{10,12})["\']?)',
        "HIGH",
        "[AADHAAR_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_AADHAAR",
        r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b',
        "HIGH",
        "[AADHAAR_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_PAN",
        r'(?i)(?:\b(?:my|the|our)?\s*(?:pan|pan\s*card)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?([A-Za-z]{5}\d{4}[A-Za-z])["\']?)',
        "HIGH",
        "[PAN_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_PAN",
        r'\b[A-Z]{5}\d{4}[A-Z]{1}\b',
        "HIGH",
        "[PAN_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_SSN",
        r'\b\d{3}-\d{2}-\d{4}\b',
        "HIGH",
        "[SSN_REDACTED]",
    ),
    (
        "GOVERNMENT_ID_NINO",
        r'\b[A-CEGHJ-PR-TW-Z]{2}\s*\d{6}\s*[A-D]\b',
        "HIGH",
        "[NINO_REDACTED]",
    ),
    (
        "PASSPORT_NUMBER",
        r'(?i)(?:\b(?:my|the|our)?\s*(?:passport|ppt)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?([A-Za-z][0-9]{7,8})["\']?)',
        "HIGH",
        "[PASSPORT_REDACTED]",
    ),
    (
        "CREDIT_CARD",
        r'\b(?:\d{4}[ -]?){3}\d{4}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',
        "CRITICAL",
        "[CREDIT_CARD_REDACTED]",
    ),
    (
        "BANK_ACCOUNT_NUMBER",
        r'\b(?:(?:bank\s+)?account\s*(?:num|no|number)?|bank\s+acc|beneficiary\s+acc(?:ount)?|transfer\s+(?:money\s+|funds\s+)?to\s+(?:bank\s+)?account|payment\s+to\s+(?:bank\s+)?account|IFSC\s+[A-Z]{4}0[A-Z0-9]{6}\s+(?:and\s+)?account)\s*(?:is|to|:|=)?\s*(\d{9,18})\b',
        "HIGH",
        "[BANK_ACCOUNT_REDACTED]",
    ),
    (
        "BANK_ROUTING_ACCOUNT",
        r'(?:routing\s+(?:number\s+)?\d{9}\s+and\s+account\s+(?:number\s+)?\d{8,17}|account\s+(?:number\s+)?\d{8,17}\s+and\s+routing\s+(?:number\s+)?\d{9}|routing\s+(?:number\s+)?021\d{6})',
        "HIGH",
        "[BANK_ACCOUNT_REDACTED]",
    ),
    (
        "IBAN_ACCOUNT",
        r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b',
        "HIGH",
        "[BANK_ACCOUNT_REDACTED]",
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:database|db|server|app|application|login|admin|account|root|user|api|client)?\s*(?:password|passwd|pwd))\s*[:=]\s*[\'"]?([^\s\'",;]{3,})[\'"]?|(?:\b(?:my|the|our|admin|user|root|account|db|database|server|app|application|login)?\s*(?:(?:database|db|server|app|application|login|admin|account|root|user)\s+)?(?:password|passwd|pwd)\s+is\s+[\'"]?([^\s\'",;]{3,})[\'"]?)|(?:\b(?:my|the|our)?\s*secret\s+(?:i\s+use\s+to\s+(?:log\s*in|access)|for\s+(?:logging\s*in|accessing|my\s+account))\s*(?:to\s+(?:my|the|our)\s+account)?\s*[:=is\s]+[\'"]?([^\s\'",;]{3,})[\'"]?)|(?:\b(?:deploy\s+credentials|server\s+credentials|login\s+credentials|account\s+credentials)\s*(?:for\s+[^:]+)?\s*[:=is\s]+[\'"]?([^\s\'",;]{3,})[\'"]?)',
        "CRITICAL",
        "[PASSWORD_REDACTED]",
    ),
    # ── OTP / One-Time Password Detection ─────────────────────────────────────
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:my|the|our|your)?\s*(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s+(?:is|was|=|:)\s*[\'"]?(\d{4,8})[\'"]?)',
        "CRITICAL",
        "[OTP_REDACTED]",
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s*(?:code|number|num|no)?\s*[:=]\s*[\'"]?(\d{4,8})[\'"]?)',
        "CRITICAL",
        "[OTP_REDACTED]",
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:my|the|our|your)?\s*(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s+[\'"]?(\d{4,8})[\'"]?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "[OTP_REDACTED]",
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:verification|2fa|two[- ]?factor|mfa|authentication)\s+(?:code|otp|pin)\s+(?:is|was|=|:)\s*[\'"]?(\d{4,8})[\'"]?)',
        "CRITICAL",
        "[OTP_REDACTED]",
    ),
    # ── PIN Detection ─────────────────────────────────────────────────────────
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:my|the|our|your)?\s*(?:atm|debit|credit|bank|card|transaction|upi|mobile)?\s*(?:pin|pin\s*(?:number|num|no|code))\s*(?:is|was|=|:)\s*[\'"]?(\d{4,6})[\'"]?)',
        "CRITICAL",
        "[PIN_REDACTED]",
    ),
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:atm|debit|credit|bank|card|transaction|upi|mobile)\s+pin\s*[:=]\s*[\'"]?(\d{4,6})[\'"]?)',
        "CRITICAL",
        "[PIN_REDACTED]",
    ),
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:my|the|our|your)?\s*(?:atm|debit|credit|bank|card|transaction|upi|mobile)?\s*(?:pin|pin\s*(?:number|num|no|code))\s+[\'"]?(\d{4,6})[\'"]?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "[PIN_REDACTED]",
    ),
    # ── Contextual Number-Only Password Detection ─────────────────────────────
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:my|the|our|admin|user|root|account)?\s*(?:password|passwd|pwd)\s+(?:is\s+)?[\'"]?(\d{4,})[\'"]?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "[PASSWORD_REDACTED]",
    ),
    # ── Auth Token / Session Token Disclosure ─────────────────────────────────
    (
        "CREDENTIAL_AUTH_TOKEN",
        r'(?:\b(?:my|the|our)?\s*(?:auth(?:entication)?|session|access|refresh)\s*(?:token|key)\s+(?:is|was|=|:)\s*[\'"]?([^\s\'",;]{8,})[\'"]?)',
        "CRITICAL",
        "[AUTH_TOKEN_REDACTED]",
    ),
    # ── Secret Key Disclosure ─────────────────────────────────────────────────
    (
        "CREDENTIAL_SECRET_KEY",
        r'(?:\b(?:my|the|our)?\s*(?:secret|private|signing|encryption)\s*(?:key|code|phrase)\s+(?:is|was|=|:)\s*[\'"]?([^\s\'",;]{6,})[\'"]?)',
        "CRITICAL",
        "[SECRET_KEY_REDACTED]",
    ),
    # ── Bank / Net Banking / UPI Credential Disclosure ────────────────────────
    (
        "CREDENTIAL_BANK_LOGIN",
        r'(?:\b(?:net\s*banking|mobile\s*banking|internet\s*banking|online\s*banking|bank(?:ing)?)\s+(?:password|passwd|pwd|pin|login)\s+(?:is|was|=|:)\s*[\'"]?([^\s\'",;]{3,})[\'"]?)',
        "CRITICAL",
        "[BANK_CREDENTIAL_REDACTED]",
    ),
    (
        "CREDENTIAL_BANK_LOGIN",
        r'(?:\b(?:upi)\s+(?:pin|password|mpin)\s*(?:is|was|=|:)\s*[\'"]?(\d{4,6})[\'"]?)',
        "CRITICAL",
        "[BANK_CREDENTIAL_REDACTED]",
    ),
    (
        "AWS_KEY",
        r'\bAKIA[0-9A-Z]{16}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "GOOGLE_CLOUD_KEY",
        r'\bAIzaSy[0-9A-Za-z_-]{33}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "SENDGRID_KEY",
        r'\bSG\.[0-9a-zA-Z._-]{24,70}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "SLACK_TOKEN",
        r'\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,34}\b',
        "CRITICAL",
        "[AUTH_SECRET_REDACTED]",
    ),
    (
        "GITHUB_TOKEN",
        r'\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[0-9a-zA-Z_]{30,60}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "OPENAI_API_KEY",
        r'\bsk-(?:proj-)?[a-zA-Z0-9_-]{16,64}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "GENERIC_SECRET_KEY",
        r'\bsk_(?:live|test)_[0-9a-zA-Z]{16,}\b',
        "CRITICAL",
        "[API_KEY_REDACTED]",
    ),
    (
        "JWT_TOKEN",
        r'\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b',
        "CRITICAL",
        "[AUTH_SECRET_REDACTED]",
    ),
    (
        "BEARER_TOKEN",
        r'[Bb]earer\s+[A-Za-z0-9\-_=.]{20,}',
        "CRITICAL",
        "[AUTH_SECRET_REDACTED]",
    ),
    (
        "PRIVATE_KEY_BLOCK",
        r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----|-----BEGIN [A-Z ]*PRIVATE KEY-----',
        "CRITICAL",
        "[AUTH_SECRET_REDACTED]",
    ),
    (
        "DATABASE_CONNECTION_STRING",
        r'(?:postgres|postgresql|mysql|mongodb|redis|mssql|oracle)://[^\s:]+:[^\s@]+@[^\s/:]+(?::\d+)?(?:/[^\s]*)?',
        "CRITICAL",
        "[DATABASE_CREDENTIALS_REDACTED]",
    ),
    (
        "MEDICAL_PATIENT_RECORD",
        r'\bMRN-\d{4,8}\b|\bpatient\s+(?:intake|record|diagnostic|history|report|summary)[:\s]|diagnosed\s+with\s+[a-zA-Z0-9\s]+and\s+prescribed|prescribed\s+(?:daily\s+)?[a-zA-Z0-9\s]+(?:mg|g|mcg|tablets?)',
        "HIGH",
        "[HEALTH_DATA_REDACTED]",
    ),
    (
        "PHYSICAL_STREET_ADDRESS",
        r'\b\d{1,5}\s+[A-Za-z0-9\s.,]+(?:Terrace|Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)[A-Za-z0-9\s,]+(?:[A-Z]{2}\s+\d{5}|\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b)|10\s+Downing\s+Street[A-Za-z0-9\s,]+',
        "MEDIUM",
        "[ADDRESS_REDACTED]",
    ),
    (
        "PASSPORT_NUMBER",
        r'\b[A-Z]{1,2}[0-9]{6,9}\b|\bPassport\s+number\s+[0-9]{7,10}\b',
        "HIGH",
        "[PASSPORT_REDACTED]",
    ),
    (
        "IP_ADDRESS",
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "LOW",
        "[IP_REDACTED]",
    ),
]

# Existing recognized redaction placeholders to ignore during re-scanning (Idempotency)
EXISTING_REDACTION_PATTERN = re.compile(
    r'\[(?:EMAIL|PHONE|AADHAAR|PAN|SSN|NINO|CREDIT_CARD|BANK_ACCOUNT|PASSWORD|API_KEY|AUTH_SECRET|HEALTH_DATA|ADDRESS|PASSPORT|IP|DATABASE_CREDENTIALS|GCP_KEY|AWS_KEY|SENDGRID_KEY|SLACK_TOKEN|GITHUB_TOKEN|JWT|PRIVATE_KEY|IBAN|HEALTH_RECORD|PAYMENT_CARD|BLOCKED_ADVERSARIAL_SEQUENCE|OTP|PIN|AUTH_TOKEN|SECRET_KEY|BANK_CREDENTIAL)_REDACTED\]|\[EMAIL REDACTED\]|\[PHONE REDACTED\]|\[NAME REDACTED\]|\[AADHAAR REDACTED\]|\[PAN REDACTED\]|\[SSN REDACTED\]|\[NINO REDACTED\]|\[PASSPORT REDACTED\]|\[LICENSE REDACTED\]|\[VOTER ID REDACTED\]|\[PAYMENT CARD REDACTED\]|\[BANK ACCOUNT REDACTED\]|\[IBAN REDACTED\]|\[UPI ID REDACTED\]|\[PASSWORD REDACTED\]|\[OTP REDACTED\]|\[PIN REDACTED\]|\[AUTH TOKEN REDACTED\]|\[SECRET KEY REDACTED\]|\[BANK CREDENTIAL REDACTED\]|\[AWS KEY REDACTED\]|\[GITHUB TOKEN REDACTED\]|\[API KEY REDACTED\]|\[GCP KEY REDACTED\]|\[SLACK TOKEN REDACTED\]|\[JWT TOKEN REDACTED\]|\[BEARER TOKEN REDACTED\]|\[PRIVATE KEY REDACTED\]|\[DATABASE CREDENTIALS REDACTED\]|\[HEALTH RECORD REDACTED\]|\[ADDRESS REDACTED\]|\[IP ADDRESS REDACTED\]|\[BLOCKED_ADVERSARIAL_SEQUENCE\]',
    re.IGNORECASE
)


class PrivacySanitizer:
    """
    Authoritative Privacy Sanitizer for Pipeline 5.
    
    Transforms sensitive textual content into standardized safe placeholders
    using deterministic, position-safe character interval merging.
    """

    def __init__(self):
        self.patterns = PII_PATTERNS

    def sanitize_text(self, text: str, mode: str = "REDACT") -> Dict[str, Any]:
        """
        Authoritative text sanitization.
        
        Args:
            text: Input string to sanitize.
            mode: Sanitization strategy ('REDACT', 'MASK', 'SYNTHETIC').
            
        Returns:
            Structured SanitizationResult dictionary with zero raw sensitive value leakage.
        """
        if not text:
            return {
                "sanitized_text": "",
                "entities_removed": [],
                "sanitization_applied": False,
                "source": "authoritative_sanitizer"
            }

        # 1. Find all pre-existing redaction placeholders to protect them from duplicate modification
        protected_intervals: List[Tuple[int, int]] = []
        for m in EXISTING_REDACTION_PATTERN.finditer(text):
            protected_intervals.append((m.start(), m.end()))

        # 2. Collect raw match intervals across all pattern definitions
        raw_intervals: List[Dict[str, Any]] = []

        for pii_type, pattern, severity, default_tag in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # If pattern has capturing groups (e.g. bank account value extraction), use the target group
                if match.lastindex and match.lastindex >= 1 and match.group(1):
                    start, end = match.start(1), match.end(1)
                    val = match.group(1)
                else:
                    start, end = match.start(), match.end()
                    val = match.group(0)

                # Skip if match falls entirely within an existing redaction placeholder (Idempotency)
                if any(p_start <= start and end <= p_end for p_start, p_end in protected_intervals):
                    continue

                placeholder = self._resolve_replacement(val, pii_type, default_tag, mode)

                raw_intervals.append({
                    "start": start,
                    "end": end,
                    "entity_type": pii_type,
                    "severity": severity,
                    "placeholder": placeholder,
                    "val_len": len(val),
                })

        if not raw_intervals:
            return {
                "sanitized_text": text,
                "entities_removed": [],
                "sanitization_applied": False,
                "source": "authoritative_sanitizer"
            }

        # 3. Position-Safe Interval Merging (handle overlapping or duplicate spans)
        # Sort intervals by start ascending, then length descending
        raw_intervals.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))

        merged_intervals: List[Dict[str, Any]] = []
        for interval in raw_intervals:
            if not merged_intervals:
                merged_intervals.append(interval)
                continue

            last = merged_intervals[-1]
            # Check for overlap
            if interval["start"] < last["end"]:
                # If new interval extends past last, merge boundaries
                if interval["end"] > last["end"]:
                    last["end"] = interval["end"]
                    # Retain higher severity entity type if applicable
                    if interval.get("severity") == "CRITICAL":
                        last["entity_type"] = interval["entity_type"]
                        last["placeholder"] = interval["placeholder"]
                # Else: completely contained, safely ignore inner duplicate
            else:
                merged_intervals.append(interval)

        # 4. Reverse String Reconstruction (right-to-left slice replacement)
        # Slicing from end to beginning preserves character indices for earlier spans
        sanitized_text = text
        entities_removed: List[Dict[str, Any]] = []

        for interval in sorted(merged_intervals, key=lambda x: x["start"], reverse=True):
            s = interval["start"]
            e = interval["end"]
            rep = interval["placeholder"]
            sanitized_text = sanitized_text[:s] + rep + sanitized_text[e:]

            # Record removed entity (EXCLUDING raw sensitive value)
            entities_removed.append({
                "entity_type": interval["entity_type"],
                "span": [s, e],
                "placeholder": rep,
                "character_length": e - s,
            })

        # Reverse entities list so it appears in chronological text order
        entities_removed.reverse()

        return {
            "sanitized_text": sanitized_text,
            "entities_removed": entities_removed,
            "detected_entities": [
                {
                    "entity_type": ent["entity_type"],
                    "span": (ent["span"][0], ent["span"][1]),
                    "location": f"Span({ent['span'][0]}, {ent['span'][1]})",
                }
                for ent in entities_removed
            ],
            "sanitization_applied": True,
            "source": "authoritative_sanitizer"
        }

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Backward-compatible tuple return: (sanitized_text, detected_entities)
        """
        res = self.sanitize_text(text, mode="REDACT")
        return res["sanitized_text"], res.get("detected_entities", [])

    def _resolve_replacement(self, val: str, pii_type: str, default_tag: str, mode: str) -> str:
        """Determines replacement tag based on mode (REDACT, MASK, SYNTHETIC)."""
        mode_upper = mode.upper() if mode else "REDACT"

        if mode_upper == "MASK":
            if pii_type == "EMAIL_ADDRESS" and "@" in val:
                user, domain = val.split("@", 1)
                dom_parts = domain.split(".")
                return f"{user[:1]}***@{dom_parts[0][:1]}***.{dom_parts[-1]}"
            elif pii_type == "PHONE_NUMBER":
                return f"***-***-{val[-4:]}"
            elif pii_type in ("CREDIT_CARD", "CREDIT_CARD_NUMBER"):
                return f"••••-••••-••••-{val[-4:]}"
            elif pii_type == "BANK_ACCOUNT_NUMBER":
                return f"••••••••{val[-4:]}"
            elif pii_type == "GOVERNMENT_ID_AADHAAR":
                return f"••••-••••-{val[-4:]}"
            elif pii_type == "CREDENTIAL_OTP":
                return f"••••{val[-2:]}" if len(val) >= 2 else "••••••"
            elif pii_type == "CREDENTIAL_PIN":
                return f"••{val[-2:]}" if len(val) >= 2 else "••••"
            elif pii_type in ("CREDENTIAL_PASSWORD", "CREDENTIAL_BANK_LOGIN"):
                return f"{val[:1]}{'•' * (len(val) - 2)}{val[-1:]}" if len(val) >= 3 else "••••••"
            elif pii_type in ("CREDENTIAL_AUTH_TOKEN", "CREDENTIAL_SECRET_KEY"):
                return f"{val[:3]}{'•' * 8}{val[-3:]}" if len(val) >= 8 else "••••••••"
            return TOKEN_MAP.get(pii_type, default_tag)

        elif mode_upper == "SYNTHETIC":
            synthetic_map = {
                "EMAIL_ADDRESS": "user_anon@privacy-safe.org",
                "PHONE_NUMBER": "+1-555-0199",
                "CREDIT_CARD": "4000-0000-0000-0000",
                "CREDIT_CARD_NUMBER": "4000-0000-0000-0000",
                "GOVERNMENT_ID_SSN": "000-00-0000",
                "GOVERNMENT_ID_AADHAAR": "0000 0000 0000",
                "BANK_ACCOUNT_NUMBER": "000000000000",
                "IP_ADDRESS": "127.0.0.1",
                "CREDENTIAL_OTP": "000000",
                "CREDENTIAL_PIN": "0000",
            }
            return synthetic_map.get(pii_type, TOKEN_MAP.get(pii_type, default_tag))

        # Default: Canonical REDACT tag
        return TOKEN_MAP.get(pii_type, default_tag)


# Singleton Instance & Aliases for backward compatibility
_GLOBAL_SANITIZER = PrivacySanitizer()


def get_sanitizer() -> PrivacySanitizer:
    return _GLOBAL_SANITIZER


PIISanitizer = PrivacySanitizer
Sanitizer = PrivacySanitizer
