"""Database tables (the PDF schema + the extra columns we agreed on)."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100))
    role = Column(String(50), default="employee")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    tickets = relationship("Ticket", back_populates="user")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True)
    ticket_code = Column(String(20), unique=True, index=True)  # e.g. T-2026-0001
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    subject = Column(String(255))
    description = Column(Text, nullable=False)
    department = Column(String(100))
    source = Column(String(20), default="web")  # web / email / api

    category = Column(String(50))
    sub_category = Column(String(80))
    category_confidence = Column(Float)
    severity = Column(String(20))
    severity_confidence = Column(Float)
    priority = Column(String(5))

    status = Column(String(20), default="Open", index=True)
    processing_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="tickets")

    @property
    def requester_email(self):
        return self.user.email if self.user else None

    logs = relationship("ActivityLog", back_populates="ticket", order_by="ActivityLog.log_id")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    log_id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.ticket_id"), nullable=False, index=True)
    action = Column(String(100))
    performed_by = Column(String(100))
    timestamp = Column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="logs")
