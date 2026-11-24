"""Analytics: every number comes from the database, computed the same way for the API and the reports.

Definitions (also written in docs/role_c_integrations.md):
    open               status not Resolved / Closed
    escalation_rate    tickets with at least one escalation / all tickets
    self_service_rate  Closed tickets that were never escalated / Closed tickets
    avg_resolution_h   mean hours from created_at to resolved_at (tickets that have a resolved_at)
    sla_breached       tickets past due_at that were resolved late, or are still open past due_at
    satisfaction_rate  'yes, it is fixed' answers / all feedback answers
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from . import config
from .models import AgentRun, Escalation, Feedback, RecurringIssue, Ticket

RESOLVED_STATES = ("Resolved", "Closed")


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # SQLite returns naive datetimes


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
    closed = [t for t in tickets if t.status == "Closed"]
    total = len(tickets)
    return {
        "total_tickets": total,
        "open": sum(1 for t in tickets if t.status not in RESOLVED_STATES),
        "resolved": sum(1 for t in tickets if t.status == "Resolved"),
        "closed": len(closed),
        "escalated_now": by_status.get("Escalated", 0),
        "by_status": dict(sorted(by_status.items())),
        "escalation_rate": _round(100 * len(escalated_ids & {t.ticket_id for t in tickets}) / total) if total else 0.0,
        "self_service_rate": (_round(100 * sum(1 for t in closed if t.ticket_id not in escalated_ids) / len(closed))
                              if closed else None),
        "avg_resolution_hours": _round(_mean(_hours(t.created_at, t.resolved_at) for t in tickets
                                             if t.resolved_at is not None)),
        "sla_breached": sum(1 for t in tickets if _is_sla_breached(t, now)),
        "by_source": dict(sorted(Counter(t.source for t in tickets).items())),
    }


# ------------------------------------------------------------------ trends
def trends(db: Session, days: int = 30) -> dict:
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
    return {"days": days, "from": start.isoformat(), "to": today.isoformat(),
            "series": [{"date": d.isoformat(), **counts} for d, counts in sorted(buckets.items())]}


# ------------------------------------------------------------------ categories
def categories(db: Session) -> dict:
    tickets = _tickets(db)
    escalated_ids = _escalated_ticket_ids(db)
    total = len(tickets)
    rows = []
    for name in config.CATEGORIES + sorted({t.category for t in tickets if t.category} - set(config.CATEGORIES)):
        group = [t for t in tickets if t.category == name]
        rows.append({
            "category": name,
            "tickets": len(group),
            "percent": _round(100 * len(group) / total) if total else 0.0,
            "escalated": sum(1 for t in group if t.ticket_id in escalated_ids),
            "escalation_rate": (_round(100 * sum(1 for t in group if t.ticket_id in escalated_ids) / len(group))
                                if group else None),
            "avg_ai_confidence": _round(_mean(t.category_confidence for t in group), 2),
        })
    rows.sort(key=lambda r: (-r["tickets"], r["category"]))
    return {"total": total, "categories": rows}


# ------------------------------------------------------------------ agents and engineers
def agent_performance(db: Session) -> dict:
    by_agent = defaultdict(list)
    for run in db.query(AgentRun).all():
        by_agent[run.agent_name].append(run)
    agents = []
    for name, runs in sorted(by_agent.items()):
        ok = sum(1 for r in runs if r.status == "ok")
        agents.append({
            "agent": name,
            "runs": len(runs),
            "ok": ok,
            "failed": len(runs) - ok,
            "success_rate": _round(100 * ok / len(runs)),
            "avg_duration_ms": _round(_mean(r.duration_ms for r in runs)),
            "avg_confidence": _round(_mean(r.confidence for r in runs), 2),
        })

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
        "total": len(escs),
        "by_status": dict(sorted(by_status.items())),
        "by_team": dict(sorted(by_team.items())),
        "by_source": dict(sorted(by_source.items())),
        "open_overdue": overdue,
        "avg_hours_to_accept": _round(_mean(_hours(e.created_at, e.accepted_at) for e in escs if e.accepted_at)),
        "avg_hours_to_resolve": _round(_mean(_hours(e.created_at, e.resolved_at) for e in escs if e.resolved_at)),
    }


# ------------------------------------------------------------------ satisfaction
def satisfaction(db: Session) -> dict:
    fb = db.query(Feedback).all()
    yes = sum(1 for f in fb if f.is_resolved)
    ratings = [f.rating for f in fb if f.rating is not None]
    return {
        "responses": len(fb),
        "fixed_yes": yes,
        "fixed_no": len(fb) - yes,
        "satisfaction_rate": _round(100 * yes / len(fb)) if fb else None,
        "avg_rating": _round(_mean(ratings), 2),
        "rated_responses": len(ratings),
        "rating_distribution": {str(i): sum(1 for r in ratings if r == i) for i in range(1, 6)},
    }


# ------------------------------------------------------------------ recurring issues
def recurring_issues(db: Session) -> dict:
    rows = db.query(RecurringIssue).order_by(RecurringIssue.occurrence_count.desc(),
                                             RecurringIssue.recurring_issue_id).all()
    return {"items": [{
        "signature": r.signature, "category": r.category, "assigned_team": r.assigned_team,
        "occurrences": r.occurrence_count or 0, "status": r.status,
        "first_seen": _aware(r.first_seen).isoformat() if r.first_seen else None,
        "last_seen": _aware(r.last_seen).isoformat() if r.last_seen else None,
        "sample_ticket_ids": r.sample_ticket_ids or [],
    } for r in rows]}


# ------------------------------------------------------------------ summary for reports
def summary(db: Session) -> dict:
    return {
        "generated_at": _now().isoformat(timespec="seconds"),
        "overview": overview(db),
        "categories": categories(db),
        "escalations": escalations(db),
        "satisfaction": satisfaction(db),
        "agent_performance": agent_performance(db),
    }


def summary_rows(report: dict) -> list:
    """Flatten the summary into (section, metric, value) rows for CSV."""
    rows = [("report", "generated_at", report["generated_at"])]
    for key, value in report["overview"].items():
        if isinstance(value, dict):
            rows += [("overview", f"{key}.{k}", v) for k, v in value.items()]
        else:
            rows.append(("overview", key, "" if value is None else value))
    for row in report["categories"]["categories"]:
        rows.append(("categories", row["category"],
                     f"tickets={row['tickets']} percent={row['percent']} escalated={row['escalated']} "
                     f"escalation_rate={row['escalation_rate']}"))
    for key, value in report["escalations"].items():
        if isinstance(value, dict):
            rows += [("escalations", f"{key}.{k}", v) for k, v in value.items()]
        else:
            rows.append(("escalations", key, "" if value is None else value))
    for key, value in report["satisfaction"].items():
        if isinstance(value, dict):
            rows += [("satisfaction", f"{key}.{k}", v) for k, v in value.items()]
        else:
            rows.append(("satisfaction", key, "" if value is None else value))
    return rows
