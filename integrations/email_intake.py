"""Email intake: an IMAP poller that turns each new message into a ticket with source='email'.

    poll_once(db, source)  - read UNSEEN mail, create one ticket per message, mark it as read.
    start_poller()         - background thread that calls poll_once every IMAP_POLL_SECONDS (IMAP_ENABLED=true).

A message only gets \\Seen after its ticket is saved, so a crash or a bad message is retried, never lost.
IMAP_MODE=mock (default when no IMAP_USER/IMAP_PASSWORD) uses MockImapSource, an in-memory inbox.
"""
import email
import imaplib
import re
import threading
import time
from email.policy import default as default_policy
from email.utils import parseaddr
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import settings as cfg

_state = {"last_poll": None, "last_result": None, "running": False}
_state_lock = threading.Lock()
_QUOTE_MARKERS = re.compile(r"^(On .+wrote:|-{2,}\s*Original Message|From: .+@.+)$", re.IGNORECASE)


class LiveImapSource:
    def __init__(self, s: cfg.Settings):
        self.s = s

    def fetch_unseen(self) -> list:
        """Returns [(uid, raw_bytes)] for unread messages."""
        conn = imaplib.IMAP4_SSL(self.s.imap_host, self.s.imap_port)
        try:
            conn.login(self.s.imap_user, self.s.imap_password)
            conn.select(self.s.imap_folder)
            _, data = conn.uid("search", None, "UNSEEN")
            uids = (data[0] or b"").split()
            messages = []
            for uid in uids:
                _, parts = conn.uid("fetch", uid, "(RFC822)")
                raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
                if raw is not None:
                    messages.append((uid.decode(), raw))
            return messages
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def mark_seen(self, uid: str):
        conn = imaplib.IMAP4_SSL(self.s.imap_host, self.s.imap_port)
        try:
            conn.login(self.s.imap_user, self.s.imap_password)
            conn.select(self.s.imap_folder)
            conn.uid("store", uid, "+FLAGS", "\\Seen")
        finally:
            try:
                conn.logout()
            except Exception:
                pass


class MockImapSource:
    """In-memory inbox. add() a raw RFC822 message to simulate a new email."""

    def __init__(self):
        self.inbox = {}  # uid -> raw bytes (unread)
        self._counter = 0

    def add(self, raw: bytes) -> str:
        self._counter += 1
        uid = str(self._counter)
        self.inbox[uid] = raw
        return uid

    def fetch_unseen(self) -> list:
        return list(self.inbox.items())

    def mark_seen(self, uid: str):
        self.inbox.pop(uid, None)


_mock_source = MockImapSource()


def get_source(s: cfg.Settings = None):
    s = s or cfg.load()
    return LiveImapSource(s) if s.imap_mode == "live" else _mock_source


def _body_text(message) -> str:
    if message.is_multipart():
        part = message.get_body(preferencelist=("plain",))
        text = part.get_content() if part is not None else ""
    else:
        text = message.get_content() if message.get_content_maintype() == "text" else ""
    kept = []
    for line in (text or "").splitlines():
        if _QUOTE_MARKERS.match(line.strip()) or line.lstrip().startswith(">"):
            break  # everything after the first quoted reply is history, not the new request
        kept.append(line)
    return "\n".join(kept).strip()


def parse_message(raw: bytes) -> dict:
    message = email.message_from_bytes(raw, policy=default_policy)
    sender_name, sender_addr = parseaddr(str(message.get("From", "")))
    if not sender_addr or "@" not in sender_addr:
        raise ValueError("message has no usable From address")
    return {
        "email": sender_addr.lower(),
        "name": sender_name or None,
        "subject": " ".join(str(message.get("Subject", "")).split())[:255] or None,
        "description": _body_text(message) or "(no text in the email body)",
    }


def poll_once(db: Session, source=None, settings: cfg.Settings = None) -> dict:
    """Create tickets from unread mail. Returns a summary (also kept for the status endpoint)."""
    from app.schemas import TicketIn
    from app import services

    s = settings or cfg.load()
    source = source or get_source(s)
    result = {"fetched": 0, "created": [], "errors": []}
    for uid, raw in source.fetch_unseen():
        result["fetched"] += 1
        try:
            parsed = parse_message(raw)
            ticket = services.create_and_classify(db, TicketIn(
                subject=parsed["subject"], description=parsed["description"], email=parsed["email"],
                name=parsed["name"], department="IT", source="email"))
            result["created"].append(ticket.ticket_code)
            source.mark_seen(uid)
        except Exception as exc:
            db.rollback()
            result["errors"].append(f"message {uid}: {exc}"[:300])
    with _state_lock:
        _state["last_poll"] = datetime.now(timezone.utc)
        _state["last_result"] = {"fetched": result["fetched"], "created": len(result["created"]),
                                 "errors": len(result["errors"])}
    return result


def status() -> dict:
    with _state_lock:
        return dict(_state)


def start_poller(settings: cfg.Settings = None):
    """Start the background poller once. Does nothing unless IMAP_ENABLED=true."""
    from app.database import SessionLocal

    s = settings or cfg.load()
    if not s.imap_enabled:
        return None
    with _state_lock:
        if _state["running"]:
            return None
        _state["running"] = True

    def loop():
        while True:
            try:
                with SessionLocal() as db:
                    poll_once(db, settings=cfg.load())
            except Exception as exc:
                print(f"[email intake] poll failed: {exc}")
            time.sleep(max(15, cfg.load().imap_poll_seconds))

    thread = threading.Thread(target=loop, name="imap-poller", daemon=True)
    thread.start()
    return thread
