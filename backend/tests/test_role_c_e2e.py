"""The Role C 'done' check: an escalation creates a Jira issue, the requester gets the right email, and the
analytics and status screens show the right numbers. Everything runs in mock / dry-run mode."""
from app import agent_bridge
from .helpers import agents_result
from .role_c_support import REQUESTER, email_log, jira_rows, outbox_to, wired  # noqa: F401


def test_escalation_creates_jira_issue_emails_the_user_and_the_numbers_match(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.2, needs_review=True))

    # 1. the employee reports a problem; the AI is not confident, so a human takes it
    r = api.post("/tickets", json={"subject": "VPN keeps dropping",
                                   "description": "Connection drops every ten minutes since Monday",
                                   "email": REQUESTER})
    assert r.status_code == 201, r.text
    ticket = r.json()
    assert ticket["status"] == "Escalated"

    # 2. a Jira issue exists for it and is in progress
    issues = api.get("/integrations/jira/tickets").json()
    assert len(issues) == 1 and issues[0]["jira_issue_key"] == "SUP-1"
    assert issues[0]["jira_status"] == "In Progress" and issues[0]["ticket_id"] == ticket["ticket_id"]
    assert wired.jira.issues["SUP-1"]["summary"].startswith(f"[{ticket['ticket_code']}]")

    # 3. the requester got the right emails, all logged as dry runs
    assert [row[0] for row in email_log(wired.session_factory)] == ["ticket_received", "escalated"]
    assert all(row[2] == "dry_run" for row in email_log(wired.session_factory))
    to_requester = outbox_to(wired)
    assert len(to_requester) == 2
    assert f"{ticket['ticket_code']} has been passed to our Network Team" in to_requester[1][1]

    # 4. analytics agree with what happened
    o = api.get("/analytics/overview").json()
    assert o["total_tickets"] == 1 and o["escalated_now"] == 1 and o["escalation_rate"] == 100.0
    assert o["open"] == 1 and o["closed"] == 0 and o["by_source"] == {"web": 1}
    e = api.get("/analytics/escalations").json()
    assert e.get("total_escalated", e.get("total")) == 1
    by_team = dict(e["by_team"]) if isinstance(e["by_team"], dict) else {r["team"]: r["count"] for r in e["by_team"]}
    assert by_team == {"Network Team": 1}
    c = api.get("/analytics/categories").json()
    cats = c if isinstance(c, list) else c.get("categories", [])
    vpn_row = next(row for row in cats if row["category"] == "VPN")
    assert vpn_row.get("count", vpn_row.get("tickets")) == 1

    # 5. the status screen shows Jira connected-in-mock, the last sync and today's emails
    s = api.get("/integrations/status").json()
    assert s["jira"]["mode"] == "mock" and s["jira"]["last_sync"] is not None
    assert s["jira"]["synced_tickets"] == 1
    assert s["email"]["dry_run_today"] == 2 and s["email"]["sent_today"] == 0 and s["email"]["failed_today"] == 0


def test_user_resolving_the_escalation_closes_the_loop_everywhere(api, wired, monkeypatch, auth_on, session_factory):
    from .helpers import login, make_user
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.2, needs_review=True))
    make_user(session_factory, "admin@x.com", role="admin")
    admin = login(api, "admin@x.com")
    t = api.post("/tickets", json={"subject": "VPN", "description": "Cannot connect at all",
                                   "email": REQUESTER}, headers=admin).json()
    esc = api.get(f"/tickets/{t['ticket_id']}/escalation", headers=admin).json()
    assert api.post(f"/escalations/{esc['escalation_id']}/accept", headers=admin).status_code == 200
    assert api.post(f"/escalations/{esc['escalation_id']}/resolve", headers=admin,
                    json={"notes": "Reset the VPN profile"}).status_code == 200
    assert api.get("/integrations/jira/tickets", headers=admin).json()[0]["jira_status"] == "Done"
    o = api.get("/analytics/overview", headers=admin).json()
    assert o["resolved"] == 1 and o["escalated_now"] == 0
    assert any("Reset the VPN profile" in m[2] for m in outbox_to(wired))


def test_webhook_and_email_intake_both_reach_the_same_pipeline(api, wired, monkeypatch):
    from email.message import EmailMessage
    from app.models import Ticket
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    r = api.post("/intake/webhook", json={"description": "Printer offline", "email": "sam@example.com"},
                 headers={"X-API-Key": "test-webhook-key"})
    assert r.status_code == 201
    msg = EmailMessage()
    msg["From"] = "ana@example.com"
    msg["Subject"] = "Mailbox full"
    msg.set_content("My mailbox is full again.")
    wired.imap.add(bytes(msg))
    assert len(api.post("/integrations/email/poll").json()["created"]) == 1
    with wired.session_factory() as db:
        sources = sorted(t.source for t in db.query(Ticket).all())
    assert sources == ["api", "email"]
    assert api.get("/analytics/overview").json()["by_source"] == {"api": 1, "email": 1}
