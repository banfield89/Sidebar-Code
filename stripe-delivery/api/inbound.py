"""Postmark inbound webhook — entry point for Steward.

Session 1 scope: validate the shared secret, hard-fail on any CHDB address,
write the raw payload to inbound_emails for audit, return 200. Sessions 3-4
will wire the classification, Aemon review, and outbox routing.

Postmark's inbound webhook can authenticate via either URL basic-auth or a
custom header. This route accepts BOTH so Kyle can pick one in the Postmark
dashboard without code changes:

  - Authorization: Basic <base64(user:POSTMARK_INBOUND_SECRET)>
  - X-Postmark-Inbound-Token: <POSTMARK_INBOUND_SECRET>

Both validate against the same env var via secrets.compare_digest.

CHDB enforcement runs BEFORE the row is inserted. There is no override.
See api/steward/enforcement.py for the rationale.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.db import get_connection
from api.steward.enforcement import ChdbSeparationViolation, enforce_inbound

logger = logging.getLogger(__name__)
router = APIRouter()


def _new_inbound_id() -> str:
    return f"in_{uuid.uuid4().hex[:24]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verify_postmark_secret(
    authorization: Optional[str],
    inbound_token: Optional[str],
) -> None:
    """Validate the Postmark inbound shared secret.

    Accepts either Basic auth (Authorization header) or the
    X-Postmark-Inbound-Token custom header. Fails closed if neither is
    present and POSTMARK_INBOUND_SECRET is set.

    If POSTMARK_INBOUND_SECRET is not set in env, the route is unconfigured
    and returns 503.
    """
    expected = os.environ.get("POSTMARK_INBOUND_SECRET")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="POSTMARK_INBOUND_SECRET not configured",
        )

    provided = None

    if authorization and authorization.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(authorization[6:].strip()).decode("utf-8")
            if ":" in decoded:
                provided = decoded.split(":", 1)[1]
            else:
                provided = decoded
        except (ValueError, UnicodeDecodeError):
            provided = None

    if not provided and inbound_token:
        provided = inbound_token.strip()

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing Postmark inbound credentials",
        )

    if not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid Postmark inbound credentials",
        )


def _steward_enabled() -> bool:
    """Read STEWARD_ENABLED env var; default true (staging-friendly).

    Production sets STEWARD_ENABLED=false manually until Kyle approves the
    Session 8 staging soak. See parking lot [PRE Q10].
    """
    raw = os.environ.get("STEWARD_ENABLED", "true").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _extract_postmark_message_id(payload: dict) -> str:
    """Pull the Postmark MessageID from the payload, with a fallback."""
    candidate = payload.get("MessageID") or payload.get("MessageId")
    if candidate:
        return str(candidate)
    headers = payload.get("Headers") or []
    if isinstance(headers, list):
        for h in headers:
            if isinstance(h, dict) and h.get("Name", "").lower() == "message-id":
                return str(h.get("Value", ""))
    return f"unknown-{uuid.uuid4().hex[:12]}"


def _extract_in_reply_to(payload: dict) -> Optional[str]:
    """Pull the In-Reply-To header from the payload, if present."""
    direct = payload.get("InReplyTo") or payload.get("InReplyToMessageId")
    if direct:
        return str(direct)
    headers = payload.get("Headers") or []
    if isinstance(headers, list):
        for h in headers:
            if isinstance(h, dict) and h.get("Name", "").lower() == "in-reply-to":
                return str(h.get("Value", ""))
    return None


def _existing_inbound_id_for_message(postmark_message_id: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT inbound_id FROM inbound_emails WHERE postmark_message_id = ?",
            (postmark_message_id,),
        ).fetchone()
    return row["inbound_id"] if row else None


def _insert_inbound_row(payload: dict) -> str:
    """Insert a row into inbound_emails. Idempotent on postmark_message_id.

    Returns the inbound_id (existing or new).
    """
    postmark_message_id = _extract_postmark_message_id(payload)
    existing = _existing_inbound_id_for_message(postmark_message_id)
    if existing:
        logger.info(
            "inbound dedupe — postmark_message_id=%s already stored as inbound_id=%s",
            postmark_message_id,
            existing,
        )
        return existing

    inbound_id = _new_inbound_id()
    now = _now()
    raw_json = json.dumps(payload, default=str)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO inbound_emails (
                inbound_id, postmark_message_id, from_email, from_name,
                to_email, subject, text_body, html_body, in_reply_to,
                raw_payload_json, matched_lead_id, classification,
                send_tier, received_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                inbound_id,
                postmark_message_id,
                str(payload.get("From", "") or ""),
                payload.get("FromName"),
                str(payload.get("To", "") or ""),
                payload.get("Subject"),
                payload.get("TextBody"),
                payload.get("HtmlBody"),
                _extract_in_reply_to(payload),
                raw_json,
                now,
            ),
        )
    return inbound_id


@router.post("/api/inbound")
async def postmark_inbound(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
    x_postmark_inbound_token: Annotated[Optional[str], Header(alias="X-Postmark-Inbound-Token")] = None,
) -> dict[str, Any]:
    """Postmark inbound webhook — Session 1 stub.

    Validates the shared secret, hard-fails on any CHDB address, writes the
    raw payload to inbound_emails for audit, and returns 200. Sessions 3-4
    add classification, Aemon review, and outbox routing.
    """
    _verify_postmark_secret(authorization, x_postmark_inbound_token)

    try:
        payload = await request.json()
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("inbound webhook received non-JSON payload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid JSON payload",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="payload must be a JSON object",
        )

    try:
        enforce_inbound(payload)
    except ChdbSeparationViolation as exc:
        logger.warning("inbound rejected by CHDB enforcement: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    inbound_id = _insert_inbound_row(payload)

    if not _steward_enabled():
        return {
            "status": "logged",
            "inbound_id": inbound_id,
            "steward_enabled": False,
        }

    return {
        "status": "logged",
        "inbound_id": inbound_id,
        "steward_enabled": True,
    }
