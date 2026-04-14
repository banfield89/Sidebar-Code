"""Lifecycle state machine + four-tier auto-send policy.

Stub for Session 1. Real implementation lands in Session 2 per
docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md.

Session 2 will add:
  - LEGAL_TRANSITIONS dict and transition() function
  - send_tier_for(template_id, classification) returning one of TIER_AUTO,
    TIER_REVIEW, TIER_ESCALATE, TIER_SILENT
  - apply_verdict(initial_tier, aemon_verdict) escalation logic
  - IllegalStateTransition exception
"""

from __future__ import annotations

TIER_AUTO = "TIER_AUTO"
TIER_REVIEW = "TIER_REVIEW"
TIER_ESCALATE = "TIER_ESCALATE"
TIER_SILENT = "TIER_SILENT"

__all__ = ["TIER_AUTO", "TIER_REVIEW", "TIER_ESCALATE", "TIER_SILENT"]
