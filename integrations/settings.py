"""Role C settings, read from the environment (a .env file in the repo root is loaded automatically).

Nothing here is required: without credentials the integrations run in mock / dry-run mode.
"""
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

try:  # optional, same as backend/app/config.py
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    # Jira Cloud. JIRA_MODE: "live" | "mock" (default: live when base URL, email and token are all set)
    jira_mode: str
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str
    jira_issue_type: str
    # Outbound email. EMAIL_MODE: "smtp" | "dry_run" (default dry_run: logged, never sent)
    email_mode: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str  # a Gmail App Password, never the account password
    email_from: str
    # Inbound email (IMAP poller). IMAP_MODE: "live" | "mock"
    imap_enabled: bool
    imap_mode: str
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str
    imap_folder: str
    imap_poll_seconds: int
    # Webhook intake and public links (the "Did this fix it?" buttons point at PUBLIC_API_URL / FRONTEND_URL)
    webhook_api_key: str
    public_api_url: str
    frontend_url: str


def load() -> Settings:
    jira_url = (_get("JIRA_URL") or _get("JIRA_BASE_URL")).rstrip("/")
    jira_email = _get("JIRA_EMAIL")
    jira_token = _get("JIRA_API_TOKEN")
    jira_mode = _get("JIRA_MODE", "").lower()
    if jira_mode not in ("live", "mock"):
        jira_mode = "live" if (jira_url and jira_email and jira_token) else "mock"

    imap_host = _get("IMAP_HOST", "imap.gmail.com")
    imap_user = _get("IMAP_USER")
    imap_password = _get("IMAP_PASSWORD")
    imap_mode = _get("IMAP_MODE", "").lower()
    if imap_mode not in ("live", "mock"):
        imap_mode = "live" if (imap_user and imap_password) else "mock"

    imap_interval = _get("IMAP_POLL_INTERVAL") or _get("IMAP_POLL_SECONDS", "60")

    return Settings(
        jira_mode=jira_mode,
        jira_base_url=jira_url,
        jira_email=jira_email,
        jira_api_token=jira_token,
        jira_project_key=_get("JIRA_PROJECT_KEY", "SUP"),
        jira_issue_type=_get("JIRA_ISSUE_TYPE", "Task"),
        email_mode="smtp" if _get("EMAIL_MODE", "dry_run").lower() == "smtp" else "dry_run",
        smtp_host=_get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(_get("SMTP_PORT", "587") or 587),
        smtp_user=_get("SMTP_USER"),
        smtp_password=_get("SMTP_PASSWORD"),
        email_from=_get("EMAIL_FROM") or _get("SMTP_USER") or "support@supportpilot.dev",
        imap_enabled=_flag("IMAP_ENABLED", False),
        imap_mode=imap_mode,
        imap_host=imap_host,
        imap_port=int(_get("IMAP_PORT", "993") or 993),
        imap_user=imap_user,
        imap_password=imap_password,
        imap_folder=_get("IMAP_FOLDER", "INBOX"),
        imap_poll_seconds=int(imap_interval or 60),
        webhook_api_key=_get("WEBHOOK_API_KEY"),
        public_api_url=_get("PUBLIC_API_URL", "http://localhost:8000").rstrip("/"),
        frontend_url=_get("FRONTEND_URL", "http://localhost:5173").rstrip("/"),
    )
