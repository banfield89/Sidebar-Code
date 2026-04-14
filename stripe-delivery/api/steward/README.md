# Steward subpackage — Sidebar Code SP3

Inbound triage, lifecycle automation, Aemon legal review, and pre-engagement intake for Sidebar Code.

This package extends the SP2 stripe-delivery service in-process. It does not run as a separate worker, sidecar, or microservice. All Steward logic executes either as HTTP routes on the existing FastAPI app or as HTTP-triggered cron endpoints with `CRON_SECRET` Bearer auth.

## Module layout

| Module | Purpose | First implemented in |
|---|---|---|
| `enforcement.py` | CHDB email separation hard-fail helpers (called from inbound, outbox, intake, crm) | Session 1 |
| `state.py` | Lifecycle state machine + `send_tier_for()` four-tier policy + `apply_verdict()` | Session 2 |
| `scheduler.py` | `scheduled_emails` CRUD + `steward_tick()` cron handler | Session 2 |
| `classifier.py` | Rule-based + LLM-fallback inbound classification | Session 3 |
| `templates.py` | Jinja2 template loader + Postmark template alias resolution | Session 3 |
| `aemon.py` | Aemon legal review — 10 rule checks per spec Section 4 | Session 3 |
| `outbox.py` | `send_now`, `queue_for_kyle`, `escalate`, `file_silent` | Session 4 |
| `intake.py` | Pre-engagement intake form generation, HMAC tokens, response capture | Session 5 |
| `brief.py` | Pre-call brief markdown generator | Session 5 |
| `sequences.py` | `NURTURE_COLD_LEAD` and `ONBOARDING_PRODUCT` step definitions | Session 7 |

## Hard rules

1. **CHDB Law inbox is non-negotiable out of scope.** Every email-touching code path checks `chdblaw.com` and rejects. Enforced in `enforcement.py`. Tests assert the rejection.
2. **Aemon-then-Kyle, serial.** No draft sends without Aemon clearance. Aemon can escalate but never de-escalate.
3. **Four-tier auto-send policy** in `state.send_tier_for()`. No template bypasses it.
4. **Idempotent everywhere.** `inbound_emails` deduped on Postmark message_id; `scheduled_emails` deduped on `dedupe_key` (UNIQUE).
5. **No long-running worker.** All logic is HTTP or HTTP-triggered cron.
6. **No em dashes in any file in this subpackage.** Code, comments, docstrings, template copy.

## Pairs with

- Spec: [docs/superpowers/specs/2026-04-13-steward-operationalized-design.md](../../../docs/superpowers/specs/2026-04-13-steward-operationalized-design.md)
- Playbook: [docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md](../../../docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md)
- Parking lot: [docs/superpowers/plans/DECISIONS_PARKING_LOT.md](../../../docs/superpowers/plans/DECISIONS_PARKING_LOT.md)
