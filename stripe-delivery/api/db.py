"""SQLite helpers: connection management and schema initialization.

Session 5 introduces processed_events (idempotency) and webhook_debug_log.
Session 6 will add purchases, leads, lead_events, delivery_failures,
tos_versions, and tech_overview_versions on top of this same module.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)

_DEFAULT_LOCAL_PATH = Path(__file__).resolve().parent.parent / "sidebarcode.db"

_lock = threading.Lock()
_initialized_paths: set[str] = set()


def get_db_path() -> Path:
    """Resolve the SQLite path from env, else the local default."""
    override = os.environ.get("SQLITE_PATH")
    if override:
        return Path(override)
    return _DEFAULT_LOCAL_PATH


@contextmanager
def get_connection(path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    """Yield a sqlite3 connection with WAL mode enabled.

    Caller is responsible for committing or rolling back. Connection is
    closed automatically on context exit.
    """
    db_path = Path(path) if path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        if str(db_path) not in _initialized_paths:
            _init_schema(db_path)
            _initialized_paths.add(str(db_path))

    conn = sqlite3.connect(str(db_path), isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


def _init_schema(path: Path) -> None:
    """Create tables if they do not exist. Safe to call repeatedly."""
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    logger.info("SQLite schema initialized at %s", path)


def reset_for_tests() -> None:
    """Test helper — clears the initialized-paths cache so a fresh tmp_path
    DB triggers schema creation."""
    with _lock:
        _initialized_paths.clear()


_SCHEMA_SQL = """
-- Session 5: webhook idempotency and debug log
CREATE TABLE IF NOT EXISTS processed_events (
    stripe_event_id TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    processed_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_debug_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_event_id TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    event_data_json TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_webhook_debug_log_event_type
    ON webhook_debug_log(event_type);

CREATE INDEX IF NOT EXISTS idx_webhook_debug_log_created_at
    ON webhook_debug_log(created_at);
"""
