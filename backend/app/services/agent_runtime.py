"""Provider-swappable orchestration for the BuildPulse demo.

The mock path is intentionally useful: judging can exercise the product without
cloud credentials.  Azure/OpenAI are opt-in through environment variables only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import uuid

import requests

from .repository_intelligence import RepositoryIntelligence
from .ci_intelligence import GitHubActionsClient, classify_failure
from .knowledge_base import KnowledgeBase
from .confluence_knowledge import ConfluenceClient
from ..config import Settings
from backend.agents.security_check import scan_and_redact


@dataclass(frozen=True)
class AgentSettings:
    provider: str = "mock"
    ci_source: str = "fixture"
    github_owner: str = "vickypandeyindia462-code"
    github_repo: str = "buildpulse-demo-services"
    github_token: str = ""
    azure_endpoint: str = ""
    azure_api_key: str = ""
    azure_chat_deployment: str = ""
    azure_embedding_deployment: str = ""
    azure_api_version: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    confluence_base_url: str = ""
    confluence_space_id: str = ""
    confluence_space_key: str = ""
    atlassian_email: str = ""
    atlassian_api_token: str = ""

    @classmethod
    def from_env(cls) -> "AgentSettings":
        settings = Settings.from_env()
        return cls(
            provider=settings.llm_provider,
            ci_source=settings.ci_source,
            github_owner=settings.github_owner,
            github_repo=settings.github_repo,
            github_token=settings.github_token,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_api_key=settings.azure_openai_api_key,
            azure_chat_deployment=settings.azure_openai_chat_deployment,
            azure_embedding_deployment=settings.azure_openai_embedding_deployment,
            azure_api_version=settings.azure_openai_api_version,
            gemini_api_key=settings.gemini_api_key,
            gemini_model=settings.gemini_model,
            confluence_base_url=settings.confluence_base_url,
            confluence_space_id=settings.confluence_space_id,
            confluence_space_key=settings.confluence_space_key,
            atlassian_email=settings.jira_email,
            atlassian_api_token=settings.jira_api_token,
        )

    @property
    def live_ready(self) -> bool:
        if self.provider == "gemini":
            return bool(self.gemini_api_key and self.gemini_model)
        return bool(self.provider == "azure_openai" and self.azure_endpoint and self.azure_api_key and self.azure_chat_deployment)


class MockLLMProvider:
    """A deterministic, evidence-only fallback for offline demonstrations."""

    name = "mock"

    def complete(self, *, question: str, evidence: list[dict[str, str]]) -> str:
        query_terms = {
            term for term in re.findall(r"[a-z0-9_-]{3,}", question.lower())
            if term not in {"about", "could", "please", "should", "what", "when", "where", "which", "with", "would"}
        }
        statements: list[str] = []
        for index, item in enumerate(evidence[:3], start=1):
            sentences = re.split(r"(?<=[.!?])\s+|\n+", item.get("content", ""))
            ranked = sorted(
                (sentence.strip() for sentence in sentences if 25 <= len(sentence.strip()) <= 320),
                key=lambda sentence: len(query_terms & set(re.findall(r"[a-z0-9_-]{3,}", sentence.lower()))),
                reverse=True,
            )
            if ranked:
                statements.append(f"{ranked[0]} [Source {index}]")
        if not statements:
            return "I found related BuildPulse sources, but they do not contain a clear passage that answers the question."
        return "Here’s what the connected BuildPulse knowledge says:\n\n" + "\n\n".join(statements)


class AzureOpenAIProvider:
    """Thin adapter activated only when the hackathon deployment is configured."""

    name = "azure_openai"

    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings

    def complete(self, *, question: str, evidence: list[dict[str, str]]) -> str:
        # Imported lazily: mock mode has no dependency on a live Azure SDK/client.
        from openai import AzureOpenAI

        client_options: dict[str, str] = {
            "azure_endpoint": self.settings.azure_endpoint,
            "api_key": self.settings.azure_api_key,
        }
        if self.settings.azure_api_version:
            client_options["api_version"] = self.settings.azure_api_version
        client = AzureOpenAI(**client_options)
        context = "\n\n".join(f"[{item['title']}]\n{item['content']}" for item in evidence[:4])
        response = client.chat.completions.create(
            model=self.settings.azure_chat_deployment,
            temperature=0.2,
            max_tokens=600,
            messages=[
                {"role": "system", "content": "You are BuildPulse. Answer only from supplied evidence. State uncertainty and propose safe, reversible engineering actions."},
                {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
            ],
        )
        return (response.choices[0].message.content or "No answer returned.").strip()


class GeminiProvider:
    """Gemini adapter that receives only sanitized, retrieved KB evidence."""

    name = "gemini"

    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings

    def complete(self, *, question: str, evidence: list[dict[str, str]]) -> str:
        from google import genai
        from google.genai import types

        context = "\n\n".join(
            f"[Source {index}: {item['title']}]\n{item['content']}"
            for index, item in enumerate(evidence[:5], start=1)
        )
        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=f"Question: {question}\n\nRetrieved BuildPulse knowledge base:\n{context}",
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=(
                    "You are BuildPulse. For greetings and social conversation, respond naturally and briefly "
                    "without citations or enterprise claims. For operational questions, answer only from the "
                    "retrieved knowledge-base evidence and cite claims using [Source N]. If the evidence is "
                    "insufficient, say exactly what is missing. Never invent services, owners, incidents, "
                    "fixes, or risk values."
                ),
            ),
        )
        return (response.text or "The knowledge base does not contain enough evidence to answer this question.").strip()


class BuildPulseAgentRuntime:
    """Coordinates CI, repository, retrieval, risk, SME, and response agents."""

    fixture_runs = [
        {
            "id": "demo-run-2431",
            "pr_number": 3,
            "service_id": "loan-service",
            "workflow": "Service CI",
            "job": "loan-service-tests",
            "status": "completed",
            "conclusion": "failure",
            "failed_step": "Run loan service tests",
            "log_excerpt": "FAILED tests/test_connection_pool.py::test_capacity_is_bounded - AssertionError: expected 30, got 45",
            "started_at": "2026-09-14T09:16:00Z",
        }
    ]

    SOCIAL_MESSAGES = {
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "thanks", "thank you", "how are you", "how are you doing", "how's it going",
        "who are you", "what can you do", "bye", "goodbye",
    }

    @staticmethod
    def _social_response(message: str) -> str:
        if message in {"how are you", "how are you doing", "how's it going"}:
            return "I’m ready to help. Tell me what you’re investigating, and I’ll ask for any missing details before checking your BuildPulse sources."
        if message in {"thanks", "thank you"}:
            return "You’re welcome. Is there another service, failure, incident, or release risk you’d like to investigate?"
        if message in {"bye", "goodbye"}:
            return "Goodbye. I’ll be here when you need to investigate another BuildPulse issue."
        if message in {"who are you", "what can you do"}:
            return "I’m the BuildPulse Copilot. I investigate CI failures, release risk, ownership, incidents, and prior resolutions using only your connected internal sources."
        return (
            "Hello! I’m the BuildPulse Copilot. I can help you investigate CI failures, "
            "release risk, service ownership, incidents, and resolutions using only your "
            "connected repository, Jira, Confluence, and BuildPulse knowledge sources. "
            "What would you like to investigate?"
        )

    def __init__(self, repository: RepositoryIntelligence | None = None, settings: AgentSettings | None = None) -> None:
        self.repository = repository or RepositoryIntelligence()
        self.settings = settings or AgentSettings.from_env()
        self.ci = GitHubActionsClient(
            self.settings.github_owner, self.settings.github_repo, self.settings.github_token
        )
        self.knowledge = KnowledgeBase(self.repository.repository_path)
        self.confluence = ConfluenceClient(self.settings.confluence_base_url, self.settings.confluence_space_id, self.settings.confluence_space_key, self.settings.atlassian_email, self.settings.atlassian_api_token)

    def _github_get(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        """Read public data even when an optional local token has expired."""
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code >= 400 and self.settings.github_token:
            response = requests.get(url, headers={"Accept": "application/vnd.github+json"}, params=params, timeout=10)
        response.raise_for_status()
        return response

    def status(self) -> dict[str, Any]:
        azure_ready = bool(
            self.settings.provider == "azure_openai"
            and self.settings.azure_endpoint
            and self.settings.azure_api_key
            and self.settings.azure_chat_deployment
        )
        gemini_ready = bool(
            self.settings.provider == "gemini"
            and self.settings.gemini_api_key
            and self.settings.gemini_model
        )
        return {
            "mode": "live" if self.settings.live_ready else "demo",
            "llm_provider": self.settings.provider if self.settings.live_ready else "mock",
            "ci_source": self.settings.ci_source,
            "provider_ready": self.settings.live_ready,
            "azure_ready": azure_ready,
            "gemini_ready": gemini_ready,
            "github_access": "token" if self.settings.github_token else "public-read-only",
            "agents": ["CI Collector", "Failure Analysis", "Knowledge Retrieval", "Risk & SME", "Copilot Response"],
        }

    def failed_runs(self) -> list[dict[str, Any]]:
        if self.settings.ci_source == "github":
            try:
                failures = self.ci.failed_runs()
                # A successful CI run is valuable live evidence, but it has no failed
                # job to analyse. Retain the labelled fixture so the product demo can
                # still demonstrate the failure-analysis path.
                if failures:
                    return failures
            except requests.RequestException:
                # A good demo should still operate if Wi-Fi or GitHub is unavailable.
                pass
        return [dict(run, source="fixture") for run in self.fixture_runs]

    def recent_runs(self) -> list[dict[str, Any]]:
        """Return real workflow-level history, including successful builds."""
        if self.settings.ci_source != "github":
            return []
        try:
            return self.ci.recent_runs()
        except requests.RequestException:
            return []

    def _documents(self, service_id: str | None = None, query: str = "") -> list[dict[str, str]]:
        search_query = query or f"{(service_id or '').replace('-', ' ')} architecture runbook recovery ownership dependencies"
        documents = self.knowledge.search(search_query, service_id=service_id, limit=5)
        if self.confluence.ready:
            try:
                documents.extend({"title": item["title"], "content": item["content"], "score": item["score"], "url": item["url"], "source": "confluence"} for item in self.confluence.search(search_query, limit=5))
            except requests.RequestException:
                pass
        return sorted(documents, key=lambda item: item.get("score") or 0, reverse=True)[:5]

    @staticmethod
    def _event(agent: str, state: str, summary: str) -> dict[str, str]:
        return {"agent": agent, "state": state, "summary": summary}

    def analyse_failure(self, run_id: str) -> dict[str, Any]:
        run = next((item for item in self.failed_runs() if str(item["id"]) == str(run_id)), None)
        if not run:
            raise KeyError(run_id)
        service_id = run.get("service_id") or "loan-service"
        demo_pr_by_service = {"payments-api": 1, "api-gateway": 2, "loan-service": 3}
        risk_pr = int(run.get("pr_number") or demo_pr_by_service.get(service_id, 3))
        risk = self.repository.pull_request_risk(risk_pr)
        log_security = {"findings_count": 0, "redacted": False, "available": bool(run.get("log_excerpt"))}
        log = run.get("log_excerpt", "")
        if run.get("source") == "github" and run.get("log_available"):
            try:
                log_result = self.ci.sanitized_job_log(str(run["id"]))
                log = log_result.pop("excerpt")
                log_security = log_result
            except requests.RequestException:
                log_security = {"findings_count": 0, "redacted": False, "available": False}
        documents = self._documents(service_id, f"{run.get('failed_step', '')} {log}")
        classification = classify_failure(log, run.get("failed_step", ""))
        capacity_issue = "capacity" in log.lower() or "expected 30" in log.lower()
        diagnosis = (
            "The configured connection-pool capacity exceeds the safe bound asserted by the service test. "
            "This can amplify database saturation during a traffic spike."
            if capacity_issue else "The workflow failed; inspect the failing assertion and validate the change against the linked runbook."
        )
        fix = (
            "Set the pool capacity to the documented safe value (30), rerun the loan-service test suite, then stage the change with database saturation monitoring."
            if capacity_issue else "Make the smallest reversible correction, rerun the failed job, and request service-owner review."
        )
        return {
            "run": run,
            "diagnosis": diagnosis,
            "recommended_fix": fix,
            "failure_class": "configuration" if capacity_issue else classification["class"],
            "confidence": classification["confidence"],
            "risk": risk,
            "owners": risk["owners"],
            "evidence": [{"title": "CI job log", "content": log}, *documents],
            "security": log_security,
            "audit_id": str(uuid.uuid4()),
            "agent_trace": [
                self._event("CI Collector", "complete", f"Loaded failed job {run.get('job', run['workflow'])}."),
                self._event("Failure Analysis", "complete", diagnosis),
                self._event("Knowledge Retrieval", "complete", f"Retrieved {len(documents)} matching repository documents."),
                self._event("Risk & SME", "complete", f"{risk['risk_level'].title()} risk ({risk['risk_score']}/100); primary owner is {risk['owners']['primary']}."),
            ],
            "mode": self.status()["mode"],
        }

    def chat(self, question: str, service_id: str | None = None, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        security = scan_and_redact(question)
        safe_question = security["redacted_text"]
        question_lower = safe_question.lower()
        normalized_question = re.sub(r"\s+", " ", question_lower).strip().strip(".,!?;:")

        def clarification(answer: str, summary: str, resolved_service: str | None = None) -> dict[str, Any]:
            return {
                "answer": answer,
                "sources": [],
                "service_id": resolved_service,
                "needs_clarification": True,
                "agent_trace": [self._event("Requirement Understanding", "waiting", summary)],
                "mode": self.status()["mode"],
                "provider_used": "requirement_intake",
                "provider_fallback": None,
                "security": {"findings_count": len(security["findings"]), "redacted": bool(security["findings"])},
                "audit_id": str(uuid.uuid4()),
            }
        safe_history: list[str] = []
        for turn in (history or [])[-6:]:
            content = str(turn.get("content", ""))[:800]
            if content:
                safe_history.append(scan_and_redact(content)["redacted_text"])
        if normalized_question in self.SOCIAL_MESSAGES:
            answer = self._social_response(normalized_question)
            provider_name = "local"
            provider_error = None
            if self.settings.live_ready and self.settings.provider == "gemini":
                provider = GeminiProvider(self.settings)
                social_question = safe_question
                if safe_history:
                    social_question = f"Conversation context: {' | '.join(safe_history)}\nCurrent message: {safe_question}"
                try:
                    answer = provider.complete(question=social_question, evidence=[])
                    provider_name = provider.name
                except Exception as error:
                    provider_error = type(error).__name__
            return {
                "answer": answer,
                "sources": [],
                "service_id": service_id,
                "agent_trace": [self._event("Copilot Response", "complete", f"Handled social conversation using {provider_name} provider without knowledge claims.")],
                "mode": self.status()["mode"],
                "provider_used": provider_name,
                "provider_fallback": provider_error,
                "security": {"findings_count": len(security["findings"]), "redacted": bool(security["findings"])},
                "audit_id": str(uuid.uuid4()),
            }
        if re.search(r"\bhow do you know (?:what|which) service\b", normalized_question):
            return {
                **clarification(
                    "I don’t know your service automatically. I only use a service you explicitly name in this conversation or one supplied by a BuildPulse page you opened. Tell me the service name, and I’ll confirm it before retrieving anything.",
                    "Explained service-context boundaries and requested an explicit service.",
                ),
                "needs_clarification": False,
            }
        explicit_service_id = None
        for service in self.repository.services():
            if service["id"] in question_lower or service["name"].lower() in question_lower:
                service_id = service["id"]
                explicit_service_id = service["id"]
                break
        if explicit_service_id is None and re.search(r"\b(my|this) service\b", normalized_question):
            return clarification(
                "Yes. Which service do you mean: Loan Service, Payments API, API Gateway, or Identity Service?",
                "Requested the service name before knowledge retrieval.",
            )
        if explicit_service_id is None and re.search(r"\b(help|assist|support)\b", normalized_question):
            service_id = None
            return clarification(
                "I can help with BuildPulse engineering services, but I don’t yet have a valid service or requirement. Are you asking about Loan Service, Payments API, API Gateway, or Identity Service—and do you need help with a CI failure, incident, release risk, documentation, or ownership?",
                "Cleared stale context and requested an in-scope service and goal.",
            )
        if not service_id and safe_history:
            for previous_turn in reversed(safe_history):
                previous_text = previous_turn.lower()
                matched_service = next(
                    (
                        service for service in self.repository.services()
                        if service["id"] in previous_text or service["name"].lower() in previous_text
                    ),
                    None,
                )
                if matched_service:
                    service_id = matched_service["id"]
                    break
        ownership_request = bool(re.search(r"\b(who\s+owns|owner(?:ship)?\s+(?:of|for)|who\s+is\s+the\s+owner)\b", normalized_question))
        if ownership_request and explicit_service_id is None:
            target = re.sub(
                r"\b(who\s+owns|owner(?:ship)?\s+(?:of|for)|who\s+is\s+the\s+owner)\b",
                "",
                normalized_question,
            ).strip().strip("?.!")
            target = re.sub(r"^the\s+", "", target)
            contextual_targets = {"", "it", "this", "that", "this service", "that service", "service"}
            if target not in contextual_targets:
                return clarification(
                    (
                        f"I don’t have a BuildPulse service named “{target}”. I can provide ownership only for "
                        "Loan Service, Payments API, API Gateway, or Identity Service. Which one did you mean?"
                    ),
                    "Rejected an unknown service and requested a catalogued service.",
                )
        vague_requests = {
            "help", "help me", "i need help", "i have an issue", "there is an issue",
            "something failed", "it failed", "can you investigate", "investigate this",
        }
        if not service_id and normalized_question in vague_requests:
            return clarification(
                "I can investigate that. Which service is affected—Loan Service, Payments API, API Gateway, or Identity Service—and what symptom or failed job are you seeing?",
                "Asked for the affected service and observed symptom.",
            )
        if service_id:
            selected_service = self.repository.service(service_id)
            service_only = normalized_question in {selected_service["id"], selected_service["name"].lower()}
            vague_service_issue = normalized_question in {"it failed", "it is failing", "there is a problem", "it has an issue"}
            if service_only:
                return clarification(
                    f"Got it—{selected_service['name']}. What are you trying to do, or what problem are you seeing?",
                    "Confirmed the service and requested the user's goal or symptom.",
                    service_id,
                )
            if vague_service_issue:
                return clarification(
                    f"I have {selected_service['name']} as the affected service. Is this a CI failure, production incident, release-risk question, or ownership request? If something failed, share the job name or error text.",
                    "Confirmed the service and requested the issue type and observable evidence.",
                    service_id,
                )
        understood_intent = bool(re.search(
            r"\b(owner|owns|ownership|backup|contact|ci|build|job|fail|error|incident|release|risk|"
            r"deploy|deployment|runbook|document|documentation|api|endpoint|slo|latency|"
            r"availability|dependency|ticket|jira|resolution|fix|timeout|health)\b",
            normalized_question,
        ))
        if not understood_intent:
            return clarification(
                "Before I search the knowledge base, what exactly do you need: ownership, a CI failure diagnosis, incident help, release risk, API/SLO information, or a runbook?",
                "Requested a concrete operational intent before retrieval.",
                service_id,
            )
        contextual_question = safe_question
        if safe_history:
            contextual_question = f"Conversation context: {' | '.join(safe_history)}\nCurrent request: {safe_question}"
        documents = self._documents(service_id, contextual_question)
        if service_id:
            service = self.repository.service(service_id)
            catalog_content = (
                f"{service['name']} is a {service['tier']} service owned by {service['primary_owner']} "
                f"with {service['backup_owner']} as backup owner and {service['team']} as the responsible team; "
                f"its health endpoint is {service['health']} and its API documentation is {service['api']}; "
                "no direct email or chat contact is recorded in the service catalog."
            )
            if ownership_request:
                catalog_content = (
                    f"{service['name']} primary owner: {service['primary_owner']}; backup owner: "
                    f"{service['backup_owner']}; responsible team: {service['team']}; direct email or chat "
                    "contact: not recorded in the service catalog."
                )
            catalog_fact = {
                "title": f"Service catalog — {service['name']}",
                "content": catalog_content,
                "score": 100,
                "source": "repository",
            }
            documents = [catalog_fact, *documents][:5]
            if ownership_request:
                documents = [catalog_fact]
                contextual_question = (
                    f"{contextual_question}\nResponse requirement: Return only the primary owner, backup owner, "
                    "responsible team, and whether direct contact details are recorded. Do not add unrelated service information."
                )
        failure = None
        if any(word in question_lower for word in ("fail", "ci", "build", "loan", "release")):
            failures = self.failed_runs()
            if failures:
                failure = self.analyse_failure(str(failures[0]["id"]))
        evidence = documents + ([{"title": "Latest CI analysis", "content": failure["diagnosis"]}] if failure else [])
        provider_error = None
        if not evidence:
            provider = MockLLMProvider()
            answer = "The BuildPulse knowledge base does not contain enough evidence to answer this question. Add or index a relevant service document."
        elif self.settings.live_ready and self.settings.provider == "gemini":
            provider = GeminiProvider(self.settings)
            try:
                answer = provider.complete(question=contextual_question, evidence=evidence)
            except Exception as error:
                provider_error = type(error).__name__
                provider = MockLLMProvider()
                answer = provider.complete(question=contextual_question, evidence=evidence)
        elif self.settings.live_ready and self.settings.provider == "azure_openai":
            provider = AzureOpenAIProvider(self.settings)
            try:
                answer = provider.complete(question=safe_question, evidence=evidence)
            except Exception as error:
                provider_error = type(error).__name__
                provider = MockLLMProvider()
                answer = provider.complete(question=safe_question, evidence=evidence)
        else:
            provider = MockLLMProvider()
            answer = provider.complete(question=contextual_question, evidence=evidence)
        return {
            "answer": answer,
            "sources": [
                {"title": item["title"], "score": item.get("score"), "chunk": item.get("chunk"), "url": item.get("url"), "source": item.get("source", "repository")}
                for item in evidence
            ],
            "service_id": service_id,
            "agent_trace": (failure or {"agent_trace": []})["agent_trace"] + [self._event("Copilot Response", "complete", f"Answered using {provider.name} provider.")],
            "mode": self.status()["mode"],
            "provider_used": provider.name,
            "provider_fallback": provider_error,
            "needs_clarification": False,
            "security": {
                "findings_count": len(security["findings"]),
                "redacted": bool(security["findings"]),
            },
            "audit_id": str(uuid.uuid4()),
        }
