# SP2 Decisions Parking Lot

**Purpose:** Questions the day-session agent hit that need Kyle's evening input. The agent uses the documented default and keeps working. Kyle reviews here in the evening and marks each item.

**Format per entry:**
- `[Session #]` `[Status: PENDING | CONFIRMED | CHANGE_TO]`
- **File:** path
- **Question:** ...
- **Agent default:** ...
- **Kyle response:** (filled in evening)
- **Logged:** YYYY-MM-DD

---

## Pending decisions

*(Day-session agents append here as they encounter questions. Kyle edits in the evening.)*

### Session 8 — Admin dashboard + crons + incident runbook

`[S8]` `[Status: PENDING]`
- **File:** stripe-delivery/api/admin.py + stripe-delivery/api/main.py
- **Question:** Admin dashboard route — playbook says `/admin/dashboard`, but Kyle wants room for a future portal that nests multiple tools.
- **Agent default:** Mounted at **`/admin/sales`** (not `/admin/dashboard`). Per-Kyle architectural decision: leaves `/admin/*` available for a future portal that proxies to multiple tools (Review Dashboard, Sales Admin, future BI). No code in any other tool needs to change today, but the route prefix is now portal-friendly.
- **Logged:** 2026-04-13

---

`[S8]` `[Status: PENDING]`
- **File:** stripe-delivery/api/admin.py — resend confirmation
- **Question:** Should the resend button have a confirmation modal?
- **Agent default:** Yes — uses inline JS `confirm()` on the form's `onsubmit`. Prevents accidental clicks. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S8]` `[Status: PENDING]`
- **File:** stripe-delivery/scripts/send_daily_digest.py + render.yaml
- **Question:** Daily digest time zone.
- **Agent default:** America/Phoenix (Kyle's local). Cron schedule is `0 15 * * *` UTC = 08:00 Phoenix year-round (Arizona does not observe DST). Cleanup crons run at 03:00 Phoenix = 10:00 UTC. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S8]` `[Status: PENDING]`
- **File:** stripe-delivery/_ops/INCIDENT_RUNBOOK.md
- **Question:** Should the incident runbook link to Stripe/Postmark/R2 dashboards by name?
- **Agent default:** Yes. Quick reference table at the bottom lists every dashboard URL Kyle might need at 9pm on Saturday. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S8]` `[Status: PENDING]`
- **File:** render.yaml — cron job env var inheritance
- **Question:** How do cron services get the same env vars as the web service?
- **Agent default:** `fromService` directive in render.yaml. Each cron job inherits specific env vars (POSTMARK_API_TOKEN, R2_*, SQLITE_PATH) from the `sidebarcode-api` web service rather than duplicating values. Kyle only updates secrets in one place.
- **Logged:** 2026-04-13

---

`[S8]` `[Status: PENDING]` — **Session 8 manual verification not yet performed.**
- After deploy, Kyle should: (1) load the admin dashboard at `https://sidebarcode-api.onrender.com/admin/sales` with basic auth, (2) confirm test purchases from Sessions 4-7 are visible, (3) trigger a manual run of `send_daily_digest.py` from the Render Cron service's "Trigger Run" button and confirm digest email arrives, (4) verify the three cron jobs appear as separate services in the Render dashboard with the schedules `0 15 * * *`, `0 10 * * *`, `30 10 * * *`. The Blueprint apply will create the new cron services on the next push — Kyle may need to re-apply the Blueprint to register them.
- **Logged:** 2026-04-13

---

### Session 7 — End-to-end delivery wiring + placeholder emails

`[S7]` `[Status: PENDING]`
- **File:** stripe-delivery/scripts/sync_postmark_templates.py + stripe-delivery/api/delivery.py
- **Question:** Reference Postmark templates by ID or by alias?
- **Agent default:** **Alias** (string), not numeric ID. Aliases survive template re-creations and let Kyle edit copy in the dashboard without code changes. Hardcoded aliases: `sp2-product-download`, `sp2-consulting-receipt`, `sp2-kyle-new-consulting-purchase`, `sp2-delivery-failure-alert`. The sync script idempotently creates/updates these by alias.
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]`
- **File:** stripe-delivery/scripts/sync_postmark_templates.py
- **Question:** Refund alert — dedicated template or plain text?
- **Agent default:** Plain text via `client.emails.send` (not `send_with_template`). The playbook lists 4 templates and refund alert is not among them. Refund alerts are internal-only (only Kyle sees them) so polished HTML is not needed. Reduces template count by 25%.
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py — build_and_deliver_zip error handling
- **Question:** delivery_failure_alert email — include full traceback or just error message?
- **Agent default:** **Full traceback**. Internal alert, not customer-facing. Saves Kyle a trip to Render logs to diagnose. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py — consulting_receipt template
- **Question:** Include purchase amount in consulting_receipt email?
- **Agent default:** Yes (`amount_formatted` merge var, formatted as `$X.XX USD`). Standard receipt practice. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py — FROM and Reply-To
- **Question:** From-address and Reply-To configuration?
- **Agent default:** Both default to `kyle@sidebarcode.com`. Overridable via env: `POSTMARK_FROM_ADDRESS` and `POSTMARK_REPLY_TO`. Kyle alert recipient is `KYLE_ALERT_EMAIL` (defaults to from address). Note: Render env already has `KYLE_ALERT_EMAIL` from Session 2 blueprint apply.
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]` — **Postmark template bodies are PLACEHOLDER ONLY.**
- All 4 templates created by `scripts/sync_postmark_templates.py` have working but rough copy. Kyle should edit each template in the Postmark dashboard during an evening session before launch. The aliases never change so editing is non-destructive to the code. Templates to refine:
  - `sp2-product-download` — buyer-facing, currently functional but plain
  - `sp2-consulting-receipt` — buyer-facing, needs Sales Playbook voice pass
  - `sp2-kyle-new-consulting-purchase` — internal, fine as-is
  - `sp2-delivery-failure-alert` — internal, fine as-is
- **Logged:** 2026-04-13

---

`[S7]` `[Status: PENDING]` — **Manual end-to-end email verification not yet performed.**
- Kyle must (1) run `python scripts/sync_postmark_templates.py` to create the 4 templates in his Postmark account, (2) complete a real test purchase of `mock_parser_trial` and confirm the download email arrives, (3) click the download link and confirm the dummy zip downloads, (4) complete a test purchase of `mock_consulting_foundation` and confirm both emails arrive (Kyle alert + buyer receipt). See post-commit instructions for exact steps.
- **Logged:** 2026-04-13

---

### Session 6 — Purchases, leads, refund handler

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/db.py — schema
- **Question:** Spec Section 9 only defines `leads` and `lead_events` schemas; the playbook also references `purchases`, `delivery_failures`, `tos_versions`, `tech_overview_versions`. What columns?
- **Agent default:** Designed `purchases` based on Section 5 of the spec (paragraph "Insert purchase row in SQLite: ..."). Columns: purchase_id, tier_id, category, delivery_type, stripe_session_id (UNIQUE), stripe_payment_intent_id, stripe_charge_id, buyer_email/name/phone, amount_cents, currency, status, zip_object_key, download_url_expires_at, download_attempts, tos_version_hash, tech_overview_version_hash, buyer_ip, created_at, updated_at. `delivery_failures` is FK to purchases with error_msg + traceback. `tos_versions` and `tech_overview_versions` are minimal: version_hash + first_seen_at. Full content reconstructable from git history.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/crm.py — insert_purchase idempotency
- **Question:** What's the idempotency key for inserts? Stripe may deliver checkout.session.completed more than once (network retries before mark_processed runs).
- **Agent default:** `stripe_session_id` is UNIQUE in the schema and `insert_purchase` short-circuits if a row with that session_id already exists. Returns the existing Purchase object. Same for `insert_lead` keyed on (source='stripe_purchase', stripe_charge_id).
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/crm.py — Lead.status default
- **Question:** Default lead status for stripe-sourced leads — `new` or `qualified`?
- **Agent default:** `qualified` (they paid, they're serious). Matches playbook default. Web-inquiry leads (Session 4 of SP3) will use `new`.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/crm.py — minimal lead capture
- **Question:** Should consulting lead rows include anything from Stripe metadata beyond email/name/phone?
- **Agent default:** No, minimal capture. Steward enriches later in SP3 by reading from the `notes` JSON column which we leave NULL on initial insert. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/webhook.py — refund lookup chain
- **Question:** charge.refunded events arrive with charge.id and charge.payment_intent. checkout.session.completed only stores payment_intent at creation time (charge_id may not exist yet). How to link?
- **Agent default:** Multi-step lookup: try `get_purchase_by_charge_id(charge_id)` first; if None, fall back to `get_purchase_by_payment_intent(charge.payment_intent)`. On match via payment_intent, backfill the charge_id on the purchase row. Robust against Stripe API timing variance.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/api/webhook.py — refund for unknown charge
- **Question:** What if charge.refunded fires but no purchase row matches?
- **Agent default:** Log warning, return 200 (so Stripe stops retrying). This happens when refunds come in for charges that pre-date the SP2 service (e.g. test mode cleanup) and is not an error.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]`
- **File:** stripe-delivery/scripts/backup_sqlite.py
- **Question:** Backup destination structure inside R2.
- **Agent default:** Object key prefix `sqlite-backups/sidebarcode-{ISO_TIMESTAMP}.db`. Retention: 30 days, pruned at end of each backup run by listing the prefix and deleting objects with `LastModified` older than cutoff. Uses `sqlite3.Connection.backup()` for consistent snapshots even if the service is mid-write.
- **Logged:** 2026-04-13

---

`[S6]` `[Status: PENDING]` — **Manual end-to-end purchase verification not yet performed.**
- The webhook orchestration is wired and unit-tested but Kyle should confirm that a real test purchase against staging actually writes a purchases row to the live SQLite at `/var/data/sidebarcode.db` on Render, and that a test refund updates it. See post-commit instructions for the SQL queries to run via Render's Shell tab.
- **Logged:** 2026-04-13

---

### Session 5 — Webhook handler + signature verification + idempotency

`[S5]` `[Status: PENDING]`
- **File:** stripe-delivery/api/db.py
- **Question:** SQLite WAL mode? Foreign keys?
- **Agent default:** Both enabled at schema initialization. `PRAGMA journal_mode = WAL` for better concurrent reads, `PRAGMA foreign_keys = ON` for referential integrity. Initialized once per process per DB path. Matches Session 6 parked default.
- **Logged:** 2026-04-13

---

`[S5]` `[Status: PENDING]`
- **File:** stripe-delivery/api/webhook.py
- **Question:** Mark events as processed before or after handler runs?
- **Agent default:** **After**. Only successful handler runs are marked processed. If handler raises, event is NOT marked, returning 500, and Stripe will retry. This guarantees at-least-once delivery semantics. Idempotency is preserved because a successful retry will short-circuit if a duplicate id arrives later.
- **Logged:** 2026-04-13

---

`[S5]` `[Status: PENDING]`
- **File:** stripe-delivery/api/webhook.py
- **Question:** Behavior on unhandled event types (e.g., invoice.paid).
- **Agent default:** Mark as processed and return 200 with `status: ignored`. Prevents Stripe from retrying events we don't care about. We can add new handlers later by extending `_HANDLERS` dict with no other code change.
- **Logged:** 2026-04-13

---

`[S5]` `[Status: PENDING]`
- **File:** stripe-delivery/api/webhook.py — handle_dispute_opened
- **Question:** What does charge.dispute.created do beyond alerting?
- **Agent default:** Currently logs and writes debug row only. Session 6/7 will extend to: set purchase status to `disputed`, send Kyle alert, leave download link active (no auto-revoke). Matches playbook default. Flagged for Session 6.
- **Logged:** 2026-04-13

---

`[S5]` `[Status: PENDING]`
- **File:** stripe-delivery/api/db.py — webhook_debug_log retention
- **Question:** How long to retain webhook_debug_log rows?
- **Agent default:** 30 days. Session 8 will add a housekeeping cron `cleanup_webhook_debug_log.py` that deletes rows older than 30 days. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S5]` `[Status: PENDING]` — **Manual webhook verification not yet performed.**
- The webhook endpoint is deployed but cannot be tested live until Kyle (a) registers `https://sidebarcode-api.onrender.com/api/webhook` in the Stripe test dashboard subscribed to `checkout.session.completed`, `charge.refunded`, `charge.dispute.created`, `charge.dispute.closed`, (b) copies the signing secret (`whsec_...`) into Render env as `STRIPE_WEBHOOK_SECRET`, (c) triggers a test event from the Stripe CLI or the dashboard's "Send test webhook" button, and (d) confirms staging logs show signature verified. See post-commit instructions for the exact steps.
- **Logged:** 2026-04-13

---

### Session 4 — Mock catalog + Stripe Checkout

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/mock_catalog_index.yaml, stripe-delivery/api/catalog.py
- **Question:** Spec uses `price` field (dollars). Stripe API needs cents. How to represent price in catalog YAML?
- **Agent default:** Renamed to `price_cents` in mock_catalog_index.yaml (integer cents). Removes ambiguity. When SP1 ships the real CATALOG_INDEX.yaml, it should use the same `price_cents` convention or the catalog loader needs a conversion shim. Flagging for SP1 swap-in session.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/api/checkout.py
- **Question:** Should Stripe Checkout collect phone number?
- **Agent default:** Yes (`phone_number_collection: enabled=True`). Helpful for consulting tiers where Kyle may need to contact buyer outside email. Buyer can leave blank if they want. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/api/checkout.py
- **Question:** Where to collect buyer IP?
- **Agent default:** Read from `X-Forwarded-For` header (Render proxy injects this), fall back to `request.client.host`. Stored in Stripe Checkout Session metadata as `buyer_ip`. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/api/checkout.py
- **Question:** ToS / Tech Overview version hashing — what file to hash?
- **Agent default:** SHA-256 (truncated to 16 hex chars) of `terms.html` and `Product Catalog/shared/technology_overview.md` content at session creation time. If file missing, hash is "unknown" (and will be flagged in Session 7 Aemon review). The Tech Overview file may not exist yet — Aemon writes it during SP1.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/api/checkout.py
- **Question:** Stripe Checkout success_url and cancel_url — where do they point?
- **Agent default:** Computed at request time as `{SITE_BASE_URL}/success?session_id={CHECKOUT_SESSION_ID}` and `{SITE_BASE_URL}/cancel`. SITE_BASE_URL env var if set, else falls back to the request's own scheme+host. The /success and /cancel HTML pages are Phase 4 of the spec and not built yet — buyers redirected after a test purchase will get 404s, but the Stripe dashboard will show the completed transaction. This is acceptable for Session 4 verification.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]`
- **File:** stripe-delivery/api/checkout.py
- **Question:** Stripe automatic_tax — enable now or later?
- **Agent default:** Enabled (`automatic_tax: enabled=True`). Kyle already activated Stripe Tax during Session 1 external account setup. This makes sales tax appear in test purchases, which is the more realistic test surface.
- **Logged:** 2026-04-13

---

`[S4]` `[Status: PENDING]` — **Manual Stripe verification not yet performed.**
- The `sync_stripe_catalog.py` script and the live POST /api/checkout test require STRIPE_SECRET_KEY which the agent does not have in its session. Kyle must run these locally before declaring Session 4 fully complete. Step 1: `cd stripe-delivery && python scripts/sync_stripe_catalog.py --dry-run` then drop `--dry-run` to actually create products. Step 2: hit deployed `/api/checkout` with curl/Postman and complete a test purchase using card 4242 4242 4242 4242. See post-commit instructions for the exact commands.
- **Logged:** 2026-04-13

---

### Session 3 — Zip builder + R2 upload + signed URLs

`[S3]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py
- **Question:** ZIP contents — include the top-level folder name or flatten?
- **Agent default:** Include (`dummy_deliverable/file.md` not `file.md`). Constant: `ZIP_INCLUDE_TOP_LEVEL_FOLDER = True`. Matches playbook default. Easier to identify what was downloaded when buyers open the zip in Finder/Explorer.
- **Logged:** 2026-04-13

---

`[S3]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py
- **Question:** ZIP compression level (0-9).
- **Agent default:** 6 (Python default — balanced speed vs ratio). Constant: `ZIP_COMPRESSION_LEVEL = 6`. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S3]` `[Status: PENDING]`
- **File:** stripe-delivery/api/delivery.py
- **Question:** Max ZIP size warning threshold.
- **Agent default:** 500 MB. Constant: `ZIP_SIZE_WARNING_BYTES = 500 * 1024 * 1024`. Logs a `logger.warning` if exceeded; does not block delivery. Matches playbook default.
- **Logged:** 2026-04-13

---

`[S3]` `[Status: PENDING]`
- **File:** stripe-delivery/tests/test_delivery.py
- **Question:** R2 integration tests — how to gate so CI doesn't fail without secrets?
- **Agent default:** `pytest.mark.skipif` on `R2_ACCOUNT_ID/R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY` env presence. Tests skip in CI (no secrets pasted) and run locally when Kyle exports credentials or sources `~/.sidebarcode-secrets.env`. Manual verification script `scripts/manual_zip_test.py` is the human-facing way to validate the live R2 roundtrip.
- **Logged:** 2026-04-13

---

`[S3]` `[Status: PENDING]` — **Manual R2 verification not yet performed.**
- The `test_upload_to_r2_roundtrip_against_dev_bucket` and `test_signed_url_returns_404_after_object_deleted` tests are gated on R2 env vars. They were not run by the agent because the agent does not have R2 credentials in its session. Kyle must run them locally before declaring Session 3 fully complete: `set -a && source ~/.sidebarcode-secrets.env && set +a && cd stripe-delivery && python -m pytest tests/test_delivery.py -v -k integration`. Or run `python scripts/manual_zip_test.py` for the human-friendly version that prints a clickable signed URL.
- **Logged:** 2026-04-13

---

### Session 2 — FastAPI skeleton + CI

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py
- **Question:** Basic auth credentials for /admin/dashboard. Playbook parks this.
- **Agent default:** Read from `ADMIN_USER` and `ADMIN_PASSWORD` env vars. Fails closed with 503 "admin dashboard not configured" if either is unset. Constant-time comparison via `secrets.compare_digest`. Matches parked default in the playbook.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py, .github/workflows/ci.yml, stripe-delivery/render.yaml
- **Question:** Python runtime version. Playbook parks 3.12.
- **Agent default:** Python 3.12 everywhere (CI, Render, local dev target). Matches Render default. Production code is written against 3.12 stdlib; agent's local pytest runs on 3.14 which is a superset — tests pass on both.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py /health endpoint
- **Question:** How to resolve the git SHA at runtime so /health can return it?
- **Agent default:** Check `GIT_COMMIT` env var first (Render will be configured to inject this), fall back to `RENDER_GIT_COMMIT`, fall back to `git rev-parse --short HEAD` for local dev, return "unknown" if all three fail. Render may need a `GIT_COMMIT=$RENDER_GIT_COMMIT` env var mapping added in the service settings — flagging for Session 2 deploy step.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py /health endpoint
- **Question:** Source of the `env` field in /health response (staging vs prod vs development).
- **Agent default:** Read from `SIDEBARCODE_ENV` env var. Default value "development" when unset. Render staging service should set `SIDEBARCODE_ENV=staging`; prod sets `=prod`. Flagging so Kyle adds this env var during the Render blueprint apply step.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/.github/workflows/ci.yml
- **Question:** gitleaks install method (playbook listed it in requirements.txt but it's a Go binary, not pip).
- **Agent default:** Installed via `gitleaks/gitleaks-action@v2` GitHub Action in CI. No local pip install. Resolves the Session 1 parking lot entry about this.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]` — **Deploy phase NOT YET RUN.**
- Session 2 was split into (a) autonomous coding phase and (b) Kyle-gated deploy phase per Option A in-session. Coding phase is complete and committed. Deploy phase requires Kyle to: (1) run Render Blueprint apply on `stripe-delivery/render.yaml`, (2) paste 6 env vars into the new service (STRIPE_SECRET_KEY, POSTMARK_API_TOKEN, R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, plus ADMIN_USER/ADMIN_PASSWORD/SIDEBARCODE_ENV/GIT_COMMIT), (3) optionally create staging.sidebarcode.com CNAME or accept onrender.com subdomain, (4) smoke test /health returns 200. Exit criteria (staging /health green, CI green) cannot be declared met until these steps complete.
- **Logged:** 2026-04-13

---

### Session 1 — repo scaffolding

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml
- **Question:** Single Render service for checkout + webhook, or split into two services?
- **Agent default:** Single service (`sidebarcode-api`). Simpler to deploy, one webhook endpoint to register, less secret duplication. Splitting is a later optimization if webhook volume starves checkout latency.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml, stripe-delivery/README.md
- **Question:** Confirm domain `sidebarcode.com` is in Kyle's control for DNS SPF/DKIM (needed for Postmark sender verification in Session 1 external tasks).
- **Agent default:** Assume yes. Session 7 emails fail closed if Postmark domain is not verified by then.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/requirements.txt
- **Question:** Playbook lists `gitleaks (dev)` as a requirements.txt entry, but gitleaks is a Go binary, not a pip package. How to install?
- **Agent default:** Added a comment in requirements.txt noting the discrepancy. Plan: install via `zricethezav/gitleaks-action` in the GitHub Actions workflow built in Session 2. No local pip install. If Kyle wants a local pre-commit hook, pre-commit framework can pull the binary.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml
- **Question:** Render Python runtime version pin. Session 2 playbook parks Python 3.12 as the default; Session 1 render.yaml needs a concrete version to deploy.
- **Agent default:** `PYTHON_VERSION=3.12` set in render.yaml envVars (matches Session 2 parked default). Overridable in Render UI.
- **Logged:** 2026-04-13

---

### Session 1 — exit criteria that could not be completed

`[S1]` `[Status: PENDING]` — **External accounts not created in session.**
- Kyle owns creating Stripe, Cloudflare R2, Postmark, and Render accounts per the playbook "External account tasks" list. Agent scope explicitly excludes API calls to these services in Session 1. The "Kyle has created external accounts (checked off manually)" exit criterion is pending Kyle's evening work before Session 2 can deploy to staging.
- **Logged:** 2026-04-13

---

### Pre-session locks (Spec Appendix B — answer BEFORE starting Session 1)

These are the open questions from the spec that, if left unanswered, force the agent into defaults that are hard to reverse mid-build. Lock them in an evening session before Session 1 starts.

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q1
- **Question:** Final pricing for all 6 consulting/workflow tiers (Foundation, Implementation, Modernization, Single Workflow, Multi Workflow, Practice Area).
- **Agent default:** Placeholder amounts in mock catalog only. Day sessions do NOT touch live prices. Kyle must set real prices before the post-SP1 swap-in session.
- **Why it matters:** Stripe Prices are immutable. Changing a price after provisioning means archiving and recreating. Cheap to fix, but annoying if done repeatedly.
- **Kyle response (LOCKED 2026-04-13):**
  Single fixed prices per tier, no published ranges. Verified against canonical Sales Playbook PRICING_LOGIC.md and TIER_BOUNDARIES.md. Drop ranges everywhere; one number per tier.
  - Foundation Package: **$5,995** (Playbook range $5,000-$7,500, middle anchor)
  - Implementation Package: **$12,995** (Playbook range $10,000-$15,000, middle anchor)
  - Modernization Package: **$29,995** (Playbook range $25,000-$40,000, middle anchor)
  - Single Workflow: **$5,000** (already flat in Playbook)
  - Multi Workflow: **$10,000** (already flat in Playbook)
  - Practice Area Pack: **$19,995** (Playbook range $15,000-$25,000, middle anchor)
  - Parser Trial: $197 (already locked in Playbook)
  - Full Litigation Suite: $2,997 (already locked in Playbook)

  **Consequence — file updates queued for post-SP1 swap-in session (NOT day sessions). FULL AUDIT 2026-04-13.**

  ### Range-language updates (replace ranges with single locked prices)
  - **index.html:** replace 4 range strings — Foundation `$5,000 – $7,500` → `$5,995`; Implementation `$10,000 – $15,000` → `$12,995`; Modernization `$25,000 – $40,000` → `$29,995`; Practice Area Pack `$15,000 – $25,000` → `$19,995`
  - **Product Catalog/CATALOG_INDEX.yaml:** for each consulting/workflow tier, set `price_min == price_max == locked_price` and rewrite `price_display`:
    - consulting_foundation: price_min=5995, price_max=5995, price_display="$5,995"
    - consulting_implementation: price_min=12995, price_max=12995, price_display="$12,995"
    - consulting_modernization: price_min=29995, price_max=29995, price_display="$29,995"
    - custom_workflows_single: already flat, no change ($5,000)
    - custom_workflows_multi: already flat, no change ($10,000)
    - custom_workflows_practice_area: price_min=19995, price_max=19995, price_display="$19,995"
    - This file drives the Stripe sync script — it is the canonical source for live provisioning.
  - **Product Catalog/_playbook/PRICING_LOGIC.md:** update 4 tier headers (Tier 3 Foundation, Tier 4 Implementation, Tier 5 Modernization, Tier 8 Practice-Area)
  - **Product Catalog/_playbook/TIER_BOUNDARIES.md:** update 4 tier headers + 6 quote blocks containing range language
  - **Product Catalog/_playbook/SALES_PLAYBOOK.md:** update ~25 range references across tier headers, quote blocks, deep dives, and target buyer sections
  - **Product Catalog/_playbook/OBJECTION_HANDLING.md:** update any range-language quotes (mostly clean — only the math fix below applies)
  - INQUIRY_RESPONSE_TEMPLATES.md and POSITIONING_CORE.md verified clean of explicit price references — no changes needed

  ### Internal math fixes (Category B — old midpoint math baked into example sentences)
  These produce wrong numbers with the new locked prices and must be corrected during swap-in:

  - **B1.** OBJECTION_HANDLING.md:134 AND SALES_PLAYBOOK.md:769 — `Full Suite plus Implementation at $15,500, year one` → change `$15,500` to `$15,992` ($2,997 + $12,995). Round to `$16,000` if cleaner narrative is preferred.
  - **B2.** PRICING_LOGIC.md:49 AND SALES_PLAYBOOK.md:505 — `One engagement per month at $12,500 = $150,000/year` → change to `$12,995 = $155,940/year`. Round to `~$13,000 = ~$156,000` if narrative cleanness matters.
  - **B3.** PRICING_LOGIC.md:111 AND SALES_PLAYBOOK.md:565 — `On a $12,500 Implementation engagement, that is $1,875 off` (15% early-adopter discount) → change to `$12,995 ... $1,949 off` (15% of $12,995 = $1,949.25, round to $1,949 or $1,950).
  - **B4.** SALES_PLAYBOOK.md:308 — `What is the extra $5,000 to $8,000 buying me over Foundation?` → change to `extra $7,000` ($12,995 − $5,995 = $7,000 exact).
  - **B5.** SALES_PLAYBOOK.md:118 — `Foundation price at $5,000 and immediately asks what the $10,000 package includes` → change to `Foundation price at $5,995 and immediately asks what the $12,995 package includes`.
  - **B5b.** SALES_PLAYBOOK.md:279 — `That is what the $5,000 buys` (referring to Foundation) → change to `That is what the $5,995 buys`.
  - **B5c.** SALES_PLAYBOOK.md:224-225, 244, 274 and similar — verify Foundation `$5,000` references and Implementation `$10,000` bare-number references are updated to `$5,995` and `$12,995` respectively. Sweep with grep before commit.

  ### Solo Launch Package — A3 decision (mark as future, do not ship at MVP)
  The Sales Playbook describes a 9th tier ("Solo Launch Package") at $4,500 / $1,500 with prior Full Suite that exists in narrative only — no CATALOG_INDEX.yaml entry, no Product Catalog folder, no website tier card, no Stripe product. **Decision 2026-04-13: A3 — mark as future, do not build at MVP.** Solo Launch is a real product idea that needs catalog scaffolding to ship; that work is post-MVP.

  **Required swap-in actions for Solo Launch:**
  - **PRICING_LOGIC.md** lines 83 onward: move the Solo Launch section from the active tier list into a clearly-labeled `## Future Offerings (Post-MVP)` section at the bottom. Add a one-line preface: "The following offerings are documented for strategic continuity but are NOT available for purchase at MVP launch. Steward and other agents must NOT quote prices or accept inquiries for these tiers until they are formally promoted into the active catalog."
  - **OBJECTION_HANDLING.md** line 172: rewrite the "I am about to start a solo practice" objection response. Remove the Solo Launch quote. Replace with a steering response that points solo practitioners toward Parser Trial or Full Suite as the entry, and notes that a dedicated solo-practitioner package is in development. Suggested rewrite: `"For new solos, the right entry is the Parser Trial at $197 or the Full Litigation Suite at $2,997 — both are firm-wide, one-time, and you own them forever. A dedicated Solo Launch Package with administrative templates and a launch session is in development for a future release. If you want a custom scoping conversation about your specific solo setup in the meantime, that is a paid hourly consulting engagement."`
  - **SALES_PLAYBOOK.md** lines 188, 441, 539, 1029: move all three Solo Launch sections into the same `Future Offerings (Post-MVP)` section. Update the Section 4 tier catalog header to read "8 Active Tiers" (not 8+1). Update the version 1.0 changelog at line 1029 to note "Solo Launch Package documented as Future Offering 2026-04-13 per SP2 swap-in audit; not shipping at MVP."
  - **SALES_PLAYBOOK.md** line 142: in the "Solo practitioner" target buyer flow, remove the Solo Launch reference and replace with the steering language above.
  - **Steward (SP3) impact:** Steward MUST be configured to recognize Solo Launch as out-of-catalog and never quote it. Document this in `_ops/AGENT_PROTOCOLS.md` during the SP3 build.
  - **No website changes** — Solo Launch was never on index.html.
  - **No CATALOG_INDEX.yaml changes** — Solo Launch was never indexed.

  ### Day session safety
  Day sessions through Session 8 continue to use mock_catalog_index.yaml — the mock prices do NOT need to match these locked prices because mock tiers exist only for Stripe test mode infrastructure validation. NONE of the file updates above happen during day sessions.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q2
- **Question:** Preferred scheduling tool for consulting handoff: Calendly, Cal.com, or other?
- **Agent default:** Cal.com with URL `https://cal.com/kylebanfield/foundation` (spec example). Template merge var `{{ scheduling_link }}` is tier-specific via catalog.
- **Why it matters:** Session 7 wires the scheduling link into the consulting receipt email. Changing tools later is a find/replace, but locking now avoids placeholder-in-production risk.
- **Kyle response (LOCKED 2026-04-13):**
  Cal.com confirmed. Dual-calendar setup:
  - **Primary calendar (bookings land here):** kyle@sidebarcode.com (Gmail)
  - **Conflict calendar (busy-block only, no event creation):** CHDB Outlook 365
  - URL pattern: `https://cal.com/kylebanfield/{tier-slug}`
  - One Cal.com event type per consulting/workflow tier with tier-appropriate duration, buffer time, and intake questions

  **Tier slug mapping (used in catalog `scheduling_link` field):**
  - foundation → `https://cal.com/kylebanfield/foundation`
  - implementation → `https://cal.com/kylebanfield/implementation`
  - modernization → `https://cal.com/kylebanfield/modernization`
  - workflow-single → `https://cal.com/kylebanfield/workflow-single`
  - workflow-multi → `https://cal.com/kylebanfield/workflow-multi`
  - workflow-practice-area → `https://cal.com/kylebanfield/workflow-practice-area`

  **Consequences queued:**
  - Kyle creates 6 Cal.com event types (one per consulting/workflow tier) BEFORE Session 7 manual verification — without these, the consulting_receipt email links 404
  - Cal.com dual-calendar conflict checking configured manually in Cal.com settings (Gmail + Outlook 365 both connected)
  - Mock catalog `scheduling_link` values use placeholder URLs; real catalog (post-SP1) uses the slugs above
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q3
- **Question:** Transactional email provider: Postmark or Resend?
- **Agent default:** Postmark (spec default; superior deliverability for transactional; template system is mature).
- **Why it matters:** Session 1 creates the account. Swapping providers after Session 7 means rewriting `send_email` calls and re-creating 4 templates. Not catastrophic but wasted time.
- **Kyle response (LOCKED 2026-04-13):** Postmark confirmed. Account already created. Domain verification status to be confirmed during Session 1 external account checklist. No code changes from spec default.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q4
- **Question:** Admin dashboard auth: basic auth (MVP) or simple login form?
- **Agent default:** Basic auth with `ADMIN_USER` / `ADMIN_PASSWORD` env vars, fail closed if unset.
- **Why it matters:** Session 8 builds the dashboard. Upgrading to a login form later is a 1-hour change. Basic auth is fine for single-user MVP.
- **Kyle response (LOCKED 2026-04-13):** Basic auth confirmed. Single-user (Kyle only) for foreseeable future. Non-guessable URL + env-var credentials sufficient. Matches spec default. No code changes.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q5
- **Question:** Parser Trial → Full Suite upsell coupon in the download email? If yes, amount and TTL?
- **Agent default:** NO coupon at MVP. Session 7 sends a clean download email without upsell. Add later if conversion data supports it.
- **Why it matters:** Adding a coupon means creating a Stripe Coupon + Promotion Code + wiring the merge var into the template. ~1 hour of work. Skipping at MVP is fine.
- **Kyle response (LOCKED 2026-04-13):** No coupon at MVP. Download email focuses on delivering the ZIP and quick-start instructions only. Revisit upsell strategy after organic upgrade data exists. Matches spec default.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q6
- **Question:** Refund policy: 7-day no-questions-asked, or case-by-case?
- **Agent default:** Case-by-case, documented in ToS as "refunds at Sidebar Code's discretion within 30 days of purchase." No automated refund button.
- **Why it matters:** Affects ToS copy and Aemon review. A "no-questions 7-day" policy is cleaner legally but means more refund losses on impulse buys.
- **Kyle response (LOCKED 2026-04-13):** Case-by-case refunds within 30 days at Kyle's sole discretion. No automated refund flow. Manual processing via Stripe dashboard. Aligns with litigator-pragmatism principle. Matches spec default.

  **Consequences queued (Aemon review block):**
  - terms.html refund clause must reflect "case-by-case within 30 days at Sidebar Code's sole discretion" language — Aemon to draft and approve BEFORE Session 7 templates ship
  - consulting_receipt and product_download Postmark templates must include refund policy reference (link to ToS), not embedded language
  - Refund handler in webhook (Session 6, already coded) is correct as-is — no code change. The decision affects ONLY the customer-facing legal language.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED — DEVIATION FROM SPEC DEFAULT]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q7
- **Question:** Failed-delivery retry strategy: auto-retry N times before alerting, or alert on first failure?
- **Agent default:** Alert Kyle on FIRST failure. Stripe's built-in webhook retry handles reprocessing. The alert is for visibility, not intervention required.
- **Why it matters:** Lower threshold = more noise but faster response. Session 7 wires this.
- **Kyle response (LOCKED 2026-04-13):** **Override spec default.** One automatic in-process retry before alerting Kyle. If first attempt fails, system retries once (with a short backoff). If retry also fails, send alert notification. Stripe's built-in webhook retry handles reprocessing of the entire event independently; the in-process retry-once governs Kyle-facing visibility alerts only. Goal: filter transient blips (R2 hiccup, Postmark momentary outage) without burying real failures.

  **Consequences queued — Session 7 code change required:**
  - `build_and_deliver_zip` in `stripe-delivery/api/delivery.py` must wrap each external call (R2 upload, Postmark send) in a retry-once-then-raise pattern. Suggested: simple `for attempt in range(2):` with 1-second backoff between attempts, raise on second failure.
  - `delivery_failures` row is written ONLY after the second failure (not the first).
  - `delivery_failure_alert` Postmark email is sent ONLY after the second failure.
  - On second failure, the function still re-raises so Stripe's webhook retry kicks in (don't suppress).
  - Add unit test: `test_deliver_zip_succeeds_on_retry_after_one_failure` (mock R2 to fail once then succeed).
  - Add unit test: `test_deliver_zip_alerts_only_on_second_failure` (mock R2 to fail twice).
  - Update INCIDENT_RUNBOOK.md "delivery failure" section to reflect the retry-once-then-alert behavior so Kyle understands when an alert means "transient" vs "broken pipe."
  - This change requires updating the SP2 spec Section 7 "Retry strategy" subsection AND the Session 7 task list before the day-coding agent runs Session 7.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE]` `[Status: CONFIRMED]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q8
- **Question:** Consulting tiers: pay in full at Checkout, or deposit + balance due?
- **Agent default:** Pay in full at Checkout. Simpler for MVP. Deposit model requires invoicing infrastructure.
- **Why it matters:** Changing to deposit model means adding Stripe Invoicing integration later. Real but not Session-1 blocking.
- **Kyle response (LOCKED 2026-04-13):** Pay in full at Checkout. No deposit/balance model. Consulting buyers are pre-qualified through Kyle's manual "notify Kyle" flow before seeing a checkout link — sticker shock is handled in conversation, not at payment. Matches spec default.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

---

## SP3 — Steward Operationalized

**Spec:** [2026-04-13-steward-operationalized-design.md](../specs/2026-04-13-steward-operationalized-design.md)
**Playbook:** [2026-04-13-sp3-day-session-playbook.md](2026-04-13-sp3-day-session-playbook.md)
**Started:** 2026-04-13 (Session 1)

### SP3 Pre-session locks (Spec Appendix B — locked BEFORE Session 1)

`[PRE Q1]` `[Status: CONFIRMED]` — **Auto-send tier policy**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 3
- **Question:** Should Steward auto-send any drafts, and if so, which?
- **Choice (LOCKED 2026-04-13):** Four tiers — `TIER_AUTO`, `TIER_REVIEW`, `TIER_ESCALATE`, `TIER_SILENT`. TIER_AUTO eligible for: FAQ replies, intake acknowledgments, unsubscribe confirms, onboarding Day 1 and Day 2, refund-confirmed receipts. Everything else routes to TIER_REVIEW or higher. Aemon reviews every TIER_AUTO send before it ships and can escalate to REVIEW. Aemon never de-escalates.
- **Why:** Strict zero-auto-send turned Kyle into the bottleneck for trivial work. Tiering puts the human in the loop where judgment matters and out of the loop where it doesn't. Aemon's review on a deterministic FAQ template is genuine quality control.
- **Reversibility:** Per-template tier overrides are exposed in the Steward admin panel. Kyle can flip a template from AUTO to REVIEW at any time without a code change.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q2]` `[Status: CONFIRMED]` — **Aemon review path**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 4
- **Question:** Does Aemon review before Kyle, after Kyle, or as a parallel gate?
- **Choice (LOCKED 2026-04-13):** **Serial: Aemon-then-Kyle.** Every customer-facing draft goes through Aemon first; Aemon's verdict and annotations are attached to the draft when it lands in Kyle's queue (or auto-sends for TIER_AUTO).
- **Why:** Single screen, single decision, full context. Avoids the "wait, I already approved this" loop that parallel review creates. Aemon catches legal/compliance exposure; Kyle catches voice and judgment. Both are necessary; ordering them serially gives Kyle the better experience.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q3]` `[Status: CONFIRMED — HARD RULE, NEVER REVISIT WITHOUT NEW SPEC]` — **Inbox scope**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 12
- **Question:** Does Steward monitor `kyle@sidebarcode.com` only, or also `kyle@chdblaw.com`?
- **Choice (LOCKED 2026-04-13):** **`kyle@sidebarcode.com` only. CHDB Law inbox is hard-prohibited at the code level.** Every code path that touches an email address (inbound webhook, outbound send, lead insertion) checks for `chdblaw.com` (case-insensitive) and rejects on hit. There is no override flag, no env var to relax the rule, no exceptions. Aemon flags any draft body referencing CHDB Law as HIGH severity.
- **Why:** Routing client-firm email through a Sidebar Code agent creates client confidentiality, attorney-client privilege, and corporate-veil exposure between CHDB Law, LLP and Banfield Consulting, LLC d/b/a Sidebar Code. Aemon will (correctly) refuse to clear any workflow that mixes the two. Kyle's standing instruction (2026-04-13): **NEVER use CHDB email for anything related to Sidebar Code.** Wire this in everywhere.
- **Code enforcement:** `_enforce_chdb_separation()` in `api/steward/enforcement.py`, called from inbound, outbox, intake, and crm.insert_lead. Unit tests assert it raises on every documented field.
- **Reversibility:** None. This is a hard architectural constraint. Revisiting requires a new spec, not a config change.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q4]` `[Status: CONFIRMED]` — **Worker model**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 2 design decisions
- **Question:** Should Steward run as a long-running worker (Render Background Worker) or as HTTP routes + cron-triggered HTTP endpoints inside the existing web service?
- **Choice (LOCKED 2026-04-13):** **No long-running worker.** Inbound is an HTTP route on the existing `sidebarcode-api` web service. Scheduled outbound runs as Render Cron Jobs hitting HTTP admin endpoints with `CRON_SECRET` Bearer auth. Both share the existing SQLite DB on the web service's persistent disk. Do NOT propose Background Worker, sidecar process, or async task loop architectures.
- **Why:** Render persistent disks are per-service. SP2 hard-learned this in Session 8 (cron jobs cannot directly access `/var/data/sidebarcode.db`). A Background Worker would have its own disk and could not read SQLite. A shared-disk SQLite invites concurrent-writer corruption. The web service already owns the DB and the schema; Steward extends it in-process.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q5]` `[Status: CONFIRMED]` — **Weekly business intelligence digest**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 15 (out of scope)
- **Question:** Should SP3 build a weekly BI digest with revenue, conversion, and pipeline metrics?
- **Choice (LOCKED 2026-04-13):** **Dropped from SP3 scope.** Replaced with a Steward-specific operational metrics panel inside the admin dashboard (drafts pending, draft-to-send latency, Aemon flag rate, classification confusion matrix, onboarding completion, nurture conversion).
- **Why:** Citadel is the analytics agent per CLAUDE.md. Building BI inside Steward forces a refactor when Citadel ships. Steward observability is "is my agent working correctly," not "is my business healthy." They are different concerns.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q6]` `[Status: CONFIRMED]` — **Classification approach**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 2 design decisions
- **Question:** Rule-based, pure LLM, or hybrid?
- **Choice (LOCKED 2026-04-13):** **Rule-based first, LLM fallback for ambiguous.** The rule-based classifier handles the deterministic 80% (spam, autoresponders, FAQ, scheduling, unsubscribe) with no API cost and full debuggability. LLM fallback (Anthropic API, default `claude-haiku-4-5-20251001`) handles the remaining 20% that need judgment. Gated by `CLASSIFIER_LLM_ENABLED` env var so Kyle can disable LLM entirely if needed.
- **Why:** Pure LLM is expensive at scale and harder to debug. Pure rule-based misses nuance. Hybrid keeps cost down while preserving judgment for the hard cases.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q7]` `[Status: PENDING]` — **Aemon transport**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 2 design decisions
- **Question:** Does Aemon's review() run as an in-process Python function call, or as an HTTP call to a sibling endpoint within the same web service?
- **Agent default (Session 1):** In-process Python function call. Faster, simpler, no IPC. The HTTP-wrapped variant can be added later if Aemon is ever extracted to a separate service.
- **Why it matters:** In-process is the cleaner default for SP3. HTTP wrapping is only worth it if Aemon needs to be a separate process for resource isolation or independent deployment. Neither is true at MVP.
- **Logged:** 2026-04-13
- **Confirmed:** PENDING — Kyle to confirm in evening review

---

`[PRE Q8]` `[Status: CONFIRMED]` — **Onboarding drip cadence**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 8
- **Question:** What cadence for the product-purchase onboarding drip?
- **Choice (LOCKED 2026-04-13):** **Day 1, 2, 7, 14, 30 from purchase.** Day 1 and Day 2 are TIER_AUTO; Day 7, 14, 30 are TIER_REVIEW. Adjustable per-tier in the catalog.
- **Why:** Standard SaaS onboarding curve, validated by years of industry data. Auto-send for the first two days because they're deterministic welcome and quickstart messages. Review-gated thereafter because content varies by buyer engagement signals.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q9]` `[Status: CONFIRMED]` — **Cold lead nurture cadence**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 8
- **Question:** How long is the cold lead nurture sequence and how many touches?
- **Choice (LOCKED 2026-04-13):** **90 days, 6 touches: Day 0, 3, 10, 30, 60, 90.** All TIER_REVIEW. A reply from the lead cancels remaining steps automatically.
- **Why:** Long enough to outlast typical legal industry buying cycles (often months); short enough that an unresponsive lead is genuinely cold by Day 90. All TIER_REVIEW because cold-lead messaging is voice-sensitive and Kyle wants final approval.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

`[PRE Q10]` `[Status: CONFIRMED]` — **Production feature flag default**
- **File:** specs/2026-04-13-steward-operationalized-design.md Section 11
- **Question:** When SP3 ships to production, should `STEWARD_ENABLED` default to true or false?
- **Choice (LOCKED 2026-04-13):** **`STEWARD_ENABLED=false` in production at first deploy.** Kyle flips to `true` after the staging soak in Session 8 is approved.
- **Why:** Lets the code ship to production for testing and verification without enabling automation. Single-flag kill switch if anything goes wrong post-launch.
- **Logged:** 2026-04-13
- **Confirmed:** 2026-04-13

---

### Session 1 — Steward scaffolding, inbound webhook stub, schema, render.yaml

`[S3-1]` `[Status: PENDING]`
- **File:** stripe-delivery/api/inbound.py — Postmark inbound shared-secret mechanism
- **Question:** Postmark's inbound webhook supports either URL basic-auth (e.g., `https://user:pass@host/api/inbound`) or a custom header for shared-secret validation. Which does Steward expect?
- **Agent default:** Accept BOTH. The validation function tries `Authorization: Basic ...` first (extracts the password as the secret), then falls back to `X-Postmark-Inbound-Token` header. Kyle picks one in the Postmark dashboard before Session 3 live testing. Both validate against the same `POSTMARK_INBOUND_SECRET` env var via `secrets.compare_digest`.
- **Logged:** 2026-04-13

---

`[S3-1]` `[Status: PENDING]`
- **File:** stripe-delivery/api/inbound.py + render.yaml — STEWARD_ENABLED default per environment
- **Question:** Spec says STEWARD_ENABLED defaults to `true` in staging and `false` in production. How to encode this without two render.yaml entries?
- **Agent default:** Code default is `true` (staging-friendly). Render production env has an explicit `STEWARD_ENABLED=false` override that Kyle sets manually before SP3 goes live. Render staging has no override (uses code default = true). Documented in `_ops/INCIDENT_RUNBOOK.md` Session 8 addendum.
- **Logged:** 2026-04-13

---

`[S3-1]` `[Status: PENDING]`
- **File:** stripe-delivery/api/db.py — inbound_emails retention
- **Question:** How long to retain raw inbound payloads in `inbound_emails`?
- **Agent default:** 90 days. Housekeeping cron added in Session 8 (deletes rows older than `received_at - 90 days`). Spec Section 12 baseline.
- **Logged:** 2026-04-13

---

`[S3-1]` `[Status: PENDING]`
- **File:** stripe-delivery/api/steward/enforcement.py — CHDB scan scope
- **Question:** Spec lists From, FromFull, To, ToFull, Cc, CcFull, Bcc, BccFull. Should the scan also cover ReplyTo, OriginalRecipient, and Headers[] address values?
- **Agent default:** **Yes — paranoid scan.** Iterate every string-shaped value in the payload (top-level + nested in Headers array) and reject on any `chdblaw.com` substring (case-insensitive). False positives are acceptable; false negatives are not. The CHDB rule has zero exceptions.
- **Logged:** 2026-04-13

---

`[S3-1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml — new Render services declared as stubs
- **Question:** SP2 Session 8 hit the "Render won't silently provision new billable resources" pain mid-build. How to avoid the same in SP3?
- **Agent default:** Declare BOTH new SP3 cron services (`sidebarcode-steward-tick`, `sidebarcode-steward-nurture-enroll`) in render.yaml in Session 1 with stub start commands. Kyle re-applies the Blueprint once at the end of Session 1 to provision them. Sessions 2-8 fill in the real start commands as code lands. Kyle does not need to re-Blueprint mid-build.
- **Note:** Stub start commands are shell scripts that print "stub - Session N implements" and exit 0. Render schedules them but they do nothing useful until the real implementation lands. This is the same pattern SP2 should have used and is the actionable lesson learned.
- **Logged:** 2026-04-13

---

`[S3-1]` `[Status: PENDING]` — **Manual Postmark inbound configuration not yet performed.**
- Kyle's outside-of-session tasks before Session 3 can be tested live:
  1. Add MX record at GoDaddy: `sidebarcode.com` → `inbound.postmarkapp.com` priority 10
  2. In Postmark dashboard → Server → Settings → Inbound: set Webhook URL to `https://sidebarcode-api.onrender.com/api/inbound`
  3. Set Inbound Domain to `sidebarcode.com`
  4. Generate a 32-character random string (`openssl rand -hex 16`), set it in Render web service env as `POSTMARK_INBOUND_SECRET`, and configure Postmark to send it as either URL basic-auth or `X-Postmark-Inbound-Token` header (agent supports both).
- **Logged:** 2026-04-13

---

## Kyle manual verification queue

*(Day-session agents drop links and test outputs here for Kyle to eyeball in the evening.)*

---

## Confirmed / resolved

*(Move entries here after Kyle marks them CONFIRMED or CHANGE_TO. Keep a running history so the next session can check prior decisions.)*
