# BuildPulse — Full Implementation & Production Readiness Plan

> Single-source plan for taking BuildPulse from prototype → production. This file will be updated after each milestone; append an entry to the "Update Log" (bottom) whenever you complete a step.

## Purpose
Provide a step-by-step, auditable implementation plan that any engineer or agent can follow to finish, harden, and operate BuildPulse in production.

## Scope
- Frontend (Streamlit) UX and pages
- Backend (FastAPI) services, security layer, orchestrator, agents
- Data storage: PostgreSQL + pgvector (production), SQLite only for local dev
- CI/CD, secrets management, infra provisioning, observability, and runbooks

## Assumptions
- Repo: `vickypandeyindia462-code/Hackathon-26`
- Local dev uses `.env` for secrets (never committed)
- Production will use secret stores (GitHub Actions secrets, Azure Key Vault, or similar)
- Docker is available for local containerized testing; Kubernetes (AKS/EKS/GKE) for production

## High-level phases
1. Discovery & Planning
2. Design & Wireframes
3. Core Implementation
4. Quality & Security Hardening
5. Integration & End-to-end Testing
6. CI/CD + Infra Provisioning
7. Staging Deployment & Validation
8. Production Release
9. Operate & Iterate

For each phase below, the plan lists tasks, acceptance criteria, artifacts, and owners (if known).

---

## 1) Discovery & Planning (status: complete)
Tasks
- Review `FullUI.md` and confirm UX requirements. (Done)
- Inventory current prototype features (frontend demo mode, `/submit/pr` endpoint, demo data). (Done)
- Define production acceptance criteria and SLA targets.

Acceptance
- Documented UI and API spec.
- Agreed list of pages and flows (see `FullUI.md`).

Artifacts
- `FullUI.md`, `FULL_IMPLEMENTATION_PLAN.md`

Owner: Product / Engineering lead

---

## 2) Design & Wireframes (status: in-progress)
Tasks
- Create high-fidelity wireframes for each major page in `FullUI.md`.
- Choose fonts, color tokens, and component spacing (system in `FullUI.md`).
- Define responsive breakpoints and accessibility targets (WCAG AA baseline).

Acceptance
- Approved mockups for Desktop and Mobile.

Artifacts
- Mockup images or design tokens file.

Owner: Designer / Frontend engineer

---

## 3) Core Implementation (status: in-progress)
This is split between frontend and backend subtasks.

3.1 Frontend
- Implement pages listed in `FullUI.md` inside `frontend/app.py`. (Scaffolded)
- Add demo JSON files under `frontend/demo_data/` for local testing. (Added)
- Implement the Contribute workflow to call backend `/submit/pr` (connected).

3.2 Backend
- Implement `/submit/pr` endpoint that creates branches, commits submission, and opens PRs. (Implemented)
- Provide a graceful configuration pattern via `.env` and fallback logic for development. (Implemented)
- Add endpoints for RAG, AI chat, SME lookup, security scan as mocks or integrations.

Acceptance
- Local frontend can run with `streamlit run frontend/app.py` and show all pages.
- Backend runs with `uvicorn backend.app.main:app --reload --port 8000` and handles `/submit/pr`.
- PR creation can be exercised end-to-end against a personal repo with a valid PAT.

Artifacts
- `frontend/app.py`, `backend/app/routers/pr_submit.py`, demo JSON files

Owner: Frontend & Backend engineers

Commands (local dev)
```powershell
# Start backend
uvicorn backend.app.main:app --reload --port 8000
# Start frontend
streamlit run frontend/app.py
```

Security note: store `GITHUB_TOKEN` only in `.env` for local dev; in production use secret store. Rotate tokens immediately after testing.

---

## 4) Quality & Security Hardening (status: pending)
Tasks
- Add input validation, size limits, and rate-limiting for ingestion endpoints.
- Add authentication / RBAC for contributer endpoints (OIDC, Azure AD, or GitHub App).
- Integrate security scanning for dependencies (Dependabot, Snyk) and linters.
- Ensure PII redaction pipeline is enforced for all uploads.

Acceptance
- No obvious injection or large-file vulnerabilities.
- All endpoints authenticated where necessary in staging.

Artifacts
- Security design doc, threat model, IAM map

Owner: Security eng / SRE

---

## 5) Integration & End-to-end Testing (status: pending)
Tasks
- Implement automated tests: unit, integration (FastAPI + DB), end-to-end (Playwright/selenium for UI flows).
- Add test data seed scripts and deterministic test harness.

Acceptance
- CI runs tests on PRs; coverage goals met (e.g., 70%+)

Artifacts
- `tests/` unit and integration suite, GitHub Actions workflows

---

## 6) CI/CD & Infra Provisioning (status: pending)
Tasks
- Add GitHub Actions workflows: lint, test, build, container image push, deploy to staging.
- Provision infra: Azure/AWS/GCP resources for Postgres (managed), object storage, secrets.
- Containerize services (backend, frontend) and publish images.

Acceptance
- Merges to `main` automatically run CI; builds are pushed to registry.

Artifacts
- `.github/workflows/*`, `Dockerfile`, `docker-compose.yml` (dev), Terraform/ARM/CloudFormation configurations.

Owner: DevOps / Platform eng

---

## 7) Staging Deployment & Validation (status: pending)
Tasks
- Deploy to staging cluster, run end-to-end smoke tests.
- Validate monitoring, logging, alerting pipelines.

Acceptance
- Staging stable for 48 hours under simulated load.
- Observability dashboards show no critical errors.

---

## 8) Production Release (status: pending)
Tasks
- Schedule release window, run final dry-run.
- Perform DB migrations via controlled process.
- Cut release; confirm post-deploy health checks.

Acceptance
- Production health OK; rollback plan tested.

---

## 9) Operate & Iterate (status: pending)
Tasks
- Monitor runbooks, create SLOs/SLIs, on-call runbooks.
- Iterate features, add metrics and improvements.

Acceptance
- On-call runbook exists and is validated.

---

## Deployment & Rollback Plan (summary)
- Use blue/green or canary deployments for minimal risk.
- Keep DB migrations backwards-compatible or use migration locking and roll-forward plans.
- Rollback: restore previous image tag and database snapshot if critical.

---

## Secrets & Credentials
- NEVER commit secrets to repo. Add `.env` to `.gitignore` (already done).
- Production: use GitHub Actions secrets and managed key vaults.
- Rotate tokens after use and log rotations.

---

## Observability & Ops
- Add metrics: request latency, error rate, ingest rate, queue depth.
- Logs: structured logs (JSON) with tracing IDs.
- Alerts: page on high error rate or ingestion failures; Slack integration for the attention feed.

---

## How this file is updated (Update Log format)
Whenever a major step is completed, append an entry under "Update Log" with the following fields:
- Date (YYYY-MM-DD)
- Step completed (phase/task)
- Short notes and links to commits or PRs
- Owner

Example:
```
2026-09-14 — Core Implementation: Added `/submit/pr` endpoint, frontend pages scaffolded. PR: https://github.com/..../pull/2 — @yourname
```

---

## Current status (snapshot)
- Frontend: pages scaffolded for all views described in `FullUI.md` (`frontend/app.py`).
- Demo data: added `frontend/demo_data/*` (attention_feed, incidents, critical_owners, recent_submissions, etc.).
- Backend: `/submit/pr` implemented with reviewers support; `.env` loading implemented.
- Local dev: `.env` present (local), switched to SQLite for dev DB to allow local startup.
- Repo: workspace pushed to `main` in GitHub repo.
- PR creation: tested successfully; PR opened via `/submit/pr`.

---

## Next immediate actions (recommended)
1. Polish UI visuals, fonts and evidence cards (frontend). — Owner: Frontend
2. Add automated tests for PR endpoint and ingestion flow. — Owner: Backend
3. Create GitHub Actions workflows for CI (lint, tests). — Owner: DevOps
4. Replace local `.env` testing token with a GitHub App or fine-grained PAT and store in secrets. — Owner: Security/Platform

---

## Update Log
- 2026-09-14 — Core Implementation: scaffolded all frontend pages, added demo data, implemented `/submit/pr` with reviewers; tested PR creation end-to-end; persisted token in `.env` for local dev and pushed workspace to `main`. (owner: engineering)


---

*If you want, I will append an update entry to this file every time I complete a task; confirm and I will commit updates automatically.*
- 2026-09-14 — Enable auto-update helper: add scripts/log_update.py  (owner: automation (copilot))
