# Sidebar Code Product Catalog Design Spec
## Sub-Project 1 of 4: Product Catalog Build-Out

**Date:** April 11, 2026
**Author:** Kyle Banfield + Claude (brainstorming session)
**Status:** Pending Kyle review
**Scope:** MVP product catalog for all 8 Sidebar Code tiers
**Approach:** Subagent dispatch + Catalog Builder skill, maximum automation, Kyle reviews

---

## Table of Contents

1. [Goal and Success Criteria](#1-goal-and-success-criteria)
2. [Folder Architecture](#2-folder-architecture)
3. [Playbook and Maester Persona](#3-playbook-and-maester-persona)
4. [Per-Tier Deliverables](#4-per-tier-deliverables)
5. [Work Sequence](#5-work-sequence)
6. [Review Gates and Quality Standards](#6-review-gates-and-quality-standards)
7. [Interfaces for Sub-Projects 2-4](#7-interfaces-for-sub-projects-2-4)

---

## 1. Goal and Success Criteria

### Goal

Build the MVP product catalog for Sidebar Code such that Kyle can respond to any inquiry within 60 seconds with accurate tier details, pricing, and next steps, AND can deliver on a signed engagement without scrambling to produce assets.

### Decomposition Context

This is sub-project 1 of 4:
- **Sub-project 1 (this spec):** Product Catalog Build-Out
- **Sub-project 2:** Website Stripe Integration + Delivery Automation
- **Sub-project 3:** AI Sales Team (Steward operationalized)
- **Sub-project 4:** Lead Generation (Scout/Raven/Herald operationalized)

Each sub-project gets its own spec and implementation plan. They build sequentially but share interfaces documented in Section 7.

### In Scope

- Folder structure for all 8 advertised tiers (2 products, 3 consulting, 3 custom workflows)
- Source-of-truth "what's in the box" documents per tier with YAML frontmatter for agent consumption
- Intake questionnaires (with YAML intake_schema blocks), engagement letters, and delivery kits
- The Sidebar Code Sales Playbook (Kyle's master voice/positioning/FAQ doc)
- Product tier deliverables shippable on day one (skill files, installer, Integration Guide, CLAUDE.md starter)
- Maester Persona instructions file for bulk drafting sessions
- Catalog Builder skill (`/build-catalog-tier`) for future tier creation
- Kyle Review Dashboard (basic todo/review tracker, Khal builds in parallel)
- CATALOG_INDEX.md and CATALOG_INDEX.yaml for agent cold-start access
- Agent protocols documentation for sub-projects 2-4
- Website update: 2 product tiers, remove Arizona refs, update Foundation description

### Out of Scope

- Full Integration Guide Chapters E-I (skill walkthroughs, deep phase)
- Deep consulting deliverables beyond MVP scaffolds (full governance framework, CLE curriculum)
- Stripe integration and payment flows (sub-project 2)
- Operational Steward/Raven/Scout/Herald infrastructure (sub-projects 3-4)
- The Hand orchestrator and real agent dispatch infrastructure
- Additional practice-area skill packs
- Jurisdiction-specific content packs (national/jurisdiction-neutral from day one)

### Success Criteria

All must be true for MVP complete:

1. Kyle can open the catalog and answer any inquiry for any of the 8 tiers in under 60 seconds
2. The 2 product tiers (Parser Trial + Full Litigation Suite) have complete customer deliverables ready to ship
3. The 3 consulting tiers have intake questionnaire, engagement letter, scope-of-work template, and sales packet ready
4. The 3 custom workflow tiers have scope-of-work template, scoping guide, and sales packet ready
5. The Sales Playbook covers positioning, pricing, tier boundaries, objections, and inquiry patterns for every tier
6. The Catalog Builder skill exists and has been tested by generating one tier folder
7. Terms of Service has been reviewed by Aemon
8. The catalog structure can be migrated to automated delivery in sub-project 2 without rework
9. The Kyle Review Dashboard tracks all pending review items across the catalog
10. Every customer-facing document passes the quality standards in Section 6

### Key Design Decisions

| Decision | Choice | Date |
|---|---|---|
| Strategy | Tiered MVP then professional-grade; don't launch until rounded out | 2026-04-11 |
| Who does the work | Kyle authors strategy/voice; agents draft bulk content; Kyle reviews all | 2026-04-11 |
| Catalog structure | Two-layer folders (_internal, _sales_packet, _customer_deliverables) with migration path | 2026-04-11 |
| MVP quality bar | Product tiers fully shippable; consulting/workflow tiers scaffolded for close-and-deliver | 2026-04-11 |
| Automation level | Subagent dispatch + Catalog Builder skill; maximum automation | 2026-04-11 |
| Product tiers | 2 tiers: Parser Trial ($197) + Full Litigation Suite ($2,997). Trio eliminated. | 2026-04-11 |
| Licensing | Flat one-time, firm-wide internal use. No seats. | 2026-04-09 |
| Jurisdiction | National from day one. Jurisdiction-neutral. No Arizona-specific packs. | 2026-04-11 |
| AI Usage Policy | Retired. Replaced with Technology Overview and Limitations Guide (CYA, not policy). | 2026-04-11 |
| Ethics training | Consulting/CLE only. No templated ethics documents in products. | 2026-04-11 |
| Privilege logs | Removed from all example lists (uploading privileged docs to LLM is a liability risk). | 2026-04-11 |
| Memory bank | Implementation tier centerpiece. Westlaw summaries as knowledge base foundation. | 2026-04-11 |
| Legal update monitoring | Future Custom Workflow offering. Not built at MVP. | 2026-04-11 |
| Installer | One-click exe/app targeting Claude Code Desktop App (not VS Code). Khal builds in Week 1. | 2026-04-11 |
| Product support | No email support in product tiers. Self-serve only. Support = paid consulting ($500/hr) or upgrade. | 2026-04-11 |
| Maester | Subagent session persona, not a wired agent. No persistent agent infrastructure needed for MVP. | 2026-04-11 |

---

## 2. Folder Architecture

### Root Location

```
C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Product Catalog\
```

### Top-Level Structure

```
Product Catalog\
+-- _playbook\
|   +-- SALES_PLAYBOOK.md
|   +-- POSITIONING_CORE.md
|   +-- PRICING_LOGIC.md
|   +-- OBJECTION_HANDLING.md
|   +-- TIER_BOUNDARIES.md
|   +-- INQUIRY_RESPONSE_TEMPLATES.md
|
+-- _maester_persona\
|   +-- MAESTER_INSTRUCTIONS.md
|   +-- DRAFTING_TEMPLATES\
|   |   +-- what_is_in_the_box_template.md
|   |   +-- intake_questionnaire_template.md
|   |   +-- scope_of_work_template.md
|   |   +-- engagement_letter_template.md
|   |   +-- customer_faq_template.md
|   +-- VOICE_REFERENCE\
|       +-- kyle_voice_samples.md
|
+-- products\
|   +-- 01_parser_trial\
|   +-- 02_full_litigation_suite\
|
+-- consulting\
|   +-- 01_foundation\
|   +-- 02_implementation\
|   +-- 03_modernization\
|
+-- custom_workflows\
|   +-- 01_single_workflow\
|   +-- 02_multi_agent\
|   +-- 03_practice_area\
|
+-- shared\
|   +-- disclaimers\
|   +-- terms_of_service\
|   +-- kyle_bio\
|   +-- logos_and_branding\
|   +-- legal_review_queue\
|
+-- _ops\
|   +-- README.md
|   +-- DEPLOYMENT_CHECKLIST.md
|   +-- VERSION_LOG.md
|   +-- HANDOFF_NOTES.md
|   +-- AGENT_PROTOCOLS.md
|
+-- CATALOG_INDEX.md
+-- CATALOG_INDEX.yaml
```

### Per-Tier Sub-Folder Pattern

Every tier folder follows this structure:

```
[tier_name]\
+-- _internal\
|   +-- methodology.md
|   +-- margins_and_time.md
|   +-- known_traps.md
|   +-- upsell_paths.md
|
+-- _sales_packet\
|   +-- what_is_in_the_box.md
|   +-- customer_faq.md
|   +-- sample_output.md (consulting/workflow tiers)
|   +-- one_page_overview.md
|   +-- inquiry_response.md
|
+-- _customer_deliverables\
|   +-- [tier-specific files]
|   +-- delivery_readme.md
|
+-- intake_and_contracting\ (consulting and workflow tiers only)
|   +-- intake_questionnaire.md (with YAML intake_schema)
|   +-- engagement_letter.md
|   +-- scope_of_work_template.md
|
+-- tier_manifest.md (with YAML frontmatter)
```

### Agent-Readiness Features

**YAML frontmatter on all tier documents.** Machine-readable fields:

```yaml
---
tier_id: consulting_foundation
tier_name: Foundation Package
price_min: 5000
price_max: 7500
price_display: "$5,000 - $7,500"
delivery_time_days: 7
includes: [list]
excludes: [list]
tier_above: consulting_implementation
tier_below: products_full_suite
upsell_path: consulting_implementation
status: mvp_complete
last_updated: 2026-04-15
reviewed_by: kyle
---
```

**CATALOG_INDEX.yaml** at root level. Central index of all 8 tiers with metadata. Agents read this on cold start. Includes `catalog_version` field that bumps on every change.

**Intake schema YAML blocks** on every intake questionnaire defining fields, types, and validation for agent data collection.

**Version tracking** via `last_updated` and `catalog_version` fields. Agents detect staleness automatically.

**Agent protocols** documented in `_ops/AGENT_PROTOCOLS.md` specifying per-tier workflows for Steward, Raven, and other future agents.

---

## 3. Playbook and Maester Persona

### 3.1 The Sales Playbook

**Location:** `Product Catalog\_playbook\SALES_PLAYBOOK.md`
**Author:** Kyle (via the 11-prompt interview sequence)
**Size:** 20-30 pages
**Purpose:** Single source of truth for voice, positioning, pricing logic, tier boundaries, objection handling, inquiry patterns. Every other catalog document derives from it.

**10 Sections:**
1. The Core Narrative (Kyle's story, 2-3 paragraphs)
2. Who We Are and Are Not (IS/IS NOT list, with example situations)
3. The Target Buyer (managing partner profile, psychology, signals)
4. The 8-Tier Catalog At a Glance (one paragraph per tier)
5. Per-Tier Positioning Deep Dive (1 page per tier: who, pain point, what they get, what they don't, 60-second pitch, top 3 questions)
6. Pricing Logic (internal: hours, margins, value delivered, market comparables, discounting policy)
7. Tier Boundaries (what's included vs held for consulting, per tier, with scripted responses)
8. Objection Handling (top 15 objections with underlying concern, preferred response, follow-up move)
9. Inquiry Response Patterns (decision tree for first-touch routing by signal quality and tier interest)
10. Voice and Writing Rules (non-negotiables, sentence patterns, word choices, example sentences)

**Authoring method:** Kyle runs the 11-prompt sequential interview sequence in a Claude Code session. Claude interviews Kyle, drafts each section from Kyle's answers, Kyle reviews and edits. Total active Kyle time: 3.5-5 hours across 4 sessions. The full prompt sequence is documented in the brainstorming session transcript (Sections 3, Prompts 0-11).

### 3.2 The Maester Persona

**Location:** `Product Catalog\_maester_persona\MAESTER_INSTRUCTIONS.md`
**Purpose:** Instructions file Kyle loads into a Claude Code session for bulk content drafting. NOT a real agent with dispatch. A session-level persona.

**Key elements:**
- Scope: what Maester drafts (sales packets, FAQs, intake forms, engagement letter shells, methodology stubs)
- Hard limits: no practice-area claims, no CLAUDE.md templates, no multi-agent blueprints, no em dashes, no improvising on pricing
- Source documents: Playbook, framework, Terms of Service
- Output format: YAML frontmatter on every draft, review_status: pending_kyle_review
- Escalation triggers: stop and ask Kyle if Playbook doesn't cover it, if business judgment required, if contradiction found
- Confidence assessment required on every draft

**5 Drafting Templates:**
1. `what_is_in_the_box_template.md`
2. `intake_questionnaire_template.md`
3. `scope_of_work_template.md`
4. `engagement_letter_template.md`
5. `customer_faq_template.md`

### 3.3 Voice Reference

**Location:** `Product Catalog\_maester_persona\VOICE_REFERENCE\kyle_voice_samples.md`
**Sources:** Landing page hero/consulting/workflow sections (6-8 paragraphs) + framework executive summary (3-4 paragraphs) + Kyle's resume for credential language.
**Kyle effort:** 15-20 minutes pulling samples. No annotation session needed.

### 3.4 Catalog Builder Skill

**Location:** `~/.claude/commands/build-catalog-tier.md`
**Purpose:** Reusable skill that generates a complete tier folder from inputs. Adding a new tier becomes a 15-minute operation instead of 4-6 hours.

**Inputs:** tier_id, tier_name, tier_category (product/consulting/workflow), price, what's included, what's excluded, upsell path, delivery timeline
**Outputs:** Complete tier folder with tier_manifest.md, what_is_in_the_box.md, customer_faq.md, inquiry_response.md, intake_questionnaire.md (with YAML schema), and internal methodology stub. All with correct YAML frontmatter.
**Reads:** Playbook for voice and positioning.
**Effort to build:** 2-3 hours.

---

## 4. Per-Tier Deliverables

### 4.1 Product Tiers (Shippable at MVP)

#### Parser Trial ($197)

**Purpose:** Get the product into the firm. Create the "aha" moment. Generate a warm consulting lead. $197 is below any approval threshold at most firms.

**Always ships the Parser skill** (not buyer's choice). Parser has the most immediate "wow" factor, most naturally leads to Full Suite upsell, and is the safest skill to demo (analyzes, doesn't generate filings).

**Customer deliverables:**
- `pleading-parser.md` (the templatized skill file)
- `INSTALLATION.md` (how to use the installer; 1 page)
- `QUICK_START.md` (2-3 pages: what Parser does, how to run it, what to expect)
- `ATTORNEY_REVIEW_CHECKLIST.md` (1 page, printable)
- `TERMS_AND_LICENSE.md` (firm-wide license, ToS link)
- `WHATS_NEXT.md` (1 page: what the Full Suite and consulting tiers offer; earned upsell, not pushy)
- `README.md`
- Installer binary (parser-only configuration)

**Prerequisite disclosure (must be communicated BEFORE purchase):** Sidebar Code skills require Claude Code (free download from Anthropic) and a Claude Pro/Max subscription or Anthropic API key (billed separately by Anthropic). This is a separate cost not included in the $197 purchase price. This must appear on:
- The website product description
- The README in the download ZIP
- The installer (if Claude Code is installed but not authenticated, show a message)
- The QUICK_START.md document

**Sales packet:** what_is_in_the_box.md, customer_faq.md, inquiry_response.md
**No intake/contracting.** One-click purchase. ToS click-through is the only contract.
**No email support.** Product tiers are self-serve. If the buyer needs help, they pay hourly consulting ($500/hr, 2-hr minimum) or upgrade to Foundation/Implementation which include support. This is stated clearly in the README and WHATS_NEXT documents.

**MVP effort:** 4-6 hours (copy skill file, write 5 short docs via Maester, Kyle reviews)

#### Full Litigation Suite ($2,997)

**Purpose:** The complete self-serve product. The consulting funnel entry point. Flagship product.

**Customer deliverables:**
- `skills/` folder with all 4 templatized skill files
- `integration_guide/` folder with:
  - Integration Guide v1.0 (PDF + DOCX, ~20-25 pages)
  - Quick Start Card (1-2 page PDF)
- `claude_md_starter/` folder with:
  - CLAUDE_starter_template.md (deliberately basic: 3 editable fields, review reminder, no-em-dashes rule, confidentiality note, upgrade path callout)
  - CLAUDE_starter_README.md (what it does, what it deliberately omits, upgrade path)
- `ATTORNEY_REVIEW_CHECKLIST.md`
- `TERMS_AND_LICENSE.md`
- `README.md`
- Installer binary (full-suite configuration, all 4 skills + CLAUDE.md starter)

**Integration Guide v1.0 scope (installer-simplified):**
- Chapter A: What This Is (3-4 pages)
- Chapter B: Installation (1-2 pages; installer does the work)
- Chapter J: Attorney Review, Ethics, and Hallucinations (8-10 pages)
- Chapter K: Troubleshooting (5-7 pages)
- Chapter L: Upgrade Paths (4-6 pages; the consulting funnel chapter)
- Per-Skill Quick Reference (4-8 pages; one page per skill)
- Quick Start Card (1-2 pages)

**v1.1 (deep phase) adds:** Chapters E-I (per-skill walkthroughs and matter-workflow integration)

**Prerequisite disclosure:** Same as Parser Trial. Claude Code + Anthropic subscription/API key required, billed separately. Must appear on website, README, installer, and Integration Guide Chapter A.

**Sales packet:** what_is_in_the_box.md, customer_faq.md (15+ questions), inquiry_response.md, one_page_overview.md
**No intake/contracting.** One-click purchase.
**No email support.** Same as Parser Trial. Self-serve product. Support is paid consulting or tier upgrade.

**MVP effort:** ~17-22 hours (Integration Guide is the dominant cost at 12-18 hours)

### 4.2 Consulting Tiers (Scaffolded for Close at MVP)

#### Foundation Package ($5,000 - $7,500)

**Purpose:** Kyle shows up and makes it work for your firm. This is a consulting session, not a product delivery. The firm walks out of the meeting with a working AI workflow, a trained team, and the confidence to use it. They did not have to read a guide, watch a video, or figure anything out on their own.

**What distinguishes Foundation from the Full Suite:** The Full Suite ($2,997) sells files; the Foundation sells Kyle's time, expertise, and the confidence that comes from having a practicing litigator in the room saying "here is how this works for a firm like yours." The target buyer (managing partner, risk-averse, not tech-comfortable) does not want files. They want someone to come in and make it work.

**Deliverables (what the client receives):**
- Kyle-led 90-minute implementation session for partners and associates (live demo, Q&A, Kyle handles the skeptics in real time; on-site or Zoom)
- Live deployment of ONE skill on the firm's workflow during the session (Kyle selects the highest-impact skill for the firm; Parser is the default for demo value, but Depo Prep may be better for a high-deposition-volume firm)
- Technology Overview and Limitations Guide (technology disclosure, NOT ethics policy; CYA document explaining what the tech does, its known limitations, and the attorney's independent obligation to verify everything)
- CLAUDE.md starter template configured live during the session (Kyle fills in firm name, jurisdiction, signing attorney on the managing partner's machine)
- 30-day email support (Kyle answers questions as the team starts using it)

**Does NOT include:**
- All 4 skills (that is the Full Suite at $2,997 or Implementation at $10-15K)
- Custom CLAUDE.md build with voice calibration (that is Implementation or the $3,000 add-on)
- Workflow audit (that is Implementation)
- Memory bank / commit-to-memory setup (that is Implementation)
- Multi-agent architecture (that is Modernization)
- Governance framework (that is Modernization)
- CLE training (that is Modernization)
- Ethics advice (that is the firm's bar counsel's job)

**Note:** A firm CAN buy both the Full Suite ($2,997) AND the Foundation Package ($5-7.5K). The Full Suite gives them all the tools. The Foundation gives them the training and the partner buy-in session. These are different products solving different problems.

**Ethics positioning:** Kyle may discuss AI awareness during the presentation as a fellow practitioner sharing his perspective. No formal document that tells firms what is or isn't ethically permissible. That is their bar's job. If they want deeper ethics guidance, that is a consulting conversation at the $500/hr rate or part of the Modernization engagement's CLE sessions.

**Key deliverable: Technology Overview and Limitations Guide.** Sections:
1. What the technology is (Claude Code, skill files, how AI generates output, what "probabilistic" means)
2. Known limitations (hallucinated citations, factual errors, jurisdiction confusion, outdated law, confident-when-wrong tendency)
3. Attorney's independent obligation (verify all citations, factual assertions, and legal conclusions; Sidebar Code does not provide legal advice; use of any AI platform without understanding the technology is on the attorney)

**Upsell trigger:** After the 90-minute session, the managing partner or lead associate says "can you make this sound like our firm?" or "can you do this for our other practice areas?" That is the Implementation pitch. Foundation deploys one skill and shows the concept. Implementation configures the entire system for the firm.

**Sales packet, intake/contracting, internal docs:** Full set per the folder pattern.
**MVP effort:** 18-25 hours total, 8-11 Kyle hours.

#### Implementation Package ($10,000 - $15,000)

**Purpose:** Transform the firm from "we have an AI policy" to "our attorneys use AI on every matter."

**Centerpiece deliverable: The Memory Bank.** Kyle builds the firm's institutional knowledge base from their existing filings + Westlaw summaries:
- Voice calibration from the firm's recent filings
- Authority library organized by topic, jurisdiction, practice area
- Argument pattern database from the firm's motion practice
- Pleading formatting standards from the firm's existing templates

Westlaw summary ingestion dramatically reduces build time (6-10 hours per practice area drops to 1-2 hours). Firm provides their Westlaw access; Kyle structures the output.

**Deliverables:**
- Custom CLAUDE.md build (tuned to firm's voice, practice areas, jurisdiction, using the memory bank)
- Workflow audit (structured interview with managing partner + lead associate; findings report with AI opportunity identification per workflow phase)
- Practice-area skill customization (the 4 standard skills configured for this firm's specific practice)
- Custom implementation guide (firm-specific version showing their workflows, their CLAUDE.md, their review protocol)
- Full skill suite via installer
- 90-day priority support + 45-day follow-up call
- Commit-to-memory workflow setup (email pipeline for ongoing document ingestion)

**Internal methodology (non-shareable IP):** CLAUDE.md build methodology, workflow audit questionnaire, memory bank build process.
**MVP effort:** 19-27 hours total, 12-17 Kyle hours.

#### Modernization Engagement ($25,000 - $40,000)

**Purpose:** Firm transformation. Every practice area. Governance. Training. Ongoing support. Rare at launch; expect 0-1 in first 6 months.

**Deliverables:**
- Multi-agent system architecture for the firm
- Complete governance framework (built per engagement, not from template)
- Full firm workflow audit across all practice areas
- CLE-eligible training sessions (accreditation pending; delivered as non-accredited CE if accreditation not complete)
- Full skill suite + firm-specific configuration
- 12-month quarterly strategic check-ins
- Dedicated project roadmap

**MVP state:** Minimally scaffolded. Project roadmap template, governance framework outline (3-5 pages showing structure, not content), phased engagement letter with milestone payments. Deep deliverables built when a customer signs.
**MVP effort:** 14-20 hours total, 8-12 Kyle hours.

### 4.3 Custom Workflow Tiers (Scaffolded at MVP)

All three tiers share the same intake questionnaire (with workflow-specific fields) and the same scoping guide that determines which tier fits.

**Scoping decision tree:**
- One workflow, one skill file, no agent coordination -> Single ($5,000)
- Two to three workflows with handoffs -> Multi ($10,000)
- Entire practice area from intake through resolution -> Practice-Area ($15,000-$25,000)
- Needs firm-wide governance or CLE -> Redirect to Modernization

#### Single Workflow Agent ($5,000)

**Deliverables (built per engagement):** One custom skill file, CLAUDE.md additions, workflow-specific quick reference (1-2 pages), one-hour training call.
**Delivery:** 2 weeks.
**Example agents:** Intake triage, demand letter generator, discovery request drafter, billing entry reviewer, case status updater, court filing compliance checker.
**MVP effort:** 8-12 hours.

#### Multi-Agent Workflow ($10,000)

**Deliverables (built per engagement):** 2-3 custom skill files, orchestration design document, CLAUDE.md additions, pipeline quick reference, two-hour training session.
**Delivery:** 3-4 weeks.
**Example pipelines:** Intake to drafting to review; discovery response pipeline; motion practice pipeline.
**MVP effort:** 8-13 hours.

#### Practice-Area Workflow ($15,000 - $25,000)

**Deliverables (built per engagement):** 4+ custom skill files, practice-area orchestration architecture, practice-area CLAUDE.md module, deployable skill pack, training materials, 90-day implementation support.
**Delivery:** 6-8 weeks.
**Example workflows:** Full collections lifecycle, full insurance defense case management, full PI plaintiff pipeline.
**MVP effort:** 11-16 hours.

### 4.4 Upsell Architecture

Each tier naturally generates demand for the next:

| From | To | Trigger |
|---|---|---|
| Parser Trial ($197) | Full Suite ($2,997) | Buyer uses Parser 3+ times in first week |
| Full Suite ($2,997) | Foundation ($5-7.5K) | Buyer asks about firm-wide adoption, partner buy-in, or "can someone show us how to use this?" |
| Foundation ($5-7.5K) | Implementation ($10-15K) | After the 90-min session, partner asks "can you make this sound like our firm?" or "can you do all our practice areas?" |
| Implementation ($10-15K) | Custom Workflow ($5-25K) | Workflow audit identifies a specific automatable bottleneck |
| Custom Workflow ($5-25K) | Modernization ($25-40K) | Firm has bought 2+ workflows and asks "can you do the whole firm?" |

Kyle never hard-sells. Each tier generates the questions that the next tier answers.

### 4.5 Future Offerings (Not MVP)

- **Legal update monitoring agent:** Custom Workflow offering. Agent monitors specified legal topics for changes (new case law, statutory amendments, rule changes) and generates structured alerts. Build when first firm asks for it.
- **Practice-area skill packs:** Separate products at separate price points. Insurance Defense, Personal Injury, etc. Build when demand proves which area first.
- **Jurisdiction modules:** Per-engagement customization, not a product. If 5+ firms from the same state request customization, consider a state-specific module product.

---

## 5. Work Sequence

### Approach: Parallel Subagent Dispatch + Incremental Completion

Infrastructure is built first (installer, dashboard, folder structure, website). Then the Playbook unlocks 5 parallel content subagents. Kyle writes non-delegable IP in parallel. Kyle reviews everything in batches. Final assembly and verification close out the MVP.

### Already Completed (as of April 12, 2026)

The following tasks are DONE and do not need to be repeated:

**Infrastructure (completed):**
- Tasks 1-6: Product Catalog folder structure created (56 directories, 12 files including shared assets, drafting templates, Maester instructions, voice reference, Attorney Review Checklist)
- Task 8: One-click installer built (2 Windows EXEs, ~11MB each; Parser Trial config + Full Suite config; Python + tkinter + PyInstaller; tested on Windows 11, skills verified in Claude Code; targets Claude Code Desktop App, not VS Code)
- Task 9: Kyle Review Dashboard built (FastAPI + vanilla HTML at localhost:5190; scans YAML frontmatter; FLAGGED section with reason tags; one-click approve/revision; email notification logged)
- Task 24: Website redesigned with full brand system (navy/brass/teal palette, Georgia serif, `< | >` logo, 2 product tiers, Arizona refs removed, Foundation updated to reflect consulting session model, example agents added to Custom Workflows)

**What these completed tasks produced:**
- Installer binaries: `Side Bar Code/installer/dist/sidebar-code-install-parser-trial.exe` and `sidebar-code-install-full-suite.exe`
- Review Dashboard: `Side Bar Code/review-dashboard/` (launch with `python server.py`, open localhost:5190)
- Folder structure: `Side Bar Code/Product Catalog/` with all 8 tier folders and sub-folders
- Website: `Side Bar Code/index.html` updated with brand + content changes (not yet pushed to GitHub)

### Remaining Work Sequence

**PHASE A: The Playbook (Kyle, ~3.5-5 hours across 2-4 sessions)**

This is the critical path blocker. Nothing else can move until this is done.

Kyle runs the 12-prompt interview sequence (Prompts 0-11) in a separate Claude Code session. The prompts are self-contained and produce a complete Playbook v1.0.

Key context the Playbook must reflect (refined during brainstorming):

Tier distinctions:
- Parser Trial ($197): One skill file. Self-serve. No support. Exists to get the product into the firm and create the "aha" moment.
- Full Litigation Suite ($2,997): All 4 skills + Integration Guide + CLAUDE.md starter. Self-serve. No support. The files-based product for self-directed attorneys.
- Foundation ($5-7.5K): Kyle shows up. 90-min session. ONE skill deployed on the firm's workflow (Kyle selects highest-impact skill). CLAUDE.md starter configured live. Technology Overview. 30-day email support. This is a consulting session, not a product delivery. The firm walks out with a working workflow and a trained team.
- Implementation ($10-15K): Kyle builds the system. All 4 skills configured. Custom CLAUDE.md with voice calibration + authority injection from firm's filings + Westlaw summaries. Memory bank. Workflow audit. 90-day support.
- Modernization ($25-40K): Kyle transforms the firm. Multi-agent architecture. Governance. CLE. 12-month quarterly check-ins.
- Custom Workflows ($5K-$25K): Bespoke agents for specific bottlenecks. Not the standard 4 skills; entirely new agents built for the firm's unique workflows.

Key distinctions to internalize:
- Full Suite sells files. Foundation sells Kyle in the room. Different buyers, different needs, both valid.
- A firm CAN buy both Full Suite AND Foundation. They solve different problems.
- Foundation deploys ONE skill (not all four). The upsell to Implementation is "you've seen what one skill can do; let me configure all four for your firm."
- No email support in ANY product tier. Support is paid consulting ($500/hr) or an upgrade to a consulting tier.
- No ethics advice documents. Technology Overview is a CYA disclosure, not a policy. Ethics training is consulting/CLE only.
- Jurisdiction-neutral nationally. No Arizona-specific content in any product.

Buyer signals to capture:
- Three people who reach out: associate (no authority, route to Parser Trial), senior partner (has authority for $5-15K, primary sales conversation), managing partner (full authority, rare inbound, propose specific tier on the call)
- Three reasons prospects say no: "we don't have time" (Foundation exists because Kyle does the work), "waiting for bar guidance" (firms that build governance now have an advantage when the mandate comes), "partners won't use it" (Kyle the litigator demonstrates the output, not the tool)
- Serious buyer signals: specific pain (not abstract interest), implementation questions (not feature questions), names a decision maker, brings up a timeline unprompted, reacts to pricing by asking about the next tier up

OUTPUT: `Product Catalog/_playbook/SALES_PLAYBOOK.md` + 5 extracted standalone files (POSITIONING_CORE.md, PRICING_LOGIC.md, TIER_BOUNDARIES.md, OBJECTION_HANDLING.md, INQUIRY_RESPONSE_TEMPLATES.md)

**PHASE B: Parallel Content Drafting (5 subagents, launched after Playbook is done)**

Once the Playbook is saved, dispatch 5 background subagents simultaneously. Each reads the Playbook and produces output to specific file paths.

Subagent 1, Maester-Catalog (autonomous):
- Draft all 8 tier what_is_in_the_box.md, customer_faq.md, inquiry_response.md
- Draft all 8 tier manifests with YAML frontmatter
- Generate CATALOG_INDEX.md and CATALOG_INDEX.yaml
- Foundation what_is_in_the_box.md must reflect: consulting session model, ONE skill deployed, Kyle in the room, 30-day support, NOT a product delivery
- Product tier docs must include no-support language
- OUTPUT: All _sales_packet/ folders populated

Subagent 2, Maester-Guide (autonomous):
- Draft Integration Guide Chapters A, B, K, L
- Chapter B is now 1 page: "Double-click the installer. Open Claude Code." (installer targets Desktop App, not VS Code)
- Draft Quick Start Card
- Draft Per-Skill Quick Reference (one page per skill)
- OUTPUT: 6 of 7 guide sections drafted

Subagent 3, Maester-Legal (autonomous):
- Draft all intake questionnaires with YAML intake_schema blocks for the 6 consulting + workflow tiers
- Foundation intake must include: firm size, practice areas, which skill to deploy (or let Kyle recommend), presentation format (on-site/Zoom), who will attend
- Draft all engagement letter templates (ALL tagged as FLAGGED [LEGAL_INSTRUMENT])
- Draft all scope of work templates
- Foundation SOW must reflect: 90-min session, one skill deployment, CLAUDE.md starter config, Technology Overview, 30-day support
- Draft Technology Overview and Limitations Guide
- OUTPUT: All intake_and_contracting/ folders populated

Subagent 4, Maester-Internal (autonomous):
- Draft all _internal/methodology.md files
- Foundation methodology must reflect: discovery call to identify best skill for the firm, customize 3-4 slides in the presentation deck, deliver session, deploy one skill live, configure starter CLAUDE.md, send Technology Overview within 48 hours, 30-day support window, Day 25 upsell check-in
- Draft all _internal/margins_and_time.md files
- Draft all _internal/upsell_paths.md files (including: Foundation -> Implementation trigger is "can you make this sound like our firm?")
- Draft Custom Workflow scoping guide
- Draft _ops/AGENT_PROTOCOLS.md
- Draft _ops/DEPLOYMENT_CHECKLIST.md
- OUTPUT: All _internal/ folders populated, _ops/ populated

Subagent 5, Catalog-Builder (autonomous):
- Build the /build-catalog-tier skill file
- Test by generating one sample tier folder
- OUTPUT: Working Catalog Builder skill at ~/.claude/commands/build-catalog-tier.md

**PHASE C: Kyle Non-Delegable Content (parallel with Phase B, ~12-18 Kyle hours)**

These can be worked on in any order. All are independent of the subagents.

Kyle Task 1: CLAUDE.md starter template + README (2-3 hours)
- The deliberately basic starter: 3 editable fields, review reminder, no-em-dashes rule, confidentiality note, upgrade path callout
- Ships with both Full Suite AND is configured live during Foundation sessions
- Save to: Product Catalog/products/02_full_litigation_suite/_customer_deliverables/claude_md_starter/

Kyle Task 2: Integration Guide Chapter J - Attorney Review, Ethics, Hallucinations (6-8 hours)
- Non-delegable liability content
- The mandatory review rule, hallucination catching checklist, confidentiality considerations, disclosure obligations (jurisdiction-neutral), supervision of AI-assisted work product
- 8-10 pages. Cannot be shortened.
- Save to: Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/

Kyle Task 3: Implementation tier internal methodology (4-6 hours)
- CLAUDE.md build methodology (crown jewel consulting IP, never shared)
- Workflow audit questionnaire (the structured interview with managing partner + lead associate)
- Memory bank build process (how to ingest firm filings + Westlaw summaries)
- Save to: Product Catalog/consulting/02_implementation/_internal/

Kyle Task 4: Foundation tier presentation deck outline (2-3 hours)
- Slide structure + speaker notes skeleton for the 90-minute session
- Must include: live demo section (15 min), "here's what the skill just did" walkthrough, Q&A facilitation notes, the 5-10 minute CLAUDE.md configuration segment, the "what comes next" soft upsell closing
- Full production deck is deep phase; outline is MVP
- Save to: Product Catalog/consulting/01_foundation/_customer_deliverables/

**PHASE D: Review, Revision, and Assembly (~8-14 Kyle hours)**

After Phases B and C are complete:

Kyle review (6-10 hours):
- Open Review Dashboard at localhost:5190
- Address FLAGGED items first (ethics, confidentiality, legal instruments)
- Batch review all sales packets (check voice, pricing accuracy, tier boundaries, no Arizona refs, no em dashes, no practice-area claims, Foundation reflects consulting session model not product delivery)
- Batch review Integration Guide chapters
- Batch review intake/contracting docs (verify Foundation intake includes skill selection and presentation format questions)
- Send engagement letters to Aemon for legal review
- Send revision notes back to subagent sessions or edit directly

Aemon: Review all 6 engagement letters + Terms of Service (if not already reviewed)

Kyle assembly (4-6 hours):
- Assemble Integration Guide v1.0 from all chapters (A, B, J, K, L + Quick Start Card + Per-Skill Quick Reference)
- Write sample outputs for consulting sales packets (redacted sample CLAUDE.md build for Implementation, sample project roadmap for Modernization)
- Copy skill files into product tier _customer_deliverables/ folders
- Copy installer binaries into product tier _customer_deliverables/ folders
- Generate final CATALOG_INDEX.md and CATALOG_INDEX.yaml
- Write _ops/HANDOFF_NOTES.md for sub-projects 2-4
- Push website update to GitHub (Render auto-deploys)

OUTPUT: MVP COMPLETE

### Revised Effort Summary (remaining work only)

| Person | Task | Hours |
|---|---|---|
| Kyle | Playbook (Phase A, prompt sequence) | 3.5-5 |
| Kyle | CLAUDE.md starter (Phase C) | 2-3 |
| Kyle | Integration Guide Ch J (Phase C) | 6-8 |
| Kyle | Implementation methodology (Phase C) | 4-6 |
| Kyle | Foundation presentation outline (Phase C) | 2-3 |
| Kyle | Review all subagent output (Phase D) | 6-10 |
| Kyle | Assembly and final polish (Phase D) | 4-6 |
| **Kyle total remaining** | | **28-41** |
| Subagents | 5 parallel content drafting sessions (Phase B) | 18-28 (compute) |
| Aemon | Engagement letter + ToS review | 5-7 |
| **Grand total remaining** | | **51-76** |

Previously completed (not counted above):
| Person | Task | Hours Spent |
|---|---|---|
| Subagent | Foundation infrastructure (Tasks 1-6) | ~4 |
| Khal | Installer (Task 8) | ~7 |
| Khal | Review Dashboard (Task 9) | ~6 |
| Subagent | Website redesign (Task 24) | ~3 |
| **Already done** | | **~20** |

### Dependencies (Updated)

```
Playbook (Phase A) -> All 5 content subagents (Phase B)
Phase B + Phase C both complete -> Phase D (review and assembly)
Engagement letters approved by Aemon -> Consulting tiers ready to close
Integration Guide assembled -> Full Suite _customer_deliverables/ complete
Website pushed to GitHub -> Render auto-deploys (sub-project 2 wires Stripe later)
```

### Critical Path (Updated)

Playbook (Phase A) -> Subagent drafts (Phase B, runs parallel with Phase C) -> Kyle review (Phase D) -> Assembly -> MVP COMPLETE

The Playbook remains the single blocker. Everything else either runs in parallel or is already done. If Kyle starts the Playbook today, the 5 content subagents launch the moment it is saved, and MVP can be complete within 2-2.5 weeks of the Playbook finishing.

---

## 6. Review Gates and Quality Standards

### Three Review Tiers

**Tier 1: Kyle Review (all external-facing content)**
Every document a prospect or customer could see. Kyle's question: "Would I be comfortable if a managing partner read this and judged my business by it?"

**Tier 2: Aemon Review (all legal instruments)**
Engagement letters, Terms of Service, Technology Overview and Limitations Guide, any SOW with indemnification language. Aemon's question: "Does this protect Kyle and Banfield Consulting, LLC?"

**Tier 3: Automated Quality Check (every document)**
Run by drafting agent or QA subagent before Kyle sees it:
- Em dash scan (zero tolerance)
- Practice-area expertise claim scan
- Disclaimer presence check
- YAML frontmatter validation
- Placeholder scan (no `{{PLACEHOLDER}}` in customer-facing docs)
- CHDB/Kyle/Aemon internal reference scan
- Arizona-specific content scan (should not appear in customer-facing docs except clearly marked examples)

### Review Status Tracking

Every document's YAML frontmatter:

```yaml
review_status: draft | pending_kyle_review | kyle_approved | pending_aemon_review | aemon_approved | revision_requested | final_approved
reviewed_by: null | kyle | aemon
reviewed_at: null | 2026-04-15
revision_notes: null | "specific revision note"
```

CATALOG_INDEX.yaml aggregates review status. Kyle Review Dashboard displays this.

### Kyle Review Dashboard

**Builder:** Khal (parallel with installer, Week 1)
**Purpose:** Simple web-based todo/review tracker showing Kyle what needs his eyes.
**Features:**
- List of all documents pending Kyle's review, grouped by tier
- Status badges: pending, approved, revision requested, blocked (waiting on Aemon)
- One-click approve/request-revision per document
- Filter by tier, by category (sales packet / deliverable / legal instrument)
- Updated automatically whenever a subagent produces output or Kyle approves something
- Shows overall catalog completion percentage

**Escalation protocol (FLAGGED items):**
- The dashboard has a visually distinct "FLAGGED" section at the top (red border, separate from routine items)
- Flagged items include a reason tag: `[ETHICS]`, `[CONFIDENTIALITY]`, `[LEGAL_INSTRUMENT]`, `[PRICING]`, `[LOW_CONFIDENCE]`
- Khal wires email notification to kyle@sidebarcode.com when a flagged item is added
- Every subagent's instructions include: "If your draft touches ethics, confidentiality, client data handling, or bar compliance, tag output as FLAGGED with reason. Do not mark as routine review."
- Flagged categories: any content discussing ethical obligations, any content about client confidentiality or data handling, any engagement letter or legal instrument, any pricing or scope representation, any LOW confidence assessment on legal questions

**Tech:** Lightweight. Can be a simple HTML page reading from the CATALOG_INDEX.yaml, or a small React component in the existing clawdbot-control-center. Khal decides implementation. Does not need to be production-grade; needs to be functional.

### Quality Standards (Non-Negotiable)

1. No em dashes anywhere
2. No practice-area expertise claims
3. Standard disclaimer on every customer-facing document
4. Practitioner-to-practitioner tone (not tech-evangelist, not condescending)
5. Active voice, short sentences
6. Lead with the legal problem, then the AI solution
7. No references to CHDB Law, Aemon, or internal agents in customer-facing docs
8. Jurisdiction-neutral throughout (no Arizona-specific content except clearly marked demo examples)
9. Every AI output example accompanied by attorney review reminder
10. No content that teaches buyers how to build what Sidebar Code sells
11. Every customer-facing document must make clear that Sidebar Code sells technology and workflow automation, not legal advice. The buyer's ethical obligations to verify the law, check citations, and review all AI output are the buyer's alone. No document may imply that purchasing Sidebar Code products satisfies any ethical obligation or substitutes for independent legal judgment.

---

## 7. Interfaces for Sub-Projects 2-4

### Interface to Sub-Project 2: Stripe + Delivery

Sub-project 2 reads from CATALOG_INDEX.yaml:

```yaml
products:
  - tier_id: product_parser_trial
    stripe_product_name: "Sidebar Code Parser Trial"
    price: 197
    delivery_type: zip_download
    delivery_source: "Product Catalog/products/01_parser_trial/_customer_deliverables/"
  - tier_id: product_full_suite
    stripe_product_name: "Sidebar Code Full Litigation Suite"
    price: 2997
    delivery_type: zip_download
    delivery_source: "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"

consulting:
  - tier_id: consulting_foundation
    delivery_type: notify_kyle
  # (same for implementation, modernization)

custom_workflows:
  - tier_id: workflow_single
    delivery_type: notify_kyle
  # (same for multi, practice_area)
```

Product tiers: Stripe webhook ZIPs _customer_deliverables/ and sends.
Consulting/workflow tiers: Stripe webhook notifies Kyle (email + CRM entry).

### Interface to Sub-Project 3: Steward

Steward reads:
- SALES_PLAYBOOK.md (primary knowledge base)
- Per-tier `_sales_packet/inquiry_response.md` (reply templates)
- Per-tier `intake_and_contracting/intake_questionnaire.md` YAML schemas (fields to collect)
- `_ops/AGENT_PROTOCOLS.md` (per-tier workflow documentation)
- CATALOG_INDEX.yaml (cold-start catalog snapshot, version tracking)

### Interface to Sub-Project 4: Scout/Raven/Herald

These agents read:
- Playbook Sections 8, 9 (objections, response patterns) for outreach content
- Per-tier `_sales_packet/what_is_in_the_box.md` for product descriptions
- Custom Workflow example agent list for lead-to-tier matching

### Handoff Document

When sub-project 1 completes, `_ops/HANDOFF_NOTES.md` documents:
- What was built and where everything lives
- What interfaces sub-projects 2-4 should consume
- What assumptions are safe (file naming, YAML schema, folder structure)
- What is NOT yet built (full consulting deliverables, CLE curriculum, practice-area packs)
- Known issues or rough edges

---

## Appendix A: Website Changes Queued

1. Product section: 2 tiers (Parser Trial $197 + Full Litigation Suite $2,997). Remove Single Skill, Litigation Trio.
2. Remove all Arizona jurisdiction references from product descriptions. Replace with "Jurisdiction-neutral; configurable for any state."
3. Foundation Package: remove "AI Usage Policy" bullet. Replace with "Technology Overview and Limitations Guide."
4. Update Custom Workflows section with example agent descriptions.
5. Update nav if needed (Skill Packs section name may need adjustment).

## Appendix B: Future Offerings (Post-MVP)

- Legal update monitoring agent (Custom Workflow)
- Practice-area skill packs (separate products)
- Jurisdiction modules (per-engagement, not products, unless demand proves otherwise)
- Foundation presentation deck (full production version, after first engagement)
- Integration Guide v1.1 (Chapters E-I, skill walkthroughs)
- Modernization governance framework (full version, after first engagement)
- CLE accreditation (Arizona State Bar provider application)

---

*End of spec. Version 1.0. Pending Kyle review.*
