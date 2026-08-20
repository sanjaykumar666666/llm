"""
Privacy Sanitizer, Masking & Anonymization Engine.
File Location: privacy_engine/sanitizer.py
"""

import re
from typing import Tuple, List, Dict, Any

PII_PATTERNS = [
    ("EMAIL_ADDRESS", r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', "[EMAIL_REDACTED]"),
    ("PHONE_NUMBER", r'(?<!\d)(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)|\b(?:\+91[\s-]?)?[6-9]\d{9}\b|\+44[\s.-]?(?:\d[\s.-]?){9,11}\b', "[PHONE_REDACTED]"),
    ("MEDICAL_PATIENT_RECORD", r'\bMRN-\d{4,8}\b|\bpatient\s+(?:intake|record|diagnostic|history|report|summary)[:\s]|diagnosed\s+with\s+[a-zA-Z0-9\s]+and\s+prescribed|prescribed\s+(?:daily\s+)?[a-zA-Z0-9\s]+(?:mg|g|mcg|tablets?)', "[HEALTH_DATA_REDACTED]"),
    ("PHYSICAL_STREET_ADDRESS", r'\b\d{1,5}\s+[A-Za-z0-9\s.,]+(?:Terrace|Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)[A-Za-z0-9\s,]+(?:[A-Z]{2}\s+\d{5}|\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b)|10\s+Downing\s+Street[A-Za-z0-9\s,]+', "[ADDRESS_REDACTED]"),
    ("GOVERNMENT_ID_SSN", r'\b\d{3}-\d{2}-\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]{1}\b', "[SSN_REDACTED]"),
    ("GOVERNMENT_ID_AADHAAR", r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b', "[AADHAAR_REDACTED]"),
    ("GOVERNMENT_ID_NINO", r'\b[A-CEGHJ-PR-TW-Z]{2}\s*\d{6}\s*[A-D]\b', "[NINO_REDACTED]"),
    ("CREDIT_CARD", r'\b(?:\d{4}[ -]?){3}\d{4}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b', "[CREDIT_CARD_REDACTED]"),
    ("BANK_ROUTING_ACCOUNT", r'(?:routing\s+(?:number\s+)?\d{9}\s+and\s+account\s+(?:number\s+)?\d{8,17}|account\s+(?:number\s+)?\d{8,17}\s+and\s+routing\s+(?:number\s+)?\d{9}|routing\s+(?:number\s+)?021\d{6})', "[BANK_ACCOUNT_REDACTED]"),
    ("AWS_KEY", r'\bAKIA[0-9A-Z]{16}\b', "[AWS_KEY_REDACTED]"),
    ("GOOGLE_CLOUD_KEY", r'\bAIzaSy[0-9A-Za-z_-]{33}\b', "[GCP_KEY_REDACTED]"),
    ("SENDGRID_KEY", r'\bSG\.[0-9a-zA-Z._-]{66}\b', "[SENDGRID_KEY_REDACTED]"),
    ("SLACK_TOKEN", r'\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,34}\b', "[SLACK_TOKEN_REDACTED]"),
    ("GITHUB_TOKEN", r'\b(ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}\b', "[GITHUB_TOKEN_REDACTED]"),
    ("OPENAI_API_KEY", r'\bsk-[a-zA-Z0-9]{32,48}\b', "[OPENAI_API_KEY_REDACTED]"),
    ("GENERIC_SECRET_KEY", r'\bsk_(?:live|test)_[0-9a-zA-Z]{16,}\b', "[API_KEY_REDACTED]"),
    ("JWT_TOKEN", r'\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b', "[JWT_REDACTED]"),
    ("PRIVATE_KEY_BLOCK", r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----|-----BEGIN [A-Z ]*PRIVATE KEY-----', "[PRIVATE_KEY_REDACTED]"),
    ("IBAN_ACCOUNT", r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b', "[IBAN_REDACTED]"),
    ("PASSPORT_NUMBER", r'\b[A-Z]{1,2}[0-9]{6,9}\b|\bPassport\s+number\s+[0-9]{7,10}\b', "[PASSPORT_REDACTED]"),
    ("IP_ADDRESS", r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', "[IP_REDACTED]"),
]


class PrivacySanitizer:
    """
    Redacts, masks, or synthetic-anonymizes PII and credentials.
    """

    def sanitize_text(self, text: str, mode: str = "REDACT") -> Dict[str, Any]:
        """
        Sanitizes input text according to specified mode: REDACT, MASK, or SYNTHETIC.
        """
        if not text:
            return {"sanitized_text": "", "detected_entities": []}

        sanitized_text = text
        detected_entities = []

        for pii_type, pattern, placeholder in PII_PATTERNS:
            matches = list(re.finditer(pattern, sanitized_text, re.IGNORECASE))
            for match in matches:
                val = match.group(0)
                preview = self._generate_preview(val)
                span = (match.start(), match.end())

                detected_entities.append({
                    "entity_type": pii_type,
                    "value_preview": preview,
                    "span": span,
                    "location": f"Span({span[0]}, {span[1]})"
                })

                replacement = self._get_replacement(val, pii_type, placeholder, mode)
                sanitized_text = sanitized_text.replace(val, replacement, 1)

        return {
            "sanitized_text": sanitized_text,
            "detected_entities": detected_entities
        }

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Backward-compatible tuple return: (sanitized_text, detected_entities)
        """
        res = self.sanitize_text(text, mode="REDACT")
        return res["sanitized_text"], res["detected_entities"]

    def _generate_preview(self, val: str) -> str:
        if len(val) <= 4:
            return "***"
        return val[:2] + "***" + val[-2:]

    def _get_replacement(self, val: str, pii_type: str, placeholder: str, mode: str) -> str:
        if mode.upper() == "MASK":
            if pii_type == "EMAIL_ADDRESS" and "@" in val:
                user, domain = val.split("@", 1)
                return f"{user[:1]}***@{domain[:1]}***.{domain.split('.')[-1]}"
            elif pii_type == "PHONE_NUMBER":
                return f"***-***-{val[-4:]}"
            elif pii_type == "CREDIT_CARD":
                return f"••••-••••-••••-{val[-4:]}"
            return self._generate_preview(val)

        elif mode.upper() == "SYNTHETIC":
            synthetic_map = {
                "EMAIL_ADDRESS": "user_anon@privacy-safe.org",
                "PHONE_NUMBER": "+1-555-0199",
                "CREDIT_CARD": "4000-0000-0000-0000",
                "GOVERNMENT_ID_SSN": "000-00-0000",
                "IP_ADDRESS": "127.0.0.1",
                "AWS_KEY": "AKIA0000000000000000",
            }
            return synthetic_map.get(pii_type, placeholder)

        # Default REDACT
        return placeholder


# Aliases for backward compatibility
PIISanitizer = PrivacySanitizer
Sanitizer = PrivacySanitizer
