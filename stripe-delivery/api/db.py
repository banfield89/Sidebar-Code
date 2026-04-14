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

-- Session 6: purchases, leads, refunds, audit trail

CREATE TABLE IF NOT EXISTS purchases (
    purchase_id              TEXT PRIMARY KEY,
    tier_id                  TEXT NOT NULL,
    category                 TEXT NOT NULL,
    delivery_type            TEXT NOT NULL,
    stripe_session_id        TEXT NOT NULL UNIQUE,
    stripe_payment_intent_id TEXT,
    stripe_charge_id         TEXT,
    buyer_email              TEXT NOT NULL,
    buyer_name               TEXT,
    buyer_phone              TEXT,
    amount_cents             INTEGER NOT NULL,
    currency                 TEXT NOT NULL,
    status                   TEXT NOT NULL,
    zip_object_key           TEXT,
    download_url_expires_at  TEXT,
    download_attempts        INTEGER NOT NULL DEFAULT 0,
    tos_version_hash         TEXT,
    tech_overview_version_hash TEXT,
    buyer_ip                 TEXT,
    created_at               TEXT NOT NULL,
    updated_at               TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_purchases_charge_id
    ON purchases(stripe_charge_id);
CREATE INDEX IF NOT EXISTS idx_purchases_payment_intent
    ON purchases(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status
    ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_tier_id
    ON purchases(tier_id);

CREATE TABLE IF NOT EXISTS leads (
    lead_id          TEXT PRIMARY KEY,
    tier_id          TEXT NOT NULL,
    source           TEXT NOT NULL,
    status           TEXT NOT NULL,
    buyer_email      TEXT NOT NULL,
    buyer_name       TEXT,
    buyer_phone      TEXT,
    buyer_firm       TEXT,
    intake_payload   TEXT,
    stripe_charge_id TEXT,
    amount_cents     INTEGER,
    created_at       TEXT NOT NULL,
    next_action_at   TEXT,
    notes            TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_charge_id ON leads(stripe_charge_id);

CREATE TABLE IF NOT EXISTS lead_events (
    event_id    TEXT PRIMARY KEY,
    lead_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    event_data  TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE INDEX IF NOT EXISTS idx_lead_events_lead_id
    ON lead_events(lead_id);

CREATE TABLE IF NOT EXISTS delivery_failures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id TEXT NOT NULL,
    error_msg   TEXT NOT NULL,
    traceback   TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id)
);

CREATE INDEX IF NOT EXISTS idx_delivery_failures_purchase
    ON delivery_failures(purchase_id);

CREATE TABLE IF NOT EXISTS tos_versions (
    version_hash    TEXT PRIMARY KEY,
    first_seen_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tech_overview_versions (
    version_hash    TEXT PRIMARY KEY,
    first_seen_at   TEXT NOT NULL
);

-- SP3 Session 1: Steward inbound debug log (raw Postmark payloads for audit)
CREATE TABLE IF NOT EXISTS inbound_emails (
    inbound_id          TEXT PRIMARY KEY,
    postmark_message_id TEXT NOT NULL,
    from_email          TEXT NOT NULL,
    from_name           TEXT,
    to_email            TEXT NOT NULL,
    subject             TEXT,
    text_body           TEXT,
    html_body           TEXT,
    in_reply_to         TEXT,
    raw_payload_json    TEXT NOT NULL,
    matched_lead_id     TEXT,
    classification      TEXT,
    send_tier           TEXT,
    received_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inbound_postmark_id
    ON inbound_emails(postmark_message_id);
CREATE INDEX IF NOT EXISTS idx_inbound_in_reply_to
    ON inbound_emails(in_reply_to);
CREATE INDEX IF NOT EXISTS idx_inbound_matched_lead
    ON inbound_emails(matched_lead_id);
CREATE INDEX IF NOT EXISTS idx_inbound_received_at
    ON inbound_emails(received_at);
"""
