# Sidebar Code Steward Operationalized Spec
## Sub-Project 3 of 4: Inbound Triage, Lifecycle Automation, Aemon Review

**Date:** April 13, 2026
**Author:** Kyle Banfield + Claude
**Status:** Pending Kyle review
**Scope:** Stand up Steward as an automation layer on top of the SP2 leads/purchases/lead_events schema so that inbound email is triaged, drafted, legally reviewed, and queued for Kyle approval (or auto-sent within strict tiers); nurture and onboarding sequences run on schedule; and consulting intake is captured automatically.
**Approach:** New `api/steward/` subpackage inside the existing stripe-delivery FastAPI service; no long-running worker; inbound is HTTP, scheduled outbound is HTTP-triggered cron; Aemon review is serial and gates every customer-facing draft.

---

## Table of Contents

1. [Goal and Success Criteria](#1-goal-and-success-criteria)
2. [System Architecture](#2-system-architecture)
3. [Auto-Send Tier Policy](#3-auto-send-tier-policy)
4. [Aemon Review Path](#4-aemon-review-path)
5. [Schema Additions](#5-schema-additions)
6. [Inbound Pipeline](#6-inbound-pipeline)
7. [Lifecycle State Machine](#7-lifecycle-state-machine)
8. [Scheduled Outbound and Nurture Sequences](#8-scheduled-outbound-and-nurture-sequences)
9. [Pre-Engagement Intake Automation](#9-pre-engagement-intake-automation)
10. [Steward Admin Panel](#10-steward-admin-panel)
11. [Deployment, Cron, and Render Topology](#11-deployment-cron-and-render-topology)
12. [Security, Compliance, and the CHDB Separation Rule](#12-security-compliance-and-the-chdb-separation-rule)
13. [Observability, Failure Handling, and Idempotency](#13-observability-failure-handling-and-idempotency)
14. [Interfaces to Sub-Project 4](#14-interfaces-to-sub-project-4)
15. [Out of Scope](#15-out-of-scope)
16. [Work Sequence](#16-work-sequence)
17. [Review Gates and Quality Standards](#17-review-gates-and-quality-standards)
18. [Appendix A: Steward Subpackage Layout](#appendix-a-steward-subpackage-layout)
19. [Appendix B: Pre-Session Locks](#appendix-b-pre-session-locks)

---

## 1. Goal and Success Criteria

### Goal

Turn Steward from a static role description into a running automation layer that handles the full inbound and lifecycle side of the Sidebar Code business so Kyle stops being the single point of failure for routine customer communication. By the end of SP3:

- Every inbound email at `kyle@sidebarcode.com` is parsed, classified, drafted, Aemon-reviewed, and either auto-sent (within strict tiers) or queued for Kyle's one-click approval within 60 seconds of arrival.
- Every consulting/workflow lead written by SP2's `notify_kyle` branch automatically receives an intake form and (after response) a generated pre-call brief.
- Every product purchase enters an onboarding sequence (Day 1, 2, 7, 14, 30) without Kyle touching it.
- Cold leads enter a 90-day nurture drip that Steward runs and Kyle approves in batched evening passes.
- Kyle's daily inbox load drops from "37 unsorted emails" to "3 hot leads + 2 customer issues, each pre-prepped with full context."

### Decomposition Context

- **Sub-Project 1 (done):** Product Catalog Build-Out — source of all template content and `CATALOG_INDEX.yaml`.
- **Sub-Project 2 (done):** Stripe + Delivery — provides `purchases`, `leads`, `lead_events` schema that SP3 reads from and writes to.
- **Sub-Project 3 (this spec):** Steward operationalized — inbound triage, lifecycle automation, Aemon review, intake capture.
- **Sub-Project 4:** Scout/Raven/Herald — outbound prospecting, drip activation, social engagement; writes leads to the same tables Steward reads.

### Success Criteria

All must be true to call SP3 done:

1. A test inbound email sent to `kyle@sidebarcode.com` arrives via Postmark inbound, gets parsed, classified into one of the four send-tiers, drafted with the right template, Aemon-reviewed, and either auto-sent (TIER_AUTO) or written to the Steward queue (TIER_REVIEW), all within 60 seconds.
2. A consulting purchase via SP2's `notify_kyle` branch automatically triggers an intake form delivery within 60 seconds of the webhook firing, and (when the form is returned) generates a pre-call brief PDF that lands in Kyle's queue.
3. A product purchase via SP2's `zip_download` branch automatically enrolls the buyer in the onboarding drip (Day 1, 2, 7, 14, 30), with each scheduled send auto-sent or queued per its tier policy.
4. The four-tier auto-send policy is enforced by a single `send_tier_for(template_id)` function with comprehensive unit tests; no template ever bypasses it.
5. Aemon's review is serial: every TIER_AUTO send and every Steward draft entering Kyle's queue carries Aemon's verdict and annotations on the same screen Kyle approves from.
6. The Steward admin panel at `/admin/steward` shows: pending drafts (with Aemon notes), pipeline by lifecycle state, scheduled emails queue, recent inbound classifications, and an operational metrics card (drafts pending, draft-to-send latency, Aemon flag rate, classification confusion matrix).
7. A 24-hour soak run with seeded leads and inbound replies completes with zero double-sends, zero unhandled exceptions, complete `lead_events` audit trail, and Aemon verdict on every send.
8. The CHDB email separation rule is enforced in code: any attempt to read from or write to a `@chdblaw.com` address fails fast with a `ValueError`, with a unit test that asserts the failure mode.
9. The cron-triggered scheduler endpoint (`POST /admin/cron/steward-tick`) fires every minute, picks up due scheduled emails, runs them through the Aemon-then-Kyle pipeline, and never double-sends across restarts.
10. Steward's full surface is covered by tests; the SP2 test count baseline (84 tests as of 2026-04-13) does not regress; CI stays green.
11. Aemon's template review pass for all SP3 outbound templates is logged in the parking lot before SP3 ships to production.
12. Kyle can stop Steward (via a feature flag `STEWARD_ENABLED=false` in Render env) and restart it without losing scheduled work or duplicating sends.

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Worker model | **No long-running worker.** Inbound is HTTP, outbound is HTTP-triggered cron, both inside the existing `sidebarcode-api` web service. | Render persistent disks are per-service. SP2 hard-learned this. A Background Worker on a separate disk cannot read SQLite and a shared-disk SQLite invites concurrent-writer corruption. The web service already owns the DB; Steward extends it. |
| Auto-send policy | **Four tiers** (TIER_AUTO, TIER_REVIEW, TIER_ESCALATE, TIER_SILENT). | Strict zero-auto-send turns Kyle into the bottleneck for trivial work (FAQ, ack). Tiering puts the human in the loop where judgment matters. |
| Aemon review path | **Serial: Aemon-then-Kyle.** Aemon reviews every draft before it reaches Kyle's queue OR before TIER_AUTO send. | One screen, one decision, full context. Avoids the "wait, I already approved this" loop that parallel review creates. |
| Inbox scope | **`@sidebarcode.com` only.** `@chdblaw.com` is hard-prohibited at the code level. | Client privilege, corporate-veil separation between CHDB Law, LLP and Banfield Consulting, LLC. Non-negotiable. Enforced by code, not policy. |
| Email parser library | Postmark inbound webhook payload (already-parsed JSON); fall back to `email.message_from_string` for the raw body when needed. | Postmark inbound delivers structured JSON; we never need to parse raw RFC 822 ourselves. |
| Template engine | **Jinja2** for body templates; Postmark templates for Postmark-managed copy. | Jinja2 for anything Steward composes locally (Aemon prompts, intake forms); Postmark templates for transactional sends so Kyle can edit copy in the dashboard without touching code. |
| Classification | **Rule-based first, LLM fallback for ambiguous.** | Rule-based catches the obvious 80% deterministically. LLM-assist (single API call to Anthropic with a small prompt) handles the 20% that need judgment. Cost-controlled, debuggable. |
| Aemon transport | **Synchronous HTTP call** to a local Aemon endpoint (`POST /admin/aemon/review`) within the same web service, OR an in-process function call. Defaults to in-process. | Same service, no IPC overhead, no additional infrastructure. Aemon's review logic is a Python function; HTTP wrapping is only added if we later separate Aemon. |
| Scheduled email storage | **SQLite `scheduled_emails` table** with `due_at`, `status`, `dedupe_key`. | Same DB as everything else. Idempotent via `dedupe_key`. |
| Cron schedule | `* * * * *` (every minute) for the Steward tick. Daily aggregation tasks at 09:00 Phoenix. | One-minute tick keeps draft-to-send latency low; daily at 09:00 matches Kyle's morning rhythm. |
| Onboarding drip cadence | **Day 1, 2, 7, 14, 30 from purchase.** | Standard SaaS onboarding curve, validated by years of industry data. Adjustable per-tier in catalog. |
| Cold lead nurture | **90 days, 6 touches.** Day 0, 3, 10, 30, 60, 90. | Long enough to outlast typical buying cycles; short enough that an unresponsive lead is genuinely cold by Day 90. |
| Pre-engagement intake | **Auto-sent within 5 minutes of consulting purchase.** Form is a plain web page on `sidebarcode.com/intake/{lead_id}` with HMAC token. | Web form is universally accessible, no third-party dependency, no app install. HMAC token prevents enumeration attacks. |
| Pre-call brief format | **Markdown rendered to PDF via WeasyPrint** (or skip PDF and email markdown). | Markdown is the canonical format Kyle reads in. PDF is optional polish. |
| Feature flag | `STEWARD_ENABLED` env var, default `true` in staging, **`false` in production until Kyle flips it.** | Lets Kyle ship code to prod without enabling automation until he's reviewed the staging soak. |

---

## 2. System Architecture

### High-level flow — inbound

```
Buyer/lead emails kyle@sidebarcode.com
       |
       v
Postmark Inbound forwards JSON to /api/inbound
       |
       v
sidebarcode-api (FastAPI web service)
  /api/inbound:
    1. Validate X-Postmark-Inbound-Token shared secret
    2. Parse Postmark JSON payload
    3. Reject if From/To touches @chdblaw.com (hard fail)
    4. Insert raw row in inbound_emails table
    5. Match to existing lead by In-Reply-To OR by buyer_email
    6. Classify: rule-based first, LLM fallback for ambiguous
    7. Determine send-tier from classification
    8. Render draft via templates.render(template_id, context)
    9. Aemon.review(draft) -> verdict + annotations
   10. If TIER_AUTO and Aemon clears: send via Postmark, write lead_events
       If TIER_REVIEW: write to scheduled_emails (status=awaiting_kyle), surface in queue
       If TIER_ESCALATE: write lead_events('escalation_required'), Postmark Kyle a brief
       If TIER_SILENT: write lead_events('filed_silent'), no send
   11. Return 200 to Postmark
```

### High-level flow — scheduled outbound

```
Render Cron Service (sidebarcode-steward-tick, every minute)
       |
       v
HTTP POST /admin/cron/steward-tick (CRON_SECRET Bearer)
       |
       v
sidebarcode-api:
  scheduler.tick():
    1. SELECT * FROM scheduled_emails WHERE due_at <= now() AND status='pending'
    2. For each: lock row (UPDATE status='processing'), render, Aemon review
    3. If TIER_AUTO and Aemon clears: send, status='sent', write lead_events
       If TIER_REVIEW: status='awaiting_kyle', surface in queue
    4. On exception: status='failed', record_delivery_failure, alert Kyle
    5. Return summary to cron service
```

### Components

| Component | Tech | New or extends? | Path |
|---|---|---|---|
| Steward subpackage | Python | new | `stripe-delivery/api/steward/` |
| Inbound webhook route | FastAPI | new | `stripe-delivery/api/inbound.py` (top-level router, mounted in main.py) |
| Steward admin panel | FastAPI HTML | extends `admin.py` | `stripe-delivery/api/admin.py` (new `/admin/steward/*` routes) |
| Steward cron tick endpoint | FastAPI | extends `admin.py` | `stripe-delivery/api/admin.py` (new `/admin/cron/steward-tick`) |
| Aemon review module | Python | new | `stripe-delivery/api/steward/aemon.py` |
| Lifecycle state machine | Python | new | `stripe-delivery/api/steward/state.py` |
| Inbound classifier | Python | new | `stripe-delivery/api/steward/classifier.py` |
| Template renderer | Python (Jinja2) | new | `stripe-delivery/api/steward/templates.py` |
| Outbox manager | Python | new | `stripe-delivery/api/steward/outbox.py` |
| Scheduler | Python | new | `stripe-delivery/api/steward/scheduler.py` |
| Intake form generator | Python | new | `stripe-delivery/api/steward/intake.py` |
| Pre-call brief generator | Python | new | `stripe-delivery/api/steward/brief.py` |
| Schema additions | SQL | extends `db.py` | `stripe-delivery/api/db.py` (`_SCHEMA_SQL`) |
| Postmark template aliases | Postmark dashboard + sync script | extends `sync_postmark_templates.py` | `stripe-delivery/scripts/sync_postmark_templates.py` |
| Render Cron services | render.yaml | extends | `render.yaml` (new cron entries) |

### Data flow contracts

- **Postmark Inbound → /api/inbound:** JSON body matching Postmark's documented inbound schema (`From`, `FromName`, `To`, `Subject`, `TextBody`, `HtmlBody`, `MessageID`, `Headers[]`, `Attachments[]`). Header `X-Postmark-Inbound-Token` carries the shared secret.
- **Steward → crm.py:** all reads and writes to `leads`, `lead_events`, and `purchases` go through the existing `api.crm` helpers. Steward never writes raw SQL to those tables.
- **Steward → scheduled_emails:** Steward owns this table fully. Scheduler reads and writes it.
- **Aemon → Steward:** in-process function call returning a `AemonVerdict` dataclass with `cleared: bool`, `severity: str`, `annotations: list[str]`, `suggested_edits: Optional[str]`.
- **Cron → web service:** `POST /admin/cron/steward-tick` with `Authorization: Bearer {CRON_SECRET}`. Returns `{processed: int, sent: int, queued: int, failed: int}`.

---

## 3. Auto-Send Tier Policy

The single source of truth for whether a Steward draft can auto-send is the `send_tier_for(template_id, classification)` function in `api/steward/state.py`. It returns one of four constants. Every send code path consults this function; no template bypasses it.

### TIER_AUTO

Drafts that auto-send after Aemon clears them. No Kyle approval required.

**Eligible templates:**
- FAQ replies (`sp3-faq-reply`)
- Acknowledgment of intake form receipt (`sp3-intake-ack`)
- Unsubscribe confirmation (`sp3-unsub-confirm`)
- Onboarding Day 1 welcome (`sp3-onboarding-day-1`) — deterministic copy, low risk
- Onboarding Day 2 quickstart reminder (`sp3-onboarding-day-2`)
- Refund-confirmed receipt (`sp3-refund-confirmed`)

**Why these:** all are deterministic, content is reviewed and Aemon-cleared at template-creation time, and the value of speed (instant response) outweighs the value of human review on every send. Aemon still runs per-send to catch substitution attacks, content drift, and merge-var injection.

### TIER_REVIEW

Drafts that go to Kyle's queue with Aemon's annotations attached. Kyle approves with one click.

**Eligible templates:**
- Pricing inquiry response (`sp3-pricing-inquiry-reply`)
- Scheduling proposal (`sp3-scheduling-proposal`)
- Cold lead nurture (Day 3, 10, 30, 60, 90)
- Re-engagement after silence
- Onboarding Day 7, 14, 30 (more substantive content)
- Refund request acknowledgment

### TIER_ESCALATE

No auto-draft sends. Steward composes a brief for Kyle and notifies him. Kyle handles personally.

**Eligible classifications:**
- Hot lead with buying signal ($X+ consulting tier interest)
- Customer complaint
- Legal/compliance question that touches engagement scope
- Anything Aemon flags with severity = "high" regardless of original tier

### TIER_SILENT

No response sent, ever. Logged for audit only.

**Eligible classifications:**
- Spam (deterministic match against block lists)
- List-bombing detection (5+ inbound from same domain in 60s)
- Auto-replies and out-of-office bounces
- Mailer-daemon non-deliveries
- Marketing solicitations to `kyle@sidebarcode.com` from cold senders

### Tier resolution rules

1. Classification determines the *initial* tier.
2. Aemon's verdict can **escalate** (move from AUTO to REVIEW, or from REVIEW to ESCALATE) but never **de-escalate** (REVIEW cannot become AUTO).
3. A template explicitly marked `force_review=true` in its config always lands in TIER_REVIEW regardless of classification.
4. Kyle can override per-template via the admin panel; overrides are logged and persist until manually cleared.

### Tests required

- `test_send_tier_for_known_templates` — every template in the registry maps to exactly one tier
- `test_aemon_can_escalate_but_not_deescalate` — verdict severity high moves AUTO->REVIEW, REVIEW->ESCALATE
- `test_force_review_overrides_auto`
- `test_unknown_template_defaults_to_escalate` — fail-safe default
- `test_classifier_spam_routes_to_silent`

---

## 4. Aemon Review Path

### Why serial Aemon-then-Kyle

Two alternatives were considered and rejected:

- **Aemon-as-final-gate (parallel):** Kyle approves first, Aemon does last-pass scan, holds and re-notifies on flag. Rejected because it creates "wait, I already approved this" friction and double-handling.
- **Aemon-only (no Kyle queue):** Aemon clears, send. Rejected because Aemon catches legal exposure, not voice or judgment, and Kyle has explicit policy authority over external content.

The serial path puts Aemon first so Kyle sees one screen with one decision and full context.

### What Aemon checks

1. **Disclaimer presence:** every customer-facing send carries the standard Sidebar Code disclaimer block per CLAUDE.md governing principle #2.
2. **Practice-area neutrality:** no claim of expertise in any legal practice area (per governing principle #1).
3. **Pricing accuracy:** any quoted price matches the locked tier prices in CATALOG_INDEX.yaml; flags any deviation.
4. **Solo Launch Package leakage:** Solo Launch is post-MVP per the SP2 swap-in audit; Aemon flags any draft that quotes it.
5. **CHDB separation:** any reference to CHDB Law, LLP, kyle@chdblaw.com, or "the law firm where I work" is a high-severity flag.
6. **Em-dash detection:** scans for em dashes, flags as low-severity for cleanup.
7. **Compliance language:** ToS and refund language matches terms.html version hash.
8. **Tone vs. tier:** flags drafts that don't match the formality level expected for the recipient's lifecycle stage (e.g., overly casual to a $30K consulting prospect).
9. **Merge variable injection:** flags any unrendered `{{ }}` in the body.
10. **Substitution attacks:** flags any URL or email address that doesn't match the sender's domain or the buyer's known data.

### Aemon's verdict

```python
@dataclass
class AemonVerdict:
    cleared: bool                 # True = safe to proceed
    severity: str                 # "none", "low", "medium", "high"
    annotations: list[str]        # human-readable findings
    suggested_edits: Optional[str]  # markdown diff if Aemon proposes changes
    rule_hits: dict[str, bool]    # which checks fired (for debugging)
    reviewed_at: str              # ISO timestamp
    aemon_version: str            # rule set version, for audit
```

### Aemon failure modes

- **Aemon raises an exception:** treat as "not cleared, severity=high"; queue draft to TIER_ESCALATE; log `delivery_failures` with the traceback.
- **Aemon is disabled (`STEWARD_AEMON_ENABLED=false`):** Steward refuses to auto-send anything; all drafts go to TIER_REVIEW with an annotation `"Aemon disabled — manual review required"`. This is the safe-failure mode.

### Tests required

- `test_aemon_clears_clean_draft`
- `test_aemon_flags_em_dash`
- `test_aemon_flags_chdb_reference` (HIGH severity)
- `test_aemon_flags_practice_area_claim` (HIGH severity)
- `test_aemon_flags_unrendered_merge_var` (HIGH severity)
- `test_aemon_flags_solo_launch_quote`
- `test_aemon_disabled_forces_review_tier`
- `test_aemon_exception_routes_to_escalate`

---

## 5. Schema Additions

All additions go into `stripe-delivery/api/db.py` `_SCHEMA_SQL` block. Backward-compatible with SP2 (CREATE TABLE IF NOT EXISTS).

```sql
-- SP3 Session 1: inbound debug log (raw Postmark payloads for audit)
CREATE TABLE IF NOT EXISTS inbound_emails (
    inbound_id        TEXT PRIMARY KEY,
    postmark_message_id TEXT NOT NULL,
    from_email        TEXT NOT NULL,
    from_name         TEXT,
    to_email          TEXT NOT NULL,
    subject           TEXT,
    text_body         TEXT,
    html_body         TEXT,
    in_reply_to       TEXT,
    raw_payload_json  TEXT NOT NULL,
    matched_lead_id   TEXT,
    classification    TEXT,
    send_tier         TEXT,
    received_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inbound_postmark_id
    ON inbound_emails(postmark_message_id);
CREATE INDEX IF NOT EXISTS idx_inbound_in_reply_to
    ON inbound_emails(in_reply_to);
CREATE INDEX IF NOT EXISTS idx_inbound_matched_lead
    ON inbound_emails(matched_lead_id);
CREATE INDEX IF NOT EXISTS idx_inbound_received_at
    ON inbound_emails(received_at);

-- SP3 Session 2: scheduled outbound queue (Steward + nurture + onboarding)
CREATE TABLE IF NOT EXISTS scheduled_emails (
    scheduled_id      TEXT PRIMARY KEY,
    lead_id           TEXT,
    purchase_id       TEXT,
    template_id       TEXT NOT NULL,
    template_context  TEXT NOT NULL,  -- JSON merge vars
    send_tier         TEXT NOT NULL,
    dedupe_key        TEXT NOT NULL UNIQUE,
    due_at            TEXT NOT NULL,
    status            TEXT NOT NULL,  -- pending, processing, awaiting_kyle, sent, failed, cancelled, suppressed
    aemon_verdict     TEXT,           -- JSON
    sent_at           TEXT,
    failure_reason    TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scheduled_due_at_status
    ON scheduled_emails(status, due_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_lead
    ON scheduled_emails(lead_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_purchase
    ON scheduled_emails(purchase_id);

-- SP3 Session 5: pre-engagement intake forms
CREATE TABLE IF NOT EXISTS intake_forms (
    intake_id         TEXT PRIMARY KEY,
    lead_id           TEXT NOT NULL,
    purchase_id       TEXT,
    tier_id           TEXT NOT NULL,
    form_token        TEXT NOT NULL UNIQUE,  -- HMAC, used in /intake/{token} URL
    form_schema_json  TEXT NOT NULL,         -- which fields per tier
    response_json     TEXT,                  -- captured answers, NULL until submitted
    pre_call_brief_md TEXT,                  -- generated after submission
    sent_at           TEXT NOT NULL,
    submitted_at      TEXT,
    expires_at        TEXT NOT NULL,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_lead ON intake_forms(lead_id);
CREATE INDEX IF NOT EXISTS idx_intake_token ON intake_forms(form_token);
```

The `lead_events` table already exists in SP2 with a flexible `event_type` and `event_data` JSON column. SP3 uses the following new event types without schema changes:

- `inbound_received` — raw inbound mapped to a lead
- `inbound_classified` — classification + send_tier recorded
- `draft_created` — Steward composed a draft
- `aemon_reviewed` — Aemon verdict attached
- `email_sent` — outbound delivered
- `email_queued_for_kyle` — TIER_REVIEW queued in admin panel
- `kyle_approved` — Kyle clicked approve in admin
- `kyle_rejected` — Kyle clicked reject in admin (with reason)
- `escalation_required` — TIER_ESCALATE triggered
- `filed_silent` — TIER_SILENT no-op
- `intake_sent` — intake form delivered
- `intake_received` — intake form submitted
- `pre_call_brief_generated` — brief PDF/markdown generated
- `nurture_started` — lead enrolled in nurture sequence
- `nurture_completed` — lead reached end of sequence
- `onboarding_started` — purchase enrolled in onboarding drip
- `onboarding_completed` — purchase reached end of drip

---

## 6. Inbound Pipeline

### Postmark Inbound configuration

Postmark configures inbound by assigning a unique inbound address per server (e.g., `5d3a...@inbound.postmarkapp.com`). To route `kyle@sidebarcode.com` through it:

1. Create an MX record at GoDaddy for `sidebarcode.com` pointing to `inbound.postmarkapp.com` priority 10. **Kyle does this in DNS before Session 3 can be tested live.**
2. In Postmark dashboard → Server → Settings → Inbound → set Webhook URL to `https://sidebarcode-api.onrender.com/api/inbound`.
3. Set Inbound Domain to `sidebarcode.com`.
4. Configure shared secret: Postmark calls this an "Inbound Webhook URL token." Kyle generates a 32-char random string, sets it in Render env as `POSTMARK_INBOUND_SECRET`, and tells Postmark to send it as the `X-Postmark-Inbound-Token` header.

### `/api/inbound` route

```python
@router.post("/api/inbound")
async def postmark_inbound(request: Request) -> dict:
    _verify_postmark_secret(request)
    payload = await request.json()
    _enforce_chdb_separation(payload)  # raises 422 if @chdblaw.com touched
    inbound_id = inbound_emails.insert(payload)
    if not steward_enabled():
        return {"status": "logged", "inbound_id": inbound_id}
    matched_lead = match_to_lead(payload)
    classification = classifier.classify(payload, matched_lead)
    tier = state.send_tier_for(classification.template_id, classification)
    draft = templates.render(classification.template_id, payload, matched_lead)
    verdict = aemon.review(draft, classification)
    final_tier = state.apply_verdict(tier, verdict)
    if final_tier == "TIER_AUTO" and verdict.cleared:
        outbox.send_now(draft, verdict)
    elif final_tier == "TIER_REVIEW":
        outbox.queue_for_kyle(draft, verdict)
    elif final_tier == "TIER_ESCALATE":
        outbox.escalate(draft, verdict, matched_lead)
    else:  # TIER_SILENT
        outbox.file_silent(payload, classification)
    return {"status": "processed", "inbound_id": inbound_id, "tier": final_tier}
```

### Idempotency

Postmark may deliver the same inbound twice on retry. Steward dedupes on `postmark_message_id`:

- `inbound_emails.postmark_message_id` is indexed; insert short-circuits if the message_id is already present and returns the existing `inbound_id`.
- Downstream processing (classification, draft, send) is idempotent on `inbound_id` — the scheduled email's `dedupe_key` includes the `inbound_id` for any reply chain.

### CHDB separation enforcement

```python
def _enforce_chdb_separation(payload: dict) -> None:
    """Hard fail if any address in From/To/Cc/Bcc matches chdblaw.com.

    This is a non-negotiable architectural constraint per Kyle's standing rule.
    SP3 must NEVER process email touching the law firm inbox.
    """
    fields = ("From", "FromFull", "To", "ToFull", "Cc", "CcFull", "Bcc", "BccFull")
    for f in fields:
        value = str(payload.get(f, ""))
        if "chdblaw.com" in value.lower():
            raise HTTPException(
                status_code=422,
                detail="CHDB inbox is not in scope for Sidebar Code. "
                       "Inbound rejected to enforce client confidentiality.",
            )
```

This enforcement runs *before* the row is inserted into `inbound_emails`. The CHDB rule has zero exceptions and is enforced by code, not policy.

### Tests required

- `test_inbound_rejects_missing_token`
- `test_inbound_rejects_invalid_token`
- `test_inbound_accepts_valid_token`
- `test_inbound_rejects_chdb_in_from`
- `test_inbound_rejects_chdb_in_to`
- `test_inbound_rejects_chdb_in_cc`
- `test_inbound_rejects_chdb_anywhere_case_insensitive`
- `test_inbound_dedupes_on_message_id`
- `test_inbound_writes_row_when_steward_disabled`
- `test_inbound_full_pipeline_classifies_and_routes`
- `test_inbound_full_pipeline_aemon_escalation`

---

## 7. Lifecycle State Machine

State machine over the existing `leads.status` column. New status values added:

```
new -> contacted -> qualified -> negotiating -> closed_won
                              \-> nurture_active -> nurture_completed -> closed_lost
                                                  \-> closed_lost
                              \-> closed_lost
```

Plus dedicated onboarding states for purchases:

```
purchased -> onboarding_active -> onboarding_completed -> active
                              \-> churned
```

### Transition rules

Codified in `api/steward/state.py`:

```python
LEGAL_TRANSITIONS = {
    "new": {"contacted", "closed_lost"},
    "contacted": {"qualified", "nurture_active", "closed_lost"},
    "qualified": {"negotiating", "nurture_active", "closed_won", "closed_lost"},
    "negotiating": {"closed_won", "closed_lost"},
    "nurture_active": {"qualified", "nurture_completed", "closed_lost"},
    "nurture_completed": {"closed_lost", "qualified"},
    "closed_won": set(),
    "closed_lost": {"qualified"},  # re-engagement is allowed
    "purchased": {"onboarding_active"},
    "onboarding_active": {"onboarding_completed", "churned"},
    "onboarding_completed": {"active", "churned"},
    "active": {"churned"},
    "churned": {"qualified"},  # winback allowed
}
```

Every state change writes a `lead_events` row with `event_type='status_changed'` and `event_data={"from": old, "to": new, "reason": reason}`.

Illegal transitions raise `IllegalStateTransition` and are NEVER silently coerced.

### Tests required

- `test_legal_transitions_round_trip` — every legal transition succeeds
- `test_illegal_transitions_raise` — every illegal transition raises
- `test_status_change_writes_lead_event`
- `test_terminal_states_have_no_outgoing` — closed_won and others are terminal except for documented winback paths

---

## 8. Scheduled Outbound and Nurture Sequences

### Scheduler tick

Every minute, Render Cron POSTs `/admin/cron/steward-tick`. Handler runs:

```python
def steward_tick() -> dict:
    now = datetime.now(timezone.utc)
    due = scheduled_emails.fetch_due(now, limit=50)
    metrics = {"processed": 0, "sent": 0, "queued": 0, "failed": 0, "skipped": 0}
    for row in due:
        try:
            scheduled_emails.lock(row.scheduled_id)  # status=processing
            draft = templates.render(row.template_id, row.context())
            verdict = aemon.review(draft)
            final_tier = state.apply_verdict(row.send_tier, verdict)
            if final_tier == "TIER_AUTO" and verdict.cleared:
                outbox.send_now(draft, verdict)
                scheduled_emails.mark_sent(row.scheduled_id, verdict)
                metrics["sent"] += 1
            elif final_tier == "TIER_REVIEW":
                scheduled_emails.mark_awaiting_kyle(row.scheduled_id, verdict)
                metrics["queued"] += 1
            elif final_tier == "TIER_ESCALATE":
                scheduled_emails.mark_failed(row.scheduled_id, "escalated to Kyle")
                outbox.escalate(draft, verdict, row.lead_id)
                metrics["failed"] += 1
        except Exception as exc:
            scheduled_emails.mark_failed(row.scheduled_id, str(exc))
            metrics["failed"] += 1
        metrics["processed"] += 1
    return metrics
```

### Nurture sequences

Defined in `api/steward/sequences.py`:

```python
NURTURE_COLD_LEAD = [
    NurtureStep(day_offset=0,  template_id="sp3-nurture-day-0",  send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=3,  template_id="sp3-nurture-day-3",  send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=10, template_id="sp3-nurture-day-10", send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=30, template_id="sp3-nurture-day-30", send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=60, template_id="sp3-nurture-day-60", send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=90, template_id="sp3-nurture-day-90", send_tier="TIER_REVIEW"),
]

ONBOARDING_PRODUCT = [
    NurtureStep(day_offset=1,  template_id="sp3-onboarding-day-1",  send_tier="TIER_AUTO"),
    NurtureStep(day_offset=2,  template_id="sp3-onboarding-day-2",  send_tier="TIER_AUTO"),
    NurtureStep(day_offset=7,  template_id="sp3-onboarding-day-7",  send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=14, template_id="sp3-onboarding-day-14", send_tier="TIER_REVIEW"),
    NurtureStep(day_offset=30, template_id="sp3-onboarding-day-30", send_tier="TIER_REVIEW"),
]
```

Enrollment writes one `scheduled_emails` row per step with `due_at = enrollment_at + step.day_offset` and `dedupe_key = f"{sequence_name}:{lead_id}:{step.template_id}"`.

Re-running enrollment is idempotent because of the unique `dedupe_key`.

### Cancellation rules

A reply from the buyer cancels remaining nurture steps for that lead automatically (engagement detected → no point continuing the cold drip). Implementation: when an inbound is matched to a lead, mark all `scheduled_emails` rows for that lead with `status='cancelled'` where status is currently `pending`.

### Tests required

- `test_enroll_cold_lead_writes_six_scheduled_rows`
- `test_enroll_is_idempotent_on_dedupe_key`
- `test_inbound_cancels_pending_nurture_steps_for_lead`
- `test_steward_tick_processes_due_rows_only`
- `test_steward_tick_skips_locked_rows`
- `test_onboarding_day_1_auto_sends_after_aemon_clear`
- `test_onboarding_day_7_routes_to_review`

---

## 9. Pre-Engagement Intake Automation

### Trigger

When SP2's `notify_kyle` branch creates a lead row, an `after_lead_inserted` hook (added in `crm.insert_lead`) calls `intake.send_intake_form(lead)`.

### Intake form delivery

1. Generate HMAC token: `form_token = hmac.new(SECRET, lead_id.encode(), 'sha256').hexdigest()[:32]`.
2. Insert `intake_forms` row with `form_token`, schema for the tier, `expires_at = now + 30 days`.
3. Schedule a `sp3-intake-form-link` email (TIER_AUTO) with merge var `intake_url = f"{SITE_BASE_URL}/intake/{form_token}"`.

### Intake form web page

`GET /intake/{form_token}`:
- Validates token, looks up `intake_forms` row, fails if expired or already submitted.
- Renders a simple HTML form with the tier-specific schema (firm name, practice areas, current AI use, primary pain point, decision-maker contact, target start date, etc.).

`POST /intake/{form_token}`:
- Validates token, captures responses into `intake_forms.response_json`, sets `submitted_at`.
- Triggers `brief.generate_pre_call_brief(intake_form)` which renders a markdown brief.
- Schedules a `sp3-intake-ack` email to the buyer (TIER_AUTO) and a `sp3-kyle-pre-call-brief` email to Kyle (also TIER_AUTO) with the brief inline.

### Pre-call brief format

Markdown, structured:

```markdown
# Pre-Call Brief: {{ buyer_firm }} — {{ tier_name }}

**Lead:** {{ buyer_name }} <{{ buyer_email }}>
**Tier:** {{ tier_name }} — ${{ amount }}
**Submitted:** {{ submitted_at }}
**Cal.com event:** {{ scheduling_link }}

## Firm snapshot
- Firm: {{ buyer_firm }}
- Practice areas: {{ practice_areas }}
- Size: {{ firm_size }}
- Current AI use: {{ current_ai_use }}

## Primary pain point
{{ primary_pain_point }}

## Decision context
- Decision-maker: {{ decision_maker }}
- Target start date: {{ target_start_date }}
- Budget signaled: {{ budget }}

## Recommended approach for this call
{{ tier_specific_talking_points }}

## Aemon-flagged concerns
{{ aemon_concerns_if_any }}

## Lead history
{{ lead_event_timeline }}
```

### Tests required

- `test_intake_form_token_is_unguessable`
- `test_intake_form_expired_returns_410`
- `test_intake_form_already_submitted_returns_409`
- `test_intake_post_writes_response_and_generates_brief`
- `test_pre_call_brief_includes_required_fields`

---

## 10. Steward Admin Panel

New routes added to `api/admin.py`:

- `GET /admin/steward` — landing page with the operational metrics card and links to sub-pages
- `GET /admin/steward/queue` — pending Kyle approvals (TIER_REVIEW drafts), with Aemon notes inline
- `POST /admin/steward/queue/{scheduled_id}/approve` — one-click approve, sends now
- `POST /admin/steward/queue/{scheduled_id}/reject` — reject with reason, writes lead_event
- `GET /admin/steward/pipeline` — leads grouped by lifecycle state
- `GET /admin/steward/scheduled` — upcoming scheduled emails
- `GET /admin/steward/inbound` — recent inbound emails with classification
- `GET /admin/steward/lead/{lead_id}` — full timeline reconstructed from lead_events
- `GET /admin/steward/metrics` — JSON endpoint for the operational metrics card

### Operational metrics

- **Drafts pending Kyle approval:** count where `status='awaiting_kyle'`
- **Draft-to-send latency:** median time from `inbound_received` to `email_sent` over last 7 days
- **Aemon flag rate:** % of drafts where Aemon severity != "none" over last 7 days
- **Classification confusion matrix:** Kyle's reject reasons grouped by initial classification (manually labeled by Kyle on reject)
- **Onboarding completion:** % of purchases that reach `onboarding_completed`
- **Nurture conversion:** % of nurture-active leads that reach `qualified` or `closed_won`
- **TIER_AUTO kill switch trigger rate:** count of times Aemon escalated AUTO to REVIEW

These are operational metrics for debugging Steward, not business metrics for measuring revenue. BI is out of scope per the design call (deferred to Citadel).

---

## 11. Deployment, Cron, and Render Topology

### Services to add to render.yaml

All declared upfront in Session 1 to avoid the SP2 mid-build Blueprint re-apply pain.

```yaml
  - type: cron
    name: sidebarcode-steward-tick
    runtime: python
    rootDir: stripe-delivery
    plan: starter
    buildCommand: pip install -r requirements.txt
    schedule: "* * * * *"  # every minute
    startCommand: python scripts/trigger_steward_tick.py
    envVars:
      - key: PYTHON_VERSION
        value: "3.12"
      - key: SP2_API_URL
        value: https://sidebarcode-api.onrender.com
      - key: CRON_SECRET
        fromService:
          type: web
          name: sidebarcode-api
          envVarKey: CRON_SECRET

  - type: cron
    name: sidebarcode-steward-nurture-enroll
    runtime: python
    rootDir: stripe-delivery
    plan: starter
    buildCommand: pip install -r requirements.txt
    schedule: "0 16 * * *"  # 09:00 America/Phoenix == 16:00 UTC (no DST)
    startCommand: python scripts/trigger_steward_nurture_sweep.py
    envVars:
      - key: PYTHON_VERSION
        value: "3.12"
      - key: SP2_API_URL
        value: https://sidebarcode-api.onrender.com
      - key: CRON_SECRET
        fromService:
          type: web
          name: sidebarcode-api
          envVarKey: CRON_SECRET
```

The `trigger_*.py` scripts are minimal shells: read `SP2_API_URL` and `CRON_SECRET`, POST to the corresponding `/admin/cron/*` endpoint, exit with the response status code.

### New env vars on the web service

- `STEWARD_ENABLED` (default `true` in staging, **`false` in production until manually flipped**)
- `STEWARD_AEMON_ENABLED` (default `true`)
- `POSTMARK_INBOUND_SECRET` (sync: false)
- `STEWARD_INTAKE_HMAC_SECRET` (sync: false)
- `ANTHROPIC_API_KEY` (sync: false, only if classifier LLM fallback is enabled)

### DNS changes (Kyle does these manually before Session 3)

- Add MX record at GoDaddy: `sidebarcode.com` → `inbound.postmarkapp.com` priority 10
- Verify the existing SPF/DKIM records don't need updating (they shouldn't — inbound is a separate path from outbound)

---

## 12. Security, Compliance, and the CHDB Separation Rule

### CHDB separation (non-negotiable)

The single most important architectural rule in SP3:

> **Steward must never read from, write to, or process any email touching `@chdblaw.com` (or any CHDB Law inbox).**

Enforced by:

1. **Inbound rejection:** `/api/inbound` calls `_enforce_chdb_separation(payload)` BEFORE the row is inserted. Any address (From, To, Cc, Bcc) matching `chdblaw.com` (case-insensitive) returns 422.
2. **Outbound rejection:** `outbox.send_now()` calls `_enforce_chdb_separation_outbound(to_address)` BEFORE the Postmark call. Any send to `@chdblaw.com` raises `ValueError`.
3. **Lead enforcement:** `crm.insert_lead` rejects any `buyer_email` matching `@chdblaw.com` (added in SP3 as a hardening pass on the existing helper).
4. **Test coverage:** at least 4 unit tests (one per enforcement point) with the assertion that the function raises.
5. **Aemon check:** Aemon flags any draft body referencing CHDB Law, LLP, kyle@chdblaw.com, or "the law firm where I work" as HIGH severity.

This rule is enforced in code, not policy. There is no override flag. If Kyle ever needs to revisit this, it requires a code change with a new spec, not a config toggle.

### Postmark inbound shared secret

Postmark's inbound webhook supports a `?` query param or a custom header for shared-secret validation. Kyle generates a 32-character random string (`openssl rand -hex 16`), sets it in Render env as `POSTMARK_INBOUND_SECRET`, and configures Postmark to send it as `X-Postmark-Inbound-Token`.

`/api/inbound` validates with `secrets.compare_digest()` — never `==`. Failure returns 401.

### HMAC for intake form tokens

```python
form_token = hmac.new(
    STEWARD_INTAKE_HMAC_SECRET.encode(),
    f"{lead_id}:{tier_id}:{datetime.now().isoformat()}".encode(),
    hashlib.sha256,
).hexdigest()[:32]
```

Tokens are unguessable, scoped to a single lead, expire in 30 days, single-use (cannot be re-submitted).

### PII handling

- Inbound emails are stored full-fidelity in `inbound_emails.raw_payload_json` for audit/debugging.
- Retention: 90 days, then a housekeeping cron deletes rows older than the cutoff.
- The `lead_events` table has unbounded retention (it's the audit trail).
- Pre-call briefs contain firm info; treated as confidential, never logged in plain text.

### Audit trail

Every Steward action writes a `lead_events` row. The full lifecycle of any lead is reconstructable from this log. This is the audit defense for "Steward sent something I didn't expect."

---

## 13. Observability, Failure Handling, and Idempotency

### Idempotency

All Steward writes are idempotent. Specifically:

- `inbound_emails` deduped on `postmark_message_id`
- `scheduled_emails` deduped on `dedupe_key` (UNIQUE constraint)
- `intake_forms` deduped on `form_token`
- The `steward_tick` handler locks rows via `UPDATE status='processing' WHERE scheduled_id=? AND status='pending'` before sending
- Postmark sends carry an `Idempotency-Key` header tied to `dedupe_key`

If the cron tick fires twice in the same minute (network retry), the second run finds zero pending rows because the first run already locked them.

### Failure handling

Adopts the same `retry_once` pattern from SP2 (per [PRE Q7] — one in-process retry, then alert and re-raise so the cron's retry loop kicks in). Specifically:

- Postmark send: wrap in `retry_once`
- Aemon HTTP call (if external): wrap in `retry_once`
- DB writes: no retry (SQLite locks are caught by WAL)

### Alerting

- `delivery_failures` row is written on second failure
- Postmark `sp3-steward-failure-alert` email to Kyle on second failure
- Steward operational metrics card surfaces failure rate over last 24h
- Daily digest (existing SP2 cron) gains a Steward section: drafts pending, drafts sent, escalations, failures

### Incident runbook addendum

`_ops/INCIDENT_RUNBOOK.md` gains four new scenarios in Session 7:

- Scenario 9: Steward inbound webhook rejecting all messages (likely shared secret mismatch)
- Scenario 10: Steward queue is empty but inbound still arriving (classifier silent fail)
- Scenario 11: Aemon is failing every draft (Aemon disabled or misconfigured)
- Scenario 12: Scheduler tick not firing (cron service issue)

---

## 14. Interfaces to Sub-Project 4

SP4 (Scout/Raven/Herald) writes leads to the same `leads` table with `source IN ('scout', 'raven', 'herald')`. Steward picks them up via the same lifecycle state machine, with one difference:

- Outbound-sourced leads start in `nurture_active`, not `new`
- They enroll in the cold lead nurture sequence automatically on insert
- Their `notes` column carries UTM and campaign ID for attribution

SP3 writes the contract; SP4 implements the producer side.

---

## 15. Out of Scope

Things explicitly NOT in SP3, so Kyle and Khal don't drift:

- **Weekly business intelligence digest.** That's Citadel. Steward gets an operational panel; Citadel gets BI.
- **Outbound prospecting (Scout).** SP4.
- **LinkedIn drafting (Herald).** SP4.
- **Drip campaign authoring (Raven beyond Steward's nurture sequences).** SP4.
- **Customer portal / login.** Not in any sub-project yet.
- **SQLite to Postgres migration.** Volume-driven, not roadmap-driven.
- **CHDB Law inbox monitoring.** Hard-prohibited (see Section 12).
- **Phone/SMS automation.** Out of scope for SP3.
- **Calendar booking automation beyond providing Cal.com links.** Cal.com is the source of truth.
- **Real-time websocket admin dashboard.** Page-refresh is fine for MVP.
- **Multi-user admin dashboard.** Single-user (Kyle) per locked SP2 [PRE Q4].
- **A separate Steward microservice or repo.** Steward extends `stripe-delivery/` in-place.
- **A long-running worker process.** Architecturally forbidden — see Section 2.
- **Migrating any SP2 endpoint.** Backward compatibility is mandatory; every SP2 test must continue to pass.

---

## 16. Work Sequence

Sessions are numbered to match the SP3 playbook ([2026-04-13-sp3-day-session-playbook.md](../plans/2026-04-13-sp3-day-session-playbook.md)). This section is the spec-side summary.

1. **Session 1 — Scaffolding + inbound webhook stub.** Steward subpackage skeleton, `/api/inbound` stub with shared-secret validation and CHDB hard-fail, `inbound_emails` table, render.yaml updates with new cron services declared (stub commands), tests.
2. **Session 2 — Lifecycle state machine + scheduled_emails table + scheduler tick.** Pure logic + cron HTTP endpoint, no live sends yet.
3. **Session 3 — Inbound classifier + template renderer + Aemon stub.** Rule-based classifier, Jinja2 template loader, Aemon module with the rule-checks but in-process.
4. **Session 4 — Aemon-then-Kyle review pipeline + four-tier policy + outbox manager.** End-to-end through send (with a sandbox Postmark stream).
5. **Session 5 — Pre-engagement intake automation.** Form delivery, web pages, response capture, pre-call brief generator.
6. **Session 6 — Steward admin panel.** Queue, pipeline, scheduled, inbound, lead timeline, operational metrics.
7. **Session 7 — Nurture sequence enrollment + onboarding drip + Aemon production rule pass.** Full lifecycle automation; Aemon reviews and approves all SP3 templates.
8. **Session 8 — Soak test, incident runbook addendum, production cutover.** 24-hour staging soak with seeded leads and inbound replies; new scenarios in INCIDENT_RUNBOOK.md; Steward enabled in production via feature flag.

---

## 17. Review Gates and Quality Standards

### Per-session gates

- Tests must stay green; the test suite count never regresses below the previous session's count.
- Every commit pushed to main with `SP3 Session N: <description>` + Co-Authored-By line.
- Every parking-lot decision logged with default + Kyle's expected confirmation in the evening.
- No em dashes in any new code, comments, docs, or template copy.

### Aemon review gates

- **Session 3 gate:** Aemon module's rule set is reviewed by Kyle; any false positives in rule-hit tests are documented in the parking lot.
- **Session 7 gate:** Aemon does a full pass on every SP3 outbound template and signs off in the parking lot before SP3 ships to production.

### Production cutover gates

- All success criteria in Section 1 met
- 24-hour staging soak clean
- Incident runbook addendum complete
- `STEWARD_ENABLED=true` in production only after Kyle approves the soak report

---

## Appendix A: Steward Subpackage Layout

```
stripe-delivery/
  api/
    inbound.py                    # /api/inbound route (top-level, mounted in main.py)
    steward/
      __init__.py                 # subpackage docstring
      README.md                   # how the pieces fit together
      state.py                    # lifecycle state machine + send_tier_for()
      classifier.py               # rule-based + LLM fallback classification
      templates.py                # Jinja2 + Postmark template alias resolution
      aemon.py                    # Aemon legal review interface
      outbox.py                   # send_now / queue_for_kyle / escalate / file_silent
      scheduler.py                # steward_tick + scheduled_emails CRUD
      sequences.py                # NURTURE_COLD_LEAD, ONBOARDING_PRODUCT
      intake.py                   # intake form generation + token + storage
      brief.py                    # pre-call brief markdown generator
      enforcement.py              # CHDB separation hard-fail helpers
  scripts/
    trigger_steward_tick.py       # cron HTTP-trigger script
    trigger_steward_nurture_sweep.py
    sync_postmark_templates.py    # extended to include sp3-* aliases
  tests/
    test_steward_state.py
    test_steward_classifier.py
    test_steward_templates.py
    test_steward_aemon.py
    test_steward_outbox.py
    test_steward_scheduler.py
    test_steward_intake.py
    test_steward_inbound_route.py
    test_steward_enforcement.py
    test_steward_admin_panel.py
    test_steward_e2e_pipeline.py
```

---

## Appendix B: Pre-Session Locks

These are open questions that must be answered before Session 1 begins. Each appears as a `[PRE]` entry in `DECISIONS_PARKING_LOT.md`. The defaults are documented in this spec; Kyle confirms or overrides in the parking lot.

### PRE Q1 — Auto-send tier policy

Locked CONFIRMED: four tiers (TIER_AUTO, TIER_REVIEW, TIER_ESCALATE, TIER_SILENT). See Section 3.

### PRE Q2 — Aemon review path

Locked CONFIRMED: serial Aemon-then-Kyle. See Section 4.

### PRE Q3 — Inbox scope

Locked CONFIRMED: `@sidebarcode.com` only. CHDB Law inbox is hard-prohibited at the code level. See Section 12.

### PRE Q4 — Worker model

Locked CONFIRMED: no long-running worker. HTTP routes + HTTP-triggered cron, all inside the existing `sidebarcode-api` web service. See Section 2 design decisions.

### PRE Q5 — Weekly BI digest

Locked CONFIRMED: dropped from SP3 scope. Replaced with Steward-specific operational metrics panel. See Section 10. BI is deferred to a future Citadel sub-project.

### PRE Q6 — Classification approach

Locked CONFIRMED: rule-based first, LLM fallback for ambiguous. Anthropic API call gated by `CLASSIFIER_LLM_ENABLED` env var. See Section 2 design decisions.

### PRE Q7 — Aemon transport

**PENDING.** Default: in-process Python function call (no HTTP). Alternative: HTTP call to a sibling endpoint within the same web service. The default is faster and simpler; the alternative is cleaner if Aemon is ever extracted. Agent default if Kyle does not specify: in-process.

### PRE Q8 — Onboarding cadence

Default CONFIRMED: Day 1, 2, 7, 14, 30. Adjustable per-tier in catalog. See Section 8.

### PRE Q9 — Cold lead nurture cadence

Default CONFIRMED: 90 days, 6 touches (Day 0, 3, 10, 30, 60, 90). See Section 8.

### PRE Q10 — Feature flag default in production

Locked CONFIRMED: `STEWARD_ENABLED=false` in production at first deploy. Kyle flips to `true` after staging soak. See Section 11.

---

*End of spec. Version 1.0. Last updated: 2026-04-13.*
