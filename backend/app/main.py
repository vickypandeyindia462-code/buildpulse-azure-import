from fastapi import FastAPI
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

app = FastAPI(title="BuildPulse API")


@app.on_event("startup")
def on_startup():
    # create tables and seed sample data (uses DATABASE_URL or sqlite dev.db)
    seed.seed()


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
