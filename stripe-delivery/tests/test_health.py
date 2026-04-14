"""Smoke tests for /health, /api/checkout, /api/webhook stubs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload
    assert "env" in payload


def test_checkout_validates_body() -> None:
    """Checkout is implemented in Session 4. Empty body should now 422."""
    response = client.post("/api/checkout", json={})
    assert response.status_code == 422


def test_webhook_returns_501() -> None:
    response = client.post("/api/webhook", content=b"{}")
    assert response.status_code == 501
    assert "not yet implemented" in response.json()["detail"].lower()
