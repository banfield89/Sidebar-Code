"""Admin dashboard (basic auth): recent purchases, pending leads, failed deliveries.

Session 8 scope. Three panels:
  1. Last 50 purchases with status
  2. Pending consulting leads (status = qualified, no follow-up recorded)
  3. Failed deliveries in last 7 days, with a Resend button

Mounted at `/admin/sales` (deliberate route prefix — leaves room for a
future portal at /admin/* that nests other tools alongside this one).
"""

from __future__ import annotations

import html
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from api import crm, delivery
from api.db import get_connection

logger = logging.getLogger(__name__)
router = APIRouter()

_basic_auth = HTTPBasic()


def _require_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(_basic_auth)],
) -> str:
    """Basic auth guard. Fails closed if env vars are unset."""
    expected_user = os.environ.get("ADMIN_USER")
    expected_password = os.environ.get("ADMIN_PASSWORD")
    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin dashboard not configured",
        )
    user_ok = secrets.compare_digest(credentials.username, expected_user)
    pass_ok = secrets.compare_digest(credentials.password, expected_password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ---------------------------------------------------------------------------
# Data queries
# ---------------------------------------------------------------------------
def _recent_purchases(limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT purchase_id, tier_id, category, delivery_type, status,
                   buyer_email, amount_cents, currency, created_at, updated_at,
                   download_url_expires_at
              FROM purchases
             ORDER BY created_at DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _pending_consulting_leads() -> list[dict[str, Any]]:
    """Leads with status=qualified AND no follow-up event recorded."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT l.lead_id, l.tier_id, l.buyer_email, l.buyer_name,
                   l.buyer_phone, l.amount_cents, l.created_at
              FROM leads l
             WHERE l.status = ?
               AND NOT EXISTS (
                   SELECT 1 FROM lead_events e
                    WHERE e.lead_id = l.lead_id
                      AND e.event_type IN ('contacted', 'scheduled', 'email_sent')
               )
             ORDER BY l.created_at DESC
            """,
            (crm.LeadStatus.QUALIFIED,),
        ).fetchall()
    return [dict(r) for r in rows]


def _failed_deliveries_last_7_days() -> list[dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT df.id, df.purchase_id, df.error_msg, df.created_at,
                   p.tier_id, p.buyer_email, p.status
              FROM delivery_failures df
              JOIN purchases p ON p.purchase_id = df.purchase_id
             WHERE df.created_at >= ?
             ORDER BY df.created_at DESC
            """,
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
_BASE_CSS = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       max-width: 1200px; margin: 2em auto; padding: 0 1em; color: #222; }
h1 { border-bottom: 2px solid #444; padding-bottom: 0.3em; }
h2 { margin-top: 2em; color: #555; }
table { border-collapse: collapse; width: 100%; font-size: 0.9em; }
th, td { padding: 0.5em 0.75em; text-align: left; border-bottom: 1px solid #eee; }
th { background: #f5f5f5; font-weight: 600; }
tr:hover { background: #fafafa; }
.status-delivered { color: #1a7f37; font-weight: 600; }
.status-refunded { color: #888; }
.status-failed { color: #cf222e; font-weight: 600; }
.status-awaiting_delivery { color: #bf8700; }
.status-disputed { color: #cf222e; font-weight: 600; }
.empty { color: #888; font-style: italic; }
.resend-form { display: inline; }
.resend-btn { background: #0969da; color: white; border: none;
              padding: 0.3em 0.8em; border-radius: 4px; cursor: pointer; font-size: 0.85em; }
.resend-btn:hover { background: #0860c4; }
.summary { background: #f0f7ff; padding: 1em; border-radius: 6px;
           margin-bottom: 1.5em; font-size: 0.9em; }
code { background: #eee; padding: 0.1em 0.3em; border-radius: 3px;
       font-size: 0.85em; }
</style>
"""


def _format_amount(cents: int | None, currency: str | None) -> str:
    if cents is None:
        return "—"
    cur = (currency or "usd").upper()
    return f"${cents / 100:.2f} {cur}"


def _format_status(status_value: str) -> str:
    safe = html.escape(status_value)
    return f'<span class="status-{safe}">{safe}</span>'


def _render_purchases_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="empty">No purchases yet.</p>'
    body = "\n".join(
        f"<tr>"
        f"<td><code>{html.escape(r['purchase_id'])}</code></td>"
        f"<td>{html.escape(r['tier_id'])}</td>"
        f"<td>{html.escape(r['delivery_type'])}</td>"
        f"<td>{_format_status(r['status'])}</td>"
        f"<td>{html.escape(r['buyer_email'])}</td>"
        f"<td>{_format_amount(r['amount_cents'], r['currency'])}</td>"
        f"<td>{html.escape(r['created_at'][:19].replace('T', ' '))}</td>"
        f"</tr>"
        for r in rows
    )
    return (
        "<table><thead><tr>"
        "<th>Purchase</th><th>Tier</th><th>Type</th><th>Status</th>"
        "<th>Buyer</th><th>Amount</th><th>Created</th>"
        "</tr></thead><tbody>"
        f"{body}</tbody></table>"
    )


def _render_leads_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="empty">No pending leads. (Or you have already followed up on all of them.)</p>'
    body = "\n".join(
        f"<tr>"
        f"<td><code>{html.escape(r['lead_id'])}</code></td>"
        f"<td>{html.escape(r['tier_id'])}</td>"
        f"<td>{html.escape(r['buyer_email'])}</td>"
        f"<td>{html.escape(r['buyer_name'] or '—')}</td>"
        f"<td>{html.escape(r['buyer_phone'] or '—')}</td>"
        f"<td>{_format_amount(r['amount_cents'], 'usd')}</td>"
        f"<td>{html.escape(r['created_at'][:19].replace('T', ' '))}</td>"
        f"</tr>"
        for r in rows
    )
    return (
        "<table><thead><tr>"
        "<th>Lead</th><th>Tier</th><th>Email</th><th>Name</th>"
        "<th>Phone</th><th>Amount</th><th>Created</th>"
        "</tr></thead><tbody>"
        f"{body}</tbody></table>"
    )


def _render_failures_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="empty">No failed deliveries in the last 7 days. ✓</p>'
    body = "\n".join(
        f"<tr>"
        f"<td><code>{html.escape(r['purchase_id'])}</code></td>"
        f"<td>{html.escape(r['tier_id'])}</td>"
        f"<td>{html.escape(r['buyer_email'])}</td>"
        f"<td>{_format_status(r['status'])}</td>"
        f"<td>{html.escape((r['error_msg'] or '')[:120])}</td>"
        f"<td>{html.escape(r['created_at'][:19].replace('T', ' '))}</td>"
        f'<td>'
        f'  <form class="resend-form" method="POST" action="/admin/sales/resend/{html.escape(r["purchase_id"])}" '
        f'        onsubmit="return confirm(\'Resend delivery for {html.escape(r["purchase_id"])}?\');">'
        f'    <button class="resend-btn" type="submit">Resend</button>'
        f'  </form>'
        f"</td>"
        f"</tr>"
        for r in rows
    )
    return (
        "<table><thead><tr>"
        "<th>Purchase</th><th>Tier</th><th>Buyer</th><th>Status</th>"
        "<th>Error</th><th>Failed at</th><th>Action</th>"
        "</tr></thead><tbody>"
        f"{body}</tbody></table>"
    )


# ---------------------------------------------------------------------------
# GET /admin/sales — the dashboard
# ---------------------------------------------------------------------------
@router.get("/admin/sales", response_class=HTMLResponse)
def sales_dashboard(user: Annotated[str, Depends(_require_admin)]) -> HTMLResponse:
    purchases = _recent_purchases(limit=50)
    leads = _pending_consulting_leads()
    failures = _failed_deliveries_last_7_days()

    total_cents = sum(r["amount_cents"] for r in purchases if r["status"] == "delivered")
    summary = (
        f"<div class='summary'>"
        f"<strong>{len(purchases)}</strong> recent purchases · "
        f"<strong>{len(leads)}</strong> pending consulting leads · "
        f"<strong>{len(failures)}</strong> failed deliveries (7d) · "
        f"<strong>${total_cents / 100:,.2f}</strong> delivered revenue (last 50)"
        f"</div>"
    )

    body = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>Sidebar Code — Sales Admin</title>{_BASE_CSS}</head><body>"
        f"<h1>Sidebar Code — Sales Admin</h1>"
        f"<p>Logged in as <code>{html.escape(user)}</code>. "
        f"Generated {datetime.now(timezone.utc).isoformat()}</p>"
        f"{summary}"
        f"<h2>Last 50 purchases</h2>"
        f"{_render_purchases_table(purchases)}"
        f"<h2>Pending consulting leads</h2>"
        f"{_render_leads_table(leads)}"
        f"<h2>Failed deliveries (last 7 days)</h2>"
        f"{_render_failures_table(failures)}"
        f"</body></html>"
    )
    return HTMLResponse(body)


# ---------------------------------------------------------------------------
# Resend action
# ---------------------------------------------------------------------------
def _resend_purchase(purchase_id: str) -> None:
    """Background task — re-runs delivery for a previously failed purchase."""
    purchase = crm.get_purchase_by_id(purchase_id)
    if purchase is None:
        logger.error("resend requested for unknown purchase_id=%s", purchase_id)
        return
    logger.info("resend triggered for purchase_id=%s", purchase_id)
    try:
        delivery.build_and_deliver_zip(purchase)
    except Exception:
        logger.exception("resend FAILED for purchase_id=%s", purchase_id)


@router.post("/admin/sales/resend/{purchase_id}")
def resend_delivery(
    purchase_id: str,
    background_tasks: BackgroundTasks,
    user: Annotated[str, Depends(_require_admin)],
) -> RedirectResponse:
    purchase = crm.get_purchase_by_id(purchase_id)
    if purchase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown purchase: {purchase_id}",
        )
    background_tasks.add_task(_resend_purchase, purchase_id)
    logger.info("resend queued for purchase_id=%s by user=%s", purchase_id, user)
    return RedirectResponse(url="/admin/sales", status_code=status.HTTP_303_SEE_OTHER)
