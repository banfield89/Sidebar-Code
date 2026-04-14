"""Tests for /success and /cancel HTML pages."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import pages
from api.main import app

client = TestClient(app)


def test_success_page_with_no_session_id_returns_generic_thank_you() -> None:
    response = client.get("/success")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Thank you" in response.text
    assert "kyle@sidebarcode.com" in response.text


def test_success_page_with_session_id_renders_zip_download_copy(monkeypatch) -> None:
    monkeypatch.setattr(
        pages,
        "_safe_stripe_session_lookup",
        lambda sid: {
            "tier_id": "mock_parser_trial",
            "delivery_type": "zip_download",
            "buyer_email": "buyer@example.com",
            "amount_total": 197,
            "currency": "usd",
        },
    )
    response = client.get("/success?session_id=cs_test_zip")
    assert response.status_code == 200
    body = response.text
    assert "download is on its way" in body
    assert "buyer@example.com" in body
    assert "Mock Parser Trial" in body
    assert "$1.97 USD" in body
    assert "72 hours" in body
    assert "spam folder" in body


def test_success_page_with_session_id_renders_notify_kyle_copy(monkeypatch) -> None:
    monkeypatch.setattr(
        pages,
        "_safe_stripe_session_lookup",
        lambda sid: {
            "tier_id": "mock_consulting_foundation",
            "delivery_type": "notify_kyle",
            "buyer_email": "consulting@example.com",
            "amount_total": 2500,
            "currency": "usd",
        },
    )
    response = client.get("/success?session_id=cs_test_consulting")
    assert response.status_code == 200
    body = response.text
    assert "Kyle will be in touch" in body
    assert "one business day" in body
    assert "consulting@example.com" in body
    assert "Mock Consulting Foundation" in body
    assert "$25.00 USD" in body
    assert "cal.com" in body  # scheduling link from mock catalog


def test_success_page_handles_stripe_lookup_failure_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(pages, "_safe_stripe_session_lookup", lambda sid: None)
    response = client.get("/success?session_id=cs_test_broken")
    assert response.status_code == 200
    body = response.text
    assert "Thank you" in body
    assert "spam folder" in body  # generic fallback copy


def test_success_page_unknown_delivery_type_falls_back_to_generic(monkeypatch) -> None:
    monkeypatch.setattr(
        pages,
        "_safe_stripe_session_lookup",
        lambda sid: {
            "tier_id": "unknown",
            "delivery_type": "unknown",
            "buyer_email": "edge@example.com",
            "amount_total": 100,
            "currency": "usd",
        },
    )
    response = client.get("/success?session_id=cs_test_edge")
    assert response.status_code == 200
    assert "Thank you" in response.text


def test_cancel_page_renders() -> None:
    response = client.get("/cancel")
    assert response.status_code == 200
    body = response.text
    assert "no charge was made" in body.lower()
    assert "kyle@sidebarcode.com" in body
    assert "sidebarcode.com" in body


def test_cancel_page_has_no_external_dependencies() -> None:
    """Cancel page must work even if Stripe / Postmark / SQLite are all down."""
    response = client.get("/cancel")
    assert response.status_code == 200
