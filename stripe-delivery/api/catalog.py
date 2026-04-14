"""Catalog loader: reads CATALOG_INDEX.yaml (or mock) and resolves tier metadata.

Session 4 scope. Returns a typed CatalogIndex with helpers for tier lookup
by tier_id. Used by checkout.py to resolve a buyer's selected tier into
the right Stripe Price and delivery_type.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass(frozen=True)
class TierEntry:
    """One catalog entry — product, consulting, or workflow tier."""

    tier_id: str
    category: str  # 'products' | 'consulting' | 'custom_workflows'
    stripe_product_name: str
    stripe_product_description: str
    price_cents: int
    currency: str
    delivery_type: str  # 'zip_download' | 'notify_kyle'
    tax_code: str
    delivery_source: Optional[str] = None  # required for zip_download
    scheduling_link: Optional[str] = None  # required for notify_kyle

    def __post_init__(self) -> None:
        if self.delivery_type not in ("zip_download", "notify_kyle"):
            raise ValueError(
                f"{self.tier_id}: delivery_type must be zip_download or notify_kyle"
            )
        if self.delivery_type == "zip_download" and not self.delivery_source:
            raise ValueError(
                f"{self.tier_id}: zip_download tier requires delivery_source"
            )
        if self.delivery_type == "notify_kyle" and not self.scheduling_link:
            raise ValueError(
                f"{self.tier_id}: notify_kyle tier requires scheduling_link"
            )
        if self.price_cents <= 0:
            raise ValueError(f"{self.tier_id}: price_cents must be positive")
        if self.currency.lower() != self.currency:
            raise ValueError(f"{self.tier_id}: currency must be lowercase ISO code")


@dataclass(frozen=True)
class CatalogIndex:
    """Full catalog: every tier across every category, plus lookup helpers."""

    tiers: tuple[TierEntry, ...] = field(default_factory=tuple)

    def get(self, tier_id: str) -> TierEntry:
        for tier in self.tiers:
            if tier.tier_id == tier_id:
                return tier
        raise KeyError(f"unknown tier_id: {tier_id}")

    def __len__(self) -> int:
        return len(self.tiers)

    def __iter__(self):
        return iter(self.tiers)


def _default_catalog_path() -> Path:
    """Resolve the catalog path from CATALOG_INDEX_PATH env var, else mock."""
    override = os.environ.get("CATALOG_INDEX_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "mock_catalog_index.yaml"


_CATEGORIES = ("products", "consulting", "custom_workflows")


def load_catalog_index(path: Optional[Path] = None) -> CatalogIndex:
    """Load and parse the catalog YAML into a CatalogIndex.

    Default path: $CATALOG_INDEX_PATH if set, else mock_catalog_index.yaml
    in the stripe-delivery folder.
    """
    catalog_path = Path(path) if path else _default_catalog_path()
    if not catalog_path.exists():
        raise FileNotFoundError(f"catalog file not found: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    tiers: list[TierEntry] = []
    seen_ids: set[str] = set()
    for category in _CATEGORIES:
        entries = raw.get(category) or []
        for entry in entries:
            tier_id = entry.get("tier_id")
            if not tier_id:
                raise ValueError(f"{category} entry missing tier_id: {entry}")
            if tier_id in seen_ids:
                raise ValueError(f"duplicate tier_id in catalog: {tier_id}")
            seen_ids.add(tier_id)
            tiers.append(
                TierEntry(
                    tier_id=tier_id,
                    category=category,
                    stripe_product_name=entry["stripe_product_name"],
                    stripe_product_description=entry["stripe_product_description"],
                    price_cents=int(entry["price_cents"]),
                    currency=str(entry["currency"]).lower(),
                    delivery_type=entry["delivery_type"],
                    tax_code=entry["tax_code"],
                    delivery_source=entry.get("delivery_source"),
                    scheduling_link=entry.get("scheduling_link"),
                )
            )

    return CatalogIndex(tiers=tuple(tiers))
