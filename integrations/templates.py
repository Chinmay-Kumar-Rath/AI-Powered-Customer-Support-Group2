"""Email templates. Plain text, so they read well in every client and need no HTML rendering.

Template names (used in email_log.template):
    ticket_received, ai_resolution, escalated, assigned, status_change, resolved, closed
"""

_TEMPLATES = {
    "ticket_received": (
        "We received your request {ticket_code}",
        "Hello {greeting},\n\n"
        "Thanks for contacting support. We have received your request ({ticket_code}):\n"
        "  Subject: {subject}\n\n"
        "Our assistant is looking at it now. You will get another email with the next step.\n",
    ),
    "ai_resolution": (
        "Suggested fix for {ticket_code}: {subject}",
        "Hello {greeting},\n\n"
        "Here is a suggested fix for your request {ticket_code}:\n\n"
        "{response_text}\n\n"
        "{steps_block}"
        "Did this fix it?\n"
        "  Yes, it is fixed:  {yes_link}\n"
        "  No, I still need help:  {no_link}\n\n"
        "If the answer does not fix it, we will pass the request to a support engineer.\n",
    ),
    "escalated": (
        "{ticket_code} has been passed to our {team}",
        "Hello {greeting},\n\n"
        "Your request {ticket_code} needs a support engineer, so it has been passed to the {team}.\n"
        "{due_line}\n"
        "Reason: {reason}\n",
    ),
    "assigned": (
        "{ticket_code} has been assigned to {assignee_name}",
        "Hello {greeting},\n\n"
        "Your request {ticket_code} is now assigned to {assignee_name} ({team}).\n",
    ),
    "status_change": (
        "{ticket_code} is now {new_status}",
        "Hello {greeting},\n\n"
        "The status of your request {ticket_code} changed from {old_status} to {new_status}.\n"
        "{message_block}",
    ),
    "resolved": (
        "{ticket_code} has been resolved",
        "Hello {greeting},\n\n"
        "Your request {ticket_code} has been resolved.\n"
        "{notes_block}\n"
        "If the problem is not fixed, reply to this email or open the ticket again.\n",
    ),
    "closed": (
        "{ticket_code} is closed - thank you",
        "Hello {greeting},\n\n"
        "Your request {ticket_code} is closed. Thank you for your feedback.\n",
    ),
}


class _Safe(dict):
    def __missing__(self, key):
        return ""


def render(template: str, data: dict) -> tuple:
    """Returns (subject, body). Missing values become empty text instead of raising."""
    subject_t, body_t = _TEMPLATES[template]
    values = _Safe(data)
    subject = " ".join(subject_t.format_map(values).split())  # one line, no stray newlines
    return subject, body_t.format_map(values)


def names() -> list:
    return list(_TEMPLATES)
