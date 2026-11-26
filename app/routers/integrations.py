"""Jira and Email Integrations router."""
import html
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))

from integrations import imap_poller, jira, notifications
from integrations.status import build_status
from .. import workflow
from ..auth import admin_only, staff_only
from ..database import get_db
from ..models import EmailLog, JiraTicket, Ticket

router = APIRouter(tags=["integrations"])


def _jira_row(row: JiraTicket) -> dict:
    return {
        "jira_id": row.jira_id,
        "ticket_id": row.ticket_id,
        "jira_issue_key": row.jira_issue_key,
        "jira_key": row.jira_issue_key,
        "jira_status": row.jira_status,
        "status": row.jira_status,
        "jira_url": row.jira_url,
        "last_updated": row.last_updated.isoformat() if row.last_updated else None,
        "last_synced_at": row.last_updated.isoformat() if row.last_updated else None,
    }


# ------------------------------------------------------------------ Jira Endpoints
@router.get("/integrations/jira/tickets")
def list_jira_tickets(user=Depends(staff_only), db: Session = Depends(get_db)):
    rows = db.query(JiraTicket).order_by(JiraTicket.jira_id.desc()).limit(200).all()
    return [_jira_row(r) for r in rows]


@router.post("/integrations/jira/refresh")
def refresh_all_jira_tickets(user=Depends(staff_only), db: Session = Depends(get_db)):
    """Pull latest Jira status for all synced tickets."""
    try:
        updated = jira.refresh_all_tickets(db)
    except jira.JiraError as exc:
        raise HTTPException(502, f"Jira refresh failed: {exc}")
    return [_jira_row(r) for r in updated]


@router.post("/integrations/jira/refresh/{ticket_id}")
@router.post("/integrations/jira/tickets/{ticket_id}/refresh")
def refresh_jira_ticket(ticket_id: int, user=Depends(staff_only), db: Session = Depends(get_db)):
    """Pull latest Jira issue status and update jira_tickets."""
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Ticket not found")
    try:
        row = jira.refresh_ticket(db, ticket_id)
    except jira.JiraError as exc:
        raise HTTPException(502, f"Jira sync failed: {exc}")
    if row is None:
        raise HTTPException(404, "Ticket not found")
    return _jira_row(row)


# ------------------------------------------------------------------ Status & Logs
@router.get("/integrations/status")
def integrations_status(user=Depends(staff_only), db: Session = Depends(get_db)):
    return build_status(db)


@router.get("/integrations/email-log")
def list_email_log(limit: int = Query(50, ge=1, le=500), user=Depends(staff_only), db: Session = Depends(get_db)):
    rows = db.query(EmailLog).order_by(EmailLog.email_id.desc()).limit(limit).all()
    return [{
        "email_id": r.email_id,
        "ticket_id": r.ticket_id,
        "to_email": r.to_email,
        "template": r.template,
        "subject": r.subject,
        "status": r.status,
        "error": r.error,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
    } for r in rows]


@router.post("/integrations/email/poll")
def poll_email_now(admin=Depends(admin_only), db: Session = Depends(get_db)):
    """Read unread mail now via IMAP and turn it into tickets."""
    result = imap_poller.poll_once(db)
    return {"fetched": result["fetched"], "created": result["created"], "errors": result["errors"]}


# ------------------------------------------------------------------ Email Feedback Links
@router.get("/feedback/{ticket_id}", response_class=HTMLResponse, tags=["feedback"])
def feedback_from_email(ticket_id: int, verdict: str, exp: int, sig: str, db: Session = Depends(get_db)):
    if not notifications.verify_feedback_link(ticket_id, verdict, exp, sig):
        return HTMLResponse("<h3>This link is invalid or has expired.</h3>", status_code=403)
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.user is None:
        return HTMLResponse("<h3>Ticket not found.</h3>", status_code=404)
    try:
        workflow.submit_feedback(db, ticket, ticket.user, is_resolved=(verdict == "yes"))
    except ValueError:
        return HTMLResponse(
            f"<h3>Ticket {html.escape(ticket.ticket_code or '')} is no longer waiting for an answer.</h3>",
            status_code=409,
        )
    message = (
        "Thank you - we are glad it is fixed. The ticket is closed."
        if verdict == "yes"
        else "Thank you - we have passed your request to a support engineer."
    )
    return HTMLResponse(f"<h3>{message}</h3>")
