"""Tests for the Session 7 delivery orchestration: zip + notify + refund.

Mocks PostmarkClient and the R2 boto3 client so no live API calls happen.
build_zip is allowed to actually run because it's local-only.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from api import crm, db as db_module, delivery


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "delivery_test.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("POSTMARK_API_TOKEN", "test_token_placeholder")
    monkeypatch.setenv("KYLE_ALERT_EMAIL", "kyle@sidebarcode.com")
    db_module.reset_for_tests()
    yield
    db_module.reset_for_tests()


@pytest.fixture
def fake_postmark(monkeypatch):
    """Replace the PostmarkClient with a MagicMock and return it."""
    fake_client = MagicMock()
    fake_client.emails = MagicMock()
    fake_client.emails.send_with_template = MagicMock(return_value={"MessageID": "msg_test"})
    fake_client.emails.send = MagicMock(return_value={"MessageID": "msg_test_plain"})
    monkeypatch.setattr(delivery, "_postmark_client", lambda: fake_client)
    return fake_client


def _make_purchase(delivery_type: str = "zip_download") -> crm.Purchase:
    return crm.insert_purchase(
        tier_id="mock_parser_trial" if delivery_type == "zip_download" else "mock_consulting_foundation",
        category="products" if delivery_type == "zip_download" else "consulting",
        delivery_type=delivery_type,
        stripe_session_id=f"cs_test_orch_{delivery_type}",
        stripe_payment_intent_id="pi_test_orch_001",
        buyer_email="buyer@example.com",
        buyer_name="Test Buyer",
        buyer_phone="+15555550100",
        amount_cents=197 if delivery_type == "zip_download" else 2500,
        currency="usd",
        status=crm.PurchaseStatus.AWAITING_DELIVERY,
    )


# ---------------------------------------------------------------------------
# build_and_deliver_zip — happy path
# ---------------------------------------------------------------------------
def test_deliver_zip_writes_purchase_fields(monkeypatch, fake_postmark) -> None:
    monkeypatch.setattr(delivery, "upload_to_r2", MagicMock(return_value="mock_parser_trial/key.zip"))
    monkeypatch.setattr(
        delivery,
        "sign_download_url",
        MagicMock(return_value="https://example.com/signed-url"),
    )

    purchase = _make_purchase("zip_download")
    delivery.build_and_deliver_zip(purchase)

    refreshed = crm.get_purchase_by_id(purchase.purchase_id)
    assert refreshed is not None
    assert refreshed.status == "delivered"
    assert refreshed.zip_object_key is not None
    assert refreshed.zip_object_key.startswith("mock_parser_trial/")
    assert refreshed.download_url_expires_at is not None

    fake_postmark.emails.send_with_template.assert_called_once()
    call_kwargs = fake_postmark.emails.send_with_template.call_args.kwargs
    assert call_kwargs["TemplateAlias"] == "sp2-product-download"
    assert call_kwargs["To"] == "buyer@example.com"
    assert call_kwargs["TemplateModel"]["download_url"] == "https://example.com/signed-url"
    assert call_kwargs["TemplateModel"]["buyer_name"] == "Test Buyer"
    assert call_kwargs["TemplateModel"]["tier_name"] == "Mock Parser Trial"


# ---------------------------------------------------------------------------
# build_and_deliver_zip — failure path
# ---------------------------------------------------------------------------
def test_deliver_zip_failure_writes_delivery_failures_row(monkeypatch, fake_postmark) -> None:
    monkeypatch.setattr(
        delivery,
        "upload_to_r2",
        MagicMock(side_effect=RuntimeError("R2 is down")),
    )

    purchase = _make_purchase("zip_download")
    with pytest.raises(RuntimeError, match="R2 is down"):
        delivery.build_and_deliver_zip(purchase)

    # delivery_failures row inserted
    with db_module.get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM delivery_failures WHERE purchase_id = ?",
            (purchase.purchase_id,),
        ).fetchall()
    assert len(rows) == 1
    assert "R2 is down" in rows[0]["error_msg"]
    assert rows[0]["traceback"]  # full traceback captured

    # delivery_failure_alert email sent to Kyle
    sends = fake_postmark.emails.send_with_template.call_args_list
    assert any(
        c.kwargs["TemplateAlias"] == "sp2-delivery-failure-alert" for c in sends
    )


# ---------------------------------------------------------------------------
# notify_kyle_new_purchase — both emails
# ---------------------------------------------------------------------------
def test_notify_kyle_sends_both_emails(fake_postmark) -> None:
    purchase = _make_purchase("notify_kyle")
    lead = crm.insert_lead(
        tier_id=purchase.tier_id,
        source="stripe_purchase",
        buyer_email=purchase.buyer_email,
        buyer_name=purchase.buyer_name,
        buyer_phone=purchase.buyer_phone,
        stripe_charge_id="ch_test_notify_001",
        amount_cents=purchase.amount_cents,
    )

    delivery.notify_kyle_new_purchase(purchase, lead)

    assert fake_postmark.emails.send_with_template.call_count == 2
    aliases = [
        c.kwargs["TemplateAlias"]
        for c in fake_postmark.emails.send_with_template.call_args_list
    ]
    recipients = [
        c.kwargs["To"]
        for c in fake_postmark.emails.send_with_template.call_args_list
    ]
    assert "sp2-consulting-receipt" in aliases
    assert "sp2-kyle-new-consulting-purchase" in aliases
    assert "buyer@example.com" in recipients
    assert "kyle@sidebarcode.com" in recipients

    # Both emails should have the formatted amount and scheduling link.
    for call in fake_postmark.emails.send_with_template.call_args_list:
        model = call.kwargs["TemplateModel"]
        assert model["amount_formatted"] == "$25.00 USD"
        assert "cal.com" in model["scheduling_link"]


# ---------------------------------------------------------------------------
# notify_kyle_refund
# ---------------------------------------------------------------------------
def test_refund_notify_sends_alert(fake_postmark) -> None:
    purchase = _make_purchase("zip_download")
    crm.update_purchase_status(
        purchase.purchase_id,
        crm.PurchaseStatus.REFUNDED,
        zip_object_key="mock_parser_trial/refunded.zip",
        stripe_charge_id="ch_test_refund_001",
    )
    refreshed = crm.get_purchase_by_id(purchase.purchase_id)

    delivery.notify_kyle_refund(refreshed)

    fake_postmark.emails.send.assert_called_once()
    kwargs = fake_postmark.emails.send.call_args.kwargs
    assert kwargs["To"] == "kyle@sidebarcode.com"
    assert "REFUND" in kwargs["Subject"]
    assert refreshed.purchase_id in kwargs["TextBody"]
    assert "mock_parser_trial" in kwargs["TextBody"]
    assert "ch_test_refund_001" in kwargs["TextBody"]


# ---------------------------------------------------------------------------
# Postmark missing token
# ---------------------------------------------------------------------------
def test_postmark_client_raises_without_token(monkeypatch) -> None:
    monkeypatch.delenv("POSTMARK_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="POSTMARK_API_TOKEN"):
        delivery._postmark_client()
