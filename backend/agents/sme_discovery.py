from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.db.models import SMEOwnership
import asyncio


async def run(query: str, context: Dict[str, Any], db: Session, tools: Optional[Dict[str, Any]] = None):
    """Async search SME ownership by system name or expertise tags."""
    # no real async DB here; run sync query in threadpool if needed
    def _query():
        return db.query(SMEOwnership).filter(
            (SMEOwnership.system_name.ilike(f"%{query}%")) |
            (SMEOwnership.expertise_tags.ilike(f"%{query}%"))
        ).all()

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _query)

    out = []
    for r in results:
        out.append({
            "system_name": r.system_name,
            "owner_name": r.owner_name,
            "owner_team": r.owner_team,
            "owner_email": r.owner_email,
            "expertise_tags": (r.expertise_tags or "").split(",")
        })

    return {"results": out}


def run_sync(query: str, context: Dict[str, Any], db: Session):
    """Backward-compatible sync helper."""
    return asyncio.run(run(query, context, db))
