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
    r'\bwhat (?:is|are|was|were) (?:a |an |the |your |our )?(?:strong |good |secure |valid |temp |temporary |random )?(?:password|passwd|pin|credit card|cvv|cvc|ssn|aadhaar|pan card|api key|jwt|token|secret key|private key|iban)\b',
    r'\bhow (?:do|does|to|can) (?:you |we |i |a user )?(?:hash|salt|protect|reset|change|store|generate|encrypt|decrypt|manage|secure|validate|process) (?:a |the |your )?(?:password|passwd|credit card|api key|token|key|credentials?)\b',
    r'\bexplain (?:how |what |the concept of |the difference between )?.*(?:password|credit card|cryptography|encryption|hashing|api key|token|salting|two factor|2fa|oauth|jwt)\b',
    r'\b(?:password|credit card|api key|identity|fraud|security) (?:manager|policy|protection|generator|hashing|salting|strength|guidelines|prevention|mechanisms?|architecture|standards?|best practices?)\b',
    r'\b(?:difference between|compare|pros and cons of) .*(?:password|token|api key|symmetric|asymmetric|public key|private key)\b',
    r'\bdefine (?:a |an |the )?(?:password|credit card|cvv|api key|ssn|aadhaar)\b',
    # General personal/relationship questions (Educational / Conceptual)
    r'\bwhat (?:is|are|was|were) (?:common |typical |frequent |major )?(?:causes?|reasons?|signs?|symptoms?|types?|examples?|effects?) of (?:relationship |marriage |marital |family |domestic |personal |workplace )?(?:conflicts?|problems?|disputes?|issues?|stress|burnout|trauma|breakups?|divorce)\b',
    r'\bhow (?:do|does|to|can) (?:couples|families|people|individuals|partners|therapists|parents|someone) (?:improve|handle|manage|resolve|navigate|deal with|treat|overcome) (?:relationship|marital|family|domestic|personal|communication) (?:conflicts?|problems?|issues?|challenges?|disputes?)\b',
    r'\b(?:explain|discuss|describe) (?:how |what |the psychology of |the dynamics of )?(?:relationship|family|interpersonal|marriage) (?:counseling|therapy|dynamics|communication|conflicts?)\b',
]

# ── Highly Personal Context Patterns & Classifiers ────────────────────────────
# Three-Level Personal Context Model:
# 1. SAFE: General inquiries/concepts (handled by educational/general matchers)
# 2. WARNING: Mild 1st-person disclosure of personal context
# 3. HIGH RISK: Detailed, identifying, narrative, or multi-party intimate disclosure

# High Risk Deep Disclosure Markers
_HIGH_PERSONAL_RISK_PATTERNS = [
    # Detailed relationship history & private multi-party events
    r'\b(?:tell you|share|describe|explain|detail|confess)\s+(?:everything|all|the whole story|every detail)\s+(?:that happened|about my|in my)\s+(?:\d+[- ](?:year|month)|long-term|past|entire)?\s*(?:relationship|marriage|partnership|divorce)',
    r'\b(?:private|intimate|secret|confidential)\s+(?:events?|details?|aspects?|conversations?|matters?)\s+involving\s+my\s+(?:partner|spouse|husband|wife|boyfriend|girlfriend|family|parents|in-laws|children|kids|ex|ex-partner)',
    r'\b(?:details? of my|everything about my)\s+(?:divorce|custody battle|family court|infidelity|affair|marital crisis|domestic dispute)',
    r'\b(?:my|our)\s+(?:\d+[- ]year|\d+[- ]month|long[- ]term)\s+relationship,\s*(?:including|involving)\s+(?:private|intimate|personal|secret)\s+(?:events?|details?|disputes?)',
    r'\b(?:intimate|secret|confidential)\s+(?:details?|history)\s+of\s+my\s+(?:family|marriage|relationship|private life|financial crisis)',
    r'\b(?:secret|private)\s+(?:family dispute|inheritance battle|court case|custody dispute|domestic conflict)\b',
    r'\b(?:confidential|sensitive)\s+personal\s+(?:experience|trauma|history|story)\s+involving\s+my\b',
]

# Warning Level Mild Personal Statement Indicators (1st-person disclosure)
_MILD_PERSONAL_CONTEXT_PATTERNS = [
    r'\b(?:i have been having|i am having|i had|i am dealing with|i have)\s+(?:problems?|issues?|trouble|struggles?|conflicts?|disagreements?|arguments?)\s+(?:with|in)\s+my\s+(?:relationship|partner|spouse|husband|wife|boyfriend|girlfriend|family|brother|sister|parents|mother|father|friend)\b',
    r'\b(?:my\s+(?:relationship|marriage|partner|spouse|husband|wife|boyfriend|girlfriend|family|brother|sister|parents))\s+(?:and i\s+)?(?:had an argument|are having problems|broke up|is struggling|had a conflict)\b',
    r'\b(?:i feel|i am feeling)\s+(?:stressed|upset|anxious|overwhelmed|heartbroken|depressed)\s+(?:about|because of)\s+my\s+(?:relationship|partner|marriage|family|divorce|finances|personal life)\b',
    r'\b(?:i want to talk about|can we talk about|asking for advice on)\s+my\s+(?:personal|relationship|family|marital|dating)\s+(?:situation|problem|struggle|conflict)\b',
    r'\b(?:my personal experience with|in my personal life|my private life)\b',
]


# ── Actual Direct Credential Disclosure Patterns ──────────────────────────────
_CREDENTIAL_DISCLOSURE_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (Entity Type, Pattern, Severity, Description)
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:database|db|server|app|application|login|admin|account|root|user|api|client)?\s*(?:password|passwd|pwd))\s*[:=]\s*[\'"]?([^\s\'",;]{3,})[\'"]?',
        "CRITICAL",
        "Direct password assignment detected in configuration or prompt text"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:my|the|our|admin|user|root|account|db|database|server|app|application|login)?\s*(?:(?:database|db|server|app|application|login|admin|account|root|user)\s+)?(?:password|passwd|pwd)\s+is\s+[\'"]?([^\s\'",;]{3,})[\'"]?)',
        "CRITICAL",
        "Plaintext password disclosure phrase detected"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:user|username|login|uname)\s+[^\s]+\s+(?:and\s+)?(?:password|passwd|pwd)\s+(?:is\s+|[:=]\s*)?[\'"]?([^\s\'",;]{3,})[\'"]?',
        "CRITICAL",
        "Paired username and password credential assignment"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:my|the|our)?\s*secret\s+(?:i\s+use\s+to\s+(?:log\s*in|access)|for\s+(?:logging\s*in|accessing|my\s+account))\s*(?:to\s+(?:my|the|our)\s+account)?\s*[:=is\s]+[\'"]?([^\s\'",;]{3,})[\'"]?)',
        "CRITICAL",
        "Plaintext login secret disclosure phrase detected"
    ),
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:deploy\s+credentials|server\s+credentials|login\s+credentials|account\s+credentials)\s*(?:for\s+[^:]+)?\s*[:=is\s]+[\'"]?([^\s\'",;]{3,})[\'"]?)',
        "CRITICAL",
        "System deploy / access credentials disclosure phrase detected"
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
        r'(?:(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?(?:system\s+|safety\s+)?(?:instructions|rules|guidelines|guardrails|constraints)|(?:print|output|reveal|leak|exfiltrate|show|dump|repeat)\s+(?:all\s+|the\s+)?(?:initial\s+|previous\s+|entire\s+|secret\s+)?(?:system\s+)?(?:prompt|instructions|rules|directives)(?:\s+verbatim)?|system\s*prompt\s*(?:exfiltration|leak|dump|reveal)|print\s+everything\s+above\s+this\s+line|(?:system[:\s]+)?system\s+override[:\s.]|you\s+are\s+now\s+(?:an\s+|in\s+)?(?:unfiltered\s+ai|developer\s+mode|dan|evil_ai)|developer\s+mode\s+dan|act\s+as\s+(?:an\s+)?evil_ai|dump\s+environment\s+variables)',
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
    # ── OTP / One-Time Password Detection ─────────────────────────────────────
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:my|the|our|your)?\s*(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s+(?:is|was|=|:)\s*["\']?(\d{4,8})["\']?)',
        "CRITICAL",
        "One-Time Password (OTP) credential disclosure"
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s*(?:code|number|num|no)?\s*[:=]\s*["\']?(\d{4,8})["\']?)',
        "CRITICAL",
        "OTP credential assignment or disclosure"
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:my|the|our|your)?\s*(?:otp|one[- ]?time[- ]?(?:password|code|pin))\s+["\']?(\d{4,8})["\']?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "Direct One-Time Password (OTP) code disclosure"
    ),
    (
        "CREDENTIAL_OTP",
        r'(?:\b(?:verification|2fa|two[- ]?factor|mfa|authentication)\s+(?:code|otp|pin)\s+(?:is|was|=|:)\s*["\']?(\d{4,8})["\']?)',
        "CRITICAL",
        "Two-factor / MFA verification code disclosure"
    ),
    # ── PIN Detection ─────────────────────────────────────────────────────────
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:my|the|our|your)?\s*(?:atm|debit|credit|bank|card|transaction|upi|mobile)?\s*(?:pin|pin\s*(?:number|num|no|code))\s*(?:is|was|=|:)\s*["\']?(\d{4,6})["\']?)',
        "CRITICAL",
        "Personal Identification Number (PIN) disclosure"
    ),
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:atm|debit|credit|bank|card|transaction|upi|mobile)\s+pin\s*[:=]\s*["\']?(\d{4,6})["\']?)',
        "CRITICAL",
        "Banking / Card PIN assignment disclosure"
    ),
    (
        "CREDENTIAL_PIN",
        r'(?:\b(?:my|the|our|your)?\s*(?:atm|debit|credit|bank|card|transaction|upi|mobile)?\s*(?:pin|pin\s*(?:number|num|no|code))\s+["\']?(\d{4,6})["\']?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "Direct PIN code disclosure"
    ),
    # ── Contextual Number-Only Password Detection ─────────────────────────────
    (
        "CREDENTIAL_PASSWORD",
        r'(?:\b(?:my|the|our|admin|user|root|account)?\s*(?:password|passwd|pwd)\s+(?:is\s+)?["\']?(\d{4,})["\']?(?:\s|$|[.,;!?]))',
        "CRITICAL",
        "Numeric-only password disclosure detected via contextual keyword"
    ),
    # ── Auth Token / Session Token Disclosure ─────────────────────────────────
    (
        "CREDENTIAL_AUTH_TOKEN",
        r'(?:\b(?:my|the|our)?\s*(?:auth(?:entication)?|session|access|refresh)\s*(?:token|key)\s+(?:is|was|=|:)\s*["\']?([^\s"\',;]{8,})["\']?)',
        "CRITICAL",
        "Authentication / Session token credential disclosure"
    ),
    # ── Secret Key Disclosure ─────────────────────────────────────────────────
    (
        "CREDENTIAL_SECRET_KEY",
        r'(?:\b(?:my|the|our)?\s*(?:secret|private|signing|encryption)\s*(?:key|code|phrase)\s+(?:is|was|=|:)\s*["\']?([^\s"\',;]{6,})["\']?)',
        "CRITICAL",
        "Secret / Private key value disclosure"
    ),
    # ── Bank / Net Banking / UPI Credential Disclosure ────────────────────────
    (
        "CREDENTIAL_BANK_LOGIN",
        r'(?:\b(?:net\s*banking|mobile\s*banking|internet\s*banking|online\s*banking|bank(?:ing)?)\s+(?:password|passwd|pwd|pin|login)\s+(?:is|was|=|:)\s*["\']?([^\s"\',;]{3,})["\']?)',
        "CRITICAL",
        "Net Banking / Mobile Banking login credential disclosure"
    ),
    (
        "CREDENTIAL_BANK_LOGIN",
        r'(?:\b(?:upi)\s+(?:pin|password|mpin)\s*(?:is|was|=|:)\s*["\']?(\d{4,6})["\']?)',
        "CRITICAL",
        "UPI PIN / Mobile Payment credential disclosure"
    ),
]

# ── Standard PII Patterns ─────────────────────────────────────────────────────
_STANDARD_PII_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (Entity Type, Pattern, Severity, Description)
    (
        "PHONE_NUMBER",
        r'(?i)(?:\b(?:my|the|our|contact)?\s*(?:phone|mobile|cell|tel|telephone|whatsapp)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?((?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}|\+?1[\s.-]?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10})["\']?)',
        "MEDIUM",
        "Personal contact phone number with context"
    ),
    (
        "PHONE_NUMBER",
        r'(?<!\d)(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)|\b(?:\+91[\s-]?)?[6-9]\d{4}[-\s]?\d{5}\b|\b(?:\+91[\s-]?)?[6-9]\d{9}\b|\+44[\s.-]?(?:\d[\s.-]?){9,11}\b',
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
        "BANK_ACCOUNT_NUMBER",
        r'\b(?:(?:bank\s+)?account\s*(?:num|no|number)?|bank\s+acc|beneficiary\s+acc(?:ount)?|transfer\s+(?:money\s+|funds\s+)?to\s+(?:bank\s+)?account|payment\s+to\s+(?:bank\s+)?account|IFSC\s+[A-Z]{4}0[A-Z0-9]{6}\s+(?:and\s+)?account)\s*(?:is|to|:|=)?\s*(\d{9,18})\b',
        "HIGH",
        "Bank Account Number with contextual indicators"
    ),
    (
        "BANK_ACCOUNT_NUMBER",
        r'\b(?:my|the|our|beneficiary)\s+(?:bank\s+account|account\s+number|acc\s+no|account)\s+is\s+(\d{9,18})\b',
        "HIGH",
        "Direct bank account number disclosure"
    ),
    (
        "BANK_ACCOUNT_NUMBER",
        r'\b(?:send|transfer|deposit|wire|pay)\s+(?:money\s+|funds\s+)?to\s+(?:bank\s+)?account\s*(?:number|num|no)?\s*[:=]?\s*(\d{9,18})\b',
        "HIGH",
        "Bank account funds transfer instruction"
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
        r'(?i)(?:\b(?:my|the|our|user|citizen|customer)?\s*(?:aadhaar|aadhar|uidai|adhaar|adhar)\s*(?:card)?\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?(\d{4}[-\s]?\d{4}[-\s]?\d{4}|\d{12})["\']?)',
        "HIGH",
        "Indian National Aadhaar Number with contextual phrase"
    ),
    (
        "GOVERNMENT_ID_AADHAAR",
        r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b',
        "HIGH",
        "12-digit Indian National Aadhaar Number formatted with spaces or hyphens"
    ),
    (
        "GOVERNMENT_ID_PAN",
        r'(?i)(?:\b(?:my|the|our)?\s*(?:pan|pan\s*card)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?([A-Za-z]{5}\d{4}[A-Za-z])["\']?)',
        "HIGH",
        "Indian Income Tax Permanent Account Number (PAN) with contextual phrase"
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
        r'(?i)(?:\b(?:my|the|our)?\s*(?:passport|ppt)\s*(?:number|no|num|#)?\s*(?:is|was|=|:)?\s*["\']?([A-Za-z][0-9]{7,8})["\']?)',
        "HIGH",
        "Passport document number with contextual phrase"
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

    def detect_personal_context(self, text: str) -> Dict[str, Any]:

        """
        Three-Level Personal Context Model:
          1. SAFE: General inquiries or conceptual discussion without meaningful personal disclosure.
          2. WARNING: Mild 1st-person disclosure of personal context without strong reason to block.
          3. HIGH_RISK: Detailed, identifying, narrative, or multi-party intimate disclosure requiring confirmation.
        
        ML Integration Preparation:
          classification_source = "rule_based_precheck"
          (Semantic ML classification with BERT + Naive Bayes will be implemented in Pipeline 3).
        """
        if not text or not text.strip():
            return {
                "detected": False,
                "level": "SAFE",
                "category": "SAFE",
                "classification_source": "rule_based_precheck",
                "requires_confirmation": False,
                "reason": "No personal information detected.",
                "matched_spans": [],
            }

        # 1. Educational / Conceptual questions without personal disclosure are SAFE
        if self.is_educational_inquiry(text):
            return {
                "detected": False,
                "level": "SAFE",
                "category": "SAFE",
                "classification_source": "rule_based_precheck",
                "requires_confirmation": False,
                "reason": "General or educational discussion without personal disclosure.",
                "matched_spans": [],
            }

        clean = text.strip()
        lower = clean.lower()

        # 2. Check for High Privacy Risk patterns (Deep, identifying, multi-party narratives)
        high_risk_hits = []
        for pat in _HIGH_PERSONAL_RISK_PATTERNS:
            for match in re.finditer(pat, clean, re.IGNORECASE):
                high_risk_hits.append({
                    "start": match.start(),
                    "end": match.end(),
                    "span": match.group(0),
                })

        # Additional multi-factor check for high personal disclosure:
        # 1st-person intent + timeframe/depth + multiple private parties/events
        has_first_person = bool(re.search(r'\b(?:i|my|we|our|me)\b', lower))
        has_narrative_intent = bool(re.search(r'\b(?:tell you|share with you|explain|talk about|discuss)\s+(?:everything|all|the whole story|every detail|my whole life)\b', lower))
        has_relationship_terms = bool(re.search(r'\b(?:relationship|marriage|partner|spouse|husband|wife|boyfriend|girlfriend|ex)\b', lower))
        has_family_terms = bool(re.search(r'\b(?:family|parents|in-laws|mother|father|brother|sister|children|kids)\b', lower))
        has_private_terms = bool(re.search(r'\b(?:private|intimate|secret|confidential|traumatic|personal)\s+(?:events?|details?|disputes?|history|matters?)\b', lower))

        is_compound_high_risk = (
            has_first_person and (
                (has_narrative_intent and (has_relationship_terms or has_family_terms)) or
                (has_relationship_terms and has_family_terms and (has_private_terms or "private" in lower)) or
                (has_private_terms and (has_relationship_terms or has_family_terms))
            )
        )

        if high_risk_hits or is_compound_high_risk:
            # Explanation never repeats the user's private content
            return {
                "detected": True,
                "level": "HIGH_RISK",
                "category": "HIGHLY_PERSONAL_CONTEXT",
                "classification_source": "rule_based_precheck",
                "requires_confirmation": True,
                "reason": "Detailed personal experiences may contain sensitive information.",
                "matched_spans": high_risk_hits if high_risk_hits else [{"start": 0, "end": len(clean), "span": "[HIGHLY PERSONAL CONTEXT]"}],
            }

        # 3. Check for Warning Level (Mild personal disclosure)
        mild_hits = []
        for pat in _MILD_PERSONAL_CONTEXT_PATTERNS:
            for match in re.finditer(pat, clean, re.IGNORECASE):
                mild_hits.append({
                    "start": match.start(),
                    "end": match.end(),
                    "span": match.group(0),
                })

        # Also check general 1st-person personal context statement
        if has_first_person and (has_relationship_terms or has_family_terms):
            is_mild_personal = bool(re.search(r'\b(?:having|had|dealing with|going through|feel|stressed|sad|struggling|argue|argument|problem|issue|conflict|advice)\b', lower))
            if is_mild_personal or mild_hits:
                return {
                    "detected": True,
                    "level": "WARNING",
                    "category": "HIGHLY_PERSONAL_CONTEXT",
                    "classification_source": "rule_based_precheck",
                    "requires_confirmation": False,
                    "reason": "Personal context disclosed in message.",
                    "matched_spans": mild_hits if mild_hits else [{"start": 0, "end": len(clean), "span": "[PERSONAL CONTEXT]"}],
                }

        # Otherwise SAFE
        return {
            "detected": False,
            "level": "SAFE",
            "category": "SAFE",
            "classification_source": "rule_based_precheck",
            "requires_confirmation": False,
            "reason": "General discussion without meaningful personal disclosure.",
            "matched_spans": [],
        }

    def detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans input text for sensitive entities, credentials, compound identifiers,
        and personal context disclosures.
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
                        "BANK_ACCOUNT_NUMBER": "Financial Information (Bank Account)",
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

        # 3. Personal Context Detection (if not purely educational)
        if not is_educational:
            pers_ctx = self.detect_personal_context(text)
            if pers_ctx["detected"]:
                for span_info in pers_ctx.get("matched_spans", []):
                    start = span_info.get("start", 0)
                    end = span_info.get("end", len(text))
                    span_val = text[start:end] if start < len(text) and end <= len(text) else text
                    raw_hits.append({
                        "entity_type": "HIGHLY_PERSONAL_CONTEXT" if pers_ctx["level"] == "HIGH_RISK" else "MILD_PERSONAL_CONTEXT",
                        "category": "Highly Personal Context" if pers_ctx["level"] == "HIGH_RISK" else "Personal Context",
                        "detected_span": span_val,
                        "start_index": start,
                        "end_index": end,
                        "severity": "HIGH" if pers_ctx["level"] == "HIGH_RISK" else "MEDIUM",
                        "confidence": 0.92,
                        "entropy": 0.0,
                        "reason": pers_ctx["reason"],
                        "context_type": "PERSONAL_CONTEXT",
                        "personal_context_level": pers_ctx["level"],
                        "classification_source": "rule_based_precheck",
                        "requires_confirmation": pers_ctx["requires_confirmation"],
                    })

        if not raw_hits:
            return []

        # 4. Deduplicate overlapping spans (preserve highest severity & largest span)
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

        # 5. Check for Credential Combinations (Compound Elevators)
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

        # 6. If query was purely educational with no genuine value matches, ensure safety
        if is_educational and len(deduped) == 0:
            return []

        return deduped

