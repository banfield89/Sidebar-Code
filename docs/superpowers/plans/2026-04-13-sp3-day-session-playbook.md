# SP3 Day Session Playbook
## Semi-autonomous coding sessions for Steward Operationalized

**Date:** April 13, 2026
**Scope:** Sub-Project 3 — inbound triage, lifecycle automation, Aemon review, intake capture
**Pairs with:** [2026-04-13-steward-operationalized-design.md](../specs/2026-04-13-steward-operationalized-design.md)
**Mode:** Day = heavy coding session. Evening = Kyle brainstorming + decisions + parking-lot review.

---

## How to use this playbook

1. Pick the next unfinished session below.
2. Copy the **paste-ready kickoff prompt** at the bottom of that session into a new Claude Code session.
3. Let the agent work. It runs to the exit criteria without needing you.
4. When the agent hits a **DECISION NEEDED** flag, it appends the question to [DECISIONS_PARKING_LOT.md](DECISIONS_PARKING_LOT.md) under the SP3 section and continues with the documented default. Do NOT stop and wait.
5. Evening: read the parking lot, mark items CONFIRMED or CHANGE_TO, refine any placeholder template copy in the Postmark dashboard.
6. Each session ends with a deploy to staging that runs green. If staging is not green, the session is not done.

### Operating principles

- **Infrastructure first, copy last.** Every template uses `{{ PLACEHOLDER }}` merge vars. Aemon-approved final copy is filled in evening sessions, not during day coding.
- **No long-running worker.** All Steward logic runs as HTTP routes or HTTP-triggered crons inside the existing `sidebarcode-api` web service. Never propose a Background Worker, sidecar process, or async task loop. SQLite lives on the web service's persistent disk and only the web service can read or write it.
- **CHDB inbox is hard-prohibited.** Steward must never read, write, or process any email touching `@chdblaw.com`. Enforced in code at every boundary (inbound webhook, outbound send, lead insertion). No override flag, no exceptions, no future revisit without a new spec.
- **Aemon-then-Kyle, serial.** Every customer-facing draft goes through Aemon first, then either auto-sends (TIER_AUTO) or lands in Kyle's queue (TIER_REVIEW) with Aemon's annotations attached. Aemon can escalate but never de-escalate.
- **Four-tier auto-send policy.** TIER_AUTO, TIER_REVIEW, TIER_ESCALATE, TIER_SILENT. Codified in `state.send_tier_for()`. No template bypasses it.
- **Never block on Kyle.** If the agent hits a decision the spec defaults don't cover, append a `[S3-X]` entry to the parking lot with the chosen default, then keep working.
- **Tests gate commits.** Every session adds tests for what it built. Baseline: 84 tests as of the start of SP3 Session 1 (verified via `pytest --collect-only`). Test count never regresses.
- **One session = one deployable PR.** No half-finished branches. If a session can't ship cleanly, split it at a natural boundary and stop.
- **Idempotent from day one.** Every webhook handler, every scheduled email, every nurture enrollment MUST be safe to run twice. Non-negotiable.
- **Backward compatible with SP2.** Every SP2 test continues to pass after every SP3 commit. SP2 endpoints are not touched except via additive extension.

### Decisions parking lot

The agent appends to [DECISIONS_PARKING_LOT.md](DECISIONS_PARKING_LOT.md) under a new `## SP3` section. Each entry has session number, file path, question, the default the agent used, and the date. Kyle reads and marks items in evening sessions.

---

## Session index

| # | Session | Depends on | Est. time | Blocks day? |
|---|---|---|---|---|
| 1 | Steward scaffolding + inbound webhook stub + render.yaml + DB schema | none (SP2 done) | 2-3h | No |
| 2 | Lifecycle state machine + scheduled_emails table + scheduler tick endpoint | 1 | 3-4h | No |
| 3 | Inbound classifier + template renderer + Aemon module (rule-based) | 2 | 3-4h | No |
| 4 | Outbox manager + four-tier policy enforcement + end-to-end inbound pipeline | 3 | 3-4h | No |
| 5 | Pre-engagement intake automation (form delivery, web pages, brief generator) | 4 | 3-4h | No |
| 6 | Steward admin panel (queue, pipeline, scheduled, inbound, lead timeline, metrics) | 4, 5 | 3-4h | No |
| 7 | Nurture sequences + onboarding drip + Aemon production rule pass | 4, 6 | 3-4h | No |
| 8 | 24-hour soak, incident runbook addendum, production cutover | 7 | 4h + 24h soak | No |

Total: ~8 day sessions, ~24-28 hours of agent work plus a 24-hour staging soak. Kyle's evening work is parking-lot review, template copy refinement, and external service configuration (DNS, Postmark inbound, Aemon rule confirmation).

**After Session 8, SP3 is fully wired end-to-end in production behind a feature flag. Kyle flips `STEWARD_ENABLED=true` in Render env when ready.**

---

## Session 1 — Scaffolding, inbound webhook stub, render.yaml, DB schema

**Goal:** Steward subpackage skeleton exists. `/api/inbound` route accepts Postmark inbound payloads behind a shared secret, hard-fails on any CHDB address, writes the raw payload to a new `inbound_emails` debug table, and returns 200. Tests pass green. New cron services declared in render.yaml with stub commands (so the Blueprint apply happens once at the start of SP3, not mid-build).

**Prereqs:**
- SP2 complete (it is, as of 2026-04-13).
- The 11 spec PRE entries (`[PRE]` Q1-Q10) are reviewed; defaults are acceptable for Session 1 to proceed.
- Kyle has NOT yet configured Postmark inbound or the GoDaddy MX record. Session 1 is fully autonomous and does not require any external service to be live.

**Autonomous tasks:**

1. Create `stripe-delivery/api/steward/` subpackage with:
   - `__init__.py` containing the package docstring
   - `README.md` describing the layout from spec Appendix A and where each module lives
   - 11 stub modules, each with a one-line docstring describing its eventual purpose: `state.py`, `classifier.py`, `templates.py`, `aemon.py`, `outbox.py`, `scheduler.py`, `sequences.py`, `intake.py`, `brief.py`, `enforcement.py`
   - Every stub file is importable (no syntax errors) but contains no business logic beyond a `__all__` list and the module docstring
2. Create `stripe-delivery/api/inbound.py` with:
   - FastAPI router exporting `router`
   - `POST /api/inbound` endpoint
   - `_verify_postmark_secret(request)` helper using `secrets.compare_digest` against `POSTMARK_INBOUND_SECRET` env var; 401 on failure or missing env
   - `_enforce_chdb_separation(payload)` helper that scans From, FromFull, To, ToFull, Cc, CcFull, Bcc, BccFull (and any address-shaped value in the payload) for `chdblaw.com` (case-insensitive) and raises HTTPException(422) on hit
   - Insert raw payload into `inbound_emails` table, return `{"status": "logged", "inbound_id": ...}` and 200
   - Wraps everything in try/except so the function never 500s on bad Postmark payloads (returns 422 with a friendly error instead)
3. Wire `inbound.router` into `stripe-delivery/api/main.py` alongside the existing routers.
4. Extend `stripe-delivery/api/db.py` `_SCHEMA_SQL` block with the `inbound_emails` table from spec Section 5. Use `CREATE TABLE IF NOT EXISTS`. Add the four indexes from the spec.
5. Update `render.yaml`:
   - Add new web service env vars (sync: false): `STEWARD_ENABLED`, `STEWARD_AEMON_ENABLED`, `POSTMARK_INBOUND_SECRET`, `STEWARD_INTAKE_HMAC_SECRET`. Optionally `ANTHROPIC_API_KEY` (sync: false) — Session 3 wires it.
   - Add two new cron services declared as **stubs** so the Blueprint apply happens now instead of mid-build:
     - `sidebarcode-steward-tick` schedule `* * * * *`, startCommand `python scripts/trigger_steward_tick.py` (the script is created in Session 2; for Session 1 commit a stub that prints "stub - Session 2 implements" and exits 0)
     - `sidebarcode-steward-nurture-enroll` schedule `0 16 * * *`, startCommand `python scripts/trigger_steward_nurture_sweep.py` (also a stub)
   - Both crons inherit `CRON_SECRET` and `SP2_API_URL` via `fromService` with the sibling `key` field per the SP2 Session 8 fix
6. Create `stripe-delivery/scripts/trigger_steward_tick.py` and `stripe-delivery/scripts/trigger_steward_nurture_sweep.py` as one-line stubs that print and exit 0. Session 2 fills in the HTTP-trigger logic.
7. Create `stripe-delivery/api/steward/enforcement.py` with the canonical `_enforce_chdb_separation` helper used by `inbound.py` and (later) `outbox.py`. Include reasoning comments referencing the standing rule.
8. Tests — add `stripe-delivery/tests/test_steward_inbound_route.py` with at minimum:
   - `test_inbound_rejects_missing_token` (401)
   - `test_inbound_rejects_invalid_token` (401)
   - `test_inbound_rejects_chdb_in_from` (422)
   - `test_inbound_rejects_chdb_in_to` (422)
   - `test_inbound_rejects_chdb_in_cc` (422)
   - `test_inbound_rejects_chdb_anywhere_case_insensitive` (422)
   - `test_inbound_accepts_valid_payload_writes_row` (200, row exists in inbound_emails)
   - `test_inbound_dedupes_on_postmark_message_id` (second insert returns existing inbound_id)
9. Add `stripe-delivery/tests/test_steward_enforcement.py` covering the `_enforce_chdb_separation` helper directly (not just via the route).
10. Run the full pytest suite; confirm baseline (84) plus new tests pass. CI must stay green.
11. Commit with the standard format and push to main.

**Agent parks these for Kyle (default chosen, Kyle confirms in evening):**

- `[S3-1]` `[Status: PENDING]` — **Postmark inbound shared-secret header name.** Spec uses `X-Postmark-Inbound-Token`. Postmark's documented mechanism uses URL basic-auth or a query parameter, not a custom header. **Default:** Accept either a URL basic-auth (`Authorization: Basic ...`) OR the `X-Postmark-Inbound-Token` header for flexibility; Kyle picks one in the Postmark dashboard before Session 3 live testing. The validation function tries both.
- `[S3-1]` `[Status: PENDING]` — **`STEWARD_ENABLED` default in staging.** Spec says `true` in staging. **Default applied:** `true` in staging, `false` in production. Both default values live in the code (with env override) so Render only needs the prod override.
- `[S3-1]` `[Status: PENDING]` — **inbound_emails retention.** Spec says 90 days. **Default:** 90 days, housekeeping cron added in Session 8.
- `[S3-1]` `[Status: PENDING]` — **CHDB enforcement scope.** Spec lists From/To/Cc/Bcc and their `*Full` variants. **Default:** also scan `ReplyTo`, `OriginalRecipient`, and `Headers[]` array values — be paranoid about address-shaped fields. False positives are acceptable; false negatives are not.

**Exit criteria:**

- `pytest -v` runs clean and the test count is at least 84 + the new SP3 inbound tests (target: 92+ tests).
- `git status` is clean after commit.
- The render.yaml passes Render's Blueprint validation (verify locally with `render blueprint validate render.yaml` if installed; otherwise eyeball that the YAML parses and the new envVars have the sibling `key` field on every `fromService` entry).
- The new `inbound_emails` table is created on the next deploy (verified by reading `db.py` and confirming `CREATE TABLE IF NOT EXISTS` is in `_SCHEMA_SQL`).
- A locally-issued `curl` against the new `/api/inbound` route with a valid token + a benign payload returns 200 and writes a row.
- A locally-issued `curl` with a CHDB-laced payload returns 422.
- The CI workflow on the pushed commit runs green: pytest, pip-audit, gitleaks all pass.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 3 Session 1 from docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md.

Read that file's Session 1 section and the matching spec at docs/superpowers/specs/2026-04-13-steward-operationalized-design.md (especially Section 6 inbound pipeline, Section 12 CHDB separation, and Appendix A subpackage layout).

Execute every Autonomous task in Session 1. Do not do anything outside Session 1's scope. Do not implement classification, Aemon, scheduling, templates, or admin panel — those are later sessions. Session 1 is scaffolding plus inbound webhook stub plus DB schema plus render.yaml.

CHDB hard-prohibition is non-negotiable. Every code path that touches an email address must reject @chdblaw.com hits. Test it.

If you hit a DECISION NEEDED, write it to docs/superpowers/plans/DECISIONS_PARKING_LOT.md under the SP3 section with session number, question, the default you chose, and continue using the default. Do not stop.

Run pytest after every meaningful change. Final pytest must show baseline 84 SP2 tests + new SP3 tests, all green.

Commit with message "SP3 Session 1: Steward scaffolding, inbound webhook stub, schema, render.yaml" plus the Co-Authored-By line for Claude Opus 4.6 (1M context). Push to main.
```

---

## Session 2 — Lifecycle state machine + scheduled_emails + scheduler tick

**Goal:** The lifecycle state machine, the `scheduled_emails` table, and the `/admin/cron/steward-tick` endpoint all exist and are tested. The cron tick endpoint can be POSTed locally with a valid `CRON_SECRET` and returns metrics. No actual sending happens yet — Aemon and templates are Session 3+.

**Prereqs:** Session 1 complete. New `inbound_emails` table is live.

**Autonomous tasks:**

1. Implement `api/steward/state.py` with the full lifecycle state machine from spec Section 7: `LEGAL_TRANSITIONS` dict, `transition(lead_id, to_status, reason)` function that validates and writes a `lead_events` row, `IllegalStateTransition` exception, `send_tier_for(template_id, classification=None)` function returning one of the four constants `TIER_AUTO`, `TIER_REVIEW`, `TIER_ESCALATE`, `TIER_SILENT`, and `apply_verdict(initial_tier, aemon_verdict)` that escalates per the rules in spec Section 3.
2. Implement `api/steward/scheduler.py` with CRUD over `scheduled_emails`: `enqueue(lead_id, purchase_id, template_id, context, send_tier, due_at, dedupe_key)`, `fetch_due(now, limit)`, `lock(scheduled_id)`, `mark_sent(scheduled_id, verdict)`, `mark_awaiting_kyle(scheduled_id, verdict)`, `mark_failed(scheduled_id, reason)`, `cancel_pending_for_lead(lead_id)`. All idempotent on `dedupe_key`.
3. Extend `api/db.py` `_SCHEMA_SQL` with the `scheduled_emails` table from spec Section 5. UNIQUE constraint on `dedupe_key`. Indexes per spec.
4. Add `POST /admin/cron/steward-tick` route to `api/admin.py`, protected by `_require_cron_secret`. The handler calls `scheduler.steward_tick()` (a thin wrapper that loops over `fetch_due()`, locks each row, and currently just marks them as `awaiting_kyle` with a placeholder verdict — Session 4 wires the real Aemon-then-send loop).
5. Implement `scripts/trigger_steward_tick.py` (replacing the Session 1 stub) — reads `SP2_API_URL` and `CRON_SECRET`, POSTs to `/admin/cron/steward-tick`, exits with the response status.
6. Tests — add `tests/test_steward_state.py`, `tests/test_steward_scheduler.py`, `tests/test_steward_admin_panel.py`:
   - State machine: `test_legal_transitions_round_trip`, `test_illegal_transitions_raise`, `test_status_change_writes_lead_event`, `test_send_tier_for_known_templates`, `test_unknown_template_defaults_to_escalate`, `test_apply_verdict_escalates_high_severity`, `test_apply_verdict_does_not_deescalate`, `test_force_review_overrides_auto`
   - Scheduler: `test_enqueue_writes_row`, `test_enqueue_idempotent_on_dedupe_key`, `test_fetch_due_returns_only_due_pending`, `test_lock_marks_processing`, `test_cancel_pending_for_lead_marks_cancelled`, `test_steward_tick_processes_due_rows_only`, `test_steward_tick_skips_locked_rows`
   - Cron endpoint: `test_steward_tick_endpoint_requires_bearer`, `test_steward_tick_endpoint_returns_metrics`
7. Commit + push.

**Agent parks these:**
- `[S3-2]` Default placeholder for `apply_verdict` when verdict is None (Session 2 doesn't have Aemon yet) — return the original tier unchanged.
- `[S3-2]` `scheduled_emails.context` storage format — JSON-serialized dict; agent default uses `json.dumps`.

**Exit criteria:**
- All new tests pass. SP2 tests still pass.
- `curl -X POST -H "Authorization: Bearer ${CRON_SECRET}" https://staging.../admin/cron/steward-tick` returns metrics JSON.
- Local trigger script POSTs successfully.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 3 Session 2 from docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md.

Session 1 is done. Read Session 2 and execute every Autonomous task. Do NOT implement classification, Aemon rule logic, template rendering, or any actual sending — those are Sessions 3-4. Session 2 is the state machine, the scheduler table, and the cron-triggered tick endpoint.

The state machine must reject illegal transitions with IllegalStateTransition. The scheduler must be idempotent on dedupe_key. The cron endpoint must validate CRON_SECRET via the existing _require_cron_secret pattern.

Parking lot rules apply. Commit with message "SP3 Session 2: lifecycle state machine, scheduled_emails, scheduler tick" plus Co-Authored-By for Claude Opus 4.6 (1M context). Push to main.
```

---

## Session 3 — Inbound classifier + template renderer + Aemon module

**Goal:** A draft can be classified, rendered, and Aemon-reviewed end-to-end (in a unit test). No sends happen yet — Session 4 wires send. Postmark inbound is configured live by Kyle as a parallel evening task during this session.

**Prereqs:** Sessions 1-2 done. Kyle has set up Postmark inbound MX record at GoDaddy and configured the inbound webhook URL + secret in the Postmark dashboard before this session can be tested live (autonomous coding does not require it).

**Autonomous tasks:**

1. `api/steward/classifier.py`:
   - Rule-based classifier with deterministic patterns: spam, list-bomb, autoresponder, FAQ, pricing inquiry, scheduling, hot lead, customer issue, intake response, unsubscribe
   - Returns a `Classification` dataclass with `template_id`, `confidence`, `rule_hits`, `requires_llm_fallback`
   - Optional LLM fallback gated by `CLASSIFIER_LLM_ENABLED` env var — calls Anthropic API with a small system prompt; for Session 3 this is stubbed and tested with a mock
2. `api/steward/templates.py`:
   - Jinja2 environment loading templates from `stripe-delivery/api/steward/templates_data/` directory
   - Map every template_id from spec Section 3 to a `.txt.j2` file (placeholder copy, marked TODO for Aemon review pass in Session 7)
   - `render(template_id, context)` returns the rendered string
   - `list_templates()` returns the registry (used by tests and admin panel)
3. `api/steward/aemon.py`:
   - `AemonVerdict` dataclass per spec Section 4
   - `review(draft, classification)` function with the 10 rule checks from spec Section 4
   - Each rule is a small function returning a `RuleHit(name, severity, message)` or None
   - Aggregates rule hits into a verdict
   - Em-dash detection uses the literal Unicode em dash character (U+2014) — never substitutes one
   - CHDB reference detection uses case-insensitive substring match against `chdblaw`
   - Practice-area claim detection uses a curated keyword list that Kyle can extend
   - Aemon never raises on draft content; only on programming errors
4. Wire classifier + templates + aemon as a unit-tested pipeline (still no sends).
5. Tests:
   - `tests/test_steward_classifier.py` — rule-based hits for each documented intent + ambiguous payloads route to LLM stub
   - `tests/test_steward_templates.py` — every template_id renders without error against a sample context, missing template_id raises
   - `tests/test_steward_aemon.py` — the 10 rule checks, including the Aemon disabled fail-closed behavior
6. Commit + push.

**Agent parks these:**
- `[S3-3]` Anthropic API model choice for LLM fallback — agent default `claude-haiku-4-5-20251001` (cheap, fast, sufficient for classification).
- `[S3-3]` Aemon practice-area keyword list — agent seeds with the 8 content pillars from CLAUDE.md plus common practice areas; Kyle tunes in evening.
- `[S3-3]` Template directory location — `stripe-delivery/api/steward/templates_data/` (chosen to keep the templates inside the Python package so they ship with the deploy).

**Exit criteria:**
- All new tests pass; SP2 + SP3 baseline holds.
- A unit test exists that runs a full inbound payload through classify → render → review and asserts the verdict structure.
- Postmark inbound is configured live by Kyle (verified manually): MX record propagated, dashboard webhook URL set, shared secret in Render env, a real test inbound to kyle@sidebarcode.com lands in `inbound_emails` table.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 3 Session 3 from docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md.

Sessions 1-2 done. Read Session 3 and execute every Autonomous task. Build the classifier (rule-based + LLM fallback stub), the Jinja2 template renderer, and the Aemon review module with all 10 rule checks from spec Section 4. Do NOT wire actual Postmark sends — that's Session 4.

CHDB detection in Aemon is case-insensitive substring match. Em-dash detection is literal Unicode U+2014 — never substitute em dashes for hyphens.

Parking lot rules apply. Commit with message "SP3 Session 3: classifier, template renderer, Aemon module" plus Co-Authored-By for Claude Opus 4.6 (1M context). Push to main.
```

---

## Session 4 — Outbox manager + four-tier policy + end-to-end pipeline

**Goal:** A real test inbound email goes through the full classify → render → Aemon → send pipeline against a Postmark sandbox stream. TIER_AUTO sends auto-send. TIER_REVIEW lands in `scheduled_emails` with `status='awaiting_kyle'`. TIER_ESCALATE writes a brief and notifies Kyle. TIER_SILENT files silently.

**Prereqs:** Sessions 1-3 done. Postmark inbound live. Postmark sandbox stream available.

**Autonomous tasks:**

1. `api/steward/outbox.py`:
   - `send_now(draft, verdict, recipient)` — wraps Postmark send in `retry_once` per the SP2 Q7 pattern, writes `lead_events` row on success, writes `delivery_failures` on second failure
   - `queue_for_kyle(draft, verdict, lead_id)` — inserts a `scheduled_emails` row with `due_at=now`, `status='awaiting_kyle'`, attaches verdict
   - `escalate(draft, verdict, lead_id)` — sends Kyle a brief via `sp3-escalation-brief` Postmark template and writes `lead_events('escalation_required')`
   - `file_silent(payload, classification)` — writes `lead_events('filed_silent')` and stops
   - All paths call `_enforce_chdb_separation_outbound(recipient)` before any Postmark API call
2. Wire `/api/inbound` to call the full pipeline from spec Section 6 (replacing the Session 1 stub which only logged and returned).
3. Add Postmark templates via `scripts/sync_postmark_templates.py`: `sp3-faq-reply`, `sp3-pricing-inquiry-reply`, `sp3-scheduling-proposal`, `sp3-escalation-brief`, `sp3-intake-ack`, `sp3-unsub-confirm`, `sp3-refund-confirmed`, `sp3-steward-failure-alert`. Placeholder bodies, marked for Session 7 Aemon copy pass.
4. Tests:
   - `tests/test_steward_outbox.py` — happy path, retry-once, second failure alerts, CHDB rejection
   - `tests/test_steward_e2e_pipeline.py` — full inbound payload → classify → render → Aemon → outbox → assert correct table state and Postmark sandbox call
5. Manual verification: send a test email to staging Postmark inbound, watch staging logs, confirm the row lands in `scheduled_emails` and (for TIER_AUTO) a real test email arrives.
6. Commit + push.

**Exit criteria:**
- All tests pass; baseline holds.
- Real test inbound flows end-to-end on staging.

**Paste-ready kickoff prompt:**
```
Work on Sub-Project 3 Session 4 from docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md.

Sessions 1-3 done. Read Session 4 and execute every Autonomous task. This is the most important session — it wires the inbound pipeline end-to-end through real Postmark sends.

CHDB enforcement runs at every outbox boundary in addition to the inbound check. Test it.

Parking lot rules apply. Commit with message "SP3 Session 4: outbox manager, four-tier policy, end-to-end pipeline" plus Co-Authored-By for Claude Opus 4.6 (1M context). Push to main.
```

---

## Session 5 — Pre-engagement intake automation

**Goal:** A consulting purchase via SP2's `notify_kyle` branch automatically triggers an intake form delivery within 60 seconds. The buyer fills out the form on `/intake/{token}`. Steward generates a markdown pre-call brief and emails it to Kyle.

**Prereqs:** Sessions 1-4 done. SP2 `notify_kyle` branch creates leads (it already does — see [crm.py:252](C:/CLAUDE/projects/Sidebar Code/Side Bar Code/stripe-delivery/api/crm.py#L252)).

**Autonomous tasks:**

1. `api/steward/intake.py`:
   - HMAC token generation with `STEWARD_INTAKE_HMAC_SECRET`
   - `send_intake_form(lead)` — creates `intake_forms` row, schedules `sp3-intake-form-link` email
   - Tier-specific form schemas (different fields for Foundation vs Implementation vs Modernization vs custom workflows)
2. `api/steward/brief.py`:
   - Markdown pre-call brief generator per spec Section 9
   - Includes lead history reconstructed from `lead_events`
3. Add intake routes to `api/admin.py` (or new `api/intake_routes.py`):
   - `GET /intake/{form_token}` renders an HTML form
   - `POST /intake/{form_token}` validates token, captures responses, generates brief, schedules emails
4. Hook into `crm.insert_lead` via an `after_insert` callback (or call Steward directly from `webhook.handle_checkout_completed` after lead insert) so intake auto-fires for `notify_kyle` purchases.
5. Add `intake_forms` table to `db.py` `_SCHEMA_SQL`.
6. Tests covering token generation, expiration, single-use, response capture, brief generation, and the `notify_kyle` integration path.
7. Commit + push.

**Paste-ready kickoff prompt:**
```
Work on SP3 Session 5. Sessions 1-4 done. Build pre-engagement intake automation per the playbook and spec Section 9. Tests must include token unguessability, expiration, single-use, and the notify_kyle integration. CHDB enforcement applies to intake form delivery. Commit with "SP3 Session 5: pre-engagement intake automation" + Co-Authored-By Claude Opus 4.6 (1M context). Push.
```

---

## Session 6 — Steward admin panel

**Goal:** `/admin/steward` is a full operational dashboard: pending Kyle approvals, pipeline by lifecycle state, scheduled emails, recent inbound, lead timelines, operational metrics. One-click approve/reject on the queue.

**Prereqs:** Sessions 1-5 done.

**Autonomous tasks:**

1. Extend `api/admin.py` with the routes from spec Section 10. Same HTTPBasic auth pattern as `/admin/sales`.
2. HTML rendering via the same f-string pattern used in `/admin/sales` (no new framework).
3. Approve action sends now via `outbox.send_now`. Reject action writes `lead_events` with reason and marks `scheduled_emails.status='cancelled'`.
4. Operational metrics card pulls from `scheduled_emails`, `lead_events`, `inbound_emails`.
5. Tests for every route + auth.
6. Commit + push.

**Paste-ready kickoff prompt:**
```
Work on SP3 Session 6. Sessions 1-5 done. Build the Steward admin panel per spec Section 10. Reuse the SP2 /admin/sales HTTPBasic auth pattern. One-click approve/reject for TIER_REVIEW queue items. Commit with "SP3 Session 6: Steward admin panel" + Co-Authored-By Claude Opus 4.6 (1M context). Push.
```

---

## Session 7 — Nurture sequences + onboarding drip + Aemon production rule pass

**Goal:** Cold leads enroll in the 90-day nurture sequence on insertion. Product purchases enroll in the onboarding drip on `zip_download` webhook. Every SP3 outbound template has been Aemon-reviewed and the verdicts logged in the parking lot.

**Prereqs:** Sessions 1-6 done.

**Autonomous tasks:**

1. `api/steward/sequences.py` — codify `NURTURE_COLD_LEAD` and `ONBOARDING_PRODUCT` from spec Section 8.
2. Enrollment hooks:
   - On lead insert with `source='web_inquiry'` or any cold-lead source, enroll in `NURTURE_COLD_LEAD`
   - On `zip_download` purchase webhook, enroll the buyer in `ONBOARDING_PRODUCT`
3. Cancel pending sequences when an inbound from the same lead is matched.
4. Aemon production rule pass: run Aemon's `review()` against every template_id in the registry, dump the verdicts to `parking_lot` for Kyle's evening sign-off.
5. Tests for enrollment, idempotency, cancellation, and the full Aemon pass output.
6. Commit + push.

**Paste-ready kickoff prompt:**
```
Work on SP3 Session 7. Sessions 1-6 done. Build nurture and onboarding sequence enrollment per spec Section 8. After enrollment is wired, run Aemon's review() against every SP3 template_id and write the verdicts to the parking lot for Kyle's evening sign-off. Commit with "SP3 Session 7: nurture sequences, onboarding drip, Aemon template pass" + Co-Authored-By Claude Opus 4.6 (1M context). Push.
```

---

## Session 8 — 24-hour soak, incident runbook addendum, production cutover

**Goal:** A 24-hour staging soak with seeded leads and inbound replies completes clean. The incident runbook gains four new Steward scenarios. `STEWARD_ENABLED` is flipped to `true` in production after Kyle approves the soak report.

**Prereqs:** Sessions 1-7 done.

**Autonomous tasks:**

1. Soak setup script: seed 5 fake leads across tiers, drop 5 fake inbound replies into the queue, let the cron tick run for 24 hours. At end of soak: zero double-sends, zero unhandled exceptions, complete `lead_events` audit log, Aemon verdict on every send.
2. Add Scenarios 9-12 to `_ops/INCIDENT_RUNBOOK.md` per spec Section 13.
3. Update `_ops/AGENT_PROTOCOLS.md` (per the Solo Launch consequence in [PRE Q1]) — Steward is configured to recognize Solo Launch as out-of-catalog and never quotes it.
4. Soak report saved to parking lot; Kyle reviews; flips `STEWARD_ENABLED=true` in Render production env.
5. Commit + push.

**Paste-ready kickoff prompt:**
```
Work on SP3 Session 8. Sessions 1-7 done. Run the 24-hour staging soak per spec Section 17 production cutover gates. Write the soak report to the parking lot. Add Scenarios 9-12 to _ops/INCIDENT_RUNBOOK.md. Update _ops/AGENT_PROTOCOLS.md per the Solo Launch consequence. Do not flip STEWARD_ENABLED in production — that's Kyle's manual step after he reads the soak report. Commit with "SP3 Session 8: soak, runbook addendum, prod cutover prep — SP3 complete" + Co-Authored-By Claude Opus 4.6 (1M context). Push.
```

---

## After Session 8: ongoing operational tasks

- Kyle flips `STEWARD_ENABLED=true` in Render production env after reviewing the soak report.
- Monitor the Steward admin panel daily for the first week.
- Collect Kyle's reject reasons for TIER_REVIEW drafts; feed them back into Aemon's rule set in a weekly evening session.
- Tune classification thresholds as real inbound traffic accumulates.
- Plan SP4 (Scout/Raven/Herald) once SP3 is stable.

---

## Rate limit and cadence notes

- Each SP3 day session is scoped to 3-4 hours of agent wall time, same as SP2.
- The 24-hour soak in Session 8 is wall time, not agent time — agent kicks it off and reports back.
- Do NOT run two day sessions in parallel. Finish one, commit, deploy staging, start the next.
- Kyle's evening work is parking-lot review, template copy refinement, and external service configuration (Postmark inbound, GoDaddy MX record, Cal.com event types if not already done in SP2).

---

*End of playbook. Version 1.0.*
