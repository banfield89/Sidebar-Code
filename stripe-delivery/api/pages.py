"""Buyer-facing post-checkout HTML pages: /success and /cancel.

Server-rendered FastAPI routes — no Jinja2, no client-side framework.
Reads the checkout session from Stripe to render tier-specific copy.

The success page handles two delivery types:
  * zip_download → "check your email for the download link"
  * notify_kyle → "Kyle will reach out + here's the scheduling link"

Cancel page is static and doesn't need any session lookup.
"""

from __future__ import annotations

import html
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Stripe lookup (lazy import so the page renders even if Stripe is misconfigured)
# ---------------------------------------------------------------------------
def _safe_stripe_session_lookup(session_id: str) -> Optional[dict[str, Any]]:
    """Best-effort fetch of a checkout session. Returns None on any failure
    so the page still renders generic copy."""
    try:
        import stripe
        if not stripe.api_key:
            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            return None
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = _safe_get(session, "metadata") or {}
        return {
            "tier_id": _safe_get(metadata, "tier_id", "unknown") or "unknown",
            "delivery_type": _safe_get(metadata, "delivery_type", "unknown") or "unknown",
            "buyer_email": (
                _safe_get(_safe_get(session, "customer_details") or {}, "email")
                or _safe_get(session, "customer_email")
                or ""
            ),
            "amount_total": _safe_get(session, "amount_total") or 0,
            "currency": _safe_get(session, "currency") or "usd",
        }
    except Exception:
        logger.exception("success page Stripe lookup failed for session_id=%s", session_id)
        return None


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        return obj[key]
    except (KeyError, TypeError, AttributeError):
        return default


# ---------------------------------------------------------------------------
# Catalog lookup for tier display name + scheduling link
# ---------------------------------------------------------------------------
def _resolve_tier_display(tier_id: str) -> dict[str, Any]:
    """Look up the tier in the catalog. Returns generic strings if unknown."""
    try:
        from api.catalog import load_catalog_index
        catalog = load_catalog_index()
        tier = catalog.get(tier_id)
        return {
            "tier_name": tier.stripe_product_name,
            "scheduling_link": tier.scheduling_link or "",
        }
    except Exception:
        return {"tier_name": "your purchase", "scheduling_link": ""}


# ---------------------------------------------------------------------------
# CSS (shared between success + cancel)
# ---------------------------------------------------------------------------
_PAGE_CSS = """
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #fafafa;
    color: #222;
    margin: 0;
    padding: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card {
    background: white;
    max-width: 560px;
    margin: 2em;
    padding: 2.5em 3em;
    border-radius: 10px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  }
  h1 { color: #0969da; margin-top: 0; font-size: 1.8em; }
  h2 { color: #444; font-size: 1.15em; margin-top: 1.8em; }
  p { line-height: 1.6; }
  .receipt {
    background: #f6f8fa;
    border-radius: 6px;
    padding: 1em 1.2em;
    margin: 1.5em 0;
    font-size: 0.95em;
  }
  .receipt strong { color: #555; }
  a.button {
    display: inline-block;
    background: #0969da;
    color: white;
    padding: 0.7em 1.4em;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    margin-top: 0.5em;
  }
  a.button:hover { background: #0860c4; }
  .support {
    color: #888;
    font-size: 0.88em;
    margin-top: 2em;
    border-top: 1px solid #eee;
    padding-top: 1.2em;
  }
  .support a { color: #0969da; }
</style>
"""


def _format_amount(cents: int, currency: str) -> str:
    return f"${cents / 100:.2f} {currency.upper()}"


def _wrap(title: str, body_html: str) -> str:
    return (
        f"<!DOCTYPE html><html lang='en'><head>"
        f"<meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{html.escape(title)} — Sidebar Code</title>"
        f"{_PAGE_CSS}</head>"
        f"<body><div class='card'>{body_html}</div></body></html>"
    )


# ---------------------------------------------------------------------------
# /success
# ---------------------------------------------------------------------------
@router.get("/success", response_class=HTMLResponse)
def success_page(session_id: str = "") -> HTMLResponse:
    if not session_id:
        return HTMLResponse(_wrap(
            "Thank you",
            "<h1>Thank you for your purchase</h1>"
            "<p>Your payment was processed successfully. Check your email for next steps.</p>"
            "<p class='support'>Questions? Contact "
            "<a href='mailto:kyle@sidebarcode.com'>kyle@sidebarcode.com</a>.</p>"
        ))

    info = _safe_stripe_session_lookup(session_id)
    if info is None:
        return HTMLResponse(_wrap(
            "Thank you",
            "<h1>Thank you for your purchase</h1>"
            "<p>Your payment was processed successfully. Check your email for next steps.</p>"
            "<p>If you don't see anything within 5 minutes, please check your spam folder "
            "or contact support.</p>"
            "<p class='support'>Questions? Contact "
            "<a href='mailto:kyle@sidebarcode.com'>kyle@sidebarcode.com</a>.</p>"
        ))

    tier_info = _resolve_tier_display(info["tier_id"])
    tier_name = tier_info["tier_name"]
    delivery_type = info["delivery_type"]
    buyer_email = info["buyer_email"] or "your email"
    amount_str = _format_amount(info["amount_total"], info["currency"])
    receipt_html = (
        f"<div class='receipt'>"
        f"<strong>Item:</strong> {html.escape(tier_name)}<br>"
        f"<strong>Amount:</strong> {html.escape(amount_str)}<br>"
        f"<strong>Email:</strong> {html.escape(buyer_email)}"
        f"</div>"
    )

    if delivery_type == "zip_download":
        body_html = (
            f"<h1>Thank you — your download is on its way</h1>"
            f"<p>Your purchase is confirmed and your download link has been emailed to "
            f"<strong>{html.escape(buyer_email)}</strong>.</p>"
            f"{receipt_html}"
            f"<h2>What happens next</h2>"
            f"<p>The email should arrive within 5 minutes. The download link is valid for "
            f"72 hours from now. Save the file to your computer before the link expires.</p>"
            f"<p>If you don't see the email, check your spam folder. Still nothing? "
            f"Reply to this purchase or contact support.</p>"
            f"<p class='support'>Questions? Contact "
            f"<a href='mailto:kyle@sidebarcode.com'>kyle@sidebarcode.com</a>.</p>"
        )
    elif delivery_type == "notify_kyle":
        scheduling_link = tier_info["scheduling_link"]
        scheduling_html = (
            f"<p><a class='button' href='{html.escape(scheduling_link)}'>Schedule on Kyle's calendar</a></p>"
            if scheduling_link else ""
        )
        body_html = (
            f"<h1>Thank you — Kyle will be in touch</h1>"
            f"<p>Your purchase is confirmed. Kyle will reach out within one business day "
            f"to coordinate next steps.</p>"
            f"{receipt_html}"
            f"<h2>Skip the wait</h2>"
            f"<p>You can also book a time directly on Kyle's calendar:</p>"
            f"{scheduling_html}"
            f"<p class='support'>Questions? Contact "
            f"<a href='mailto:kyle@sidebarcode.com'>kyle@sidebarcode.com</a>.</p>"
        )
    else:
        body_html = (
            f"<h1>Thank you for your purchase</h1>"
            f"<p>Your payment was processed successfully. Kyle will be in touch shortly.</p>"
            f"{receipt_html}"
            f"<p class='support'>Questions? Contact "
            f"<a href='mailto:kyle@sidebarcode.com'>kyle@sidebarcode.com</a>.</p>"
        )

    return HTMLResponse(_wrap("Thank you", body_html))


# ---------------------------------------------------------------------------
# /cancel
# ---------------------------------------------------------------------------
@router.get("/cancel", response_class=HTMLResponse)
def cancel_page() -> HTMLResponse:
    body_html = (
        "<h1>No problem — no charge was made</h1>"
        "<p>You closed the checkout window before completing payment. "
        "Your card was not charged and nothing was created on our side.</p>"
        "<p>If you have questions about a Sidebar Code product or want help "
        "deciding which tier fits your firm, just reach out:</p>"
        "<p><a class='button' href='mailto:kyle@sidebarcode.com'>Email Kyle</a></p>"
        "<p class='support'>Or visit "
        "<a href='https://sidebarcode.com'>sidebarcode.com</a> "
        "to browse the product list.</p>"
    )
    return HTMLResponse(_wrap("Checkout canceled", body_html))
