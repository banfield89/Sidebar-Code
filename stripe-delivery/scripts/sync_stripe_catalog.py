"""Sync the local catalog YAML to Stripe Products and Prices.

Idempotent: re-running with no changes is a no-op. When a tier's price or
currency changes, the script archives the old Price (Stripe Prices are
immutable) and creates a new Price under the same Product.

Usage (from stripe-delivery/):
    python scripts/sync_stripe_catalog.py            # apply changes
    python scripts/sync_stripe_catalog.py --dry-run  # report what would change
    python scripts/sync_stripe_catalog.py --catalog path/to/file.yaml

The script auto-loads ~/.sidebarcode-secrets.env if present, so STRIPE_SECRET_KEY
does not need to be exported beforehand.

Outputs:
  * Console summary: created / updated / unchanged / archived counts.
  * Writes CATALOG_INDEX.stripe.yaml next to the source catalog with the
    resolved stripe_product_id and stripe_price_id for each tier.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Auto-load secrets file
# ---------------------------------------------------------------------------
def _autoload_secrets() -> None:
    secrets_path = Path.home() / ".sidebarcode-secrets.env"
    if not secrets_path.exists():
        return
    try:
        from dotenv import dotenv_values  # type: ignore[import-untyped]
    except ImportError:
        return
    values = dotenv_values(secrets_path)
    cleaned = {k: (v or "").strip() for k, v in values.items()}

    # Stripe — prefer test mode for sync runs.
    if not os.environ.get("STRIPE_SECRET_KEY"):
        key = cleaned.get("STRIPE_SECRET_KEY_TEST") or cleaned.get("STRIPE_SECRET_KEY")
        if key:
            os.environ["STRIPE_SECRET_KEY"] = key


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import stripe  # noqa: E402
import yaml  # noqa: E402

from api.catalog import CatalogIndex, TierEntry, load_catalog_index  # noqa: E402


# ---------------------------------------------------------------------------
# Reporting types
# ---------------------------------------------------------------------------
@dataclass
class TierSyncResult:
    tier_id: str
    action: str  # 'created' | 'updated' | 'unchanged' | 'price_archived'
    stripe_product_id: str
    stripe_price_id: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Safe accessor for Stripe StripeObject
# ---------------------------------------------------------------------------
def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Stripe v15 StripeObject lacks dict-style .get(); use [] with fallback."""
    if obj is None:
        return default
    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        return default


# ---------------------------------------------------------------------------
# Stripe operations
# ---------------------------------------------------------------------------
def _find_product_by_tier_id(tier_id: str) -> Optional[Any]:
    """Search Stripe Products for one whose metadata.tier_id matches."""
    # Stripe doesn't support metadata search on Products via list, so we
    # paginate. At MVP volumes (<50 products) this is fine.
    for product in stripe.Product.list(limit=100, active=True).auto_paging_iter():
        metadata = _safe_get(product, "metadata") or {}
        if _safe_get(metadata, "tier_id") == tier_id:
            return product
    return None


def _find_active_price(product_id: str, amount: int, currency: str) -> Optional[Any]:
    """Return the active Price under product_id matching amount + currency."""
    for price in stripe.Price.list(product=product_id, active=True, limit=100).auto_paging_iter():
        if _safe_get(price, "unit_amount") == amount and _safe_get(price, "currency") == currency:
            return price
    return None


def _archive_existing_active_prices(product_id: str, keep_id: Optional[str] = None) -> int:
    """Archive every active Price under product_id except `keep_id`."""
    archived = 0
    for price in stripe.Price.list(product=product_id, active=True, limit=100).auto_paging_iter():
        if price.id == keep_id:
            continue
        stripe.Price.modify(price.id, active=False)
        archived += 1
    return archived


def _upsert_product(tier: TierEntry) -> Any:
    existing = _find_product_by_tier_id(tier.tier_id)
    if existing is None:
        return stripe.Product.create(
            name=tier.stripe_product_name,
            description=tier.stripe_product_description,
            tax_code=tier.tax_code,
            metadata={
                "tier_id": tier.tier_id,
                "category": tier.category,
                "delivery_type": tier.delivery_type,
            },
        )

    existing_metadata = _safe_get(existing, "metadata") or {}
    needs_update = (
        _safe_get(existing, "name") != tier.stripe_product_name
        or _safe_get(existing, "description") != tier.stripe_product_description
        or _safe_get(existing_metadata, "delivery_type") != tier.delivery_type
    )
    if needs_update:
        return stripe.Product.modify(
            existing.id,
            name=tier.stripe_product_name,
            description=tier.stripe_product_description,
            metadata={
                "tier_id": tier.tier_id,
                "category": tier.category,
                "delivery_type": tier.delivery_type,
            },
        )
    return existing


def _upsert_price(tier: TierEntry, product_id: str) -> tuple[Any, bool]:
    """Return (price, was_created)."""
    existing = _find_active_price(product_id, tier.price_cents, tier.currency)
    if existing is not None:
        return existing, False

    created = stripe.Price.create(
        product=product_id,
        unit_amount=tier.price_cents,
        currency=tier.currency,
        tax_behavior="exclusive",
        metadata={"tier_id": tier.tier_id},
    )
    return created, True


# ---------------------------------------------------------------------------
# Sync orchestration
# ---------------------------------------------------------------------------
def sync_catalog(catalog: CatalogIndex, *, dry_run: bool = False) -> list[TierSyncResult]:
    results: list[TierSyncResult] = []
    for tier in catalog:
        if dry_run:
            existing_product = _find_product_by_tier_id(tier.tier_id)
            existing_price = (
                _find_active_price(existing_product.id, tier.price_cents, tier.currency)
                if existing_product
                else None
            )
            if existing_product is None:
                action = "would_create"
            elif existing_price is None:
                action = "would_create_new_price"
            else:
                action = "would_no_op"
            results.append(
                TierSyncResult(
                    tier_id=tier.tier_id,
                    action=action,
                    stripe_product_id=existing_product.id if existing_product else "",
                    stripe_price_id=existing_price.id if existing_price else "",
                )
            )
            continue

        product = _upsert_product(tier)
        price, was_created = _upsert_price(tier, product.id)
        archived = _archive_existing_active_prices(product.id, keep_id=price.id)

        if was_created and archived > 0:
            action = "updated"
            notes = f"created new Price, archived {archived} old Price(s)"
        elif was_created:
            action = "created"
            notes = "first Price created"
        else:
            action = "unchanged"
            notes = ""
        results.append(
            TierSyncResult(
                tier_id=tier.tier_id,
                action=action,
                stripe_product_id=product.id,
                stripe_price_id=price.id,
                notes=notes,
            )
        )
    return results


def write_resolved_catalog(catalog: CatalogIndex, results: list[TierSyncResult], output_path: Path) -> None:
    """Write CATALOG_INDEX.stripe.yaml with resolved Stripe IDs."""
    by_id = {r.tier_id: r for r in results}
    payload: dict[str, list[dict[str, Any]]] = {
        "products": [],
        "consulting": [],
        "custom_workflows": [],
    }
    for tier in catalog:
        result = by_id.get(tier.tier_id)
        entry = {
            "tier_id": tier.tier_id,
            "stripe_product_name": tier.stripe_product_name,
            "stripe_product_id": result.stripe_product_id if result else "",
            "stripe_price_id": result.stripe_price_id if result else "",
            "price_cents": tier.price_cents,
            "currency": tier.currency,
            "delivery_type": tier.delivery_type,
            "tax_code": tier.tax_code,
        }
        if tier.delivery_source:
            entry["delivery_source"] = tier.delivery_source
        if tier.scheduling_link:
            entry["scheduling_link"] = tier.scheduling_link
        payload[tier.category].append(entry)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local catalog to Stripe Products + Prices")
    parser.add_argument("--catalog", type=Path, default=None, help="Path to catalog YAML")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without applying")
    args = parser.parse_args()

    if not os.environ.get("STRIPE_SECRET_KEY"):
        print("ERROR: STRIPE_SECRET_KEY is not set", file=sys.stderr)
        return 1
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    if not stripe.api_key.startswith("sk_test_"):
        print(
            "WARNING: STRIPE_SECRET_KEY is not a test-mode key. "
            "Day sessions should NEVER touch live mode.",
            file=sys.stderr,
        )

    catalog = load_catalog_index(args.catalog)
    print(f"Loaded {len(catalog)} tiers from catalog")
    results = sync_catalog(catalog, dry_run=args.dry_run)

    print("")
    print("Sync results:")
    print("-" * 80)
    for r in results:
        line = f"  {r.tier_id:<35} {r.action:<22}"
        if r.stripe_product_id:
            line += f" prod={r.stripe_product_id}"
        if r.stripe_price_id:
            line += f" price={r.stripe_price_id}"
        print(line)
        if r.notes:
            print(f"      {r.notes}")
    print("-" * 80)

    if not args.dry_run:
        catalog_source = args.catalog or (Path(__file__).resolve().parent.parent / "mock_catalog_index.yaml")
        output_path = catalog_source.parent / "CATALOG_INDEX.stripe.yaml"
        write_resolved_catalog(catalog, results, output_path)
        print(f"\nWrote resolved catalog to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
