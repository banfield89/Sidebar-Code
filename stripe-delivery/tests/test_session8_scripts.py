"""Tests for Session 8 scripts: daily digest + R2 cleanup + webhook log cleanup."""

from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from api import crm, db as db_module, delivery


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "scripts_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("POSTMARK_API_TOKEN", "test_placeholder")
    monkeypatch.setenv("KYLE_ALERT_EMAIL", "kyle@sidebarcode.com")
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


def _import_script(name: str):
    """Import a stripe-delivery/scripts/* module by name."""
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# Daily digest
# ---------------------------------------------------------------------------
def test_daily_digest_sends_even_on_zero_purchases(monkeypatch) -> None:
    fake_send = MagicMock()
    monkeypatch.setattr(delivery, "_send_plain_email", fake_send)

    digest = _import_script("send_daily_digest")
    monkeypatch.setattr(digest, "_send_plain_email", fake_send)

    rc = digest.main()
    assert rc == 0
    fake_send.assert_called_once()
    kwargs = fake_send.call_args.kwargs
    assert "quiet day" in kwargs["subject"]
    assert "No purchases" in kwargs["text_body"]
    assert kwargs["to"] == "kyle@sidebarcode.com"


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
    monkeypatch.setattr(delivery, "_send_plain_email", fake_send)
    digest = _import_script("send_daily_digest")
    monkeypatch.setattr(digest, "_send_plain_email", fake_send)

    digest.main()

    kwargs = fake_send.call_args.kwargs
    assert "1 purchase" in kwargs["subject"]
    assert "$1.97" in kwargs["subject"]
    assert "digest@example.com" in kwargs["text_body"]
    assert "mock_parser_trial" in kwargs["text_body"]


# ---------------------------------------------------------------------------
# R2 cleanup
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


def test_cleanup_r2_dry_run_does_not_delete(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    expired = now - timedelta(days=10)
    fake_client = MagicMock()
    fake_paginator = MagicMock()
    fake_paginator.paginate.return_value = [
        {"Contents": [{"Key": "expired/object.zip", "LastModified": expired}]}
    ]
    fake_client.get_paginator.return_value = fake_paginator

    cleanup = _import_script("cleanup_r2")
    monkeypatch.setattr(cleanup, "_r2_client", lambda: fake_client)

    counts = cleanup.cleanup_bucket("test-bucket", max_age_days=7, dry_run=True)
    assert counts["deleted"] == 1  # would-have-deleted count
    fake_client.delete_object.assert_not_called()


# ---------------------------------------------------------------------------
# webhook_debug_log cleanup
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

    cleanup = _import_script("cleanup_webhook_debug_log")
    deleted = cleanup.cleanup(retention_days=30, dry_run=False)
    assert deleted == 1

    with db_module.get_connection() as conn:
        rows = conn.execute("SELECT stripe_event_id FROM webhook_debug_log").fetchall()
    remaining = {r["stripe_event_id"] for r in rows}
    assert remaining == {"evt_new_001"}


def test_cleanup_webhook_debug_log_dry_run_does_not_delete() -> None:
    old_ts = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    with db_module.get_connection() as conn:
        conn.execute(
            "INSERT INTO webhook_debug_log (stripe_event_id, event_type, event_data_json, created_at) VALUES (?, ?, ?, ?)",
            ("evt_dryrun_001", "checkout.session.completed", "{}", old_ts),
        )

    cleanup = _import_script("cleanup_webhook_debug_log")
    count = cleanup.cleanup(retention_days=30, dry_run=True)
    assert count == 1

    with db_module.get_connection() as conn:
        rows = conn.execute("SELECT * FROM webhook_debug_log").fetchall()
    assert len(rows) == 1  # still there
