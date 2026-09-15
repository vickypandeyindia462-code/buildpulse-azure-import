"""Safe local knowledge-base retrieval for repository documentation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.I)
ALLOWED_SUFFIXES = {".md", ".txt"}
MAX_FILE_CHARS = 80_000
CHUNK_CHARS = 2_000
CHUNK_OVERLAP = 250
STOP_WORDS = {"about", "anything", "could", "does", "explain", "from", "have", "into", "should", "that", "their", "this", "what", "when", "where", "which", "with", "would"}


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOP_WORDS}


class KnowledgeBase:
    def __init__(self, repository_path: str | Path) -> None:
        self.repository_path = Path(repository_path)

    def _paths(self) -> list[Path]:
        candidates = list((self.repository_path / "docs").rglob("*"))
        candidates.extend(self.repository_path.glob("*/README.md"))
        root_readme = self.repository_path / "README.md"
        if root_readme.exists():
            candidates.append(root_readme)
        return sorted({path for path in candidates if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES})

    def _chunks(self) -> list[dict[str, Any]]:
        chunks = []
        for path in self._paths():
            content = path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
            relative = path.relative_to(self.repository_path).as_posix()
            start = 0
            index = 0
            while start < len(content):
                text = content[start:start + CHUNK_CHARS].strip()
                if text:
                    chunks.append({"title": relative, "content": text, "chunk": index})
                if start + CHUNK_CHARS >= len(content):
                    break
                start += CHUNK_CHARS - CHUNK_OVERLAP
                index += 1
        return chunks

    def search(self, query: str, service_id: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        service_tokens = _tokens((service_id or "").replace("-", " "))
        ranked = []
        for chunk in self._chunks():
            haystack = _tokens(f"{chunk['title']} {chunk['content']}")
            overlap = len(query_tokens & haystack)
            service_overlap = len(service_tokens & haystack)
            score = overlap * 10 + service_overlap * 6
            if score:
                ranked.append({**chunk, "score": score})
        ranked.sort(key=lambda item: (-item["score"], item["title"], item["chunk"]))
        selected = ranked[:limit]
        # Preserve operational diversity when onboarding/profile pages score
        # highly on the same service terms and would otherwise crowd out the
        # actionable runbook from a small result set.
        runbook = next((item for item in ranked if "runbook" in item["title"].lower()), None)
        if runbook and selected and all("runbook" not in item["title"].lower() for item in selected):
            selected[-1] = runbook
        return selected
