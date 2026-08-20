"""
Context-Aware Privacy Entity & Span Detection Engine.
File Location: privacy_engine/context_detector.py

Capabilities:
  1. Distinguishes MENTION OF SENSITIVE CONCEPTS (educational) from ACTUAL SENSITIVE DATA (disclosure).
  2. Character-exact span extraction (start_index, end_index, raw_value).
  3. Credential combination detection (Username+Password, Card+CVV, Key+Secret).
  4. Structured explainable output per entity (severity, confidence, reason, context_type).
"""

import re
import math
from typing import List, Dict, Any, Tuple, Optional

# ── Educational / Conceptual Inquiry Patterns ─────────────────────────────────
# Queries matching these patterns without explicit value assignments are conceptual/safe.
_EDUCATIONAL_INQUIRY_PATTERNS = [
    r'\bwhat (?:is|are|was|were) (?:a |an |the |your |our )?(?:password|passwd|pin|credit card|cvv|cvc|ssn|aadhaar|pan card|api key|jwt|token|secret key|private key|iban)\b',
    r'\bhow (?:do|does|to|can) (?:you |we |i |a user )?(?:hash|salt|protect|reset|change|store|generate|encrypt|decrypt|manage|secure|validate|process) (?:a |the |your )?(?:password|passwd|credit card|api key|token|key|credentials?)\b',
    r'\bexplain (?:how |what |the concept of |the difference between )?.*(?:password|credit card|cryptography|encryption|hashing|api key|token|salting|two factor|2fa|oauth|jwt)\b',
    r'\b(?:password|credit card|api key|identity|fraud|security) (?:manager|policy|protection|generator|hashing|salting|strength|guidelines|prevention|mechanisms?|architecture|standards?|best practices?)\b',
    r'\b(?:difference between|compare|pros and cons of) .*(?:password|token|api key|symmetric|asymmetric|public key|private key)\b',
    r'\bdefine (?:a |an |the )?(?:password|credit card|cvv|api key|ssn|aadhaar)\b',
]

# ── Actual Direct Credential Disclosure Patterns ──────────────────────────────
_CREDENTIAL_DISCLOSURE_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (Entity Type, Pattern, Severity, Description)
    (
        "CREDENTIAL_PASSWORD",
        r'(?:password|passwd|pwd)\s*[:=]\s*[\'"]?([^\s\'",;]{4,})[\'"]?',
        "CRITICAL",
        "Direct password assignment detected in configuration or prompt text"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:my|the|our|admin|user|root|account)\s+(?:(?:account\s+)?password|passwd|pwd)\s+is\s+[\'"]?([A-Za-z0-9@#$%^&*!_+\-=]{4,})[\'"]?',
        "CRITICAL",
        "Plaintext password disclosure phrase detected"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:user|username|login)\s+[^\s]+\s+(?:and\s+)?(?:password|passwd)\s+[\'"]?([A-Za-z0-9@#$%^&*!_+\-=]{4,})[\'"]?',
        "CRITICAL",
        "Paired username and password credential assignment"
    ),
    (
        "DATABASE_CONNECTION_STRING",
        r'(?:postgres|postgresql|mysql|mongodb|redis|mssql|oracle)://[^\s:]+:[^\s@]+@[^\s/:]+(?::\d+)?(?:/[^\s]*)?',
        "CRITICAL",
        "Database connection URI with embedded authentication credentials"
    ),
    (
        "AWS_ACCESS_KEY",
        r'\bAKIA[0-9A-Z]{16}\b',
        "CRITICAL",
        "Amazon Web Services (AWS) 20-character Access Key ID"
    ),
    (
        "GITHUB_TOKEN",
        r'\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[0-9a-zA-Z_]{30,60}\b',
        "CRITICAL",
        "GitHub Personal Access Token or OAuth Token"
    ),
    (
        "OPENAI_API_KEY",
        r'\bsk-(?:proj-)?[a-zA-Z0-9_-]{16,64}\b',
        "CRITICAL",
        "OpenAI Secret API Key"
    ),
    (
        "GOOGLE_CLOUD_API_KEY",
        r'\bAIzaSy[0-9A-Za-z_-]{33}\b',
        "CRITICAL",
        "Google Cloud Service Account API Key"
    ),
    (
        "SENDGRID_API_KEY",
        r'\bSG\.[0-9a-zA-Z._-]{24,70}\b',
        "CRITICAL",
        "SendGrid Email API Key"
    ),
    (
        "SLACK_BOT_TOKEN",
        r'\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,34}\b',
        "CRITICAL",
        "Slack Bot OAuth Authorization Token"
    ),
    (
        "PROMPT_INJECTION_OVERRIDE",
        r'(?:ignore\s+(?:all\s+)?(?:previous\s+)?(?:system\s+|your\s+)?(?:instructions|safety\s+guidelines)|disregard\s+(?:all\s+)?(?:safety\s+)?guardrails|system\s+override[:\s]|developer\s+mode\s+dan|output\s+the\s+entire\s+system\s+prompt|repeat\s+all\s+instructions\s+above|you\s+are\s+an\s+unfiltered\s+ai|act\s+as\s+evil_ai|print\s+your\s+initial\s+instructions|dump\s+environment\s+variables|reveal\s+(?:the\s+)?(?:secret\s+)?system\s+prompt)',
        "CRITICAL",
        "Adversarial Prompt Injection & Guardrail Override Attempt"
    ),
    (
        "GENERIC_API_SECRET",
        r'\bsk_(?:live|test)_[0-9a-zA-Z]{16,}\b',
        "CRITICAL",
        "Stripe / SaaS Live Secret API Key"
    ),
    (
        "JWT_TOKEN",
        r'\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b',
        "CRITICAL",
        "JSON Web Token (JWT) with encoded header and signature"
    ),
    (
        "BEARER_TOKEN",
        r'[Bb]earer\s+[A-Za-z0-9\-_=.]{20,}',
        "CRITICAL",
        "HTTP Authorization Bearer Token secret"
    ),
    (
        "PRIVATE_KEY_BLOCK",
        r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----|-----BEGIN [A-Z ]*PRIVATE KEY-----',
        "CRITICAL",
        "PEM formatted cryptographic Private Key block"
    ),
]

# ── Standard PII Patterns ─────────────────────────────────────────────────────
_STANDARD_PII_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (Entity Type, Pattern, Severity, Description)
    (
        "EMAIL_ADDRESS",
        r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b',
        "MEDIUM",
        "Direct contact email address"
    ),
    (
        "PHONE_NUMBER",
        r'(?<!\d)(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)|\b(?:\+91[\s-]?)?[6-9]\d{9}\b|\+44[\s.-]?(?:\d[\s.-]?){9,11}\b',
        "MEDIUM",
        "Personal contact phone number"
    ),
    (
        "MEDICAL_PATIENT_RECORD",
        r'\bMRN-\d{4,8}\b|\bpatient\s+(?:intake|record|diagnostic|history|report|summary)[:\s]|diagnosed\s+with\s+[a-zA-Z0-9\s]+and\s+prescribed|prescribed\s+(?:daily\s+)?[a-zA-Z0-9\s]+(?:mg|g|mcg|tablets?)|scheduled\s+for\s+[a-zA-Z0-9\s]+(?:surgery|catheterization|procedure)|tested\s+positive\s+for\s+[a-zA-Z0-9\s]+;\s*allergy',
        "MEDIUM",
        "Protected Health Information (PHI / Medical Record)"
    ),
    (
        "PHYSICAL_STREET_ADDRESS",
        r'\b\d{1,5}[A-Za-z]?\s+[A-Za-z0-9\s.,]+(?:Terrace|Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)[A-Za-z0-9\s,]+(?:[A-Z]{2}\s+\d{5}|\b[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}\b|\bLondon\b|\bUSA\b|\bUnited Kingdom\b)|10\s+Downing\s+Street[A-Za-z0-9\s,]+',
        "MEDIUM",
        "Residential / Physical Delivery Address"
    ),
    (
        "CREDIT_CARD_NUMBER",
        r'\b(?:\d{4}[ -]?){3}\d{4}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',
        "HIGH",
        "Payment card number (Visa, Mastercard, Amex)"
    ),
    (
        "BANK_ROUTING_ACCOUNT",
        r'(?:routing\s+(?:number\s+)?\d{9}\s+and\s+account\s+(?:number\s+)?\d{8,17}|account\s+(?:number\s+)?\d{8,17}\s+and\s+routing\s+(?:number\s+)?\d{9}|routing\s+(?:number\s+)?021\d{6})',
        "HIGH",
        "Bank Routing & Checking Account Number Pair"
    ),
    (
        "GOVERNMENT_ID_SSN",
        r'\b\d{3}-\d{2}-\d{4}\b',
        "HIGH",
        "United States Social Security Number (SSN)"
    ),
    (
        "GOVERNMENT_ID_AADHAAR",
        r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b',
        "HIGH",
        "12-digit Indian National Aadhaar Number"
    ),
    (
        "GOVERNMENT_ID_PAN",
        r'\b[A-Z]{5}\d{4}[A-Z]{1}\b',
        "HIGH",
        "Indian Income Tax Permanent Account Number (PAN)"
    ),
    (
        "GOVERNMENT_ID_NINO",
        r'\b[A-Z]{2}\s*\d{6}\s*[A-D]\b',
        "HIGH",
        "UK National Insurance Number (NINO)"
    ),
    (
        "PASSPORT_NUMBER",
        r'\b[A-Z]{1,2}[0-9]{7,9}\b|\bPassport\s+number\s+[0-9]{7,10}\b',
        "HIGH",
        "International Passport identity document number"
    ),
    (
        "BANK_ACCOUNT_IBAN",
        r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b',
        "HIGH",
        "International Bank Account Number (IBAN)"
    ),
    (
        "IP_ADDRESS",
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        "LOW",
        "IPv4 network address"
    ),
]

# ── Combination Indicators ────────────────────────────────────────────────────
_USERNAME_INDICATORS = [
    r'(?:user|username|login|uname)\s*[:=]\s*[\'"]?([^\s\'",;]+)[\'"]?',
    r'(?:user|username)\s+is\s+[\'"]?([^\s\'",;]+)[\'"]?',
]

_CVV_EXPIRATION_INDICATORS = [
    r'\b(?:cvv|cvc|security code|cvv2)[\s:=#]*\d{3,4}\b',
    r'\b(?:exp|expiration|expires|valid thru)[\s:=]*\d{1,2}[/-]\d{2,4}\b',
]

_API_SECRET_INDICATORS = [
    r'(?:secret|api_secret|client_secret)\s*[:=]\s*[\'"]?([^\s\'",;]{8,})[\'"]?',
]


def _shannon_entropy(text: str) -> float:
    """Compute Shannon entropy in bits per character."""
    if not text:
        return 0.0
    freq: Dict[str, float] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)


def _is_luhn_valid(card_number_str: str) -> bool:
    """Validate credit card number using Luhn algorithm."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) not in (13, 14, 15, 16, 19):
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


class ContextAwareEntityDetector:
    """
    Precision Entity & Span Detector with Context Sensitivity.
    Distinguishes conceptual discussions from actual private data disclosures.
    """

    def is_educational_inquiry(self, text: str) -> bool:
        """Determines if the text is asking a conceptual, educational, or general question."""
        if not text or not text.strip():
            return False
        clean = text.strip().lower()
        # If prompt contains explicit credential disclosures or tokens, it is not educational
        for _, pat, _, _ in _CREDENTIAL_DISCLOSURE_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return False
        for pat in _EDUCATIONAL_INQUIRY_PATTERNS:
            if re.search(pat, clean, re.IGNORECASE):
                return True
        return False

    def detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans input text for sensitive entities, credentials, and compound identifiers.
        Returns a deduplicated, context-verified list of detected entity objects.
        """
        if not text or not text.strip():
            return []

        # Check if the entire query is an educational question without values
        is_educational = self.is_educational_inquiry(text)

        raw_hits: List[Dict[str, Any]] = []

        # 1. Scan for actual credential disclosure patterns (Highest Priority)
        for entity_type, pattern, severity, desc in _CREDENTIAL_DISCLOSURE_PATTERNS:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    val = match.group(0)
                    start, end = match.start(), match.end()
                    conf = 0.98

                    # Evaluate entropy for passwords
                    entropy = _shannon_entropy(val)
                    raw_hits.append({
                        "entity_type": entity_type,
                        "category": "Password / Credential" if "PASSWORD" in entity_type else "API Key / Token",
                        "detected_span": val,
                        "start_index": start,
                        "end_index": end,
                        "severity": severity,
                        "confidence": conf,
                        "entropy": round(entropy, 2),
                        "reason": desc,
                        "context_type": "ACTUAL_DISCLOSURE",
                    })
            except re.error:
                pass

        # 2. Scan standard PII patterns
        for entity_type, pattern, severity, desc in _STANDARD_PII_PATTERNS:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    val = match.group(0)
                    start, end = match.start(), match.end()

                    # Filters & False-positive guards
                    if entity_type == "IP_ADDRESS":
                        parts = val.split(".")
                        if all(p in ("0", "1", "2", "3", "127", "255") for p in parts):
                            continue  # Ignore localhost / loopback / broadcast
                    elif entity_type == "PASSPORT_NUMBER" and len(val) < 7:
                        continue
                    elif entity_type == "GOVERNMENT_ID_AADHAAR":
                        digits = re.sub(r'\D', '', val)
                        if len(digits) != 12:
                            continue

                    category_map = {
                        "EMAIL_ADDRESS": "Email Address",
                        "PHONE_NUMBER": "Phone Number",
                        "CREDIT_CARD_NUMBER": "Financial Information (Credit Card)",
                        "BANK_ROUTING_ACCOUNT": "Financial Bank Account & Routing",
                        "GOVERNMENT_ID_SSN": "Government ID (SSN)",
                        "GOVERNMENT_ID_AADHAAR": "Government ID (Aadhaar)",
                        "GOVERNMENT_ID_PAN": "Government ID (PAN)",
                        "GOVERNMENT_ID_NINO": "Government ID (UK NINO)",
                        "PASSPORT_NUMBER": "Passport Document",
                        "BANK_ACCOUNT_IBAN": "Bank Account (IBAN)",
                        "MEDICAL_PATIENT_RECORD": "Protected Health Information (PHI)",
                        "PHYSICAL_STREET_ADDRESS": "Physical / Delivery Address",
                        "IP_ADDRESS": "Network IP Address",
                    }

                    raw_hits.append({
                        "entity_type": entity_type,
                        "category": category_map.get(entity_type, "Personal Information"),
                        "detected_span": val,
                        "start_index": start,
                        "end_index": end,
                        "severity": severity,
                        "confidence": 0.95 if entity_type != "IP_ADDRESS" else 0.80,
                        "entropy": round(_shannon_entropy(val), 2),
                        "reason": desc,
                        "context_type": "ACTUAL_DISCLOSURE",
                    })
            except re.error:
                pass

        if not raw_hits:
            return []

        # 3. Deduplicate overlapping spans (preserve highest severity & largest span)
        raw_hits.sort(key=lambda h: (h["start_index"], -h["end_index"]))
        deduped: List[Dict[str, Any]] = []
        last_end = -1

        for hit in raw_hits:
            if hit["start_index"] >= last_end:
                deduped.append(hit)
                last_end = hit["end_index"]
            else:
                # Overlap: replace if current has higher severity
                sev_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
                prev = deduped[-1]
                if sev_order.get(hit["severity"], 0) > sev_order.get(prev["severity"], 0):
                    deduped[-1] = hit
                    last_end = hit["end_index"]

        # 4. Check for Credential Combinations (Compound Elevators)
        # Combination A: Credit Card + (CVV or Expiration)
        has_card = any(e["entity_type"] == "CREDIT_CARD_NUMBER" for e in deduped)
        has_cvv_or_exp = any(re.search(pat, text, re.IGNORECASE) for pat in _CVV_EXPIRATION_INDICATORS)
        if has_card and has_cvv_or_exp:
            for e in deduped:
                if e["entity_type"] == "CREDIT_CARD_NUMBER":
                    e["entity_type"] = "FINANCIAL_PAYMENT_CREDENTIALS"
                    e["category"] = "Financial Payment Credentials (Card + CVV/Exp)"
                    e["severity"] = "CRITICAL"
                    e["confidence"] = 0.99
                    e["reason"] = "Actionable financial payment credential combination (Card Number + CVV/Expiration) detected"

        # Combination B: Username + Password
        has_password = any(e["entity_type"] == "CREDENTIAL_PASSWORD" for e in deduped)
        has_username = any(re.search(pat, text, re.IGNORECASE) for pat in _USERNAME_INDICATORS)
        if has_password and has_username:
            for e in deduped:
                if e["entity_type"] == "CREDENTIAL_PASSWORD":
                    e["entity_type"] = "COMPOUND_AUTHENTICATION_CREDENTIALS"
                    e["category"] = "Authentication Credentials (Username + Password)"
                    e["severity"] = "CRITICAL"
                    e["confidence"] = 0.99
                    e["reason"] = "Combined username and password authentication pair detected"

        # Combination C: API Key + Secret
        has_api_key = any("API_KEY" in e["entity_type"] or "TOKEN" in e["entity_type"] for e in deduped)
        has_secret = any(re.search(pat, text, re.IGNORECASE) for pat in _API_SECRET_INDICATORS)
        if has_api_key and has_secret:
            for e in deduped:
                if "API_KEY" in e["entity_type"]:
                    e["severity"] = "CRITICAL"
                    e["category"] = "API Key + Secret Combination"
                    e["reason"] = "API key and client secret credential pair detected"

        # 5. If query was purely educational with no genuine value matches, ensure safety
        if is_educational and len(deduped) == 0:
            return []

        return deduped
