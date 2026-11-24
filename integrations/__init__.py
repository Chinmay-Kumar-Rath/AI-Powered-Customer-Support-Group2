"""Role C integrations: Jira, email (outbound + IMAP intake), webhook helpers.

hooks.py imports `integrations.notifications` and `integrations.jira`; the backend routes live in
backend/app/role_c_api.py. Every external service has a mock or dry-run mode so the whole flow runs
without credentials.
"""
