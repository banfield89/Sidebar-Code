"""Tests for api/crm.py — Session 6 scope."""

from __future__ import annotations

from pathlib import Path

import pytest

from api import crm, db as db_module


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "crm_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------
def test_purchase_insert_and_fetch() -> None:
    purchase = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_test_unit_001",
        stripe_payment_intent_id="pi_test_001",
        buyer_email="buyer@example.com",
        buyer_name="Test Buyer",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.AWAITING_DELIVERY,
    )
    assert purchase.purchase_id.startswith("pur_")
    assert purchase.tier_id == "mock_parser_trial"
    assert purchase.status == "awaiting_delivery"

    fetched = crm.get_purchase_by_session_id("cs_test_unit_001")
    assert fetched is not None
    assert fetched.purchase_id == purchase.purchase_id
    assert fetched.buyer_email == "buyer@example.com"


def test_purchase_insert_idempotent_on_session_id() -> None:
    p1 = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_test_dup",
        buyer_email="buyer@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.AWAITING_DELIVERY,
    )
    p2 = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_test_dup",
        buyer_email="buyer@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.AWAITING_DELIVERY,
    )
    assert p1.purchase_id == p2.purchase_id


def test_get_purchase_by_charge_id_returns_none_when_absent() -> None:
    assert crm.get_purchase_by_charge_id("ch_does_not_exist") is None


def test_update_purchase_status_changes_status_and_updated_at() -> None:
    purchase = crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_test_status",
        buyer_email="buyer@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.AWAITING_DELIVERY,
    )
    crm.update_purchase_status(
        purchase.purchase_id,
        crm.PurchaseStatus.DELIVERED,
        zip_object_key="some/key.zip",
        stripe_charge_id="ch_test_001",
    )
    refreshed = crm.get_purchase_by_id(purchase.purchase_id)
    assert refreshed is not None
    assert refreshed.status == "delivered"
    assert refreshed.zip_object_key == "some/key.zip"
    assert refreshed.stripe_charge_id == "ch_test_001"
    assert refreshed.updated_at >= purchase.updated_at


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------
def test_lead_insert_and_fetch() -> None:
    lead = crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="lead@example.com",
        buyer_name="Test Lead",
        stripe_charge_id="ch_test_lead_001",
        amount_cents=2500,
    )
    assert lead.lead_id.startswith("lead_")
    assert lead.status == "qualified"  # default for stripe-sourced

    fetched = crm.get_lead(lead.lead_id)
    assert fetched is not None
    assert fetched.buyer_email == "lead@example.com"

    by_charge = crm.get_lead_by_charge_id("ch_test_lead_001")
    assert by_charge is not None
    assert by_charge.lead_id == lead.lead_id


def test_lead_insert_idempotent_on_charge_id() -> None:
    l1 = crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="lead@example.com",
        stripe_charge_id="ch_test_lead_dup",
    )
    l2 = crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="lead@example.com",
        stripe_charge_id="ch_test_lead_dup",
    )
    assert l1.lead_id == l2.lead_id


def test_record_lead_event_persists_row() -> None:
    lead = crm.insert_lead(
        tier_id="mock_consulting_foundation",
        source="stripe_purchase",
        buyer_email="event@example.com",
        stripe_charge_id="ch_event_001",
    )
    event_id = crm.record_lead_event(lead.lead_id, "created", {"source": "test"})
    assert event_id.startswith("levt_")

    with db_module.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM lead_events WHERE event_id = ?", (event_id,)
        ).fetchone()
    assert row is not None
    assert row["lead_id"] == lead.lead_id
    assert row["event_type"] == "created"
