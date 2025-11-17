import os
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Any, Optional

import apsw

import config

try:
    import psycopg2

    _HAVE_PG = True
except Exception:
    # If psycopg2 isn't available we silently fall back to SQLite.
    psycopg2 = None  # type: ignore[assignment]
    _HAVE_PG = False


POSTGRES_USER = os.getenv("POSTGRES_USER", "preetam")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "preetam123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "main")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "analytics")


class DbCursor:
    def __init__(self, backend: str, raw_cursor: Any):
        self.backend = backend
        self._cur = raw_cursor

    def getdescription(self):
        if self.backend == "sqlite":
            return self._cur.getdescription()
        # psycopg2 returns description as a sequence of tuples
        return self._cur.description or []

    def fetchone(self):
        return self._cur.fetchone()

    def __iter__(self):
        return self

    def __next__(self):
        if self.backend == "sqlite":
            return next(self._cur)
        row = self._cur.fetchone()
        if row is None:
            raise StopIteration
        return row


class DbConnection:
    """
    Thin wrapper providing a minimal common API for SQLite (apsw)
    and Postgres (psycopg2), so the rest of the code can stay
    mostly unchanged.
    """

    def __init__(self, backend: str, raw_con: Any):
        self.backend = backend
        self._con = raw_con
        self._last_rowcount = 0

    def execute(self, sql: str, params: Iterable[Any] = ()):
        if self.backend == "sqlite":
            cur = self._con.execute(sql, tuple(params))
            return DbCursor("sqlite", cur)
        # Postgres: convert SQLite-style '?' placeholders to '%s'
        sql_pg = sql.replace("?", "%s")
        cur = self._con.cursor()
        cur.execute(sql_pg, tuple(params))
        self._last_rowcount = cur.rowcount
        return DbCursor("postgres", cur)

    def changes(self) -> int:
        if self.backend == "sqlite":
            return self._con.changes()
        return self._last_rowcount

    def close(self):
        self._con.close()

    # Transaction context manager: `with con:`
    def __enter__(self):
        if self.backend == "sqlite":
            # Start an explicit transaction
            self._con.execute("BEGIN;")
        else:
            # psycopg2 uses implicit transactions; nothing to do on enter
            pass
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.backend == "sqlite":
            if exc_type:
                self._con.execute("ROLLBACK;")
            else:
                self._con.execute("COMMIT;")
        else:
            if exc_type:
                self._con.rollback()
            else:
                self._con.commit()


_BACKEND: Optional[str] = None  # "postgres" or "sqlite"


def _connect_sqlite() -> DbConnection:
    con = apsw.Connection(str(config.DB_PATH))
    # Execute PRAGMAs outside of transaction
    con.execute("PRAGMA busy_timeout=5000;")
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return DbConnection("sqlite", con)


def _connect_postgres() -> DbConnection:
    if not _HAVE_PG:
        raise RuntimeError("psycopg2 not available")
    con = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    )
    # Ensure analytics schema exists and is first in search_path
    cur = con.cursor()
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{POSTGRES_SCHEMA}";')
    cur.execute(f'SET search_path TO "{POSTGRES_SCHEMA}", public;')
    con.commit()
    return DbConnection("postgres", con)


def _connect() -> DbConnection:
    """
    Prefer Postgres, fall back to SQLite if anything goes wrong.
    The chosen backend is cached so we don't keep retrying Postgres
    on every connection attempt.
    """
    global _BACKEND

    if _BACKEND == "postgres":
        return _connect_postgres()
    if _BACKEND == "sqlite":
        return _connect_sqlite()

    # First time: try Postgres, then SQLite.
    if _HAVE_PG:
        try:
            con = _connect_postgres()
            _BACKEND = "postgres"
            return con
        except Exception:
            # Any failure: mark backend as sqlite and fall back.
            _BACKEND = "sqlite"
            return _connect_sqlite()
    else:
        _BACKEND = "sqlite"
        return _connect_sqlite()


@contextmanager
def get_con():
    con = _connect()
    try:
        yield con
    finally:
        con.close()


def init_db():
    """
    Create tables for whichever backend is active.
    We keep separate DDL for SQLite and Postgres to avoid
    cross-dialect quirks.
    """
    with get_con() as con, con:
        if getattr(con, "backend", "sqlite") == "postgres":
            # Postgres schema (analytics schema is already on search_path)
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  id SERIAL PRIMARY KEY,
                  key TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  active BOOLEAN NOT NULL DEFAULT TRUE
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                  id SERIAL PRIMARY KEY,
                  project_key TEXT NOT NULL REFERENCES projects(key) ON UPDATE CASCADE ON DELETE RESTRICT,
                  type TEXT NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  severity TEXT,
                  status TEXT NOT NULL DEFAULT 'pending',
                  created_by TEXT NOT NULL,
                  assignee TEXT,
                  resolution TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                  id SERIAL PRIMARY KEY,
                  feedback_id INTEGER NOT NULL REFERENCES feedback(id) ON DELETE CASCADE,
                  body TEXT NOT NULL,
                  created_by TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )
        else:
            # SQLite schema (original APSW DDL)
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  id INTEGER PRIMARY KEY,
                  key TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  active INTEGER NOT NULL DEFAULT 1
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                  id INTEGER PRIMARY KEY,
                  project_key TEXT NOT NULL REFERENCES projects(key) ON UPDATE CASCADE ON DELETE RESTRICT,
                  type TEXT NOT NULL,                    -- 'bug' | 'feature'
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  severity TEXT,
                  status TEXT NOT NULL DEFAULT 'pending',   -- from config.STATUSES
                  created_by TEXT NOT NULL,
                  assignee TEXT,
                  resolution TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                  id INTEGER PRIMARY KEY,
                  feedback_id INTEGER NOT NULL REFERENCES feedback(id) ON DELETE CASCADE,
                  body TEXT NOT NULL,
                  created_by TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )

        # seed allowed projects (works on both backends)
        for p in config.ALLOWED_PROJECTS:
            con.execute(
                "INSERT INTO projects(key,name,active) VALUES(?,?,1) "
                "ON CONFLICT (key) DO NOTHING;",
                (p["key"], p["name"]),
            )


def query(con: DbConnection, sql: str, params: Iterable[Any] = ()):
    cur = con.execute(sql, params)
    # Get column names while cursor is still open
    try:
        cols = [d[0] for d in cur.getdescription()]
        for row in cur:
            yield dict(zip(cols, row))
    except Exception:
        # If we can't get description (e.g. no results), just return
        return


def scalar(con: DbConnection, sql: str, params: Iterable[Any] = ()):
    # Special-case SQLite's last_insert_rowid() for Postgres
    if getattr(con, "backend", "sqlite") == "postgres":
        normalized = " ".join(sql.strip().lower().split())
        if normalized.startswith("select last_insert_rowid()"):
            # Use Postgres' lastval(), which returns the most recently
            # assigned sequence value in this session.
            cur = con.execute("SELECT lastval();")
            r = cur.fetchone()
            return r[0] if r else None

    cur = con.execute(sql, params)
    r = cur.fetchone()
    return r[0] if r else None


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
