"""Tests for api/catalog.py — catalog loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.catalog import CatalogIndex, TierEntry, load_catalog_index

MOCK_CATALOG_PATH = Path(__file__).resolve().parent.parent / "mock_catalog_index.yaml"


def test_mock_catalog_loads_three_tiers() -> None:
    catalog = load_catalog_index(MOCK_CATALOG_PATH)
    assert len(catalog) == 3
    tier_ids = {tier.tier_id for tier in catalog}
    assert tier_ids == {"mock_parser_trial", "mock_consulting_foundation", "mock_workflow_single"}


def test_mock_catalog_parser_trial_is_zip_download() -> None:
    catalog = load_catalog_index(MOCK_CATALOG_PATH)
    tier = catalog.get("mock_parser_trial")
    assert tier.delivery_type == "zip_download"
    assert tier.delivery_source is not None
    assert tier.price_cents == 197
    assert tier.currency == "usd"
    assert tier.category == "products"


def test_mock_catalog_consulting_is_notify_kyle() -> None:
    catalog = load_catalog_index(MOCK_CATALOG_PATH)
    tier = catalog.get("mock_consulting_foundation")
    assert tier.delivery_type == "notify_kyle"
    assert tier.scheduling_link is not None
    assert tier.price_cents == 2500
    assert tier.category == "consulting"


def test_catalog_get_unknown_tier_raises_keyerror() -> None:
    catalog = load_catalog_index(MOCK_CATALOG_PATH)
    with pytest.raises(KeyError):
        catalog.get("nope_not_a_real_tier")


def test_zip_download_tier_requires_delivery_source() -> None:
    with pytest.raises(ValueError, match="delivery_source"):
        TierEntry(
            tier_id="bad",
            category="products",
            stripe_product_name="x",
            stripe_product_description="y",
            price_cents=100,
            currency="usd",
            delivery_type="zip_download",
            tax_code="txcd_10502000",
            delivery_source=None,
        )


def test_notify_kyle_tier_requires_scheduling_link() -> None:
    with pytest.raises(ValueError, match="scheduling_link"):
        TierEntry(
            tier_id="bad",
            category="consulting",
            stripe_product_name="x",
            stripe_product_description="y",
            price_cents=100,
            currency="usd",
            delivery_type="notify_kyle",
            tax_code="txcd_20030000",
            scheduling_link=None,
        )


def test_invalid_delivery_type_rejected() -> None:
    with pytest.raises(ValueError, match="delivery_type"):
        TierEntry(
            tier_id="bad",
            category="products",
            stripe_product_name="x",
            stripe_product_description="y",
            price_cents=100,
            currency="usd",
            delivery_type="email_only",  # invalid
            tax_code="txcd_10502000",
            delivery_source="some/path",
        )


def test_negative_price_rejected() -> None:
    with pytest.raises(ValueError, match="price_cents"):
        TierEntry(
            tier_id="bad",
            category="products",
            stripe_product_name="x",
            stripe_product_description="y",
            price_cents=0,
            currency="usd",
            delivery_type="zip_download",
            tax_code="txcd_10502000",
            delivery_source="some/path",
        )


def test_load_missing_catalog_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_catalog_index(Path("/nonexistent/path/catalog.yaml"))
