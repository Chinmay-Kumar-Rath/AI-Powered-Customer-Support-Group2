"""Analytics: database aggregations for the API and reports.

Endpoints:
- /analytics/overview
- /analytics/trends
- /analytics/categories
- /analytics/agent-performance
- /analytics/escalations
- /analytics/satisfaction
- /analytics/recurring-issues
- /reports/summary
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import config
from .models import AgentRun, Escalation, Feedback, RecurringIssue, Ticket

RESOLVED_STATES = ("Resolved", "Closed")


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _now():
    return datetime.now(timezone.utc)


def _round(value, digits=1):
    return None if value is None else round(value, digits)


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _hours(start, end):
    start, end = _aware(start), _aware(end)
    if start is None or end is None:
        return None
    return (end - start).total_seconds() / 3600


def _tickets(db: Session):
    return db.query(Ticket).all()


def _escalated_ticket_ids(db: Session) -> set:
    return {row[0] for row in db.query(Escalation.ticket_id).distinct()}


def _is_sla_breached(ticket, now) -> bool:
    due = _aware(ticket.due_at)
    if due is None:
        return False
    resolved = _aware(ticket.resolved_at)
    if resolved is not None:
        return resolved > due
    return ticket.status not in RESOLVED_STATES and now > due


# ------------------------------------------------------------------ overview
def overview(db: Session) -> dict:
    tickets = _tickets(db)
    now = _now()
    escalated_ids = _escalated_ticket_ids(db)
    by_status = Counter(t.status for t in tickets)
    resolved_tickets = [t for t in tickets if t.status in RESOLVED_STATES]
    closed = [t for t in tickets if t.status == "Closed"]
    open_tickets = [t for t in tickets if t.status not in RESOLVED_STATES]
    total = len(tickets)

    # auto resolution rate: resolved/closed tickets that were never escalated
    resolved_total = len(resolved_tickets)
    auto_resolved_count = sum(1 for t in resolved_tickets if t.ticket_id not in escalated_ids)
    auto_res_rate = _round(100.0 * auto_resolved_count / resolved_total) if resolved_total else 0.0

    # avg response time in seconds (processing_ms or time to first response)
    response_times = [t.processing_ms / 1000.0 for t in tickets if t.processing_ms is not None]
    avg_resp_sec = _round(_mean(response_times), 2) if response_times else 0.0

    # avg satisfaction from feedback
    ratings = [f.rating for f in db.query(Feedback.rating).all() if f.rating is not None]
    avg_sat = _round(_mean(ratings), 2)

    return {
        "total_tickets": total,
        "open_tickets": len(open_tickets),
        "resolved_tickets": len(resolved_tickets),
        "escalated_tickets": len(escalated_ids & {t.ticket_id for t in tickets}),
        "auto_resolution_rate": auto_res_rate,
        "avg_response_time_sec": avg_resp_sec,
        "avg_satisfaction": avg_sat,
        # backward compatibility aliases
        "open": len(open_tickets),
        "resolved": sum(1 for t in tickets if t.status == "Resolved"),
        "closed": len(closed),
        "escalated_now": by_status.get("Escalated", 0),
        "by_status": dict(sorted(by_status.items())),
        "escalation_rate": _round(100.0 * len(escalated_ids & {t.ticket_id for t in tickets}) / total) if total else 0.0,
        "self_service_rate": (_round(100.0 * sum(1 for t in closed if t.ticket_id not in escalated_ids) / len(closed))
                              if closed else None),
        "avg_resolution_hours": _round(_mean(_hours(t.created_at, t.resolved_at) for t in tickets
                                             if t.resolved_at is not None)),
        "sla_breached": sum(1 for t in tickets if _is_sla_breached(t, now)),
        "by_source": dict(sorted(Counter(t.source for t in tickets).items())),
    }


# ------------------------------------------------------------------ trends
def trends(db: Session, days: int = 30) -> list:
    today = _now().date()
    start = today - timedelta(days=days - 1)
    buckets = {start + timedelta(days=i): {"created": 0, "resolved": 0, "escalated": 0} for i in range(days)}
    for t in _tickets(db):
        created = _aware(t.created_at)
        if created and created.date() in buckets:
            buckets[created.date()]["created"] += 1
        resolved = _aware(t.resolved_at)
        if resolved and resolved.date() in buckets:
            buckets[resolved.date()]["resolved"] += 1
    for esc in db.query(Escalation).all():
        created = _aware(esc.created_at)
        if created and created.date() in buckets:
            buckets[created.date()]["escalated"] += 1
    return [{"date": d.isoformat(), **counts} for d, counts in sorted(buckets.items())]


def trends_dict(db: Session, days: int = 30) -> dict:
    today = _now().date()
    start = today - timedelta(days=days - 1)
    series = trends(db, days)
    return {"days": days, "from": start.isoformat(), "to": today.isoformat(), "series": series}


# ------------------------------------------------------------------ categories
def categories(db: Session) -> list:
    tickets = _tickets(db)
    escalated_ids = _escalated_ticket_ids(db)
    total = len(tickets)
    rows = []
    category_names = config.CATEGORIES + sorted({t.category for t in tickets if t.category} - set(config.CATEGORIES))
    for name in category_names:
        group = [t for t in tickets if t.category == name]
        resolved = sum(1 for t in group if t.status in RESOLVED_STATES)
        esc_count = sum(1 for t in group if t.ticket_id in escalated_ids)
        rows.append({
            "category": name,
            "count": len(group),
            "tickets": len(group),  # alias
            "resolved_count": resolved,
            "escalated_count": esc_count,
            "escalated": esc_count,  # alias
            "percent": _round(100.0 * len(group) / total) if total else 0.0,
            "escalation_rate": (_round(100.0 * esc_count / len(group)) if group else None),
            "avg_ai_confidence": _round(_mean(t.category_confidence for t in group), 2),
        })
    rows.sort(key=lambda r: (-r["count"], r["category"]))
    return rows


def categories_dict(db: Session) -> dict:
    rows = categories(db)
    return {"total": sum(r["count"] for r in rows), "categories": rows}


# ------------------------------------------------------------------ agents
def agent_performance(db: Session) -> list:
    by_agent = defaultdict(list)
    for run in db.query(AgentRun).all():
        by_agent[run.agent_name].append(run)
    agents = []
    for name, runs in sorted(by_agent.items()):
        ok = sum(1 for r in runs if r.status == "ok")
        total = len(runs)
        agents.append({
            "agent_name": name,
            "agent": name,  # alias
            "total_runs": total,
            "runs": total,  # alias
            "ok": ok,
            "failed": total - ok,
            "success_rate": _round(100.0 * ok / total) if total else 0.0,
            "avg_duration_ms": _round(_mean(r.duration_ms for r in runs)),
            "avg_confidence": _round(_mean(r.confidence for r in runs), 2),
        })
    return agents


def agent_performance_dict(db: Session) -> dict:
    agents = agent_performance(db)
    by_engineer = defaultdict(list)
    for esc in db.query(Escalation).filter(Escalation.assigned_to.isnot(None)).all():
        by_engineer[esc.assignee.name if esc.assignee else str(esc.assigned_to)].append(esc)
    engineers = []
    for name, escs in sorted(by_engineer.items()):
        resolved = [e for e in escs if e.status == "Resolved"]
        engineers.append({
            "engineer": name,
            "assigned": len(escs),
            "resolved": len(resolved),
            "open": len(escs) - len(resolved),
            "avg_hours_to_resolve": _round(_mean(_hours(e.created_at, e.resolved_at) for e in resolved)),
        })
    return {"agents": agents, "engineers": engineers}


# ------------------------------------------------------------------ escalations
def escalations(db: Session) -> dict:
    escs = db.query(Escalation).all()
    now = _now()
    by_status = Counter(e.status for e in escs)
    by_team = Counter(e.assigned_team or "unassigned" for e in escs)
    by_source = Counter(e.escalated_by or "unknown" for e in escs)
    overdue = sum(1 for e in escs if e.status != "Resolved" and _aware(e.due_at) and _aware(e.due_at) < now)
    return {
        "total_escalated": len(escs),
        "total": len(escs),  # alias
        "sla_breached": overdue,
        "open_overdue": overdue,  # alias
        "by_team": [{"team": team, "count": count} for team, count in sorted(by_team.items())],
        "by_team_dict": dict(sorted(by_team.items())),
        "by_status": [{"status": st, "count": count} for st, count in sorted(by_status.items())],
        "by_status_dict": dict(sorted(by_status.items())),
        "by_source": dict(sorted(by_source.items())),
        "avg_hours_to_accept": _round(_mean(_hours(e.created_at, e.accepted_at) for e in escs if e.accepted_at)),
        "avg_hours_to_resolve": _round(_mean(_hours(e.created_at, e.resolved_at) for e in escs if e.resolved_at)),
    }


# ------------------------------------------------------------------ satisfaction
def satisfaction(db: Session) -> dict:
    fb = db.query(Feedback).all()
    yes = sum(1 for f in fb if f.is_resolved)
    total = len(fb)
    ratings = [f.rating for f in fb if f.rating is not None]
    dist = {str(i): sum(1 for r in ratings if r == i) for i in range(1, 6)}
    pos_rate = _round(100.0 * yes / total) if total else None
    return {
        "total_responses": total,
        "responses": total,  # alias
        "fixed_yes": yes,
        "fixed_no": total - yes,
        "avg_rating": _round(_mean(ratings), 2),
        "positive_rate": pos_rate,
        "satisfaction_rate": pos_rate,  # alias
        "rated_responses": len(ratings),
        "distribution": dist,
        "rating_distribution": dist,  # alias
    }


# ------------------------------------------------------------------ recurring issues
def recurring_issues(db: Session) -> list:
    rows = db.query(RecurringIssue).order_by(RecurringIssue.occurrence_count.desc(),
                                             RecurringIssue.recurring_issue_id).all()
    return [{
        "recurring_issue_id": r.recurring_issue_id,
        "signature": r.signature,
        "category": r.category,
        "assigned_team": r.assigned_team,
        "occurrence_count": r.occurrence_count or 0,
        "occurrences": r.occurrence_count or 0,  # alias
        "status": r.status,
        "first_seen": _aware(r.first_seen).isoformat() if r.first_seen else None,
        "last_seen": _aware(r.last_seen).isoformat() if r.last_seen else None,
        "sample_ticket_ids": r.sample_ticket_ids or [],
    } for r in rows]


def recurring_issues_dict(db: Session) -> dict:
    items = recurring_issues(db)
    return {"items": items}


# ------------------------------------------------------------------ summary for reports
def summary(db: Session) -> dict:
    return {
        "generated_at": _now().isoformat(timespec="seconds"),
        "overview": overview(db),
        "categories": categories_dict(db),
        "escalations": escalations(db),
        "satisfaction": satisfaction(db),
        "agent_performance": agent_performance_dict(db),
    }


def summary_rows(report: dict) -> list:
    """Flatten the summary into (section, metric, value) rows for CSV."""
    rows = [("report", "generated_at", report["generated_at"])]
    for key, value in report["overview"].items():
        if isinstance(value, dict):
            rows += [("overview", f"{key}.{k}", v) for k, v in value.items()]
        elif not isinstance(value, list):
            rows.append(("overview", key, "" if value is None else value))
    cats = report["categories"].get("categories", report["categories"])
    for row in cats:
        rows.append(("categories", row["category"],
                     f"tickets={row.get('count', row.get('tickets', 0))} "
                     f"resolved={row.get('resolved_count', 0)} "
                     f"escalated={row.get('escalated_count', row.get('escalated', 0))}"))
    for key, value in report["escalations"].items():
        if isinstance(value, dict):
            rows += [("escalations", f"{key}.{k}", v) for k, v in value.items()]
        elif not isinstance(value, list):
            rows.append(("escalations", key, "" if value is None else value))
    for key, value in report["satisfaction"].items():
        if isinstance(value, dict):
            rows += [("satisfaction", f"{key}.{k}", v) for k, v in value.items()]
        elif not isinstance(value, list):
            rows.append(("satisfaction", key, "" if value is None else value))
    return rows
