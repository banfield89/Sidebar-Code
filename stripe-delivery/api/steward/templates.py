"""Template renderer — Jinja2 for local composition, Postmark aliases for sends.

Stub for Session 1. Real implementation lands in Session 3 per the playbook.

Session 3 will add:
  - Jinja2 environment loading from api/steward/templates_data/
  - render(template_id, context) returning rendered string
  - list_templates() returning the registry
  - Postmark template alias mapping for transactional sends
"""

from __future__ import annotations

__all__: list[str] = []
