"""Inbound email classifier — rule-based first, LLM fallback for ambiguous.

Stub for Session 1. Real implementation lands in Session 3 per the playbook.

Session 3 will add:
  - Classification dataclass (template_id, confidence, rule_hits)
  - Rule-based classifier covering spam, FAQ, pricing inquiry, scheduling,
    hot lead, customer issue, intake response, unsubscribe, autoresponder
  - LLM fallback gated by CLASSIFIER_LLM_ENABLED env var (Anthropic API,
    default model claude-haiku-4-5-20251001)
"""

from __future__ import annotations

__all__: list[str] = []
