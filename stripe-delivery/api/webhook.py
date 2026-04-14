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
from typing import Any, Callable, Optional

import stripe
from fastapi import APIRouter, HTTPException, Request, status

from api import crm, delivery
from api.catalog import load_catalog_index
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


def _resolve_buyer_email(session: Any) -> str:
    """Pull the buyer email from a Stripe session, with fallbacks."""
    customer_details = _safe(session, "customer_details")
    if customer_details:
        email = _safe(customer_details, "email")
        if email:
            return email
    direct = _safe(session, "customer_email")
    if direct:
        return direct
    return "unknown@unknown.invalid"


def _resolve_buyer_name(session: Any) -> Optional[str]:
    customer_details = _safe(session, "customer_details")
    if customer_details:
        return _safe(customer_details, "name")
    return None


def _resolve_buyer_phone(session: Any) -> Optional[str]:
    customer_details = _safe(session, "customer_details")
    if customer_details:
        return _safe(customer_details, "phone")
    return None


def handle_checkout_completed(event: stripe.Event) -> None:
    session = event["data"]["object"]
    session_id = _safe(session, "id") or "unknown"
    metadata = _safe(session, "metadata") or {}
    tier_id = _safe(metadata, "tier_id") or "unknown"

    logger.info(
        "checkout.session.completed received — tier_id=%s session_id=%s",
        tier_id,
        session_id,
    )
    _write_debug_log(event["id"], event["type"], _to_serializable(session))

    if tier_id == "unknown":
        logger.warning("checkout.session.completed has no tier_id metadata; skipping")
        return

    catalog = load_catalog_index()
    try:
        tier = catalog.get(tier_id)
    except KeyError:
        logger.error("checkout.session.completed for unknown tier_id=%s", tier_id)
        return

    purchase = crm.insert_purchase(
        tier_id=tier.tier_id,
        category=tier.category,
        delivery_type=tier.delivery_type,
        stripe_session_id=session_id,
        stripe_payment_intent_id=_safe(session, "payment_intent"),
        buyer_email=_resolve_buyer_email(session),
        buyer_name=_resolve_buyer_name(session),
        buyer_phone=_resolve_buyer_phone(session),
        amount_cents=int(_safe(session, "amount_total") or tier.price_cents),
        currency=(_safe(session, "currency") or tier.currency),
        status=(
            crm.PurchaseStatus.AWAITING_DELIVERY
            if tier.delivery_type == "zip_download"
            else crm.PurchaseStatus.AWAITING_DELIVERY
        ),
        tos_version_hash=_safe(metadata, "tos_version_hash"),
        tech_overview_version_hash=_safe(metadata, "tech_overview_version_hash"),
        buyer_ip=_safe(metadata, "buyer_ip"),
    )

    if tier.delivery_type == "zip_download":
        delivery.build_and_deliver_zip(purchase)
    else:  # notify_kyle
        lead = crm.insert_lead(
            tier_id=tier.tier_id,
            source="stripe_purchase",
            buyer_email=purchase.buyer_email,
            buyer_name=purchase.buyer_name,
            buyer_phone=purchase.buyer_phone,
            stripe_charge_id=purchase.stripe_charge_id,
            amount_cents=purchase.amount_cents,
            status=crm.LeadStatus.QUALIFIED,
        )
        crm.record_lead_event(lead.lead_id, "created", {"purchase_id": purchase.purchase_id})
        delivery.notify_kyle_new_purchase(purchase, lead)


def handle_refund(event: stripe.Event) -> None:
    charge = event["data"]["object"]
    charge_id = _safe(charge, "id") or "unknown"
    payment_intent_id = _safe(charge, "payment_intent")
    logger.info("charge.refunded received — charge_id=%s", charge_id)
    _write_debug_log(event["id"], event["type"], _to_serializable(charge))

    purchase = crm.get_purchase_by_charge_id(charge_id)
    if purchase is None and payment_intent_id:
        purchase = crm.get_purchase_by_payment_intent(payment_intent_id)
    if purchase is None:
        logger.warning("charge.refunded for unknown charge_id=%s", charge_id)
        return

    # If we found purchase via payment_intent, backfill the charge id.
    if purchase.stripe_charge_id != charge_id:
        crm.update_purchase_status(
            purchase.purchase_id,
            purchase.status,
            stripe_charge_id=charge_id,
        )

    if purchase.delivery_type == "zip_download" and purchase.zip_object_key:
        try:
            delivery.delete_r2_object(purchase.zip_object_key)
        except Exception:
            logger.exception("failed to delete R2 object on refund — continuing")

    crm.update_purchase_status(
        purchase.purchase_id,
        crm.PurchaseStatus.REFUNDED,
        download_url_expires_at=datetime.now(timezone.utc).isoformat(),
    )

    delivery.notify_kyle_refund(purchase)


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
