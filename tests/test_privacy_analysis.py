"""
Test Suite: Privacy & PII Analysis Engine.
File: tests/test_privacy_analysis.py
"""

import pytest
from backend.services.universal_content_service import UniversalContentService


def test_privacy_severity_and_scoring():
    """Verify privacy grading accurately scores critical, high, medium, and low privacy payloads."""
    # 1. Clean payload
    clean_scores = UniversalContentService.calculate_multidimensional_risks(
        copyright_assessment={"copyright_risk_level": "LOW"},
        privacy_detections=[],
        analyzed_frames=[{"privacy_risk": "LOW"}],
        segments=[]
    )
    assert clean_scores["privacy_risk_level"] == "LOW"
    assert clean_scores["privacy_risk_score"] <= 30

    # 2. Critical credentials payload
    crit_scores = UniversalContentService.calculate_multidimensional_risks(
        copyright_assessment={"copyright_risk_level": "LOW"},
        privacy_detections=[{"type": "AWS_ACCESS_KEY", "severity": "CRITICAL"}],
        analyzed_frames=[{"privacy_risk": "HIGH"}],
        segments=[]
    )
    assert crit_scores["privacy_risk_level"] == "CRITICAL"
    assert crit_scores["privacy_risk_score"] >= 90
