"""
Text Processing, Multi-Entity Detection, and Shannon Entropy Security Analysis Engine.
File Location: processing/text_processor.py
"""

import re
import math
from typing import Dict, Any, List


class TextProcessor:
    """
    Handles text cleaning, normalization, Shannon entropy estimation, 
    and comprehensive 15+ PII/Credential pattern scanning.
    """

    def __init__(self):
        # Enterprise-Grade Regular Expression Patterns
        self.regex_patterns = {
            "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "PHONE_NUMBER": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "GOVERNMENT_ID_SSN": r"\b\d{3}-\d{2}-\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]{1}\b",  # US SSN + IN PAN
            "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "IBAN_ACCOUNT": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
            "PASSPORT_NUMBER": r"\b[A-Z]{1,2}[0-9]{6,9}\b",
            "AWS_KEY": r"\bAKIA[0-9A-Z]{16}\b",
            "GITHUB_TOKEN": r"\b(ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}\b",
            "OPENAI_API_KEY": r"\bsk-[a-zA-Z0-9]{32,48}\b",
            "GENERIC_SECRET_KEY": r"\bsk_live_[0-9a-zA-Z]{24}\b",
            "JWT_TOKEN": r"\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b",
            "PRIVATE_KEY_BLOCK": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            "CREDENTIAL_PASSWORD": r"\b(?:password|passwd|pwd|secret|api_key|access_token)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?",
            "HEALTH_ID_MRN": r"\bMRN-?\d{6,10}\b|\bMED-?\d{5,9}\b",
        }

        # Risk weights for different entity types
        self.entity_severity = {
            "PRIVATE_KEY_BLOCK": 1.0,
            "AWS_KEY": 1.0,
            "GITHUB_TOKEN": 1.0,
            "OPENAI_API_KEY": 1.0,
            "GENERIC_SECRET_KEY": 0.95,
            "CREDENTIAL_PASSWORD": 0.95,
            "JWT_TOKEN": 0.90,
            "CREDIT_CARD": 0.85,
            "GOVERNMENT_ID_SSN": 0.85,
            "IBAN_ACCOUNT": 0.80,
            "HEALTH_ID_MRN": 0.75,
            "PASSPORT_NUMBER": 0.70,
            "EMAIL_ADDRESS": 0.50,
            "PHONE_NUMBER": 0.45,
            "IP_ADDRESS": 0.35,
        }

    def clean_text(self, text: str) -> str:
        """
        Normalizes input text by removing excessive whitespace.
        """
        if not text:
            return ""
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned.strip()

    def calculate_shannon_entropy(self, text: str) -> float:
        """
        Calculates Shannon entropy of text to detect high-randomness secret strings (e.g. passwords, hash keys).
        """
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return round(entropy, 3)

    def detect_pii_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans text using regex rules to identify explicit PII & credential entities.
        """
        detected = []
        if not text:
            return detected

        for entity_type, pattern in self.regex_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                val = match.group()
                severity = self.entity_severity.get(entity_type, 0.5)
                detected.append({
                    "entity_type": entity_type,
                    "value": val,
                    "start": match.start(),
                    "end": match.end(),
                    "severity": severity,
                })
        return detected

    def process(self, raw_text: str) -> Dict[str, Any]:
        """
        Executes complete text inspection pipeline.
        """
        cleaned_text = self.clean_text(raw_text)
        entities = self.detect_pii_entities(cleaned_text)
        entity_types = list(set([e["entity_type"] for e in entities]))
        entropy = self.calculate_shannon_entropy(cleaned_text)

        # Highest entity severity
        max_severity = max([e["severity"] for e in entities], default=0.0)

        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "detected_entities": entities,
            "detected_entity_types": entity_types,
            "contains_regex_pii": len(entities) > 0,
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "shannon_entropy": entropy,
            "max_entity_severity": max_severity,
        }
