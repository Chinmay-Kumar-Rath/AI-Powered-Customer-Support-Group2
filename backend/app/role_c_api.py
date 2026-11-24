"""Role C HTTP endpoints: webhook intake, integrations status, Jira refresh, analytics, reports,
and the signed "Did this fix it?" links from the emails."""
import hmac
import html
import sys
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from . import analytics, reports, services, workflow
from .auth import admin_only, staff_only
from .database import get_db
from .models import EmailLog, JiraTicket, Ticket
from .schemas import TicketIn

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:  # so that the top-level `integrations` package can be imported
    sys.path.append(str(_ROOT))

from integrations import email_intake, jira, notifications, settings as integration_settings  # noqa: E402
from integrations.status import build_status  # noqa: E402

router = APIRouter()


# ------------------------------------------------------------------ webhook intake
class WebhookIn(BaseModel):
    subject: Optional[str] = None
    description: str
    email: EmailStr  # the requester
    name: Optional[str] = None
    department: str = "IT"


@router.post("/intake/webhook", status_code=201, tags=["intake"])
def webhook_intake(data: WebhookIn, x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
                   db: Session = Depends(get_db)):
    """Create a ticket from an external system. Send the key in the X-API-Key header (set WEBHOOK_API_KEY)."""
    expected = integration_settings.load().webhook_api_key
    if not expected:
        raise HTTPException(503, "Webhook intake is not configured. Set WEBHOOK_API_KEY on the server.")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Missing or invalid X-API-Key header.")
    ticket = services.create_and_classify(db, TicketIn(
        subject=data.subject, description=data.description, email=data.email, name=data.name,
        department=data.department, source="api"))
    return {"ticket_id": ticket.ticket_id, "ticket_code": ticket.ticket_code, "status": ticket.status}


# ------------------------------------------------------------------ "Did this fix it?" links (from the email)
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
        return HTMLResponse(f"<h3>Ticket {html.escape(ticket.ticket_code or '')} is no longer waiting for an answer."
                            "</h3>", status_code=409)
    message = ("Thank you - we are glad it is fixed. The ticket is closed." if verdict == "yes"
               else "Thank you - we have passed your request to a support engineer.")
    return HTMLResponse(f"<h3>{message}</h3>")


# ------------------------------------------------------------------ integrations status and jira
def _jira_row(row: JiraTicket) -> dict:
    return {"jira_id": row.jira_id, "ticket_id": row.ticket_id, "jira_issue_key": row.jira_issue_key,
            "jira_status": row.jira_status, "jira_url": row.jira_url,
            "last_updated": row.last_updated.isoformat() if row.last_updated else None}


@router.get("/integrations/status", tags=["integrations"])
def integrations_status(user=Depends(staff_only), db: Session = Depends(get_db)):
    return build_status(db)


@router.get("/integrations/jira/tickets", tags=["integrations"])
def list_jira_tickets(user=Depends(staff_only), db: Session = Depends(get_db)):
    rows = db.query(JiraTicket).order_by(JiraTicket.jira_id.desc()).limit(200).all()
    return [_jira_row(r) for r in rows]


@router.post("/integrations/jira/tickets/{ticket_id}/refresh", tags=["integrations"])
def refresh_jira_ticket(ticket_id: int, user=Depends(staff_only), db: Session = Depends(get_db)):
    """Push the ticket to Jira (create or update) and read the Jira status back into jira_tickets."""
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Ticket not found")
    try:
        row = jira.refresh_ticket(db, ticket_id)
    except jira.JiraError as exc:
        raise HTTPException(502, f"Jira sync failed: {exc}")
    if row is None:
        raise HTTPException(404, "Ticket not found")
    return _jira_row(row)


@router.get("/integrations/email-log", tags=["integrations"])
def list_email_log(limit: int = Query(50, ge=1, le=500), user=Depends(staff_only), db: Session = Depends(get_db)):
    rows = db.query(EmailLog).order_by(EmailLog.email_id.desc()).limit(limit).all()
    return [{"email_id": r.email_id, "ticket_id": r.ticket_id, "to_email": r.to_email, "template": r.template,
             "subject": r.subject, "status": r.status, "error": r.error,
             "sent_at": r.sent_at.isoformat() if r.sent_at else None} for r in rows]


@router.post("/integrations/email/poll", tags=["integrations"])
def poll_email_now(admin=Depends(admin_only), db: Session = Depends(get_db)):
    """Read unread mail now and turn it into tickets (the background poller does this on a timer)."""
    result = email_intake.poll_once(db)
    return {"fetched": result["fetched"], "created": result["created"], "errors": result["errors"]}


# ------------------------------------------------------------------ analytics
@router.get("/analytics/overview", tags=["analytics"])
def analytics_overview(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.overview(db)


@router.get("/analytics/trends", tags=["analytics"])
def analytics_trends(days: int = Query(30, ge=1, le=365), user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.trends(db, days)


@router.get("/analytics/categories", tags=["analytics"])
def analytics_categories(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.categories(db)


@router.get("/analytics/agent-performance", tags=["analytics"])
def analytics_agents(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.agent_performance(db)


@router.get("/analytics/escalations", tags=["analytics"])
def analytics_escalations(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.escalations(db)


@router.get("/analytics/satisfaction", tags=["analytics"])
def analytics_satisfaction(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.satisfaction(db)


@router.get("/analytics/recurring-issues", tags=["analytics"])
def analytics_recurring(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.recurring_issues(db)


@router.get("/reports/summary", tags=["analytics"])
def report_summary(format: Literal["csv", "pdf"] = "csv", user=Depends(staff_only), db: Session = Depends(get_db)):
    report = analytics.summary(db)
    if format == "pdf":
        return Response(reports.to_pdf(report), media_type="application/pdf",
                        headers={"Content-Disposition": 'attachment; filename="supportpilot-summary.pdf"'})
    return Response(reports.to_csv(report), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="supportpilot-summary.csv"'})


def start_background_jobs():
    """Called once at server start: the IMAP poller (only when IMAP_ENABLED=true)."""
    return email_intake.start_poller()
