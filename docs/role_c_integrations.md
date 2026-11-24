# Role C: integrations and analytics

Code: `integrations/` (Jira, email, IMAP intake, status) and `backend/app/analytics.py`, `reports.py`,
`role_c_api.py` (HTTP endpoints). `backend/app/hooks.py` already calls these modules on every ticket event.

## Modes (nothing needs credentials to run)

| Integration | Mock / dry-run mode | Live mode |
|---|---|---|
| Jira | `JIRA_MODE=mock` (default without credentials): issues kept in memory | Jira Cloud REST v3 with email + API token |
| Email | `EMAIL_MODE=dry_run` (default): message is logged to `email_log` with status `dry_run`, never sent | `EMAIL_MODE=smtp`: Gmail SMTP on 587 with STARTTLS |
| IMAP intake | `IMAP_MODE=mock` (default without credentials): in-memory inbox | IMAP over SSL, reads UNSEEN mail |

## Jira

- `integrations/jira.py`: `sync_ticket(db, ticket_id)` is called by `hooks.py` after each ticket change.
  It creates the issue once, then updates summary and description, reads the Jira status, transitions it
  (`To Do` for Open/Awaiting User, `In Progress` for Escalated/In Progress, `Done` for Resolved/Closed) and
  adds a comment on each status change. Results are stored in `jira_tickets`.
- Refresh: `POST /integrations/jira/tickets/{ticket_id}/refresh` (staff). Same as `sync_ticket`, returns the row.
- Setup: create a free Jira Cloud site, then an API token at id.atlassian.com > Security > API tokens.
  Set `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`.

## Email

- Templates (`integrations/templates.py`): `ticket_received`, `ai_resolution` (with "Did this fix it?" yes/no
  links), `escalated`, `assigned`, `status_change`, `resolved`, `closed`.
- Recipient: the ticket requester. Every send is logged to `email_log`. Sending happens in the hooks
  background thread, so a slow or failed SMTP server never delays ticket creation.
- Feedback links: `GET /feedback/{ticket_id}?verdict=yes|no&exp=...&sig=...`. Signed with HMAC (secret: `JWT_SECRET`),
  valid 7 days, no login. "yes" closes the ticket; "no" escalates it to a human.
- Gmail setup: turn on 2-Step Verification, create an App Password, set `EMAIL_MODE=smtp`, `SMTP_USER`
  (the Gmail address), `SMTP_PASSWORD` (the App Password).

## Intake

- `POST /intake/webhook` with header `X-API-Key`. 503 if `WEBHOOK_API_KEY` is not set, 401 if the key is wrong.
  Tickets get `source=api`.
- IMAP poller (`IMAP_ENABLED=true`): every `IMAP_POLL_SECONDS` it reads unread mail and creates tickets with
  `source=email`. A message is marked read only after its ticket is saved. Manual run:
  `POST /integrations/email/poll` (admin). Quoted replies are cut off before the new text.

## Status screen

`GET /integrations/status` (staff) returns Jira mode, connected, last sync, synced tickets, last error;
emails sent today (`sent_today`, `dry_run_today`, `failed_today`); IMAP state; webhook configured.
`GET /integrations/email-log` lists recent emails.

## Analytics (staff)

| Endpoint | Contents |
|---|---|
| `/analytics/overview` | totals, open/resolved/closed, escalation rate, self-service rate, average resolution hours, SLA breaches |
| `/analytics/trends?days=30` | per day: created, resolved, escalated |
| `/analytics/categories` | per category: tickets, share, escalations, escalation rate, average AI confidence |
| `/analytics/agent-performance` | per agent: runs, success rate, average duration and confidence; per engineer: assigned, resolved, hours to resolve |
| `/analytics/escalations` | by status, team, source; overdue open escalations; average hours to accept and resolve |
| `/analytics/satisfaction` | "fixed" yes/no answers, satisfaction rate, average rating, rating distribution |
| `/analytics/recurring-issues` | rows written by the recurring-issue detector, most frequent first |
| `/reports/summary?format=csv\|pdf` | the whole summary as a downloadable file |

Definitions: open = not Resolved or Closed. Escalation rate = tickets with at least one escalation / all tickets.
Self-service rate = closed tickets never escalated / closed tickets. SLA breached = resolved after `due_at`, or
still open past `due_at`.

## Tests

`backend/tests/test_role_c_*.py`. They run on the in-memory database with Jira in mock mode, email in dry-run
mode and IMAP in mock mode (`backend/tests/role_c_support.py`). The SMTP path and the Jira Cloud client are
tested with fakes (`FakeSMTP`, `httpx.MockTransport`). No test uses the network.

Run: `cd backend && python -m pytest -q`
