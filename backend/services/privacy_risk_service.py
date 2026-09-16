"""
Context-Aware Privacy Risk & Exposure Analysis Service.
File: backend/services/privacy_risk_service.py

Implements:
  1. Context-Aware Entity Detection (Locations, Names, Contacts, IDs, Credentials, Financials).
  2. Context Analysis (Distinguishes Personal Disclosures from General Knowledge / Inquiries).
  3. Deterministic Risk Scoring (0 to 10 scale across 5 levels: MINIMAL, LOW, MEDIUM, HIGH, CRITICAL).
  4. Multi-Message Combination Risk & Cumulative Exposure Analysis.
  5. Cryptographic & Safe Masking (Zero Raw Secret Leakage).
  6. Actionable Explanations and Safe Usage Recommendations.
"""

import re
import html
from typing import Dict, Any, List, Optional, Tuple, Set


class PrivacyRiskService:
    """
    Production Context-Aware Privacy Risk Intelligence Engine.
    """

    # ── RISK LEVEL THRESHOLDS & BADGES ───────────────────────────────────────
    RISK_LEVEL_THRESHOLDS = [
        (0, 0, "MINIMAL", "🟢 MINIMAL", "#10B981"),
        (1, 1, "MINIMAL", "🟢 MINIMAL", "#10B981"),
        (2, 4, "LOW",     "🟡 LOW",     "#FBBF24"),
        (5, 6, "MEDIUM",  "🟠 MEDIUM",  "#F97316"),
        (7, 8, "HIGH",    "🔴 HIGH",    "#EF4444"),
        (9, 10, "CRITICAL", "🚨 CRITICAL", "#DC2626"),
    ]

    # ── 1. LOCATION DICTIONARIES & GEOGRAPHY PATTERNS ────────────────────────
    COUNTRIES = {
        "india", "united states", "usa", "uk", "united kingdom", "canada", "australia",
        "germany", "france", "japan", "china", "singapore", "uae", "dubai", "saudi arabia",
        "new zealand", "italy", "spain", "brazil", "russia", "south africa", "nepal",
        "sri lanka", "bangladesh", "pakistan", "malaysia", "indonesia", "thailand"
    }

    INDIAN_STATES = {
        "tamil nadu", "tamilnadu", "karnataka", "kerala", "andhra pradesh", "andhra",
        "telangana", "maharashtra", "delhi", "uttar pradesh", "gujarat", "rajasthan",
        "west bengal", "punjab", "haryana", "bihar", "odisha", "orissa", "madhya pradesh",
        "assam", "jharkhand", "chhattisgarh", "uttarakhand", "himachal pradesh", "goa",
        "tripura", "meghalaya", "manipur", "nagaland", "mizoram", "sikkim", "arunachal pradesh",
        "jammu and kashmir", "ladakh", "puducherry", "pondicherry", "chandigarh"
    }

    MAJOR_CITIES_AND_DISTRICTS = {
        "krishnagiri", "chennai", "bangalore", "bengaluru", "hyderabad", "mumbai", "delhi",
        "pune", "kolkata", "ahmedabad", "coimbatore", "madurai", "salem", "hosur", "trichy",
        "tiruchirappalli", "tirunelveli", "vellore", "erode", "thanjavur", "dharmapuri",
        "mysore", "mysuru", "mangalore", "hubli", "visakhapatnam", "vizag", "vijayawada",
        "guntur", "warangal", "kochi", "cochin", "thiruvananthapuram", "trivandrum", "calicut",
        "kozhikode", "thrissur", "noida", "gurgaon", "gurugram", "faridabad", "ghaziabad",
        "jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "patna", "vadodara",
        "surat", "chandigarh", "nashik", "aurangabad", "solapur", "amravati", "varanasi"
    }

    # ── 2. PERSONAL DISCLOSURE CONTEXT PATTERNS ──────────────────────────────
    PERSONAL_DISCLOSURE_PREFIXES = [
        r'\b(?:i\s+live\s+in|i\s+am\s+from|i\s+belong\s+to|i\s+reside\s+in|i\s+stay\s+in|my\s+home\s+is\s+in|my\s+house\s+is\s+in)\b',
        r'\b(?:my\s+address\s+is|my\s+residence\s+is|my\s+location\s+is|my\s+city\s+is|my\s+district\s+is|my\s+state\s+is|my\s+country\s+is)\b',
        r'\b(?:my\s+house\s+is\s+near|i\s+live\s+near|i\s+stay\s+near|my\s+flat\s+is\s+near|my\s+apartment\s+is\s+near)\b',
        r'\b(?:my\s+house\s+number\s+is|house\s+no|flat\s+no|door\s+no|apartment\s+no|apt\s+no|plot\s+no)\b',
        r'\b(?:my\s+name\s+is|i\s+am|myself|my\s+full\s+name\s+is|call\s+me)\b',
        r'\b(?:my\s+phone\s+is|my\s+phone\s+number\s+is|my\s+mobile\s+is|my\s+number\s+is|call\s+me\s+at|reach\s+me\s+at|contact\s+me\s+at|whatsapp\s+me\s+at)\b',
        r'\b(?:my\s+email\s+is|my\s+email\s+address\s+is|mail\s+me\s+at|send\s+email\s+to|email\s+id\s+is)\b',
        r'\b(?:my\s+pan\s+is|my\s+pan\s+number\s+is|my\s+aadhaar\s+is|my\s+aadhaar\s+number\s+is|my\s+passport\s+is|my\s+driving\s+licence\s+is|my\s+voter\s+id\s+is)\b',
        r'\b(?:my\s+password\s+is|password\s+is|password\s*[:=]|secret\s+is|my\s+otp\s+is|otp\s+is|otp\s*[:=]|my\s+pin\s+is)\b',
        r'\b(?:my\s+api\s+key\s+is|api\s+key\s*[:=]|access\s+token\s*[:=]|secret\s+key\s*[:=]|my\s+token\s+is)\b',
        r'\b(?:my\s+card\s+number\s+is|card\s+no\s*[:=]|my\s+bank\s+account\s+is|account\s+number\s+is|acc\s+no\s*[:=]|a/c\s+no\s*[:=])\b',
    ]

    # General Knowledge / Educational Context (False Positive Suppressors)
    GENERAL_QUERY_PATTERNS = [
        r'\b(?:what\s+is|what\s+are|how\s+is|how\s+to|tell\s+me\s+about|explain|describe|define)\b',
        r'\b(?:weather\s+in|temperature\s+in|climate\s+in|population\s+of|history\s+of|capital\s+of|places\s+to\s+visit\s+in|distance\s+between)\b',
        r'\b(?:is\s+famous\s+for|famous\s+places\s+in|tourist\s+spots\s+in|best\s+food\s+in|restaurants\s+in|hotels\s+in|route\s+to|trains\s+to)\b',
        r'\b(?:i\s+like|i\s+love|i\s+visited|i\s+went\s+to|i\s+traveled\s+to|great\s+city|big\s+city|nice\s+place)\b',
    ]

    # Non-sensitive number contexts (dogs, train, chapter, temp, dates)
    NON_SENSITIVE_NUMBER_PATTERNS = [
        r'\b\d+\s+(?:dogs?|cats?|pets?|books?|pages?|chapters?|articles?|items?|people|members?|km|kilometers?|miles?|meters?|kg|liters?|hours?|mins?|minutes?|days?|months?|years?|dollars?|rupees?|inr|usd|degrees?|celsius|fahrenheit|percent|%)\b',
        r'\b(?:train|flight|bus|express|route|chapter|page|section|rule|version|v|step|level|room|table|model)\s*(?:no|number|#)?\s*[:=]?\s*\d+\b',
        r'\b(?:in|year|since|during)\s+(?:19\d{2}|20\d{2})\b',
    ]

    # ── 3. MASKING UTILITIES ──────────────────────────────────────────────────

    @classmethod
    def mask_phone_number(cls, raw_val: str) -> str:
        """Masks phone number showing only last 4 digits (e.g. ******3210)."""
        digits = re.sub(r'\D', '', raw_val)
        if len(digits) >= 4:
            last4 = digits[-4:]
            return f"******{last4}"
        return "******"

    @classmethod
    def mask_email_address(cls, raw_val: str) -> str:
        """Masks email address (e.g. a***@example.com)."""
        if "@" in raw_val:
            user_part, domain_part = raw_val.split("@", 1)
            first_char = user_part[0] if user_part else "u"
            return f"{first_char}***@{domain_part}"
        return "***@masked.com"

    @classmethod
    def mask_pan_number(cls, raw_val: str) -> str:
        """Masks PAN card number (e.g. ABCDE****F)."""
        clean = raw_val.strip().upper()
        if len(clean) == 10:
            return f"{clean[:5]}****{clean[-1]}"
        return "ABCDE****F"

    @classmethod
    def mask_aadhaar_number(cls, raw_val: str) -> str:
        """Masks Aadhaar number (e.g. **** **** 5678)."""
        digits = re.sub(r'\D', '', raw_val)
        if len(digits) >= 4:
            return f"**** **** {digits[-4:]}"
        return "**** **** ****"

    @classmethod
    def mask_card_number(cls, raw_val: str) -> str:
        """Masks Credit/Debit card number (e.g. **** **** **** 1234)."""
        digits = re.sub(r'\D', '', raw_val)
        if len(digits) >= 4:
            return f"**** **** **** {digits[-4:]}"
        return "**** **** **** ****"

    @classmethod
    def mask_secret_credential(cls, raw_val: str) -> str:
        """Masks secret, password, OTP, or API key completely."""
        return "******"

    @classmethod
    def mask_address(cls, raw_val: str) -> str:
        """Masks residential address preserving only city or general area."""
        return re.sub(r'(?i)\b(?:house|flat|door|plot|apt|building)\s+(?:no\.?|number|#)?\s*[a-z0-9/-]+', '[RESIDENCE REDACTED]', raw_val)

    # ── 4. CONTEXT-AWARE SENSITIVE DETECTION ─────────────────────────────────

    @classmethod
    def detect_sensitive_information(cls, text: str) -> List[Dict[str, Any]]:
        """
        Extracts candidate sensitive items from text with span offsets and context classification.
        """
        if not text or not text.strip():
            return []

        raw_lower = text.lower()
        detections: List[Dict[str, Any]] = []

        # ── Check General Knowledge & False Positive Suppressors ──────────────
        is_general_query = any(re.search(p, raw_lower) for p in cls.GENERAL_QUERY_PATTERNS)
        is_explicit_disclosure = any(re.search(p, raw_lower) for p in cls.PERSONAL_DISCLOSURE_PREFIXES)

        # ── 1. AUTHENTICATION SECRETS (PASSWORDS, OTPs, API KEYS) ────────────
        # 1a. Password
        pwd_match = re.search(r'(?i)\b(?:my\s+password\s+is|password\s*[:=]|secret\s+is)\s*[\'"]?([^\s\'",;]{4,})[\'"]?', text)
        if pwd_match:
            val = pwd_match.group(1)
            detections.append({
                "type": "PASSWORD",
                "category": "AUTHENTICATION_SECRET",
                "raw_value": val,
                "masked_value": cls.mask_secret_credential(val),
                "start": pwd_match.start(),
                "end": pwd_match.end(),
                "base_score": 10,
                "risk_level": "CRITICAL",
                "reason": "Plaintext authentication password shared. Exposes accounts to unauthorized access and takeover.",
                "action": "Do not share passwords in chat. If active, change and rotate this password immediately."
            })

        # 1b. OTP Code
        otp_match = re.search(r'(?i)\b(?:my\s+otp\s+is|otp\s*[:=]|one-time\s+password\s+is|verification\s+code\s+is)\s*[:=]?\s*(\d{4,8})\b', text)
        if otp_match:
            val = otp_match.group(1)
            detections.append({
                "type": "OTP_CODE",
                "category": "AUTHENTICATION_SECRET",
                "raw_value": val,
                "masked_value": cls.mask_secret_credential(val),
                "start": otp_match.start(),
                "end": otp_match.end(),
                "base_score": 9,
                "risk_level": "CRITICAL",
                "reason": "Time-sensitive One-Time Password (OTP) shared. Enables immediate 2FA bypass and account compromise.",
                "action": "Never share OTP codes. OTPs should only be entered into official verification prompts."
            })

        # 1c. API Keys & Access Tokens
        api_match = re.search(r'\b(?:sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35}|Bearer\s+[a-zA-Z0-9._~+/-]{25,})\b', text)
        if not api_match:
            api_match = re.search(r'(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*[\'"]?([a-zA-Z0-9_\-.]{12,})[\'"]?', text)
        if api_match:
            val = api_match.group(0)
            detections.append({
                "type": "API_KEY",
                "category": "AUTHENTICATION_SECRET",
                "raw_value": val,
                "masked_value": "sk-****KEY" if "sk-" in val else "******",
                "start": api_match.start(),
                "end": api_match.end(),
                "base_score": 10,
                "risk_level": "CRITICAL",
                "reason": "Cloud or service API access token detected. Allows unauthorized API usage, billing misuse, and backend penetration.",
                "action": "Revoke and regenerate this API token immediately in your developer dashboard."
            })

        # ── 2. GOVERNMENT IDENTITY DOCUMENTS ─────────────────────────────────
        # 2a. Aadhaar Number (12 digits)
        aadhaar_match = re.search(r'\b(?:aadhaar|uidai|adhar|uid)?\s*[:=]?\s*([2-9]\d{3}\s?\d{4}\s?\d{4})\b', text, re.IGNORECASE)
        if aadhaar_match and any(kw in raw_lower for kw in ["aadhaar", "uidai", "adhar", "uid", "identity", "kyc", "doc"]):
            val = aadhaar_match.group(1)
            detections.append({
                "type": "AADHAAR_NUMBER",
                "category": "GOVERNMENT_ID",
                "raw_value": val,
                "masked_value": cls.mask_aadhaar_number(val),
                "start": aadhaar_match.start(),
                "end": aadhaar_match.end(),
                "base_score": 8,
                "risk_level": "HIGH",
                "reason": "Official government national identification number (Aadhaar) shared. Poses identity theft and fraudulent KYC risks.",
                "action": "Avoid sharing complete 12-digit Aadhaar numbers in public chat environments."
            })

        # 2b. PAN Card Number (5 letters + 4 digits + 1 letter)
        pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text)
        if pan_match:
            val = pan_match.group(0)
            detections.append({
                "type": "PAN_NUMBER",
                "category": "GOVERNMENT_ID",
                "raw_value": val,
                "masked_value": cls.mask_pan_number(val),
                "start": pan_match.start(),
                "end": pan_match.end(),
                "base_score": 8,
                "risk_level": "HIGH",
                "reason": "Official Income Tax Permanent Account Number (PAN) shared. Can be used for unauthorized financial profiling.",
                "action": "Mask or avoid sharing PAN numbers in unencrypted communications."
            })

        # 2c. Passport Number
        passport_match = re.search(r'\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b', text)
        if passport_match and any(kw in raw_lower for kw in ["passport", "travel", "visa", "citizenship", "embassy"]):
            val = passport_match.group(0)
            detections.append({
                "type": "PASSPORT_NUMBER",
                "category": "GOVERNMENT_ID",
                "raw_value": val,
                "masked_value": f"{val[:2]}****{val[-2:]}",
                "start": passport_match.start(),
                "end": passport_match.end(),
                "base_score": 8,
                "risk_level": "HIGH",
                "reason": "International passport travel document number shared. May enable unauthorized travel profiling.",
                "action": "Do not disclose passport details in public channels."
            })

        # ── 3. FINANCIAL CREDENTIALS (CARDS, BANK ACCOUNTS) ──────────────────
        # 3a. Credit / Debit Card
        card_match = re.search(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b', text.replace(" ", "").replace("-", ""))
        if not card_match:
            card_match = re.search(r'\b(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4})\b', text)
        if card_match and any(kw in raw_lower for kw in ["card", "credit", "debit", "visa", "mastercard", "exp", "cvv", "payment"]):
            val = card_match.group(0)
            has_cvv = bool(re.search(r'(?i)\b(?:cvv|cvc|security\s+code)\s*[:=]?\s*\d{3,4}\b', text))
            base_s = 10 if has_cvv else 8
            r_level = "CRITICAL" if has_cvv else "HIGH"
            detections.append({
                "type": "PAYMENT_CARD",
                "category": "FINANCIAL_DATA",
                "raw_value": val,
                "masked_value": cls.mask_card_number(val),
                "start": card_match.start(),
                "end": card_match.end(),
                "base_score": base_s,
                "risk_level": r_level,
                "reason": "Financial payment card credentials shared. Enables unauthorized card-not-present transactions.",
                "action": "Never disclose payment card numbers or CVVs in chat. If exposed, freeze the card immediately."
            })

        # 3b. Bank Account Number
        bank_match = re.search(r'\b(?:account|acc|ac|a/c)\s*(?:no|number|#)?\s*[:=.,]?\s*(\d{9,18})\b', text, re.IGNORECASE)
        if bank_match:
            val = bank_match.group(1)
            detections.append({
                "type": "BANK_ACCOUNT",
                "category": "FINANCIAL_DATA",
                "raw_value": val,
                "masked_value": f"******{val[-4:]}" if len(val) >= 4 else "******",
                "start": bank_match.start(),
                "end": bank_match.end(),
                "base_score": 7,
                "risk_level": "HIGH",
                "reason": "Bank account number shared. Can be targeted for unauthorized direct debits or social engineering.",
                "action": "Do not share full banking account numbers in public messaging."
            })

        # 3c. UPI ID / Virtual Payment Address (VPA)
        upi_match = re.search(r'\b([a-zA-Z0-9.\-_]{2,49}@(okhdfcbank|okaxis|oksbi|okicici|upi|paytm|ybl|apl|axl|ibl|barodampay|federal|kotak|postbank|idfcbank|freecharge|airtel|pingpay))\b', text, re.IGNORECASE)
        if upi_match:
            val = upi_match.group(1)
            user_p, vpa_bank = val.split("@", 1) if "@" in val else (val, "upi")
            masked_upi = f"{user_p[:1]}***@{vpa_bank}"
            detections.append({
                "type": "UPI_ID",
                "category": "FINANCIAL_DATA",
                "raw_value": val,
                "masked_value": masked_upi,
                "start": upi_match.start(),
                "end": upi_match.end(),
                "base_score": 6,
                "risk_level": "MEDIUM",
                "reason": "Unified Payments Interface (UPI) VPA shared. Discloses linked bank handle and personal payment identifier.",
                "action": "Avoid sharing UPI VPAs in public chat channels."
            })

        # ── 4. DIRECT CONTACT INFORMATION (PHONE, EMAIL) ─────────────────────
        # 4a. Phone Number (Indian & International)
        phone_match = re.search(r'(?:(?:\+|00)91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b', text)
        if not phone_match:
            phone_match = re.search(r'(?:\+?1[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b', text)
        # Verify it is not a general number context (e.g. train number, 5-digit zip, simple count)
        if phone_match:
            raw_phone_val = phone_match.group(0)
            digits_only = re.sub(r'\D', '', raw_phone_val)
            is_non_sens = bool(re.search(rf'\b{re.escape(raw_phone_val)}\s+(?:dogs?|cats?|pages?|chapters?|km|kg|meters?|years?|rupees?|dollars?)\b', text, re.IGNORECASE))
            if len(digits_only) in (10, 11, 12) and not is_non_sens:
                detections.append({
                    "type": "PHONE_NUMBER",
                    "category": "CONTACT_INFORMATION",
                    "raw_value": raw_phone_val,
                    "masked_value": cls.mask_phone_number(raw_phone_val),
                    "start": phone_match.start(),
                    "end": phone_match.end(),
                    "base_score": 5,
                    "risk_level": "MEDIUM",
                    "reason": "Personal direct contact phone number shared. May lead to unsolicited calls, spam, and targeted smishing.",
                    "action": "Public chats lo phone number unnecessary ga share cheyyakandi."
                })

        # 4b. Email Address
        email_match = re.search(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', text)
        if email_match:
            val = email_match.group(0)
            detections.append({
                "type": "EMAIL_ADDRESS",
                "category": "CONTACT_INFORMATION",
                "raw_value": val,
                "masked_value": cls.mask_email_address(val),
                "start": email_match.start(),
                "end": email_match.end(),
                "base_score": 3,
                "risk_level": "LOW",
                "reason": "Personal email address shared. May attract spam and spear-phishing campaigns.",
                "action": "Avoid sharing personal email addresses publicly unless necessary."
            })

        # ── 5. LOCATION HIERARCHY & ADDRESS ANALYSIS ─────────────────────────
        # Check Level 6/7: Full Address (House No, Flat No, Street, PIN code)
        full_addr_match = re.search(r'(?i)\b(?:house|flat|door|plot|apt|apartment|building)\s+(?:no\.?|number|#)?\s*[a-z0-9/-]+.*?(?:street|road|nagar|colony|layout|lane|avenue|cross|main|salai|marg).*?(?:krishnagiri|chennai|bangalore|hyderabad|mumbai|delhi|pune|\d{6})', text)
        has_pin = bool(re.search(r'\b\d{6}\b', text)) and any(kw in raw_lower for kw in ["pin", "pincode", "postal", "zip", "nagar", "road", "street"])
        has_house = bool(re.search(r'(?i)\b(?:house\s+(?:no|number)|flat\s+(?:no|number)|door\s+(?:no|number)|plot\s+(?:no|number))\b', text))

        if full_addr_match or (has_house and (any(c in raw_lower for c in cls.MAJOR_CITIES_AND_DISTRICTS) or has_pin)):
            has_phone = any(d["type"] == "PHONE_NUMBER" for d in detections)
            base_s = 10 if has_phone else 8
            r_lvl = "CRITICAL" if has_phone else "HIGH"
            reason_txt = "Exact residential physical address + direct contact info exposed." if has_phone else "Specific residential home address shared."
            detections.append({
                "type": "EXACT_RESIDENTIAL_ADDRESS",
                "category": "LOCATION_DATA",
                "raw_value": text,
                "masked_value": cls.mask_address(text),
                "start": 0,
                "end": len(text),
                "base_score": base_s,
                "risk_level": r_lvl,
                "reason": reason_txt,
                "action": "Avoid posting precise house/apartment addresses in online chat systems."
            })

        # Check Level 5: Street-level location
        elif re.search(r'(?i)\b(?:i\s+live\s+on|my\s+house\s+is\s+on|on\s+[a-z\s]+(?:road|street|nagar|colony|salai|marg|avenue))\s+in\s+([a-z\s]+)', text):
            detections.append({
                "type": "STREET_LOCATION",
                "category": "LOCATION_DATA",
                "raw_value": text,
                "masked_value": "[STREET-LEVEL LOCATION]",
                "start": 0,
                "end": len(text),
                "base_score": 5,
                "risk_level": "MEDIUM",
                "reason": "Specific street-level residential location shared.",
                "action": "Consider sharing only city-level location instead of exact street names."
            })

        # Check Level 4: Locality / Landmark ("near Krishnagiri bus stand")
        elif re.search(r'(?i)\b(?:i\s+live\s+near|my\s+house\s+is\s+(?:near|opposite|behind)|near\s+[a-z\s]+(?:bus\s+stand|railway\s+station|market|hospital|temple|lake))\b', text):
            detections.append({
                "type": "LOCALITY_LOCATION",
                "category": "LOCATION_DATA",
                "raw_value": text,
                "masked_value": "[LOCALITY / LANDMARK]",
                "start": 0,
                "end": len(text),
                "base_score": 4,
                "risk_level": "LOW",
                "reason": "Local neighborhood landmark or area shared.",
                "action": "Keep neighborhood landmarks confidential to preserve physical privacy."
            })

        # Check Level 3: City / District ("I live in Krishnagiri", "My address is Krishnagiri")
        elif is_explicit_disclosure and any(c in raw_lower for c in cls.MAJOR_CITIES_AND_DISTRICTS):
            matched_city = next(c for c in cls.MAJOR_CITIES_AND_DISTRICTS if c in raw_lower)
            detections.append({
                "type": "GENERAL_LOCATION",
                "category": "LOCATION_DATA",
                "raw_value": matched_city.title(),
                "masked_value": matched_city.title(),
                "start": text.lower().find(matched_city),
                "end": text.lower().find(matched_city) + len(matched_city),
                "base_score": 2,
                "risk_level": "LOW",
                "reason": "City/district-level personal location information shared.",
                "action": "Avoid combining city-level locations with exact street addresses or identity documents."
            })

        # Check Level 2: State ("I live in Tamil Nadu")
        elif is_explicit_disclosure and any(s in raw_lower for s in cls.INDIAN_STATES):
            matched_state = next(s for s in cls.INDIAN_STATES if s in raw_lower)
            detections.append({
                "type": "BROAD_LOCATION",
                "category": "LOCATION_DATA",
                "raw_value": matched_state.title(),
                "masked_value": matched_state.title(),
                "start": text.lower().find(matched_state),
                "end": text.lower().find(matched_state) + len(matched_state),
                "base_score": 2,
                "risk_level": "LOW",
                "reason": "State-level broad geographical area shared.",
                "action": "Broad state locations carry minimal privacy risk when not combined with contact data."
            })

        # Check Level 1: Country ("I am from India")
        elif is_explicit_disclosure and any(c in raw_lower for c in cls.COUNTRIES):
            matched_country = next(c for c in cls.COUNTRIES if c in raw_lower)
            detections.append({
                "type": "BROAD_LOCATION",
                "category": "LOCATION_DATA",
                "raw_value": matched_country.title(),
                "masked_value": matched_country.title(),
                "start": text.lower().find(matched_country),
                "end": text.lower().find(matched_country) + len(matched_country),
                "base_score": 1,
                "risk_level": "MINIMAL",
                "reason": "Country-level broad geographical location shared.",
                "action": "Country mentions carry minimal privacy risk."
            })

        # ── 6. PERSONAL NAME ─────────────────────────────────────────────────
        name_match = re.search(r'(?i)\b(?:my\s+name\s+is|my\s+full\s+name\s+is|call\s+me|myself)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
        if not name_match:
            cand = re.search(r'(?i)\bi\s+am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
            if cand:
                first_w = cand.group(1).lower().split()[0]
                if first_w not in {"from", "in", "at", "living", "staying", "near", "working", "studying", "a", "an", "the", "not", "very", "so", "just", "here", "there", "writing", "asking", "looking", "trying", "going", "interested", "sure", "happy"}:
                    name_match = cand

        if name_match:
            p_name = name_match.group(1)
            detections.append({
                "type": "PERSONAL_NAME",
                "category": "IDENTITY_DATA",
                "raw_value": p_name,
                "masked_value": p_name,
                "start": name_match.start(1),
                "end": name_match.end(1),
                "base_score": 2,
                "risk_level": "LOW",
                "reason": "Personal name shared in conversation.",
                "action": "A personal name alone is low risk, but increases in severity when paired with contact or identity details."
            })

        # ── 7. LOW / MEDIUM PERSONAL ATTRIBUTES & PREFERENCES ─────────────────
        # 7a. Height (e.g. 170 cm, 5'10", 5 feet 7 inches)
        height_match = re.search(r'(?i)\b(?:height\s*(?:is|:)?\s*|i\s+am\s+)?(\d{2,3}\s*(?:cm|cms|centimeters?)|[4-7]\s*(?:ft|feet|\')\s*(?:\d{1,2}\s*(?:in|inches|\")?)?)\b', text)
        if height_match and any(kw in raw_lower for kw in ["height", "tall", "cm", "feet", "inch"]):
            val = height_match.group(1).strip()
            detections.append({
                "type": "PHYSICAL_ATTRIBUTE_HEIGHT",
                "category": "PHYSICAL_DATA",
                "raw_value": val,
                "masked_value": val,
                "start": height_match.start(1),
                "end": height_match.end(1),
                "base_score": 1,
                "risk_level": "LOW",
                "reason": "Physical height attribute mentioned. By itself, height generally cannot uniquely identify a person.",
                "action": "Low sensitivity alone, but increases identifiability when combined with photo or personal identifiers."
            })

        # 7b. Weight (e.g. 65 kg, 140 lbs)
        weight_match = re.search(r'(?i)\b(?:weight\s*(?:is|:)?\s*|weigh\s+)?(\d{2,3}\s*(?:kg|kgs|kilos?|lbs|pounds))\b', text)
        if weight_match and any(kw in raw_lower for kw in ["weight", "weigh", "kg", "lbs"]):
            val = weight_match.group(1).strip()
            detections.append({
                "type": "PHYSICAL_ATTRIBUTE_WEIGHT",
                "category": "PHYSICAL_DATA",
                "raw_value": val,
                "masked_value": val,
                "start": weight_match.start(1),
                "end": weight_match.end(1),
                "base_score": 1,
                "risk_level": "LOW",
                "reason": "Physical weight attribute mentioned. By itself, weight does not uniquely identify a person.",
                "action": "Keep combined biometrics confidential in public forums."
            })

        # 7c. Age / Age Range (e.g. 23 years old, age 23)
        age_match = re.search(r'(?i)\b(?:i\s+am\s+|age\s*(?:is|:)?\s*)(\d{1,2})\s*(?:years?\s+old|yrs?\s+old)?\b', text)
        if age_match and ("age" in raw_lower or "years old" in raw_lower or "yrs old" in raw_lower):
            val = age_match.group(1).strip()
            detections.append({
                "type": "DEMOGRAPHIC_AGE",
                "category": "DEMOGRAPHIC_DATA",
                "raw_value": f"{val} years old",
                "masked_value": f"{val} years old",
                "start": age_match.start(1),
                "end": age_match.end(1),
                "base_score": 1,
                "risk_level": "LOW",
                "reason": "Personal age attribute mentioned. General age alone carries low individual risk.",
                "action": "Avoid pairing age with specific city, school, or workplace data."
            })

        # 7d. Workplace / Employer (e.g. I work at Google, works in Infosys)
        work_match = re.search(r'(?i)\b(?:i\s+work\s+(?:at|for|in)|employed\s+at|working\s+at)\s+([A-Z][a-zA-Z0-9\s&]{2,30})\b', text)
        if work_match:
            val = work_match.group(1).strip()
            detections.append({
                "type": "PROFESSIONAL_WORKPLACE",
                "category": "PROFESSIONAL_DATA",
                "raw_value": val,
                "masked_value": val,
                "start": work_match.start(1),
                "end": work_match.end(1),
                "base_score": 3,
                "risk_level": "MEDIUM",
                "reason": "Specific workplace or employer disclosed. Can narrow down individual identity when paired with location/name.",
                "action": "Do not share exact team or corporate identifiers alongside personal contact details."
            })

        # 7e. School / College / University (e.g. studying at IIT Madras)
        edu_match = re.search(r'(?i)\b(?:studying\s+at|student\s+at|alumni\s+of|college\s+is|school\s+is)\s+([A-Z][a-zA-Z0-9\s&]{2,35})\b', text)
        if edu_match:
            val = edu_match.group(1).strip()
            detections.append({
                "type": "EDUCATIONAL_INSTITUTION",
                "category": "EDUCATIONAL_DATA",
                "raw_value": val,
                "masked_value": val,
                "start": edu_match.start(1),
                "end": edu_match.end(1),
                "base_score": 3,
                "risk_level": "MEDIUM",
                "reason": "Educational institution disclosed. Contributes to identity profiling when combined with name or graduation year.",
                "action": "Keep educational affiliations broad in public chats."
            })

        # ── 8. MEDICAL & HEALTH RECORDS (PROTECTED HEALTH INFORMATION - PHI) ─
        # 8a. Clinical Diagnosis & Patient Intake Records
        med_diag = re.search(r'(?i)\b(?:MRN-\d{4,8}|patient\s+(?:intake|record|diagnostic|history|report|summary)[:\s]|(?:diagnosed\s+(?:with|of)|suffering\s+from|tested\s+positive\s+for|biopsy\s+shows|clinical\s+diagnosis|pathology\s+report)\s+[a-z0-9\s,-]{2,40}?(?:diabetes|cancer|hypertension|covid-?19|asthma|depression|anxiety|hiv|cardiac|tumor|leukemia|arthritis|alzheimer|dementia|bipolar|infection|pneumonia|hepatitis|stroke|disorder|ulcer|epilepsy)|scheduled\s+for\s+[a-zA-Z0-9\s]+(?:surgery|catheterization|procedure))', text)
        if med_diag:
            val = med_diag.group(0)
            detections.append({
                "type": "MEDICAL_DIAGNOSIS",
                "category": "HEALTH_DATA",
                "raw_value": val,
                "masked_value": "[HEALTH RECORD REDACTED]",
                "start": med_diag.start(),
                "end": med_diag.end(),
                "base_score": 8,
                "risk_level": "HIGH",
                "reason": "Protected Health Information (PHI) / Clinical diagnosis disclosed. Exposes sensitive medical status.",
                "action": "Do not disclose private medical records or clinical health conditions in AI prompts."
            })

        # 8b. Prescription Medications & Dosages
        rx_match = re.search(r'(?i)\b(?:prescribed|prescription|dosage|taking|dose\s+of)\s+(?:daily\s+|twice\s+daily\s+|oral\s+)?[a-zA-Z0-9\s-]{2,30}?\s*(?:\d{1,4}\s*(?:mg|g|mcg|ml|tablets?|capsules?|units?))|\b(?:amoxicillin|metformin|lisinopril|atorvastatin|levothyroxine|amlodipine|metoprolol|omeprazole|losartan|albuterol|gabapentin|hydrochlorothiazide|sertraline|simvastatin|montelukast|escitalopram|pantoprazole|fluoxetine|furosemide|doxycycline|ibuprofen|paracetamol|aspirin|prednisone)\s*(?:\d{1,4}\s*(?:mg|g|mcg|ml))\b', text)
        if rx_match:
            val = rx_match.group(0)
            detections.append({
                "type": "PRESCRIPTION_MEDICATION",
                "category": "HEALTH_DATA",
                "raw_value": val,
                "masked_value": "[PRESCRIPTION REDACTED]",
                "start": rx_match.start(),
                "end": rx_match.end(),
                "base_score": 7,
                "risk_level": "HIGH",
                "reason": "Personal prescription medication and dosage information disclosed. Reveals health conditions and therapy.",
                "action": "Mask medication names and dosages before querying AI models."
            })

        # ── 9. CONFIDENTIAL COMPANY INFORMATION & TRADE SECRETS ─────────────
        biz_match = re.search(r'(?i)(?:\b(?:confidential\s+project|internal\s+project|project\s+codename|codename)\s*[:=]?\s*[\'"]?([A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)?)|Project\s+(?:Titan|Apollo|Genesis|Prometheus|Manhattan|Starlight|Blackhawk|Vanguard|Phoenix|Mercury)\s*[-:]?\s*(?:confidential|internal\s+only|strictly\s+confidential|proprietary)|\b(?:(?:q[1-4]|quarterly|annual|fiscal\s+year|fy\d{2,4})\s+(?:revenue|sales|profit|margin|earnings|ebitda)\s*(?:is|was|=|:)\s*[\$€£₹]?\s*\d+(?:\.\d+)?\s*(?:million|billion|m|b|k)?|\b(?:internal|confidential)\s+(?:profit\s+margin|financials?|revenue|budget)\s*(?:is|was|=|:)?\s*[\$€£₹]?\s*\d+(?:\.\d+)?\s*(?:%|million|billion|m|b)?)|confidential\s+(?:company|internal|business|client)\s+(?:data|database|records?|strategy|roadmap|memo|information)|proprietary\s+(?:algorithm|architecture|source\s+code|trade\s+secret)|strictly\s+confidential\s+under\s+nda|confidential\s+client\s+contract\s+value\s*[:=]?\s*[\$€£₹]?\s*\d+)', text)
        if biz_match:
            val = biz_match.group(0)
            detections.append({
                "type": "CONFIDENTIAL_BUSINESS_INFO",
                "category": "BUSINESS_CONFIDENTIAL",
                "raw_value": val,
                "masked_value": "[CONFIDENTIAL BUSINESS DATA]",
                "start": biz_match.start(),
                "end": biz_match.end(),
                "base_score": 9,
                "risk_level": "CRITICAL",
                "reason": "Confidential company data, financial metrics, project roadmap, or trade secrets disclosed. Poses severe corporate data breach risks.",
                "action": "Confidential internal business information must not be transmitted to public cloud LLMs."
            })

        # ── 10. DRIVER'S LICENSE & VOTER ID ──────────────────────────────────
        dl_match = re.search(r'\b(?:[A-Z]{2}[0-9]{2}[ -]?[0-9]{4}[ -]?[0-9]{7}|DL[ -]?[A-Z0-9]{8,16})\b', text)
        if dl_match:
            val = dl_match.group(0)
            detections.append({
                "type": "DRIVING_LICENSE",
                "category": "GOVERNMENT_ID",
                "raw_value": val,
                "masked_value": f"{val[:3]}****{val[-2:]}",
                "start": dl_match.start(),
                "end": dl_match.end(),
                "base_score": 7,
                "risk_level": "HIGH",
                "reason": "Driver's license identity document number disclosed.",
                "action": "Mask driver's license numbers in communications."
            })

        return detections

    # ── 4b. FULL PERSONAL INFORMATION SANITIZATION / ANONYMIZATION ───────────

    @classmethod
    def sanitize_text(cls, text: str, mode: str = "MASK") -> str:
        """
        Sanitizes, masks, and anonymizes personal information from text:
          - Phone numbers -> ******3210 or [PHONE_NUMBER]
          - Email addresses -> e***@example.com or [EMAIL_ADDRESS]
          - Passwords / Keys / OTPs -> ****** or [REDACTED_CREDENTIAL]
          - Aadhaar / PAN -> **** **** 1234 / ABCDE****F or [GOVT_ID]
          - Medical Records -> [HEALTH RECORD REDACTED] or [HEALTH_DATA_REDACTED]
          - Confidential Company Info -> [CONFIDENTIAL BUSINESS DATA]
          - UPI IDs -> u***@okhdfcbank or [UPI_ID_REDACTED]
          - Residential addresses -> [RESIDENTIAL_ADDRESS]
          - Personal Names -> [NAME]
          - Physical Biometrics (Height, Weight, Age) -> [HEIGHT], [WEIGHT], [AGE]
          - Workplace & Educational Institutions -> [WORKPLACE], [INSTITUTION]
        """
        if not text:
            return ""

        sanitized = text
        detections = cls.detect_sensitive_information(text)
        detections_sorted = sorted(
            [d for d in detections if d.get("raw_value")],
            key=lambda x: len(str(x["raw_value"])),
            reverse=True
        )

        for d in detections_sorted:
            raw_v = str(d["raw_value"]).strip()
            if not raw_v or len(raw_v) < 2:
                continue

            masked_v = d.get("masked_value", f"[{d['type']}]")
            repl = f"[{d['type']}]" if mode == "REDACT" else masked_v

            try:
                sanitized = re.sub(rf'\b{re.escape(raw_v)}\b', repl, sanitized, flags=re.IGNORECASE)
            except Exception:
                sanitized = sanitized.replace(raw_v, repl)

        return sanitized

    # ── 5. MULTI-MESSAGE COMBINATION RISK & CONVERSATION ANALYSIS ────────────

    @classmethod
    def calculate_combined_risk(
        cls,
        current_detections: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes cumulative privacy exposure across conversation turns:
          - Tracks all categories disclosed across history (Name, City, Phone, Address, IDs)
          - Detects dangerous correlation points (e.g. Name + Location + Phone = HIGH risk)
        """
        all_categories: Set[str] = set()
        all_types: Set[str] = set()

        # Collect current message detections
        for d in current_detections:
            all_categories.add(d.get("category", "UNKNOWN"))
            all_types.add(d.get("type", "UNKNOWN"))

        # Inspect chat_history safely for metadata (NO raw secret logging)
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    user_txt = msg.get("text", "")
                    # Extract lightweight types from history
                    hist_dets = cls.detect_sensitive_information(user_txt)
                    for hd in hist_dets:
                        all_categories.add(hd.get("category", "UNKNOWN"))
                        all_types.add(hd.get("type", "UNKNOWN"))

        has_name = "PERSONAL_NAME" in all_types
        has_loc = any(t in all_types for t in ["GENERAL_LOCATION", "LOCALITY_LOCATION", "STREET_LOCATION", "BROAD_LOCATION", "EXACT_RESIDENTIAL_ADDRESS"])
        has_phone = "PHONE_NUMBER" in all_types
        has_email = "EMAIL_ADDRESS" in all_types
        has_id = any(t in all_types for t in ["AADHAAR_NUMBER", "PAN_NUMBER", "PASSPORT_NUMBER", "DRIVING_LICENSE", "VOTER_ID"])
        has_secret = any(t in all_types for t in ["PASSWORD", "OTP_CODE", "API_KEY", "PAYMENT_CARD"])
        has_confidential = any(t in all_types for t in ["CONFIDENTIAL_BUSINESS_INFO", "TRADE_SECRET", "INTERNAL_FINANCIAL_METRICS"])
        has_medical = any(t in all_types for t in ["MEDICAL_DIAGNOSIS", "PRESCRIPTION_MEDICATION", "MEDICAL_PATIENT_RECORD"])
        has_full_addr = "EXACT_RESIDENTIAL_ADDRESS" in all_types
        has_work = "PROFESSIONAL_WORKPLACE" in all_types
        has_edu = "EDUCATIONAL_INSTITUTION" in all_types
        has_age = "DEMOGRAPHIC_AGE" in all_types
        has_height = "PHYSICAL_ATTRIBUTE_HEIGHT" in all_types

        # ── Correlation Evaluation ───────────────────────────────────────────
        if has_secret or has_confidential:
            score = 10 if has_secret else 9
            level = "CRITICAL"
            reason = "Active credentials, passwords, confidential trade secrets, or payment cards exposed in conversation."
        elif has_full_addr and has_phone:
            score = 10
            level = "CRITICAL"
            reason = "Exact physical home address combined with direct personal telephone number."
        elif (has_medical and (has_name or has_phone or has_id)):
            score = 9
            level = "CRITICAL"
            reason = "Protected Health Information (PHI) directly linked to identifiable personal contact/identity."
        elif (has_name and has_loc and has_phone) or (has_id and has_phone):
            score = 8
            level = "HIGH"
            reason = "Cumulative profile exposure: Full Name + Location + Direct Phone Number enables direct personal tracking."
        elif has_medical:
            score = 8
            level = "HIGH"
            reason = "Protected Health Information (Clinical Diagnosis / Prescription) disclosed."
        elif (has_name and has_loc and (has_work or has_edu or has_age)):
            score = 6
            level = "MEDIUM"
            reason = "Combination of Full Name + Location + Demographic/Professional attributes significantly increases identifiability."
        elif (has_name and has_phone) or (has_loc and has_phone) or (has_name and has_email and has_loc):
            score = 6
            level = "MEDIUM"
            reason = "Multiple identifying points combined across messages (Contact details + Location/Name)."
        elif has_name and has_loc:
            score = 4
            level = "LOW"
            reason = "Name and general location shared across conversation turns."
        elif current_detections:
            max_det_score = max(d.get("base_score", 0) for d in current_detections)
            score = max_det_score
            level = next(lvl for min_s, max_s, lvl, _, _ in cls.RISK_LEVEL_THRESHOLDS if min_s <= score <= max_s)
            reason = current_detections[0].get("reason", "Sensitive item disclosed.")
        else:
            score = 0
            level = "MINIMAL"
            reason = "No cumulative privacy risk detected across conversation."

        return {
            "score": score,
            "level": level,
            "reason": reason,
            "all_categories": sorted(list(all_categories)),
            "all_types": sorted(list(all_types)),
            "is_multi_turn_escalated": len(all_categories) >= 2 and score >= 6,
        }

    # ── 6. MEMORY & CONTEXT LEAKAGE / UNEXPECTED PERSONALIZATION ANALYZER ────

    @classmethod
    def analyze_ai_response_leakage(
        cls,
        user_message: str,
        ai_response: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        account_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes AI Response to detect:
          1. Unexpected retrieval of personal information from memory or prior turns.
          2. Unnecessary personalization (e.g. answering 10+10 with '20, Sanjay from Krishnagiri').
          3. Context leakage across conversation boundaries.
          4. Complete Source Attribution (Current Message, Conversation History, Account/Profile, Inferred).
          5. Multi-factor risk calculation:
             PRIVACY RISK = SENSITIVITY + IDENTIFIABILITY + COMBINATION RISK + SOURCE RISK + UNEXPECTED CONTEXT USE + POTENTIAL HARM
        """
        ai_dets = cls.detect_sensitive_information(ai_response)
        user_dets = cls.detect_sensitive_information(user_message)
        user_raw_types = {d["type"] for d in user_dets}
        user_raw_vals = {str(d.get("raw_value", "")).lower() for d in user_dets if d.get("raw_value")}

        history_dets: List[Dict[str, Any]] = []
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    history_dets.extend(cls.detect_sensitive_information(msg.get("text", "")))
        history_types = {d["type"] for d in history_dets}
        history_vals = {str(d.get("raw_value", "")).lower() for d in history_dets if d.get("raw_value")}

        account_keys = set(account_profile.keys()) if account_profile else set()
        account_vals = {str(v).lower() for v in account_profile.values()} if account_profile else set()

        # Check for remembered entities from history/account that appear directly in ai_response
        for hd in history_dets:
            raw_h_val = str(hd.get("raw_value", "")).strip()
            if raw_h_val and len(raw_h_val) >= 3:
                if re.search(rf'\b{re.escape(raw_h_val)}\b', ai_response, re.IGNORECASE):
                    if not any(ad.get("type") == hd["type"] for ad in ai_dets):
                        ai_dets.append({
                            "type": hd["type"],
                            "category": hd.get("category", "PERSONAL_DATA"),
                            "raw_value": raw_h_val,
                            "masked_value": hd.get("masked_value", raw_h_val),
                            "base_score": hd.get("base_score", 2),
                            "risk_level": hd.get("risk_level", "LOW"),
                            "reason": f"AI referenced remembered {hd['type']} from past context.",
                        })

        for acc_k, acc_v in (account_profile or {}).items():
            acc_str = str(acc_v).strip()
            if acc_str and len(acc_str) >= 3:
                if re.search(rf'\b{re.escape(acc_str)}\b', ai_response, re.IGNORECASE):
                    if not any(ad.get("raw_value", "").lower() == acc_str.lower() for ad in ai_dets):
                        ai_dets.append({
                            "type": f"ACCOUNT_{acc_k.upper()}",
                            "category": "ACCOUNT_DATA",
                            "raw_value": acc_str,
                            "masked_value": acc_str,
                            "base_score": 3,
                            "risk_level": "MEDIUM",
                            "reason": f"AI referenced account profile {acc_k}.",
                        })

        # Classify user prompt intent (Generic vs Personal question)
        is_generic_question = any(re.search(p, user_message.lower()) for p in [
            r'\b(?:\d+\s*[\+\-\*\/]\s*\d+|what\s+is\s+\d+|math|calculate)\b',
            r'\b(?:what\s+is\s+the\s+capital|who\s+wrote|define|explain\s+how|weather\s+in)\b',
            r'\b(?:translate|convert|code\s+for|factorial|fibonacci)\b',
        ])

        evaluated_items = []
        has_unexpected_personalization = False
        unnecessary_exposure = False

        for ad in ai_dets:
            val_lower = str(ad.get("raw_value", "")).lower()
            a_type = ad["type"]

            # 1. Source Determination
            if (val_lower in user_raw_vals or a_type in user_raw_types or val_lower in user_message.lower()) and val_lower:
                source = "Current user message"
                source_risk = 0
                expected = True
            elif val_lower in history_vals or a_type in history_types:
                source = "Previous conversation memory"
                source_risk = 3
                expected = False
                has_unexpected_personalization = True
            elif val_lower in account_vals or any(k in val_lower for k in account_keys):
                source = "Account/profile information"
                source_risk = 3
                expected = False
                has_unexpected_personalization = True
            else:
                source = "Inferred / Model Generated"
                source_risk = 1
                expected = True

            # 2. Necessity Check
            if is_generic_question and not expected:
                necessity = "Unnecessary"
                unnecessary_exposure = True
            elif is_generic_question:
                necessity = "Unnecessary"
            elif expected:
                necessity = "Relevant"
            else:
                necessity = "Unexpected"

            # 3. Individual Risk
            ind_level = ad.get("risk_level", "LOW")
            ind_score = ad.get("base_score", 1)

            evaluated_items.append({
                "type": ad["type"],
                "category": ad.get("category", "PERSONAL_DATA"),
                "value": ad.get("masked_value", ad.get("raw_value")),
                "source": source,
                "source_risk": source_risk,
                "individual_risk": ind_level,
                "individual_score": ind_score,
                "necessity": necessity,
                "is_unexpected": not expected,
                "reason": ad.get("reason", ""),
            })

        # Multi-factor score formula aligned with Personal Information Privacy Risk Analyzer:
        # PRIVACY RISK = SENSITIVITY + IDENTIFIABILITY + COMBINATION RISK + SOURCE RISK + UNEXPECTED CONTEXT USE + POTENTIAL HARM
        if evaluated_items:
            base_s = max(item["individual_score"] for item in evaluated_items)
            comb_factor = 1 if len(evaluated_items) >= 2 else 0
            unexpected_factor = 2 if has_unexpected_personalization else 0
            unnecessary_factor = 1 if unnecessary_exposure else 0

            # Direct credentials / high-risk identifiers retain their full severity
            if any(item["individual_risk"] == "CRITICAL" for item in evaluated_items):
                final_calc_score = 10
            elif any(item["individual_risk"] == "HIGH" for item in evaluated_items):
                final_calc_score = min(10, max(7, base_s + comb_factor + unexpected_factor + unnecessary_factor))
            else:
                final_calc_score = min(10, base_s + comb_factor + unexpected_factor + unnecessary_factor)

            final_level = next(lvl for min_s, max_s, lvl, _, _ in cls.RISK_LEVEL_THRESHOLDS if min_s <= final_calc_score <= max_s)
        else:
            final_calc_score = 0
            final_level = "MINIMAL"

        # Construct structured explanation
        if unnecessary_exposure or has_unexpected_personalization:
            privacy_concern = (
                "Unexpected personal context exposure: The AI introduced personal information (such as name or location) "
                "that was not provided in the current prompt and was unnecessary to answer the query. "
                "Retrieving personal context from memory without user expectation creates privacy leakage."
            )
        elif evaluated_items:
            privacy_concern = (
                f"Personal information detected ({len(evaluated_items)} items). "
                f"Evaluation: Sensitivity ({final_level}), Necessity ({evaluated_items[0]['necessity']})."
            )
        else:
            privacy_concern = "No personal information leakage or unexpected memory retrieval detected in AI response."

        return {
            "has_leakage": len(evaluated_items) > 0,
            "has_unexpected_personalization": has_unexpected_personalization,
            "is_unnecessary_exposure": unnecessary_exposure,
            "final_risk_score": final_calc_score,
            "final_risk_level": final_level,
            "badge": next(b for min_s, max_s, _, b, _ in cls.RISK_LEVEL_THRESHOLDS if min_s <= final_calc_score <= max_s),
            "evaluated_items": evaluated_items,
            "privacy_concern": privacy_concern,
        }

    # ── 7. MASTER MESSAGE PRIVACY ANALYSIS METHOD ────────────────────────────

    @classmethod
    def analyze_message(
        cls,
        text: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main API entrypoint:
          1. Detects sensitive disclosures in user text.
          2. Evaluates context (General inquiry vs. personal disclosure).
          3. Calculates individual and cross-message cumulative combination risk.
          4. Returns structured privacy_analysis payload.
        """
        if not text or not text.strip():
            return {
                "has_privacy_risk": False,
                "overall_risk": {"level": "MINIMAL", "score": 0},
                "detections": [],
                "combined_exposure": {"level": "MINIMAL", "score": 0, "reason": None},
                "recommendations": [],
                "masked_text": text,
            }

        detections = cls.detect_sensitive_information(text)
        combined_info = cls.calculate_combined_risk(detections, chat_history)

        final_score = combined_info["score"]
        final_level = combined_info["level"]
        has_risk = final_score >= 2 and len(detections) > 0

        # Build recommendations list
        recommendations = []
        for d in detections:
            act = d.get("action")
            if act and act not in recommendations:
                recommendations.append(act)

        if combined_info["is_multi_turn_escalated"]:
            recommendations.append("Multiple identifying details have been shared across this chat. Avoid adding further contact or identity data.")

        # Format detection objects for API response
        formatted_detections = []
        for d in detections:
            formatted_detections.append({
                "type": d["type"],
                "category": d["category"],
                "masked_value": d["masked_value"],
                "risk_level": d["risk_level"],
                "risk_score": d["base_score"],
                "reason": d["reason"],
                "recommended_action": d["action"],
            })

        return {
            "has_privacy_risk": has_risk,
            "overall_risk": {
                "level": final_level,
                "score": final_score,
                "badge": next(b for min_s, max_s, _, b, _ in cls.RISK_LEVEL_THRESHOLDS if min_s <= final_score <= max_s),
            },
            "detections": formatted_detections,
            "combined_exposure": {
                "level": combined_info["level"],
                "score": combined_info["score"],
                "reason": combined_info["reason"],
                "is_escalated": combined_info["is_multi_turn_escalated"],
            },
            "recommendations": recommendations,
            "total_sensitive_items": len(detections),
            "sanitized_text": cls.sanitize_text(text, mode="REDACT"),
            "masked_text": cls.sanitize_text(text, mode="MASK"),
        }

    # ── 8. STRUCTURED PRIVACY RISK REPORT GENERATOR ──────────────────────────

    @classmethod
    def generate_privacy_report(
        cls,
        user_message: str,
        ai_response: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        account_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates the exact standardized Privacy Risk Report:
          ### INFORMATION DETECTED
          ### SOURCE
          ### INDIVIDUAL RISK
          ### COMBINATION RISK
          ### NECESSITY
          ### UNEXPECTED PERSONALIZATION
          ### PRIVACY CONCERN
          ### FINAL RISK SCORE
        """
        leakage = cls.analyze_ai_response_leakage(user_message, ai_response, chat_history, account_profile)
        items = leakage["evaluated_items"]

        if not items:
            info_det = "None detected (No personal information exposed)"
            sources = "N/A"
            ind_risk = "None"
            comb_risk = "No combination risk"
            necessity = "N/A"
            unexp_str = "No"
        else:
            info_det = "\n".join([f"* {item['type'].replace('_', ' ').title()}: {item['value']}" for item in items])
            sources = ", ".join(list(dict.fromkeys([item["source"] for item in items])))
            ind_risk = ", ".join([f"{item['type']}: {item['individual_risk']}" for item in items])
            comb_risk = "Elevated due to multi-attribute correlation" if len(items) >= 2 else "Individual attribute alone"
            necessity = ", ".join(list(dict.fromkeys([item["necessity"] for item in items])))
            unexp_str = "Yes" if leakage["has_unexpected_personalization"] else "No"

        score_badge = leakage["badge"]

        # User-friendly simple language guidance
        what_det = ", ".join([item["type"].replace("_", " ").title() for item in items]) if items else "No personal details"
        why_risky = leakage["privacy_concern"]
        what_could_happen = "Unexpected personal context retrieval or data combination can lead to unauthorized profiling, identity tracking, or user surprise." if items else "No privacy harm identified."
        what_ai_should_do = "The AI should answer the direct question without introducing extraneous personal details or unprompted memory retrieval." if leakage["has_unexpected_personalization"] else "Maintain current safe privacy posture."

        report = f"""### INFORMATION DETECTED
{info_det}

### SOURCE
{sources}

### INDIVIDUAL RISK
{ind_risk}

### COMBINATION RISK
{comb_risk}

### NECESSITY
{necessity}

### UNEXPECTED PERSONALIZATION
{unexp_str}

### PRIVACY CONCERN
{leakage['privacy_concern']}

### FINAL RISK SCORE
{score_badge}

---

### SUMMARY EXPLANATION
* **What information was detected?**: {what_det}
* **Why is it risky or not risky?**: {why_risky}
* **What could happen?**: {what_could_happen}
* **What should the AI do instead?**: {what_ai_should_do}"""

        return report

