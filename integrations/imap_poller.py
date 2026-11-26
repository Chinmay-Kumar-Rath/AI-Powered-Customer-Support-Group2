"""Email intake via IMAP poller: turns UNSEEN messages into tickets with source='email'.

Features:
- Connects via imaplib to fetch UNSEEN emails
- Deduplicates using Message-ID header so the same email never creates duplicate tickets
- Parses sender email, subject, and plain-text body
- Marks processed emails as \\Seen
- Safe start/stop background loop hook, disabled automatically if IMAP_HOST is empty or IMAP_ENABLED is false
"""
import email
import imaplib
import re
import threading
import time
from email.policy import default as default_policy
from email.utils import parseaddr
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from . import settings as cfg

_state = {"last_poll": None, "last_result": None, "running": False}
_state_lock = threading.Lock()
_QUOTE_MARKERS = re.compile(r"^(On .+wrote:|-{2,}\s*Original Message|From: .+@.+)$", re.IGNORECASE)
_BOUNCE_PATTERNS = re.compile(
    r"(mailer-daemon|postmaster|no-?reply|donotreply|notifications?@)",
    re.IGNORECASE,
)
_BOUNCE_SUBJECT_PREFIXES = (
    "delivery status notification",
    "undelivered mail",
    "mail delivery subsystem",
    "failure notice",
    "returned mail",
    "auto-reply",
    "automatic reply",
)


def is_bounce_or_automated(raw: bytes, parsed: dict) -> bool:
    """Detect automated bounce messages, delivery status notifications, and noreply addresses

    to avoid recursive notification/ticket creation loops.
    """
    sender = (parsed.get("email") or "").lower()
    if _BOUNCE_PATTERNS.search(sender):
        return True

    subject = (parsed.get("subject") or "").lower()
    if any(subject.startswith(p) for p in _BOUNCE_SUBJECT_PREFIXES):
        return True

    try:
        msg = email.message_from_bytes(raw, policy=default_policy)
        auto_submitted = (msg.get("Auto-Submitted") or "").lower()
        if auto_submitted in ("auto-generated", "auto-replied", "auto-notified"):
            return True
        precedence = (msg.get("Precedence") or "").lower()
        if precedence in ("bulk", "junk", "auto_reply"):
            return True
    except Exception:
        pass

    return False


# Deduplication tracking for Message-IDs
_seen_message_ids = set()
_seen_lock = threading.Lock()
_stop_event = threading.Event()
_poller_thread: Optional[threading.Thread] = None


class LiveImapSource:
    def __init__(self, s: cfg.Settings):
        self.s = s

    def fetch_unseen(self) -> list:
        """Returns [(uid, raw_bytes)] for unread messages."""
        if not self.s.imap_host:
            return []
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
        if not self.s.imap_host:
            return
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
    import sys
    s = s or cfg.load()
    if s.imap_mode == "live":
        return LiveImapSource(s)
    intake_mod = sys.modules.get("integrations.email_intake")
    if intake_mod is not None and hasattr(intake_mod, "_mock_source"):
        return intake_mod._mock_source
    return _mock_source


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
    message_id = str(message.get("Message-ID", "")).strip() or None
    return {
        "email": sender_addr.lower(),
        "name": sender_name or None,
        "subject": " ".join(str(message.get("Subject", "")).split())[:255] or None,
        "description": _body_text(message) or "(no text in the email body)",
        "message_id": message_id,
    }


def poll_once(db: Session, source=None, settings: cfg.Settings = None) -> dict:
    """Create tickets from unread mail. Deduplicates via Message-ID. Returns summary."""
    from app.schemas import TicketIn
    from app import services

    s = settings or cfg.load()
    source = source or get_source(s)
    result = {"fetched": 0, "created": [], "skipped": 0, "errors": []}
    for uid, raw in source.fetch_unseen():
        result["fetched"] += 1
        try:
            parsed = parse_message(raw)
            if is_bounce_or_automated(raw, parsed):
                result["skipped"] += 1
                source.mark_seen(uid)
                continue

            msg_id = parsed.get("message_id")
            if msg_id:
                with _seen_lock:
                    if msg_id in _seen_message_ids:
                        result["skipped"] += 1
                        source.mark_seen(uid)
                        continue
                    _seen_message_ids.add(msg_id)

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
        _state["last_result"] = {
            "fetched": result["fetched"],
            "created": len(result["created"]),
            "skipped": result["skipped"],
            "errors": len(result["errors"]),
        }
    return result


def status() -> dict:
    with _state_lock:
        return dict(_state)


def start_poller(settings: cfg.Settings = None) -> Optional[threading.Thread]:
    """Start the background IMAP poller thread.

    Disabled automatically if IMAP_HOST is empty or IMAP_ENABLED is false.
    """
    global _poller_thread
    from app.database import SessionLocal

    s = settings or cfg.load()
    if not s.imap_enabled or not s.imap_host:
        return None
    with _state_lock:
        if _state["running"]:
            return _poller_thread
        _state["running"] = True
        _stop_event.clear()

    def loop():
        while not _stop_event.is_set():
            try:
                with SessionLocal() as db:
                    poll_once(db, settings=cfg.load())
            except Exception as exc:
                print(f"[email intake] poll failed: {exc}")
            # Sleep in small slices so stopping is prompt
            poll_interval = max(15, cfg.load().imap_poll_seconds)
            for _ in range(poll_interval):
                if _stop_event.is_set():
                    break
                time.sleep(1)

    _poller_thread = threading.Thread(target=loop, name="imap-poller", daemon=True)
    _poller_thread.start()
    return _poller_thread


def stop_poller():
    """Safely stop the poller background loop."""
    global _poller_thread
    with _state_lock:
        _state["running"] = False
        _stop_event.set()
    if _poller_thread and _poller_thread.is_alive():
        _poller_thread.join(timeout=3)
    _poller_thread = None
