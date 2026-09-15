from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Load environment variables from a local .env file (if present).
# This allows setting GITHUB_TOKEN once in a .env file during local development
# so the backend doesn't require repeatedly re-exporting the token each shell.
load_dotenv()

from .routers import sme
from .routers import orchestrator as orchestrator_router
from .routers import ingest as ingest_router
from .routers import rag_router as rag_router
from .routers import security as security_router
from .routers import ai as ai_router
from .db import seed
from .routers import pr_submit as pr_submit_router
from .routers import repository as repository_router
from .routers import agents as agents_router
from .routers import jira as jira_router
from .routers import knowledge as knowledge_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    # create tables and seed sample data (uses DATABASE_URL or sqlite dev.db)
    seed.seed()
    yield


app = FastAPI(title="BuildPulse API", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(sme.router)
app.include_router(orchestrator_router.router)
app.include_router(ingest_router.router)
app.include_router(rag_router.router)
app.include_router(security_router.router)
app.include_router(ai_router.router)
app.include_router(pr_submit_router.router)
app.include_router(repository_router.router)
app.include_router(agents_router.router)
app.include_router(jira_router.router)
app.include_router(knowledge_router.router)

# The approved BuildPulse web experience is a static HTML/CSS/JavaScript app.
# Register this after the API routers so their routes win over the catch-all
# static-file mount.
WEB_DIR = Path(__file__).resolve().parents[2] / "frontend" / "web"
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="buildpulse-web")
