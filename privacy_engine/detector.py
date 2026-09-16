"""
Privacy Entity & Context-Aware Detector Module Alias.
File Location: privacy_engine/detector.py

Provides direct exports and backward-compatible aliases for context-aware privacy entity detection.
"""

from privacy_engine.context_detector import (
    ContextAwareEntityDetector,
    _CREDENTIAL_DISCLOSURE_PATTERNS,
    _HIGH_PERSONAL_RISK_PATTERNS,
    _MILD_PERSONAL_CONTEXT_PATTERNS,
    _EDUCATIONAL_INQUIRY_PATTERNS,
)

# Standard Aliases
ContextAwarePrivacyDetector = ContextAwareEntityDetector
PrivacyDetector = ContextAwareEntityDetector

__all__ = [
    "ContextAwareEntityDetector",
    "ContextAwarePrivacyDetector",
    "PrivacyDetector",
]
