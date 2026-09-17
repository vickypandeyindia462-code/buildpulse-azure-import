"""Read-only synchronization of BuildPulse's approved engineering sources."""

from __future__ import annotations

from typing import Any

from ..config import Settings
from .ci_intelligence import GitHubActionsClient
from .confluence_knowledge import ConfluenceClient
from .jira_intelligence import JiraClient
from .knowledge_base import KnowledgeBase
from .repository_intelligence import RepositoryIntelligence
from .retrieval_store import RetrievalStore


class UnifiedIngestionService:
    def __init__(self) -> None:
        settings = Settings.from_env()
        self.repository = RepositoryIntelligence()
        self.store = RetrievalStore(KnowledgeBase(self.repository.repository_path))
        self.confluence = ConfluenceClient(settings.confluence_base_url, settings.confluence_space_id, settings.confluence_space_key, settings.jira_email, settings.jira_api_token)
        self.jira = JiraClient(settings.jira_base_url, settings.jira_project_key, settings.jira_email, settings.jira_api_token)
        self.ci = GitHubActionsClient(settings.github_owner, settings.github_repo, settings.github_token)

    def sync(self) -> dict[str, Any]:
        results: dict[str, Any] = {"repository": self.store.index_repository()}
        errors: dict[str, str] = {}
        external: list[dict[str, Any]] = []
        if self.confluence.ready:
            try:
                for page in self.confluence.pages():
                    external.append({"source": "confluence", "external_id": page["id"], "title": page["title"], "content": page["content"], "url": page["url"], "updated_at": page.get("updated_at"), "document_type": "confluence_page"})
            except Exception as exc:
                errors["confluence"] = type(exc).__name__
        if self.jira.ready:
            try:
                for issue in self.jira.historical_incidents():
                    content = "\n".join(filter(None, [issue["summary"], issue.get("description"), issue.get("resolution_notes"), f"Resolution: {issue.get('resolution') or 'Completed'}", f"Resolved by: {issue.get('resolved_by') or issue.get('assignee') or 'Unknown'}"]))
                    external.append({"source": "jira", "external_id": issue["key"], "title": issue["summary"], "content": content, "service_id": issue.get("service_id"), "url": issue["url"], "updated_at": issue.get("updated"), "document_type": "resolved_incident"})
            except Exception as exc:
                errors["jira"] = type(exc).__name__
        try:
            for run in self.ci.failed_runs():
                content = f"Workflow: {run.get('workflow')}\nJob: {run.get('job')}\nFailed step: {run.get('failed_step')}\nConclusion: failure\nBranch: {run.get('branch') or 'unknown'}"
                external.append({"source": "github-ci", "external_id": run["id"], "title": f"CI failure — {run.get('job') or run.get('workflow')}", "content": content, "service_id": run.get("service_id"), "url": run.get("url"), "updated_at": run.get("started_at"), "document_type": "ci_failure"})
        except Exception as exc:
            errors["github-ci"] = type(exc).__name__
        results["external"] = self.store.index_source_documents(external)
        results["sources"] = {
            "confluence": len([item for item in external if item["source"] == "confluence"]),
            "jira": len([item for item in external if item["source"] == "jira"]),
            "github-ci": len([item for item in external if item["source"] == "github-ci"]),
        }
        results["errors"] = errors
        results["retrieval"] = self.store.status()
        return results
