"""Centralized, runtime-loaded application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    ci_source: str
    github_owner: str
    github_repo: str
    github_token: str
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_chat_deployment: str
    azure_openai_embedding_deployment: str
    gemini_api_key: str
    gemini_model: str
    jira_base_url: str
    jira_project_key: str
    jira_email: str
    jira_api_token: str
    confluence_base_url: str
    confluence_space_id: str
    confluence_space_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        owner = os.getenv("GITHUB_OWNER", "vickypandeyindia462-code").strip()
        repo = os.getenv("GITHUB_REPO", "buildpulse-demo-services").strip()
        # Accept both GITHUB_REPO=repo and GITHUB_REPO=owner/repo, but expose one
        # normalized representation to every GitHub integration.
        if "/" in repo:
            configured_owner, repo = repo.split("/", 1)
            owner = configured_owner or owner
        elif ":" in repo:
            configured_owner, repo = repo.split(":", 1)
            owner = configured_owner or owner
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
            ci_source=os.getenv("CI_SOURCE", "fixture").strip().lower(),
            github_owner=owner,
            github_repo=repo,
            github_token=os.getenv("GITHUB_TOKEN", "").strip(),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip(),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", "").strip(),
            azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "").strip(),
            azure_openai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "").strip(),
            azure_openai_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip(),
            jira_base_url=os.getenv("JIRA_BASE_URL", "").strip().rstrip("/"),
            jira_project_key=os.getenv("JIRA_PROJECT_KEY", "").strip(),
            jira_email=os.getenv("JIRA_EMAIL", "").strip(),
            jira_api_token=os.getenv("JIRA_API_TOKEN", "").strip(),
            confluence_base_url=os.getenv("CONFLUENCE_BASE_URL", "").strip().rstrip("/"),
            confluence_space_id=os.getenv("CONFLUENCE_SPACE_ID", "").strip(),
            confluence_space_key=os.getenv("CONFLUENCE_SPACE_KEY", "").strip(),
        )
