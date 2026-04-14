"""Tests for api/inbound.py — Postmark inbound webhook stub (Session 1).

Session 1 scope: validate the shared secret, hard-fail on any CHDB address,
write the raw payload to inbound_emails for audit, return 200. Sessions 3-4
add classification, Aemon review, and outbox routing.

These tests cover the secret validation (both basic-auth and header form),
CHDB enforcement at the route boundary, the inbound_emails row insertion,
idempotency on Postmark MessageID, and the Steward enabled flag.
"""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from api.db import get_connection
from api.main import app

client = TestClient(app)

INBOUND_SECRET = "test-inbound-secret-32-chars-aaaa"


def _basic_auth_header(secret: str = INBOUND_SECRET, user: str = "postmark") -> dict[str, str]:
    token = base64.b64encode(f"{user}:{secret}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _token_header(secret: str = INBOUND_SECRET) -> dict[str, str]:
    return {"X-Postmark-Inbound-Token": secret}


def _clean_payload(message_id: str = "<msg-aaa-001@example.com>") -> dict:
    return {
        "From": "buyer@example.com",
        "FromName": "Test Buyer",
        "To": "kyle@sidebarcode.com",
        "Subject": "Question about Foundation tier",
        "TextBody": "Hi Kyle, can you tell me what is included?",
        "HtmlBody": "<p>Hi Kyle, can you tell me what is included?</p>",
        "MessageID": message_id,
        "Headers": [
            {"Name": "Message-ID", "Value": message_id},
            {"Name": "Date", "Value": "Mon, 13 Apr 2026 12:00:00 -0700"},
        ],
    }


# ---------------------------------------------------------------------------
# Configuration / 503 path
# ---------------------------------------------------------------------------
def test_inbound_503_when_secret_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("POSTMARK_INBOUND_SECRET", raising=False)
    response = client.post("/api/inbound", json=_clean_payload(), headers=_token_header())
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# 401 paths — missing or invalid credentials
# ---------------------------------------------------------------------------
def test_inbound_rejects_missing_token(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    response = client.post("/api/inbound", json=_clean_payload())
    assert response.status_code == 401


def test_inbound_rejects_invalid_token(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    response = client.post(
        "/api/inbound",
        json=_clean_payload(),
        headers={"X-Postmark-Inbound-Token": "wrong-secret"},
    )
    assert response.status_code == 401


def test_inbound_rejects_invalid_basic_auth(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    bad = base64.b64encode(b"postmark:wrong-secret").decode()
    response = client.post(
        "/api/inbound",
        json=_clean_payload(),
        headers={"Authorization": f"Basic {bad}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Happy paths — valid credentials and clean payload
# ---------------------------------------------------------------------------
def test_inbound_accepts_valid_token(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-token-001@example.com>")
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "logged"
    assert body["inbound_id"].startswith("in_")


def test_inbound_accepts_valid_basic_auth(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-basic-001@example.com>")
    response = client.post("/api/inbound", json=payload, headers=_basic_auth_header())
    assert response.status_code == 200
    assert response.json()["status"] == "logged"


def test_inbound_writes_row(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-write-001@example.com>")
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 200
    inbound_id = response.json()["inbound_id"]

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM inbound_emails WHERE inbound_id = ?", (inbound_id,)
        ).fetchone()
    assert row is not None
    assert row["postmark_message_id"] == "<msg-write-001@example.com>"
    assert row["from_email"] == "buyer@example.com"
    assert row["to_email"] == "kyle@sidebarcode.com"
    assert row["subject"] == "Question about Foundation tier"


def test_inbound_dedupes_on_postmark_message_id(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-dupe-001@example.com>")
    first = client.post("/api/inbound", json=payload, headers=_token_header())
    second = client.post("/api/inbound", json=payload, headers=_token_header())
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["inbound_id"] == second.json()["inbound_id"]

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT COUNT(*) AS n FROM inbound_emails WHERE postmark_message_id = ?",
            ("<msg-dupe-001@example.com>",),
        ).fetchone()
    assert rows["n"] == 1


# ---------------------------------------------------------------------------
# 422 paths — CHDB enforcement
# ---------------------------------------------------------------------------
def test_inbound_rejects_chdb_in_from(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-chdb-from@example.com>")
    payload["From"] = "kyle@chdblaw.com"
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 422
    assert "chdb" in response.json()["detail"].lower() or "CHDB" in response.json()["detail"]


def test_inbound_rejects_chdb_in_to(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-chdb-to@example.com>")
    payload["To"] = "kyle@chdblaw.com"
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 422


def test_inbound_rejects_chdb_in_cc(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-chdb-cc@example.com>")
    payload["Cc"] = "associate@chdblaw.com"
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 422


def test_inbound_rejects_chdb_anywhere_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-chdb-headers@example.com>")
    payload["Headers"].append(
        {"Name": "X-Forward", "Value": "via KYLE@CHDBLAW.COM"}
    )
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 422


def test_inbound_rejects_chdb_does_not_write_row(monkeypatch) -> None:
    """CHDB enforcement runs BEFORE the row is inserted."""
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    payload = _clean_payload("<msg-chdb-noinsert@example.com>")
    payload["From"] = "kyle@chdblaw.com"
    client.post("/api/inbound", json=payload, headers=_token_header())

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM inbound_emails WHERE postmark_message_id = ?",
            ("<msg-chdb-noinsert@example.com>",),
        ).fetchone()
    assert row is None


# ---------------------------------------------------------------------------
# 422 paths — bad payload shape
# ---------------------------------------------------------------------------
def test_inbound_rejects_non_object_payload(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    response = client.post("/api/inbound", json=["not", "an", "object"], headers=_token_header())
    assert response.status_code == 422


def test_inbound_rejects_non_json_payload(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    response = client.post(
        "/api/inbound",
        content=b"not json at all",
        headers={**_token_header(), "Content-Type": "application/json"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Steward enabled flag
# ---------------------------------------------------------------------------
def test_inbound_logs_when_steward_disabled(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    monkeypatch.setenv("STEWARD_ENABLED", "false")
    payload = _clean_payload("<msg-disabled-001@example.com>")
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 200
    body = response.json()
    assert body["steward_enabled"] is False
    assert body["status"] == "logged"


def test_inbound_steward_enabled_default_true(monkeypatch) -> None:
    monkeypatch.setenv("POSTMARK_INBOUND_SECRET", INBOUND_SECRET)
    monkeypatch.delenv("STEWARD_ENABLED", raising=False)
    payload = _clean_payload("<msg-enabled-001@example.com>")
    response = client.post("/api/inbound", json=payload, headers=_token_header())
    assert response.status_code == 200
    assert response.json()["steward_enabled"] is True
