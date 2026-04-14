"""Outbox manager — send_now, queue_for_kyle, escalate, file_silent.

Stub for Session 1. Real implementation lands in Session 4 per the playbook.

Session 4 will add:
  - send_now(draft, verdict, recipient) — TIER_AUTO path; wraps Postmark in retry_once
  - queue_for_kyle(draft, verdict, lead_id) — TIER_REVIEW path; inserts scheduled_emails row
  - escalate(draft, verdict, lead_id) — TIER_ESCALATE path; sends Kyle a brief
  - file_silent(payload, classification) — TIER_SILENT path; lead_event only

Every path calls api.steward.enforcement.enforce_outbound(recipient)
BEFORE any Postmark API call. CHDB recipients are rejected with
ChdbSeparationViolation.
"""

from __future__ import annotations

__all__: list[str] = []
