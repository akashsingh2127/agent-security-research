"""SQLite database setup, schema management, and connection handling.

Audit Integrity Notice:
Audit events are exposed strictly as append-only operations through the
application interface (no update or delete methods exist). However, because
SQLite is a local embedded file database, it lacks hardware-enforced write-once
guarantees. An adversary with direct OS/filesystem access or arbitrary SQL execution
could tamper with the audit_events table. Therefore, application audit logs are
treated as internal evidence that must be corroborated out-of-band by the
independent security_engine in future milestones.
"""

import sqlite3
from collections.abc import Generator
from pathlib import Path
from typing import Optional
from target_app.config import settings


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_records_owner_id ON records(owner_id);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    request_id TEXT NOT NULL,
    principal_id TEXT,
    action TEXT NOT NULL,
    resource_id TEXT,
    resource_owner TEXT,
    auth_decision TEXT NOT NULL,
    outcome TEXT NOT NULL,
    error_detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_principal ON audit_events(principal_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_id);
"""


def get_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    target_path = Path(db_path) if db_path is not None else settings.resolved_db_path

    # Ensure parent directory exists if using a file path
    if str(target_path) != ":memory:":
        target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(target_path),
        check_same_thread=False,
        timeout=10.0,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if str(target_path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[Path | str] = None) -> None:
    """Initialize the SQLite database schema if tables do not exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency yielding an active SQLite connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

