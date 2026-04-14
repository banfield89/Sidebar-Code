# SP2 Day Session Playbook
## Semi-autonomous coding sessions for Stripe + Delivery build-out

**Date:** April 13, 2026
**Scope:** Sub-Project 2 infrastructure tasks that can run without SP1 content
**Pairs with:** [2026-04-13-stripe-delivery-design.md](../specs/2026-04-13-stripe-delivery-design.md)
**Mode:** Day = heavy coding with agent. Evening = Kyle brainstorming + decisions.

---

## How to use this playbook

1. Pick the next unfinished session below.
2. Copy the **paste-ready kickoff prompt** at the bottom of that session into a new Claude Code session.
3. Let the agent work. It should run to the exit criteria without needing you.
4. When the agent hits a **DECISION NEEDED** flag, it appends the question to [DECISIONS_PARKING_LOT.md](DECISIONS_PARKING_LOT.md) and keeps going with the documented default. Do NOT stop and wait.
5. Evening: read the parking lot, make the calls, update the placeholder values in the next day's session.
6. Each session ends with a deploy to staging that runs green. If staging isn't green, the session is not done.

### Operating principles

- **Infrastructure first, copy last.** Every template uses `{{ PLACEHOLDER }}` merge vars. Copy is filled in a separate evening pass, not during coding.
- **Mock the catalog.** Use `mock_catalog_index.yaml` (checked in) with 3 fake tiers until SP1 ships real data. Swap later.
- **Never block on Kyle.** If the agent needs a decision, it picks the spec default, logs the question to the parking lot, and continues.
- **Tests gate commits.** Every session adds tests for what it built. Staging deploy must pass the tests.
- **One session = one deployable PR.** No half-finished branches.
- **Idempotent from day one.** Every webhook handler, every cron, every background task MUST be safe to run twice. Non-negotiable.

### Decisions parking lot

The agent writes to [DECISIONS_PARKING_LOT.md](DECISIONS_PARKING_LOT.md) in this folder. Each entry has: session number, file path, question, the default the agent used, date. Kyle reads this in the evening and marks items `CONFIRMED` or `CHANGE_TO: ...`.

---

## Session index

| # | Session | Depends on | Est. time | Blocks day? |
|---|---|---|---|---|
| 1 | Accounts + secrets + repo scaffolding | none | 2-3h | No |
| 2 | FastAPI skeleton + CI + staging deploy | 1 | 3-4h | No |
| 3 | Zip builder + R2 upload + signed URLs | 2 | 3-4h | No |
| 4 | Mock catalog + Stripe sync + Checkout session | 2 | 3-4h | No |
| 5 | Webhook handler + signature verification + idempotency | 4 | 3-4h | No |
| 6 | SQLite schema + purchases + leads + refund handler | 5 | 3-4h | No |
| 7 | End-to-end delivery wiring (both branches) + placeholder emails | 3, 6 | 4h | No |
| 8 | Admin dashboard + daily digest + housekeeping crons + runbook | 7 | 3-4h | No |

Total: ~8 day sessions, ~24-30 hours of agent work. Kyle's evening work is answering parking-lot questions and writing copy.

**After Session 8, SP2 is fully wired end-to-end in staging with mock data. SP1 outputs can be swapped in during a single finishing session whenever SP1 ships.**

---

## Session 1 — Accounts, secrets, repo scaffolding

**Goal:** External services provisioned. Repo has the SP2 folder structure and empty config files. Nothing deployed yet.

**Prereqs:** None. This is the first session.

**Autonomous tasks:**
1. Create `Side Bar Code/stripe-delivery/` with the full folder layout from Appendix A of the spec.
2. Write `requirements.txt` with: fastapi, uvicorn, stripe, boto3, python-multipart, postmarker, pyyaml, pytest, httpx, python-dotenv, gitleaks (dev).
3. Write `.env.example` with every variable name from Section 6 of the spec, no values.
4. Write `render.yaml` defining the web service and static site, pointing at this folder.
5. Write `README.md` with a 20-line summary of what the service does and how to run locally.
6. Create empty Python files for every module named in Appendix A: `main.py`, `checkout.py`, `webhook.py`, `catalog.py`, `delivery.py`, `crm.py`, `admin.py`. Each file has a one-line docstring describing its purpose.
7. Create `tests/` folder with a `conftest.py` that loads `.env.test`.
8. Initialize `pytest.ini` and confirm `pytest` runs (zero tests is fine).
9. Commit.

**External account tasks (Kyle does these outside the agent, 30 min):**
- Create Stripe account if not already existing. Enable Stripe Tax (US-only), enable Radar.
- Create Cloudflare R2 account, create three buckets: `sidebarcode-dev`, `sidebarcode-staging`, `sidebarcode-prod`. Add lifecycle rule: delete objects 7 days after `download_url_expires_at` tag.
- Create Postmark account. Add domain `sidebarcode.com`. Note SPF/DKIM records for DNS.
- Create Render account if not existing. Link to GitHub.

**Agent parks these for Kyle:**
- DECISION NEEDED: Do we use a single Render service for checkout + webhook, or split them? Default: single service (simpler).
- DECISION NEEDED: Confirm domain `sidebarcode.com` is in Kyle's control for DNS SPF/DKIM. Default: assume yes.

**Exit criteria:**
- Folder structure matches Appendix A exactly.
- `pytest` runs clean with zero tests.
- `git status` is clean after commit.
- Kyle has created the external accounts (checked off manually).

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 1 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Read that file's Session 1 section and the matching spec at [path-to]/docs/superpowers/specs/2026-04-13-stripe-delivery-design.md Appendix A.

Execute every Autonomous task in Session 1. Do not do anything outside Session 1's scope. If you hit a DECISION NEEDED, write it to [path-to]/docs/superpowers/plans/DECISIONS_PARKING_LOT.md with session number, question, and the default you chose, then continue using the default.

Do not wait for Kyle on the external account tasks; those are his to do separately. Just note them as pending.

Finish when every exit criterion in Session 1 is met. Commit with message "SP2 Session 1: repo scaffolding and service folder layout".
```

---

## Session 2 — FastAPI skeleton, CI, first staging deploy

**Goal:** `/health` returns 200 on staging.sidebarcode.com. CI runs tests and secret scans on every push.

**Prereqs:** Session 1 done. Render + GitHub linked. `STRIPE_SECRET_KEY` (test mode), `POSTMARK_API_TOKEN`, `R2_*` env vars set in Render staging.

**Autonomous tasks:**
1. Build FastAPI app in `api/main.py` with routes: `/health`, `/api/checkout` (stub, returns 501), `/api/session/{id}` (stub), `/api/webhook` (stub), `/admin/dashboard` (stub with basic auth).
2. `/health` returns `{status: ok, version: <git sha>, env: <staging|prod>}`.
3. Write `conftest.py` and three tests: `test_health_ok`, `test_checkout_returns_501`, `test_webhook_returns_501`.
4. Add GitHub Actions workflow `.github/workflows/ci.yml`: run `pytest`, run `gitleaks detect`, run `pip-audit`. All three gate merges.
5. Deploy to Render staging. Confirm `/health` returns 200 from `staging.sidebarcode.com/health`.
6. Commit.

**Agent parks these:**
- DECISION NEEDED: Basic auth credentials for `/admin/dashboard`. Default: read from `ADMIN_USER` and `ADMIN_PASSWORD` env vars, fail closed if unset.
- DECISION NEEDED: Python version. Default: 3.12 (matches Render default).

**Exit criteria:**
- `curl https://staging.sidebarcode.com/health` returns 200 with correct JSON.
- CI runs green on the commit.
- Three tests pass locally and in CI.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 2 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Session 1 is done. Read Session 2 and execute every Autonomous task. Parking lot rules from the playbook apply. Deploy must reach staging and /health must return 200 before you commit.

If the Render deploy fails for a reason you cannot diagnose from logs, park it with full error output and move to the next task that does not depend on staging.

Commit with message "SP2 Session 2: FastAPI skeleton, CI, staging deploy".
```

---

## Session 3 — Zip builder, R2 upload, signed URLs

**Goal:** Given any local folder path, produce a signed R2 download URL that works for 72 hours and returns the zipped contents. Fully tested.

**Prereqs:** Session 2 deployed. R2 buckets created. `R2_*` env vars set.

**Autonomous tasks:**
1. In `api/delivery.py`, implement `build_zip(source_dir: Path, purchase_id: str) -> Path`. Recursively zip; inject a top-level `README.txt` with purchase_id, generated-at timestamp, placeholder license summary, and `support@sidebarcode.com`.
2. Implement `upload_to_r2(zip_path: Path, object_key: str) -> str`. Uses boto3 with R2 endpoint. Returns the object key on success. Tags object with `expires_at=<iso>` for lifecycle cleanup.
3. Implement `sign_download_url(object_key: str, ttl_seconds: int = 259200) -> str`. Returns presigned URL.
4. Create `tests/fixtures/dummy_deliverable/` with 3 sample files (a text file, a fake PDF placeholder, a folder with nested files).
5. Write tests: `test_build_zip_includes_readme`, `test_build_zip_preserves_folder_structure`, `test_upload_to_r2_roundtrip` (uses dev bucket), `test_signed_url_expires` (mocked clock), `test_signed_url_rejects_after_delete` (integration test against dev bucket).
6. Manual verification script `scripts/manual_zip_test.py`: zips the dummy folder, uploads, prints signed URL for Kyle to click and verify.
7. Commit.

**Agent parks these:**
- DECISION NEEDED: Should ZIP contents include the top-level folder name (`parser_trial/file.md`) or not (`file.md`)? Default: yes, include folder name for clarity.
- DECISION NEEDED: ZIP compression level. Default: 6 (Python default, balanced).
- DECISION NEEDED: Max ZIP size alert threshold. Default: 500MB — log warning if exceeded.

**Exit criteria:**
- All 5 tests pass, including the R2 roundtrip integration test against the dev bucket.
- Manual script produces a URL that Kyle can click to download the dummy zip.
- The signed URL returns 403 or 404 after the R2 object is deleted.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 3 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-2 are done. Read Session 3 and execute every Autonomous task. The R2 roundtrip test MUST hit the real dev bucket, not a mock. Parking lot rules from the playbook apply.

After the tests pass, run the manual verification script and save its output (including the signed URL) to DECISIONS_PARKING_LOT.md under a "Kyle manual verification" section. Kyle will click the link in the evening to confirm.

Commit with message "SP2 Session 3: zip builder, R2 upload, signed URLs".
```

---

## Session 4 — Mock catalog, Stripe sync script, Checkout session creation

**Goal:** `POST /api/checkout` with a mock tier_id returns a real Stripe test-mode Checkout URL. Kyle can complete a test purchase end-to-end in staging.

**Prereqs:** Session 2 deployed. Stripe test mode key set in Render staging.

**Autonomous tasks:**
1. Create `mock_catalog_index.yaml` in `stripe-delivery/` with 3 fake tiers: `mock_parser_trial` ($1.97 — Stripe minimum), `mock_consulting_foundation` ($25.00 notify_kyle), `mock_workflow_single` ($50.00 notify_kyle). Mirror the exact schema from spec Section 3.
2. In `api/catalog.py`, implement `load_catalog_index(path=None) -> CatalogIndex`. Default path: `mock_catalog_index.yaml` in dev/staging, real path in prod (env-driven).
3. Write `scripts/sync_stripe_catalog.py`: reads catalog, upserts Stripe Products (key = `metadata.tier_id`), creates new Price if amount or currency differs, archives old Price. Writes `CATALOG_INDEX.stripe.yaml` to disk with the resolved `stripe_product_id` and `stripe_price_id`. Dry-run flag supported.
4. Run the sync against Stripe test mode. Confirm 3 products exist in test dashboard.
5. Implement `POST /api/checkout` body: `{tier_id, tos_accepted, tech_overview_accepted}`. Validates both acceptance booleans are true (422 if not). Creates Stripe Checkout Session with `line_items` from the resolved Price, metadata includes `tier_id`, `tos_accepted_at`, `tech_overview_accepted_at`, `tos_version_hash`, `tech_overview_version_hash`, buyer IP from request. Returns `{checkout_url, session_id}`.
6. Implement `GET /api/session/{session_id}`: fetches the session from Stripe, returns `{tier_id, delivery_type, amount, status}`. Read-only.
7. Tests: `test_checkout_requires_tos`, `test_checkout_requires_tech_overview`, `test_checkout_creates_session_with_metadata`, `test_session_get_returns_tier_info`, `test_sync_catalog_upsert_roundtrip` (against Stripe test mode).
8. Manual verification: hit `POST /api/checkout` on staging with `tier_id=mock_parser_trial`, paste the returned URL into a browser, complete the purchase with card `4242 4242 4242 4242`. Confirm Stripe dashboard shows the test charge.
9. Commit.

**Agent parks these:**
- DECISION NEEDED: Should Stripe Checkout collect phone number? Default: yes (helpful for consulting tiers).
- DECISION NEEDED: Minimum viable tier price for Stripe? Stripe minimum is $0.50; mock uses $1.97 to stay meaningful but cheap for testing.
- DECISION NEEDED: Buyer IP collection location — request headers or Stripe client_reference_id? Default: request headers at session creation, stored in Stripe metadata.

**Exit criteria:**
- Mock catalog has 3 tiers, spec-compliant schema.
- Sync script creates products in Stripe test mode; re-running is idempotent.
- A full test purchase completes: Kyle clicks link → Stripe Checkout → pays with test card → lands on `/success`.
- Webhook does NOT yet fire (that's Session 5) — but the Stripe dashboard shows the session completed.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 4 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-3 are done. Read Session 4 and execute every Autonomous task. Use Stripe test mode — never hit live mode in day sessions.

After the sync script runs, verify in the Stripe dashboard that 3 test-mode products exist. After implementing /api/checkout, run the manual verification yourself using curl + a headless test purchase with card 4242 4242 4242 4242. Save the completed session_id to the parking lot.

Parking lot rules from the playbook apply. Commit with message "SP2 Session 4: mock catalog, Stripe sync, Checkout session creation".
```

---

## Session 5 — Webhook handler, signature verification, idempotency

**Goal:** `checkout.session.completed` events land in `/api/webhook`, pass signature verification, get deduped, and trigger a stub delivery function. Refund and dispute events also handled.

**Prereqs:** Session 4 done. Webhook secret set in Render staging.

**Autonomous tasks:**
1. Register webhook endpoint in Stripe test dashboard: `https://staging.sidebarcode.com/api/webhook`. Subscribe to `checkout.session.completed`, `charge.refunded`, `charge.dispute.created`, `charge.dispute.closed`. Copy the signing secret to Render env.
2. Implement `POST /api/webhook` in `api/webhook.py`: read raw body, verify signature with `stripe.Webhook.construct_event`, return 400 on failure.
3. Create SQLite table `processed_events (stripe_event_id PRIMARY KEY, processed_at TEXT)`. Middleware: if event_id already processed, return 200 immediately. Else insert and continue.
4. Route the event by type to stub handlers: `handle_checkout_completed(session) -> None` (logs and returns), `handle_refund(charge)`, `handle_dispute_opened(dispute)`, `handle_dispute_closed(dispute)`.
5. Each stub writes a line to a debug log table `webhook_debug_log (id, event_type, event_data_json, created_at)`.
6. Tests: `test_webhook_rejects_bad_signature`, `test_webhook_accepts_good_signature` (using Stripe's test signature construction), `test_webhook_idempotent_same_event_twice`, `test_webhook_routes_events_correctly`.
7. Manual verification: trigger a test event from Stripe CLI (`stripe trigger checkout.session.completed`), confirm staging logs show signature verified and stub handler called. Run the trigger twice and confirm the second is short-circuited by idempotency.
8. Commit.

**Agent parks these:**
- DECISION NEEDED: What does `charge.dispute.created` do beyond alerting? Spec says "flag, no auto-revoke." Default: set purchase status to `disputed`, send Kyle alert, leave download link active.
- DECISION NEEDED: How long to retain `webhook_debug_log` rows? Default: 30 days, housekeeping cron deletes older.

**Exit criteria:**
- Stripe CLI trigger delivers an event that passes signature verification in staging.
- Replaying the same event is a no-op.
- Bad signatures return 400.
- All 4 tests pass.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 5 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-4 are done. Read Session 5 and execute every Autonomous task. Use Stripe CLI (`stripe listen` + `stripe trigger`) for local testing, but the final manual verification MUST hit staging.

Idempotency is non-negotiable — the test for "same event twice is a no-op" must pass before commit.

Parking lot rules from the playbook apply. Commit with message "SP2 Session 5: webhook handler, signature verification, idempotency".
```

---

## Session 6 — SQLite schema, purchases, leads, refund handler

**Goal:** A complete test purchase writes a purchase row and (if consulting) a lead row. Refund writes the refund status and deletes the R2 object.

**Prereqs:** Sessions 3 and 5 done.

**Autonomous tasks:**
1. Create migration `api/migrations/001_initial_schema.sql` with all tables from spec Section 9 plus: `purchases`, `delivery_failures`, `webhook_debug_log`, `processed_events`, `tos_versions`, `tech_overview_versions`. Use the exact schema from the spec.
2. Implement `api/crm.py` with models and helpers: `insert_purchase`, `insert_lead`, `update_purchase_status`, `get_purchase_by_charge_id`, `record_lead_event`, `get_lead`. All use parameterized SQL. All are idempotent where it makes sense.
3. Wire `handle_checkout_completed` from Session 5 to:
   - Look up tier in catalog by `tier_id` from session metadata.
   - Branch on `delivery_type`: `zip_download` → insert purchase row, call `build_and_deliver_zip` stub (next session wires it). `notify_kyle` → insert purchase row AND lead row, call `notify_kyle_new_purchase` stub.
4. Wire `handle_refund`:
   - Look up purchase by `stripe_charge_id`.
   - For zip_download: delete R2 object, set `status=refunded`, set `download_url_expires_at=now`.
   - For notify_kyle: set `status=refunded`, call `notify_kyle_refund` stub.
5. Tests: `test_purchase_insert_and_fetch`, `test_lead_insert_and_fetch`, `test_checkout_completed_zip_branch_writes_purchase`, `test_checkout_completed_notify_branch_writes_purchase_and_lead`, `test_refund_deletes_r2_object` (uses dev bucket), `test_refund_sets_status_refunded`.
6. Nightly backup script `scripts/backup_sqlite.py`: copies the SQLite file to R2 as `sqlite-backup-{date}.db`. Retains 30 days.
7. Commit.

**Agent parks these:**
- DECISION NEEDED: SQLite WAL mode? Default: yes, enabled in app startup.
- DECISION NEEDED: Should consulting lead rows include anything from Stripe metadata beyond email/name/phone? Default: no, minimal capture, Steward enriches later.
- DECISION NEEDED: Lead `status` default for stripe-sourced leads: `new` or `qualified`? Default: `qualified` (they paid, they're serious).

**Exit criteria:**
- All 6 tests pass.
- Running a full mock purchase end-to-end: checkout → Stripe → webhook → purchase row written in SQLite on staging.
- Running a refund: R2 object deleted, purchase row updated.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 6 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-5 are done. Read Session 6 and execute every Autonomous task. Use the exact SQLite schema from the spec Section 9 — do not deviate. Steward depends on this schema being stable.

Parking lot rules from the playbook apply. Commit with message "SP2 Session 6: SQLite schema, purchases, leads, refund handler".
```

---

## Session 7 — End-to-end delivery wiring (both branches) + placeholder emails

**Goal:** A completed checkout on staging results in an actual email landing in Kyle's inbox (zip_download branch: with a working signed URL to a mock zip; notify_kyle branch: with placeholder receipt + scheduling link).

**Prereqs:** Sessions 3, 5, 6 done. Postmark staging templates created with merge var skeletons.

**Autonomous tasks:**
1. Create Postmark templates (via API or dashboard) with placeholder bodies:
   - `product_download`: `{{ buyer_name }}, your {{ tier_name }} is ready. Download: {{ download_url }}. Expires {{ expires_at }}. Support: {{ support_email }}.`
   - `consulting_receipt`: placeholder body with `{{ tier_name }}`, `{{ amount }}`, `{{ scheduling_link }}`, `{{ kyle_email }}`.
   - `kyle_new_consulting_purchase`: placeholder with `{{ buyer_name }}`, `{{ buyer_email }}`, `{{ tier_name }}`, `{{ amount }}`, `{{ crm_link }}`.
   - `delivery_failure_alert`: placeholder with `{{ purchase_id }}`, `{{ tier_id }}`, `{{ error }}`, `{{ traceback }}`.
2. Save template IDs to env vars (`POSTMARK_TEMPLATE_PRODUCT_DOWNLOAD`, etc).
3. Implement a small helper `retry_once(callable, *args, backoff_seconds=1.0, **kwargs)` in `api/delivery.py`. Pattern: try callable → on any exception, sleep backoff_seconds, try once more → on second exception, raise. NOT a generic decorator — it's an explicit wrapper used per call site so failures show up clearly in traces. Per the 2026-04-13 PRE Q7 decision (see DECISIONS_PARKING_LOT.md and spec Section 7 "Retry strategy").
4. Implement `build_and_deliver_zip(purchase)` in `api/delivery.py`: resolves `delivery_source` path from catalog → calls `build_zip` → wraps `upload_to_r2` in `retry_once` → wraps `sign_download_url` in `retry_once` (cheap and local but sometimes hits R2) → writes `zip_object_key` and `download_url_expires_at` to purchase row → wraps Postmark `product_download` template send in `retry_once`. ONLY after a `retry_once` raises (meaning two consecutive failures of the same call) does the function write a `delivery_failures` row and send a `delivery_failure_alert` Postmark. After writing the alert, re-raise the exception so Stripe webhook retry kicks in. Do NOT suppress.
5. Implement `notify_kyle_new_purchase(purchase, lead)`: reads tier `scheduling_link` from catalog → wraps Postmark `kyle_new_consulting_purchase` send in `retry_once` → wraps Postmark `consulting_receipt` send in `retry_once`. No exception suppression. On second-failure raise, the webhook handler bubbles to Stripe for Layer-2 retry.
6. Implement `notify_kyle_refund(purchase)`: wraps Postmark refund alert send in `retry_once`. Same retry-once-then-raise semantics.
7. Wire the stubs from Session 6 to the real functions.
8. Tests:
   - `test_deliver_zip_writes_purchase_fields` — happy path, all calls succeed first try
   - `test_deliver_zip_succeeds_on_retry_after_one_r2_failure` — mock R2 to fail once then succeed; confirm purchase delivered, NO `delivery_failures` row written, NO alert sent (NEW per Q7)
   - `test_deliver_zip_succeeds_on_retry_after_one_postmark_failure` — mock Postmark to fail once then succeed; same assertions (NEW per Q7)
   - `test_deliver_zip_alerts_only_on_second_r2_failure` — mock R2 to fail twice; confirm `delivery_failures` row written, `delivery_failure_alert` sent, exception re-raised (NEW per Q7)
   - `test_deliver_zip_alerts_only_on_second_postmark_failure` — mock Postmark to fail twice; same assertions (NEW per Q7)
   - `test_notify_kyle_sends_both_emails`
   - `test_notify_kyle_retries_once_per_send` — mock first Postmark call to fail once then succeed (NEW per Q7)
   - `test_refund_notify_sends_alert`
   - `test_retry_once_helper_basic` — unit test for the retry_once helper itself: success first try, success second try, failure both tries
   Use Postmark test mode for all email tests; use a mock or recording R2 client for the failure-path tests (do NOT actually fail real R2 calls in CI).
8. Manual verification: complete a test purchase of `mock_parser_trial` on staging. Confirm Kyle receives an email with a working download link. Click the link, confirm the dummy zip downloads. Complete a test purchase of `mock_consulting_foundation`. Confirm Kyle receives the alert email and the "buyer" (Kyle) receives the receipt.
9. Commit.

**Agent parks these:**
- DECISION NEEDED: Postmark template copy is fully placeholder. Kyle fills in evening sessions. Log each template ID + current placeholder body to the parking lot for Kyle to iterate on.
- DECISION NEEDED: Should the `delivery_failure_alert` email include the traceback, or just the error message? Default: full traceback (it's an internal alert, not customer-facing).
- DECISION NEEDED: Does the `consulting_receipt` email include the purchase amount? Default: yes (standard receipt practice).

**Exit criteria:**
- Complete mock purchase on staging → email arrives → download works.
- Complete mock consulting purchase on staging → Kyle alert + buyer receipt both arrive.
- All 9 tests pass (including the 5 new retry-behavior tests per Q7).
- `retry_once` helper exists in `api/delivery.py` and is exercised by every external call in the delivery functions.
- A simulated transient failure (R2 fails once then succeeds) does NOT write a `delivery_failures` row and does NOT send an alert — verified by test, not just by code review.
- Parking lot has the 4 template bodies logged for Kyle's evening copy pass.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 7 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-6 are done. Read Session 7 and execute every Autonomous task. Use Postmark test mode for all emails in tests, but manual verification must hit Postmark staging stream so real emails land in Kyle's inbox.

This is the most important session — end of it means the full delivery pipe works with mock data. Do not cut corners on the test coverage for delivery failures.

Parking lot rules from the playbook apply. Commit with message "SP2 Session 7: end-to-end delivery wiring + placeholder emails".
```

---

## Session 8 — Admin dashboard, daily digest, housekeeping crons, incident runbook

**Goal:** Kyle can see at a glance what's happening. Dead pipe fails loudly. Bad state self-heals or alerts.

**Prereqs:** Session 7 done.

**Autonomous tasks:**
1. Implement `/admin/dashboard` (basic auth) with three panels:
   - Last 50 purchases with status (delivered, refunded, awaiting_delivery, failed).
   - Pending consulting leads (status = qualified AND no follow-up recorded).
   - Failed deliveries in last 7 days with a "Resend" button that regenerates the ZIP and signed URL.
2. Implement resend action: background task, reuses `build_and_deliver_zip`, writes audit row.
3. Implement `scripts/send_daily_digest.py`: queries purchases and leads for the last 24 hours, sends Postmark email to Kyle. Sends even on zero-purchase days (so silence is meaningful).
4. Implement `scripts/cleanup_r2.py`: lists R2 objects, deletes any whose tagged `expires_at` is more than 7 days old. Logs a summary line.
5. Implement `scripts/cleanup_webhook_debug_log.py`: deletes `webhook_debug_log` rows older than 30 days.
6. Configure Render cron jobs for all three scripts: digest daily at 08:00 Kyle time, cleanups nightly at 03:00.
7. Write `_ops/INCIDENT_RUNBOOK.md` covering: webhook service down, Stripe webhook retries visible in dashboard, R2 upload failing, Postmark delivery failing, SQLite locked, buyer reports missing email, dispute opened. Each scenario has a "symptoms", "diagnosis", "fix", "prevention" section.
8. Tests: `test_admin_dashboard_requires_auth`, `test_admin_dashboard_lists_recent_purchases`, `test_resend_action_creates_new_signed_url`, `test_daily_digest_sends_even_on_zero_purchases`, `test_cleanup_r2_deletes_expired_objects_only`.
9. Manual verification: load the admin dashboard in staging, confirm it shows the test purchases from previous sessions. Trigger a manual run of the daily digest script and confirm Kyle receives the email.
10. Commit.

**Agent parks these:**
- DECISION NEEDED: Admin dashboard — should the resend button have a confirmation modal? Default: yes (prevents accidental clicks).
- DECISION NEEDED: Daily digest time zone. Default: America/Phoenix (Kyle's local).
- DECISION NEEDED: Should the incident runbook link to Stripe/Postmark/R2 dashboards by name? Default: yes, with URL placeholders Kyle fills in.

**Exit criteria:**
- Admin dashboard loads on staging and shows accurate data.
- Daily digest email arrives in Kyle's inbox with a test run.
- All cron jobs configured and one successful manual run each.
- Incident runbook exists and covers 7+ scenarios.
- All 5 tests pass.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 2 Session 8 from [path-to]/docs/superpowers/plans/2026-04-13-sp2-day-session-playbook.md.

Sessions 1-7 are done. Read Session 8 and execute every Autonomous task. This closes out the SP2 infrastructure build. After this session, SP2 is staging-complete with mock data and ready for SP1 content swap-in.

The incident runbook is not optional — Kyle needs to know what to do when things break at 9pm on a Saturday. Write it like the reader is tired and stressed.

Parking lot rules from the playbook apply. Commit with message "SP2 Session 8: admin dashboard, crons, incident runbook — SP2 infra complete".
```

---

## After Session 8: the "SP1 swap-in" session

When SP1 is done, one more session (not a day session — closer to a half-day) does the swap:

1. Point `CATALOG_INDEX_PATH` env var at the real `Product Catalog/CATALOG_INDEX.yaml`.
2. Run `sync_stripe_catalog.py` against Stripe test mode with real tiers at real prices.
3. Replace Postmark template placeholder bodies with Kyle's final copy (pulled from Sales Playbook voice).
4. Replace the success/cancel page copy.
5. Replace the pre-checkout modal copy with per-tier `what_is_in_the_box.md` summaries.
6. Aemon review gate: ToS, refund policy, email templates, Technology Overview acceptance language.
7. Kyle does a full staging purchase of all 8 real tiers with test cards.
8. Flip to Stripe live mode, provision real products, redeploy.
9. Kyle purchases each live tier with his own card, refunds after verification.
10. Launch.

This swap-in is the Section 10 Phase 7 of the spec, compressed into a single session because all the plumbing is already live.

---

## Rate limit strategy notes

- Each day session is scoped to 3-4 hours of agent wall time. That burns caps efficiently without running overnight.
- Day sessions assume Claude Code is the agent. Evening brainstorming happens in claude.ai chat (separate cap pool).
- If a day session stalls on a DECISION that the spec default doesn't cleanly cover, the agent logs it and moves to the next session's tasks rather than waiting.
- Do NOT run two day sessions in parallel. Finish one, commit, deploy staging, start the next. Parallel sessions cause merge conflicts and waste caps.
- Kyle's evening work is cheap: read parking lot, answer questions, write copy into placeholder email templates. That work doesn't need heavy model calls.

---

*End of playbook. Version 1.0.*
