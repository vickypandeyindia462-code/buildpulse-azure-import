from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import os
import requests
import base64
import json
from datetime import datetime
from ..config import Settings

router = APIRouter(prefix="/submit", tags=["submit"])

# Configure repo via env or default to user's repo provided earlier
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_owner_repo():
    """Resolve owner/repo from environment at call time."""
    settings = Settings.from_env()
    return settings.github_owner, settings.github_repo

GITHUB_API = "https://api.github.com"


def gh_headers():
    token = os.getenv("GITHUB_TOKEN", GITHUB_TOKEN)
    if not token:
        raise RuntimeError("GITHUB_TOKEN not configured in environment")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "buildpulse"}


@router.post("/pr")
def submit_create_pr(payload: Any = Body(...)):
    """Create a branch, add the submission JSON file under data/submissions/, and open a PR to main.

    Payload can be either a list of document dicts (legacy) or an object like:
      {"docs": [...], "reviewers": ["user1","user2"]}
    """
    # normalize incoming payload
    if isinstance(payload, list):
        docs = payload
        reviewers = None
    elif isinstance(payload, dict):
        docs = payload.get("docs") or payload.get("documents") or payload.get("items") or payload.get("payload")
        if docs is None:
            # maybe the dict is itself a single doc
            docs = [payload]
        reviewers = payload.get("reviewers")
    else:
        raise HTTPException(status_code=400, detail="Invalid payload")

    owner, repo = get_owner_repo()
    # Ensure a usable fallback for local testing if env parsing fails
    if not owner or not repo:
        owner, repo = "vickypandeyindia462-code", "Hackathon-26"

    try:
        # get repository info to determine default branch
        r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=gh_headers())
        r.raise_for_status()
        repo_info = r.json()
        base_branch = repo_info.get("default_branch", "main")

        # get base branch sha
        r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/ref/heads/{base_branch}", headers=gh_headers())
        r.raise_for_status()
        base_sha = r.json()["object"]["sha"]

        # create new branch
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        branch_name = f"ingest/auto-{ts}"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
        r = requests.post(f"{GITHUB_API}/repos/{owner}/{repo}/git/refs", headers=gh_headers(), json=payload)
        r.raise_for_status()

        # prepare file content
        filename = f"data/submissions/auto-{ts}.json"
        content_bytes = json.dumps(docs, ensure_ascii=False, indent=2).encode("utf-8")
        b64 = base64.b64encode(content_bytes).decode("ascii")

        put_payload = {
            "message": f"chore: add ingest submission {ts}",
            "content": b64,
            "branch": branch_name
        }
        r = requests.put(f"{GITHUB_API}/repos/{owner}/{repo}/contents/{filename}", headers=gh_headers(), json=put_payload)
        r.raise_for_status()

        # create PR
        pr_payload = {
            "title": f"Ingest submission: auto-{ts}",
            "head": branch_name,
            "base": base_branch,
            "body": "Automated ingest submission created by BuildPulse UI. Please review and merge."
        }
        r = requests.post(f"{GITHUB_API}/repos/{owner}/{repo}/pulls", headers=gh_headers(), json=pr_payload)
        r.raise_for_status()
        pr = r.json()

        # optionally request reviewers (GitHub API separate endpoint)
        try:
            if reviewers and isinstance(reviewers, (list, tuple)) and len(reviewers) > 0:
                pr_number = pr.get("number")
                if pr_number:
                    rev_payload = {"reviewers": reviewers}
                    rr = requests.post(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers", headers=gh_headers(), json=rev_payload)
                    # ignore reviewer errors but log them
        except Exception:
            pass

        return {"pr_url": pr.get("html_url"), "branch": branch_name, "file": filename}
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except requests.HTTPError as he:
        # try to return helpful message
        detail = None
        try:
            detail = he.response.json()
        except Exception:
            detail = str(he)
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
