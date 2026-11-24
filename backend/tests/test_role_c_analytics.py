"""Analytics: every number checked against values worked out by hand from the fixture data below."""
from datetime import datetime, timedelta, timezone

from app.models import AgentRun, Escalation, Feedback, RecurringIssue
from .helpers import login, make_user
from .role_c_support import make_ticket, wired  # noqa: F401

BASE = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)  # fixed clock for the fixture data


def seed(session_factory):
    """Four tickets, two escalations, two engineers' outcomes, three feedback answers, two agent steps."""
    ids = {
        "vpn_closed": make_ticket(session_factory, "T-0001", category="VPN", source="web", status="Closed",
                                  created_at=BASE - timedelta(days=2), resolved_at=BASE - timedelta(days=2) + timedelta(hours=2),
                                  closed_at=BASE - timedelta(days=2) + timedelta(hours=3), category_confidence=0.9),
        "mail_escalated": make_ticket(session_factory, "T-0002", email="ana@example.com", category="Email",
                                      source="email", status="Escalated", created_at=BASE - timedelta(hours=1),
                                      due_at=BASE - timedelta(minutes=30), category_confidence=0.8),
        "security_resolved": make_ticket(session_factory, "T-0003", category="Security", source="web",
                                         status="Resolved", created_at=BASE - timedelta(hours=5),
                                         resolved_at=BASE - timedelta(hours=1), due_at=BASE + timedelta(hours=3),
                                         category_confidence=0.6),
        "mail_closed": make_ticket(session_factory, "T-0004", category="Email", source="web", status="Closed",
                                   created_at=BASE - timedelta(hours=3), resolved_at=BASE - timedelta(hours=2),
                                   due_at=BASE + timedelta(hours=21), category_confidence=0.6),
    }
    with session_factory() as db:
        eve = make_user(session_factory, "eve@supportpilot.dev", role="engineer", team="Network Team",
                        name="Eve Engineer")
        db.add_all([
            Escalation(ticket_id=ids["mail_escalated"], assigned_team="Messaging Team", escalated_by="AI",
                       escalation_reason="low confidence", status="Open", assigned_to=eve,
                       created_at=BASE - timedelta(hours=1), due_at=BASE - timedelta(minutes=30)),
            Escalation(ticket_id=ids["security_resolved"], assigned_team="Security Team", escalated_by="AI",
                       escalation_reason="security", status="Resolved", assigned_to=eve,
                       created_at=BASE - timedelta(hours=5), accepted_at=BASE - timedelta(hours=4),
                       resolved_at=BASE - timedelta(hours=1), due_at=BASE + timedelta(hours=3)),
            Feedback(ticket_id=ids["vpn_closed"], is_resolved=True, rating=5),
            Feedback(ticket_id=ids["mail_closed"], is_resolved=True, rating=4),
            Feedback(ticket_id=ids["security_resolved"], is_resolved=False),
            AgentRun(ticket_id=ids["vpn_closed"], agent_name="Resolution", status="ok", duration_ms=50, confidence=0.8),
            AgentRun(ticket_id=ids["vpn_closed"], agent_name="Diagnosis", status="ok", duration_ms=10, confidence=0.9),
            AgentRun(ticket_id=ids["mail_escalated"], agent_name="Diagnosis", status="ok", duration_ms=20, confidence=0.8),
            AgentRun(ticket_id=ids["security_resolved"], agent_name="Diagnosis", status="ok", duration_ms=30, confidence=0.7),
            AgentRun(ticket_id=ids["mail_closed"], agent_name="Diagnosis", status="error", duration_ms=40, confidence=0.6),
            RecurringIssue(signature="vpn-timeout", category="VPN", assigned_team="Network Team", occurrence_count=7,
                           first_seen=BASE - timedelta(days=10), last_seen=BASE - timedelta(days=1),
                           sample_ticket_ids=[ids["vpn_closed"]], status="Open"),
            RecurringIssue(signature="email-bounce", category="Email", assigned_team="Messaging Team",
                           occurrence_count=3, status="Open"),
        ])
        db.commit()
    return ids


def test_overview_numbers(api, wired, session_factory):
    seed(session_factory)
    o = api.get("/analytics/overview").json()
    assert o["total_tickets"] == 4
    assert o["open"] == 1                      # only the escalated one is still open
    assert o["resolved"] == 1 and o["closed"] == 2 and o["escalated_now"] == 1
    assert o["by_status"] == {"Closed": 2, "Escalated": 1, "Resolved": 1}
    assert o["escalation_rate"] == 50.0        # 2 of 4 tickets were escalated
    assert o["self_service_rate"] == 100.0     # both closed tickets were never escalated
    assert o["avg_resolution_hours"] == 2.3    # (2 + 4 + 1) / 3
    assert o["sla_breached"] == 1              # the escalated ticket is past its deadline
    assert o["by_source"] == {"email": 1, "web": 3}


def test_trends_add_up_over_the_window(api, wired, session_factory):
    seed(session_factory)
    t = api.get("/analytics/trends?days=30").json()
    assert t["days"] == 30 and len(t["series"]) == 30
    assert sum(d["created"] for d in t["series"]) == 4
    assert sum(d["resolved"] for d in t["series"]) == 3
    assert sum(d["escalated"] for d in t["series"]) == 2


def test_categories_numbers(api, wired, session_factory):
    seed(session_factory)
    c = api.get("/analytics/categories").json()
    assert c["total"] == 4
    rows = {r["category"]: r for r in c["categories"]}
    assert c["categories"][0]["category"] == "Email"  # most tickets first
    assert rows["Email"] == {"category": "Email", "tickets": 2, "percent": 50.0, "escalated": 1,
                             "escalation_rate": 50.0, "avg_ai_confidence": 0.7}
    assert rows["VPN"]["tickets"] == 1 and rows["VPN"]["percent"] == 25.0 and rows["VPN"]["escalation_rate"] == 0.0
    assert rows["Security"]["escalation_rate"] == 100.0
    assert rows["Hardware"]["tickets"] == 0 and rows["Hardware"]["escalation_rate"] is None


def test_agent_performance_numbers(api, wired, session_factory):
    seed(session_factory)
    a = api.get("/analytics/agent-performance").json()
    agents = {r["agent"]: r for r in a["agents"]}
    assert agents["Diagnosis"] == {"agent": "Diagnosis", "runs": 4, "ok": 3, "failed": 1, "success_rate": 75.0,
                                   "avg_duration_ms": 25.0, "avg_confidence": 0.75}
    assert agents["Resolution"]["success_rate"] == 100.0 and agents["Resolution"]["avg_duration_ms"] == 50.0
    eng = a["engineers"][0]
    assert eng == {"engineer": "Eve Engineer", "assigned": 2, "resolved": 1, "open": 1,
                   "avg_hours_to_resolve": 4.0}


def test_escalation_numbers(api, wired, session_factory):
    seed(session_factory)
    e = api.get("/analytics/escalations").json()
    assert e["total"] == 2
    assert e["by_status"] == {"Open": 1, "Resolved": 1}
    assert e["by_team"] == {"Messaging Team": 1, "Security Team": 1}
    assert e["by_source"] == {"AI": 2}
    assert e["open_overdue"] == 1
    assert e["avg_hours_to_accept"] == 1.0 and e["avg_hours_to_resolve"] == 4.0


def test_satisfaction_numbers(api, wired, session_factory):
    seed(session_factory)
    s = api.get("/analytics/satisfaction").json()
    assert s["responses"] == 3 and s["fixed_yes"] == 2 and s["fixed_no"] == 1
    assert s["satisfaction_rate"] == 66.7
    assert s["avg_rating"] == 4.5 and s["rated_responses"] == 2
    assert s["rating_distribution"] == {"1": 0, "2": 0, "3": 0, "4": 1, "5": 1}


def test_recurring_issues_sorted_by_occurrences(api, wired, session_factory):
    seed(session_factory)
    items = api.get("/analytics/recurring-issues").json()["items"]
    assert [i["signature"] for i in items] == ["vpn-timeout", "email-bounce"]
    assert items[0]["occurrences"] == 7 and items[0]["sample_ticket_ids"]


def test_empty_database_gives_zeros_not_errors(api, wired):
    o = api.get("/analytics/overview").json()
    assert o["total_tickets"] == 0 and o["escalation_rate"] == 0.0 and o["self_service_rate"] is None
    assert api.get("/analytics/satisfaction").json()["satisfaction_rate"] is None


def test_reports_as_csv_and_pdf(api, wired, session_factory):
    seed(session_factory)
    csv_resp = api.get("/reports/summary?format=csv")
    assert csv_resp.status_code == 200 and csv_resp.headers["content-type"].startswith("text/csv")
    lines = csv_resp.text.splitlines()
    assert lines[0] == "section,metric,value"
    assert "overview,total_tickets,4" in lines and "overview,escalation_rate,50.0" in lines
    assert "satisfaction,satisfaction_rate,66.7" in lines
    pdf = api.get("/reports/summary?format=pdf")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF") and b"%%EOF" in pdf.content[-32:]


def test_analytics_are_staff_only(api, wired, auth_on, session_factory):
    make_user(session_factory, "emp@x.com", role="employee")
    assert api.get("/analytics/overview").status_code == 401  # no token at all
    headers = login(api, "emp@x.com")
    assert api.get("/analytics/overview", headers=headers).status_code == 403
    assert api.get("/reports/summary?format=pdf", headers=headers).status_code == 403
