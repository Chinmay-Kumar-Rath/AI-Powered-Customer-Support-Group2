import csv
import io
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import services
from .database import Base, engine, get_db
from .models import ActivityLog, Ticket
from .schemas import LogOut, StatusUpdate, TicketIn, TicketOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(engine)  # creates the 3 tables if they don't exist
    except OperationalError as exc:
        print("\n*** Could not connect to PostgreSQL. ***")
        print("Is the database running?  Try:  docker compose up -d   (see README)\n")
        raise exc
    yield


app = FastAPI(
    title="SupportPilot API",
    description="Milestone 1: ticket intake, AI classification, lifecycle tracking.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketIn, db: Session = Depends(get_db)):
    return services.create_and_classify(db, data)


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if category:
        q = q.filter(Ticket.category == category)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if severity:
        q = q.filter(Ticket.severity == severity)
    return q.order_by(Ticket.ticket_id.desc()).offset(offset).limit(limit).all()


@app.post("/tickets/bulk")
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV with columns: subject, description, email (optional: department, name)."""
    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or "description" not in reader.fieldnames or "email" not in reader.fieldnames:
        raise HTTPException(400, "CSV must have at least the columns: description, email (subject optional)")

    created, errors = 0, []
    for line_no, row in enumerate(reader, start=2):  # line 1 is the header
        if created + len(errors) >= 5000:
            errors.append({"row": line_no, "error": "stopped: limit of 5000 rows per upload"})
            break
        try:
            data = TicketIn(
                subject=row.get("subject") or None,
                description=row.get("description") or "",
                email=(row.get("email") or "").strip(),
                department=(row.get("department") or "IT"),
                name=row.get("name") or None,
                source="api",
            )
            services.create_and_classify(db, data)
            created += 1
        except ValidationError as exc:
            errors.append({"row": line_no, "error": exc.errors()[0]["msg"]})
    return {"created": created, "failed": len(errors), "errors": errors[:20]}


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@app.get("/tickets/{ticket_id}/history", response_model=list[LogOut])
def ticket_history(ticket_id: int, db: Session = Depends(get_db)):
    if not db.get(Ticket, ticket_id):
        raise HTTPException(404, "Ticket not found")
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.ticket_id == ticket_id)
        .order_by(ActivityLog.log_id)
        .all()
    )


@app.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    try:
        return services.change_status(db, ticket, body.status, body.performed_by)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    return services.build_stats(db)
