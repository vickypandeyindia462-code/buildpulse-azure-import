from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Query

from ..config import Settings
from ..services.confluence_knowledge import ConfluenceClient
from ..services.knowledge_base import KnowledgeBase
from ..services.repository_intelligence import RepositoryIntelligence
from ..services.retrieval_store import RetrievalStore
from ..services.unified_ingestion import UnifiedIngestionService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def confluence() -> ConfluenceClient:
    settings = Settings.from_env()
    return ConfluenceClient(settings.confluence_base_url, settings.confluence_space_id, settings.confluence_space_key, settings.jira_email, settings.jira_api_token)


def retrieval() -> RetrievalStore:
    repository = RepositoryIntelligence()
    return RetrievalStore(KnowledgeBase(repository.repository_path))


@router.get("/status")
def status() -> dict[str, Any]:
    try:
        return {"confluence": confluence().status(), "retrieval": retrieval().status()}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Confluence unavailable") from exc


@router.post("/index")
def index_repository() -> dict[str, Any]:
    """Idempotently index approved repository documentation."""
    try:
        return retrieval().index_repository()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge indexing failed: {type(exc).__name__}") from exc


@router.post("/sync")
def sync_all_sources() -> dict[str, Any]:
    """Read and index every configured source without mutating upstream systems."""
    try:
        return UnifiedIngestionService().sync()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge synchronization failed: {type(exc).__name__}") from exc


@router.get("/search")
def search(q: str = Query(default="", max_length=500), source: str = "all") -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    retrieval_status: dict[str, Any] = {}
    if source in {"all", "repository"}:
        store = retrieval()
        retrieval_status = store.status()
        if retrieval_status["indexed_documents"]:
            repository_items = store.search(q or "architecture runbook incident", limit=20)
            if source == "repository":
                repository_items = [item for item in repository_items if item.get("source") == "repository"]
        else:
            repository_items = store.knowledge.search(q or "architecture runbook incident", limit=20)
        items.extend({"source": "repository", "url": None, "snippet": item.get("content", "")[:260], **item} for item in repository_items)
    indexed_confluence = bool((retrieval_status.get("source_counts") or {}).get("confluence"))
    if source == "confluence" or (source == "all" and not indexed_confluence):
        try:
            items.extend(confluence().search(q, limit=20))
        except requests.RequestException:
            if source == "confluence":
                raise HTTPException(status_code=502, detail="Confluence search unavailable")
    items.sort(key=lambda item: item.get("score") or 0, reverse=True)
    return {"items": items[:30], "total": len(items[:30]), "sources": sorted(set(item["source"] for item in items))}
