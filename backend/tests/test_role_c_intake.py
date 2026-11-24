"""Intake: the webhook (API key header) and the IMAP email poller, both creating tickets with the right source."""
from email.message import EmailMessage

from app import agent_bridge
from app.models import Ticket
from integrations import email_intake
from .role_c_support import WEBHOOK_KEY, wired  # noqa: F401
from .helpers import agents_result


def raw_mail(sender="Maya Lopez <maya@example.com>", subject="Cannot open the shared drive", body="The drive is empty.\n"):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "support@supportpilot.dev"
    msg["Subject"] = subject
    msg.set_content(body)
    return bytes(msg)


WEBHOOK_BODY = {"subject": "Printer offline", "description": "The 3rd floor printer shows offline",
                "email": "sam@example.com", "name": "Sam"}


# ------------------------------------------------------------------ webhook
def test_webhook_needs_the_key_header(api, wired):
    r = api.post("/intake/webhook", json=WEBHOOK_BODY)
    assert r.status_code == 401
    r = api.post("/intake/webhook", json=WEBHOOK_BODY, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_webhook_is_closed_when_no_key_is_configured(api, wired, monkeypatch):
    monkeypatch.setenv("WEBHOOK_API_KEY", "")
    r = api.post("/intake/webhook", json=WEBHOOK_BODY, headers={"X-API-Key": "anything"})
    assert r.status_code == 503


def test_webhook_creates_a_ticket_with_api_source(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    r = api.post("/intake/webhook", json=WEBHOOK_BODY, headers={"X-API-Key": WEBHOOK_KEY})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ticket_code"].startswith("T-") and body["status"] == "Awaiting User"
    with wired.session_factory() as db:
        ticket = db.get(Ticket, body["ticket_id"])
        assert ticket.source == "api" and ticket.subject == "Printer offline"
        assert ticket.user.email == "sam@example.com"


def test_webhook_rejects_an_invalid_requester_email(api, wired):
    r = api.post("/intake/webhook", json={**WEBHOOK_BODY, "email": "not-an-email"},
                 headers={"X-API-Key": WEBHOOK_KEY})
    assert r.status_code == 422


# ------------------------------------------------------------------ email parsing
def test_parse_message_takes_sender_subject_and_the_new_text_only():
    raw = raw_mail(body="Please help.\n\nOn Mon, 3 Nov 2026 at 9:00, Support wrote:\n> old text\n")
    parsed = email_intake.parse_message(raw)
    assert parsed["email"] == "maya@example.com" and parsed["name"] == "Maya Lopez"
    assert parsed["subject"] == "Cannot open the shared drive"
    assert parsed["description"] == "Please help."


def test_parse_message_without_a_sender_is_rejected():
    msg = EmailMessage()
    msg["Subject"] = "No sender"
    msg.set_content("hi")
    try:
        email_intake.parse_message(bytes(msg))
    except ValueError as exc:
        assert "From" in str(exc)
    else:
        raise AssertionError("expected ValueError")


# ------------------------------------------------------------------ IMAP poller
def test_poll_creates_email_tickets_and_keeps_bad_messages_unread(wired, session_factory):
    wired.imap.add(raw_mail())
    bad = wired.imap.add(EmailMessage().as_bytes())  # no From header
    with session_factory() as db:
        result = email_intake.poll_once(db, source=wired.imap)
    assert result["fetched"] == 2 and len(result["created"]) == 1 and len(result["errors"]) == 1
    assert list(wired.imap.inbox) == [bad]  # the good one is marked read, the bad one waits for a human
    with session_factory() as db:
        ticket = db.query(Ticket).filter(Ticket.subject == "Cannot open the shared drive").one()
        assert ticket.source == "email" and ticket.user.email == "maya@example.com"


def test_poll_endpoint_runs_the_poller_now(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    wired.imap.add(raw_mail(subject="VPN keeps dropping"))
    r = api.post("/integrations/email/poll")
    assert r.status_code == 200, r.text
    assert r.json()["fetched"] == 1 and len(r.json()["created"]) == 1 and r.json()["errors"] == []
    assert wired.imap.inbox == {}


def test_poller_is_off_unless_enabled(monkeypatch):
    monkeypatch.delenv("IMAP_ENABLED", raising=False)
    assert email_intake.start_poller() is None
