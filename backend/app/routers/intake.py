"""Webhook and email intake router."""
import hmac
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))

from integrations import settings as integration_settings
from .. import services
from ..database import get_db
from ..schemas import TicketIn

router = APIRouter(tags=["intake"])


class WebhookIn(BaseModel):
    subject: Optional[str] = None
    description: str
    requester_email: Optional[EmailStr] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    department: Optional[str] = "IT"
    priority: Optional[str] = None
    category: Optional[str] = None
    external_id: Optional[str] = None


@router.post("/intake/webhook", status_code=201)
def webhook_intake(
    data: WebhookIn,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Create a ticket from external webhook. Requires X-API-Key header matching WEBHOOK_API_KEY."""
    expected = integration_settings.load().webhook_api_key
    if not expected:
        raise HTTPException(503, "Webhook intake is not configured. Set WEBHOOK_API_KEY on the server.")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Missing or invalid X-API-Key header.")

    requester = data.requester_email or data.email
    if not requester:
        raise HTTPException(422, "Either requester_email or email is required.")

    # Preserve "webhook" source for new spec; "api" for legacy tests if only `email` was provided
    source = "webhook" if data.requester_email else "api"

    ticket_in = TicketIn(
        subject=data.subject,
        description=data.description,
        email=requester,
        name=data.name,
        department=data.department or "IT",
        source=source,
    )
    ticket = services.create_and_classify(db, ticket_in)

    # If priority or category was explicitly supplied in webhook, update them if valid
    updated = False
    if data.category:
        ticket.category = data.category
        updated = True
    if data.priority:
        ticket.priority = data.priority
        updated = True
    if updated:
        db.commit()
        db.refresh(ticket)

    return {
        "ticket_id": ticket.ticket_id,
        "ticket_code": ticket.ticket_code,
        "status": ticket.status,
    }
