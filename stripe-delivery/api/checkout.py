"""Checkout routes: creates Stripe Checkout sessions and reads session state.

Session 4 scope. Session 5 will add the webhook handler that processes
checkout.session.completed events triggered by these sessions.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.catalog import CatalogIndex, TierEntry, load_catalog_index

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Stripe client
# ---------------------------------------------------------------------------
def _ensure_stripe_key() -> None:
    """Set the Stripe API key on the global stripe module.

    Reads STRIPE_SECRET_KEY from env. Raises a clean 500 if missing so the
    error message identifies the misconfiguration instead of a generic
    library error.
    """
    if stripe.api_key:
        return
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="STRIPE_SECRET_KEY is not configured",
        )
    stripe.api_key = key


# ---------------------------------------------------------------------------
# Version hashing for ToS / Tech Overview audit trail
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # Side Bar Code/


def _hash_file(path: Path) -> str:
    """SHA-256 hash of a file's contents. Returns 'unknown' if not found."""
    if not path.exists():
        return "unknown"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _tos_version_hash() -> str:
    return _hash_file(_REPO_ROOT / "terms.html")


def _tech_overview_version_hash() -> str:
    return _hash_file(_REPO_ROOT / "Product Catalog" / "shared" / "technology_overview.md")


# ---------------------------------------------------------------------------
# Catalog cache (load once per process)
# ---------------------------------------------------------------------------
_catalog_cache: Optional[CatalogIndex] = None


def get_catalog() -> CatalogIndex:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = load_catalog_index()
    return _catalog_cache


def reset_catalog_cache() -> None:
    """Test helper — clears the in-process catalog cache."""
    global _catalog_cache
    _catalog_cache = None


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class CheckoutRequest(BaseModel):
    tier_id: str = Field(..., min_length=1, max_length=128)
    tos_accepted: bool
    tech_overview_accepted: bool


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SessionInfoResponse(BaseModel):
    tier_id: str
    delivery_type: str
    amount: int
    currency: str
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_buyer_ip(request: Request) -> str:
    """Best-effort buyer IP. Trusts X-Forwarded-For when behind Render's proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _resolve_base_url(request: Request) -> str:
    """SITE_BASE_URL env var, else fall back to the request's own scheme+host."""
    override = os.environ.get("SITE_BASE_URL")
    if override:
        return override.rstrip("/")
    return f"{request.url.scheme}://{request.url.netloc}"


def _build_session_metadata(
    tier: TierEntry, payload: CheckoutRequest, request: Request
) -> dict[str, str]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "tier_id": tier.tier_id,
        "category": tier.category,
        "delivery_type": tier.delivery_type,
        "tos_accepted_at": now_iso,
        "tos_version_hash": _tos_version_hash(),
        "tech_overview_accepted_at": now_iso,
        "tech_overview_version_hash": _tech_overview_version_hash(),
        "buyer_ip": _resolve_buyer_ip(request),
    }


# ---------------------------------------------------------------------------
# POST /api/checkout
# ---------------------------------------------------------------------------
@router.post("/api/checkout", response_model=CheckoutResponse)
def create_checkout(payload: CheckoutRequest, request: Request) -> CheckoutResponse:
    """Create a Stripe Checkout Session for the requested tier.

    Validates ToS + Technology Overview acceptance booleans before contacting
    Stripe — buyers must explicitly tick both boxes on the pre-checkout modal.
    """
    if not payload.tos_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ToS acceptance required",
        )
    if not payload.tech_overview_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Technology Overview acceptance required",
        )

    catalog = get_catalog()
    try:
        tier = catalog.get(payload.tier_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown tier_id: {payload.tier_id}",
        )

    _ensure_stripe_key()
    base_url = _resolve_base_url(request)
    metadata = _build_session_metadata(tier, payload, request)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": tier.currency,
                        "product_data": {
                            "name": tier.stripe_product_name,
                            "description": tier.stripe_product_description,
                            "metadata": {"tier_id": tier.tier_id},
                        },
                        "unit_amount": tier.price_cents,
                        "tax_behavior": "exclusive",
                    },
                    "quantity": 1,
                }
            ],
            metadata=metadata,
            phone_number_collection={"enabled": True},
            success_url=f"{base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/cancel",
            automatic_tax={"enabled": True},
        )
    except stripe.error.StripeError as exc:  # type: ignore[attr-defined]
        logger.exception("Stripe Checkout session creation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"stripe error: {exc}",
        ) from exc

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


# ---------------------------------------------------------------------------
# GET /api/session/{session_id}
# ---------------------------------------------------------------------------
@router.get("/api/session/{session_id}", response_model=SessionInfoResponse)
def read_session(session_id: str) -> SessionInfoResponse:
    """Read-only lookup for the success page to display purchase state."""
    _ensure_stripe_key()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError as exc:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown session: {session_id}",
        ) from exc
    except stripe.error.StripeError as exc:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"stripe error: {exc}",
        ) from exc

    def _safe(obj, key, default=None):
        if obj is None:
            return default
        try:
            return obj[key]
        except (KeyError, TypeError, AttributeError):
            return default

    metadata = _safe(session, "metadata") or {}
    return SessionInfoResponse(
        tier_id=_safe(metadata, "tier_id", "unknown") or "unknown",
        delivery_type=_safe(metadata, "delivery_type", "unknown") or "unknown",
        amount=_safe(session, "amount_total", 0) or 0,
        currency=_safe(session, "currency", "usd") or "usd",
        status=_safe(session, "status", "unknown") or "unknown",
    )
