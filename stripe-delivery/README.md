# Sidebar Code — Stripe + Delivery Service (SP2)

FastAPI service that turns sidebarcode.com into a working storefront. Reads
`CATALOG_INDEX.yaml` from SP1, creates Stripe Checkout sessions, processes
Stripe webhooks, and delivers the purchased tier automatically.

Two delivery branches:
- **zip_download** — zips `_customer_deliverables/`, uploads to Cloudflare R2,
  emails the buyer a 72-hour signed download URL via Postmark.
- **notify_kyle** — writes a CRM lead to SQLite, emails Kyle, emails the buyer
  a receipt plus a scheduling link.

Source of truth for pricing and delivery type is `CATALOG_INDEX.yaml`. No code
changes are required to adjust prices or add a tier.

## Run locally

```bash
cd stripe-delivery
python -m venv .venv && source .venv/Scripts/activate  # Windows bash
pip install -r requirements.txt
cp .env.example .env        # fill in Stripe test keys, R2 dev bucket, etc.
uvicorn api.main:app --reload
pytest
```

See `docs/superpowers/specs/2026-04-13-stripe-delivery-design.md` for the full
spec and `docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md` for
the session-by-session build plan.
