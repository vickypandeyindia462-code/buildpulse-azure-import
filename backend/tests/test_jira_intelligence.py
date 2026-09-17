from backend.app.services.jira_intelligence import JiraClient


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
        if url.endswith("/myself"):
            return Response({"active": True})
        if "/project/" in url:
            return Response({"key": "SUP", "projectTypeKey": "service_desk"})
        if url.endswith("/transitions") and method == "GET":
            return Response({"transitions": [{"id": "111", "name": "Resolve", "to": {"statusCategory": {"key": "done"}}}]})
        if "/comment" in url or "/transitions" in url:
            return Response({})
        if "/issue/" in url and method == "GET":
            return Response({"fields": {"comment": {"comments": []}}, "changelog": {"histories": []}})
        if method == "GET":
            return Response({"issues": [{"key": "SUP-1", "fields": {"summary": "[BuildPulse Demo] Loan incident", "status": {"name": "Open", "statusCategory": {"key": "new"}}, "priority": {"name": "Highest"}, "issuetype": {"name": "Incident"}, "labels": ["buildpulse-demo", "loan-service", "scenario-bp-loan-pool"], "created": "2026-09-15", "updated": "2026-09-15"}}]})
        self.created.append(kwargs["json"])
        return Response({"key": f"SUP-{len(self.created) + 1}"})


def test_jira_status_and_dashboard_mapping():
    client = JiraClient("https://example.atlassian.net", "SUP", "user@example.com", "token", session=Session())
    assert client.status()["connected"] is True
    dashboard = client.dashboard()
    assert dashboard["source"] == "jira"
    assert dashboard["open_incidents"] == 1
    assert dashboard["release_readiness"] == 92
    assert dashboard["attention"][0]["service_id"] == "loan-service"


def test_ticket_seeding_is_idempotent_by_scenario_label():
    session = Session()
    result = JiraClient("https://example.atlassian.net", "SUP", "user@example.com", "token", session=session).seed_demo_tickets()
    assert "BP-LOAN-POOL" in result["skipped"]
    assert result["total"] == 8
    assert len(session.created) == 7
    assert all("synthetic-data" in request["fields"]["labels"] for request in session.created)


def test_historical_seeding_resolves_four_labelled_incidents():
    session = Session()
    result = JiraClient("https://example.atlassian.net", "SUP", "user@example.com", "token", session=session).seed_historical_incidents()
    assert result["total"] == 4
    issue_creates = [request for request in session.created if "fields" in request]
    assert len(issue_creates) == 4
    assert all("historical-incident" in request["fields"]["labels"] for request in issue_creates)
