---
doc_type: operational
last_updated: 2026-04-11
---

# Product Catalog Operations

This catalog contains all Sidebar Code product, consulting, and custom workflow tier documentation.

## Structure

- `_playbook/` - Kyle's sales playbook (internal only, never shared with prospects)
- `_maester_persona/` - Instructions and templates for Maester drafting sessions
- `products/` - Self-serve product tiers (Parser Trial, Full Litigation Suite)
- `consulting/` - Consulting engagement tiers (Foundation, Implementation, Modernization)
- `custom_workflows/` - Custom agent workflow tiers (Single, Multi, Practice-Area)
- `shared/` - Assets shared across all tiers (disclaimers, bios, branding)
- `_ops/` - Operational documents (this folder)
- `CATALOG_INDEX.md` / `.yaml` - Central tier index for agent consumption

## Per-Tier Folder Pattern

Every tier folder contains:
- `_internal/` - Kyle's eyes only (methodology, margins, upsell paths)
- `_sales_packet/` - What prospects see during sales conversations
- `_customer_deliverables/` - What paying customers receive
- `intake_and_contracting/` - Intake forms and engagement letters (consulting/workflow tiers only)
- `tier_manifest.md` - One-page summary with YAML frontmatter

## Review Status

Check `CATALOG_INDEX.yaml` for current review status across all tiers.
Check the Kyle Review Dashboard for items pending Kyle's review.

## Rules

- Nothing in `_sales_packet/` or `_customer_deliverables/` ships without Kyle's approval
- Nothing in `intake_and_contracting/` ships without Aemon's legal review
- All customer-facing documents must pass the quality standards in the spec (Section 6)
