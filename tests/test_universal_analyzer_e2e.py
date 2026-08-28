"""
Test Suite: Universal Social Media Content Analyzer Complete End-to-End Test.
File: tests/test_universal_analyzer_e2e.py
"""

import pytest
from backend.routes.youtube_analysis import run_social_media_pipeline


def test_complete_end_to_end_pipeline_workflow():
    """
    Verifies complete end-to-end flow:
      1. User enters URL
      2. Platform detected
      3. Metadata extracted
      4. Media analyzed
      5. Summary generated
      6. Privacy analysis
      7. Copyright risk analysis
      8. Frame analysis
      9. Recommendations generated
      10. Clean result compiled
    """
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    custom_payload = (
        "[00:05] Today we are discussing AI ethics and cybersecurity.\n"
        "[00:25] Customer contact is alex.smith@company.org and phone +1 (555) 987-6543.\n"
        "[00:50] Aadhaar verification code is 9876-5432-1098.\n"
        "[01:15] Educational summary under Creative Commons CC-BY attribution."
    )

    result = run_social_media_pipeline(test_url, custom_transcript=custom_payload)

    # 1. Verification of Status
    assert result["status"] == "success"

    # 2. Verification of Platform & Metadata
    assert result["platform"] == "YouTube"
    assert result["content_type"] == "video"
    assert "media_metadata" in result
    assert result["media_metadata"]["is_accessible"] is True

    # 3. Verification of Summary Synthesis
    assert "media_summary" in result
    assert result["media_summary"]["is_original_synthesis"] is True
    assert len(result["media_summary"]["main_topics"]) >= 2

    # 4. Verification of Privacy & PII Detections
    assert len(result["privacy_detections"]) >= 2
    det_types = [d["type"] for d in result["privacy_detections"]]
    assert "EMAIL_ADDRESS" in det_types
    assert "PHONE_NUMBER" in det_types
    assert "AADHAAR_NUMBER" in det_types

    # 5. Verification of Copyright Assessment
    assert "copyright_assessment" in result
    assert "copyright_risk_level" in result["copyright_assessment"]
    assert "safe_use_guidance" in result["copyright_assessment"]

    # 6. Verification of Sampled Frames & Beginner Explanations
    assert len(result["analyzed_frames"]) > 0
    for f in result["analyzed_frames"]:
        assert "frame_number" in f
        assert "timestamp_str" in f
        assert "privacy_risk" in f
        assert "copyright_risk" in f
        assert "recommendation" in f
        assert "beginner_explanation" in f
        assert "where" in f
        assert "why" in f
        assert "what_could_happen" in f
        assert "what_to_do" in f

    # 7. Verification of Multi-Dimensional Risk Scores
    assert "risk_breakdown" in result
    rb = result["risk_breakdown"]
    assert "privacy_risk_level" in rb
    assert "copyright_risk_level" in rb
    assert "content_risk_level" in rb
    assert "overall_risk_level" in rb

    # 8. Verification of Final Report & Legal Disclaimer
    assert "final_report" in result
    assert "disclaimer" in result
    assert "legal advice" in result["disclaimer"].lower()
