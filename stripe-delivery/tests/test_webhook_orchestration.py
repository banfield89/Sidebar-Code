"""Tests that exercise the full webhook → crm → delivery stub orchestration.

Builds on Session 5's signature-construction helpers but targets the
Session 6 work: a checkout.session.completed event should land a purchase
row in SQLite, and a charge.refunded should mark it refunded and call
delete_r2_object.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import crm, db as db_module, delivery
from api.main import app

WEBHOOK_SECRET = "whsec_orchestration_test_secret"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "orch_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


client = TestClient(app)


def _sign(payload: bytes) -> str:
    ts = int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _make_session_event(
    event_id: str,
    tier_id: str,
    delivery_type: str,
    session_id: str = "cs_test_orch_001",
    payment_intent: str = "pi_test_orch_001",
    amount: int = 197,
) -> bytes:
    event = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "api_version": "2024-06-20",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_intent": payment_intent,
                "amount_total": amount,
                "currency": "usd",
                "customer_details": {
                    "email": "buyer@example.com",
                    "name": "Test Buyer",
                    "phone": "+15555550100",
                },
                "metadata": {
                    "tier_id": tier_id,
                    "delivery_type": delivery_type,
                    "tos_version_hash": "abc123def456",
                    "tech_overview_version_hash": "def456abc789",
                    "buyer_ip": "1.2.3.4",
                },
            }
        },
        "livemode": False,
        "pending_webhooks": 0,
        "request": {"id": None, "idempotency_key": None},
    }
    return json.dumps(event).encode()


def _make_refund_event(
    event_id: str,
    charge_id: str = "ch_test_orch_001",
    payment_intent: str = "pi_test_orch_001",
) -> bytes:
    event = {
        "id": event_id,
        "object": "event",
        "type": "charge.refunded",
        "api_version": "2024-06-20",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": charge_id,
                "object": "charge",
                "payment_intent": payment_intent,
                "amount_refunded": 197,
            }
        },
        "livemode": False,
        "pending_webhooks": 0,
        "request": {"id": None, "idempotency_key": None},
    }
    return json.dumps(event).encode()


# ---------------------------------------------------------------------------
# checkout.session.completed → zip_download branch
# ---------------------------------------------------------------------------
def test_checkout_completed_zip_branch_writes_purchase(monkeypatch) -> None:
    deliver_mock = MagicMock()
    monkeypatch.setattr(delivery, "build_and_deliver_zip", deliver_mock)

    payload = _make_session_event(
        event_id="evt_orch_zip",
        tier_id="mock_parser_trial",
        delivery_type="zip_download",
        session_id="cs_test_zip_orch",
    )
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )
    assert response.status_code == 200

    purchase = crm.get_purchase_by_session_id("cs_test_zip_orch")
    assert purchase is not None
    assert purchase.tier_id == "mock_parser_trial"
    assert purchase.delivery_type == "zip_download"
    assert purchase.buyer_email == "buyer@example.com"
    assert purchase.buyer_name == "Test Buyer"
    assert purchase.buyer_phone == "+15555550100"
    assert purchase.amount_cents == 197
    assert purchase.tos_version_hash == "abc123def456"
    assert purchase.buyer_ip == "1.2.3.4"
    assert purchase.status == "awaiting_delivery"

    deliver_mock.assert_called_once()
    delivered_purchase = deliver_mock.call_args.args[0]
    assert delivered_purchase.purchase_id == purchase.purchase_id


# ---------------------------------------------------------------------------
# checkout.session.completed → notify_kyle branch
# ---------------------------------------------------------------------------
def test_checkout_completed_notify_branch_writes_purchase_and_lead(monkeypatch) -> None:
    notify_mock = MagicMock()
    monkeypatch.setattr(delivery, "notify_kyle_new_purchase", notify_mock)

    payload = _make_session_event(
        event_id="evt_orch_notify",
        tier_id="mock_consulting_foundation",
        delivery_type="notify_kyle",
        session_id="cs_test_notify_orch",
        amount=2500,
    )
    response = client.post(
        "/api/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )
    assert response.status_code == 200

    purchase = crm.get_purchase_by_session_id("cs_test_notify_orch")
    assert purchase is not None
    assert purchase.delivery_type == "notify_kyle"
    assert purchase.amount_cents == 2500
    assert purchase.status == "awaiting_delivery"

    # Lead row should also exist for consulting tiers.
    with db_module.get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM leads WHERE buyer_email = ?", ("buyer@example.com",)
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "qualified"
    assert rows[0]["source"] == "stripe_purchase"
    assert rows[0]["amount_cents"] == 2500

    # Lead event row should record the creation.
    with db_module.get_connection() as conn:
        events = conn.execute(
            "SELECT * FROM lead_events WHERE lead_id = ?", (rows[0]["lead_id"],)
        ).fetchall()
    assert len(events) >= 1
    assert events[0]["event_type"] == "created"

    notify_mock.assert_called_once()


def test_checkout_completed_idempotent_replay(monkeypatch) -> None:
    """Replaying the same event should not create duplicate purchases."""
    monkeypatch.setattr(delivery, "build_and_deliver_zip", MagicMock())

    payload = _make_session_event(
        event_id="evt_orch_replay",
        tier_id="mock_parser_trial",
        delivery_type="zip_download",
        session_id="cs_test_replay",
    )
    headers = {"stripe-signature": _sign(payload)}

    r1 = client.post("/api/webhook", content=payload, headers=headers)
    r2 = client.post("/api/webhook", content=payload, headers=headers)
    assert r1.status_code == 200
    assert r2.status_code == 200

    with db_module.get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM purchases WHERE stripe_session_id = ?", ("cs_test_replay",)
        ).fetchall()
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# charge.refunded handler
# ---------------------------------------------------------------------------
def test_refund_sets_status_refunded(monkeypatch) -> None:
    """Refund handler should mark the matching purchase as refunded."""
    monkeypatch.setattr(delivery, "build_and_deliver_zip", MagicMock())
    monkeypatch.setattr(delivery, "delete_r2_object", MagicMock())
    monkeypatch.setattr(delivery, "notify_kyle_refund", MagicMock())

    # First insert the purchase via a checkout event.
    checkout_payload = _make_session_event(
        event_id="evt_for_refund",
        tier_id="mock_parser_trial",
        delivery_type="zip_download",
        session_id="cs_test_for_refund",
        payment_intent="pi_test_for_refund",
    )
    client.post(
        "/api/webhook",
        content=checkout_payload,
        headers={"stripe-signature": _sign(checkout_payload)},
    )

    # Now fire the refund.
    refund_payload = _make_refund_event(
        event_id="evt_refund_001",
        charge_id="ch_test_refund_001",
        payment_intent="pi_test_for_refund",
    )
    response = client.post(
        "/api/webhook",
        content=refund_payload,
        headers={"stripe-signature": _sign(refund_payload)},
    )
    assert response.status_code == 200

    purchase = crm.get_purchase_by_session_id("cs_test_for_refund")
    assert purchase is not None
    assert purchase.status == "refunded"
    assert purchase.download_url_expires_at is not None


def test_refund_calls_delete_r2_object_when_zip_key_present(monkeypatch) -> None:
    monkeypatch.setattr(delivery, "build_and_deliver_zip", MagicMock())
    delete_mock = MagicMock()
    monkeypatch.setattr(delivery, "delete_r2_object", delete_mock)
    monkeypatch.setattr(delivery, "notify_kyle_refund", MagicMock())

    # Insert a purchase and pretend delivery completed.
    checkout_payload = _make_session_event(
        event_id="evt_for_refund_with_key",
        tier_id="mock_parser_trial",
        delivery_type="zip_download",
        session_id="cs_test_with_key",
        payment_intent="pi_test_with_key",
    )
    client.post(
        "/api/webhook",
        content=checkout_payload,
        headers={"stripe-signature": _sign(checkout_payload)},
    )
    purchase = crm.get_purchase_by_session_id("cs_test_with_key")
    crm.update_purchase_status(
        purchase.purchase_id,
        crm.PurchaseStatus.DELIVERED,
        zip_object_key="mock_parser_trial/cs_test_with_key.zip",
        stripe_charge_id="ch_test_with_key",
    )

    refund_payload = _make_refund_event(
        event_id="evt_refund_with_key",
        charge_id="ch_test_with_key",
        payment_intent="pi_test_with_key",
    )
    client.post(
        "/api/webhook",
        content=refund_payload,
        headers={"stripe-signature": _sign(refund_payload)},
    )

    delete_mock.assert_called_once_with("mock_parser_trial/cs_test_with_key.zip")


def test_refund_for_unknown_charge_logs_warning_does_not_500(monkeypatch) -> None:
    monkeypatch.setattr(delivery, "delete_r2_object", MagicMock())
    monkeypatch.setattr(delivery, "notify_kyle_refund", MagicMock())

    refund_payload = _make_refund_event(
        event_id="evt_refund_orphan",
        charge_id="ch_orphan_no_purchase",
        payment_intent="pi_orphan_no_purchase",
    )
    response = client.post(
        "/api/webhook",
        content=refund_payload,
        headers={"stripe-signature": _sign(refund_payload)},
    )
    # Should still 200 (no purchase to update) — Stripe should NOT retry.
    assert response.status_code == 200
