# BuildPulse VM Deployment and Handoff Guide

This document is the single handoff reference for deploying BuildPulse to the hackathon VM through GitHub and Azure DevOps. It is safe to give to another coding agent. It intentionally contains **no passwords, PATs, API keys, connection strings, or personal data**.

## 1. Objective

Deploy the BuildPulse engineering-intelligence dashboard to the hackathon VM so developers and leads can use:

- focused Developer and Engineering Lead dashboards;
- failed CI pipeline investigation and remediation;
- grounded Copilot chat over service documentation, Jira, Confluence, GitHub CI/PR information, and service ownership;
- PostgreSQL/pgvector knowledge retrieval;
- visible service/provider health and answer provenance.

The desired delivery path is:

```text
Public GitHub repository
        ↓
Azure DevOps Pipeline
        ↓ (self-hosted agent)
Hackathon VM
        ↓
Docker Compose + BuildPulse API + managed PostgreSQL
```

The VM should use a **self-hosted Azure DevOps agent**. This is preferable to SSH for this demo because Docker Desktop is already on the VM and no public SSH endpoint is required.

## 2. Current project state

### Repositories and important commits

The deployment source repository is:

<https://github.com/vickypandeyindia462-code/buildpulse-azure-import>

The completed feature release was pushed to its `main` branch at:

```text
f9a9818 — feat: add grounded service knowledge and dashboard intelligence
```

Azure DevOps has already been connected to this GitHub repository. A starter pipeline was created and its first job succeeded. That proves GitHub-to-Azure-DevOps checkout works, but the starter pipeline **does not deploy the application yet**.

The older local source repository is `HACK`. The GitHub target had unrelated history before the release, so its `main` branch was deliberately force-updated with approval. The previous target commit was `c69994d` and is recoverable if needed.

### Features implemented

- Collapsible navigation and fixed top-bar identity.
- Developer / Engineering Lead workspace switch.
- Service-status modal showing Jira, GitHub, model, database, and RAG health.
- Chat answer provenance so the UI can distinguish model responses from grounded fallback responses.
- Developer priority work list, calendar/notes, assigned Jira items, and contributor recognition.
- More focused pipeline remediation with a default individual service, not "all services".
- Grounded CI investigation using job logs, service context, runbooks, and retrieval evidence.
- PostgreSQL + pgvector retrieval store with keyword/hybrid fallback.
- Tool-oriented chat runtime for CI failure analysis, PR risk, engineering knowledge search, and service ownership.
- New seed service handbooks for Loan Service, Payments API, API Gateway, and Identity Service.

Each service handbook covers architecture, roles and responsibilities, progress and future plan, historical incidents, new-joiner tools, entitlement requests, risk profile, and rules/regulations.

### Knowledge already created locally/external systems

- Four managed service handbook files are in `backend/knowledge_seed/docs/service-handbooks/`.
- Four matching Confluence pages were created.
- A resolved API Gateway historical incident (`SUP-27`) was created in Jira.
- A prior local knowledge sync indexed 99 documents:
  - 41 repository documents;
  - 41 Confluence documents;
  - 4 Jira incidents;
  - 13 GitHub CI records.

The VM will build its own database/index, so run knowledge sync again after the VM starts.

### Local verification already completed

Focused tests passed after the service knowledge changes:

```text
30 passed
```

Live retrieval checks produced precise answers for new-joiner access, Payments API roadmap, and API Gateway architecture.

## 3. Security rules — do not skip

1. Never commit `.env`, API keys, PATs, Jira/Confluence tokens, PostgreSQL credentials, or VM credentials.
2. Do not paste secrets into Azure Pipeline YAML, commit messages, logs, screenshots, or chat.
3. Use Azure DevOps secret variables or a secure local VM `.env` file when a secret is needed.
4. Use read-only GitHub, Jira, and Confluence credentials whenever possible.
5. Give the Azure DevOps agent only the access it needs. The registration PAT needs `Agent Pools: Read & manage`; it should expire after the hackathon.
6. Restrict the dashboard port to the hackathon network. Do not expose PostgreSQL port 5432 publicly.

## 4. What the VM needs before deployment

The VM should be Windows unless the team explicitly chooses Linux. Install/verify:

- Git;
- Docker Desktop running with Linux containers enabled;
- Docker Compose v2;
- network access to GitHub, Azure DevOps, the managed PostgreSQL instance, the selected AI provider, and any approved Jira/Confluence/GitHub APIs.

Verify from PowerShell:

```powershell
git --version
docker version
docker compose version
```

Docker Desktop must be running under the same signed-in Windows user that runs the self-hosted agent.

## 5. Azure DevOps agent setup — current step

### Agent pool answer

When `config.cmd` asks for the agent pool, enter:

```text
Default
```

Or press Enter if `Default` is offered as the default.

### Register the agent

In Azure DevOps:

1. Open **Project settings → Agent pools → Default → New agent**.
2. Download the Windows agent ZIP.
3. Create `C:\azagent` and extract the ZIP contents there. The folder must contain `config.cmd`, `run.cmd`, `bin`, and `externals`.
4. In PowerShell:

```powershell
cd C:\azagent
.\config.cmd
```

5. Use this organization URL when asked for the server URL:

```text
https://dev.azure.com/pncapifest/
```

6. Choose `PAT` authentication and use a newly generated Azure DevOps PAT with **Agent Pools: Read & manage**. Do not share the PAT.
7. Set the agent name to:

```text
buildpulse-vm
```

8. Accept `_work` for the work folder.
9. For the first demo, answer **No** when asked to run as a Windows service. Run it interactively instead:

```powershell
.\run.cmd
```

Keep that terminal open. In **Project settings → Agent pools → Default**, verify that `buildpulse-vm` is **Online**.

Why interactive first: Docker Desktop commonly grants engine access to the logged-in user, not to a Windows service account. A service setup can be considered later only after Docker permissions are confirmed.

## 6. Prepare persistent VM configuration

Create a location that is outside the Azure agent checkout folder. Agent checkouts may be cleaned between runs.

```powershell
New-Item -ItemType Directory -Force -Path C:\BuildPulse\config
```

Create this file manually on the VM:

```text
C:\BuildPulse\config\.env
```

Start from `.env.example` in the repository. Do **not** copy a local workstation `.env` file because it may contain incorrect paths or credentials.

The actual deployment pipeline will copy this local protected file into its temporary checkout immediately before Compose starts, then the checkout is discarded on cleanup.

## 7. Configure the provisioned PostgreSQL database

### Recommended approach

Use the provisioned PostgreSQL instance for BuildPulse data and vector retrieval. It must allow network traffic from the VM and support the `vector` extension / pgvector. The application creates its tables at startup.

Use the provider-issued connection details in `C:\BuildPulse\config\.env`. The application uses SQLAlchemy with the `psycopg` driver, so the URL must use this form:

```env
DATABASE_URL=postgresql+psycopg://DATABASE_USER:URL_ENCODED_PASSWORD@DATABASE_HOST:5432/DATABASE_NAME?sslmode=require
```

Set a dimension compatible with the configured embedding model:

```env
EMBEDDING_DIM=1536
```

For Gemini `gemini-embedding-001`, confirm its vector dimension in the provider setup and set `EMBEDDING_DIM` to the actual returned dimension if it differs. If using OpenAI `text-embedding-3-small`, 1536 is appropriate.

### Important Compose behavior

`docker-compose.yml` was updated to honor `DATABASE_URL` from the VM `.env`. If it is absent, it falls back to the bundled `postgres` Compose service for local development.

Keep the `postgres` Compose service in place initially; the API health dependency remains useful. If the team later wants to remove the local database entirely, change the Compose dependency and health check deliberately and test the full stack. Do not make that change during the final demo setup without time to validate it.

### Database validation

Before app startup, confirm firewall/security-group rules allow the VM to connect to the managed database. Do not expose the database publicly. After startup, call the knowledge status endpoint as described in section 11.

## 8. Replace the Claude / Sonnet configuration

The local machine’s configured Anthropic endpoint was an Azure AI Foundry-style endpoint and did not respond as a compatible Anthropic Messages API endpoint. This is why the app showed grounded fallback answers locally.

On the VM, choose **one** provider and configure it correctly. For direct Anthropic/Sonnet API use, put only these values in `C:\BuildPulse\config\.env`:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=REPLACE_WITH_YOUR_SECRET
ANTHROPIC_MODEL=REPLACE_WITH_YOUR_ACTUAL_AVAILABLE_SONNET_MODEL
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

Rules:

- Use a model ID enabled for your Anthropic account; do not assume a model name.
- `ANTHROPIC_BASE_URL` should be the direct Anthropic API endpoint unless the gateway explicitly supports the Anthropic Messages API contract.
- Do not put an Azure AI Foundry endpoint into `ANTHROPIC_BASE_URL` unless the gateway documentation says it accepts Anthropic-compatible `/v1/messages` requests and required headers.
- Restart the API after changing any model variables.

### Gemini option

Gemini embeddings were working locally. Gemini can be used for both chat and embeddings if the credentials are valid:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=REPLACE_WITH_YOUR_SECRET
GEMINI_MODEL=REPLACE_WITH_YOUR_AVAILABLE_MODEL
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

### Azure OpenAI / Azure AI Foundry option

If the hackathon gives an OpenAI-compatible Azure deployment, configure it as Azure OpenAI instead of Anthropic:

```env
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=REPLACE_WITH_ENDPOINT
AZURE_OPENAI_API_KEY=REPLACE_WITH_SECRET
AZURE_OPENAI_API_VERSION=REPLACE_WITH_SUPPORTED_VERSION
AZURE_OPENAI_CHAT_DEPLOYMENT=REPLACE_WITH_DEPLOYMENT_NAME
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=REPLACE_WITH_EMBEDDING_DEPLOYMENT_NAME
```

Use Azure **deployment names**, not public model names.

### How to confirm the provider is truly live

After deployment, call:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/agents/status
```

Confirm the selected provider reports ready. In the UI, a source/provenance indicator should identify model vs grounded fallback behavior. A fallback answer is still grounded in retrieved evidence, but it is not proof that the live remote model is working.

## 9. Configure read-only knowledge sources

Add only services that are available and approved for the demo.

### GitHub CI and pull-request data

```env
CI_SOURCE=github
GITHUB_OWNER=vickypandeyindia462-code
GITHUB_REPO=buildpulse-demo-services
GITHUB_TOKEN=REPLACE_WITH_READ_ONLY_TOKEN
```

The GitHub token should read repositories, Actions runs/logs, and pull requests; do not grant write/admin permissions.

### Jira

```env
JIRA_BASE_URL=https://YOUR_SITE.atlassian.net
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
JIRA_EMAIL=YOUR_ATLASSIAN_EMAIL
JIRA_API_TOKEN=REPLACE_WITH_SECRET
```

### Confluence

```env
CONFLUENCE_BASE_URL=https://YOUR_SITE.atlassian.net
CONFLUENCE_SPACE_ID=YOUR_SPACE_ID
CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY
```

Use an integration identity with read-only access where possible. If a source is blank, the application continues with repository knowledge and local seed handbooks.

## 10. Demo-services repository requirement

Compose expects the BuildPulse app repository and demo-services repository to be siblings:

```text
<workspace>/
├── buildpulse-azure-import/
└── buildpulse-demo-services/
```

The `api` container mounts the latter as `/data/demo-services` in read-only mode. The Azure deployment pipeline must ensure that the demo-services repository is cloned next to its BuildPulse checkout or change the volume source deliberately.

The default runtime location inside Docker must stay:

```env
DEMO_SERVICES_REPO_PATH=/data/demo-services
```

## 11. First manual VM launch before automating deployment

Do this once to validate credentials and Docker independently of Azure Pipelines.

1. Clone both repositories to sibling directories on the VM.
2. Copy `C:\BuildPulse\config\.env` to the BuildPulse repository root as `.env`.
3. From the BuildPulse repository root:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Expected:

- `postgres` is healthy;
- `api` is running;
- the dashboard is reachable on port 8000 unless `API_PORT` is set.

4. Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

5. Build the knowledge index after the app is healthy:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/knowledge/sync
```

The operation is idempotent and reads external sources; it does not write to GitHub, Jira, or Confluence.

## 12. Final Azure Pipeline to add after agent is online

Do not use the initial starter YAML as the deployment configuration. Replace it after `buildpulse-vm` shows Online.

The final YAML needs these stages:

1. **Validate** — checkout GitHub source, install API test dependencies, run tests, and run `docker compose config --quiet`.
2. **Deploy** — must use pool `Default` and demand the named `buildpulse-vm` agent; ensure the demo-services sibling repository exists; copy `C:\BuildPulse\config\.env` to the temporary checkout; run `docker compose up --build -d`.
3. **Verify** — wait for `/health`, check agent/retrieval status, and run `POST /api/knowledge/sync` only after valid embedding and integration settings exist.

The exact file should be created by the next agent only after verifying the VM paths, agent status, and whether GitHub credentials permit the agent to clone `buildpulse-demo-services`.

Avoid embedding secrets in the YAML. The protected VM-local `.env` file is the simplest hackathon approach. A production-grade approach would use Azure Key Vault + variable groups/managed identity.

## 13. Verification checklist after pipeline deployment

### Services

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/agents/status
Invoke-RestMethod http://127.0.0.1:8000/api/knowledge/status
```

Expected:

- application health status is `ok`;
- selected model provider is ready;
- retrieval backend is PostgreSQL;
- document count is greater than zero;
- vector search is enabled after successful embedding;
- no secrets appear in output/logs.

### RAG test

Open or call:

```text
http://127.0.0.1:8000/api/knowledge/search?q=connection%20pool%20runbook&source=repository
```

Expected retrieval methods include `pgvector` or `hybrid`.

### UI test

Open:

```text
http://127.0.0.1:8000/
```

Verify:

1. Developer and Engineering Lead switch works.
2. Service-status modal reports accurate green/red dependency states.
3. Failed Pipelines shows service-specific jobs.
4. Investigate Failure / Ask Copilot uses the selected failure context.
5. Ask “What tools and entitlements does a new Identity Service developer need?”
6. Ask “What is the current progress and future plan for Payments API?”
7. Ask “What is the architecture of API Gateway?”

Answers should be short, service-specific, and cite retrieved sources rather than dumping an entire page.

## 14. Troubleshooting

### Agent is offline

- Keep `C:\azagent\run.cmd` running in the signed-in VM session.
- Check the PAT scope and expiry.
- Check that the server URL is `https://dev.azure.com/pncapifest/`.
- Confirm the pool is `Default`.

### Docker fails from the agent

- Open Docker Desktop and wait for it to be ready.
- Run the agent under the same Windows user that launched Docker Desktop.
- Do not configure the agent as a service until interactive mode is proven.

### Managed PostgreSQL connection fails

- Check network firewall rules allow the VM.
- Verify the host, port, database name, and URL-encoded password.
- Ensure SSL configuration matches provider requirements (`sslmode=require` is common).
- Ensure pgvector/`vector` extension is available. Ask the provisioner to enable it if not.

### Vector search is false

- Confirm the database is PostgreSQL and vector extension is available.
- Confirm the embedding credential is valid.
- Confirm `EMBEDDING_DIM` matches the actual embedding model output.
- Restart the API and run knowledge sync again.

### Chat shows fallback instead of Claude

- Confirm `LLM_PROVIDER=anthropic`.
- Confirm the direct Anthropic endpoint or a fully compatible gateway endpoint.
- Confirm the selected Sonnet model is enabled for the key.
- Inspect `docker compose logs --tail 200 api` locally; do not share credentials/log lines containing secrets.
- Restart the API after editing `.env`.

### Jira/Confluence are absent from answers

- Confirm the source URL/token/space/project are correct and readable by the integration user.
- Run `POST /api/knowledge/sync` again.
- Check knowledge status for source counts and embedding failures.

## 15. Work still required

1. Finish registering `buildpulse-vm` in the `Default` Azure DevOps agent pool and confirm it is Online.
2. Verify Docker/Git/Compose on the VM.
3. Create the protected VM `.env` using the provisioned PostgreSQL connection and one valid model provider.
4. Confirm the VM can access the managed PostgreSQL instance and that pgvector is enabled.
5. Manually start the stack once and run the verification checklist.
6. Replace the Azure starter YAML with a real Validate → Deploy → Verify pipeline.
7. Commit/push that pipeline YAML to `buildpulse-azure-import/main`.
8. Run the pipeline and confirm it uses `buildpulse-vm`.
9. Run a final knowledge sync and UI smoke test.
10. Rotate short-lived PATs and any temporary hackathon keys after the event.

## 16. Key files for a successor agent

- `BUILD_PULSE_VM_HANDOFF.md` — this document.
- `HACKATHON_VM_MIGRATION.md` — lower-level migration checklist.
- `.env.example` — safe variable template, no secrets.
- `docker-compose.yml` — API/database deployment definition.
- `backend/app/services/agent_runtime.py` — chat and CI reasoning behavior.
- `backend/app/services/retrieval_store.py` — PostgreSQL/pgvector retrieval.
- `backend/app/services/unified_ingestion.py` — source synchronization.
- `backend/knowledge_seed/docs/service-handbooks/` — detailed service onboarding and operational knowledge.

When continuing this work, preserve the user’s existing changes, do not commit secrets, and validate each deployment step before moving to the next.
