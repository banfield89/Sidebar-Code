"""SQLite models and helpers for purchases, leads, and lead events.

Session 6 scope. Every function uses parameterized SQL. Inserts are
idempotent where it makes sense — re-inserting a purchase with the same
stripe_session_id is a no-op (returns the existing row).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from api.db import get_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Status enums (string constants, not Python enums, for SQLite portability)
# ---------------------------------------------------------------------------
class PurchaseStatus:
    AWAITING_DELIVERY = "awaiting_delivery"
    DELIVERED = "delivered"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    FAILED = "failed"


class LeadStatus:
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


# ---------------------------------------------------------------------------
# Dataclasses returned by the read helpers
# ---------------------------------------------------------------------------
@dataclass
class Purchase:
    purchase_id: str
    tier_id: str
    category: str
    delivery_type: str
    stripe_session_id: str
    stripe_payment_intent_id: Optional[str]
    stripe_charge_id: Optional[str]
    buyer_email: str
    buyer_name: Optional[str]
    buyer_phone: Optional[str]
    amount_cents: int
    currency: str
    status: str
    zip_object_key: Optional[str]
    download_url_expires_at: Optional[str]
    download_attempts: int
    tos_version_hash: Optional[str]
    tech_overview_version_hash: Optional[str]
    buyer_ip: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Purchase":
        return cls(**{k: row[k] for k in row.keys() if k in cls.__annotations__})


@dataclass
class Lead:
    lead_id: str
    tier_id: str
    source: str
    status: str
    buyer_email: str
    buyer_name: Optional[str]
    buyer_phone: Optional[str]
    buyer_firm: Optional[str]
    intake_payload: Optional[str]
    stripe_charge_id: Optional[str]
    amount_cents: Optional[int]
    created_at: str
    next_action_at: Optional[str]
    notes: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Lead":
        return cls(**{k: row[k] for k in row.keys() if k in cls.__annotations__})


# ---------------------------------------------------------------------------
# Time + id helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_purchase_id() -> str:
    return f"pur_{uuid.uuid4().hex[:24]}"


def _new_lead_id() -> str:
    return f"lead_{uuid.uuid4().hex[:24]}"


def _new_event_id() -> str:
    return f"levt_{uuid.uuid4().hex[:24]}"


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------
def insert_purchase(
    *,
    tier_id: str,
    category: str,
    delivery_type: str,
    stripe_session_id: str,
    buyer_email: str,
    amount_cents: int,
    currency: str,
    status: str,
    stripe_payment_intent_id: Optional[str] = None,
    stripe_charge_id: Optional[str] = None,
    buyer_name: Optional[str] = None,
    buyer_phone: Optional[str] = None,
    tos_version_hash: Optional[str] = None,
    tech_overview_version_hash: Optional[str] = None,
    buyer_ip: Optional[str] = None,
) -> Purchase:
    """Insert a purchase row. Idempotent on stripe_session_id.

    If a purchase with the same stripe_session_id already exists, returns
    the existing row without modifying it. This is required because
    Stripe may deliver checkout.session.completed more than once.
    """
    existing = get_purchase_by_session_id(stripe_session_id)
    if existing is not None:
        logger.info("insert_purchase short-circuit — session_id=%s already has purchase=%s",
                    stripe_session_id, existing.purchase_id)
        return existing

    purchase_id = _new_purchase_id()
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO purchases (
                purchase_id, tier_id, category, delivery_type,
                stripe_session_id, stripe_payment_intent_id, stripe_charge_id,
                buyer_email, buyer_name, buyer_phone,
                amount_cents, currency, status,
                tos_version_hash, tech_overview_version_hash, buyer_ip,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                purchase_id, tier_id, category, delivery_type,
                stripe_session_id, stripe_payment_intent_id, stripe_charge_id,
                buyer_email, buyer_name, buyer_phone,
                amount_cents, currency, status,
                tos_version_hash, tech_overview_version_hash, buyer_ip,
                now, now,
            ),
        )
    return get_purchase_by_id(purchase_id)  # type: ignore[return-value]


def get_purchase_by_id(purchase_id: str) -> Optional[Purchase]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE purchase_id = ?", (purchase_id,)
        ).fetchone()
    return Purchase.from_row(row) if row else None


def get_purchase_by_session_id(stripe_session_id: str) -> Optional[Purchase]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_session_id = ?", (stripe_session_id,)
        ).fetchone()
    return Purchase.from_row(row) if row else None


def get_purchase_by_charge_id(stripe_charge_id: str) -> Optional[Purchase]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_charge_id = ?", (stripe_charge_id,)
        ).fetchone()
    return Purchase.from_row(row) if row else None


def get_purchase_by_payment_intent(payment_intent_id: str) -> Optional[Purchase]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_payment_intent_id = ?",
            (payment_intent_id,),
        ).fetchone()
    return Purchase.from_row(row) if row else None


def update_purchase_status(
    purchase_id: str,
    status: str,
    *,
    zip_object_key: Optional[str] = None,
    download_url_expires_at: Optional[str] = None,
    stripe_charge_id: Optional[str] = None,
) -> None:
    """Update mutable fields on a purchase row. Always bumps updated_at."""
    fields = ["status = ?", "updated_at = ?"]
    params: list[Any] = [status, _now()]
    if zip_object_key is not None:
        fields.append("zip_object_key = ?")
        params.append(zip_object_key)
    if download_url_expires_at is not None:
        fields.append("download_url_expires_at = ?")
        params.append(download_url_expires_at)
    if stripe_charge_id is not None:
        fields.append("stripe_charge_id = ?")
        params.append(stripe_charge_id)
    params.append(purchase_id)

    with get_connection() as conn:
        conn.execute(
            f"UPDATE purchases SET {', '.join(fields)} WHERE purchase_id = ?",
            tuple(params),
        )


def increment_download_attempts(purchase_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE purchases
               SET download_attempts = download_attempts + 1,
                   updated_at = ?
             WHERE purchase_id = ?
            """,
            (_now(), purchase_id),
        )


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------
def insert_lead(
    *,
    tier_id: str,
    source: str,
    buyer_email: str,
    status: str = LeadStatus.QUALIFIED,
    buyer_name: Optional[str] = None,
    buyer_phone: Optional[str] = None,
    buyer_firm: Optional[str] = None,
    intake_payload: Optional[dict] = None,
    stripe_charge_id: Optional[str] = None,
    amount_cents: Optional[int] = None,
    notes: Optional[dict] = None,
) -> Lead:
    """Insert a lead row. Idempotent on (source, stripe_charge_id) pair."""
    if stripe_charge_id and source == "stripe_purchase":
        existing = get_lead_by_charge_id(stripe_charge_id)
        if existing is not None:
            logger.info("insert_lead short-circuit — charge_id=%s already has lead=%s",
                        stripe_charge_id, existing.lead_id)
            return existing

    lead_id = _new_lead_id()
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO leads (
                lead_id, tier_id, source, status,
                buyer_email, buyer_name, buyer_phone, buyer_firm,
                intake_payload, stripe_charge_id, amount_cents,
                created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id, tier_id, source, status,
                buyer_email, buyer_name, buyer_phone, buyer_firm,
                json.dumps(intake_payload) if intake_payload else None,
                stripe_charge_id, amount_cents,
                now,
                json.dumps(notes) if notes else None,
            ),
        )
    return get_lead(lead_id)  # type: ignore[return-value]


def get_lead(lead_id: str) -> Optional[Lead]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE lead_id = ?", (lead_id,)
        ).fetchone()
    return Lead.from_row(row) if row else None


def get_lead_by_charge_id(stripe_charge_id: str) -> Optional[Lead]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE stripe_charge_id = ?", (stripe_charge_id,)
        ).fetchone()
    return Lead.from_row(row) if row else None


def update_lead_status(lead_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE leads SET status = ? WHERE lead_id = ?", (status, lead_id))


# ---------------------------------------------------------------------------
# Lead events
# ---------------------------------------------------------------------------
def record_lead_event(
    lead_id: str,
    event_type: str,
    event_data: Optional[dict] = None,
) -> str:
    event_id = _new_event_id()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO lead_events (event_id, lead_id, event_type, event_data, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_id,
                lead_id,
                event_type,
                json.dumps(event_data) if event_data else None,
                _now(),
            ),
        )
    return event_id


# ---------------------------------------------------------------------------
# Delivery failures
# ---------------------------------------------------------------------------
def record_delivery_failure(purchase_id: str, error_msg: str, traceback: Optional[str] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO delivery_failures (purchase_id, error_msg, traceback, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (purchase_id, error_msg, traceback, _now()),
        )
