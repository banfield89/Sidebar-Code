"""Aemon legal-review module — gates every Steward draft before send.

Stub for Session 1. Real implementation lands in Session 3 per the playbook.

Session 3 will add the 10 rule checks from spec Section 4:
  1. Disclaimer presence
  2. Practice-area neutrality
  3. Pricing accuracy against CATALOG_INDEX.yaml
  4. Solo Launch Package leakage detection
  5. CHDB separation reference detection (HIGH severity)
  6. Em-dash detection (low severity)
  7. ToS / refund language hash match
  8. Tone-vs-tier mismatch flag
  9. Merge variable injection (unrendered jinja vars)
 10. Substitution attack detection (URL/email mismatch)

Aemon-then-Kyle is serial. Aemon never raises on draft content; only on
programming errors. Aemon disabled (STEWARD_AEMON_ENABLED=false) forces
all drafts into TIER_REVIEW with an annotation.
"""

from __future__ import annotations

__all__: list[str] = []
