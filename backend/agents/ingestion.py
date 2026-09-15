from typing import Dict, Any, Optional, List
import asyncio
import uuid
import os
import json

try:
    # import embedding provider if available
    from backend.app.embeddings import get_embedding
except Exception:
    get_embedding = None


async def run(docs: List[Dict[str, Any]], context: Dict[str, Any], db=None, tools: Optional[Dict[str, Any]] = None):
    """Ingest documents: assign IDs and return summary."""
    def _process(docs):
        out = []
        for d in docs:
            doc_id = str(uuid.uuid4())
            out.append({"id": doc_id, "content": d.get("content", ""), "source": d.get("source")})
        return out

    loop = asyncio.get_event_loop()
    processed = await loop.run_in_executor(None, _process, docs)

    # persist to DB if session provided
    if db is not None:
        try:
            from backend.app.db.models import Document
            for d in processed:
                # compute embedding if provider present and DB supports vector
                emb = None
                if get_embedding is not None:
                    try:
                        emb = get_embedding(d["content"])
                    except Exception:
                        emb = None

                # if embedding is a list, and DB expects text fallback, stringify
                store_emb = emb if isinstance(emb, (list, tuple)) else None
                if store_emb is not None and db.get_bind().dialect.name == "sqlite":
                    store_emb = json.dumps(store_emb)

                doc = Document(id=d["id"], content=d["content"], source=d.get("source"))
                # attach embedding if model has attribute
                if hasattr(Document, "embedding") and store_emb is not None:
                    # SQLite receives serialized JSON; pgvector receives the list.
                    doc.embedding = store_emb

                db.add(doc)
            db.commit()
        except Exception:
            db.rollback()
            raise

    return {"processed_count": len(processed), "documents": processed}


def run_sync(docs: List[Dict[str, Any]], context: Dict[str, Any], db=None):
    import asyncio

    return asyncio.run(run(docs, context, db))
