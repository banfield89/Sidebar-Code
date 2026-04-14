"""Nurture and onboarding sequence definitions.

Stub for Session 1. Real implementation lands in Session 7 per the playbook.

Session 7 will add:
  - NURTURE_COLD_LEAD: 6 steps, Day 0/3/10/30/60/90, all TIER_REVIEW
  - ONBOARDING_PRODUCT: 5 steps, Day 1/2/7/14/30, Day 1+2 TIER_AUTO,
    Day 7+14+30 TIER_REVIEW
  - NurtureStep dataclass (day_offset, template_id, send_tier)
  - enroll(lead_or_purchase, sequence) — writes one scheduled_emails row per
    step with dedupe_key f"{sequence_name}:{lead_id}:{template_id}"
"""

from __future__ import annotations

__all__: list[str] = []
