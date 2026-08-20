"""
Explainability Route.
File: backend/routes/explainability.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.mock_ml_engine import MockMLEngineService

router = APIRouter()

class ExplainabilityRequest(BaseModel):
    modality: Optional[str] = "Text"
    content: Optional[str] = ""

@router.post("/explainability")
def explainability_endpoint(req: ExplainabilityRequest):
    return MockMLEngineService.process_explainability(req.modality, req.content)
