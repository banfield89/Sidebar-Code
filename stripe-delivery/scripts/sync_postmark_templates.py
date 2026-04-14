"""Create or update Postmark templates by alias.

Idempotent: re-running with no changes is a no-op. The four templates
have placeholder bodies for now — Kyle replaces the copy in evening
sessions via the Postmark dashboard. The aliases (referenced from
api/delivery.py) never change, so editing the body in Postmark does
not require a code change.

Usage:
    python scripts/sync_postmark_templates.py            # apply changes
    python scripts/sync_postmark_templates.py --dry-run  # report only

Auto-loads ~/.sidebarcode-secrets.env so POSTMARK_API_TOKEN does not
need to be exported beforehand.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
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
    if not os.environ.get("POSTMARK_API_TOKEN") and cleaned.get("POSTMARK_API_TOKEN"):
        os.environ["POSTMARK_API_TOKEN"] = cleaned["POSTMARK_API_TOKEN"]


_autoload_secrets()

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from postmarker.core import PostmarkClient  # noqa: E402


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------
@dataclass
class TemplateSpec:
    alias: str
    name: str
    subject: str
    text_body: str
    html_body: str


PRODUCT_DOWNLOAD = TemplateSpec(
    alias="sp2-product-download",
    name="Sidebar Code — Product Download Ready",
    subject="Your {{tier_name}} is ready to download",
    text_body="""Hi {{buyer_name}},

Thanks for your purchase. Your {{tier_name}} is ready.

Download link (expires {{expires_at}}):
{{download_url}}

Save the file to your computer before the link expires. If you have
trouble downloading, reply to this email or contact {{support_email}}.

Purchase ID: {{purchase_id}}
Order placed: {{purchased_at}}

— Kyle
{{support_email}}
""",
    html_body="""<p>Hi {{buyer_name}},</p>

<p>Thanks for your purchase. Your <strong>{{tier_name}}</strong> is ready.</p>

<p><a href="{{download_url}}">Click here to download</a> — link expires {{expires_at}}.</p>

<p>Save the file to your computer before the link expires. If you have trouble
downloading, reply to this email or contact <a href="mailto:{{support_email}}">{{support_email}}</a>.</p>

<p>Purchase ID: {{purchase_id}}<br>
Order placed: {{purchased_at}}</p>

<p>— Kyle<br>
<a href="mailto:{{support_email}}">{{support_email}}</a></p>
""",
)

CONSULTING_RECEIPT = TemplateSpec(
    alias="sp2-consulting-receipt",
    name="Sidebar Code — Consulting Receipt",
    subject="Receipt for your {{tier_name}} purchase",
    text_body="""Hi {{buyer_name}},

Thanks for purchasing the {{tier_name}}.

Receipt:
  Item:    {{tier_name}}
  Amount:  {{amount_formatted}}
  Order:   {{purchase_id}}
  Date:    {{purchased_at}}

What happens next: I'll reach out within one business day to set up
our session. You can also book directly on my calendar:

{{scheduling_link}}

Questions? Reply to this email or contact {{kyle_email}}.

— Kyle
{{kyle_email}}
""",
    html_body="""<p>Hi {{buyer_name}},</p>

<p>Thanks for purchasing the <strong>{{tier_name}}</strong>.</p>

<p><strong>Receipt:</strong><br>
Item: {{tier_name}}<br>
Amount: {{amount_formatted}}<br>
Order: {{purchase_id}}<br>
Date: {{purchased_at}}</p>

<p><strong>What happens next:</strong> I'll reach out within one business day to
set up our session. You can also <a href="{{scheduling_link}}">book directly on my calendar</a>.</p>

<p>Questions? Reply to this email or contact
<a href="mailto:{{kyle_email}}">{{kyle_email}}</a>.</p>

<p>— Kyle<br>
<a href="mailto:{{kyle_email}}">{{kyle_email}}</a></p>
""",
)

KYLE_NEW_CONSULTING_PURCHASE = TemplateSpec(
    alias="sp2-kyle-new-consulting-purchase",
    name="Sidebar Code — New Consulting Purchase Alert (Kyle)",
    subject="New consulting purchase: {{tier_name}} ({{amount_formatted}})",
    text_body="""New {{tier_name}} purchase just came in.

Buyer:        {{buyer_name}} <{{buyer_email}}>
Phone:        {{buyer_phone}}
Tier:         {{tier_name}} ({{tier_id}})
Amount:       {{amount_formatted}}
Purchase ID:  {{purchase_id}}
Lead ID:      {{lead_id}}
Stripe:       {{stripe_dashboard_link}}

Buyer scheduling link sent in their receipt:
  {{scheduling_link}}

CRM lead row inserted automatically. Reach out within 1 business day.
""",
    html_body="""<p>New <strong>{{tier_name}}</strong> purchase just came in.</p>

<table>
<tr><td>Buyer:</td><td>{{buyer_name}} &lt;<a href="mailto:{{buyer_email}}">{{buyer_email}}</a>&gt;</td></tr>
<tr><td>Phone:</td><td>{{buyer_phone}}</td></tr>
<tr><td>Tier:</td><td>{{tier_name}} ({{tier_id}})</td></tr>
<tr><td>Amount:</td><td>{{amount_formatted}}</td></tr>
<tr><td>Purchase ID:</td><td>{{purchase_id}}</td></tr>
<tr><td>Lead ID:</td><td>{{lead_id}}</td></tr>
<tr><td>Stripe:</td><td><a href="{{stripe_dashboard_link}}">View in Stripe</a></td></tr>
</table>

<p>Buyer scheduling link sent in their receipt: <a href="{{scheduling_link}}">{{scheduling_link}}</a></p>

<p>CRM lead row inserted automatically. Reach out within 1 business day.</p>
""",
)

DELIVERY_FAILURE_ALERT = TemplateSpec(
    alias="sp2-delivery-failure-alert",
    name="Sidebar Code — Delivery Failure Alert (Kyle)",
    subject="DELIVERY FAILED: {{tier_id}} for {{purchase_id}}",
    text_body="""A product delivery failed in SP2. Stripe will retry, but you should
investigate to make sure it's not a persistent error.

Purchase ID:  {{purchase_id}}
Tier:         {{tier_id}}
Buyer:        {{buyer_email}}
Failed at:    {{failed_at}}

Error:
{{error_message}}

Traceback:
{{traceback}}

Render logs:  {{render_logs_link}}
Stripe event: {{stripe_event_link}}
""",
    html_body="""<p>A product delivery failed in SP2. Stripe will retry, but you should
investigate to make sure it's not a persistent error.</p>

<p><strong>Purchase ID:</strong> {{purchase_id}}<br>
<strong>Tier:</strong> {{tier_id}}<br>
<strong>Buyer:</strong> {{buyer_email}}<br>
<strong>Failed at:</strong> {{failed_at}}</p>

<p><strong>Error:</strong></p>
<pre>{{error_message}}</pre>

<p><strong>Traceback:</strong></p>
<pre>{{traceback}}</pre>

<p><a href="{{render_logs_link}}">Render logs</a> |
<a href="{{stripe_event_link}}">Stripe event</a></p>
""",
)

ALL_TEMPLATES = [
    PRODUCT_DOWNLOAD,
    CONSULTING_RECEIPT,
    KYLE_NEW_CONSULTING_PURCHASE,
    DELIVERY_FAILURE_ALERT,
]


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------
def _find_template(client: PostmarkClient, alias: str) -> dict[str, Any] | None:
    """Look up a template by alias. Returns None if not found."""
    try:
        return client.templates.get(template_id=alias)
    except Exception:
        return None


def sync_template(client: PostmarkClient, spec: TemplateSpec, dry_run: bool) -> str:
    existing = _find_template(client, spec.alias)
    if existing is None:
        if dry_run:
            return "would_create"
        client.templates.create(
            Name=spec.name,
            Alias=spec.alias,
            Subject=spec.subject,
            HtmlBody=spec.html_body,
            TextBody=spec.text_body,
        )
        return "created"

    needs_update = (
        existing.get("Name") != spec.name
        or existing.get("Subject") != spec.subject
        or existing.get("TextBody") != spec.text_body
        or existing.get("HtmlBody") != spec.html_body
    )
    if needs_update:
        if dry_run:
            return "would_update"
        client.templates.edit(
            template_id=spec.alias,
            Name=spec.name,
            Subject=spec.subject,
            HtmlBody=spec.html_body,
            TextBody=spec.text_body,
        )
        return "updated"
    return "unchanged"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("POSTMARK_API_TOKEN")
    if not token:
        print("ERROR: POSTMARK_API_TOKEN is not set", file=sys.stderr)
        return 1

    client = PostmarkClient(server_token=token)

    print(f"Syncing {len(ALL_TEMPLATES)} templates...")
    print("-" * 80)
    for spec in ALL_TEMPLATES:
        action = sync_template(client, spec, dry_run=args.dry_run)
        print(f"  {spec.alias:<40} {action}")
    print("-" * 80)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
