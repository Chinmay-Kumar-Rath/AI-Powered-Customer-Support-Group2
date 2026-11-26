"""Automated tests for Role C: Integrations & Analytics Backend.

Covers:
1. sync_ticket in mock mode creating/updating jira_tickets.
2. notify for all 7 events in dry_run mode writing to email_log (verifying ai_resolution_sent contains feedback links).
3. POST /intake/webhook rejecting missing/wrong API key with 401 and creating a ticket with valid key.
4. GET /integrations/status and all /analytics/* endpoints returning expected schema and accurate counts.
5. GET /reports/summary?format=csv and format=pdf returning valid non-empty responses.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import agent_bridge, classifier, config, hooks
from app.database import Base, get_db
from app.main import app
from app.models import (
    ActivityLog,
    AgentRun,
    EmailLog,
    Escalation,
    Feedback,
    JiraTicket,
    RecurringIssue,
    Ticket,
    User,
)
from integrations import imap_poller, jira, mailer, notifications, settings as integration_settings


WEBHOOK_KEY = "super-secret-webhook-key"
REQUESTER_EMAIL = "alex@example.com"
FRONTEND_URL = "http://localhost:5173"


@pytest.fixture()
def db_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session_factory(db_engine, monkeypatch):
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(notifications, "session_factory", factory)
    monkeypatch.setattr(hooks, "session_factory", factory)
    return factory


@pytest.fixture()
def client(session_factory, monkeypatch):
    monkeypatch.setattr(config, "AUTH_DISABLED", True)
    monkeypatch.setattr(hooks, "SYNC", True)
    monkeypatch.setattr(hooks, "session_factory", session_factory)
    monkeypatch.setattr(notifications, "session_factory", session_factory)

    monkeypatch.setenv("JIRA_MODE", "mock")
    monkeypatch.setenv("EMAIL_MODE", "dry_run")
    monkeypatch.setenv("IMAP_MODE", "mock")
    monkeypatch.setenv("WEBHOOK_API_KEY", WEBHOOK_KEY)
    monkeypatch.setenv("FRONTEND_URL", FRONTEND_URL)
    monkeypatch.setenv("PUBLIC_API_URL", "http://testserver")

    jira.reset_client()
    mailer.reset_mailer()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(classifier, "classify", lambda s, d, dep: {
        "category": "VPN", "sub_category": "Timeout", "category_confidence": 0.95,
        "severity": "Medium", "severity_confidence": 0.88, "priority": "P2"})

    yield TestClient(app)
    app.dependency_overrides.clear()
    jira.reset_client()
    mailer.reset_mailer()


def _create_seed_ticket(session_factory, code="T-2026-0001", email=REQUESTER_EMAIL, status="Open", **kwargs):
    with session_factory() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name="Alex Test", email=email, role="employee", department="IT", is_active=True)
            db.add(user)
            db.flush()
        ticket = Ticket(
            user_id=user.user_id,
            ticket_code=code,
            subject=kwargs.get("subject", "VPN Connection Issue"),
            description=kwargs.get("description", "Cannot reach the internal network"),
            department="IT",
            source=kwargs.get("source", "web"),
            category=kwargs.get("category", "VPN"),
            severity=kwargs.get("severity", "Medium"),
            priority=kwargs.get("priority", "P2"),
            status=status,
            processing_ms=kwargs.get("processing_ms", 120.0),
            created_at=kwargs.get("created_at", datetime.now(timezone.utc) - timedelta(hours=2)),
            resolved_at=kwargs.get("resolved_at"),
            due_at=kwargs.get("due_at"),
        )
        db.add(ticket)
        db.commit()
        return ticket.ticket_id


# ------------------------------------------------------------------ 1. Jira Integration (Mock Mode)
def test_sync_ticket_mock_mode_creates_and_updates_jira_tickets(session_factory, monkeypatch):
    monkeypatch.setenv("JIRA_MODE", "mock")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
    jira.reset_client()

    ticket_id = _create_seed_ticket(session_factory, code="T-2026-0001", status="Open")

    with session_factory() as db:
        # Initial sync creates Jira issue in mock mode
        row = jira.sync_ticket(db, ticket_id)
        assert row is not None
        assert row.ticket_id == ticket_id
        assert row.jira_issue_key == "SUP-1"
        assert row.jira_key == "SUP-1"
        assert row.jira_status == "To Do"
        assert row.jira_url.endswith("/browse/SUP-1")
        assert row.last_synced_at is not None

        # Verify record exists in DB
        db_row = db.query(JiraTicket).filter(JiraTicket.ticket_id == ticket_id).first()
        assert db_row is not None
        assert db_row.jira_issue_key == "SUP-1"

        # Update ticket status to Escalated -> sync again updates existing Jira issue
        ticket = db.get(Ticket, ticket_id)
        ticket.status = "Escalated"
        db.commit()

        updated_row = jira.sync_ticket(db, ticket_id)
        assert updated_row is not None
        assert updated_row.jira_issue_key == "SUP-1"
        assert updated_row.jira_status == "In Progress"

        # Verify no duplicate jira_tickets rows were created
        total_rows = db.query(JiraTicket).filter(JiraTicket.ticket_id == ticket_id).count()
        assert total_rows == 1


# ------------------------------------------------------------------ 2. Email Notifications (Dry-Run Mode)
def test_notify_all_7_events_in_dry_run_mode(session_factory, monkeypatch):
    monkeypatch.setenv("EMAIL_MODE", "dry_run")
    monkeypatch.setenv("FRONTEND_URL", FRONTEND_URL)
    mailer.reset_mailer()

    ticket_id = _create_seed_ticket(session_factory, code="T-2026-0010", status="Open")

    events = [
        ("ticket_received", {}),
        ("ai_resolution_sent", {"confidence": 0.92}),
        ("escalated", {"team": "Network Team", "reason": "Complex VPN routing problem"}),
        ("assigned", {"assignee_name": "Dave Support", "team": "Network Team"}),
        ("status_changed", {"old_status": "Open", "new_status": "In Progress", "message": "Investigating"}),
        ("resolved", {"notes": "Reset VPN session tunnel"}),
        ("closed", {}),
    ]

    for event_name, ctx in events:
        status = notifications.notify(event_name, ticket_id, **ctx)
        assert status == "dry_run"

    # Verify all 7 events are logged in email_log
    with session_factory() as db:
        logs = db.query(EmailLog).filter(EmailLog.ticket_id == ticket_id).order_by(EmailLog.email_id).all()
        assert len(logs) == 7
        templates_logged = [l.template for l in logs]
        assert "ticket_received" in templates_logged
        assert "ai_resolution" in templates_logged
        assert "escalated" in templates_logged
        assert "assigned" in templates_logged
        assert "status_change" in templates_logged
        assert "resolved" in templates_logged
        assert "closed" in templates_logged
        assert all(l.status == "dry_run" for l in logs)

    # Verify ai_resolution_sent contains action feedback links pointing to FRONTEND_URL
    dry_mailer = mailer.get_mailer()
    assert isinstance(dry_mailer, mailer.DryRunMailer)
    ai_mails = [m for m in dry_mailer.outbox if "Suggested fix" in m[1]]
    assert len(ai_mails) >= 1
    body = ai_mails[0][2]
    assert "Did this fix it?" in body
    expected_yes_link = f"{FRONTEND_URL}/tickets/{ticket_id}?feedback=yes"
    expected_no_link = f"{FRONTEND_URL}/tickets/{ticket_id}?feedback=no"
    assert expected_yes_link in body
    assert expected_no_link in body


# ------------------------------------------------------------------ 3. Webhook Intake Endpoint
def test_webhook_intake_authentication_and_ticket_creation(client, session_factory):
    payload = {
        "subject": "Email sync failure",
        "description": "Outlook fails to authenticate with IMAP server",
        "requester_email": "robin@example.com",
        "priority": "P2",
        "category": "Email",
        "external_id": "EXT-9988",
    }

    # Missing API Key -> 401
    r_no_key = client.post("/intake/webhook", json=payload)
    assert r_no_key.status_code == 401

    # Wrong API Key -> 401
    r_bad_key = client.post("/intake/webhook", json=payload, headers={"X-API-Key": "invalid-key"})
    assert r_bad_key.status_code == 401

    # Valid API Key -> 201 Created
    r_valid = client.post("/intake/webhook", json=payload, headers={"X-API-Key": WEBHOOK_KEY})
    assert r_valid.status_code == 201, r_valid.text
    resp = r_valid.json()
    assert "ticket_id" in resp
    assert resp["ticket_code"].startswith("T-")

    # Verify ticket in database has source="webhook"
    with session_factory() as db:
        ticket = db.get(Ticket, resp["ticket_id"])
        assert ticket is not None
        assert ticket.source == "webhook"
        assert ticket.user.email == "robin@example.com"
        assert ticket.subject == "Email sync failure"


# ------------------------------------------------------------------ 4. Integrations Status & Analytics Endpoints
def test_integrations_status_schema(client, session_factory):
    # Seed 1 ticket synced with Jira and 1 email log
    tid = _create_seed_ticket(session_factory, code="T-2026-0099")
    with session_factory() as db:
        db.add(JiraTicket(ticket_id=tid, jira_issue_key="SUP-99", jira_status="Open",
                          last_updated=datetime.now(timezone.utc)))
        db.add(EmailLog(ticket_id=tid, to_email="alex@example.com", template="ticket_received",
                        status="sent", sent_at=datetime.now(timezone.utc)))
        db.commit()

    r = client.get("/integrations/status")
    assert r.status_code == 200, r.text
    data = r.json()

    # Required structure:
    # jira: { "connected": bool, "mode": str, "last_sync": iso_timestamp | null, "synced_count": int }
    assert "jira" in data
    assert isinstance(data["jira"]["connected"], bool)
    assert data["jira"]["mode"] in ("mock", "live")
    assert "last_sync" in data["jira"]
    assert "synced_count" in data["jira"]
    assert data["jira"]["synced_count"] >= 1

    # email: { "mode": str, "sent_today": int, "failed_today": int }
    assert "email" in data
    assert "mode" in data["email"]
    assert isinstance(data["email"]["sent_today"], int)
    assert isinstance(data["email"]["failed_today"], int)

    # imap: { "configured": bool }
    assert "imap" in data
    assert "configured" in data["imap"]
    assert isinstance(data["imap"]["configured"], bool)


def test_analytics_endpoints_schemas_and_counts(client, session_factory):
    # Seed sample data for analytics
    t1 = _create_seed_ticket(session_factory, code="T-2026-0101", category="Network", status="Resolved",
                             processing_ms=100.0,
                             created_at=datetime.now(timezone.utc) - timedelta(days=2),
                             resolved_at=datetime.now(timezone.utc) - timedelta(days=1))
    t2 = _create_seed_ticket(session_factory, code="T-2026-0102", category="VPN", status="Open",
                             processing_ms=150.0,
                             created_at=datetime.now(timezone.utc) - timedelta(days=1),
                             due_at=datetime.now(timezone.utc) - timedelta(hours=1))  # overdue

    with session_factory() as db:
        # Add escalation
        db.add(Escalation(ticket_id=t2, assigned_team="Network Team", escalation_reason="Outage",
                          status="Open", due_at=datetime.now(timezone.utc) - timedelta(hours=1)))
        # Add feedback
        db.add(Feedback(ticket_id=t1, is_resolved=True, rating=5))
        # Add agent run
        db.add(AgentRun(ticket_id=t1, agent_name="Diagnosis", status="ok", duration_ms=45.0, confidence=0.88))
        # Add recurring issue
        db.add(RecurringIssue(signature="vpn-gateway-drop", category="VPN", assigned_team="Network Team",
                              occurrence_count=5, status="Open"))
        db.commit()

    # 1. GET /analytics/overview
    r_ov = client.get("/analytics/overview")
    assert r_ov.status_code == 200
    ov = r_ov.json()
    assert "total_tickets" in ov
    assert "open_tickets" in ov
    assert "resolved_tickets" in ov
    assert "escalated_tickets" in ov
    assert "auto_resolution_rate" in ov
    assert "avg_response_time_sec" in ov
    assert "avg_satisfaction" in ov
    assert ov["total_tickets"] >= 2
    assert ov["open_tickets"] >= 1
    assert ov["resolved_tickets"] >= 1

    # 2. GET /analytics/trends?days=30 -> [{ date, created, resolved, escalated }]
    r_tr = client.get("/analytics/trends?days=30")
    assert r_tr.status_code == 200
    tr = r_tr.json()
    assert isinstance(tr, list)
    assert len(tr) == 30
    assert "date" in tr[0]
    assert "created" in tr[0]
    assert "resolved" in tr[0]
    assert "escalated" in tr[0]

    # 3. GET /analytics/categories -> [{ category, count, resolved_count, escalated_count }]
    r_cat = client.get("/analytics/categories")
    assert r_cat.status_code == 200
    cat = r_cat.json()
    assert isinstance(cat, list)
    assert len(cat) > 0
    first_cat = cat[0]
    assert "category" in first_cat
    assert "count" in first_cat
    assert "resolved_count" in first_cat
    assert "escalated_count" in first_cat

    # 4. GET /analytics/agent-performance -> [{ agent_name, total_runs, avg_duration_ms, success_rate, avg_confidence }]
    r_ap = client.get("/analytics/agent-performance")
    assert r_ap.status_code == 200
    ap = r_ap.json()
    assert isinstance(ap, list)
    diag = next((a for a in ap if a["agent_name"] == "Diagnosis"), None)
    assert diag is not None
    assert "total_runs" in diag
    assert "avg_duration_ms" in diag
    assert "success_rate" in diag
    assert "avg_confidence" in diag
    assert diag["total_runs"] >= 1
    assert diag["success_rate"] == 100.0

    # 5. GET /analytics/escalations -> { total_escalated, sla_breached, by_team: [{ team, count }], by_status: [{ status, count }] }
    r_esc = client.get("/analytics/escalations")
    assert r_esc.status_code == 200
    esc = r_esc.json()
    assert "total_escalated" in esc
    assert "sla_breached" in esc
    assert "by_team" in esc
    assert "by_status" in esc
    assert isinstance(esc["by_team"], list)
    assert isinstance(esc["by_status"], list)
    assert esc["total_escalated"] >= 1

    # 6. GET /analytics/satisfaction -> { total_responses, avg_rating, positive_rate, distribution: { "1": int, ... } }
    r_sat = client.get("/analytics/satisfaction")
    assert r_sat.status_code == 200
    sat = r_sat.json()
    assert "total_responses" in sat
    assert "avg_rating" in sat
    assert "positive_rate" in sat
    assert "distribution" in sat
    assert sat["total_responses"] >= 1
    assert sat["avg_rating"] == 5.0
    assert sat["distribution"]["5"] >= 1

    # 7. GET /analytics/recurring-issues -> list of rows from recurring_issues
    r_rec = client.get("/analytics/recurring-issues")
    assert r_rec.status_code == 200
    rec = r_rec.json()
    assert isinstance(rec, list)
    assert len(rec) >= 1
    assert rec[0]["signature"] == "vpn-gateway-drop"
    assert rec[0]["occurrence_count"] == 5


# ------------------------------------------------------------------ 5. Reports Summary Endpoint (CSV & PDF)
def test_reports_summary_csv_and_pdf(client, session_factory):
    _create_seed_ticket(session_factory, code="T-2026-0301")

    # CSV report
    r_csv = client.get("/reports/summary?format=csv")
    assert r_csv.status_code == 200
    assert "text/csv" in r_csv.headers.get("content-type", "")
    assert len(r_csv.content) > 0
    csv_text = r_csv.text
    assert "section,metric,value" in csv_text
    assert "overview" in csv_text

    # PDF report
    r_pdf = client.get("/reports/summary?format=pdf")
    assert r_pdf.status_code == 200
    assert "application/pdf" in r_pdf.headers.get("content-type", "")
    assert len(r_pdf.content) > 0
    assert r_pdf.content.startswith(b"%PDF")
