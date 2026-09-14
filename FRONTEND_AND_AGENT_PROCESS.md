# Frontend-First Workflow and Agent-by-Agent Plan

## Overview
This document defines a clear, gated process: complete frontend work first, obtain your confirmation after testing, then proceed to each backend agent (`ingestion`, `rag`, `security_check`, `sme_discovery`) one-by-one. Each phase contains review, implement, test, and confirmation steps.

## Prerequisites
- Activate the project's virtual environment (Windows PowerShell):

```powershell
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Tests: `pytest` is used for backend tests.

## Frontend Phase (Block until confirmation)
1. Explore frontend
   - Files: `frontend/app.py`, `frontend/Dockerfile`, `frontend` assets.
   - Goal: identify app framework, dependencies, and run steps.

2. Start frontend dev server (local)
   - Typical commands to try (pick one based on discovery):

```powershell
python frontend/app.py
# or
python -m flask run --app frontend.app
# or
docker-compose up frontend
```

3. Run frontend smoke tests
   - Manual check: open UI in browser at the printed host/port.
   - Automated: if frontend has test suite, run it (example):

```powershell
pytest frontend/tests -q
```

4. Audit frontend issues
   - Record errors, console logs, network failures, and failing tests.
   - Prioritize fixes: blocking vs non-blocking.

5. Implement frontend fixes
   - Make minimal, focused changes to fix blocking issues and unit tests.
   - Keep commits small; include test updates.

6. Add frontend tests
   - Add unit/integration tests covering regressions fixed.
   - Ensure test run locally: `pytest frontend/tests -q`.

7. Request frontend confirmation
   - When frontend tests pass and manual checks are OK, ask for your confirmation to proceed to agents.

## Agent-by-Agent Phase (Repeat per agent)
For each agent in `backend/agents/` (sequence: `ingestion`, `rag`, `security_check`, `sme_discovery`) perform:

1. Explore agent
   - Files: `backend/agents/<agent>.py`, any imports in `backend/app/routers`.
   - Read tests that reference the agent: check `backend/tests` for related tests.

2. Run agent unit tests
   - Run only related tests, example:

```powershell
pytest backend/tests/test_agents.py::test_<specific> -q
```

3. Audit failures and behavior
   - Capture stack traces, failing assertions, and expected vs actual.

4. Implement fixes or improvements
   - Make minimal, well-tested changes.
   - If changes affect API contracts, update routers in `backend/app/routers/` and update documentation.

5. Add/Update tests
   - Create or update unit tests to cover new behavior and prevent regressions.

6. Run full backend tests for the agent

```powershell
pytest backend/tests -q
```

7. Request confirmation for this agent
   - Only after you confirm, proceed to the next agent.

## Final Integration Testing
- After all agents are confirmed, run full test suite:

```powershell
pytest -q
```

- Run any end-to-end scripts in `backend/scripts/` like `ingest_and_query.py` to validate workflows.

## Branching, Commits, and PRs
- Work on a feature branch: `feature/frontend-fix-xxx` → open PR.
- For agents: `feature/agent-<name>-fix` per agent.
- Include test summary and manual test steps in PR description.

## Reporting & Artifacts
- For each phase, collect:
  - Test run output (passing/failing counts)
  - Failing stack traces and patches applied
  - Screenshots / screen recordings for UI regressions

## Suggested Timeline (example)
- Frontend exploration & smoke: 1 day
- Frontend fixes & tests: 1–2 days
- Per-agent review & fix: 0.5–2 days depending on complexity

## Next Steps (after you confirm)
- I will start with the frontend exploration and run the dev server.
- I will create small patches and open PRs; I'll run tests locally and share results.

---
Document created by GitHub Copilot assistant. Follow-up: tell me "Proceed with frontend" to start the first hands-on phase.
