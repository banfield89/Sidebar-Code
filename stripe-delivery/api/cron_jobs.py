"""Cron job logic that needs SQLite — must run inside the web service.

Render persistent disks are per-service, not shared across the web service
and cron services. Anything that touches /var/data/sidebarcode.db has to
run inside `sidebarcode-api`. Cron services trigger this logic via HTTP
calls to the /admin/cron/* endpoints in api/admin.py.

Functions here are pure logic: no HTTP, no auth. The endpoints in admin.py
handle auth and HTTP wrapping; tests can call these functions directly
without spinning up FastAPI.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from api.db import get_connection
from api.delivery import _send_plain_email

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Daily digest
# ---------------------------------------------------------------------------
def _query_yesterday(now: datetime) -> dict[str, Any]:
    start = now - timedelta(hours=24)
    cutoff = start.isoformat()
    with get_connection() as conn:
        purchases = conn.execute(
            """
            SELECT tier_id, delivery_type, status, amount_cents, currency,
                   buyer_email, created_at
              FROM purchases
             WHERE created_at >= ?
             ORDER BY created_at DESC
            """,
            (cutoff,),
        ).fetchall()
        leads_today = conn.execute(
            "SELECT COUNT(*) AS n FROM leads WHERE created_at >= ?", (cutoff,)
        ).fetchone()
        failures_today = conn.execute(
            "SELECT COUNT(*) AS n FROM delivery_failures WHERE created_at >= ?", (cutoff,)
        ).fetchone()
        pending_leads = conn.execute(
            """
            SELECT COUNT(*) AS n FROM leads
             WHERE status = 'qualified'
               AND NOT EXISTS (
                   SELECT 1 FROM lead_events e
                    WHERE e.lead_id = leads.lead_id
                      AND e.event_type IN ('contacted', 'scheduled', 'email_sent')
               )
            """
        ).fetchone()

    purchase_rows = [dict(p) for p in purchases]
    delivered_total = sum(
        p["amount_cents"] for p in purchase_rows if p["status"] == "delivered"
    )
    refunded_total = sum(
        p["amount_cents"] for p in purchase_rows if p["status"] == "refunded"
    )
    return {
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "purchase_count": len(purchase_rows),
        "purchases": purchase_rows,
        "delivered_revenue_cents": delivered_total,
        "refunded_total_cents": refunded_total,
        "leads_today": leads_today["n"],
        "failures_today": failures_today["n"],
        "pending_leads": pending_leads["n"],
    }


def _format_amount(cents: int, currency: str = "usd") -> str:
    return f"${cents / 100:,.2f} {currency.upper()}"


def _format_digest(metrics: dict[str, Any]) -> tuple[str, str]:
    date_str = metrics["window_end"][:10]
    if metrics["purchase_count"] == 0:
        subject = f"Sidebar Code daily digest — {date_str} (quiet day)"
        headline = "No purchases in the last 24 hours."
    else:
        subject = (
            f"Sidebar Code daily digest — {date_str} — "
            f"{metrics['purchase_count']} purchase(s), "
            f"{_format_amount(metrics['delivered_revenue_cents'])}"
        )
        headline = (
            f"{metrics['purchase_count']} purchase(s) in the last 24 hours, "
            f"{_format_amount(metrics['delivered_revenue_cents'])} delivered."
        )

    lines = [
        "Sidebar Code — daily digest",
        "=" * 60,
        f"Window:  {metrics['window_start']}  ->  {metrics['window_end']}",
        "",
        headline,
        "",
        "Numbers (last 24 hours)",
        "-" * 60,
        f"  Purchases:           {metrics['purchase_count']}",
        f"  Delivered revenue:   {_format_amount(metrics['delivered_revenue_cents'])}",
        f"  Refunded:            {_format_amount(metrics['refunded_total_cents'])}",
        f"  New leads:           {metrics['leads_today']}",
        f"  Failed deliveries:   {metrics['failures_today']}",
        "",
        "Open work",
        "-" * 60,
        f"  Pending consulting leads (need follow-up): {metrics['pending_leads']}",
        "",
    ]
    if metrics["purchases"]:
        lines.append("Recent purchases")
        lines.append("-" * 60)
        for p in metrics["purchases"][:20]:
            lines.append(
                f"  [{p['status']:<18}] {p['tier_id']:<32} "
                f"{_format_amount(p['amount_cents'], p['currency'])}  "
                f"{p['buyer_email']}"
            )
        lines.append("")
    lines.append("Admin: https://sidebarcode-api.onrender.com/admin/sales")
    lines.append("Stripe: https://dashboard.stripe.com/test/payments")
    lines.append("")
    return subject, "\n".join(lines)


def run_daily_digest() -> dict[str, Any]:
    """Build and send the daily digest. Returns the metrics dict for testing."""
    import os

    now = datetime.now(timezone.utc)
    metrics = _query_yesterday(now)
    subject, body = _format_digest(metrics)
    to = os.environ.get("KYLE_ALERT_EMAIL", "kyle@sidebarcode.com")
    _send_plain_email(to=to, subject=subject, text_body=body)
    logger.info("daily digest sent to %s — purchases=%d", to, metrics["purchase_count"])
    return metrics


# ---------------------------------------------------------------------------
# Webhook debug log cleanup
# ---------------------------------------------------------------------------
def run_cleanup_webhook_debug_log(retention_days: int = 30) -> int:
    """Delete webhook_debug_log rows older than retention_days. Returns count."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with get_connection() as conn:
        result = conn.execute(
            "DELETE FROM webhook_debug_log WHERE created_at < ?", (cutoff,)
        )
        deleted = result.rowcount
    logger.info("webhook_debug_log cleanup deleted %d rows older than %s", deleted, cutoff)
    return deleted
