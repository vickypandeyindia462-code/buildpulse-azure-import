from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Query

from ..config import Settings
from ..services.confluence_knowledge import ConfluenceClient
from ..services.knowledge_base import KnowledgeBase
from ..services.repository_intelligence import RepositoryIntelligence

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def confluence() -> ConfluenceClient:
    settings = Settings.from_env()
    return ConfluenceClient(settings.confluence_base_url, settings.confluence_space_id, settings.confluence_space_key, settings.jira_email, settings.jira_api_token)


@router.get("/status")
def status() -> dict[str, Any]:
    try:
        return confluence().status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Confluence unavailable") from exc


@router.get("/search")
def search(q: str = Query(default="", max_length=500), source: str = "all") -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if source in {"all", "repository"}:
        kb = KnowledgeBase(RepositoryIntelligence().repository_path)
        items.extend({**item, "source": "repository", "url": None, "snippet": item.get("content", "")[:260]} for item in kb.search(q or "architecture runbook incident", limit=20))
    if source in {"all", "confluence"}:
        try:
            items.extend(confluence().search(q, limit=20))
        except requests.RequestException:
            if source == "confluence":
                raise HTTPException(status_code=502, detail="Confluence search unavailable")
    items.sort(key=lambda item: item.get("score") or 0, reverse=True)
    return {"items": items[:30], "total": len(items[:30]), "sources": sorted(set(item["source"] for item in items))}
