"""Tests for api/webhook.py — Session 5 scope.

Constructs real Stripe signatures using the documented HMAC-SHA256 scheme
so we can exercise the full verify -> dispatch -> log -> idempotency path
without hitting Stripe's API.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api import db as db_module
from api.main import app

WEBHOOK_SECRET = "whsec_test_unit_placeholder_secret_value"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    """Each test gets a fresh SQLite file in tmp_path."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


client = TestClient(app)


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET, timestamp: int | None = None) -> str:
    """Build a valid Stripe-Signature header for `payload`."""
    ts = timestamp or int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _make_event(
    event_id: str = "evt_test_001",
    event_type: str = "checkout.session.completed",
    object_data: dict[str, Any] | None = None,
) -> bytes:
    """Build a minimal Stripe event payload."""
    obj = object_data or {
        "id": "cs_test_session_001",
        "object": "checkout.session",
        "metadata": {"tier_id": "mock_parser_trial", "delivery_type": "zip_download"},
    }
    event = {
        "id": event_id,
        "object": "event",
        "type": event_type,
        "api_version": "2024-06-20",
        "created": int(time.time()),
        "data": {"object": obj},
        "livemode": False,
        "pending_webhooks": 0,
        "request": {"id": None, "idempotency_key": None},
    }
    return json.dumps(event).encode()


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------
def test_webhook_rejects_bad_signature() -> None:
    payload = _make_event()
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": "t=1234567890,v1=deadbeef"},
    )
    assert response.status_code == 400


def test_webhook_rejects_missing_signature_header() -> None:
    payload = _make_event()
    response = client.post("/api/webhook", content=payload)
    assert response.status_code == 400


def test_webhook_accepts_good_signature() -> None:
    payload = _make_event(event_id="evt_test_good_sig")
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["event_id"] == "evt_test_good_sig"
    assert body["event_type"] == "checkout.session.completed"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------
def test_webhook_idempotent_same_event_twice() -> None:
    payload = _make_event(event_id="evt_test_idempotency")
    headers = {"stripe-signature": _sign(payload)}

    # First delivery — processed.
    r1 = client.post("/api/webhook", content=payload, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed"

    # Second delivery — short-circuited as duplicate.
    r2 = client.post("/api/webhook", content=payload, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "event_type,object_data",
    [
        (
            "checkout.session.completed",
            {"id": "cs_test_001", "object": "checkout.session", "metadata": {"tier_id": "mock_parser_trial"}},
        ),
        ("charge.refunded", {"id": "ch_test_001", "object": "charge"}),
        ("charge.dispute.created", {"id": "dp_test_001", "object": "dispute", "status": "needs_response"}),
        ("charge.dispute.closed", {"id": "dp_test_002", "object": "dispute", "status": "won"}),
    ],
)
def test_webhook_routes_events_correctly(event_type: str, object_data: dict[str, Any]) -> None:
    payload = _make_event(
        event_id=f"evt_route_{event_type.replace('.', '_')}",
        event_type=event_type,
        object_data=object_data,
    )
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert response.json()["event_type"] == event_type


def test_webhook_unhandled_event_type_marked_processed() -> None:
    """Events we don't have a handler for should still be marked processed
    so Stripe doesn't keep retrying them."""
    payload = _make_event(
        event_id="evt_unknown_type",
        event_type="invoice.paid",
        object_data={"id": "in_test_001", "object": "invoice"},
    )
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


# ---------------------------------------------------------------------------
# Debug log persistence
# ---------------------------------------------------------------------------
def test_webhook_writes_debug_log_row() -> None:
    payload = _make_event(event_id="evt_debug_log")
    client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )

    with db_module.get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM webhook_debug_log WHERE stripe_event_id = ?",
            ("evt_debug_log",),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["event_type"] == "checkout.session.completed"
