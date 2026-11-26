"""The data behind the Integrations status screen: Jira connected, last sync, emails sent today."""
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import email_intake, jira, settings as cfg


def _iso(dt):
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


def build_status(db: Session, settings: cfg.Settings = None) -> dict:
    from app.models import EmailLog, JiraTicket

    s = settings or cfg.load()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    status_rows = (db.query(EmailLog.status, func.count(EmailLog.email_id))
                   .filter(EmailLog.sent_at >= today_start).group_by(EmailLog.status).all())
    counts = {str(r[0]): int(r[1]) for r in status_rows}
    last_sync = db.query(func.max(JiraTicket.last_updated)).scalar()
    health = jira.health()
    poll = email_intake.status()
    synced_count = db.query(func.count(func.distinct(JiraTicket.ticket_id))).scalar() or 0
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jira": {
            "mode": s.jira_mode,
            "connected": jira.is_connected(s),
            "site": s.jira_base_url or None,
            "project_key": s.jira_project_key,
            "last_sync": _iso(last_sync),
            "synced_count": synced_count,
            "synced_tickets": synced_count,
            "last_error": health["last_error"] if s.jira_mode == "live" else None,
        },
        "email": {
            "mode": s.email_mode,
            "from": s.email_from,
            "sent_today": counts.get("sent", 0),
            "dry_run_today": counts.get("dry_run", 0),
            "failed_today": counts.get("failed", 0),
        },
        "imap": {
            "configured": bool(s.imap_host and (s.imap_mode != "live" or (s.imap_user and s.imap_password))),
            "enabled": s.imap_enabled,
            "mode": s.imap_mode,
        },
        "email_intake": {
            "enabled": s.imap_enabled,
            "mode": s.imap_mode,
            "last_poll": _iso(poll["last_poll"]),
            "last_result": poll["last_result"],
        },
        "webhook": {"configured": bool(s.webhook_api_key)},
    }
