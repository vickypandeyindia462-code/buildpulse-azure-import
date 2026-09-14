from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
import inspect
import asyncio

from backend.app.db.database import DATABASE_URL, SessionLocal


class Orchestrator:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL") or DATABASE_URL

    def run_sme_discovery(self, query: str) -> Dict[str, Any]:
        # create a session and call the SME agent (sync or async)
        db = SessionLocal()
        try:
            from backend.agents import sme_discovery

            # prefer async run() if provided
            agent_run = getattr(sme_discovery, "run", None)
            if inspect.iscoroutinefunction(agent_run):
                return asyncio.run(agent_run(query, {}, db))

            # fallback to run_sync helper
            agent_sync = getattr(sme_discovery, "run_sync", None)
            if callable(agent_sync):
                return agent_sync(query, {}, db)

            # last resort: call directly
            return agent_run(query, {}, db)
        finally:
            db.close()


orchestrator = Orchestrator()
