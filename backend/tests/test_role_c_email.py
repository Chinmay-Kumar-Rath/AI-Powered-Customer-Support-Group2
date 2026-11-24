"""Email: templates, the seven notifications, dry-run and SMTP modes, the email_log, and the feedback links."""
import re
from urllib.parse import urlparse

import pytest

from app import agent_bridge
from integrations import mailer, notifications, templates
from .helpers import agents_result
from .role_c_support import REQUESTER, email_log, make_ticket, outbox_to, wired  # noqa: F401


def new_ticket(api, headers=None, **over):
    body = {"subject": "VPN drops", "description": "Connection drops every ten minutes", "email": REQUESTER,
            **over}
    r = api.post("/tickets", json=body, headers=headers or {})
    assert r.status_code == 201, r.text
    return r.json()


def link(body: str, label: str) -> str:
    match = re.search(label + r":\s+(\S+)", body)
    assert match, body
    return match.group(1)


# ------------------------------------------------------------------ templates
@pytest.mark.parametrize("name", templates.names())
def test_every_template_renders_without_missing_values(name):
    data = {"ticket_code": "T-2026-0001", "subject": "VPN drops", "greeting": "Maya", "status": "Open",
            "response_text": "Restart the client.", "steps_block": "Steps:\n  1. Restart\n\n",
            "yes_link": "http://y", "no_link": "http://n", "team": "Network Team", "reason": "Needs a human",
            "due_line": "We aim to respond by soon.\n", "assignee_name": "Eve", "old_status": "Open",
            "new_status": "In Progress", "message_block": "", "notes_block": ""}
    subject, body = templates.render(name, data)
    assert "T-2026-0001" in subject and "\n" not in subject
    assert "Hello Maya" in body and "{" not in body


def test_ai_resolution_email_has_the_feedback_question():
    _, body = templates.render("ai_resolution", {"ticket_code": "T", "subject": "s", "greeting": "M",
                                                 "response_text": "Try this", "steps_block": "",
                                                 "yes_link": "http://y", "no_link": "http://n"})
    assert "Did this fix it?" in body and "http://y" in body and "http://n" in body


# ------------------------------------------------------------------ the notifications, logged in dry-run
def test_ticket_received_is_sent_to_the_requester_and_logged(api, wired):
    t = new_ticket(api)
    msgs = outbox_to(wired)
    assert msgs and f"We received your request {t['ticket_code']}" in msgs[0][1]
    logs = email_log(wired.session_factory)
    assert logs[0] == ("ticket_received", REQUESTER, "dry_run", None)


def test_ai_answer_email_links_work_and_yes_closes_the_ticket(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    t = new_ticket(api)
    ai_mail = [m for m in outbox_to(wired) if "Suggested fix" in m[1]]
    assert len(ai_mail) == 1 and "Did this fix it?" in ai_mail[0][2]
    yes_url = urlparse(link(ai_mail[0][2], "Yes, it is fixed"))
    r = api.get(yes_url.path + "?" + yes_url.query)  # no login: the link is signed
    assert r.status_code == 200 and "closed" in r.text
    assert api.get(f"/tickets/{t['ticket_id']}").json()["status"] == "Closed"
    assert outbox_to(wired)[-1][1].endswith("is closed - thank you")


def test_no_link_escalates_to_a_human(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    t = new_ticket(api)
    ai_mail = [m for m in outbox_to(wired) if "Suggested fix" in m[1]][0]
    no_url = urlparse(link(ai_mail[2], "No, I still need help"))
    assert api.get(no_url.path + "?" + no_url.query).status_code == 200
    assert api.get(f"/tickets/{t['ticket_id']}").json()["status"] == "Escalated"
    escalated = [m for m in outbox_to(wired) if "passed to our Network Team" in m[1]]
    assert len(escalated) == 1 and "The user reported" in escalated[0][2]


def test_tampered_or_expired_feedback_links_are_refused(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.9))
    t = new_ticket(api)
    ai_mail = [m for m in outbox_to(wired) if "Suggested fix" in m[1]][0]
    url = urlparse(link(ai_mail[2], "Yes, it is fixed"))
    tampered = url.query.replace("verdict=yes", "verdict=no")
    assert api.get(f"/feedback/{t['ticket_id']}?{tampered}").status_code == 403  # signature no longer matches
    assert api.get(f"/feedback/{t['ticket_id']}?verdict=yes&exp=1&sig=abc").status_code == 403  # expired


def test_escalation_email_goes_to_the_requester(api, wired, monkeypatch):
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.2, needs_review=True))
    t = new_ticket(api)
    templates_sent = [row[0] for row in email_log(wired.session_factory)]
    assert templates_sent == ["ticket_received", "escalated"]
    subject, body = outbox_to(wired)[-1][1], outbox_to(wired)[-1][2]
    assert f"{t['ticket_code']} has been passed to our Network Team" in subject
    assert "We aim to respond by" in body and "Reason:" in body


def test_assignment_and_status_change_emails(api, wired, monkeypatch, auth_on, session_factory):
    from .helpers import login, make_user
    monkeypatch.setattr(agent_bridge, "run", agents_result(confidence=0.2, needs_review=True))
    make_user(session_factory, "admin@x.com", role="admin")
    make_user(session_factory, "eng@x.com", role="engineer", team="Network Team", name="Eve Engineer")
    admin = login(api, "admin@x.com")
    t = new_ticket(api, headers=admin, email=REQUESTER)  # ticket created by an admin for the requester
    esc = api.get(f"/tickets/{t['ticket_id']}/escalation", headers=admin).json()
    engineer_id = api.get("/users", headers=admin).json()
    eng = next(u for u in engineer_id if u["email"] == "eng@x.com")
    assert api.post(f"/escalations/{esc['escalation_id']}/assign", json={"user_id": eng["user_id"]},
                    headers=admin).status_code == 200
    # one email when routing auto-assigned her during the escalation, one for the manual assignment
    assigned = [m for m in outbox_to(wired) if "assigned to Eve Engineer" in m[1]]
    assert len(assigned) == 2
    eng_headers = login(api, "eng@x.com")
    assert api.post(f"/escalations/{esc['escalation_id']}/accept", headers=eng_headers).status_code == 200
    assert any("is now In Progress" in m[1] for m in outbox_to(wired))
    assert api.post(f"/escalations/{esc['escalation_id']}/notes", headers=eng_headers,
                    json={"note": "Please reboot", "visible_to_user": True}).status_code == 200
    assert any("Please reboot" in m[2] for m in outbox_to(wired))
    assert api.post(f"/escalations/{esc['escalation_id']}/resolve", headers=eng_headers,
                    json={"notes": "Fixed the DNS record"}).status_code == 200
    resolved = [m for m in outbox_to(wired) if m[1].endswith("has been resolved")]
    assert len(resolved) == 1 and "Fixed the DNS record" in resolved[0][2]


# ------------------------------------------------------------------ dry-run, SMTP and failures
def test_dry_run_is_the_default_and_sends_nothing(monkeypatch):
    monkeypatch.delenv("EMAIL_MODE", raising=False)
    assert isinstance(mailer.get_mailer(), mailer.DryRunMailer)


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.calls = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, msg):
        self.calls.append(("send", msg["To"], msg["Subject"]))


def test_smtp_mode_sends_through_gmail_settings_and_logs_sent(api, wired, monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("EMAIL_MODE", "smtp")
    monkeypatch.setenv("SMTP_USER", "support.bot@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")
    mailer.reset_mailer()
    new_ticket(api)
    server = FakeSMTP.instances[0]
    assert (server.host, server.port) == ("smtp.gmail.com", 587)
    assert server.calls[0] == "starttls"
    assert server.calls[1] == ("login", "support.bot@gmail.com", "abcd efgh ijkl mnop")
    assert ("send", REQUESTER, server.calls[2][2]) and server.calls[2][0] == "send"
    assert email_log(wired.session_factory)[0][2] == "sent"


def test_smtp_without_credentials_logs_failed_and_does_not_break_the_ticket(api, wired, monkeypatch):
    monkeypatch.setenv("EMAIL_MODE", "smtp")
    mailer.reset_mailer()
    t = new_ticket(api)  # must still succeed
    assert t["ticket_code"]
    status = email_log(wired.session_factory)[0]
    assert status[2] == "failed" and "SMTP_USER" in status[3]


def test_notify_for_unknown_ticket_does_nothing(wired):
    assert notifications.notify("closed", 4242) is None
    assert wired.mailer.outbox == []
