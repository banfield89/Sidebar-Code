# Sidebar Code Stripe Integration + Delivery Automation Spec
## Sub-Project 2 of 4: Storefront and Delivery

**Date:** April 13, 2026
**Author:** Kyle Banfield + Claude
**Status:** Pending Kyle review
**Scope:** Turn the Sidebar Code website into a working storefront for all 8 tiers with automated delivery for product tiers and assisted handoff for consulting/workflow tiers
**Approach:** Stripe Checkout + webhook handler + catalog-driven delivery pipeline reading from `CATALOG_INDEX.yaml`

---

## Table of Contents

1. [Goal and Success Criteria](#1-goal-and-success-criteria)
2. [System Architecture](#2-system-architecture)
3. [Stripe Product Provisioning](#3-stripe-product-provisioning)
4. [Checkout Flow](#4-checkout-flow)
5. [Webhook and Delivery Pipeline](#5-webhook-and-delivery-pipeline)
6. [Storage, Security, and Compliance](#6-storage-security-and-compliance)
7. [Observability, Refunds, and Failure Handling](#7-observability-refunds-and-failure-handling)
8. [Deployment and Environments](#8-deployment-and-environments)
9. [Interfaces to Sub-Projects 3-4](#9-interfaces-to-sub-projects-3-4)
10. [Work Sequence](#10-work-sequence)
11. [Review Gates and Quality Standards](#11-review-gates-and-quality-standards)

---

## 1. Goal and Success Criteria

### Goal

A buyer visiting sidebarcode.com can purchase any of the 8 advertised tiers without Kyle touching the transaction, and the right thing happens automatically based on the tier's `delivery_type`:

- **Product tiers** (Parser Trial $197, Full Litigation Suite $2,997) → buyer receives a time-limited signed download link to a freshly-zipped copy of that tier's `_customer_deliverables/` folder within 60 seconds of payment capture.
- **Consulting and custom workflow tiers** → Kyle is notified (email + CRM entry + calendar placeholder), the buyer receives a receipt and a scheduling link, and the lead enters the intake pipeline that Steward will run in Sub-Project 3.

### Decomposition Context

Sub-Project 2 is the monetization and fulfillment layer. It is the only sub-project where money moves. It reads from Sub-Project 1's outputs and writes to a CRM schema that Sub-Project 3 consumes.

- **Sub-Project 1 (done/in progress):** Product Catalog Build-Out — source of all deliverable content and `CATALOG_INDEX.yaml`
- **Sub-Project 2 (this spec):** Stripe + Delivery — this layer
- **Sub-Project 3:** Steward operationalized — consumes the CRM leads this sub-project creates
- **Sub-Project 4:** Scout/Raven/Herald — outbound agents that route into checkout URLs this sub-project owns

### In Scope

- Stripe account configuration, product and price provisioning driven by `CATALOG_INDEX.yaml`
- Checkout flow integrated into [index.html](../../../index.html): buy button per tier, hosted Stripe Checkout session, success and cancel pages
- Webhook listener (FastAPI or equivalent) handling `checkout.session.completed`, `charge.refunded`, `charge.dispute.created`
- Delivery pipeline:
  - `zip_download` branch: zip `_customer_deliverables/`, upload to object storage, generate signed URL, email to buyer
  - `notify_kyle` branch: email Kyle, create CRM lead record, email buyer a scheduling link
- Email infrastructure (transactional) for receipts, download links, and Kyle notifications
- ToS and Technology Overview acceptance checkbox wired to Checkout metadata (required before pay)
- Tax handling via Stripe Tax (automatic calculation for US states)
- Basic refund and dispute handling playbook (automated revocation of download links on refund)
- Lead/CRM data model (JSON schema + storage) that Sub-Project 3 can consume
- Deploy pipeline: GitHub → Render (static site) + Render web service (webhook handler)
- Staging environment with Stripe test mode
- Minimal analytics: conversion funnel, per-tier purchase counts, refund rate

### Out of Scope

- Steward agent operational logic (Sub-Project 3 handles inbound responses)
- Outbound lead-gen agents (Sub-Project 4)
- Customer account/portal (no login in MVP; delivery via email link only)
- Subscription pricing (all tiers are one-time flat fees)
- International tax/VAT (US-only at MVP; add later if demand proves out)
- In-app upsell flows beyond a single "related tier" callout on the success page
- Fraud scoring beyond Stripe Radar defaults
- Full-featured CRM (use a lightweight JSON/SQLite store; real CRM is a later decision)

### Success Criteria

All must be true for SP2 complete:

1. A test purchase of the Parser Trial on staging completes end-to-end: buyer receives signed download link within 60 seconds, link expires at 72 hours, ZIP contains the exact contents of `products/01_parser_trial/_customer_deliverables/` at the time of purchase.
2. A test purchase of the Full Litigation Suite completes end-to-end with the same guarantees.
3. A test purchase of Foundation Consulting creates a CRM lead record, emails Kyle, and emails the buyer a receipt plus a Calendly-style scheduling link.
4. Stripe Tax computes sales tax for a US buyer in at least 3 states correctly.
5. A refund issued in the Stripe dashboard revokes the buyer's download link within 5 minutes.
6. `CATALOG_INDEX.yaml` is the only source Kyle edits to change prices or add/remove a tier — no code changes required for a price update.
7. Webhook handler signature-verifies every Stripe event and rejects unsigned requests.
8. ToS + Technology Overview acceptance is recorded in Stripe metadata for every purchase, with timestamp and IP.
9. The live site on sidebarcode.com passes a manual purchase of the Parser Trial using a real card (Kyle's own) and the money lands in the Sidebar Code Stripe account.
10. A disaster-recovery exercise confirms that if the webhook service is down, Stripe retries and delivery still succeeds once the service is back.

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Payment provider | Stripe Checkout (hosted) not Stripe Elements | Minimizes PCI scope; faster to ship; proven |
| Webhook backend | FastAPI + Python, deployed as Render web service | Matches existing stack (review-dashboard is FastAPI); Python-native zip/upload |
| Delivery storage | Cloudflare R2 (S3-compatible) | Zero egress cost, cheaper than S3, signed URLs supported |
| Signed URL TTL | 72 hours, 5 download attempts max | Long enough for travel/forwarding; short enough to limit leakage |
| Zip generation | On-demand per purchase, not pre-built | Always current; no stale cache risk after catalog updates |
| CRM store | SQLite with JSON columns at MVP; Postgres later | Avoids infra until volume justifies |
| Transactional email | Postmark (or Resend) | Stripe Email receipts aren't customizable enough for download links |
| ToS acceptance | Checkbox on pre-checkout page, passed to Stripe via `metadata` | Auditable; ties to specific Stripe session |
| Tax | Stripe Tax enabled US-only | Sufficient for MVP; expand when international demand proves out |
| Catalog source | `CATALOG_INDEX.yaml` is single source of truth | Zero code changes to adjust price/tier; SP1 already structured for this |
| Environments | `staging.sidebarcode.com` + prod | Full Stripe test-mode loop on staging before every deploy |
| Secrets | Render environment variables; no secrets in repo | Standard |

---

## 2. System Architecture

### High-level flow

```
Buyer -> sidebarcode.com (static)
       -> "Buy" button on tier card
       -> /api/checkout (FastAPI)
           reads CATALOG_INDEX.yaml
           creates Stripe Checkout Session with metadata
       -> Stripe Checkout (hosted)
           collects payment + tax + ToS acceptance
       -> success.html  [redirect]
           (shows "check your email" and scheduling link if applicable)

Stripe async:
       -> POST /api/webhook (FastAPI)
           verify signature
           branch on tier delivery_type:
             zip_download  -> zip _customer_deliverables/
                              upload to R2
                              generate signed URL (72h)
                              email buyer via Postmark
                              record purchase in SQLite
             notify_kyle   -> create CRM lead in SQLite
                              email Kyle
                              email buyer with receipt + scheduler link
                              record purchase
```

### Components

| Component | Tech | Hosted where | Purpose |
|---|---|---|---|
| Static site | HTML/CSS/JS | Render static (auto-deploy from GitHub) | Marketing + buy buttons |
| Checkout API | FastAPI | Render web service | Creates Stripe Sessions from catalog |
| Webhook handler | FastAPI (same service) | Render web service | Processes Stripe events, delivers |
| Zip builder | Python (zipfile) | Same service, background task | Packages deliverables on demand |
| Object storage | Cloudflare R2 | Cloudflare | Stores generated ZIPs, signed URLs |
| Email | Postmark API | Postmark | Receipts, download links, Kyle notifications |
| CRM store | SQLite + JSON cols | Render persistent disk (5GB) | Leads and purchase records |
| Monitoring | Render logs + Postmark logs + Stripe dashboard | N/A | Observability |

### Data flow contracts

- **Static site → Checkout API:** `POST /api/checkout` with `{ tier_id: string, tos_accepted: bool, tech_overview_accepted: bool }`. Returns Stripe Checkout URL.
- **Checkout API → Stripe:** creates Checkout Session with `line_items` from catalog, `metadata` = `{ tier_id, tos_accepted_at, tech_overview_accepted_at, buyer_ip }`, `success_url`, `cancel_url`.
- **Stripe → Webhook:** signed `checkout.session.completed` event, contains session metadata.
- **Webhook → R2:** uploads `{tier_id}-{session_id}.zip`.
- **Webhook → Postmark:** sends templated email with signed URL.
- **Webhook → SQLite:** inserts purchase row.

---

## 3. Stripe Product Provisioning

### Source of truth

`CATALOG_INDEX.yaml` (produced by SP1) contains the full product registry. SP2 adds a provisioning script that reads this file and syncs Stripe.

Required fields per entry (SP1 already writes these):

```yaml
products:
  - tier_id: product_parser_trial
    stripe_product_name: "Sidebar Code Parser Trial"
    stripe_product_description: "One-line marketing description under 350 chars"
    price: 197
    currency: usd
    delivery_type: zip_download
    delivery_source: "Product Catalog/products/01_parser_trial/_customer_deliverables/"
    tax_code: "txcd_10502000"  # Digital goods / downloadable software

consulting:
  - tier_id: consulting_foundation
    stripe_product_name: "Sidebar Code Foundation Package"
    stripe_product_description: "90-minute consulting session with one skill deployed live"
    price: 2500  # placeholder — Kyle confirms before provisioning
    currency: usd
    delivery_type: notify_kyle
    scheduling_link: "https://cal.com/kylebanfield/foundation"
    tax_code: "txcd_20030000"  # Professional services

custom_workflows:
  - tier_id: workflow_single
    # same pattern
```

### Provisioning script

`scripts/sync_stripe_catalog.py`:

1. Reads `CATALOG_INDEX.yaml`.
2. For each tier: upsert Stripe Product (by `tier_id` stored in Product `metadata.tier_id`), upsert Price (create new Price if amount changed; archive old Price; never edit a Price in place).
3. Writes back a `stripe_product_id` and `stripe_price_id` into a sibling file `CATALOG_INDEX.stripe.yaml` (not committed — stored on Render disk or in env secret).
4. Outputs a diff: what was added, changed, archived.

Run as a manual script on catalog updates. Not an automatic deploy hook at MVP — Kyle runs it after any price/tier change.

### Handling price changes

Stripe Prices are immutable. The script archives the old Price and creates a new one. Outstanding Checkout Sessions using the old Price still honor it; new sessions use the new Price. This is the correct Stripe idiom and avoids race conditions.

---

## 4. Checkout Flow

### Pre-checkout page

Each tier card on [index.html](../../../index.html) gets a "Buy" button (product tiers) or "Get started" button (consulting/workflow tiers). Clicking opens a modal with:

1. Tier summary pulled from `_sales_packet/what_is_in_the_box.md` (short version).
2. Price, one-time flat fee disclosure, firm-wide internal license language.
3. **Prerequisite disclosure:** "Requires Claude Code + Anthropic subscription or API key, billed separately."
4. Two required checkboxes:
   - "I have read and accept the [Terms of Service](../../../terms.html)."
   - "I have read and accept the [Technology Overview and Limitations Guide](../../../Product%20Catalog/shared/technology_overview.md)."
5. "Proceed to Checkout" button — disabled until both checkboxes are ticked.

On click, the button calls `POST /api/checkout` with the tier_id and acceptance booleans. The API returns a Stripe Checkout URL; the browser redirects.

### Stripe Checkout (hosted)

- Collects billing address (required for Stripe Tax).
- Collects payment method.
- Displays the ToS + Technology Overview acceptance timestamps in the metadata (not shown to buyer, but recorded for audit).
- On success → redirect to `/success?session_id={CHECKOUT_SESSION_ID}`.
- On cancel → redirect to `/cancel` (friendly message, offer to contact Kyle).

### Success page

- Reads `session_id` from query string, calls `GET /api/session/{session_id}` to fetch the tier_id and delivery_type.
- **zip_download:** "Your download link has been emailed to {buyer_email}. It expires in 72 hours. If you don't see it in 5 minutes, check spam or contact support@sidebarcode.com."
- **notify_kyle:** "Thanks for your purchase. Kyle will reach out within 1 business day. You can also [schedule directly on his calendar]({scheduling_link})."
- Related tier callout: a single suggested upgrade path (e.g., Parser Trial → Full Suite).

### Cancel page

- "No charge was made. If you have questions, email support@sidebarcode.com."
- Back-to-home button.

---

## 5. Webhook and Delivery Pipeline

### Events handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Trigger delivery pipeline for the tier |
| `charge.refunded` | Revoke download link, mark purchase as refunded, notify Kyle |
| `charge.dispute.created` | Flag purchase, notify Kyle, do not auto-revoke |
| `charge.dispute.closed` | Update purchase status based on outcome |

### Delivery pipeline — `zip_download`

Runs as a background task (FastAPI `BackgroundTasks`) so webhook returns `200` fast enough for Stripe's 5-second requirement.

Steps:

1. Look up the tier in `CATALOG_INDEX.yaml` by `tier_id` from session metadata.
2. Resolve `delivery_source` to an absolute path on the server (deliverables are baked into the service image at deploy time — see Section 8).
3. Zip the folder in-memory or to a temp file. Include a top-level `README.txt` with purchase info, license summary, and support contact.
4. Upload to R2 as `{tier_id}/{session_id}.zip` with server-side encryption.
5. Generate signed URL with 72-hour TTL using R2's presign API.
6. Insert purchase row in SQLite: `purchase_id, tier_id, session_id, stripe_charge_id, buyer_email, amount_cents, currency, created_at, zip_object_key, download_url_expires_at, download_attempts, status='delivered'`.
7. Call Postmark with template `product_download`, merge vars: buyer name, tier name, download URL, expiry, support email.
8. On any step failure: see the **Retry strategy** in Section 7. Each external call (R2, Postmark) retries once with a 1-second backoff before raising. The `delivery_failures` row and Postmark alert are written ONLY after the second failure. The function then re-raises so Stripe's webhook retry kicks in (do NOT catch-and-suppress at the handler boundary).

### Delivery pipeline — `notify_kyle`

1. Look up tier in `CATALOG_INDEX.yaml`.
2. Insert CRM lead row in SQLite: `lead_id, tier_id, session_id, stripe_charge_id, buyer_email, buyer_name, buyer_phone, amount_cents, currency, created_at, status='new', source='stripe_purchase'`.
3. Insert purchase row (same table as zip_download path) with `status='awaiting_delivery'`.
4. Postmark Kyle via template `kyle_new_consulting_purchase`: buyer info, tier, amount, scheduling link, CRM deep-link.
5. Postmark buyer via template `consulting_receipt`: receipt, what happens next, scheduling link, Kyle's direct email.

### Refund handling

`charge.refunded` handler:

1. Look up purchase by `stripe_charge_id`.
2. For `zip_download` tiers: delete R2 object, set `download_url_expires_at=now`, status `refunded`. The signed URL becomes invalid (deleted object returns 404; even cached URLs fail).
3. For `notify_kyle` tiers: status `refunded`, Postmark Kyle to stop work.
4. Audit log entry.

---

## 6. Storage, Security, and Compliance

### Secrets management

All secrets live in Render environment variables. `.env.example` in the repo lists variable names only (no values):

```
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PUBLISHABLE_KEY=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=
POSTMARK_API_TOKEN=
KYLE_ALERT_EMAIL=
SQLITE_PATH=
SITE_BASE_URL=
```

### Webhook signature verification

Every incoming webhook MUST pass `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`. Requests that fail verification return `400` and are logged but not processed. No exceptions.

### Signed URL security

- R2 signed URLs are bearer tokens. Treat them as secrets in email content.
- Emails go only to the billing email on the Stripe session.
- Download attempts are logged. More than 5 attempts triggers an alert to Kyle.
- URLs expire at 72 hours absolute (not rolling).

### ToS and Technology Overview acceptance audit

Every purchase records:
- `tos_version` (hash of [terms.html](../../../terms.html) content at purchase time)
- `tos_accepted_at` (ISO timestamp)
- `tech_overview_version` (hash)
- `tech_overview_accepted_at`
- `buyer_ip` (from Stripe Checkout metadata)

This data is stored in the purchase row AND written to Stripe metadata for redundancy. Ethics audit defense requires this chain.

### PCI scope

Hosted Stripe Checkout means Sidebar Code never touches card data. PCI scope is minimal (SAQ A). Document this in the privacy policy.

### Data retention

- Purchase rows: retained 7 years (tax/accounting).
- CRM lead rows: retained until manually archived.
- Generated ZIPs in R2: deleted 7 days after `download_url_expires_at` (housekeeping job runs nightly).
- Webhook payloads: retained 30 days for debugging.

---

## 7. Observability, Refunds, and Failure Handling

### Monitoring

- **Render logs:** all webhook events, all delivery attempts, all errors.
- **Postmark dashboard:** delivery, bounce, open rates for all transactional emails.
- **Stripe dashboard:** the canonical revenue and refund source.
- **Kyle-facing dashboard (lightweight):** single page at `/admin/dashboard` (basic auth) showing last 50 purchases, pending consulting leads, failed deliveries needing retry.

### Metrics tracked

Per tier, per day:
- Checkout sessions created
- Checkout sessions completed (conversion)
- Successful deliveries
- Failed deliveries
- Refunds
- Disputes

### Alerting

Postmark → Kyle when:
- Any delivery fails twice in a row
- Any webhook signature verification fails
- A dispute is opened
- Daily digest of all purchases (even on zero-purchase days, so Kyle notices if the pipeline silently dies)

### Retry strategy

Two layers of retry, working independently:

**Layer 1 — In-process retry (handler-side, NEW per Q7 decision 2026-04-13):**
- Each external call inside the delivery handler (R2 upload, Postmark send, etc.) is wrapped in a retry-once-then-raise pattern.
- Pattern: attempt → if exception → wait 1 second → attempt again → if exception → raise.
- Rationale: filters transient blips (R2 momentary 503, Postmark momentary timeout) without burying real failures or paging Kyle for noise.
- Implementation: a small `retry_once(callable, *args, backoff_seconds=1.0)` helper in `api/delivery.py`. NOT a generic decorator — explicit per call site so failures are obvious in traces.
- The `delivery_failures` row is inserted ONLY after the second failure of any external call, never on the first.
- The `delivery_failure_alert` Postmark email is sent ONLY after the second failure.
- After raising, the function bubbles the exception up to the webhook handler, which propagates to Stripe.

**Layer 2 — Stripe webhook retry:**
- Stripe retries the entire webhook event for up to 3 days with exponential backoff if the handler returns non-2xx or times out.
- This catches catastrophic failures: webhook service down, database hard-locked, two consecutive Layer-1 retries both failing.
- Handler MUST be idempotent so Stripe retries don't double-deliver: `stripe_event_id` is the primary key in `processed_events`, short-circuit if already seen.
- Zip generation is deterministic per session_id, so regenerating on retry is safe.

**Why both layers exist:**
- Layer 1 is fast and silent. It absorbs the 90% case of "R2 had a hiccup, retry succeeded, customer never noticed."
- Layer 2 is slow and visible. It absorbs the 9% case of "service was down for 3 minutes, the event got reprocessed, customer got their download 4 minutes late."
- The 1% case of "actually broken, alert Kyle" only fires after both layers fail, which is exactly when human attention is warranted.

**What this changes from the original spec:** The original spec said "alert Kyle on first failure." That was overridden by the 2026-04-13 PRE Q7 decision in DECISIONS_PARKING_LOT.md to reduce alert noise from transient issues.

### Failure modes worth planning for

| Failure | Detection | Recovery |
|---|---|---|
| R2 upload fails (transient) | Exception in handler | Layer-1 retry-once succeeds silently; no alert |
| R2 upload fails (persistent) | Two consecutive Layer-1 failures | Alert Kyle; Stripe webhook retry kicks in |
| Postmark send fails (transient) | Exception on first send | Layer-1 retry-once succeeds silently; no alert |
| Postmark send fails (persistent) | Two consecutive Layer-1 failures | Alert Kyle via fallback channel; resends manually |
| Postmark bounce after delivery | Postmark bounce webhook | Kyle alerted, resends manually |
| Zip corrupted | Size/checksum mismatch | Regenerate; email apology + new link |
| Webhook service down | Stripe retry queue | Event reprocessed when service returns |
| Database locked | SQLite write timeout | Retry with backoff; Postgres upgrade if persistent |
| Buyer reports never received | Support ticket | Admin dashboard "resend" button generates new signed URL |

---

## 8. Deployment and Environments

### Environments

- **Development:** local, SQLite file, Stripe test mode, Postmark sandbox, R2 dev bucket
- **Staging:** `staging.sidebarcode.com`, Render preview deploy, Stripe test mode, Postmark test stream, R2 staging bucket
- **Production:** `sidebarcode.com`, Render production, Stripe live mode, Postmark production, R2 prod bucket

### Deploy pipeline

- Static site (`index.html`, `terms.html`, etc.): Render static site, auto-deploys on push to `main`.
- Webhook service: Render web service, auto-deploys on push to `main`.
- Deliverables folder (`Product Catalog/`): **committed to the repo** so deploys bake the current catalog state into the image. This means a catalog content update requires a deploy. Acceptable at MVP volumes.

### Rollback

- Render supports one-click rollback to any prior deploy.
- If a bad deploy breaks checkout: roll back, Stripe retries any pending webhooks against the restored version.

### Pre-production checklist (blocks go-live)

1. All 8 tiers provisioned in live Stripe account with correct prices.
2. Live webhook endpoint registered with Stripe and signature verified on a test event.
3. R2 production bucket lifecycle rule for 7-day ZIP cleanup active.
4. Postmark production sender domain verified, SPF/DKIM configured.
5. ToS page reviewed by Aemon.
6. Technology Overview reviewed by Aemon.
7. Kyle completes a live purchase of each tier with his own card (refund after).
8. Admin dashboard basic auth set.
9. Backup of SQLite to R2 daily (cron).
10. Incident runbook written and saved to `_ops/INCIDENT_RUNBOOK.md`.

---

## 9. Interfaces to Sub-Projects 3-4

### Interface to Sub-Project 3: Steward

Steward reads from the CRM store this sub-project writes. Schema contract:

```sql
CREATE TABLE leads (
  lead_id TEXT PRIMARY KEY,
  tier_id TEXT NOT NULL,
  source TEXT NOT NULL,  -- 'stripe_purchase', 'web_inquiry', 'manual'
  status TEXT NOT NULL,  -- 'new', 'contacted', 'qualified', 'closed_won', 'closed_lost'
  buyer_email TEXT NOT NULL,
  buyer_name TEXT,
  buyer_phone TEXT,
  buyer_firm TEXT,
  intake_payload JSON,   -- matches intake_schema for that tier
  stripe_charge_id TEXT, -- null if not a paid lead
  amount_cents INTEGER,
  created_at TEXT NOT NULL,
  next_action_at TEXT,
  notes JSON
);

CREATE TABLE lead_events (
  event_id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL,
  event_type TEXT NOT NULL,  -- 'created', 'email_sent', 'email_received', 'scheduled', 'status_changed'
  event_data JSON,
  created_at TEXT NOT NULL,
  FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);
```

Steward will:
- Read `leads` where `status='new'` and run its inquiry workflow
- Write `lead_events` rows for every action it takes
- Update `leads.status` and `leads.next_action_at` as it progresses

SP2 MUST NOT assume Steward exists. The `notify_kyle` path works fully without Steward; Steward is an enhancement that picks up the same leads.

### Interface to Sub-Project 4: Scout/Raven/Herald

Outbound agents write leads to the same `leads` table with `source='scout'`, `source='raven'`, or `source='herald'`. They also write UTM parameters and campaign IDs into `notes` so attribution works when those leads eventually convert through Stripe Checkout.

The static site supports `?utm_source=...&utm_campaign=...` in checkout URLs; the checkout API writes UTM params into Stripe session metadata, which the webhook copies into the purchase row.

### What this sub-project does NOT do for SP3/SP4

- No agent orchestration
- No email parsing
- No outbound sending
- No lead scoring

All of that is SP3/SP4. This sub-project just writes the data those projects read.

---

## 10. Work Sequence

Phased so Kyle can review and course-correct at each checkpoint.

### Phase 1: Foundations (Week 1)

1. Stripe account setup, Stripe Tax enabled US-only, Radar enabled.
2. Cloudflare R2 buckets created (dev, staging, prod) with lifecycle rules.
3. Postmark account setup, sender domain `sidebarcode.com` verified with SPF/DKIM, templates drafted (`product_download`, `consulting_receipt`, `kyle_new_consulting_purchase`, `delivery_failure_alert`).
4. Render services provisioned: static site, web service for checkout + webhook, persistent disk.
5. Secrets management: all env vars set in Render, `.env.example` committed.

### Phase 2: Checkout API (Week 1-2)

6. FastAPI skeleton with `/health`, `/api/checkout`, `/api/session/{id}`, `/api/webhook` routes.
7. Catalog loader: `load_catalog_index()` reads `CATALOG_INDEX.yaml` from disk, caches in memory.
8. `/api/checkout` creates Stripe Checkout Session with metadata, returns URL.
9. `scripts/sync_stripe_catalog.py`: upsert products and prices from catalog.
10. Run sync against Stripe test mode, verify products appear with correct prices.

### Phase 3: Webhook Handler and Delivery (Week 2)

11. Webhook signature verification.
12. `processed_events` idempotency table + middleware.
13. Zip builder: recursive zip of `_customer_deliverables/` with README injection.
14. R2 upload + signed URL generation.
15. `zip_download` branch complete: end-to-end Parser Trial test in staging.
16. SQLite schema created, purchase row inserted on delivery.
17. Postmark integration, `product_download` template tested.
18. `notify_kyle` branch: CRM lead insertion, Kyle alert, buyer receipt.

### Phase 4: Pre-Checkout UX (Week 2-3)

19. Tier card "Buy" buttons wired into modal.
20. ToS + Technology Overview acceptance checkboxes with version hashing.
21. Success page with tier-aware messaging.
22. Cancel page.
23. Related-tier callout data wired from `CATALOG_INDEX.yaml`.

### Phase 5: Refunds, Disputes, Monitoring (Week 3)

24. `charge.refunded` handler: R2 delete, purchase status update, Kyle alert.
25. `charge.dispute.created` handler: flag, alert, no auto-revoke.
26. Admin dashboard at `/admin/dashboard` (basic auth): last 50 purchases, failed deliveries, pending leads, resend button.
27. Daily digest email to Kyle (even on zero-purchase days).
28. Housekeeping cron: delete old R2 ZIPs, nightly SQLite backup to R2.

### Phase 6: Pre-Production Hardening (Week 3-4)

29. Load test: 50 simulated concurrent checkouts in staging.
30. Disaster recovery exercise: stop webhook service, run purchase, restart, confirm delivery completes.
31. Aemon reviews ToS, Technology Overview, receipt/download email language, refund policy.
32. Incident runbook written.
33. Live-mode switch: provision products in live Stripe, update env vars, deploy.
34. Kyle test purchases each of 8 tiers with his own card; refunds after verification.

### Phase 7: Launch (Week 4)

35. DNS cutover (if not already live).
36. Announce to Kyle's network (tie-in with Sub-Project 4 when ready).
37. Monitor for 7 days, daily check-in on admin dashboard.
38. Write `_ops/SP2_HANDOFF_NOTES.md` for Sub-Projects 3-4.

---

## 11. Review Gates and Quality Standards

### Aemon review (legal/ethics)

Must review before go-live:
- ToS page ([terms.html](../../../terms.html))
- Technology Overview and Limitations Guide
- Refund policy language
- Email templates for buyer-facing communications
- Purchase receipt language (no language implying legal advice)
- Prerequisite disclosure (Claude Code + Anthropic subscription)
- ToS acceptance audit trail (sufficient for enforceability)

### Kyle review

- Price list before Stripe provisioning
- All email templates for voice/tone
- Admin dashboard layout
- Success/cancel page copy
- The actual purchase experience on staging before live

### Security review

- Webhook signature verification test suite
- Signed URL TTL and download attempt limits
- Admin dashboard auth
- Secret scanning in repo (`gitleaks` or equivalent in CI)
- Dependency vulnerability scan (`pip-audit`)

### Quality bar for customer-facing content

Same rules as Sub-Project 1:
- No em-dashes
- No implied legal advice
- Plain English
- Every email has a human-reachable support address
- Every failure path has a recovery option visible to the buyer

---

## Appendix A: File Layout

```
Side Bar Code/
  stripe-delivery/                        # new in SP2
    api/
      main.py                             # FastAPI app
      checkout.py                         # /api/checkout
      webhook.py                          # /api/webhook
      catalog.py                          # CATALOG_INDEX.yaml loader
      delivery.py                         # zip + R2 + Postmark
      crm.py                              # SQLite models for leads + purchases
      admin.py                            # /admin/dashboard
    scripts/
      sync_stripe_catalog.py              # Stripe product/price provisioner
      backup_sqlite.py                    # nightly backup to R2
      cleanup_r2.py                       # delete expired ZIPs
    templates/
      emails/
        product_download.html
        consulting_receipt.html
        kyle_new_consulting_purchase.html
        delivery_failure_alert.html
        daily_digest.html
      pages/
        success.html
        cancel.html
    tests/
      test_webhook_idempotency.py
      test_zip_builder.py
      test_catalog_loader.py
      test_refund_flow.py
    _ops/
      INCIDENT_RUNBOOK.md
      SP2_HANDOFF_NOTES.md                # written at end of SP2
    requirements.txt
    render.yaml
    .env.example
```

## Appendix B: Open Questions for Kyle

1. Confirm final pricing for all 6 consulting/workflow tiers before Stripe provisioning.
2. Preferred scheduling tool for consulting handoff: Calendly, Cal.com, or something else?
3. Preferred transactional email provider: Postmark or Resend? (Postmark is the default in this spec.)
4. Admin dashboard auth: basic auth for MVP, or wire up a simple login?
5. Should the Parser Trial include an upsell-to-Full-Suite coupon in the download email? (Recommended yes, 10% off within 30 days.)
6. Refund policy: 7-day no-questions-asked, or case-by-case? (Spec assumes case-by-case.)
7. Should failed deliveries auto-retry N times before alerting, or alert on first failure? (Spec: first failure alerts, Stripe's retry handles the rest.)
8. For consulting tiers, should the buyer pay in full at Checkout, or a deposit with balance due after the session? (Spec assumes pay in full.)

---

*End of spec. Version 1.0. Pending Kyle review.*
