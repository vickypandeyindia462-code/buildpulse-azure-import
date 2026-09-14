from fastapi import APIRouter
from backend.orchestrator import orchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.get("/sme")
def orchestrator_sme(query: str):
    return orchestrator.run_sme_discovery(query)
