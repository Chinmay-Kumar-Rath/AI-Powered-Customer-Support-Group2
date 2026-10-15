"""Settings. No .env file and no API keys needed.

The default points to the PostgreSQL started by docker-compose.yml
(or the local install described in the README). If you ever need a
different database, set a DATABASE_URL environment variable - it is
optional and nothing breaks without it.
"""
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://supportpilot:supportpilot@localhost:5432/supportpilot",
)

# Allowed values, agreed by the whole team. Do not change without telling everyone.
CATEGORIES = ["Network", "VPN", "Software", "Hardware", "Password Reset", "Email", "Security"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
PRIORITIES = ["P1", "P2", "P3", "P4"]

# Ticket lifecycle: current status -> statuses it is allowed to move to
ALLOWED_TRANSITIONS = {
    "Open": ["Classified"],
    "Classified": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Closed": [],
}
