import urllib.request, json, sqlite3

# Check email_log and jira_tickets in DB
conn = sqlite3.connect('backend/supportpilot.db')
conn.row_factory = sqlite3.Row

print("=== EMAIL LOG ===")
rows = conn.execute("SELECT email_id, ticket_id, to_email, template, subject, status, error FROM email_log ORDER BY email_id DESC LIMIT 10").fetchall()
for r in rows:
    print(dict(r))

print("\n=== JIRA TICKETS ===")
rows = conn.execute("SELECT * FROM jira_tickets ORDER BY jira_id DESC LIMIT 10").fetchall()
for r in rows:
    print(dict(r))

print("\n=== TICKETS ===")
rows = conn.execute("SELECT ticket_id, ticket_code, title, status, priority, category, source FROM tickets ORDER BY ticket_id DESC LIMIT 5").fetchall()
for r in rows:
    print(dict(r))

conn.close()

# Check analytics overview
req = urllib.request.Request("http://localhost:8000/analytics/overview")
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
    print("\n=== ANALYTICS OVERVIEW ===")
    print(json.dumps(data, indent=2))

# Check integrations status again
req = urllib.request.Request("http://localhost:8000/integrations/status")
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
    print("\n=== INTEGRATIONS STATUS ===")
    print(json.dumps(data, indent=2))
