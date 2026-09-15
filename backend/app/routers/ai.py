"""Compatibility route for clients that still call the original AI endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.agent_runtime import BuildPulseAgentRuntime


router = APIRouter(prefix="/ai", tags=["legacy-ai"], deprecated=True)


class LegacyChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    service_id: str | None = None


@router.post("/chat", deprecated=True)
def ai_chat(payload: LegacyChatRequest) -> dict[str, Any]:
    """Route legacy requests through the canonical Copilot runtime."""
    try:
        result = BuildPulseAgentRuntime().chat(payload.query, payload.service_id)
        result["deprecated"] = "Use POST /api/copilot/chat with the 'question' field."
        return result
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Unable to resolve the requested service context") from error
