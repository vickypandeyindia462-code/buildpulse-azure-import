"""Confluence Cloud publishing and bounded knowledge retrieval."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


MAX_PAGE_CHARS = 80_000
DEFAULT_PAGE_TITLES = {"overview", "getting started in confluence", "meeting notes"}


def markdown_to_storage(text: str) -> str:
    """Convert the small demo Markdown subset to safe Confluence storage HTML."""
    output: list[str] = []
    in_code = False
    for raw in text[:MAX_PAGE_CHARS].splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            output.append("<pre>" if not in_code else "</pre>")
            in_code = not in_code
        elif in_code:
            output.append(html.escape(line) + "\n")
        elif line.startswith("### "):
            output.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            output.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            output.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith(("- ", "* ")):
            output.append(f"<p>• {html.escape(line[2:])}</p>")
        elif re.match(r"^\d+\. ", line):
            output.append(f"<p>{html.escape(line)}</p>")
        elif line:
            output.append(f"<p>{html.escape(line)}</p>")
    if in_code:
        output.append("</pre>")
    return "".join(output)


def plain_text(storage: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", storage))).strip()


@dataclass
class ConfluenceClient:
    base_url: str
    space_id: str
    space_key: str
    email: str
    api_token: str
    session: Any = requests

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.space_id and self.email and self.api_token)

    def _request(self, method: str, path: str, **kwargs):
        response = self.session.request(method, f"{self.base_url}{path}", auth=(self.email, self.api_token), headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=25, **kwargs)
        response.raise_for_status()
        return response

    def pages(self) -> list[dict[str, Any]]:
        response = self._request("GET", f"/wiki/api/v2/spaces/{self.space_id}/pages", params={"limit": 100, "body-format": "storage", "status": "current"}).json()
        return [self._page(item) for item in response.get("results", [])]

    def _page(self, item: dict[str, Any]) -> dict[str, Any]:
        storage = ((item.get("body") or {}).get("storage") or {}).get("value", "")
        webui = (item.get("_links") or {}).get("webui") or f"/wiki/pages/viewpage.action?pageId={item['id']}"
        webui = webui if webui.startswith("/wiki") else f"/wiki{webui}"
        return {"id": str(item["id"]), "title": item.get("title", "Untitled"), "content": plain_text(storage), "url": f"{self.base_url}{webui}", "source": "confluence", "updated_at": (item.get("version") or {}).get("createdAt")}

    def status(self) -> dict[str, Any]:
        space = self._request("GET", f"/wiki/api/v2/spaces/{self.space_id}").json()
        return {"ready": self.ready, "connected": True, "space_id": str(space.get("id")), "space_key": space.get("key"), "space_name": space.get("name"), "source": "confluence"}

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        terms = set(re.findall(r"[a-z0-9_-]{3,}", query.lower()))
        ranked = []
        for page in self.pages():
            if page["title"].strip().lower() in DEFAULT_PAGE_TITLES:
                continue
            corpus = set(re.findall(r"[a-z0-9_-]{3,}", f"{page['title']} {page['content']}".lower()))
            overlap = len(terms & corpus)
            if not query.strip() or overlap:
                ranked.append({**page, "score": min(100, 35 + overlap * 10), "snippet": page["content"][:260]})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]

    def publish_repository(self, repository_path: Path) -> dict[str, Any]:
        existing = {page["title"]: page for page in self.pages()}
        root_title = "BuildPulse Knowledge Hub"
        root = existing.get(root_title)
        created: list[dict[str, str]] = []
        skipped: list[str] = []
        if not root:
            root = self._create_page(root_title, "<h1>BuildPulse Knowledge Hub</h1><p>Architecture, runbooks, postmortems, service guides, and operational knowledge for the synthetic BuildPulse demonstration.</p>")
            created.append({"title": root_title, "id": root["id"]})
        paths = sorted((repository_path / "docs").rglob("*.md")) + sorted(repository_path.glob("*/README.md"))
        for path in paths:
            relative = path.relative_to(repository_path).as_posix()
            title = f"BuildPulse — {relative}"
            if title in existing:
                skipped.append(title)
                continue
            body = f"<p><strong>Source repository path:</strong> {html.escape(relative)}</p>" + markdown_to_storage(path.read_text(encoding="utf-8"))
            page = self._create_page(title, body, parent_id=root["id"])
            created.append({"title": title, "id": page["id"]})
        return {"created": created, "skipped": skipped, "total": len(created) + len(skipped), "source": "confluence"}

    def _create_page(self, title: str, storage: str, parent_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"spaceId": self.space_id, "status": "current", "title": title, "body": {"representation": "storage", "value": storage}}
        if parent_id:
            payload["parentId"] = parent_id
        return self._request("POST", "/wiki/api/v2/pages", json=payload).json()
