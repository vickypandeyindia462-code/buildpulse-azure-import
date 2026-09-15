from typing import Any

import requests
from fastapi import APIRouter, HTTPException

from ..config import Settings
from ..services.jira_intelligence import JiraClient

router = APIRouter(prefix="/api/jira", tags=["jira"])


def client() -> JiraClient:
    settings = Settings.from_env()
    return JiraClient(settings.jira_base_url, settings.jira_project_key, settings.jira_email, settings.jira_api_token)


@router.get("/status")
def jira_status() -> dict[str, Any]:
    try:
        return client().status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Jira connection unavailable") from exc


@router.get("/issues")
def jira_issues() -> dict[str, Any]:
    try:
        items = client().issues()
        return {"items": items, "total": len(items), "source": "jira"}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Jira issues unavailable") from exc


@router.get("/dashboard")
def jira_dashboard() -> dict[str, Any]:
    try:
        return client().dashboard()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Jira dashboard unavailable") from exc


@router.get("/historical-incidents")
def historical_incidents() -> dict[str, Any]:
    try:
        items = client().historical_incidents()
        return {"items": items, "total": len(items), "source": "jira"}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Jira historical incidents unavailable") from exc


@router.get("/similar-incidents/{issue_key}")
def similar_incidents(issue_key: str) -> dict[str, Any]:
    try:
        jira = client()
        current = next((item for item in jira.issues() if item["key"] == issue_key), None)
        if not current:
            raise HTTPException(status_code=404, detail="Jira issue not found")
        query = f"{current['summary']} {current['description']}"
        matches = jira.similar_incidents(query, current.get("service_id"))
        return {"issue": current, "matches": matches, "total": len(matches), "source": "jira"}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Jira similarity analysis unavailable") from exc
