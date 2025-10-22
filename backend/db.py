# db.py
import apsw
from datetime import datetime
from typing import Iterable, Any, Dict, Optional
from contextlib import contextmanager
import config

def _connect() -> apsw.Connection:
    # APSW gives direct SQLite; set WAL + foreign keys + busy timeout
    con = apsw.Connection(str(config.DB_PATH))
    # Execute PRAGMAs outside of transaction
    con.execute("PRAGMA busy_timeout=5000;")  # ensure we wait before enabling WAL
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con

@contextmanager
def get_con():
    con = _connect()
    try:
        yield con
    finally:
        con.close()

def init_db():
    with get_con() as con, con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY,
          key TEXT UNIQUE NOT NULL,
          name TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
          id INTEGER PRIMARY KEY,
          project_key TEXT NOT NULL REFERENCES projects(key) ON UPDATE CASCADE ON DELETE RESTRICT,
          type TEXT NOT NULL,                    -- 'bug' | 'feature'
          title TEXT NOT NULL,
          description TEXT NOT NULL,
          severity TEXT,
          status TEXT NOT NULL DEFAULT 'open',   -- from config.STATUSES
          created_by TEXT NOT NULL,
          assignee TEXT,
          resolution TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS comments (
          id INTEGER PRIMARY KEY,
          feedback_id INTEGER NOT NULL REFERENCES feedback(id) ON DELETE CASCADE,
          body TEXT NOT NULL,
          created_by TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)
        # seed allowed projects
        for p in config.ALLOWED_PROJECTS:
            con.execute(
                "INSERT OR IGNORE INTO projects(key,name,active) VALUES(?,?,1);",
                (p["key"], p["name"])
            )

def query(con: apsw.Connection, sql: str, params: Iterable[Any] = ()):
    cur = con.execute(sql, params)
    # Get column names while cursor is still open
    try:
        cols = [d[0] for d in cur.getdescription()]
        # Iterate directly over cursor
        for row in cur:
            yield dict(zip(cols, row))
    except apsw.ExecutionCompleteError:
        # If we can't get description, it means query returned no results
        return

def scalar(con: apsw.Connection, sql: str, params: Iterable[Any] = ()):
    cur = con.execute(sql, params)
    r = cur.fetchone()
    return r[0] if r else None

def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
