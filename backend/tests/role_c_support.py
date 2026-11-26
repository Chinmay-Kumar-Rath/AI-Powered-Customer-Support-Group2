"""Shared setup for the Role C tests: every integration in mock / dry-run mode, on the in-memory test database."""
from types import SimpleNamespace

import pytest

from app import hooks
from app.models import Ticket, User
from integrations import email_intake, jira, mailer, notifications

WEBHOOK_KEY = "test-webhook-key"
REQUESTER = "maya@example.com"


@pytest.fixture()
def wired(monkeypatch, session_factory, api):
    """Jira, email and IMAP in mock mode; webhook key set; notifications write to the test database."""
    for name in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "SMTP_USER", "SMTP_PASSWORD",
                 "IMAP_USER", "IMAP_PASSWORD", "IMAP_ENABLED"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("JIRA_MODE", "mock")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
    monkeypatch.setenv("EMAIL_MODE", "dry_run")
    monkeypatch.setenv("IMAP_MODE", "mock")
    monkeypatch.setenv("WEBHOOK_API_KEY", WEBHOOK_KEY)
    monkeypatch.setenv("PUBLIC_API_URL", "http://testserver")
    monkeypatch.setenv("EMAIL_FROM", "support@supportpilot.dev")
    jira.reset_client()
    mailer.reset_mailer()
    monkeypatch.setattr(hooks, "_notifications", notifications)
    monkeypatch.setattr(hooks, "_jira", jira)
    monkeypatch.setattr(notifications, "session_factory", session_factory)
    monkeypatch.setattr(email_intake, "_mock_source", email_intake.MockImapSource())
    yield SimpleNamespace(mailer=mailer.get_mailer(), imap=email_intake._mock_source,
                          jira=jira.get_client(), session_factory=session_factory)
    jira.reset_client()
    mailer.reset_mailer()


def outbox_to(wired, address=REQUESTER):
    return [m for m in wired.mailer.outbox if m[0] == address]


def email_log(session_factory):
    from app.models import EmailLog
    with session_factory() as db:
        return [(r.template, r.to_email, r.status, r.error) for r in db.query(EmailLog).order_by(EmailLog.email_id)]


def jira_rows(session_factory):
    from app.models import JiraTicket
    with session_factory() as db:
        return [(r.ticket_id, r.jira_issue_key, r.jira_status) for r in db.query(JiraTicket).order_by(JiraTicket.jira_id)]


def make_ticket(session_factory, code, email=REQUESTER, **fields):
    """Insert a ticket straight into the database (for analytics tests). Returns its ticket_id."""
    with session_factory() as db:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(name=email.split("@")[0], email=email, role="employee", department="IT", is_active=True)
            db.add(user)
            db.flush()
        ticket = Ticket(user_id=user.user_id, ticket_code=code, subject=fields.pop("subject", "Issue"),
                        description="Something is broken", department="IT", **fields)
        db.add(ticket)
        db.commit()
        return ticket.ticket_id
