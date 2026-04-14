"""CHDB email separation enforcement — hard rule, no exceptions.

Kyle's standing instruction (2026-04-13): Steward must never read, write, or
process any email touching @chdblaw.com. This is enforced at every boundary
where an email address could enter or leave the system:

  - api/inbound.py before inserting into inbound_emails
  - api/steward/outbox.py before any Postmark send
  - api/steward/intake.py before generating intake form delivery
  - api/crm.py insert_lead (hardening pass added in SP3)

Why: routing client-firm email through a Sidebar Code agent creates client
confidentiality, attorney-client privilege, and corporate-veil exposure
between CHDB Law, LLP and Banfield Consulting, LLC d/b/a Sidebar Code.
There is no override flag. Revisiting this rule requires a new spec, not a
config change.

False positives are acceptable; false negatives are not. The scan is
deliberately paranoid: it iterates every string-shaped value in the
payload (including nested Headers[] arrays) and rejects on any
`chdblaw.com` substring (case-insensitive).
"""

from __future__ import annotations

from typing import Any

CHDB_DOMAIN_MARKER = "chdblaw.com"


class ChdbSeparationViolation(ValueError):
    """Raised when any code path attempts to touch a @chdblaw.com address."""


def contains_chdb(value: Any) -> bool:
    """Recursively scan any value for a chdblaw.com substring (case-insensitive).

    Walks dicts, lists, tuples, and strings. Returns True on the first hit.
    Non-string scalars (int, bool, None) are ignored.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return CHDB_DOMAIN_MARKER in value.lower()
    if isinstance(value, dict):
        return any(contains_chdb(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(contains_chdb(v) for v in value)
    return False


def enforce_inbound(payload: dict) -> None:
    """Hard-fail if any field in a Postmark inbound payload touches CHDB.

    Called from api/inbound.py BEFORE the row is inserted into
    inbound_emails. Raises ChdbSeparationViolation on hit; the caller
    converts this into an HTTP 422 response.
    """
    if contains_chdb(payload):
        raise ChdbSeparationViolation(
            "Inbound payload contains an @chdblaw.com address. "
            "CHDB Law inbox is hard-prohibited in Sidebar Code per "
            "the standing CHDB email separation rule (2026-04-13). "
            "See api/steward/enforcement.py for rationale."
        )


def enforce_outbound(recipient: str | None) -> None:
    """Hard-fail if a Steward send is targeting a CHDB address.

    Called from api/steward/outbox.py BEFORE any Postmark send.
    Empty/None recipients pass through (the caller handles missing-recipient
    errors separately).
    """
    if recipient is None:
        return
    if contains_chdb(recipient):
        raise ChdbSeparationViolation(
            f"Refusing to send to {recipient!r}: CHDB Law inbox is "
            "hard-prohibited in Sidebar Code per the standing rule "
            "(2026-04-13). See api/steward/enforcement.py."
        )


def enforce_lead_email(buyer_email: str | None) -> None:
    """Hard-fail if a lead is being created with a CHDB buyer_email.

    Called from api/crm.py insert_lead as a hardening pass added in SP3.
    """
    if buyer_email is None:
        return
    if contains_chdb(buyer_email):
        raise ChdbSeparationViolation(
            f"Refusing to insert lead with buyer_email={buyer_email!r}: "
            "CHDB Law inbox is hard-prohibited per the standing rule."
        )
