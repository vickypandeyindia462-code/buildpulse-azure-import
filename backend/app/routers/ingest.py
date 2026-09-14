from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.app.db.database import SessionLocal
from backend.agents import ingestion

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
def ingest_documents(docs: List[Dict[str, Any]]):
    db = SessionLocal()
    try:
        res = ingestion.run_sync(docs, {}, db)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
