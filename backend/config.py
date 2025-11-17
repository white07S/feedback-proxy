# config.py
import os
from pathlib import Path

DB_PATH = Path("./feedback.db")

# Postgres connection settings (Postgres-first, SQLite fallback)
POSTGRES_USER = os.getenv("POSTGRES_USER", "preetam")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "preetam123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "main")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
# Schema used for this app in Postgres
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "analytics")

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
