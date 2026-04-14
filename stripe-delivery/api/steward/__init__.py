"""Steward subpackage — inbound triage, lifecycle automation, Aemon review.

SP3 of Sidebar Code. Extends the SP2 stripe-delivery service in-process.
No long-running worker; inbound is HTTP, scheduled outbound is HTTP-triggered
cron, both inside the existing sidebarcode-api web service.

CHDB email separation is a hard architectural rule enforced in
api/steward/enforcement.py. Every code path that touches an email address
must reject any address matching chdblaw.com. There is no override flag.

See docs/superpowers/specs/2026-04-13-steward-operationalized-design.md for
the full design and docs/superpowers/plans/2026-04-13-sp3-day-session-playbook.md
for the build sequence.
"""

__all__: list[str] = []
