"""Email templates: plain text and HTML for all 7 lifecycle events.

Template names (used in email_log.template):
    ticket_received, ai_resolution, escalated, assigned, status_change, resolved, closed
"""
import html

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
        "{frontend_links_block}"
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

_HTML_TEMPLATES = {
    "ticket_received": (
        "<h2>Support Request Received</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Thanks for contacting support. We have received your request <strong>{ticket_code}</strong>:</p>"
        "<blockquote><strong>Subject:</strong> {subject}</blockquote>"
        "<p>Our assistant is analyzing your ticket now. You will receive an update shortly.</p>"
    ),
    "ai_resolution": (
        "<h2>Suggested Fix for {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Here is a suggested resolution for your ticket:</p>"
        "<div style='background:#f4f7f9;border-left:4px solid #0066cc;padding:12px;margin:12px 0;'>"
        "{response_text_html}"
        "</div>"
        "{steps_html}"
        "<h3>Did this fix it?</h3>"
        "<p style='margin:16px 0;'>"
        "<a href='{frontend_yes_link}' style='display:inline-block;padding:10px 18px;margin-right:12px;background:#28a745;color:#ffffff;text-decoration:none;border-radius:4px;font-weight:bold;'>Yes, it fixed it</a>"
        "<a href='{frontend_no_link}' style='display:inline-block;padding:10px 18px;background:#dc3545;color:#ffffff;text-decoration:none;border-radius:4px;font-weight:bold;'>No, I still need help</a>"
        "</p>"
        "<p style='font-size:12px;color:#666;'>Direct link: <a href='{yes_link}'>Yes</a> | <a href='{no_link}'>No</a></p>"
    ),
    "escalated": (
        "<h2>Ticket Escalated: {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Your request has been passed to the <strong>{team}</strong> for engineer review.</p>"
        "<p>{due_line_html}</p>"
        "<p><strong>Reason:</strong> {reason}</p>"
    ),
    "assigned": (
        "<h2>Ticket Assigned: {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Your request is now assigned to <strong>{assignee_name}</strong> ({team}).</p>"
    ),
    "status_change": (
        "<h2>Status Updated: {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Status changed from <em>{old_status}</em> to <strong>{new_status}</strong>.</p>"
        "<div>{message_block_html}</div>"
    ),
    "resolved": (
        "<h2>Ticket Resolved: {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Your request has been marked as resolved.</p>"
        "<div>{notes_block_html}</div>"
        "<p>If you still encounter issues, please reopen the ticket or reply to this message.</p>"
    ),
    "closed": (
        "<h2>Ticket Closed: {ticket_code}</h2>"
        "<p>Hello <strong>{greeting}</strong>,</p>"
        "<p>Your ticket is now closed. Thank you for your feedback!</p>"
    ),
}

_EMAIL_WRAPPER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 20px; background: #f9fafb; }}
.container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; }}
.header {{ border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 20px; font-size: 20px; font-weight: bold; color: #1e3a8a; }}
.footer {{ border-top: 1px solid #e5e7eb; margin-top: 24px; padding-top: 12px; font-size: 12px; color: #6b7280; text-align: center; }}
</style>
</head>
<body>
<div class="container">
<div class="header">SupportPilot IT Support</div>
{content}
<div class="footer">&copy; SupportPilot Platform. Automated notification.</div>
</div>
</body>
</html>"""


class _Safe(dict):
    def __missing__(self, key):
        return ""


def render(template: str, data: dict) -> tuple:
    """Returns (subject, body). Missing values become empty text instead of raising."""
    key = "ai_resolution" if template in ("ai_resolution", "ai_resolution_sent") else template
    key = "status_change" if key in ("status_change", "status_changed") else key
    subject_t, body_t = _TEMPLATES[key]
    values = _Safe(data)
    subject = " ".join(subject_t.format_map(values).split())  # one line, no stray newlines
    return subject, body_t.format_map(values)


def render_html(template: str, data: dict) -> str:
    """Returns styled HTML body for the email."""
    key = "ai_resolution" if template in ("ai_resolution", "ai_resolution_sent") else template
    key = "status_change" if key in ("status_change", "status_changed") else key
    html_tpl = _HTML_TEMPLATES.get(key, "<p>{greeting}</p>")
    # Prepare escaped variants
    safe_data = dict(data)
    safe_data["response_text_html"] = html.escape(str(data.get("response_text", ""))).replace("\n", "<br>")
    safe_data["due_line_html"] = html.escape(str(data.get("due_line", "")))
    safe_data["message_block_html"] = html.escape(str(data.get("message_block", ""))).replace("\n", "<br>")
    safe_data["notes_block_html"] = html.escape(str(data.get("notes_block", ""))).replace("\n", "<br>")
    safe_data["frontend_yes_link"] = data.get("frontend_yes_link") or data.get("yes_link", "#")
    safe_data["frontend_no_link"] = data.get("frontend_no_link") or data.get("no_link", "#")

    steps = data.get("steps") or []
    if steps:
        steps_items = "".join(f"<li>{html.escape(s)}</li>" for s in steps)
        safe_data["steps_html"] = f"<ol>{steps_items}</ol>"
    else:
        safe_data["steps_html"] = ""

    content = html_tpl.format_map(_Safe(safe_data))
    return _EMAIL_WRAPPER.format(content=content)


def render_all(template: str, data: dict) -> tuple:
    """Returns (subject, text_body, html_body)."""
    subject, text_body = render(template, data)
    html_body = render_html(template, data)
    return subject, text_body, html_body


def names() -> list:
    return list(_TEMPLATES)
