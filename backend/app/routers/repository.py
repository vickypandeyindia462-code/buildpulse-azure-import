import subprocess
import requests

from fastapi import APIRouter, HTTPException

from ..services.repository_intelligence import RepositoryIntelligence
from ..services.jira_intelligence import JiraClient
from ..config import Settings


router = APIRouter(prefix="/api", tags=["repository-intelligence"])


def intelligence() -> RepositoryIntelligence:
    return RepositoryIntelligence()


def _github_open_prs(settings: Settings) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/pulls"
    response = requests.get(url, headers=headers, params={"state": "open", "per_page": 50}, timeout=15)
    if response.status_code >= 400 and settings.github_token:
        response = requests.get(url, headers={"Accept": "application/vnd.github+json"}, params={"state": "open", "per_page": 50}, timeout=15)
    response.raise_for_status()
    return [{
        "number": item["number"], "title": item["title"], "state": item["state"],
        "branch": item["head"]["ref"], "base": item["base"]["ref"], "url": item["html_url"],
        "author": item["user"]["login"], "created_at": item["created_at"], "updated_at": item["updated_at"],
        "draft": item.get("draft", False), "source": "github",
    } for item in response.json()]


@router.get("/pull-requests")
def list_pull_requests():
    try:
        items = _github_open_prs(Settings.from_env())
        return {"items": items, "total": len(items), "source": "github"}
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail="GitHub pull requests unavailable") from error


@router.get("/services")
def list_services():
    try:
        services = intelligence().services()
        return {"items": services, "total": len(services)}
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/services/{service_id}")
def get_service(service_id: str):
    try:
        return intelligence().service(service_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Service not found: {service_id}") from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/pull-requests/{pr_number}/risk")
def get_pull_request_risk(pr_number: int):
    try:
        settings = Settings.from_env()
        repository = intelligence()
        try:
            result = repository.pull_request_risk(pr_number)
        except KeyError:
            live_pr = next((item for item in _github_open_prs(settings) if item["number"] == pr_number), None)
            if not live_pr:
                raise
            result = repository.assess_change(live_pr["branch"], pr_number=pr_number, review_status="pending", test_status="passed")
            result["title"] = live_pr["title"]
            result["url"] = live_pr["url"]
        jira = JiraClient(settings.jira_base_url, settings.jira_project_key, settings.jira_email, settings.jira_api_token)
        if jira.ready:
            try:
                query = " ".join([result["service"], *result["changed_files"], *(driver["factor"] for driver in result["drivers"])])
                matches = jira.similar_incidents(query, result["service_id"], limit=2)
                result["historical_incidents"] = matches
                if matches:
                    points = 15
                    result["drivers"].append({"factor": "Similar change caused a resolved production incident", "points": points, "jira_issue": matches[0]["key"], "similarity": matches[0]["similarity_score"]})
                    result["risk_score"] = min(100, result["risk_score"] + points)
                    result["risk_level"] = repository._risk_level(result["risk_score"])
                    result["recommended_checks"].append(f"Review {matches[0]['key']} and confirm its preventive controls before merge.")
            except requests.RequestException:
                result["historical_incidents"] = []
        return result
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/portfolio/overview")
def get_portfolio_overview():
    try:
        return intelligence().portfolio_overview()
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
