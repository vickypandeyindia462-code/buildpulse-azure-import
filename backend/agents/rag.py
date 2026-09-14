from typing import Dict, Any, Optional, List
import asyncio
import os

try:
    from backend.app.embeddings import get_embedding
except Exception:
    get_embedding = None

from sqlalchemy import text



async def run(query: str, context: Dict[str, Any], db=None, tools: Optional[Dict[str, Any]] = None):
    """Simple RAG: search `context['documents']` for query substring matches."""
    docs = context.get("documents", [])

    def _search(docs, q):
        matches = []
        ql = q.lower()
        for d in docs:
            content = d.get("content", "")
            if ql in content.lower():
                matches.append({"id": d.get("id"), "content": content})
        return matches

    loop = asyncio.get_event_loop()
    # if DB provided and looks like Postgres with pgvector, attempt vector search
    pg_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    if db is not None and (pg_url.startswith("postgres") or pg_url.startswith("postgresql")) and get_embedding is not None:
        try:
            qvec = get_embedding(query)
            # serialize vector parameter for pgvector compatibility
            if isinstance(qvec, (list, tuple)):
                vec_param = "[" + ",".join(str(float(x)) for x in qvec) + "]"
            else:
                vec_param = str(qvec)
            # run raw SQL nearest-neighbor using pgvector <-> operator; cast param to vector
            sql = text("SELECT id, content FROM documents ORDER BY embedding <-> CAST(:vec AS vector) LIMIT :k")
            res = db.execute(sql, {"vec": vec_param, "k": 5}).fetchall()
            results = [{"id": r[0], "content": r[1]} for r in res]
            return {"query": query, "results": results, "method": "pgvector"}
        except Exception:
            # fallback to in-memory substring search
            pass

    results = await loop.run_in_executor(None, _search, docs, query)
    return {"query": query, "results": results, "method": "substring"}


def run_sync(query: str, context: Dict[str, Any], db=None):
    import asyncio

    return asyncio.run(run(query, context, db))
