from pathlib import Path

from backend.app.services.confluence_knowledge import ConfluenceClient, markdown_to_storage, plain_text


class Response:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class Session:
    def __init__(self):
        self.created = []

    def request(self, method, url, **kwargs):
        if method == "POST":
            self.created.append(kwargs["json"])
            return Response({"id": str(100 + len(self.created)), "title": kwargs["json"]["title"]})
        if url.endswith("/spaces/262146"):
            return Response({"id": "262146", "key": "BPK", "name": "BuildPulse"})
        return Response({"results": [{"id": "10", "title": "Loan recovery", "body": {"storage": {"value": "<h1>Pool saturation</h1><p>Restore capacity safely.</p>"}}, "_links": {"webui": "/wiki/spaces/BPK/pages/10"}, "version": {"createdAt": "2026-09-15"}}]})


class SessionWithStarterPage(Session):
    def request(self, method, url, **kwargs):
        if method == "GET" and not url.endswith("/spaces/262146"):
            return Response({"results": [
                {"id": "1", "title": "Getting started in Confluence", "body": {"storage": {"value": "<p>Generic starter instructions</p>"}}},
                {"id": "10", "title": "BuildPulse — Loan recovery", "body": {"storage": {"value": "<p>Restore pool capacity safely.</p>"}}},
            ]})
        return super().request(method, url, **kwargs)


def client(session=None):
    return ConfluenceClient("https://example.atlassian.net", "262146", "BPK", "user@example.com", "token", session=session or Session())


def test_storage_conversion_and_plain_text_are_safe():
    storage = markdown_to_storage("# Heading\n\n<script>alert(1)</script>")
    assert "<h1>Heading</h1>" in storage
    assert "&lt;script&gt;" in storage
    assert plain_text(storage).startswith("Heading")


def test_confluence_status_and_search_return_openable_pages():
    assert client().status()["connected"] is True
    result = client().search("pool saturation")
    assert result[0]["source"] == "confluence"
    assert result[0]["url"].endswith("/wiki/spaces/BPK/pages/10")


def test_search_excludes_generic_atlassian_starter_pages():
    results = client(SessionWithStarterPage()).search("starter restore capacity")
    assert [result["title"] for result in results] == ["BuildPulse — Loan recovery"]


def test_repository_publish_is_idempotent_by_title(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "runbook.md").write_text("# Recovery", encoding="utf-8")
    session = Session()
    result = client(session).publish_repository(tmp_path)
    assert result["total"] == 2
    assert [payload["title"] for payload in session.created] == ["BuildPulse Knowledge Hub", "BuildPulse — docs/runbook.md"]
