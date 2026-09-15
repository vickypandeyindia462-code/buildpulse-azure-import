# BuildPulse — Living Implementation Plan

> Single source of truth for completed work, current verification, known gaps, and future delivery. Update this file after every milestone.

## Product goal

BuildPulse is a security-first engineering intelligence application. It combines CI/CD failures, repository changes, service dependencies, operational documentation, incidents, ownership, and deterministic risk signals into an evidence-backed developer Copilot.

Primary demo question:

> Why did the Loan Service build fail, what should we fix, who owns it, and can Release 24.3 still proceed?

## Agreed architecture

```text
Browser → static HTML/CSS/JavaScript served by FastAPI → /api endpoints
        → security scan/redaction → orchestrator
          ├─ CI intelligence
          ├─ repository intelligence
          ├─ knowledge retrieval
          ├─ SME discovery
          └─ deterministic risk
        → evidence-backed response

Sources: demo-services Git repo + GitHub Actions + SQLite/Postgres/pgvector
AI: deterministic mock now; Azure OpenAI deployment on hackathon day
```

The static frontend is the product UI. Streamlit is legacy scaffolding, not the target frontend.

## Current snapshot — 2026-09-14

### Complete

- Eight-page polished UI served by FastAPI.
- Separate `buildpulse-demo-services` repository with four synthetic services.
- Catalog ownership, backup SMEs, dependencies, architecture docs, and Loan Service runbook.
- Three synthetic feature branches/open PRs used for explainable demonstrations.
- Read-only local Git diff analysis and deterministic PR risk scoring.
- Live GitHub Actions workflow history with public-read fallback.
- Deterministic failed Loan Service CI fixture for a reliable demo.
- Mock orchestration trace: CI Collector → Failure Analysis → Knowledge Retrieval → Risk & SME → Copilot Response.
- Optional Azure OpenAI Copilot configuration.
- Optional Gemini live Copilot configuration through the official Google GenAI SDK.
- Runtime-loaded and normalized GitHub/Azure configuration.
- Copilot question redaction for emails, SSN-like values, and common GitHub/OpenAI tokens.
- Correct SQLite ingestion persistence: embeddings serialize to JSON, source metadata is retained, and transaction errors are surfaced.

### Partial

- Live CI reads workflow/job metadata, but not sanitized failed-job logs.
- Copilot uses two repository documents; complete indexed retrieval is pending.
- RAG has substring and pgvector paths, but needs chunking, filters, and stronger citations.
- Copilot security scanning is enforced; immutable audit persistence and full pipeline coverage remain pending.
- Document contribution is currently a visual form only.
- Incidents, release metrics, and Security Center audit records remain demo content.

## Milestones

### M1 — UI foundation — complete

- Adopt approved HTML/CSS/JS and serve it through FastAPI.
- Preserve all eight product pages and responsive navigation.

### M2 — Repository Intelligence — complete

- Read the service catalog, resolve ownership/dependencies, inspect branch diffs without executing code, calculate deterministic risk, and connect Dashboard/SME/Risk UI.

### M3 — Agent and live-CI foundation — complete

- Add mock-first orchestration, failed-CI fixture, GitHub Actions history, Azure-ready settings, Copilot integration, and live CI card.

### M4 — Stabilization and security baseline — complete

Completed:

- Centralized runtime configuration and normalized both `GITHUB_REPO=repo` and `GITHUB_REPO=owner/repo`.
- Fixed SQLite embedding persistence and stopped hiding ingestion rollbacks.
- Retained document source metadata.
- Redacted sensitive Copilot input before orchestration.
- Added audit IDs and safe security summaries to Copilot responses.
- Added regression tests for configuration, persistence, and redaction.
- Made `/api/copilot/chat` canonical and converted `/ai/chat` into a deprecated compatibility adapter with normal FastAPI validation/errors.
- Modernized Azure/OpenAI embedding clients and connected embeddings to the shared configuration contract.
- Isolated all unit/API tests from `dev.db` and disabled accidental paid/network model calls during unit tests.
- Replaced deprecated FastAPI startup events with lifespan handling and adopted SQLAlchemy's current declarative base API.
- Updated the legacy AI verification script to call the canonical endpoint.
- Browser-smoke-tested Dashboard API loading and a complete Copilot response with sources, security status, audit ID, and agent trace.

Acceptance evidence: 29 tests passed, 1 optional Postgres/pgvector test skipped; Python compilation and diff validation passed. Two remaining warnings originate from the installed Starlette/TestClient compatibility layer.

### M5 — Secure live CI failure intelligence — complete

- Fetches failed workflows, jobs, failed steps, PR/branch context, and service identity from GitHub Actions.
- Downloads job logs only with an authenticated read token; public mode never claims logs are available.
- Accepts text or ZIP logs, caps downloads at 2 MB, and caps the actionable tail excerpt at 12,000 characters.
- Redacts emails, SSN-like data, and common GitHub/OpenAI token formats before analysis.
- Deterministically classifies test, dependency, configuration, contract, timeout, deployment, build, or unknown failures.
- Calculates explainable confidence from log availability, failed-step identity, and matched signatures.
- Enriches the result with repository risk, changed files, dependency context, owners, architecture, and runbook evidence.
- Returns diagnosis, safe fix, confidence drivers, security summary, and audit ID.
- Copilot prefers a real failure when present and retains the labelled fixture otherwise.
- Dashboard renders a CI Failure Intelligence card with live/fixture provenance, classification, confidence, and risk.
- Dedicated CI Failures page lists all failed jobs and filters them by service.
- Selecting a job opens its failed step, diagnosis, recommended fix, confidence drivers, risk, primary/backup owners, log-security status, recommended checks, and expandable evidence.
- Detail actions can open a live GitHub job or transfer the failure context directly into Copilot.

Safety boundary: BuildPulse proposes changes but does not automatically edit code, rerun workflows, merge PRs, or deploy.

Acceptance evidence: 33 tests passed, 1 optional pgvector test skipped. Browser verification rendered the fixture as a configuration failure with 90% explainable confidence, risk 65, and a Copilot handoff. The dedicated failed-jobs page and service filter were loaded successfully in the running UI. Real private/job-log verification requires a future failed GitHub run plus a read-only token.

### M5.5 — Full synthetic demo-services ecosystem — implementation complete

- Expanded the separate `buildpulse-demo-services` repository on isolated branch `codex/full-demo-ecosystem`; existing main, release, and PR-risk branches remain untouched.
- Added runnable FastAPI entry points and health endpoints for Loan Service, Payments API, API Gateway, and Identity Service.
- Added original domain behavior for explainable loan decisions, idempotent payment reservations, correlation-ID propagation, and signed-token expiry validation.
- Added four deterministic live-fix scenarios covering configuration drift, payment idempotency, observability contracts, and authentication boundaries.
- Added synthetic incidents, release history, and telemetry snapshots with explicit provenance labels.
- Enriched the service catalog with SLOs, API/health routes, ownership, dependencies, runbooks, and KB mappings.
- Added service-specific KB articles, recovery runbooks, a blameless synthetic postmortem, and an end-to-end live-fix demonstration guide.
- Replaced duplicated workflow jobs with a four-service test matrix and repository-metadata validation.
- Added an attribution page linking official FastAPI, GitHub Actions, and Google SRE guidance; no third-party application code or real customer data was copied.

Acceptance evidence: all 16 service tests passed (Loan 5, Payments 4, Gateway 4, Identity 3); metadata validation connected 4 services to 4 failure scenarios and their corresponding runbooks/KB articles. The branch is ready for commit and remote publication.

Live demonstration state:

- Healthy ecosystem branch: `codex/full-demo-ecosystem`, commit `188e1d9`, GitHub Actions run `34880958887` passed.
- Disposable failure branch: `demo/failing-loan-pool`, commit `c6c79e8`, GitHub Actions run `34881709583` failed as designed.
- Isolated signal: Loan Service reports one failure (`runtime=40`, `configured=60`) while its other five tests and all Payments/Gateway/Identity tests pass.
- Expected fix: replace the duplicate `MAX_CONNECTIONS = 40` definition with the configured `CONNECTION_POOL_MAX` source of truth, then push to demonstrate failed-to-passed CI recovery.
- Multi-service history branch: `demo/failing-matrix`, commits `9d9eeb3`, `fc9f8cf`, and `0463651` generated three completed failed workflow runs (`34883111707`, `34883390345`, `34883480924`). Each run contains one controlled failed job for every service.
- Current live inventory: 13 GitHub failed jobs — Loan Service 4, Payments API 3, API Gateway 3, Identity Service 3.
- CI Failures UI now renders every job as one compact horizontal row. No analysis is selected automatically; diagnosis, fix, owners, confidence, security, checks, evidence, and actions appear only after the user clicks a row.

### M6 — Secure contribution and Knowledge Discovery — in progress

Completed foundation:

- Added a bounded local KB index for approved repository `docs/**/*.md`, service READMEs, and text articles.
- Added service-aware lexical ranking with source path, chunk number, and relevance score.
- Added Gemini as a provider-swappable live assistant using `GEMINI_API_KEY` and configurable `GEMINI_MODEL`.
- Gemini receives only the redacted question and the top five retrieved KB excerpts.
- Grounding instructions require `[Source N]` citations and prohibit invented services, owners, incidents, fixes, or risk values.
- Questions with no supporting evidence return an explicit insufficient-evidence response without invoking a live model.
- Installed and verified the official `google-genai` SDK.

Remaining:

- Upload file plus title, type, team, service, description, and access scope.
- Validate type/size and safely extract PDF/DOCX/MD/TXT/CSV.
- Scan → redact/block/review → chunk → embed → store → audit.
- Add ingestion status and semantic search with filters, snippets, relevance, and citations.
- Keep GitHub PR creation as an explicit optional review workflow after validation.

### M6.5 — Live Jira engineering intelligence — complete

- Added environment-only Jira Cloud configuration and authenticated REST client support.
- Added `/api/jira/status`, `/api/jira/issues`, and `/api/jira/dashboard` read endpoints.
- Restricted dashboard retrieval to issues carrying the `buildpulse-demo` label.
- Added service mapping through `loan-service`, `payments-api`, `api-gateway`, and `identity-service` Jira labels.
- Added idempotent scenario-label ticket seeding; reruns skip existing scenarios instead of creating duplicates.
- Created `SUP-1` through `SUP-8`, comprising one synthetic incident and one remediation/verification task for every service.
- Replaced Executive Dashboard fixture readiness, incident count, release blockers, attention feed, and incident distribution with live Jira calculations and direct ticket links.
- Jira-derived readiness is explainable: Highest open items deduct 8 points and High open items deduct 3 points from 100.
- Credentials remain only in local `.env`; neither APIs nor UI expose the account email or token.

Acceptance evidence: Jira authentication and project access returned HTTP 200; live dashboard reported 8 labelled issues, 4 open incidents, 7 High/Highest blockers, readiness 64%, and exactly 2 issues for each service. Full application verification: 39 passed, 1 optional pgvector test skipped.

### M6.6 — Jira historical resolution and predictive PR risk — complete

- Created and resolved three explicitly synthetic historical production incidents: `SUP-9` (Loan pool saturation), `SUP-10` (Payments duplicate reservations), and `SUP-11` (Identity token boundary regression).
- Stored symptoms, production impact, root cause, resolution procedure, verification, and preventive controls in each historical issue.
- Added a resolution-verification comment and transitioned each issue through Jira's `Resolve` workflow action to `Completed`.
- Reads Jira changelog history to identify the actual account that performed the resolving transition; fictional engineering identities remain only synthetic content.
- Added `/api/jira/historical-incidents` and `/api/jira/similar-incidents/{issue_key}`.
- Added service-aware lexical similarity using current-ticket summaries/descriptions against historical symptoms, root causes, and resolution notes.
- Added historical-incident evidence to PR Risk Radar. A matching prior production incident contributes an explainable +15 risk points, links to Jira, identifies the resolver, and adds a preventive-control review check.
- Risk UI displays the historical ticket, similarity score, resolver, and direct resolution link.

Acceptance evidence: all three historical issues are `Completed`; Jira changelog resolver attribution succeeded. `SUP-1` matched `SUP-9` at 100%. Loan PR #3 matched `SUP-9` at 99% and increased to risk 80 with the historical incident driver.

### M6.7 — Live pull-request Risk Radar workspace — complete

- Added a live GitHub `/api/pull-requests` endpoint for open PR metadata.
- Replaced the static PR selector with a compact one-line-per-PR list matching the CI Failures interaction model.
- Added service filtering and explicit refresh; no risk analysis is shown until a PR row is clicked.
- Clicking a PR loads its deterministic change risk, ownership, dependencies, verification checks, Jira historical matches, resolver attribution, and direct GitHub/Jira links.
- Existing synthetic PRs #1–#3 cover Payments, Gateway, and Loan.
- Added tested branch `feature/identity-token-validation` and opened synthetic Identity Service PR #4, completing coverage across all four services; no PR was merged.
- Historical similarity is constrained to the same service to prevent unrelated incidents from influencing PR risk.

Acceptance evidence: GitHub returned 4 open PRs. Live analysis produced Payments #1 risk 75 with `SUP-10`, Gateway #2 risk 45 without a cross-service match, Loan #3 risk 80 with `SUP-9`, and Identity #4 risk 50 with `SUP-11`. Full verification remained 40 passed, 1 skipped.

### M6.8 — Confluence knowledge source and publishing — complete

- Added separate Confluence site configuration because Jira and Confluence are hosted at different Atlassian subdomains.
- Validated Confluence space `262146` and preserved the user's existing meeting-notes page.
- Added safe Confluence v2 APIs for status, bounded page retrieval, lexical search, and idempotent publishing by exact title.
- Published a `BuildPulse Knowledge Hub` plus 16 child pages covering architecture, service READMEs, KB articles, runbooks, postmortem, references, and the live-demo guide.
- Added `/api/knowledge/status` and `/api/knowledge/search` with repository, Confluence, or combined-source selection.
- Replaced static Knowledge Discovery results with live ranked results, source badges, snippets, match scores, and working Confluence links.
- Added Confluence evidence to the Copilot Knowledge Retrieval stage; source responses now preserve provider and openable URL.
- Markdown is converted to escaped, bounded Confluence storage HTML before publishing.

Acceptance evidence: Confluence returned 17 BuildPulse pages. Combined search for `loan connection pool saturation` returned 15 ranked results from both `confluence` and `repository`, with live page URLs. Full application verification: 43 passed, 1 optional pgvector test skipped.

### M6.9 — Service onboarding and judge-ready knowledge — complete

- Added one new-joiner guide for each of Loan Service, Payments API, API Gateway, and Identity Service.
- Added one API reference per service covering endpoints, request/response contracts, validation, errors, local ports, and security boundaries.
- Added one service/SME profile per service with team, tier, SLOs, escalation signals, primary/backup expertise, and related Jira evidence.
- Added cross-service guidance for ownership/escalation, release-readiness and PR-risk formulas, and security/data/AI boundaries.
- Added a judge/demo FAQ covering live-vs-synthetic provenance, fix generation, agent roles, dependency fallback, merge governance, and the recommended demonstration path.
- Committed and published all 16 documents to healthy branch `codex/full-demo-ecosystem` at `4c505b1`.
- Published the 16 new pages under the existing Confluence knowledge hub without changing or duplicating existing pages.

Acceptance evidence: repository metadata validation passed. Confluence now contains 33 BuildPulse pages: 4 onboarding, 4 API, 4 service/SME, 3 operations, 1 judge FAQ, plus the prior 17-page knowledge set.

### M7 — Streaming Copilot

- Route across CI, repository, knowledge, SME, incidents, and risk.
- Add SSE user-safe progress events (never hidden model reasoning).
- Render evidence cards, confidence drivers, security notice, and audit ID.
- Preserve mock/offline fallback behavior.

### M8 — Persistent incidents, releases, and audit

- Add models/migrations for incidents, timelines, releases, chunks, ingestion jobs, findings, and audit events.
- Seed a coherent Release 24.3 story.
- Compute readiness from incidents, CI, approvals, ownership, and mitigations.
- Add similar-incident/RCA retrieval and real Security Center data.

### M9 — Production hardening

- Authentication/RBAC, mutating-endpoint authorization, rate/size limits.
- Structured logging, tracing, health/readiness checks, metrics, and safe error contracts.
- Postgres/pgvector CI, dependency scanning, browser E2E tests, staging, Azure rehearsal, and rollback plan.

## Configuration contract

Credentials belong only in local `.env` or a managed secret store—never source control or chat.

```env
LLM_PROVIDER=mock
CI_SOURCE=fixture
GITHUB_OWNER=vickypandeyindia462-code
GITHUB_REPO=buildpulse-demo-services
GITHUB_TOKEN=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
```

Hackathon-day switch: set `LLM_PROVIDER=azure_openai`, `CI_SOURCE=github`, and the exact organizer-provided deployment names.

Gemini switch: set `LLM_PROVIDER=gemini`, add the restricted key to local `.env`, and set `GEMINI_MODEL` to the exact model available to that key.

## Verification

```powershell
cd "C:\Users\Vijay\OneDrive\Documents\HACK"
& ".\.venv\Scripts\python.exe" -m pytest -q
& ".\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002 --reload
```

Primary endpoints: `/health`, `/api/agents/status`, `/api/ci/runs`, `/api/ci/failures`, `/api/ci/failures/{run_id}/analysis`, `/api/copilot/chat`, `/api/services`, `/api/services/{service_id}`, `/api/pull-requests/{pr_number}/risk`, `/api/portfolio/overview`.

## Update log

- 2026-09-14 — Initial FastAPI/Streamlit scaffold, database, RAG, SME, scan, and PR submission created.
- 2026-09-14 — Replaced Streamlit UI with approved static frontend served by FastAPI.
- 2026-09-14 — Added separate synthetic services repo and three PR-risk branches.
- 2026-09-14 — Added repository intelligence, ownership/dependencies, and deterministic Risk Radar.
- 2026-09-14 — Added mock agent flow, failed-CI fixture, Copilot, and Azure-ready configuration.
- 2026-09-14 — Connected and verified live `Service CI` workflow history on `release/24.3`.
- 2026-09-14 — Reconciled the full prior ChatGPT history and designated this as the living plan.
- 2026-09-14 — Began M4: centralized runtime settings, normalized GitHub configuration, fixed SQLite ingestion persistence/error reporting, enforced Copilot input redaction, added audit IDs, and added regression tests.
- 2026-09-14 — Completed M4: unified Copilot routing, modernized embeddings, isolated test databases and credentials, removed application deprecations, standardized legacy API validation, and browser-verified the end-to-end mock Copilot flow. Verification: 29 passed, 1 skipped.
- 2026-09-14 — Completed M5: added safe GitHub failed-job collection, bounded text/ZIP log extraction, pre-analysis redaction, deterministic failure classification/confidence, repository/SME/risk/document enrichment, real-failure preference with fixture fallback, dashboard failure card, and browser verification. Verification: 33 passed, 1 skipped.
- 2026-09-14 — Extended M5 UI: added a separate CI Failures workspace with service filtering, selectable failed-job list, full diagnosis/fix details, confidence drivers, ownership, risk, security status, evidence expansion, GitHub linking, and Copilot handoff.
- 2026-09-14 — Began M6: added repository KB discovery/chunking/ranking, source metadata, explicit insufficient-evidence behavior, and a grounded Gemini provider using the official SDK. Verification: 37 tests expected including the optional pgvector skip.
- 2026-09-14 — Completed the full synthetic demo-services expansion on `codex/full-demo-ecosystem`: four runnable APIs, 16 passing service tests, CI matrix, metadata validator, four controlled failure/fix scenarios, operational datasets, SLO-enriched catalog, KB/runbooks/postmortem, references, and a live-fix guide.
- 2026-09-15 — Published `demo/failing-loan-pool` with an isolated 40-versus-60 Loan Service configuration-drift assertion. GitHub Actions run `34881709583` failed as designed and is ready for live BuildPulse diagnosis and remediation.
- 2026-09-15 — Added three genuine multi-service failure waves on `demo/failing-matrix`, yielding at least three failed GitHub jobs per service (13 total including the existing Loan failure). Redesigned the failed-jobs workspace as a compact one-line list with click-only detail expansion. Verification: GitHub job APIs confirmed all 12 matrix jobs failed as designed; BuildPulse grouped live results as Loan 4 / Payments 3 / Gateway 3 / Identity 3; application tests remained 37 passed, 1 skipped.
- 2026-09-15 — Completed live Jira integration for project `SUP`: added safe connector/status/issues/dashboard APIs, idempotent synthetic seeding, created `SUP-1` through `SUP-8`, and replaced Executive Dashboard release/incident/attention/distribution fixtures with live Jira data. Verification: 8 issues, 4 incidents, 7 blockers, 64% readiness, 2 issues per service; 39 tests passed, 1 skipped.
- 2026-09-15 — Added Jira historical-resolution intelligence: created/resolved `SUP-9`–`SUP-11`, extracted resolver attribution and resolution evidence, added current-issue similarity APIs, and incorporated matching production history into PR risk scoring and UI. Live evidence: `SUP-1` → `SUP-9` 100% similar; Loan PR #3 → `SUP-9` 99% similar and risk 80.
- 2026-09-15 — Rebuilt Risk Radar as a click-to-expand live PR list, added service filtering, opened Identity demo PR #4, and verified four-service PR analysis with service-constrained Jira historical matching.
- 2026-09-15 — Added Confluence as a first-class knowledge source, published a 17-page BuildPulse hierarchy, connected multi-source search and Copilot evidence, and replaced static Knowledge Discovery cards with live openable results. Verification: 43 passed, 1 skipped.
- 2026-09-15 — Added and published 16 judge-ready service documents: four onboarding guides, four API references, four service/SME profiles, three operational policies, and a demo FAQ. Confluence knowledge increased from 17 to 33 BuildPulse pages; repository commit `4c505b1`.
- 2026-09-15 — Prepared the BuildPulse application for repository handoff: removed disposable smoke-test and auto-commit helpers, removed temporary content-staging directories, sanitized the Git remote, retained supported operational utilities, and excluded local secrets and runtime database state from the release commit.
- 2026-09-15 — Improved Copilot conversation quality: greetings now receive a natural capability-aware response without irrelevant retrieval, while offline answers synthesize only retrieved BuildPulse evidence with source markers instead of returning a generic mock template. Live Gemini remains an environment-only switch and receives the same bounded, redacted evidence context.
- 2026-09-15 — Hardened Copilot greeting and failure UX: punctuation-bearing greetings bypass retrieval, and frontend request failures now show a neutral retry notice rather than an invented Loan Service recommendation.
- 2026-09-15 — Added resilient grounded-provider failover: transient Gemini/Azure errors now fall back to deterministic answers synthesized from the already-retrieved internal evidence, preserving sources and returning provider diagnostics without exposing secrets or emitting HTTP 500.
