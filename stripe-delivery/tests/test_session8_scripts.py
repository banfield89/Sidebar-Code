"""Tests for Session 8 cron job logic.

After the HTTP-trigger refactor, the digest and webhook log cleanup logic
lives in api/cron_jobs.py and is exercised via the /admin/cron/* HTTP
endpoints. The R2 cleanup script remains a standalone script because it
talks only to R2 (no SQLite needed).
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import cron_jobs, crm, db as db_module, delivery
from api.main import app


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "scripts_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("POSTMARK_API_TOKEN", "test_placeholder")
    monkeypatch.setenv("KYLE_ALERT_EMAIL", "kyle@sidebarcode.com")
    monkeypatch.setenv("CRON_SECRET", "test_cron_secret_value")
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


client = TestClient(app)
CRON_HEADERS = {"Authorization": "Bearer test_cron_secret_value"}


def _import_script(name: str):
    """Import a stripe-delivery/scripts/* module by name."""
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# Daily digest — logic in cron_jobs.py
# ---------------------------------------------------------------------------
def test_daily_digest_sends_even_on_zero_purchases(monkeypatch) -> None:
    fake_send = MagicMock()
    monkeypatch.setattr(cron_jobs, "_send_plain_email", fake_send)

    metrics = cron_jobs.run_daily_digest()

    assert metrics["purchase_count"] == 0
    fake_send.assert_called_once()
    kwargs = fake_send.call_args.kwargs
    assert "quiet day" in kwargs["subject"]
    assert "No purchases" in kwargs["text_body"]


def test_daily_digest_includes_recent_purchases(monkeypatch) -> None:
    crm.insert_purchase(
        tier_id="mock_parser_trial",
        category="products",
        delivery_type="zip_download",
        stripe_session_id="cs_digest_001",
        buyer_email="digest@example.com",
        amount_cents=197,
        currency="usd",
        status=crm.PurchaseStatus.DELIVERED,
    )

    fake_send = MagicMock()
    monkeypatch.setattr(cron_jobs, "_send_plain_email", fake_send)
    metrics = cron_jobs.run_daily_digest()

    assert metrics["purchase_count"] == 1
    kwargs = fake_send.call_args.kwargs
    assert "1 purchase" in kwargs["subject"]
    assert "$1.97" in kwargs["subject"]
    assert "digest@example.com" in kwargs["text_body"]
    assert "mock_parser_trial" in kwargs["text_body"]


# ---------------------------------------------------------------------------
# Cron HTTP endpoints
# ---------------------------------------------------------------------------
def test_cron_daily_digest_endpoint_requires_bearer_token() -> None:
    response = client.post("/admin/cron/daily-digest")
    assert response.status_code == 401


def test_cron_daily_digest_endpoint_rejects_wrong_token() -> None:
    response = client.post(
        "/admin/cron/daily-digest",
        headers={"Authorization": "Bearer wrong_secret"},
    )
    assert response.status_code == 401


def test_cron_daily_digest_endpoint_succeeds_with_valid_token(monkeypatch) -> None:
    fake_send = MagicMock()
    monkeypatch.setattr(cron_jobs, "_send_plain_email", fake_send)
    response = client.post("/admin/cron/daily-digest", headers=CRON_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["purchase_count"] == 0
    fake_send.assert_called_once()


def test_cron_daily_digest_503_when_secret_unset(monkeypatch) -> None:
    monkeypatch.delenv("CRON_SECRET", raising=False)
    response = client.post("/admin/cron/daily-digest", headers=CRON_HEADERS)
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# Webhook debug log cleanup — logic in cron_jobs.py
# ---------------------------------------------------------------------------
def test_cleanup_webhook_debug_log_deletes_old_rows() -> None:
    old_ts = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    new_ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    with db_module.get_connection() as conn:
        conn.execute(
            "INSERT INTO webhook_debug_log (stripe_event_id, event_type, event_data_json, created_at) VALUES (?, ?, ?, ?)",
            ("evt_old_001", "checkout.session.completed", "{}", old_ts),
        )
        conn.execute(
            "INSERT INTO webhook_debug_log (stripe_event_id, event_type, event_data_json, created_at) VALUES (?, ?, ?, ?)",
            ("evt_new_001", "checkout.session.completed", "{}", new_ts),
        )

    deleted = cron_jobs.run_cleanup_webhook_debug_log(retention_days=30)
    assert deleted == 1

    with db_module.get_connection() as conn:
        rows = conn.execute("SELECT stripe_event_id FROM webhook_debug_log").fetchall()
    remaining = {r["stripe_event_id"] for r in rows}
    assert remaining == {"evt_new_001"}


def test_cron_cleanup_webhook_log_endpoint_succeeds(monkeypatch) -> None:
    old_ts = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    with db_module.get_connection() as conn:
        conn.execute(
            "INSERT INTO webhook_debug_log (stripe_event_id, event_type, event_data_json, created_at) VALUES (?, ?, ?, ?)",
            ("evt_endpoint_old", "checkout.session.completed", "{}", old_ts),
        )

    response = client.post("/admin/cron/cleanup-webhook-log", headers=CRON_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["deleted_rows"] == 1


# ---------------------------------------------------------------------------
# R2 cleanup — still a standalone script (no SQLite)
# ---------------------------------------------------------------------------
def test_cleanup_r2_deletes_expired_objects_only(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    fresh = now - timedelta(days=2)
    expired = now - timedelta(days=10)

    fake_client = MagicMock()
    fake_paginator = MagicMock()
    fake_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "fresh/object.zip", "LastModified": fresh},
                {"Key": "expired/object.zip", "LastModified": expired},
                {"Key": "sqlite-backups/skip-me.db", "LastModified": expired},
            ]
        }
    ]
    fake_client.get_paginator.return_value = fake_paginator
    fake_client.delete_object = MagicMock()

    cleanup = _import_script("cleanup_r2")
    monkeypatch.setattr(cleanup, "_r2_client", lambda: fake_client)

    counts = cleanup.cleanup_bucket("test-bucket", max_age_days=7, dry_run=False)
    assert counts["scanned"] == 3
    assert counts["deleted"] == 1
    assert counts["skipped"] == 1
    fake_client.delete_object.assert_called_once_with(
        Bucket="test-bucket", Key="expired/object.zip"
    )
