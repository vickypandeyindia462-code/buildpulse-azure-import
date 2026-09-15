# BuildPulse (minimal scaffold)

This workspace contains a minimal scaffold for the BuildPulse demo:

- `backend/app/main.py` — FastAPI app with `/health` endpoint
- `frontend/web/` — approved BuildPulse HTML, CSS, and JavaScript interface
- `docker-compose.yml` — local compose with Postgres and API; the API serves the UI
- `.env.example` — environment variables

Quick local checks (Windows PowerShell):

```powershell
cd "C:\Users\Vijay\OneDrive\Documents\HACK"
# activate venv
.\.venv\Scripts\Activate.ps1
# run backend (uvicorn)
.\.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload
# Open the BuildPulse UI at http://127.0.0.1:8000
```

You can also run `docker compose up --build`; then open http://127.0.0.1:8000.

## Agent demo mode (no keys required)

BuildPulse starts in deterministic mock mode. The UI Copilot uses the local
synthetic service repository, a failed Loan Service CI fixture, architecture
documents, and explicit risk/SME data. This makes the demo reliable without a
cloud account.

Useful API checks while the server is running:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/api/agents/status
Invoke-RestMethod http://127.0.0.1:8002/api/ci/failures/demo-run-2431/analysis
```

The demo service CI workflow is in the separate
`buildpulse-demo-services/.github/workflows/service-ci.yml` repository. Push
that workflow when you are ready for GitHub Actions to create live runs.

## Hackathon-day Azure switch

Copy `.env.example` to `.env`. Keep `.env` local and never commit it. After
the organizers provide the Azure Foundry deployment, change only these values:

```env
LLM_PROVIDER=azure_openai
CI_SOURCE=github
AZURE_OPENAI_ENDPOINT=<provided endpoint>
AZURE_OPENAI_API_KEY=<provided key>
AZURE_OPENAI_CHAT_DEPLOYMENT=<provided deployment name>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<provided embedding deployment name>
GITHUB_TOKEN=<fine-grained read-only token>
```

`AZURE_OPENAI_API_VERSION` is optional; set it only if the Azure endpoint
details provided by the organizers require one. The application uses the
deployment names you configure rather than hard-coding a model name.

For the current public demo repository, you can enable real workflow/job
collection immediately with `CI_SOURCE=github`; `GITHUB_TOKEN` is optional.
Add a fine-grained read-only token later for private repositories, job-log
downloads, or more GitHub API capacity.
