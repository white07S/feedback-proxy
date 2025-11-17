import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Any, Optional

import apsw

import config

logger = logging.getLogger(__name__)

try:
    import asyncpg

    _HAVE_PG = True
except Exception:
    # If asyncpg isn't available we silently fall back to SQLite.
    asyncpg = None  # type: ignore[assignment]
    _HAVE_PG = False


class DbCursor:
    """
    Simple in-memory cursor that works for both SQLite and Postgres.
    """

    def __init__(self, columns: Optional[list[str]], rows: list[tuple[Any, ...]]):
        self._columns = columns or []
        self._rows = rows
        self._index = 0

    def getdescription(self):
        # Emulate DB-API cursor.description: sequence of tuples
        return [(name,) for name in self._columns]

    def fetchone(self):
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


def _convert_placeholders(sql: str) -> str:
    """
    Convert SQLite-style '?' placeholders to asyncpg '$1', '$2', ...
    """
    out: list[str] = []
    idx = 1
    for ch in sql:
        if ch == "?":
            out.append(f"${idx}")
            idx += 1
        else:
            out.append(ch)
    return "".join(out)


class DbConnection:
    """
    Thin wrapper providing a minimal common API for SQLite (apsw)
    and Postgres (asyncpg), so the rest of the code can stay
    mostly unchanged.
    """

    def __init__(self, backend: str, raw_con: Any, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.backend = backend
        self._con = raw_con
        self._last_rowcount = 0
        self._loop = loop

    def execute(self, sql: str, params: Iterable[Any] = ()):
        if self.backend == "sqlite":
            cur = self._con.execute(sql, tuple(params))
            try:
                desc = cur.getdescription()
                columns = [d[0] for d in desc]
                rows = list(cur)
            except apsw.ExecutionCompleteError:
                columns, rows = [], []
            return DbCursor(columns, rows)

        # Postgres via asyncpg
        if not self._loop:
            raise RuntimeError("Event loop is required for Postgres backend")

        sql_pg = _convert_placeholders(sql)
        params_tuple = tuple(params)
        normalized = " ".join(sql.strip().lower().split())
        is_select = normalized.startswith("select")

        if is_select:

            async def _run_select():
                records = await self._con.fetch(sql_pg, *params_tuple)
                if records:
                    cols = list(records[0].keys())
                    rows = [tuple(r[c] for c in cols) for r in records]
                else:
                    cols, rows = [], []
                self._last_rowcount = len(rows)
                return cols, rows

            columns, rows = self._loop.run_until_complete(_run_select())
        else:

            async def _run_exec():
                status = await self._con.execute(sql_pg, *params_tuple)
                parts = status.split()
                count = 0
                if parts and parts[-1].isdigit():
                    count = int(parts[-1])
                self._last_rowcount = count
                return [], []

            columns, rows = self._loop.run_until_complete(_run_exec())

        return DbCursor(columns, rows)

    def changes(self) -> int:
        if self.backend == "sqlite":
            return self._con.changes()
        return self._last_rowcount

    def close(self):
        if self.backend == "sqlite":
            self._con.close()
        else:
            if self._loop:
                self._loop.run_until_complete(self._con.close())
                self._loop.close()

    # Transaction context manager: `with con:`
    def __enter__(self):
        if self.backend == "sqlite":
            # Start an explicit transaction
            self._con.execute("BEGIN;")
        # For Postgres/asyncpg we rely on per-statement transactions.
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.backend == "sqlite":
            if exc_type:
                self._con.execute("ROLLBACK;")
            else:
                self._con.execute("COMMIT;")
        # For Postgres/asyncpg, no explicit transaction handling here.


_BACKEND: Optional[str] = "postgres"


def _connect_sqlite() -> DbConnection:
    con = apsw.Connection(str(config.DB_PATH))
    # Execute PRAGMAs outside of transaction
    con.execute("PRAGMA busy_timeout=5000;")
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return DbConnection("sqlite", con)


def _connect_postgres() -> DbConnection:
    if not _HAVE_PG:
        raise RuntimeError("asyncpg not available")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create connection
    con = loop.run_until_complete(
        asyncpg.connect(
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DB,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
        )
    )
    # Ensure analytics schema exists and is first in search_path
    loop.run_until_complete(
        con.execute(f'CREATE SCHEMA IF NOT EXISTS "{config.POSTGRES_SCHEMA}";')
    )
    loop.run_until_complete(
        con.execute(f'SET search_path TO "{config.POSTGRES_SCHEMA}", public;')
    )

    return DbConnection("postgres", con, loop)


def _connect() -> DbConnection:
    """
    Prefer Postgres, fall back to SQLite if anything goes wrong.
    The chosen backend is cached so we don't keep retrying Postgres
    on every connection attempt.
    """
    global _BACKEND

    # If we've previously decided on SQLite, always use that.
    if _BACKEND == "sqlite":
        return _connect_sqlite()

    # Try Postgres when asyncpg is available.
    if _HAVE_PG:
        try:
            con = _connect_postgres()
            _BACKEND = "postgres"
            logger.info("DB backend selected: postgres (schema=%s)", config.POSTGRES_SCHEMA)
            return con
        except Exception as exc:
            # Any failure: mark backend as sqlite and fall back.
            logger.warning("Postgres connection failed (%s); falling back to SQLite", exc)
            _BACKEND = "sqlite"
            return _connect_sqlite()

    # No asyncpg available: use SQLite.
    logger.info("asyncpg not available; using SQLite backend")
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
            logger.info("Using Postgres backend for schema initialization")
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
        is_pg = getattr(con, "backend", "sqlite") == "postgres"
        active_default = True if is_pg else 1
        for p in config.ALLOWED_PROJECTS:
            con.execute(
                "INSERT INTO projects(key,name,active) VALUES(?,?,?) "
                "ON CONFLICT (key) DO NOTHING;",
                (p["key"], p["name"], active_default),
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
