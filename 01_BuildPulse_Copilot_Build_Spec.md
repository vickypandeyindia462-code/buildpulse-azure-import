# BuildPulse AI — Build Specification (for VS Code Copilot / implementation reference)

> **Purpose of this document:** This is the working spec to paste into Copilot Chat / keep open in VS Code while building. It defines stack, structure, schema, agent contracts, API routes, and a phased build order so Copilot generates code consistent with one architecture instead of improvising each time.

---

## 1. Project Summary

**BuildPulse AI** is a security-first enterprise engineering copilot. It turns fragmented engineering knowledge (incidents, releases, ownership, docs) into actionable answers through one conversational interface, backed by 5 specialist agents and a Postgres knowledge/data layer.

**Core promise:** ask one question ("why did the loan service fail last night?") and get RCA + similar past incidents + the right SME + a risk assessment + a recommended fix — synthesized, not five separate lookups.

---

## 2. Final Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Streamlit (multi-page) | Single web app, no separate Node/React needed |
| Backend API | FastAPI | Async, OpenAPI docs for free, easy to containerize |
| Orchestration / RAG | LlamaIndex | Query engines per knowledge domain + agent/tool framework |
| LLM provider | Azure AI Foundry | Use free-tier/available models (e.g. gpt-4o-mini class, Phi-3 class) via `azure-ai-inference` / `azure-ai-projects` SDK |
| Database | PostgreSQL + `pgvector` extension | One database for structured data AND embeddings — avoids running a second vector DB service |
| PII detection | Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`) | Free, OSS, designed for exactly this |
| Secret scanning | Custom regex/entropy scanner (pattern used by `detect-secrets`) | No external service dependency, keeps hackathon self-contained |
| Auth (optional, if time allows) | Simple API-key or mock SSO header | Don't build real SSO in a hackathon — mock it |
| Containerization | Docker + docker-compose | 3 services: `postgres`, `api`, `frontend` |
| Sample data | `Faker` + hand-authored seed JSON | Generates incidents, releases, ownership, KB articles |
| Dev tooling | VS Code + GitHub Copilot | This doc is the shared context for Copilot |

**Why not Node.js:** nothing in this system needs a JS runtime — Streamlit renders the UI server-side in Python. Adding Node only adds a second dependency chain to manage on a personal laptop with limited time. Skip it unless you specifically want a custom JS widget.

**Why Postgres+pgvector over a dedicated vector DB (Chroma/Pinecone/Weaviate):** you already need Postgres for incidents/releases/ownership/audit logs. `pgvector` lets embeddings live in the same DB and the same docker-compose service — one less moving part, one less thing that can fail during a live demo.

---

## 3. Repository Structure

```
buildpulse-ai/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── config.py                # env/settings via pydantic-settings
│   │   ├── db/
│   │   │   ├── database.py          # SQLAlchemy engine/session
│   │   │   ├── models.py            # ORM models
│   │   │   └── seed.py              # sample data generator (Faker)
│   │   ├── agents/
│   │   │   ├── orchestrator.py      # router / synthesis agent
│   │   │   ├── knowledge_discovery.py
│   │   │   ├── incident_intelligence.py
│   │   │   ├── sme_discovery.py
│   │   │   ├── risk_radar.py
│   │   │   └── security_trust.py
│   │   ├── rag/
│   │   │   ├── embeddings.py        # Azure AI Foundry embedding calls
│   │   │   ├── vector_store.py      # pgvector-backed LlamaIndex store
│   │   │   └── ingest.py            # loads sample docs into vector store
│   │   ├── security/
│   │   │   ├── pii_detector.py      # Presidio wrapper
│   │   │   ├── secret_scanner.py    # regex/entropy scanner
│   │   │   └── audit_logger.py      # writes to audit_log table
│   │   ├── routers/
│   │   │   ├── chat.py
│   │   │   ├── knowledge.py
│   │   │   ├── incidents.py
│   │   │   ├── sme.py
│   │   │   ├── risk.py
│   │   │   ├── security.py
│   │   │   └── dashboard.py
│   │   └── schemas.py               # pydantic request/response models
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                       # Streamlit entrypoint
│   └── pages/
│       ├── 1_🏠_Executive_Dashboard.py
│       ├── 2_💬_AI_Copilot_Chat.py
│       ├── 3_📚_Knowledge_Discovery.py
│       ├── 4_🚨_Incident_Intelligence.py
│       ├── 5_👥_SME_Directory.py
│       ├── 6_⚠️_Risk_Radar.py
│       └── 7_🔐_Security_Trust_Center.py
└── data/
    └── sample/                      # seed JSON/CSV for demo data
```

---

## 4. Environment & Docker Setup

`.env.example`:
```
# Azure AI Foundry
AZURE_AI_ENDPOINT=
AZURE_AI_API_KEY=
AZURE_AI_CHAT_MODEL=          # e.g. gpt-4o-mini deployment name
AZURE_AI_EMBEDDING_MODEL=     # e.g. text-embedding-3-small deployment name

# Postgres
POSTGRES_USER=buildpulse
POSTGRES_PASSWORD=changeme
POSTGRES_DB=buildpulse
DATABASE_URL=postgresql://buildpulse:changeme@postgres:5432/buildpulse

# App
ENV=development
LOG_LEVEL=INFO
```

`docker-compose.yml` (structure Copilot should generate):
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16   # ships pgvector pre-installed
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  api:
    build: ./backend
    env_file: .env
    depends_on: [postgres]
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    env_file: .env
    depends_on: [api]
    ports: ["8501:8501"]

volumes:
  pgdata:
```

> On a personal laptop with Docker Desktop + admin rights this is a one-command `docker compose up --build` demo environment. No internal bank network needed since everything (models via Azure AI Foundry, data via seeded Postgres) is self-contained.

---

## 5. Database Schema (PostgreSQL)

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base articles / docs (for RAG)
CREATE TABLE kb_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    system_name TEXT,            -- e.g. "Loan Service"
    tags TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Incidents
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    system_name TEXT,
    severity TEXT CHECK (severity IN ('P1','P2','P3','P4')),
    root_cause TEXT,
    resolution TEXT,
    status TEXT CHECK (status IN ('open','investigating','resolved','closed')),
    occurred_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    embedding VECTOR(1536)       -- for "find similar incidents"
);

-- SME / ownership registry
CREATE TABLE sme_ownership (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name TEXT NOT NULL,   -- e.g. "Kafka Platform"
    owner_name TEXT NOT NULL,
    owner_team TEXT,
    owner_email TEXT,
    expertise_tags TEXT[],
    related_doc_id UUID REFERENCES kb_articles(id)
);

-- Releases
CREATE TABLE releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    release_name TEXT,           -- e.g. "24.3"
    system_name TEXT,
    scheduled_at TIMESTAMPTZ,
    risk_score NUMERIC(5,2),
    risk_level TEXT CHECK (risk_level IN ('low','medium','high','critical')),
    risk_drivers JSONB,          -- e.g. [{"factor": "open P1 incidents", "weight": 0.4}]
    status TEXT
);

-- Security scan findings
CREATE TABLE security_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_type TEXT CHECK (finding_type IN ('pii','secret')),
    source TEXT,                 -- file/query/document reference
    detail TEXT,
    severity TEXT,
    detected_at TIMESTAMPTZ DEFAULT now(),
    resolved BOOLEAN DEFAULT false
);

-- Audit log (every agent action, security-relevant)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    action TEXT,                 -- e.g. "chat_query", "pii_redacted"
    agent_name TEXT,
    query_text TEXT,
    response_summary TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. Agent Architecture & Orchestration Pattern

**Pattern: Router/Orchestrator + specialist tool-agents (tool-calling), not a rigid pipeline.**

```
User query → Orchestrator Agent
                 │
                 ├─ classifies intent (which agent(s) apply)
                 ├─ calls relevant agent(s) as tools (can call more than one)
                 ├─ each agent returns structured JSON, not free text
                 └─ orchestrator synthesizes one coherent answer + cites sources
```

Implement the Orchestrator using Azure AI Foundry's function/tool-calling: register each of the 5 agents as a callable "tool" with a JSON schema. The model decides which tools to call based on the user's question, exactly like the "why did loan service fail" example needing Incident Intelligence + SME Discovery + Risk Radar together.

### 6.1 Agent Contracts

Each agent is a Python class with one public method: `run(query: str, context: dict) -> AgentResult`, where `AgentResult` is a pydantic model with `summary`, `data`, `sources`, `confidence`.

#### A. Knowledge Discovery Agent
- **Purpose:** search enterprise knowledge (KB articles, system docs)
- **Example query:** "how does the loan service work?"
- **Returns:** summary, related systems, dependencies, recommended docs
- **Implementation:** LlamaIndex query engine over `kb_articles.embedding` (pgvector)

#### B. Incident Intelligence Agent
- **Purpose:** root cause analysis, similar past incidents
- **Example query:** "why did load service fail?"
- **Returns:** likely root cause, matched historical incidents (vector similarity on `incidents.embedding`), resolution steps that worked before
- **Implementation:** hybrid — structured filter (system_name, severity) + vector similarity + LLM summarization

#### C. SME Discovery Agent
- **Purpose:** find who owns/knows a system
- **Example query:** "who owns the Kafka platform?"
- **Returns:** owner name, team, contact, related documentation
- **Implementation:** structured lookup on `sme_ownership`, optionally LLM to phrase the answer naturally

#### D. Risk Radar (Delivery Risk) Agent
- **Purpose:** release/delivery risk scoring
- **Example query:** "can release 24.3 go live tomorrow?"
- **Returns:** risk score (0–100), risk level, risk drivers (e.g. open P1s on that system, recent incident frequency, SME availability), recommendation
- **Implementation:** rules-based scoring function (deterministic, explainable — important for a bank demo) + LLM to narrate the drivers. Keep the scoring formula transparent, not a black-box LLM guess.

#### E. Security & Trust Center Agent
- **Purpose:** PII detection, secret scanning, audit logging (this one wraps utility functions rather than an LLM call)
- **Sub-capabilities:**
  - `detect_pii(text) -> list[Finding]` using Presidio
  - `scan_secrets(text) -> list[Finding]` using regex/entropy patterns (AWS keys, API tokens, connection strings, etc.)
  - `log_audit_event(...)` writes to `audit_log` on every orchestrator call
- **Runs on every request** as a pre/post-processing step, not just on-demand — redact PII before sending anything to the LLM, and scan any user-pasted text before it's stored.

---

## 7. API Endpoints (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Main conversational endpoint → orchestrator |
| POST | `/knowledge/search` | Direct knowledge discovery query |
| POST | `/incidents/rca` | Direct RCA query |
| GET | `/incidents/similar/{incident_id}` | Similar incidents |
| GET | `/sme/{system_name}` | SME lookup |
| POST | `/risk/assess` | Release risk assessment |
| GET | `/risk/release/{release_name}` | Existing risk score |
| POST | `/security/scan-pii` | PII scan on arbitrary text |
| POST | `/security/scan-secrets` | Secret scan on arbitrary text |
| GET | `/dashboard/executive` | Aggregated metrics for exec dashboard |
| GET | `/audit/logs` | Audit trail (admin view) |
| GET | `/health` | Container health check |

All routes return typed pydantic response models — Copilot should generate `schemas.py` first so every router shares consistent types.

---

## 8. Frontend Pages (Streamlit)

1. **Executive Dashboard** — build health, open incidents, release risk, knowledge reuse stats, security metrics (use `st.metric` + `st.plotly_chart` / native `st.bar_chart`)
2. **AI Copilot Chat** — single conversational interface (`st.chat_message`, `st.chat_input`), calls `/chat`, renders synthesized answer with expandable sections for RCA / similar incidents / SME / risk (source cards, not just a wall of text)
3. **Knowledge Discovery** — search box + result cards (summary, related systems, dependencies)
4. **Incident Intelligence** — incident list/filter + RCA detail view
5. **SME Directory** — searchable ownership table
6. **Risk Radar** — release list with risk scores/drivers, filterable
7. **Security & Trust Center** — PII/secret finding feed + audit log viewer

Use `st.set_page_config(layout="wide")` and a shared `frontend/utils/api_client.py` for all `/backend` calls so pages don't duplicate `requests` boilerplate.

---

## 9. Sample Data Generation Plan

Build `backend/app/db/seed.py`:
- ~15–20 `kb_articles` covering systems like "Loan Service", "Kafka Platform", "Payments Gateway", "Auth Service"
- ~40–60 `incidents` spread across systems/severities, some deliberately similar (for RCA similarity matching to have something to find)
- ~10 `sme_ownership` records, one owner per major system
- ~10 `releases`, mix of risk levels, some with intentionally high risk drivers (open P1s, low SME availability) for a good demo story
- A handful of `security_findings` pre-seeded so the Security Center isn't empty on first load
- Generate embeddings for `kb_articles` and `incidents` at seed time via the Azure AI Foundry embedding model — don't compute these live during the demo (avoid API latency mid-demo)

Run once via `docker compose exec api python -m app.db.seed`.

---

## 10. Security & Compliance Features (bank context — take these seriously even in a hackathon)

- **PII detection (Presidio):** run on (a) any free-text the user pastes into chat, (b) any document ingested into the KB before embedding/storing. Redact or mask before it touches the LLM.
- **Secret scanning:** run on ingested documents/config-like text; flag AWS/Azure keys, connection strings, tokens via regex + Shannon-entropy check on suspicious strings.
- **Audit logging:** every `/chat` call and every agent invocation writes one row to `audit_log` — who asked what, which agent(s) responded, when. This is the single most "bank-credible" feature — make sure the demo shows it.
- **No real customer data ever** — sample data only, clearly labeled synthetic in the README and on-screen.

---

## 11. Suggested Build Order (phased for hackathon time pressure)

1. **Foundation (do first):** docker-compose skeleton, Postgres + pgvector up, FastAPI `/health`, Streamlit "hello world" page — prove the 3 containers talk to each other before building any agent logic.
2. **Data layer:** schema migrations + seed script with sample data.
3. **Knowledge Discovery Agent** end-to-end (simplest, proves RAG + Azure AI Foundry connectivity works).
4. **SME Discovery Agent** (simplest — mostly structured lookup, fast win).
5. **Incident Intelligence Agent** (RCA + similarity search).
6. **Risk Radar Agent** (deterministic scoring + narration).
7. **Security & Trust Center** (Presidio + secret scanner + audit logging wired into every request).
8. **Orchestrator** tying all 5 agents together behind `/chat`.
9. **Streamlit pages**, starting with AI Copilot Chat and Executive Dashboard (the two judges will look at first), then the rest.
10. **Polish pass:** seed a strong demo narrative (e.g. "release 24.3" query that lights up all 5 agents), error handling, loading states.

---

## 12. Conventions for Copilot to Follow

- Python 3.11+, type hints everywhere, pydantic v2 models for all request/response shapes.
- All agent classes implement the same `run()` interface (section 6.1) so the orchestrator can treat them uniformly.
- No hardcoded secrets — everything from `.env` via `pydantic-settings`.
- All DB access through SQLAlchemy sessions, no raw psycopg calls scattered around.
- Every FastAPI router file mirrors a Streamlit page — keep 1:1 mapping for clarity during a hackathon demo.
- Keep LLM prompts in a dedicated `prompts.py` per agent, not inline strings, so they're easy to tune under time pressure.
