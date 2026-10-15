"""Shapes of the data going in and out of the API (validation happens here)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class TicketIn(BaseModel):
    subject: Optional[str] = None          # may be empty - description alone is enough
    description: str
    email: EmailStr
    department: str = "IT"
    name: Optional[str] = None
    source: Literal["web", "email", "api"] = "web"

    @field_validator("subject", "name", "department", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("description", mode="before")
    @classmethod
    def _clean_description(cls, v):
        v = v.strip() if isinstance(v, str) else v
        if not v or len(v) < 5:
            raise ValueError("description must be at least 5 characters")
        return v


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: int
    ticket_code: Optional[str]
    requester_email: Optional[str]
    subject: Optional[str]
    description: str
    department: Optional[str]
    source: Optional[str]
    category: Optional[str]
    sub_category: Optional[str]
    category_confidence: Optional[float]
    severity: Optional[str]
    severity_confidence: Optional[float]
    priority: Optional[str]
    status: str
    processing_ms: Optional[float]
    created_at: datetime


class StatusUpdate(BaseModel):
    status: str
    performed_by: str = "system"


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    action: str
    performed_by: Optional[str]
    timestamp: datetime
