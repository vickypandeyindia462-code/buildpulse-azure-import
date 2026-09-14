from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import openai
from openai import OpenAI
import traceback

from backend.agents import rag
from backend.app.db.database import SessionLocal
from backend.app.db.models import Document

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
def ai_chat(payload: Dict[str, Any]):
    try:
        query = payload.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="query is required")

        use_db = payload.get("use_db", True)

        # obtain candidate documents via RAG
        docs = []
        if use_db:
            db = SessionLocal()
            try:
                rows = db.query(Document).all()
                docs = [{"id": r.id, "content": r.content} for r in rows]
                rag_res = rag.run_sync(query, {"documents": docs}, db)
            finally:
                db.close()
        else:
            rag_res = rag.run_sync(query, {"documents": payload.get("documents", [])}, None)

        hits = rag_res.get("results", [])

        # build prompt
        context_chunks = "\n\n".join([f"Source ({h.get('id')}): {h.get('content')}" for h in hits[:5]])
        prompt = f"You are a helpful assistant. Use the following sources to answer the question.\n\nSources:\n{context_chunks}\n\nQuestion: {query}\n\nAnswer concisely and cite source ids."

        # call OpenAI chat if key present
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        if not api_key:
            # fallback: return rag hits as context-only answer
            return {"answer": "", "sources": hits, "note": "No LLM API key configured"}

        try:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=payload.get("model", "gpt-3.5-turbo"),
                messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.2,
            )
            # new SDK returns objects; try several access patterns
            answer = None
            try:
                answer = resp.choices[0].message[0].content
            except Exception:
                try:
                    answer = resp.choices[0].message.content
                except Exception:
                    try:
                        answer = resp["choices"][0]["message"]["content"]
                    except Exception:
                        answer = str(resp)
            if isinstance(answer, bytes):
                answer = answer.decode('utf-8')
            answer = (answer or '').strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

        return {"answer": answer, "sources": hits, "method": "rag+chat"}
    except HTTPException as he:
        return {"error": str(he.detail)}
    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "traceback": tb}
