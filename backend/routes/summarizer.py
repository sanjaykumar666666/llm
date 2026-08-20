"""
Text Summarizer Route.
File: backend/routes/summarizer.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.mock_ml_engine import MockMLEngineService

router = APIRouter()

class SummarizeRequest(BaseModel):
    text: str
    summary_length: Optional[str] = "medium"

@router.post("/summarize")
def summarizer_endpoint(req: SummarizeRequest):
    return MockMLEngineService.process_summarize(req.text, req.summary_length)
