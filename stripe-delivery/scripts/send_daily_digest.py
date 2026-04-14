"""Daily digest cron — emails Kyle a summary of the previous 24 hours.

Sends EVEN ON ZERO-PURCHASE DAYS so silence is meaningful: if the inbox
is empty in the morning, the cron itself is broken.

Runs as a Render cron job (configured in render.yaml). Can also run
manually for testing.

Usage:
    python scripts/send_daily_digest.py
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Auto-load secrets
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
    for key in ("POSTMARK_API_TOKEN", "KYLE_ALERT_EMAIL", "SQLITE_PATH"):
        if not os.environ.get(key) and cleaned.get(key):
            os.environ[key] = cleaned[key]


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api.db import get_connection  # noqa: E402
from api.delivery import _send_plain_email  # noqa: E402

logger = logging.getLogger("daily_digest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _query_yesterday(now: datetime) -> dict[str, Any]:
    """Pull the metrics for the 24 hours ending at `now`."""
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
    """Return (subject, plain_text_body)."""
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


def main() -> int:
    if not os.environ.get("POSTMARK_API_TOKEN"):
        print("ERROR: POSTMARK_API_TOKEN not set", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    metrics = _query_yesterday(now)
    subject, body = _format_digest(metrics)

    to = os.environ.get("KYLE_ALERT_EMAIL", "kyle@sidebarcode.com")
    _send_plain_email(to=to, subject=subject, text_body=body)
    logger.info("daily digest sent to %s — purchases=%d", to, metrics["purchase_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
