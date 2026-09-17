# BuildPulse Hackathon VM Migration Runbook

This is the complete post-migration checklist for running BuildPulse on the hackathon VM. Do not copy the current local `.env` file or commit credentials. Create a new `.env` directly on the VM.

## 1. Required VM software

- Git
- Docker Desktop with Linux containers enabled
- Docker Compose v2 (`docker compose`)
- Optional for running outside Docker: Python 3.11+

Verify:

```powershell
git --version
docker version
docker compose version
```

Docker Desktop must be running before continuing.

## 2. Copy the repositories

The supplied Docker Compose configuration expects the application repository and demo-services repository to be siblings:

```text
workspace/
├── HACK/
└── buildpulse-demo-services/
```

If the second repository is stored elsewhere, update the `api.volumes` entry in `docker-compose.yml`:

```yaml
volumes:
  - ../buildpulse-demo-services:/data/demo-services:ro
```

Keep this mount read-only. BuildPulse only needs to inspect repository documentation and metadata.

## 3. Create the VM environment file

From the `HACK` directory:

```powershell
Copy-Item .env.example .env
```

On Linux:

```bash
cp .env.example .env
```

Then edit `.env`. Never add `.env` to Git.

### Required database settings

Use the Docker service name `postgres`, not `localhost`, because the API runs inside the Compose network:

```env
POSTGRES_USER=buildpulse
POSTGRES_PASSWORD=REPLACE_WITH_A_STRONG_PASSWORD
POSTGRES_DB=buildpulse
DATABASE_URL=postgresql+psycopg://buildpulse:REPLACE_WITH_A_STRONG_PASSWORD@postgres:5432/buildpulse
EMBEDDING_DIM=1536
```

Use the same password in `POSTGRES_PASSWORD` and `DATABASE_URL`. If the password contains URL-special characters, URL-encode it in `DATABASE_URL`.

### Repository and GitHub settings

Inside Docker, the repository path must remain `/data/demo-services`:

```env
DEMO_SERVICES_REPO_PATH=/data/demo-services
CI_SOURCE=github
GITHUB_OWNER=YOUR_GITHUB_ORGANIZATION_OR_USERNAME
GITHUB_REPO=YOUR_REPOSITORY_NAME
GITHUB_TOKEN=YOUR_READ_ONLY_GITHUB_TOKEN
```

The GitHub token should have only the permissions needed to read repositories, pull requests, Actions runs, and logs. Do not use a personal token with write or administration access.

### Choose one chat-model provider

Only configure the provider you intend to demonstrate. BuildPulse falls back to its grounded local response provider if the selected remote model is unavailable.

OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=YOUR_OPENAI_KEY
OPENAI_MODEL=YOUR_AVAILABLE_GPT_MODEL
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_BASE_URL=
```

Anthropic/Sonnet:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY
ANTHROPIC_MODEL=YOUR_AVAILABLE_SONNET_MODEL
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_KEY
GEMINI_MODEL=YOUR_AVAILABLE_GEMINI_MODEL
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Azure OpenAI / Azure AI Foundry:

```env
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=YOUR_ENDPOINT
AZURE_OPENAI_API_KEY=YOUR_KEY
AZURE_OPENAI_API_VERSION=YOUR_SUPPORTED_API_VERSION
AZURE_OPENAI_CHAT_DEPLOYMENT=YOUR_CHAT_DEPLOYMENT_NAME
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=YOUR_EMBEDDING_DEPLOYMENT_NAME
```

Use deployment names for Azure, not assumed public model names.

### Optional Jira and Confluence integrations

```env
JIRA_BASE_URL=https://YOUR_SITE.atlassian.net
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
JIRA_EMAIL=YOUR_ATLASSIAN_EMAIL
JIRA_API_TOKEN=YOUR_ATLASSIAN_API_TOKEN

CONFLUENCE_BASE_URL=https://YOUR_SITE.atlassian.net
CONFLUENCE_SPACE_ID=YOUR_SPACE_ID
CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY
```

Use a dedicated read-only integration account if possible. Leaving these values blank keeps the application usable with repository and fixture data.

## 4. Validate configuration before starting

From the `HACK` directory:

```powershell
docker compose config --quiet
```

This command must finish without an error. It validates Compose structure but does not verify credentials.

## 5. Build and start BuildPulse

```powershell
docker compose up --build -d
docker compose ps
```

Expected services:

- `postgres`: healthy
- `api`: running and exposed on port `8000`

Watch startup logs if either service is unhealthy:

```powershell
docker compose logs --tail 200 postgres
docker compose logs --tail 200 api
```

The application automatically creates the PostgreSQL `vector` extension and required tables during API startup.

## 6. Build the knowledge index

Indexing is explicit so a deployment never incurs embedding costs unexpectedly. Run it once after startup and again whenever repository documentation changes:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/knowledge/index
```

Linux/curl equivalent:

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/index
```

After Jira, Confluence, and GitHub are configured, synchronize every approved
read-only source with:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/knowledge/sync
```

This operation is idempotent and does not modify any upstream ticket, page,
repository, pull request, or workflow.

The response should show:

- `backend`: `postgresql`
- `documents`: greater than zero
- `embedding_failures`: `0`
- `vector_search`: `true`

If `embedding_failures` is greater than zero, text is still indexed and keyword retrieval continues to work. Correct the embedding credentials or deployment name, then rerun the same indexing command to backfill vectors.

## 7. Verify the complete deployment

### Application health

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected: `status: ok`.

### Model and trusted-tool status

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/agents/status
```

Confirm:

- `mode` is `live`
- `provider_ready` is `true`
- `llm_provider` matches the selected provider
- Four trusted tools are listed

The trusted tools should be:

1. `get_ci_failure_analysis`
2. `get_pull_request_risk`
3. `search_engineering_knowledge`
4. `get_service_ownership`

### Retrieval status

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/knowledge/status
```

Confirm the retrieval backend is PostgreSQL, indexed document count is greater than zero, and vector search is enabled.

### Retrieval smoke test

Open:

```text
http://127.0.0.1:8000/api/knowledge/search?q=connection%20pool%20runbook&source=repository
```

Results should include `retrieval_method` values such as `pgvector` or `hybrid`.

### UI and Copilot smoke test

Open `http://127.0.0.1:8000/` and verify:

1. Developer and Engineering Lead workspaces toggle correctly.
2. Developer navigation shows focused operational work rather than a separate knowledge-discovery page.
3. Open Failed Pipelines, select a failed job, choose Investigate Failure, then Ask Copilot.
4. Copilot diagnoses the selected run directly without asking which job failed.
5. The answer shows evidence, provider information, and an audit identifier.
6. Ask “Who owns the Payments API?” and verify the answer is grounded in the service catalog.
7. Ask for a runbook or prior resolution and verify indexed knowledge sources are shown.

### Optional test suite

Inside the API container:

```powershell
docker compose exec api python -m pytest -q
```

The last local verification before migration was `70 passed, 1 skipped`. On a correctly configured PostgreSQL VM, the pgvector test should also be eligible to run.

## 8. Security checklist

- Never commit `.env`, API keys, tokens, or VM credentials.
- Use read-only GitHub and Atlassian credentials.
- Do not expose PostgreSQL port `5432` publicly. Remove the Compose `ports` mapping for PostgreSQL if host access is unnecessary.
- Restrict inbound port `8000` to the hackathon network or place the application behind an authenticated reverse proxy.
- Rotate all temporary hackathon credentials after the event.
- Keep the demo-services volume read-only.
- Do not add deployment-write, Jira-write, merge, rollback, shell, or arbitrary HTTP tools to the Copilot allowlist without separate authorization controls.
- Check logs for secrets before screen sharing.

## 9. Updating the VM after code changes

```powershell
git pull
docker compose up --build -d
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/knowledge/index
```

Then repeat the health, provider-status, retrieval-status, and UI smoke tests.

## 10. Troubleshooting

### Docker named-pipe or permission error

Start Docker Desktop and wait until the engine reports that it is running. Run the terminal as the same Windows user that launched Docker Desktop. If organizational policy blocks Docker engine access, ask the VM administrator to add the account to the appropriate Docker users group and sign out/in.

### API cannot connect to PostgreSQL

- Confirm `DATABASE_URL` uses host `postgres`, not `localhost`.
- Confirm the password matches `POSTGRES_PASSWORD`.
- Check `docker compose ps` and PostgreSQL logs.
- If credentials were changed after the PostgreSQL volume was first created, the existing volume retains its original database credentials. For a disposable new hackathon database only, stop the stack and deliberately recreate its volume. Do not remove a volume containing data you need.

### Provider reports demo mode or fallback

- Confirm `LLM_PROVIDER` exactly matches `openai`, `anthropic`, `gemini`, or `azure_openai`.
- Confirm the corresponding key, endpoint, model, or deployment is available to that account.
- Restart the API after changing `.env`: `docker compose up -d --force-recreate api`.
- Inspect `docker compose logs --tail 200 api` without sharing secret values.

### Knowledge search works but vector search is false

- Confirm the backend is PostgreSQL.
- Confirm a valid embedding key/deployment is configured.
- Confirm `EMBEDDING_DIM` matches the embedding model output; the default `text-embedding-3-small` configuration uses `1536`.
- Rerun `POST /api/knowledge/index` after correcting configuration.

### GitHub failures are missing

- Confirm `CI_SOURCE=github`.
- Verify owner and repository names.
- Confirm the token can read Actions runs and logs.
- BuildPulse intentionally retains a labelled fixture failure when GitHub has no current failed run, so the remediation demonstration remains available.

## Demo-ready definition

The VM is ready when all of the following are true:

- Docker services are healthy.
- `/health` returns `ok`.
- The selected model provider reports ready.
- PostgreSQL retrieval reports indexed documents and vector search enabled.
- Failed-pipeline Ask Copilot produces a grounded diagnosis and remediation.
- Ownership and runbook questions return evidence-backed answers.
- Developer/Lead workspace switching works.
- No credentials appear in Git, browser output, screenshots, or application logs.
