from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from backend.agents import rag
from backend.app.db.database import SessionLocal
from backend.app.db.models import Document

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def rag_query(payload: Dict[str, Any]):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    use_db = payload.get("use_db", True)
    docs = payload.get("documents")

    if use_db:
        db = SessionLocal()
        try:
            rows = db.query(Document).all()
            docs = [{"id": r.id, "content": r.content} for r in rows]
            # pass DB session to rag so it can perform pgvector search
            res = rag.run_sync(query, {"documents": docs or []}, db)
            return res
        finally:
            db.close()

    res = rag.run_sync(query, {"documents": docs or []}, None)
    return res
