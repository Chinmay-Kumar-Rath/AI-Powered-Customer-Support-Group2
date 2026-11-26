import sqlite3, json, urllib.request

conn = sqlite3.connect('backend/supportpilot.db')
conn.row_factory = sqlite3.Row

# Get table schema
print("=== TICKETS TABLE SCHEMA ===")
for r in conn.execute("PRAGMA table_info(tickets)").fetchall():
    print(dict(r))

print("\n=== EMAIL_LOG TABLE SCHEMA ===")
for r in conn.execute("PRAGMA table_info(email_log)").fetchall():
    print(dict(r))

print("\n=== JIRA_TICKETS TABLE SCHEMA ===")
for r in conn.execute("PRAGMA table_info(jira_tickets)").fetchall():
    print(dict(r))

print("\n=== ALL TICKETS ===")
rows = conn.execute("SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT 5").fetchall()
for r in rows:
    print(dict(r))

print("\n=== ALL EMAIL_LOG ===")
rows = conn.execute("SELECT * FROM email_log ORDER BY email_id DESC LIMIT 10").fetchall()
for r in rows:
    print(dict(r))

print("\n=== ALL JIRA_TICKETS ===")
rows = conn.execute("SELECT * FROM jira_tickets ORDER BY jira_id DESC LIMIT 10").fetchall()
for r in rows:
    print(dict(r))

conn.close()

# Check email log endpoint
try:
    req = urllib.request.Request("http://localhost:8000/integrations/email-log")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        print(f"\n=== EMAIL LOG ENDPOINT ({len(data)} entries) ===")
        for e in data[:5]:
            print(e)
except Exception as ex:
    print(f"Email log endpoint error: {ex}")
