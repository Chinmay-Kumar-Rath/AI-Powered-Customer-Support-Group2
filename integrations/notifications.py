"""Turns ticket events into emails and logs every one in email_log.

hooks.py calls notify(event, ticket_id, **context) in a background thread.
Recipient: the ticket requester (the person who reported the problem).
Feedback links ("Did this fix it?") are signed, expire after 7 days and need no login.
"""
import hashlib
import hmac
import time

from app import config as app_config
from app.database import SessionLocal
from app.models import EmailLog, Escalation, Ticket, TicketResponse

from . import mailer, settings as cfg, templates

session_factory = SessionLocal  # tests replace this with an in-memory database

EVENT_TEMPLATES = {
    "ticket_received": "ticket_received",
    "ai_resolution_sent": "ai_resolution",
    "escalated": "escalated",
    "assigned": "assigned",
    "status_changed": "status_change",
    "resolved": "resolved",
    "closed": "closed",
}
FEEDBACK_LINK_DAYS = 7


# ------------------------------------------------------------------ feedback links
def _signature(ticket_id: int, verdict: str, expires: int) -> str:
    message = f"{ticket_id}:{verdict}:{expires}".encode()
    return hmac.new(app_config.JWT_SECRET.encode(), message, hashlib.sha256).hexdigest()


def feedback_link(ticket_id: int, verdict: str, settings: cfg.Settings = None) -> str:
    s = settings or cfg.load()
    expires = int(time.time()) + FEEDBACK_LINK_DAYS * 86400
    sig = _signature(ticket_id, verdict, expires)
    return f"{s.public_api_url}/feedback/{ticket_id}?verdict={verdict}&exp={expires}&sig={sig}"


def verify_feedback_link(ticket_id: int, verdict: str, expires: int, sig: str) -> bool:
    if verdict not in ("yes", "no") or int(time.time()) > expires:
        return False
    return hmac.compare_digest(_signature(ticket_id, verdict, expires), sig)


# ------------------------------------------------------------------ building the email
def _greeting(ticket: Ticket) -> str:
    user = ticket.user
    return (user.name or user.email) if user else "there"


def _base_data(ticket: Ticket) -> dict:
    return {"ticket_code": ticket.ticket_code, "subject": ticket.subject or "Support request",
            "greeting": _greeting(ticket), "status": ticket.status}


def _data_for(db, event: str, ticket: Ticket, context: dict, settings: cfg.Settings) -> dict:
    data = _base_data(ticket)
    if event == "ticket_received":
        pass
    elif event == "ai_resolution_sent":
        response = (db.query(TicketResponse).filter(TicketResponse.ticket_id == ticket.ticket_id)
                    .order_by(TicketResponse.response_id.desc()).first())
        steps = (response.steps or []) if response else []
        data.update(
            response_text=(response.generated_response if response else "") or "",
            steps_block=("Steps:\n" + "\n".join(f"  {i}. {s}" for i, s in enumerate(steps, 1)) + "\n\n")
            if steps else "",
            yes_link=feedback_link(ticket.ticket_id, "yes", settings),
            no_link=feedback_link(ticket.ticket_id, "no", settings),
        )
    elif event == "escalated":
        esc = (db.query(Escalation).filter(Escalation.ticket_id == ticket.ticket_id)
               .order_by(Escalation.escalation_id.desc()).first())
        due = context.get("due_at") or (esc.due_at.isoformat() if esc and esc.due_at else None)
        data.update(team=context.get("team") or (esc.assigned_team if esc else "support team"),
                    reason=context.get("reason") or "",
                    due_line=f"We aim to respond by {due}.\n" if due else "")
    elif event == "assigned":
        esc = (db.query(Escalation).filter(Escalation.ticket_id == ticket.ticket_id)
               .order_by(Escalation.escalation_id.desc()).first())
        data.update(assignee_name=context.get("assignee_name") or "a support engineer",
                    team=context.get("team") or (esc.assigned_team if esc else "support team"))
    elif event == "status_changed":
        data.update(old_status=context.get("old_status") or "",
                    new_status=context.get("new_status") or ticket.status,
                    message_block=(f"\nMessage from the support team:\n{context['message']}\n"
                                   if context.get("message") else ""))
        if context.get("assignee_name"):
            data["message_block"] += f"\nAn engineer, {context['assignee_name']}, is now working on it.\n"
    elif event == "resolved":
        notes = context.get("notes") or ""
        data["notes_block"] = f"\nWhat was done:\n{notes}\n" if notes else ""
    return data


def _send_and_log(db, ticket: Ticket, to_email: str, template: str, subject: str, body: str, settings):
    status, error = "failed", None
    try:
        status = mailer.get_mailer(settings).send(to_email, subject, body, settings.email_from)
    except Exception as exc:  # a failed email must never break the ticket flow
        error = str(exc)[:1000]
        print(f"[email] {template} to {to_email} failed: {error}")
    db.add(EmailLog(ticket_id=ticket.ticket_id, to_email=to_email, template=template,
                    subject=subject[:255], status=status, error=error))
    db.commit()
    return status


def notify(event: str, ticket_id: int, **context):
    """Build and send the email for one event, then log it. Runs in a background thread (hooks.py)."""
    template = EVENT_TEMPLATES.get(event)
    if template is None:
        return None
    settings = cfg.load()
    with session_factory() as db:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None or ticket.user is None or not ticket.user.email:
            return None
        data = _data_for(db, event, ticket, context, settings)
        subject, body = templates.render(template, data)
        return _send_and_log(db, ticket, ticket.user.email, template, subject, body, settings)
