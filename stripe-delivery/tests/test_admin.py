"""Tests for api/admin.py — Session 8 admin dashboard + resend action."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import crm, db as db_module, delivery
from api.main import app


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "admin_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("ADMIN_USER", "kyle")
    monkeypatch.setenv("ADMIN_PASSWORD", "test_pw_123")
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


client = TestClient(app)
AUTH = ("kyle", "test_pw_123")


def _seed_purchases() -> list[crm.Purchase]:
    rows = [
        crm.insert_purchase(
            tier_id="mock_parser_trial",
            category="products",
            delivery_type="zip_download",
            stripe_session_id="cs_admin_001",
            buyer_email="alice@example.com",
            buyer_name="Alice",
            amount_cents=197,
            currency="usd",
            status=crm.PurchaseStatus.DELIVERED,
        ),
        crm.insert_purchase(
            tier_id="mock_consulting_foundation",
            category="consulting",
            delivery_type="notify_kyle",
            stripe_session_id="cs_admin_002",
            buyer_email="bob@example.com",
            buyer_name="Bob",
            amount_cents=2500,
            currency="usd",
            status=crm.PurchaseStatus.AWAITING_DELIVERY,
        ),
    ]
    return rows


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def test_admin_dashboard_requires_auth() -> None:
    response = client.get("/admin/sales")
    assert response.status_code == 401


def test_admin_dashboard_rejects_wrong_password() -> None:
    response = client.get("/admin/sales", auth=("kyle", "wrong_password"))
    assert response.status_code == 401


def test_admin_dashboard_503_when_admin_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_USER", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    response = client.get("/admin/sales", auth=("kyle", "test_pw_123"))
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# Dashboard rendering
# ---------------------------------------------------------------------------
def test_admin_dashboard_lists_recent_purchases() -> None:
    _seed_purchases()
    response = client.get("/admin/sales", auth=AUTH)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "alice@example.com" in body
    assert "bob@example.com" in body
    assert "mock_parser_trial" in body
    assert "mock_consulting_foundation" in body
    assert "$1.97" in body
    assert "$25.00" in body
    assert "delivered" in body
    assert "awaiting_delivery" in body


def test_admin_dashboard_shows_pending_consulting_leads() -> None:
    crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="charlie@example.com",
        buyer_name="Charlie",
        stripe_charge_id="ch_admin_001",
        amount_cents=2500,
    )
    response = client.get("/admin/sales", auth=AUTH)
    assert response.status_code == 200
    assert "charlie@example.com" in response.text
    assert "Charlie" in response.text


def test_admin_dashboard_hides_followed_up_leads() -> None:
    lead = crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="dave@example.com",
        stripe_charge_id="ch_admin_002",
    )
    crm.record_lead_event(lead.lead_id, "contacted", {"by": "kyle"})
    response = client.get("/admin/sales", auth=AUTH)
    assert "dave@example.com" not in response.text


def test_admin_dashboard_shows_failed_deliveries() -> None:
    purchase = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_failed_001",
        buyer_email="failed@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.FAILED,
    )
    crm.record_delivery_failure(
        purchase.purchase_id,
        error_msg="R2 was down at the time",
        traceback="(no traceback)",
    )
    response = client.get("/admin/sales", auth=AUTH)
    assert response.status_code == 200
    assert "failed@example.com" in response.text
    assert "R2 was down" in response.text
    assert "Resend" in response.text


# ---------------------------------------------------------------------------
# Resend action
# ---------------------------------------------------------------------------
def test_resend_action_creates_new_signed_url(monkeypatch) -> None:
    deliver_mock = MagicMock()
    monkeypatch.setattr(delivery, "build_and_deliver_zip", deliver_mock)

    purchase = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_resend_001",
        buyer_email="resend@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.FAILED,
    )

    response = client.post(
        f"/admin/sales/resend/{purchase.purchase_id}",
        auth=AUTH,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/sales"
    deliver_mock.assert_called_once()
    delivered_purchase = deliver_mock.call_args.args[0]
    assert delivered_purchase.purchase_id == purchase.purchase_id


def test_resend_action_404_for_unknown_purchase() -> None:
    response = client.post(
        "/admin/sales/resend/pur_does_not_exist",
        auth=AUTH,
        follow_redirects=False,
    )
    assert response.status_code == 404


def test_resend_action_requires_auth() -> None:
    response = client.post(
        "/admin/sales/resend/pur_anything",
        follow_redirects=False,
    )
    assert response.status_code == 401
