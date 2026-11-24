"""Jira Cloud integration: create, update, transition and comment on issues.

    sync_ticket(db, ticket_id)  - push a SupportPilot ticket to Jira (create or update), store the result in
                                  the jira_tickets table. Called from hooks.py after every ticket change.
    refresh_ticket(db, ticket_id) - same as sync_ticket, plus it reads the remote status back (the
                                  "refresh" endpoint in role_c_api.py).

Two clients share one interface:
    CloudJiraClient - Jira Cloud REST API v3 (email + API token, HTTP basic auth).
    MockJiraClient  - in-memory issues, used when no credentials are configured and in the tests.
"""
import itertools
import threading
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from . import settings as cfg
from .settings import Settings

# SupportPilot status -> Jira status (names of the default Jira Software workflow)
STATUS_MAP = {
    "Open": "To Do",
    "Classified": "To Do",
    "Awaiting User": "To Do",
    "Escalated": "In Progress",
    "In Progress": "In Progress",
    "Resolved": "Done",
    "Closed": "Done",
}
_state = {"last_ok": None, "last_error": None, "last_error_at": None}
_state_lock = threading.Lock()


class JiraError(Exception):
    pass


def _now():
    return datetime.now(timezone.utc)


def _record_ok():
    with _state_lock:
        _state["last_ok"] = _now()


def _record_error(message: str):
    with _state_lock:
        _state["last_error"] = message[:500]
        _state["last_error_at"] = _now()


def health() -> dict:
    with _state_lock:
        return dict(_state)


# ------------------------------------------------------------------ clients
class MockJiraClient:
    """Keeps issues in memory. Behaves like Jira: new issues start in 'To Do'."""
    mode = "mock"
    TRANSITIONS = {"To Do", "In Progress", "Done"}

    def __init__(self, project_key: str = "SUP", base_url: str = "https://mock.atlassian.net"):
        self.project_key = project_key
        self.base_url = base_url
        self.issues = {}  # key -> dict(summary, description, status, comments=[])
        self._numbers = itertools.count(1)

    def _issue(self, key):
        if key not in self.issues:
            raise JiraError(f"Issue {key} does not exist")
        return self.issues[key]

    def create_issue(self, summary: str, description: str, labels=None) -> dict:
        key = f"{self.project_key}-{next(self._numbers)}"
        self.issues[key] = {"summary": summary, "description": description, "status": "To Do",
                            "labels": list(labels or []), "comments": []}
        return {"key": key, "url": f"{self.base_url}/browse/{key}"}

    def update_issue(self, key: str, summary: str = None, description: str = None):
        issue = self._issue(key)
        if summary is not None:
            issue["summary"] = summary
        if description is not None:
            issue["description"] = description

    def get_issue(self, key: str) -> dict:
        issue = self._issue(key)
        return {"key": key, "summary": issue["summary"], "status": issue["status"],
                "url": f"{self.base_url}/browse/{key}"}

    def transition_issue(self, key: str, status_name: str):
        if status_name not in self.TRANSITIONS:
            raise JiraError(f"No transition to '{status_name}' in this workflow")
        self._issue(key)["status"] = status_name

    def add_comment(self, key: str, text: str):
        self._issue(key)["comments"].append(text)


class CloudJiraClient:
    """Jira Cloud REST API v3. Authenticates with the account email and an API token."""
    mode = "live"

    def __init__(self, base_url: str, email: str, api_token: str, project_key: str, issue_type: str):
        self.base_url = base_url
        self.project_key = project_key
        self.issue_type = issue_type
        self._http = httpx.Client(base_url=f"{base_url}/rest/api/3", auth=(email, api_token),
                                  headers={"Accept": "application/json", "Content-Type": "application/json"},
                                  timeout=20)

    def _call(self, method: str, path: str, **kwargs):
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise JiraError(f"Jira is unreachable: {exc}") from exc
        if response.status_code >= 400:
            raise JiraError(f"Jira {method} {path} failed ({response.status_code}): {response.text[:300]}")
        return response.json() if response.content else {}

    @staticmethod
    def _adf(text: str) -> dict:
        """Atlassian Document Format: one paragraph per blank-line-separated block."""
        paragraphs = [p for p in (text or "").split("\n\n") if p.strip()] or [" "]
        return {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": p}]} for p in paragraphs]}

    def create_issue(self, summary: str, description: str, labels=None) -> dict:
        body = {"fields": {
            "project": {"key": self.project_key}, "summary": summary[:255],
            "description": self._adf(description), "issuetype": {"name": self.issue_type},
            "labels": [str(label).replace(" ", "-") for label in (labels or [])]}}
        key = self._call("POST", "/issue", json=body)["key"]
        return {"key": key, "url": f"{self.base_url}/browse/{key}"}

    def update_issue(self, key: str, summary: str = None, description: str = None):
        fields = {}
        if summary is not None:
            fields["summary"] = summary[:255]
        if description is not None:
            fields["description"] = self._adf(description)
        if fields:
            self._call("PUT", f"/issue/{key}", json={"fields": fields})

    def get_issue(self, key: str) -> dict:
        data = self._call("GET", f"/issue/{key}", params={"fields": "summary,status"})
        return {"key": key, "summary": data["fields"]["summary"], "status": data["fields"]["status"]["name"],
                "url": f"{self.base_url}/browse/{key}"}

    def transition_issue(self, key: str, status_name: str):
        transitions = self._call("GET", f"/issue/{key}/transitions").get("transitions", [])
        match = next((t for t in transitions if t["to"]["name"].lower() == status_name.lower()), None)
        if not match:
            available = ", ".join(t["to"]["name"] for t in transitions) or "none"
            raise JiraError(f"{key}: no transition to '{status_name}' (available: {available})")
        self._call("POST", f"/issue/{key}/transitions", json={"transition": {"id": match["id"]}})

    def add_comment(self, key: str, text: str):
        self._call("POST", f"/issue/{key}/comment", json={"body": self._adf(text)})


_client = None
_client_key = None


def get_client(settings: Settings = None):
    """One shared client per mode/config. Tests can call reset_client() to start fresh."""
    global _client, _client_key
    s = settings or cfg.load()
    key = (s.jira_mode, s.jira_base_url, s.jira_email, s.jira_project_key)
    if _client is None or _client_key != key:
        if s.jira_mode == "live":
            _client = CloudJiraClient(s.jira_base_url, s.jira_email, s.jira_api_token,
                                      s.jira_project_key, s.jira_issue_type)
        else:
            _client = MockJiraClient(s.jira_project_key)
        _client_key = key
    return _client


def reset_client():
    global _client, _client_key
    _client, _client_key = None, None


def is_connected(settings: Settings = None) -> bool:
    s = settings or cfg.load()
    if s.jira_mode != "live":
        return False
    h = health()
    return h["last_ok"] is not None and (h["last_error_at"] is None or h["last_ok"] >= h["last_error_at"])


# ------------------------------------------------------------------ sync
def _text_of(ticket, latest_escalation=None) -> str:
    lines = [
        f"SupportPilot ticket {ticket.ticket_code}",
        f"Requester: {ticket.user.email if ticket.user else '-'}",
        f"Category: {ticket.category or '-'} / Severity: {ticket.severity or '-'} / Priority: {ticket.priority or '-'}",
        f"Source: {ticket.source}",
    ]
    if latest_escalation is not None:
        lines.append(f"Team: {latest_escalation.assigned_team or '-'}")
        lines.append(f"Assignee: {latest_escalation.assignee_name or 'unassigned'}")
        if latest_escalation.escalation_reason:
            lines.append(f"Escalation reason: {latest_escalation.escalation_reason}")
    lines.append("")
    lines.append(ticket.description or "")
    return "\n".join(lines)


def _summary_of(ticket) -> str:
    return f"[{ticket.ticket_code}] {ticket.subject or 'Support request'}"


def sync_ticket(db: Session, ticket_id: int, client=None):
    """Make Jira match the ticket: create the issue once, then keep summary, description and status in step.

    Returns the jira_tickets row (or None if the ticket does not exist). Errors are re-raised after being
    recorded, so the caller (hooks.py prints them; the refresh endpoint returns them) can report them.
    """
    from app.models import JiraTicket, Ticket, Escalation  # imported here: keeps this module import-light

    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        return None
    client = client or get_client()
    row = (db.query(JiraTicket).filter(JiraTicket.ticket_id == ticket_id)
           .order_by(JiraTicket.jira_id.desc()).first())
    target = STATUS_MAP.get(ticket.status, "To Do")
    escalation = (db.query(Escalation).filter(Escalation.ticket_id == ticket_id)
                  .order_by(Escalation.escalation_id.desc()).first())
    try:
        if row is None or not row.jira_issue_key:
            issue = client.create_issue(_summary_of(ticket), _text_of(ticket, escalation),
                                        labels=["supportpilot", ticket.category or "uncategorised"])
            if row is None:
                row = JiraTicket(ticket_id=ticket_id)
                db.add(row)
            row.jira_issue_key, row.jira_url = issue["key"], issue["url"]
            key = issue["key"]
            remote_status = "To Do"
            created = True
        else:
            key = row.jira_issue_key
            client.update_issue(key, summary=_summary_of(ticket), description=_text_of(ticket, escalation))
            remote_status = client.get_issue(key)["status"]  # pull: what Jira says right now
            created = False

        if remote_status != target:
            client.transition_issue(key, target)
            client.add_comment(key, f"SupportPilot: ticket status is now '{ticket.status}' "
                                    f"(Jira: {target}).")
        elif created:
            client.add_comment(key, f"SupportPilot: ticket {ticket.ticket_code} created ({ticket.status}).")
        row.jira_status = target  # after the checks above, Jira is at the target status
        row.last_updated = _now()
        db.commit()
        _record_ok()
        return row
    except Exception as exc:
        db.rollback()
        _record_error(str(exc))
        raise


def refresh_ticket(db: Session, ticket_id: int, client=None):
    """Re-read the Jira issue and bring both sides in line (the refresh endpoint calls this)."""
    return sync_ticket(db, ticket_id, client=client)
