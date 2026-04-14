"""Pre-engagement intake automation — form delivery, HMAC tokens, response capture.

Stub for Session 1. Real implementation lands in Session 5 per the playbook.

Session 5 will add:
  - HMAC token generation with STEWARD_INTAKE_HMAC_SECRET
  - send_intake_form(lead) — creates intake_forms row, schedules form-link email
  - Tier-specific form schemas
  - GET /intake/{token} HTML form rendering
  - POST /intake/{token} response capture and brief generation
"""

from __future__ import annotations

__all__: list[str] = []
