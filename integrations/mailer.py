"""Outbound email transport. Two modes, picked by EMAIL_MODE:

    dry_run (default) - nothing leaves the server. The message is printed and kept in DryRunMailer.outbox,
                        and email_log records status 'dry_run'.
    smtp              - SMTP with STARTTLS. For Gmail: smtp.gmail.com:587 + a dedicated Google App Password
                        (SMTP_USER = the Gmail address, SMTP_PASSWORD = the 16-character app password).
"""
import smtplib
import ssl
import threading
from email.message import EmailMessage

from . import settings as cfg


class MailError(Exception):
    pass


class DryRunMailer:
    mode = "dry_run"

    def __init__(self):
        self.outbox = []  # (to, subject, body) - inspected by the tests
        self.html_outbox = []  # (to, subject, html_body)
        self._lock = threading.Lock()

    def send(self, to: str, subject: str, body: str, sender: str, html_body: str = None) -> str:
        with self._lock:
            self.outbox.append((to, subject, body))
            if html_body:
                self.html_outbox.append((to, subject, html_body))
        print(f"[email dry-run] to={to} subject={subject!r}")
        return "dry_run"


class SmtpMailer:
    mode = "smtp"

    def __init__(self, settings: cfg.Settings):
        self.s = settings

    def send(self, to: str, subject: str, body: str, sender: str, html_body: str = None) -> str:
        if not (self.s.smtp_user and self.s.smtp_password):
            raise MailError("SMTP_USER and SMTP_PASSWORD must be set when EMAIL_MODE=smtp")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")
        try:
            with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(self.s.smtp_user, self.s.smtp_password)
                server.send_message(msg)
        except (smtplib.SMTPException, OSError) as exc:
            raise MailError(f"SMTP send failed: {exc}") from exc
        return "sent"


_mailer = None
_mailer_mode = None


def get_mailer(settings: cfg.Settings = None):
    global _mailer, _mailer_mode
    s = settings or cfg.load()
    if _mailer is None or _mailer_mode != s.email_mode:
        _mailer = SmtpMailer(s) if s.email_mode == "smtp" else DryRunMailer()
        _mailer_mode = s.email_mode
    return _mailer


def reset_mailer():
    global _mailer, _mailer_mode
    _mailer, _mailer_mode = None, None
