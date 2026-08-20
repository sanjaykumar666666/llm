"""
AI Trust Chat — Policy, Receipt, and Events API Routes
File: backend/routes/policies.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import JSONResponse
from backend.services.policy_engine import (
    get_all_policies, create_policy, update_policy,
    delete_policy, toggle_policy, reset_to_defaults,
)
from backend.services.trust_receipt import get_all_receipts, get_receipt_by_id, format_receipt_text
from backend.services.security_events import get_all_events, get_event_summary

router = APIRouter()


# ── POLICIES ──────────────────────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    name: str
    condition: str
    condition_detail: str
    action: str
    enabled: Optional[bool] = True
    priority: Optional[int] = 99


@router.get("/policies")
def list_policies():
    return {"success": True, "policies": get_all_policies()}


@router.post("/policies")
def add_policy(req: PolicyCreate):
    p = create_policy(**req.dict())
    return {"success": True, "policy": p}


@router.put("/policies/{policy_id}")
def edit_policy(policy_id: str, req: dict):
    p = update_policy(policy_id, **req)
    if p:
        return {"success": True, "policy": p}
    return JSONResponse(status_code=404, content={"success": False, "error": "Policy not found."})


@router.delete("/policies/{policy_id}")
def remove_policy(policy_id: str):
    success = delete_policy(policy_id)
    if success:
        return {"success": True}
    return JSONResponse(status_code=404, content={"success": False, "error": "Policy not found."})


@router.post("/policies/{policy_id}/toggle")
def toggle(policy_id: str):
    p = toggle_policy(policy_id)
    if p:
        return {"success": True, "policy": p}
    return JSONResponse(status_code=404, content={"success": False, "error": "Policy not found."})


@router.post("/policies/reset")
def reset_policies():
    reset_to_defaults()
    return {"success": True, "message": "Policies reset to defaults."}


# ── TRUST RECEIPTS ─────────────────────────────────────────────────────────────

@router.get("/receipts")
def list_receipts(limit: int = 50):
    receipts = get_all_receipts()[:limit]
    return {"success": True, "receipts": receipts, "total": len(receipts)}


@router.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: str):
    r = get_receipt_by_id(receipt_id)
    if r:
        return {"success": True, "receipt": r, "formatted": format_receipt_text(r)}
    return JSONResponse(status_code=404, content={"success": False, "error": "Receipt not found."})


# ── SECURITY EVENTS ────────────────────────────────────────────────────────────

@router.get("/events")
def list_events(
    filter_type: Optional[str] = None,
    filter_severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
):
    events = get_all_events(filter_type=filter_type, filter_severity=filter_severity, search=search, limit=limit)
    summary = get_event_summary()
    return {"success": True, "events": events, "summary": summary}
