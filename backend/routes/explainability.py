"""
Explainability Route.
File: backend/routes/explainability.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.services.shap_explainer import SHAPExplainer

router = APIRouter()


class ExplainabilityRequest(BaseModel):
    modality: Optional[str] = "Text"
    content: Optional[str] = ""


@router.post("/explainability")
def explainability_endpoint(req: ExplainabilityRequest) -> Dict[str, Any]:
    """
    Explainability API endpoint.
    Returns token attributions and feature contributions for text input.
    Returns explicit 'not_available' for multimodal inputs where explainability models are not yet connected.
    """
    text = (req.content or "").strip()
    modality = req.modality or "Text"

    if not text:
        return {
            "explainability_status": "empty_input",
            "modality": modality,
            "token_attributions": [],
            "feature_contributions": [],
            "message": "No content provided for explainability analysis."
        }

    if modality.lower() in ("image", "video", "youtube"):
        return {
            "explainability_status": "not_available",
            "modality": modality,
            "token_attributions": [],
            "feature_contributions": [],
            "message": f"Multimodal explainability for {modality} is not available in the current pipeline."
        }

    shap_data = SHAPExplainer.explain_prompt(text, 0.0)
    return {
        "explainability_status": "available",
        "modality": "Text",
        "token_attributions": shap_data.get("token_attributions", []),
        "feature_contributions": shap_data.get("feature_contributions", []),
        "top_features": shap_data.get("feature_contributions", []),
        "message": "Token and feature attributions evaluated."
    }
