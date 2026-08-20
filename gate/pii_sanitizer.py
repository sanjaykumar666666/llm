"""
Backward-compatible wrapper for gate.pii_sanitizer.
Delegates cleanly to privacy_engine.sanitizer.
"""

from typing import Tuple, List, Dict, Any
from privacy_engine.sanitizer import PrivacySanitizer, PII_PATTERNS


class PIISanitizer:
    """
    Backward-compatible alias for PIISanitizer.
    """

    def __init__(self):
        self._engine = PrivacySanitizer()

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        return self._engine.sanitize(text)

    def sanitize_text(self, text: str, mode: str = "REDACT") -> Dict[str, Any]:
        return self._engine.sanitize_text(text, mode=mode)
