"""Persistent hybrid retrieval backed by PostgreSQL/pgvector or SQLite."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlencode

from sqlalchemy import text

from .. import embeddings
from ..db.database import SessionLocal
from ..db.models import Document
from .knowledge_base import KnowledgeBase, _tokens


class RetrievalStore:
    def __init__(self, knowledge: KnowledgeBase, session_factory: Any = SessionLocal) -> None:
        self.knowledge = knowledge
        self.session_factory = session_factory

    @staticmethod
    def _document_id(title: str, chunk: int) -> str:
        return "repo-" + hashlib.sha256(f"{title}:{chunk}".encode()).hexdigest()[:32]

    def index_repository(self) -> dict[str, Any]:
        chunks = self.knowledge.chunks()
        db = self.session_factory()
        indexed = 0
        embedding_failures = 0
        embedding_available = embeddings.configured_provider() != "mock"
        try:
            dialect = db.get_bind().dialect.name
            for chunk in chunks:
                doc_id = self._document_id(chunk["title"], chunk["chunk"])
                source = f"repository:{chunk['title']}#chunk={chunk['chunk']}"
                existing = db.get(Document, doc_id)
                if (
                    existing
                    and existing.content == chunk["content"]
                    and existing.source == source
                    and (existing.embedding is not None or not embedding_available)
                ):
                    continue
                stored_vector: Any = None
                if dialect == "postgresql" and embedding_available:
                    try:
                        stored_vector = embeddings.get_embedding(chunk["content"])
                    except Exception:
                        embedding_failures += 1
                        embedding_available = False
                elif dialect == "sqlite":
                    # SQLite uses keyword retrieval, so never incur a remote
                    # embedding call merely to maintain the local index.
                    stored_vector = json.dumps(embeddings._mock_embedding(chunk["content"]))
                if existing:
                    existing.content, existing.source, existing.embedding = chunk["content"], source, stored_vector
                else:
                    db.add(Document(id=doc_id, content=chunk["content"], source=source, embedding=stored_vector))
                indexed += 1
            db.commit()
            return {
                "documents": len(chunks),
                "updated": indexed,
                "backend": dialect,
                "embedding_provider": embeddings.configured_provider(),
                "embedding_failures": embedding_failures,
                "vector_search": dialect == "postgresql" and embedding_available and embedding_failures == 0,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def index_source_documents(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Idempotently index normalized documents from approved external sources."""
        db = self.session_factory()
        updated = 0
        failures = 0
        rejected: list[dict[str, str]] = []
        embedding_available = embeddings.configured_provider() != "mock"
        try:
            dialect = db.get_bind().dialect.name
            for item in documents:
                kind = str(item["source"]).replace("\x00", "")
                external_id = str(item["external_id"]).replace("\x00", "")
                metadata = urlencode({
                    "title": str(item.get("title") or external_id).replace("\x00", " "),
                    "service_id": str(item.get("service_id") or ""),
                    "url": str(item.get("url") or ""),
                    "updated_at": str(item.get("updated_at") or ""),
                    "document_type": str(item.get("document_type") or "knowledge"),
                })
                source = f"{kind}:{external_id}?{metadata}"
                content = str(item.get("content") or "").replace("\x00", " ")[:12000].strip()
                if not content:
                    continue
                doc_id = "source-" + hashlib.sha256(f"{kind}:{external_id}".encode()).hexdigest()[:32]
                existing = db.get(Document, doc_id)
                if existing and existing.content == content and existing.source == source and (existing.embedding is not None or not embedding_available):
                    continue
                vector: Any = None
                if dialect == "postgresql" and embedding_available:
                    try:
                        vector = embeddings.get_embedding(content)
                    except Exception:
                        failures += 1
                        embedding_available = False
                elif dialect == "sqlite":
                    vector = json.dumps(embeddings._mock_embedding(content))
                if existing:
                    existing.content, existing.source, existing.embedding = content, source, vector
                else:
                    db.add(Document(id=doc_id, content=content, source=source, embedding=vector))
                try:
                    db.commit()
                    updated += 1
                except Exception as exc:
                    db.rollback()
                    rejected.append({"document": f"{kind}:{external_id}", "error": f"{type(exc).__name__}: {str(exc)[:240]}"})
            db.commit()
            return {"documents": len(documents), "updated": updated, "embedding_failures": failures, "rejected": rejected}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _item(row: Any, score: float, method: str) -> dict[str, Any]:
        source = row.source or "indexed"
        match = re.match(r"repository:(.+)#chunk=(\d+)$", source)
        if match:
            return {"title": match.group(1), "content": row.content, "chunk": int(match.group(2)), "score": round(score, 3), "source": "repository", "url": None, "updated_at": None, "document_type": "repository_document", "service_id": None, "retrieval_method": method}
        prefix, _, query_string = source.partition("?")
        kind, _, external_id = prefix.partition(":")
        metadata = {key: values[0] for key, values in parse_qs(query_string).items()}
        return {
            "title": metadata.get("title", external_id or source), "content": row.content, "chunk": None,
            "score": round(score, 3), "source": kind, "url": metadata.get("url") or None,
            "updated_at": metadata.get("updated_at") or None, "document_type": metadata.get("document_type", "knowledge"),
            "service_id": metadata.get("service_id") or None, "retrieval_method": method,
        }

    def search(self, query: str, service_id: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        db = self.session_factory()
        try:
            dialect = db.get_bind().dialect.name
            semantic: list[dict[str, Any]] = []
            if dialect == "postgresql" and embeddings.configured_provider() != "mock":
                try:
                    vector = embeddings.get_embedding(query)
                    vector_text = "[" + ",".join(str(float(value)) for value in vector) + "]"
                    rows = db.execute(text(
                        "SELECT id, content, source, 1 - (embedding <=> CAST(:vector AS vector)) AS similarity "
                        "FROM documents WHERE embedding IS NOT NULL AND (source LIKE 'repository:%' OR source LIKE 'confluence:%' OR source LIKE 'jira:%' OR source LIKE 'github-ci:%') "
                        "ORDER BY embedding <=> CAST(:vector AS vector) LIMIT :limit"
                    ), {"vector": vector_text, "limit": limit * 3}).fetchall()
                    for row in rows:
                        holder = type("IndexedRow", (), {"content": row[1], "source": row[2]})
                        semantic.append(self._item(holder, max(0.0, float(row[3] or 0)) * 100, "pgvector"))
                except Exception:
                    db.rollback()

            query_tokens = _tokens(query) | _tokens((service_id or "").replace("-", " "))
            lexical: list[dict[str, Any]] = []
            approved = db.query(Document).filter(
                Document.source.like("repository:%") | Document.source.like("confluence:%") |
                Document.source.like("jira:%") | Document.source.like("github-ci:%")
            ).all()
            for row in approved:
                if service_id and f"service_id={service_id}" not in (row.source or "") and not (row.source or "").startswith("repository:"):
                    continue
                overlap = len(query_tokens & _tokens(f"{row.source} {row.content}"))
                if overlap:
                    lexical.append(self._item(row, overlap * 10, "keyword"))
            lexical.sort(key=lambda item: -item["score"])

            combined: dict[tuple[str, int | None], dict[str, Any]] = {}
            for item in [*semantic, *lexical]:
                key = (item["title"], item["chunk"])
                current = combined.get(key)
                if current:
                    current["score"] = round(current["score"] + item["score"] * 0.35, 3)
                    current["retrieval_method"] = "hybrid"
                else:
                    combined[key] = item
            return sorted(combined.values(), key=lambda item: -item["score"])[:limit]
        finally:
            db.close()

    def status(self) -> dict[str, Any]:
        db = self.session_factory()
        try:
            dialect = db.get_bind().dialect.name
            count = db.query(Document).filter(
                Document.source.like("repository:%") | Document.source.like("confluence:%") |
                Document.source.like("jira:%") | Document.source.like("github-ci:%")
            ).count()
            vector_count = int(db.execute(text(
                "SELECT count(*) FROM documents WHERE embedding IS NOT NULL AND (source LIKE 'repository:%' OR source LIKE 'confluence:%' OR source LIKE 'jira:%' OR source LIKE 'github-ci:%')"
            )).scalar_one())
            source_counts = {
                row[0]: int(row[1]) for row in db.execute(text(
                    "SELECT split_part(source, ':', 1), count(*) FROM documents "
                    "WHERE source IS NOT NULL GROUP BY split_part(source, ':', 1)"
                )).fetchall()
            } if dialect == "postgresql" else {
                kind: sum(1 for row in db.query(Document).all() if (row.source or "").startswith(f"{kind}:"))
                for kind in ("repository", "confluence", "jira", "github-ci")
            }
            return {
                "backend": dialect,
                "vector_search": dialect == "postgresql" and vector_count > 0,
                "embedding_provider": embeddings.configured_provider(),
                "indexed_documents": count,
                "vector_documents": vector_count,
                "source_counts": source_counts,
            }
        finally:
            db.close()
