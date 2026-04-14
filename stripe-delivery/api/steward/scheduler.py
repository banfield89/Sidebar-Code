"""Scheduled email queue + steward_tick cron handler.

Stub for Session 1. Real implementation lands in Session 2 per the playbook.

Session 2 will add:
  - scheduled_emails CRUD: enqueue, fetch_due, lock, mark_sent,
    mark_awaiting_kyle, mark_failed, cancel_pending_for_lead
  - steward_tick() — cron-triggered handler that processes due rows
  - All operations idempotent on the unique dedupe_key

The cron tick endpoint POST /admin/cron/steward-tick lives in api/admin.py
and calls scheduler.steward_tick() under CRON_SECRET Bearer auth.
"""

from __future__ import annotations

__all__: list[str] = []
