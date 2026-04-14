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

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q1
- **Question:** Final pricing for all 6 consulting/workflow tiers (Foundation, Implementation, Modernization, Single Workflow, Multi Workflow, Practice Area).
- **Agent default:** Placeholder amounts in mock catalog only. Day sessions do NOT touch live prices. Kyle must set real prices before the post-SP1 swap-in session.
- **Why it matters:** Stripe Prices are immutable. Changing a price after provisioning means archiving and recreating. Cheap to fix, but annoying if done repeatedly.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q2
- **Question:** Preferred scheduling tool for consulting handoff: Calendly, Cal.com, or other?
- **Agent default:** Cal.com with URL `https://cal.com/kylebanfield/foundation` (spec example). Template merge var `{{ scheduling_link }}` is tier-specific via catalog.
- **Why it matters:** Session 7 wires the scheduling link into the consulting receipt email. Changing tools later is a find/replace, but locking now avoids placeholder-in-production risk.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q3
- **Question:** Transactional email provider: Postmark or Resend?
- **Agent default:** Postmark (spec default; superior deliverability for transactional; template system is mature).
- **Why it matters:** Session 1 creates the account. Swapping providers after Session 7 means rewriting `send_email` calls and re-creating 4 templates. Not catastrophic but wasted time.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q4
- **Question:** Admin dashboard auth: basic auth (MVP) or simple login form?
- **Agent default:** Basic auth with `ADMIN_USER` / `ADMIN_PASSWORD` env vars, fail closed if unset.
- **Why it matters:** Session 8 builds the dashboard. Upgrading to a login form later is a 1-hour change. Basic auth is fine for single-user MVP.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q5
- **Question:** Parser Trial → Full Suite upsell coupon in the download email? If yes, amount and TTL?
- **Agent default:** NO coupon at MVP. Session 7 sends a clean download email without upsell. Add later if conversion data supports it.
- **Why it matters:** Adding a coupon means creating a Stripe Coupon + Promotion Code + wiring the merge var into the template. ~1 hour of work. Skipping at MVP is fine.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q6
- **Question:** Refund policy: 7-day no-questions-asked, or case-by-case?
- **Agent default:** Case-by-case, documented in ToS as "refunds at Sidebar Code's discretion within 30 days of purchase." No automated refund button.
- **Why it matters:** Affects ToS copy and Aemon review. A "no-questions 7-day" policy is cleaner legally but means more refund losses on impulse buys.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q7
- **Question:** Failed-delivery retry strategy: auto-retry N times before alerting, or alert on first failure?
- **Agent default:** Alert Kyle on FIRST failure. Stripe's built-in webhook retry handles reprocessing. The alert is for visibility, not intervention required.
- **Why it matters:** Lower threshold = more noise but faster response. Session 7 wires this.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q8
- **Question:** Consulting tiers: pay in full at Checkout, or deposit + balance due?
- **Agent default:** Pay in full at Checkout. Simpler for MVP. Deposit model requires invoicing infrastructure.
- **Why it matters:** Changing to deposit model means adding Stripe Invoicing integration later. Real but not Session-1 blocking.
- **Kyle response:**
- **Logged:** 2026-04-13

---

---

## Kyle manual verification queue

*(Day-session agents drop links and test outputs here for Kyle to eyeball in the evening.)*

---

## Confirmed / resolved

*(Move entries here after Kyle marks them CONFIRMED or CHANGE_TO. Keep a running history so the next session can check prior decisions.)*
