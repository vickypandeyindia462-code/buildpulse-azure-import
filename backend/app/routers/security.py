from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.agents import security_check

router = APIRouter(prefix="/security", tags=["security"])


@router.post("/scan")
def scan_text(payload: Dict[str, Any]):
    text = payload.get("text")
    if text is None:
        raise HTTPException(status_code=400, detail="text is required")
    res = security_check.run_sync(text, {})
    return res
