"""Stripe webhook handler: signature verification, idempotency, and event routing.

Session 5 scope. Sessions 6-7 will replace the stub handlers below with
real purchase-row insertion and delivery orchestration.

Order of operations on every incoming event:
  1. Read raw body (must NOT parse before verifying signature).
  2. Verify signature via stripe.Webhook.construct_event.
  3. Check processed_events for idempotency. If seen, 200 immediately.
  4. Dispatch to a stub handler based on event.type.
  5. Each stub writes to webhook_debug_log for audit.
  6. Mark event as processed AFTER the handler succeeds, so retries on
     handler failure are still possible (Stripe's exponential backoff).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable

import stripe
from fastapi import APIRouter, HTTPException, Request, status

from api.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------
def _verify_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify Stripe signature and return the parsed Event.

    Raises HTTPException(400) on any failure.
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not set — cannot verify webhook")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="webhook secret not configured",
        )
    try:
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=secret,
        )
    except ValueError as exc:
        logger.warning("Stripe webhook payload not parseable: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid payload") from exc
    except stripe.error.SignatureVerificationError as exc:  # type: ignore[attr-defined]
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid signature") from exc


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------
def _is_already_processed(event_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT stripe_event_id FROM processed_events WHERE stripe_event_id = ?",
            (event_id,),
        ).fetchone()
        return row is not None


def _mark_processed(event_id: str, event_type: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_events (stripe_event_id, event_type, processed_at) VALUES (?, ?, ?)",
            (event_id, event_type, datetime.now(timezone.utc).isoformat()),
        )


# ---------------------------------------------------------------------------
# Debug log
# ---------------------------------------------------------------------------
def _write_debug_log(event_id: str, event_type: str, event_data: Any) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO webhook_debug_log
                (stripe_event_id, event_type, event_data_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                json.dumps(event_data, default=str),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


# ---------------------------------------------------------------------------
# Stub handlers — Session 6/7 will replace these with real orchestration
# ---------------------------------------------------------------------------
def _safe(obj: Any, key: str, default: Any = None) -> Any:
    """Safe accessor for Stripe StripeObject, which lacks dict-style .get()."""
    if obj is None:
        return default
    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        return default


def _to_serializable(obj: Any) -> Any:
    """Convert a StripeObject (or anything else) to plain JSON-able data."""
    if hasattr(obj, "to_dict_recursive"):
        try:
            return obj.to_dict_recursive()
        except Exception:
            pass
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    return obj


def handle_checkout_completed(event: stripe.Event) -> None:
    session = event["data"]["object"]
    metadata = _safe(session, "metadata") or {}
    tier_id = _safe(metadata, "tier_id", "unknown") or "unknown"
    logger.info(
        "checkout.session.completed received — tier_id=%s session_id=%s",
        tier_id,
        _safe(session, "id"),
    )
    _write_debug_log(event["id"], event["type"], _to_serializable(session))


def handle_refund(event: stripe.Event) -> None:
    charge = event["data"]["object"]
    logger.info("charge.refunded received — charge_id=%s", _safe(charge, "id"))
    _write_debug_log(event["id"], event["type"], _to_serializable(charge))


def handle_dispute_opened(event: stripe.Event) -> None:
    dispute = event["data"]["object"]
    logger.info("charge.dispute.created received — dispute_id=%s", _safe(dispute, "id"))
    _write_debug_log(event["id"], event["type"], _to_serializable(dispute))


def handle_dispute_closed(event: stripe.Event) -> None:
    dispute = event["data"]["object"]
    logger.info(
        "charge.dispute.closed received — dispute_id=%s status=%s",
        _safe(dispute, "id"),
        _safe(dispute, "status"),
    )
    _write_debug_log(event["id"], event["type"], _to_serializable(dispute))


_HANDLERS: dict[str, Callable[[stripe.Event], None]] = {
    "checkout.session.completed": handle_checkout_completed,
    "charge.refunded": handle_refund,
    "charge.dispute.created": handle_dispute_opened,
    "charge.dispute.closed": handle_dispute_closed,
}


# ---------------------------------------------------------------------------
# POST /api/webhook
# ---------------------------------------------------------------------------
@router.post("/api/webhook")
async def stripe_webhook(request: Request) -> dict[str, str]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    event = _verify_signature(payload, sig_header)

    event_id = event["id"]
    event_type = event["type"]

    if _is_already_processed(event_id):
        logger.info("webhook idempotency short-circuit — event_id=%s already processed", event_id)
        return {"status": "duplicate", "event_id": event_id}

    handler = _HANDLERS.get(event_type)
    if handler is None:
        logger.info("webhook ignoring unhandled event type: %s", event_type)
        _mark_processed(event_id, event_type)
        return {"status": "ignored", "event_id": event_id, "event_type": event_type}

    try:
        handler(event)
    except Exception:
        logger.exception("webhook handler failed — Stripe will retry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="handler error",
        )

    _mark_processed(event_id, event_type)
    return {"status": "processed", "event_id": event_id, "event_type": event_type}
