# config.py
from pathlib import Path

DB_PATH = Path("./feedback.db")

# developer-controlled projects; users can *not* add here
ALLOWED_PROJECTS = [
    {"key": "nfrfscenario", "name": "NFRF Scenario"},
    {"key": "nfrfconnect",  "name": "NFRF Connect"},
]

FEEDBACK_TYPES = ["bug", "feature"]
STATUSES = ["pending", "in_progress", "resolved", "closed"]
SEVERITIES = ["low", "medium", "high", "critical"]  # optional
PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# mock people directory for assignment
PEOPLE = [
    {"username": "preetam", "name": "Preetam Shah"},
    {"username": "alice", "name": "Alice Johnson"},
    {"username": "brian", "name": "Brian Lee"},
    {"username": "carmen", "name": "Carmen Diaz"},
]
