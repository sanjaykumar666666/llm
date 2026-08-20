"""
Settings Configuration Route.
File: backend/routes/settings.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class SettingsModel(BaseModel):
    sanitization_mode: Optional[str] = "REDACT"
    warning_threshold: Optional[int] = 35
    block_threshold: Optional[int] = 75

@router.get("/settings")
def get_settings():
    return {
        "sanitization_mode": "REDACT",
        "warning_threshold": 35,
        "block_threshold": 75,
        "status": "active"
    }

@router.post("/settings")
def update_settings(settings: SettingsModel):
    return {
        "message": "Settings updated successfully",
        "data": settings
    }
