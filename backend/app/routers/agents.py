from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.agent_runtime import BuildPulseAgentRuntime


router = APIRouter(prefix="/api", tags=["agents"])


def runtime() -> BuildPulseAgentRuntime:
    return BuildPulseAgentRuntime()


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    service_id: str | None = None


@router.get("/agents/status")
def agent_status() -> dict[str, Any]:
    return runtime().status()


@router.get("/ci/failures")
def list_ci_failures() -> dict[str, Any]:
    runs = runtime().failed_runs()
    return {"items": runs, "total": len(runs)}


@router.get("/ci/runs")
def list_ci_runs() -> dict[str, Any]:
    runs = runtime().recent_runs()
    return {"items": runs, "total": len(runs)}


@router.get("/ci/failures/{run_id}/analysis")
def analyse_ci_failure(run_id: str) -> dict[str, Any]:
    try:
        return runtime().analyse_failure(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="CI run not found") from error


@router.post("/copilot/chat")
def copilot_chat(payload: ChatRequest) -> dict[str, Any]:
    return runtime().chat(payload.question, payload.service_id)
