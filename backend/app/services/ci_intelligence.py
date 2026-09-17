"""Safe GitHub Actions collection and deterministic CI failure analysis."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Any

import requests

from backend.agents.security_check import scan_and_redact


MAX_LOG_DOWNLOAD_BYTES = 2_000_000
MAX_LOG_EXCERPT_CHARS = 12_000

SERVICE_BY_JOB = {
    "loan": "loan-service",
    "payment": "payments-api",
    "gateway": "api-gateway",
    "identity": "identity-service",
}

FAILURE_PATTERNS = (
    ("test", re.compile(r"\b(failed|assertionerror|pytest|tests?/)\b", re.I)),
    ("dependency", re.compile(r"\b(could not resolve|dependency|no matching distribution|module not found)\b", re.I)),
    ("configuration", re.compile(r"\b(config|configuration|environment variable|expected .{0,30} got)\b", re.I)),
    ("contract", re.compile(r"\b(contract|schema|openapi|breaking change)\b", re.I)),
    ("timeout", re.compile(r"\b(timeout|timed out|deadline exceeded)\b", re.I)),
    ("deployment", re.compile(r"\b(deploy|rollout|container failed|health check)\b", re.I)),
    ("build", re.compile(r"\b(build failed|compilation|compiler error|docker build)\b", re.I)),
)


def service_for_job(job_name: str) -> str | None:
    lowered = job_name.lower()
    return next((service for token, service in SERVICE_BY_JOB.items() if token in lowered), None)


def classify_failure(log_excerpt: str, failed_step: str = "") -> dict[str, Any]:
    evidence = f"{failed_step}\n{log_excerpt}"
    matches = [name for name, pattern in FAILURE_PATTERNS if pattern.search(evidence)]
    failure_class = matches[0] if matches else "unknown"
    score = min(95, 45 + (20 if log_excerpt.strip() else 0) + (15 if failed_step.strip() else 0) + min(15, len(matches) * 5))
    return {
        "class": failure_class,
        "confidence": {
            "score": score,
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "drivers": [
                {"signal": "sanitized job log available", "points": 20 if log_excerpt.strip() else 0},
                {"signal": "failed step identified", "points": 15 if failed_step.strip() else 0},
                {"signal": "failure signatures matched", "points": min(15, len(matches) * 5)},
            ],
        },
    }


def extract_log_text(content: bytes, content_type: str = "") -> str:
    """Extract bounded UTF-8 text from GitHub's text or ZIP log response."""
    content = content[:MAX_LOG_DOWNLOAD_BYTES]
    if content.startswith(b"PK") or "zip" in content_type.lower():
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                chunks = []
                for info in archive.infolist():
                    if info.is_dir() or info.file_size > MAX_LOG_DOWNLOAD_BYTES:
                        continue
                    chunks.append(archive.read(info)[:MAX_LOG_DOWNLOAD_BYTES].decode("utf-8", errors="replace"))
                text = "\n".join(chunks)
        except (zipfile.BadZipFile, OSError):
            text = ""
    else:
        text = content.decode("utf-8", errors="replace")
    # Prefer the tail: test runners and build tools normally emit the actionable
    # summary there, while still enforcing a strict model-context boundary.
    return text[-MAX_LOG_EXCERPT_CHARS:]


@dataclass
class GitHubActionsClient:
    owner: str
    repo: str
    token: str = ""
    session: Any = requests

    @property
    def base_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def _get(self, url: str, *, params: dict[str, Any] | None = None, allow_public_retry: bool = True):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code >= 400 and self.token and allow_public_retry:
            headers.pop("Authorization", None)
            response = self.session.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response

    def recent_runs(self) -> list[dict[str, Any]]:
        response = self._get(f"{self.base_url}/actions/runs", params={"per_page": 10})
        return [{
            "id": str(run["id"]), "workflow": run["name"], "status": run["status"],
            "conclusion": run.get("conclusion"), "started_at": run.get("run_started_at"),
            "url": run["html_url"], "branch": run.get("head_branch"), "source": "github",
        } for run in response.json().get("workflow_runs", [])]

    def failed_runs(self) -> list[dict[str, Any]]:
        response = self._get(f"{self.base_url}/actions/runs", params={"status": "completed", "per_page": 20})
        failures = []
        for run in response.json().get("workflow_runs", []):
            if run.get("conclusion") != "failure":
                continue
            jobs = self._get(f"{self.base_url}/actions/runs/{run['id']}/jobs").json().get("jobs", [])
            for job in [item for item in jobs if item.get("conclusion") == "failure"]:
                failed_step = next((step.get("name") for step in job.get("steps", []) if step.get("conclusion") == "failure"), "Inspect GitHub job log")
                failures.append({
                    "id": str(job["id"]), "run_id": str(run["id"]), "workflow": run["name"],
                    "job": job.get("name", run["name"]), "service_id": service_for_job(job.get("name", "")),
                    "status": run["status"], "conclusion": "failure", "failed_step": failed_step,
                    "started_at": run.get("run_started_at"), "url": job.get("html_url", run["html_url"]),
                    "branch": run.get("head_branch"), "pr_number": (run.get("pull_requests") or [{}])[0].get("number"),
                    "source": "github", "log_available": bool(self.token),
                })
        return failures

    def failed_run(self, job_id: str) -> dict[str, Any] | None:
        """Resolve one selected job directly so analysis does not depend on a changing list call."""
        response = self._get(f"{self.base_url}/actions/jobs/{job_id}")
        job = response.json()
        if job.get("conclusion") != "failure":
            return None
        run = self._get(job["run_url"]).json() if job.get("run_url") else {}
        failed_step = next(
            (step.get("name") for step in job.get("steps", []) if step.get("conclusion") == "failure"),
            "Inspect GitHub job log",
        )
        return {
            "id": str(job["id"]), "run_id": str(run.get("id") or ""),
            "workflow": run.get("name") or job.get("name", "GitHub Actions"),
            "job": job.get("name", "GitHub Actions"), "service_id": service_for_job(job.get("name", "")),
            "status": job.get("status"), "conclusion": "failure", "failed_step": failed_step,
            "started_at": job.get("started_at") or run.get("run_started_at"),
            "url": job.get("html_url") or run.get("html_url"), "branch": run.get("head_branch"),
            "pr_number": (run.get("pull_requests") or [{}])[0].get("number"),
            "source": "github", "log_available": bool(self.token),
        }

    def sanitized_job_log(self, job_id: str) -> dict[str, Any]:
        if not self.token:
            return {"excerpt": "", "findings_count": 0, "redacted": False, "available": False}
        response = self._get(f"{self.base_url}/actions/jobs/{job_id}/logs", allow_public_retry=False)
        text = extract_log_text(response.content, response.headers.get("content-type", ""))
        security = scan_and_redact(text)
        return {
            "excerpt": security["redacted_text"], "findings_count": len(security["findings"]),
            "redacted": bool(security["findings"]), "available": bool(text),
        }
