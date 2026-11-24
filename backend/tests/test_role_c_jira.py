"""Jira: mock client, sync_ticket, the Cloud client's requests, the refresh endpoint and the status screen."""
import httpx
import pytest

from app import agent_bridge
from integrations import jira
from .helpers import agents_result, login, make_user
from .role_c_support import REQUESTER, jira_rows, wired  # noqa: F401  (wired = the fixture)


def new_ticket(api, **over):
    body = {"subject": "VPN drops", "description": "Connection drops every ten minutes", "email": REQUESTER,
            "department": "IT", **over}
    r = api.post("/tickets", json=body)
    assert r.status_code == 201, r.text
    return r.json()


# ------------------------------------------------------------------ mock client
def test_mock_client_create_update_transition_comment():
    c = jira.MockJiraClient("SUP")
    issue = c.create_issue("[T-1] VPN", "details", labels=["supportpilot"])
    assert issue["key"] == "SUP-1" and issue["url"].endswith("/browse/SUP-1")
    assert c.get_issue("SUP-1")["status"] == "To Do"
    c.update_issue("SUP-1", summary="[T-1] VPN (updated)")
    c.transition_issue("SUP-1", "In Progress")
    c.add_comment("SUP-1", "hello")
    got = c.get_issue("SUP-1")
    assert got["summary"] == "[T-1] VPN (updated)" and got["status"] == "In Progress"
    assert c.issues["SUP-1"]["comments"] == ["hello"]


def test_mock_client_rejects_unknown_issue_and_status():
    c = jira.MockJiraClient("SUP")
    with pytest.raises(jira.JiraError):
        c.get_issue("SUP-404")
    c.create_issue("x", "y")
    with pytest.raises(jira.JiraError):
        c.transition_issue("SUP-1", "Shipped")


# ------------------------------------------------------------------ sync_ticket
def test_escalation_creates_a_jira_issue(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.2, needs_review=True))
    t = new_ticket(api)  # VPN / High / P2 -> escalated by the AI
    assert t["status"] == "Escalated"
    rows = jira_rows(wired.session_factory)
    assert rows == [(t["ticket_id"], "SUP-1", "In Progress")]
    issue = wired.jira.issues["SUP-1"]
    assert issue["summary"].startswith(f"[{t['ticket_code']}]")
    assert "Network Team" in issue["description"]  # the escalation details reach Jira
    assert "Escalation reason" in issue["description"]
    assert any("now 'Escalated'" in c or "In Progress" in c for c in issue["comments"])


def test_new_ticket_is_synced_as_to_do_and_updated_later(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    t = new_ticket(api)  # AI answer sent -> 'Awaiting User' -> Jira 'To Do'
    assert t["status"] == "Awaiting User"
    assert jira_rows(wired.session_factory) == [(t["ticket_id"], "SUP-1", "To Do")]
    # the user confirms the fix -> Closed -> Jira 'Done'
    r = api.post(f"/tickets/{t['ticket_id']}/feedback", json={"is_resolved": True, "rating": 5})
    assert r.status_code == 201, r.text
    assert jira_rows(wired.session_factory) == [(t["ticket_id"], "SUP-1", "Done")]
    assert wired.jira.issues["SUP-1"]["status"] == "Done"


def test_sync_ticket_without_a_ticket_returns_none(wired):
    with wired.session_factory() as db:
        assert jira.sync_ticket(db, 999) is None


def test_sync_records_errors_and_reraises(wired, session_factory):
    from .role_c_support import make_ticket
    ticket_id = make_ticket(session_factory, "T-2026-0900")  # no Jira issue yet, so sync must create one
    class Broken(jira.MockJiraClient):
        def create_issue(self, *a, **k):
            raise jira.JiraError("boom")
    with session_factory() as db:
        with pytest.raises(jira.JiraError, match="boom"):
            jira.sync_ticket(db, ticket_id, client=Broken())
    assert jira.health()["last_error"] == "boom" and jira.health()["last_error_at"] is not None
    assert jira_rows(session_factory) == []  # nothing half-written


# ------------------------------------------------------------------ Jira Cloud client (HTTP mocked)
def test_cloud_client_sends_the_right_requests():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.content.decode() if request.content else ""))
        if request.method == "POST" and request.url.path == "/rest/api/3/issue":
            return httpx.Response(201, json={"key": "ACME-7"})
        if request.method == "GET" and request.url.path == "/rest/api/3/issue/ACME-7/transitions":
            return httpx.Response(200, json={"transitions": [
                {"id": "31", "to": {"name": "Done"}}, {"id": "21", "to": {"name": "In Progress"}}]})
        if request.method == "POST" and request.url.path == "/rest/api/3/issue/ACME-7/transitions":
            return httpx.Response(204)
        return httpx.Response(400, text="bad request")

    client = jira.CloudJiraClient("https://acme.atlassian.net", "bot@acme.com", "token", "ACME", "Task")
    client._http = httpx.Client(base_url="https://acme.atlassian.net/rest/api/3", transport=httpx.MockTransport(handler))
    issue = client.create_issue("[T-1] VPN", "line one\n\nline two", labels=["supportpilot"])
    assert issue == {"key": "ACME-7", "url": "https://acme.atlassian.net/browse/ACME-7"}
    assert '"key":"ACME"' in seen[0][2] and "line two" in seen[0][2]  # Atlassian document format body
    client.transition_issue("ACME-7", "in progress")  # case-insensitive match
    assert ('"id":"21"' in seen[-1][2]) and seen[-1][1].endswith("/transitions")
    with pytest.raises(jira.JiraError, match="no transition to 'Blocked'"):
        client.transition_issue("ACME-7", "Blocked")
    with pytest.raises(jira.JiraError, match="400"):
        client.add_comment("ACME-9", "x")  # the mock handler answers 400 for unknown paths


def test_get_client_picks_mock_without_credentials(wired):
    assert isinstance(jira.get_client(), jira.MockJiraClient)


# ------------------------------------------------------------------ refresh endpoint and status screen
def test_refresh_endpoint_creates_or_updates_the_issue(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    t = new_ticket(api)
    # Ticket already has an issue; refresh must update it, not create a second one
    r = api.post(f"/integrations/jira/tickets/{t['ticket_id']}/refresh")
    assert r.status_code == 200, r.text
    assert r.json()["jira_issue_key"] == "SUP-1" and r.json()["jira_status"] == "To Do"
    assert len(wired.jira.issues) == 1
    assert api.post("/integrations/jira/tickets/9999/refresh").status_code == 404


def test_refresh_endpoint_is_staff_only(api, wired, auth_on, session_factory):
    make_user(session_factory, "emp@x.com", role="employee")
    headers = login(api, "emp@x.com")
    assert api.post("/integrations/jira/tickets/1/refresh", headers=headers).status_code == 403


def test_integrations_status_reports_jira_and_email(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    before = api.get("/integrations/status").json()
    assert before["jira"]["mode"] == "mock" and before["jira"]["connected"] is False
    assert before["jira"]["last_sync"] is None and before["email"]["sent_today"] == 0
    new_ticket(api)  # ticket_received + ai_resolution emails (dry run) and a Jira issue
    status = api.get("/integrations/status").json()
    assert status["jira"]["last_sync"] is not None and status["jira"]["synced_tickets"] == 1
    assert status["email"]["mode"] == "dry_run"
    assert status["email"]["dry_run_today"] == 2 and status["email"]["sent_today"] == 0
    assert status["webhook"]["configured"] is True
    assert api.get("/integrations/jira/tickets").json()[0]["jira_issue_key"] == "SUP-1"
