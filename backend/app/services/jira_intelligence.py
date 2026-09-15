"""Jira Cloud read model and idempotent synthetic-demo ticket seeding."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any
import re

import requests


SERVICE_LABELS = {
    "loan-service": "Loan Service",
    "payments-api": "Payments API",
    "api-gateway": "API Gateway",
    "identity-service": "Identity Service",
}

DEMO_TICKETS = (
    ("BP-LOAN-POOL", "[System] Incident", "Loan Service connection pool configuration drift", "loan-service", "Highest", "Release 24.3 blocker: runtime pool capacity is 40 while declared configuration is 60."),
    ("BP-LOAN-RUNBOOK", "Task", "Validate Loan Service saturation recovery runbook", "loan-service", "High", "Verify rollback thresholds and load-test evidence before release approval."),
    ("BP-PAY-IDEMPOTENCY", "[System] Incident", "Payments API accepts a zero-value reservation", "payments-api", "Highest", "Contract validation permits a non-positive reservation and requires a minimal reversible fix."),
    ("BP-PAY-RETRY", "Task", "Review Payments API idempotency retry controls", "payments-api", "High", "Confirm the same idempotency key and payload return the original reservation."),
    ("BP-GATEWAY-ROUTE", "[System] Incident", "API Gateway identity route is missing", "api-gateway", "High", "The expected /identity route is absent from the route registry."),
    ("BP-GATEWAY-TRACE", "Task", "Verify API Gateway correlation ID propagation", "api-gateway", "Medium", "Confirm valid correlation IDs reach every upstream service."),
    ("BP-IDENTITY-TOKEN", "[System] Incident", "Identity Service accepts an empty demo token", "identity-service", "Highest", "The validator accepts the demo- prefix without a subject."),
    ("BP-IDENTITY-EXPIRY", "Task", "Validate Identity Service token expiry boundary", "identity-service", "High", "Confirm tokens are rejected when exp is equal to current time."),
)

HISTORICAL_INCIDENTS = (
    ("BP-HIST-LOAN-2025", "Loan Service production saturation after pool configuration change", "loan-service", "Highest", "Symptoms: dependency timeouts and 18% error rate after a connection-pool change. Root cause: runtime capacity diverged from the reviewed configuration and exceeded downstream limits. Resolution: restored one configuration source, capped concurrency, rolled back, then load-tested at 80%, 90%, and 100% pool utilization. Verification: p95 latency returned below 350 ms and dependency errors remained below 2%. Preventive action: configuration contract test and staged saturation monitoring."),
    ("BP-HIST-PAY-2025", "Payments duplicate reservations after timeout retry", "payments-api", "Highest", "Symptoms: multiple reservation identifiers for the same payment following client timeouts. Root cause: reservation creation occurred before the idempotency-ledger lookup. Resolution: moved the lookup before creation, returned the original response for identical payloads, rejected conflicting key reuse, and reconciled duplicates. Verification: repeated-request and conflicting-payload tests passed. Preventive action: bounded retries and an idempotency invariant alert."),
    ("BP-HIST-IDENTITY-2025", "Identity token boundary regression reached production", "identity-service", "High", "Symptoms: empty-subject and boundary-expired demo tokens were accepted. Root cause: prefix-only validation and an incorrect expiry comparison. Resolution: required a non-empty subject, used constant-time signature comparison, and rejected exp less than or equal to now. Verification: malformed, modified, empty-subject, and expiry-boundary tests passed. Preventive action: security contract checks in CI."),
)


def _adf(text: str) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def _adf_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        own = value.get("text", "")
        return " ".join(filter(None, [own, *(_adf_text(item) for item in value.get("content", []))])).strip()
    if isinstance(value, list):
        return " ".join(_adf_text(item) for item in value).strip()
    return ""


def _tokens(text: str) -> set[str]:
    ignored = {"the", "and", "for", "from", "with", "service", "tests", "src", "demo"}
    return {token for token in re.findall(r"[a-z0-9_-]{3,}", text.lower()) if token not in ignored}


@dataclass
class JiraClient:
    base_url: str
    project_key: str
    email: str
    api_token: str
    session: Any = requests

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.project_key and self.email and self.api_token)

    def _request(self, method: str, path: str, **kwargs):
        response = self.session.request(
            method, f"{self.base_url}{path}", auth=(self.email, self.api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=20, **kwargs,
        )
        response.raise_for_status()
        return response

    def status(self) -> dict[str, Any]:
        if not self.ready:
            return {"ready": False, "connected": False, "project_key": self.project_key or None}
        account = self._request("GET", "/rest/api/3/myself").json()
        project = self._request("GET", f"/rest/api/3/project/{self.project_key}").json()
        return {"ready": True, "connected": True, "account_active": account.get("active", False), "project_key": project.get("key"), "project_type": project.get("projectTypeKey"), "source": "jira"}

    def issues(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET", "/rest/api/3/search/jql",
            params={"jql": f'project = "{self.project_key}" AND labels = "buildpulse-demo" ORDER BY created DESC', "maxResults": 100, "fields": "summary,status,priority,issuetype,labels,created,updated,description,resolution,assignee"},
        ).json()
        items = []
        for issue in response.get("issues", []):
            fields = issue.get("fields", {})
            labels = fields.get("labels") or []
            service_id = next((key for key in SERVICE_LABELS if key in labels), None)
            items.append({
                "key": issue["key"], "summary": fields.get("summary", "Untitled Jira issue"),
                "service_id": service_id, "service": SERVICE_LABELS.get(service_id, "Unmapped service"),
                "status": (fields.get("status") or {}).get("name"),
                "status_category": ((fields.get("status") or {}).get("statusCategory") or {}).get("key"),
                "priority": (fields.get("priority") or {}).get("name", "Unspecified"),
                "issue_type": (fields.get("issuetype") or {}).get("name"), "labels": labels,
                "description": _adf_text(fields.get("description")),
                "resolution": (fields.get("resolution") or {}).get("name"),
                "assignee": (fields.get("assignee") or {}).get("displayName"),
                "created": fields.get("created"), "updated": fields.get("updated"),
                "url": f"{self.base_url}/browse/{issue['key']}", "source": "jira",
            })
        return items

    def historical_incidents(self) -> list[dict[str, Any]]:
        resolved = [item for item in self.issues() if item["status_category"] == "done" and "historical-incident" in item["labels"]]
        for item in resolved:
            detail = self._request("GET", f"/rest/api/3/issue/{item['key']}", params={"expand": "changelog", "fields": "comment"}).json()
            histories = detail.get("changelog", {}).get("histories", [])
            transition = next((history for history in reversed(histories) if any(change.get("field") == "status" and change.get("toString") in {"Completed", "Done", "Resolved"} for change in history.get("items", []))), None)
            item["resolved_by"] = (transition or {}).get("author", {}).get("displayName") or item.get("assignee") or "Unknown resolver"
            comments = ((detail.get("fields") or {}).get("comment") or {}).get("comments", [])
            item["resolution_notes"] = " ".join(_adf_text(comment.get("body")) for comment in comments)
        return resolved

    def similar_incidents(self, text: str, service_id: str | None = None, limit: int = 3) -> list[dict[str, Any]]:
        query = _tokens(text)
        ranked = []
        for incident in self.historical_incidents():
            if service_id and incident["service_id"] != service_id:
                continue
            corpus = _tokens(f"{incident['summary']} {incident['description']} {incident['resolution_notes']}")
            overlap = len(query & corpus)
            service_bonus = 4 if service_id else 0
            score = overlap + service_bonus
            if score:
                ranked.append({**incident, "similarity_score": min(100, 35 + score * 8), "matched_terms": sorted(query & corpus)[:8]})
        return sorted(ranked, key=lambda item: item["similarity_score"], reverse=True)[:limit]

    def dashboard(self) -> dict[str, Any]:
        issues = self.issues()
        open_items = [item for item in issues if item["status_category"] != "done"]
        incidents = [item for item in open_items if "Incident" in (item["issue_type"] or "")]
        blockers = [item for item in open_items if item["priority"] in {"Highest", "High"}]
        counts = Counter(item["service_id"] for item in incidents if item["service_id"])
        readiness = max(0, 100 - len([item for item in blockers if item["priority"] == "Highest"]) * 8 - len([item for item in blockers if item["priority"] == "High"]) * 3)
        return {
            "source": "jira", "project_key": self.project_key, "issue_count": len(issues),
            "open_incidents": len(incidents), "release_blockers": len(blockers), "release_readiness": readiness,
            "attention": open_items[:6], "incidents_by_service": dict(counts), "issues": issues,
        }

    def seed_demo_tickets(self) -> dict[str, Any]:
        existing = {label for item in self.issues() for label in item["labels"] if label.startswith("scenario-")}
        created, skipped = [], []
        for scenario, issue_type, summary, service_id, priority, description in DEMO_TICKETS:
            scenario_label = f"scenario-{scenario.lower()}"
            if scenario_label in existing:
                skipped.append(scenario)
                continue
            payload = {"fields": {"project": {"key": self.project_key}, "summary": f"[BuildPulse Demo] {summary}", "description": _adf(description), "issuetype": {"name": issue_type}, "priority": {"name": priority}, "labels": ["buildpulse-demo", service_id, scenario_label, "synthetic-data"]}}
            result = self._request("POST", "/rest/api/3/issue", json=payload).json()
            created.append(result["key"])
        return {"created": created, "skipped": skipped, "total": len(created) + len(skipped), "source": "jira"}

    def seed_historical_incidents(self) -> dict[str, Any]:
        existing = {label for item in self.issues() for label in item["labels"] if label.startswith("scenario-bp-hist-")}
        created, skipped = [], []
        for scenario, summary, service_id, priority, description in HISTORICAL_INCIDENTS:
            label = f"scenario-{scenario.lower()}"
            if label in existing:
                skipped.append(scenario)
                continue
            payload = {"fields": {"project": {"key": self.project_key}, "summary": f"[BuildPulse Historical Demo] {summary}", "description": _adf(description), "issuetype": {"name": "[System] Incident"}, "priority": {"name": priority}, "labels": ["buildpulse-demo", "historical-incident", "resolved-example", service_id, label, "synthetic-data"]}}
            key = self._request("POST", "/rest/api/3/issue", json=payload).json()["key"]
            self._request("POST", f"/rest/api/3/issue/{key}/comment", json={"body": _adf("Resolution verified and documented for BuildPulse similarity retrieval. This ticket and its operational history are synthetic.")})
            transitions = self._request("GET", f"/rest/api/3/issue/{key}/transitions").json().get("transitions", [])
            resolved = next((item for item in transitions if item.get("to", {}).get("statusCategory", {}).get("key") == "done" and item.get("name") == "Resolve"), None) or next((item for item in transitions if item.get("to", {}).get("statusCategory", {}).get("key") == "done"), None)
            if not resolved:
                raise RuntimeError(f"No resolved transition available for {key}")
            self._request("POST", f"/rest/api/3/issue/{key}/transitions", json={"transition": {"id": resolved["id"]}})
            created.append(key)
        return {"created": created, "skipped": skipped, "total": len(created) + len(skipped), "source": "jira"}
