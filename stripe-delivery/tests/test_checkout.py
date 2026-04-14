"""Tests for api/checkout.py — Session 4 scope.

Unit tests use FastAPI's TestClient and monkeypatch the `stripe` module
so no live Stripe calls are made. Integration tests are gated on
STRIPE_SECRET_KEY presence and run locally only.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import checkout as checkout_module
from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    """Each test starts with a clean catalog cache and a stub Stripe key."""
    checkout_module.reset_catalog_cache()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_unit_test_placeholder")
    import stripe
    monkeypatch.setattr(stripe, "api_key", "sk_test_unit_test_placeholder")
    yield
    checkout_module.reset_catalog_cache()


def _valid_payload(tier_id: str = "mock_parser_trial") -> dict:
    return {
        "tier_id": tier_id,
        "tos_accepted": True,
        "tech_overview_accepted": True,
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_checkout_requires_tos() -> None:
    payload = _valid_payload()
    payload["tos_accepted"] = False
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 422
    assert "tos" in response.json()["detail"].lower()


def test_checkout_requires_tech_overview() -> None:
    payload = _valid_payload()
    payload["tech_overview_accepted"] = False
    response = client.post("/api/checkout", json=payload)
    assert response.status_code == 422
    assert "technology overview" in response.json()["detail"].lower()


def test_checkout_unknown_tier_returns_404(monkeypatch) -> None:
    response = client.post("/api/checkout", json=_valid_payload("not_a_real_tier"))
    assert response.status_code == 404


def test_checkout_missing_fields_returns_422() -> None:
    response = client.post("/api/checkout", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Stripe call shape (mocked)
# ---------------------------------------------------------------------------
def test_checkout_creates_session_with_metadata(monkeypatch) -> None:
    fake_session = SimpleNamespace(
        id="cs_test_unit_abc123",
        url="https://checkout.stripe.com/c/pay/cs_test_unit_abc123",
    )
    create_mock = MagicMock(return_value=fake_session)

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "create", create_mock)

    response = client.post("/api/checkout", json=_valid_payload("mock_parser_trial"))
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "cs_test_unit_abc123"
    assert body["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_test_unit_abc123"

    create_mock.assert_called_once()
    kwargs = create_mock.call_args.kwargs
    assert kwargs["mode"] == "payment"

    line_items = kwargs["line_items"]
    assert len(line_items) == 1
    assert line_items[0]["quantity"] == 1
    assert line_items[0]["price_data"]["unit_amount"] == 197
    assert line_items[0]["price_data"]["currency"] == "usd"
    assert line_items[0]["price_data"]["product_data"]["metadata"]["tier_id"] == "mock_parser_trial"

    metadata = kwargs["metadata"]
    assert metadata["tier_id"] == "mock_parser_trial"
    assert metadata["delivery_type"] == "zip_download"
    assert metadata["category"] == "products"
    assert "tos_accepted_at" in metadata
    assert "tos_version_hash" in metadata
    assert "tech_overview_accepted_at" in metadata
    assert "tech_overview_version_hash" in metadata
    assert "buyer_ip" in metadata


def test_checkout_consulting_tier_creates_session_with_notify_kyle_metadata(monkeypatch) -> None:
    fake_session = SimpleNamespace(
        id="cs_test_unit_consulting",
        url="https://checkout.stripe.com/c/pay/cs_test_unit_consulting",
    )
    create_mock = MagicMock(return_value=fake_session)

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "create", create_mock)

    response = client.post("/api/checkout", json=_valid_payload("mock_consulting_foundation"))
    assert response.status_code == 200

    kwargs = create_mock.call_args.kwargs
    assert kwargs["metadata"]["delivery_type"] == "notify_kyle"
    assert kwargs["metadata"]["category"] == "consulting"
    assert kwargs["line_items"][0]["price_data"]["unit_amount"] == 2500


def test_checkout_collects_phone_number(monkeypatch) -> None:
    fake_session = SimpleNamespace(id="cs_test", url="https://checkout.stripe.com/c/pay/cs_test")
    create_mock = MagicMock(return_value=fake_session)

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "create", create_mock)

    client.post("/api/checkout", json=_valid_payload())
    kwargs = create_mock.call_args.kwargs
    assert kwargs["phone_number_collection"] == {"enabled": True}


# ---------------------------------------------------------------------------
# GET /api/session/{id}
# ---------------------------------------------------------------------------
def test_session_get_returns_tier_info(monkeypatch) -> None:
    fake_session = {
        "id": "cs_test_lookup",
        "metadata": {
            "tier_id": "mock_parser_trial",
            "delivery_type": "zip_download",
        },
        "amount_total": 197,
        "currency": "usd",
        "status": "complete",
    }
    retrieve_mock = MagicMock(return_value=fake_session)

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "retrieve", retrieve_mock)

    response = client.get("/api/session/cs_test_lookup")
    assert response.status_code == 200
    body = response.json()
    assert body["tier_id"] == "mock_parser_trial"
    assert body["delivery_type"] == "zip_download"
    assert body["amount"] == 197
    assert body["currency"] == "usd"
    assert body["status"] == "complete"

    retrieve_mock.assert_called_once_with("cs_test_lookup")
