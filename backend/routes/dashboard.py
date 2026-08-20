"""
Privacy Dashboard Metrics Route.
File: backend/routes/dashboard.py
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard/metrics")
def dashboard_metrics_endpoint():
    return {
        "total_inputs": 142,
        "safe_inputs": 94,
        "warning_inputs": 32,
        "blocked_inputs": 16,
        "privacy_risks_detected": 48,
        "prompt_injections": 12,
        "statistics_by_modality": {
            "Text Analysis": 68,
            "Image Analyzer": 34,
            "Video Analyzer": 18,
            "YouTube Analyzer": 22
        },
        "risk_distribution": {
            "Safe (0-30%)": 66,
            "Warning (31-70%)": 23,
            "Critical (71-100%)": 11
        },
        "is_mock": True
    }
