# SP1 Swap-In Playbook
## How to flip Sidebar Code SP2 from mock data to real Sub-Project 1 outputs and launch live

**Date created:** 2026-04-13
**Trigger:** Run this playbook the day SP1 (Product Catalog Build-Out) ships its final outputs.
**Estimated wall time:** Half a day (4-6 hours total — agent time + your time).
**Prereqs:** All 8 SP2 day sessions complete and verified in staging with mock data.

---

## What "SP1 ships" means

This playbook starts when SP1 has produced:

1. A real `Product Catalog/CATALOG_INDEX.yaml` listing all 8 tiers with real `tier_id`, `stripe_product_name`, `stripe_product_description`, `price_cents`, `currency`, `delivery_type`, `delivery_source`, `tax_code`, and (for consulting) `scheduling_link`
2. Real `_customer_deliverables/` folders for the 2 product tiers (Parser Trial, Full Litigation Suite) — populated with the actual code/skills/docs that customers will receive
3. The `Product Catalog/shared/technology_overview.md` document Aemon will use during legal review
4. The 8 tier-specific `_sales_packet/what_is_in_the_box.md` summaries (used by index.html modals later, not strictly required for SP2 wiring)

If any of these are missing, **stop and finish them in SP1 first.** Do not partially run this playbook.

---

## Operating principles

- **One pass through this document, no skipping.** Every step depends on the prior one. Don't reorder.
- **Stay in test mode until Step 8.** You only flip to live mode after every test mode check passes.
- **Never run live mode steps from the agent.** Steps 8-10 are Kyle-only with the agent in read-only mode for safety.
- **Aemon must approve before live flip.** Step 6 is a hard gate — no skipping.
- **Idempotent everywhere.** Every script in this playbook can be re-run safely. If a step fails halfway, you can re-run it.
- **Backup before each destructive step.** Every step that mutates the database or external services has a "before you proceed" checkpoint.

---

## Phase 1 — Prep (15 min)

### Step 1.1: Verify SP2 staging is currently green

Before touching anything, confirm SP2 still works with mock data. This is your baseline — if anything regresses during the swap-in, you can compare to this known-good state.

```bash
# Health check
curl https://sidebarcode-api.onrender.com/health
# Expected: {"status":"ok","version":"<sha>","env":"staging"}

# Mock catalog still loads
curl -X POST https://sidebarcode-api.onrender.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier_id":"mock_parser_trial","tos_accepted":true,"tech_overview_accepted":true}'
# Expected: returns checkout_url

# Admin dashboard loads
# Open https://sidebarcode-api.onrender.com/admin/sales (basic auth)
```

If any of these fail, **fix SP2 first** before proceeding. Don't compound problems.

### Step 1.2: Snapshot the mock catalog and Stripe state

So you can roll back if needed:

1. Download `stripe-delivery/mock_catalog_index.yaml` to a local backup folder
2. Take a screenshot of https://dashboard.stripe.com/test/products listing the 3 mock products (so you know what to clean up later)
3. Run a manual SQLite backup:
   ```bash
   # SSH into Render via the Shell tab on sidebarcode-api
   sqlite3 /var/data/sidebarcode.db ".backup /var/data/sidebarcode-pre-swap.db"
   ```

### Step 1.3: Verify SP1 outputs are present

```bash
cd "C:/CLAUDE/projects/Sidebar Code/Side Bar Code"
ls "Product Catalog/CATALOG_INDEX.yaml"
ls "Product Catalog/shared/technology_overview.md"
ls "Product Catalog/products/01_parser_trial/_customer_deliverables/"
ls "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"
```

All 4 should exist and be non-empty. Sample the catalog YAML to confirm it has all 8 tiers:

```bash
grep "tier_id:" "Product Catalog/CATALOG_INDEX.yaml" | wc -l
# Expected: 8
```

---

## Phase 2 — Schema reconciliation (30 min)

### Step 2.1: Audit the catalog field names

The mock catalog uses `price_cents` (integer cents). The spec section 3 example uses `price` (dollars). Find out which the real catalog uses:

```bash
grep -E "(price|price_cents):" "Product Catalog/CATALOG_INDEX.yaml" | head -5
```

**If it uses `price_cents`:** ✅ no shim needed. Skip to Step 2.2.

**If it uses `price`:** the SP2 catalog loader expects `price_cents`. Two options:
- Option A (preferred): edit `Product Catalog/CATALOG_INDEX.yaml` to rename `price` → `price_cents` and convert dollar values to integer cents (e.g., `price: 197` → `price_cents: 19700`). Update SP1's catalog generator to emit cents going forward.
- Option B: add a conversion shim in `stripe-delivery/api/catalog.py` that accepts either field name and normalizes. If you go this route, update `test_catalog.py` to cover both.

Document which option you picked in the parking lot.

### Step 2.2: Audit the delivery_source paths

The mock catalog points at `stripe-delivery/tests/fixtures/dummy_deliverable/`. The real catalog should point at `Product Catalog/products/<tier>/_customer_deliverables/`. Verify each `delivery_source` value:

```bash
grep "delivery_source:" "Product Catalog/CATALOG_INDEX.yaml"
```

For each `delivery_source`, confirm the path exists relative to the repo root:

```bash
# Example
ls "Product Catalog/products/01_parser_trial/_customer_deliverables/"
```

If any path is wrong or missing, fix in SP1's catalog generator before proceeding.

### Step 2.3: Audit the consulting tiers' scheduling_link values

```bash
grep "scheduling_link:" "Product Catalog/CATALOG_INDEX.yaml"
```

Each consulting/workflow tier needs a non-empty scheduling link. Per the locked Pre-session decision (Cal.com), these should be:

- Foundation Package → `https://cal.com/kylebanfield/foundation` (or whatever Kyle set up)
- Implementation, Modernization, Single Workflow, Multi Workflow, Practice Area Pack → each tier needs its own Cal.com URL OR a shared one

If any are blank, fix in SP1's catalog generator before proceeding.

### Step 2.4: Lock the prices

The PRE locked pricing decision in DECISIONS_PARKING_LOT.md sets these for consulting/workflow tiers:

- Foundation Package: $5,995 (`price_cents: 599500`)
- Implementation Package: $12,995 (`price_cents: 1299500`)
- Modernization Package: $29,995 (`price_cents: 2999500`)
- Single Workflow: $5,000 (`price_cents: 500000`)
- Multi Workflow: $10,000 (`price_cents: 1000000`)
- Practice Area Pack: $19,995 (`price_cents: 1999500`)
- Parser Trial: $197 (`price_cents: 19700`)
- Full Litigation Suite: $2,997 (`price_cents: 299700`)

Confirm the real `CATALOG_INDEX.yaml` matches these exact values. If anything is different, **stop and discuss with Kyle before proceeding** — Stripe Prices are immutable so wrong prices mean re-provisioning.

---

## Phase 3 — Catalog wiring (20 min)

### Step 3.1: Set CATALOG_INDEX_PATH in Render staging

Tell SP2 to load the real catalog instead of the mock.

1. Render → `sidebarcode-api` → **Environment** tab
2. Add a new variable:
   - Key: `CATALOG_INDEX_PATH`
   - Value: `Product Catalog/CATALOG_INDEX.yaml` (the path is relative to the repo root, which is the `Side Bar Code/` directory)
3. Save Changes → Render auto-redeploys (~2 min)

### Step 3.2: Verify the new catalog loads

After redeploy:

```bash
# This should now use the real catalog. Test with one of the real tier_ids.
curl -X POST https://sidebarcode-api.onrender.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier_id":"product_parser_trial","tos_accepted":true,"tech_overview_accepted":true}'
```

Expected: returns a `checkout_url` for the real Parser Trial. If you get 404 "unknown tier_id," the catalog isn't loading from the new path — check Render logs for `FileNotFoundError` and verify the env var value matches the actual file location.

### Step 3.3: Test that mock tiers no longer work

```bash
curl -X POST https://sidebarcode-api.onrender.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier_id":"mock_parser_trial","tos_accepted":true,"tech_overview_accepted":true}'
```

Expected: 404 (mock tiers are gone — only real tiers in the new catalog). This confirms the swap.

---

## Phase 4 — Stripe test-mode provisioning (30 min)

### Step 4.1: Sync the real catalog to Stripe TEST mode

This creates the 8 real products in Stripe test mode. Test mode is still safe — no real charges.

```bash
cd "C:/CLAUDE/projects/Sidebar Code/Side Bar Code/stripe-delivery"
python scripts/sync_stripe_catalog.py --dry-run
```

Expected output: 8 lines, each `would_create` (because the real tier_ids don't exist in your test account yet).

If any tier shows `would_no_op` and you didn't expect that, **investigate** — it means a stale product from a previous experiment matches one of the real tier_ids. Either rename the real tier or delete the stale product manually in the Stripe dashboard before continuing.

### Step 4.2: Apply the real sync

```bash
python scripts/sync_stripe_catalog.py
```

Expected: 8 lines, each `created` with new `prod_xxx` and `price_xxx` IDs. The script writes `CATALOG_INDEX.stripe.yaml` in the catalog folder with the resolved IDs.

### Step 4.3: Verify in the Stripe dashboard

Open https://dashboard.stripe.com/test/products. You should see 8 new products (plus the 3 mock ones from before — leave the mocks for now, you'll clean them up in Phase 9).

Click into one (e.g., the real Parser Trial) and confirm:
- Name matches the catalog's `stripe_product_name`
- Price matches `price_cents` (e.g., $197.00 for Parser Trial)
- Tax code matches `tax_code`
- Metadata has `tier_id`, `category`, `delivery_type` set

### Step 4.4: Idempotency check

Run the sync a third time:

```bash
python scripts/sync_stripe_catalog.py
```

All 8 should report `unchanged`. If any report `created` or `updated`, the script has a bug — stop and investigate.

---

## Phase 5 — Email copy refinement (1-2 hours, Kyle's evening work)

This phase is mostly Kyle, not the agent. The 4 Postmark templates currently have functional placeholder copy. Replace each with finalized copy that matches Kyle's Sales Playbook voice.

### Step 5.1: Edit each template in the Postmark dashboard

Go to https://account.postmarkapp.com → your server → Templates. Edit each:

| Template alias | Notes |
|---|---|
| `sp2-product-download` | Buyer-facing. Should match the warm-but-professional tone in the Sales Playbook. Keep all merge variables intact ({{buyer_name}}, {{tier_name}}, {{download_url}}, {{expires_at}}, {{purchase_id}}, {{purchased_at}}, {{support_email}}). |
| `sp2-consulting-receipt` | Buyer-facing. Mirror the consulting-tier brand voice. Keep merge vars: {{buyer_name}}, {{tier_name}}, {{amount_formatted}}, {{purchase_id}}, {{purchased_at}}, {{scheduling_link}}, {{kyle_email}}. |
| `sp2-kyle-new-consulting-purchase` | Internal-only (to Kyle). Current copy is fine — refine if you want richer formatting. |
| `sp2-delivery-failure-alert` | Internal-only. Current copy is fine. |

**Do NOT change the aliases.** Code references them by alias and renaming would break the integration.

### Step 5.2: Send a test from Postmark for each template

In Postmark's template editor, click "Preview" or "Send Test" to send a test email to yourself with sample merge data. Read each one in your inbox and revise until you're happy.

### Step 5.3: Re-verify the catalog tier names render correctly

The product_download and consulting_receipt templates use `{{tier_name}}` which comes from the catalog's `stripe_product_name` field. Make sure the tier names in your real catalog read well in the email subject lines and body. (e.g., "Sidebar Code Parser Trial" reads naturally; "PARSER_TRIAL_V1" would look wrong.)

---

## Phase 6 — Aemon legal review gate (timeline depends on Aemon)

This is a **hard gate**. Do not proceed to Phase 7 until Aemon explicitly approves all of the following:

### Step 6.1: ToS review

Aemon reviews `terms.html` for:
- Refund policy language (case-by-case within 30 days, per locked Pre-session decision)
- License grant language (single-firm internal use, no resale/redistribution)
- Limitation of liability appropriate for legal-tech product
- Dispute resolution clause
- Choice of law (Arizona)
- Bar ethics compliance for legal-tech sale

### Step 6.2: Technology Overview review

Aemon reviews `Product Catalog/shared/technology_overview.md` for:
- Accurate description of what the product does and doesn't do
- Prerequisite disclosures (Claude Code + Anthropic subscription/API key billed separately)
- Limitations and required human oversight
- No language implying legal advice
- Bar ethics compliance for AI-assisted legal work

### Step 6.3: Email template review

Aemon reviews each of the 4 Postmark template bodies (after Kyle's Phase 5 edits) for:
- No language implying legal advice
- Clear separation of "this is a tool" vs "this is legal counsel"
- Compliance with attorney advertising rules in Arizona

### Step 6.4: Pre-checkout modal copy

When the success/cancel pages and pre-checkout modal exist (Phase 7), Aemon reviews their copy too.

### Step 6.5: Aemon sign-off recorded

Aemon writes a one-page review memo and saves to `_ops/AEMON_PRE_LAUNCH_REVIEW.md`. This is your audit trail — keep it permanently.

**No Phase 7 work until this memo exists.**

---

## Phase 7 — Pre-launch test purchases (1 hour)

Now you complete a real test purchase against staging for every tier. Test mode = safe, no real money.

### Step 7.1: Run a full purchase for each of the 8 tiers

For each tier_id in the real catalog:

```bash
TIER_ID="product_parser_trial"  # change per tier

curl -X POST https://sidebarcode-api.onrender.com/api/checkout \
  -H "Content-Type: application/json" \
  -d "{\"tier_id\":\"$TIER_ID\",\"tos_accepted\":true,\"tech_overview_accepted\":true}"
```

Open the returned `checkout_url` in a browser, complete the purchase with `4242 4242 4242 4242`, and verify:

| For zip_download tiers (Parser Trial, Full Suite) | For notify_kyle tiers (Foundation, Implementation, Modernization, 3 workflow tiers) |
|---|---|
| Email arrives in your inbox within 60 seconds | TWO emails arrive: receipt to buyer + alert to Kyle |
| Download link works | Receipt email includes correct scheduling link |
| Zip contains the actual real `_customer_deliverables/` content | Kyle alert includes buyer name/email/phone |
| Status shows `delivered` in admin dashboard | Status shows `awaiting_delivery`, lead row exists |

8 tiers = 8 test purchases. This is tedious but essential — every tier exercises a slightly different code path.

### Step 7.2: Run a test refund

For one zip_download purchase from Step 7.1:

1. Stripe dashboard → click the test charge → Refund
2. Wait 60 seconds
3. Verify in the admin dashboard that status is now `refunded`
4. Verify the original download link returns 404
5. Verify Kyle received the refund alert email

### Step 7.3: Run the daily digest cron once

Render → `sidebarcode-daily-digest-p52f` → Trigger Run

Verify:
- Cron run succeeds (HTTP 200)
- Email arrives in Kyle's inbox showing the 8 test purchases plus the 1 refund

### Step 7.4: Verify Aemon's review memo is filed

If `_ops/AEMON_PRE_LAUNCH_REVIEW.md` doesn't exist, **STOP** and do not proceed to live mode flip.

---

## Phase 8 — Live mode flip (45 min) — KYLE ONLY, NO AGENT

This is the only step where you absolutely cannot let the agent run commands. Live mode = real money. Mistakes are expensive.

### Step 8.1: Generate live-mode Stripe API keys

1. https://dashboard.stripe.com/apikeys (note: NOT `/test/apikeys` — this is the live page)
2. **Reveal Live Secret Key** — copy `sk_live_...` value
3. Save to `~/.sidebarcode-secrets.env` under `STRIPE_SECRET_KEY_LIVE=` (the slot already exists, just paste)
4. Copy Publishable Key (`pk_live_...`) → save to `STRIPE_PUBLISHABLE_KEY_LIVE=`

### Step 8.2: Provision real products in live mode

```bash
cd "C:/CLAUDE/projects/Sidebar Code/Side Bar Code/stripe-delivery"
STRIPE_SECRET_KEY="$(grep STRIPE_SECRET_KEY_LIVE ~/.sidebarcode-secrets.env | cut -d= -f2)" \
  python scripts/sync_stripe_catalog.py --dry-run
```

The script will warn loudly: `WARNING: STRIPE_SECRET_KEY is not a test-mode key`. **This is correct** — you intentionally set it to the live key.

If the dry-run shows `would_create` for all 8 tiers (expected — live mode is empty), drop `--dry-run`:

```bash
STRIPE_SECRET_KEY="$(grep STRIPE_SECRET_KEY_LIVE ~/.sidebarcode-secrets.env | cut -d= -f2)" \
  python scripts/sync_stripe_catalog.py
```

8 real products with real `prod_live_xxx` and `price_live_xxx` IDs are now in your live Stripe account.

### Step 8.3: Register a NEW webhook endpoint in LIVE Stripe

Test mode and live mode webhooks are completely separate. You need to create a new endpoint in live mode.

1. https://dashboard.stripe.com/webhooks (note: NOT `/test/`)
2. **+ Add endpoint**
3. URL: `https://sidebarcode-api.onrender.com/api/webhook`
4. Events: `checkout.session.completed`, `charge.refunded`, `charge.dispute.created`, `charge.dispute.closed`
5. Add endpoint
6. Copy the new **live signing secret** (`whsec_live_xxx`) — different from the test secret

### Step 8.4: Update Render env vars to live mode

This is the moment of truth. Update three env vars on `sidebarcode-api`:

| Key | New value |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` (your live secret key) |
| `STRIPE_PUBLISHABLE_KEY` | `pk_live_...` (your live publishable key) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_live_...` (your live webhook signing secret) |
| `SIDEBARCODE_ENV` | `prod` (was `staging`) |
| `R2_BUCKET` | `sidebarcode-prod` (was `sidebarcode-staging`) |
| `SITE_BASE_URL` | `https://sidebarcode.com` (or whatever your production domain is) |

Save Changes. Render auto-redeploys. Wait for green Live indicator.

### Step 8.5: Verify with a real card purchase of Parser Trial ($197)

```bash
curl -X POST https://sidebarcode-api.onrender.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier_id":"product_parser_trial","tos_accepted":true,"tech_overview_accepted":true}'
```

Open the returned URL. The Stripe Checkout page now shows **live mode** (no orange test banner at the top).

**Pay with your real credit card.** Use your real billing address. This is real money — $197 will move from your card to your Stripe account.

After the charge succeeds:
- Email arrives in your inbox with download link
- Click link, verify the real Parser Trial deliverable downloads
- Confirm in https://dashboard.stripe.com/payments (live, no `/test/`) that the $197 charge appears

### Step 8.6: Refund yourself

```
Stripe dashboard → live payments → click your $197 charge → Refund
```

The refund triggers a real `charge.refunded` webhook which deletes the R2 object and marks the purchase row refunded. You'll receive a refund alert email from your own service.

The $197 returns to your card in 5-10 business days (Stripe's standard refund timeline).

### Step 8.7: Test purchase + refund cycle for the 7 remaining tiers

Run the same flow for each of the other 7 tiers. Each will charge your card briefly, then refund. You'll be out roughly $0 after all refunds clear (test fees aside).

This is the most expensive verification step in the playbook (~$80,000 in temporary charges + refunds for the consulting tiers), but it proves every tier works end-to-end with real cards. **Don't skip any tier.**

---

## Phase 9 — Cleanup (15 min)

### Step 9.1: Delete the mock test-mode products

Now that real products exist, the 3 mock products in Stripe test mode are clutter. Delete them via the Stripe dashboard:

1. https://dashboard.stripe.com/test/products
2. Find each `mock_*` product → click → **Archive** (then optionally **Delete**)

The mock catalog YAML stays in the repo as a test fixture — only Stripe-side cleanup needed.

### Step 9.2: Disable the mock catalog as a test fallback

Edit `stripe-delivery/api/catalog.py`'s `_default_catalog_path()` function to return `None` or raise an error if `CATALOG_INDEX_PATH` is unset. This prevents accidentally running the production service against the mock catalog if the env var is ever cleared.

Optional — only do this if you're paranoid. The current behavior is to fall back to the mock, which is safer for local dev.

### Step 9.3: Update DECISIONS_PARKING_LOT.md

Mark every `[PRE]`, `[S1]`-`[S8]` entry as `CONFIRMED` with the launch date. This is your audit trail.

---

## Phase 10 — Launch (1 hour)

### Step 10.1: DNS cutover (if not already done)

If your production domain (`sidebarcode.com`) wasn't already pointing at the Render service, do it now:

1. Render → `sidebarcode-api` → Settings → Custom Domains → Add `sidebarcode.com`
2. Render gives you a CNAME target
3. Add the CNAME in your DNS provider (GoDaddy)
4. Wait for verification (5-30 min)

### Step 10.2: Smoke test from a clean browser

Use an incognito window or a different device. Visit `https://sidebarcode.com` (or the buy button on your marketing site) and complete one more $197 purchase with a real card to confirm the cleanest possible buyer experience.

### Step 10.3: Announce

When the smoke test passes, you can announce the launch.

### Step 10.4: Monitor for 7 days

For the first week post-launch, check the admin dashboard (`/admin/sales`) every morning and read the daily digest carefully. Watch for:

- Any failed deliveries (should be zero in a healthy state)
- Any disputes (should be zero or extremely rare)
- Any Postmark bounces (some are inevitable, monitor the rate)
- Render service health (should be green continuously)

If anything looks wrong, consult `_ops/INCIDENT_RUNBOOK.md`.

### Step 10.5: Write `_ops/SP2_HANDOFF_NOTES.md`

When SP3 (Steward) is ready to start consuming the leads SP2 writes to SQLite, document the handoff: schema reference, env var inventory, runbook pointer, common queries. Save in `_ops/SP2_HANDOFF_NOTES.md`.

---

## Rollback procedure (if anything goes wrong in Phase 8-10)

If a real-mode purchase fails, a buyer reports a major issue, or anything else triggers an emergency rollback:

### Immediate rollback (60 seconds)

1. Render → `sidebarcode-api` → Environment → set `STRIPE_SECRET_KEY` back to the test-mode key
2. Save Changes → service redeploys with test mode active
3. New checkouts now go through Stripe test mode → no more real money moves
4. Stripe live webhook endpoint stays registered but won't fire (no live charges happening)

### After-rollback steps

1. Refund any already-completed live charges via the Stripe dashboard
2. Send a personal apology email to any affected buyers
3. Triage the failure mode — usually it's something this playbook missed
4. Fix, re-test in test mode, then re-attempt the live flip

**Rollback is cheap. Don't hesitate.** The cost of staying broken is much higher than the cost of admitting "we hit a snag, give us 24 hours."

---

## Estimated total time

- Phase 1: 15 min
- Phase 2: 30 min
- Phase 3: 20 min
- Phase 4: 30 min
- Phase 5: 1-2 hours (Kyle, evening)
- Phase 6: depends on Aemon (could be hours or days — don't rush this)
- Phase 7: 1 hour
- Phase 8: 45 min (KYLE ONLY)
- Phase 9: 15 min
- Phase 10: 1 hour + 7 days monitoring

**Total agent time:** ~2-3 hours
**Total Kyle time:** ~3-4 hours including review
**Calendar time:** 1-3 days depending on Aemon's review speed

---

*This playbook replaces the spec's brief "Phase 7 — Launch" section with concrete, sequenced steps. Update this file every time you discover something this playbook missed during a real swap-in.*
