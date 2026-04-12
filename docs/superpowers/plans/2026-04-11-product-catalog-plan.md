# Sidebar Code Product Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP product catalog for all 8 Sidebar Code tiers so Kyle can respond to any inquiry in 60 seconds and deliver on signed engagements without scrambling.

**Architecture:** Three parallel workstreams after the Playbook foundation is complete. Content workstream uses 5 dispatched subagents to draft all tier folders. Infrastructure workstream (Khal) builds the installer EXE and Review Dashboard. Website workstream updates the landing page. Kyle writes non-delegable IP content and reviews everything.

**Tech Stack:** Markdown with YAML frontmatter (content), Node.js or Python packaged as EXE (installer), React/HTML (dashboard), static HTML (website)

**Spec:** `docs/superpowers/specs/2026-04-11-product-catalog-design.md`

---

## File Structure

### New Files to Create

**Foundation Layer:**
```
Product Catalog/
  CATALOG_INDEX.md
  CATALOG_INDEX.yaml
  _playbook/
    SALES_PLAYBOOK.md
    POSITIONING_CORE.md
    PRICING_LOGIC.md
    OBJECTION_HANDLING.md
    TIER_BOUNDARIES.md
    INQUIRY_RESPONSE_TEMPLATES.md
  _maester_persona/
    MAESTER_INSTRUCTIONS.md
    DRAFTING_TEMPLATES/
      what_is_in_the_box_template.md
      intake_questionnaire_template.md
      scope_of_work_template.md
      engagement_letter_template.md
      customer_faq_template.md
    VOICE_REFERENCE/
      kyle_voice_samples.md
  shared/
    disclaimers/
      standard_disclaimer.md
      product_no_support_notice.md
    terms_of_service/
      terms_reference.md
    kyle_bio/
      kyle_bio_short.md
      kyle_bio_medium.md
      kyle_bio_long.md
  _ops/
    README.md
    DEPLOYMENT_CHECKLIST.md
    VERSION_LOG.md
    HANDOFF_NOTES.md
    AGENT_PROTOCOLS.md
```

**Per-Tier Folders (8 total, each with same sub-structure):**
```
products/01_parser_trial/
products/02_full_litigation_suite/
consulting/01_foundation/
consulting/02_implementation/
consulting/03_modernization/
custom_workflows/01_single_workflow/
custom_workflows/02_multi_agent/
custom_workflows/03_practice_area/
```

Each tier folder contains:
```
[tier]/
  tier_manifest.md
  _internal/
    methodology.md
    margins_and_time.md
    known_traps.md
    upsell_paths.md
  _sales_packet/
    what_is_in_the_box.md
    customer_faq.md
    inquiry_response.md
    one_page_overview.md
    sample_output.md          (consulting/workflow tiers only)
  _customer_deliverables/
    delivery_readme.md
    [tier-specific files]
  intake_and_contracting/     (consulting/workflow tiers only)
    intake_questionnaire.md
    engagement_letter.md
    scope_of_work_template.md
```

**Product-Tier-Specific Customer Deliverables:**
```
products/01_parser_trial/_customer_deliverables/
  pleading-parser.md          (copied from General Litigation/)
  INSTALLATION.md
  QUICK_START.md
  ATTORNEY_REVIEW_CHECKLIST.md
  TERMS_AND_LICENSE.md
  WHATS_NEXT.md
  README.md

products/02_full_litigation_suite/_customer_deliverables/
  skills/
    pleading-parser.md
    deposition-prep.md
    oral-argument-prep.md
    motion-drafting.md
  integration_guide/
    Sidebar_Code_Integration_Guide_v1.0.md
    Quick_Start_Card.md
  claude_md_starter/
    CLAUDE_starter_template.md
    CLAUDE_starter_README.md
  ATTORNEY_REVIEW_CHECKLIST.md
  TERMS_AND_LICENSE.md
  README.md
```

**Infrastructure:**
```
~/.claude/commands/build-catalog-tier.md     (Catalog Builder skill)
[Khal's project directory]/installer/        (EXE installer source)
[Khal's project directory]/review-dashboard/ (Review Dashboard source)
```

**Website:**
```
Side Bar Code/index.html                     (modify existing)
```

### Existing Files Referenced

```
Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/
  pleading-parser.md
  deposition-prep.md
  oral-argument-prep.md
  motion-drafting.md

Side Bar Code/SIDEBAR_CODE_FRAMEWORK.md
Side Bar Code/index.html
Side Bar Code/terms.html
```

---

## Phase 1: Foundation Infrastructure (Week 1, Days 1-2)

### Task 1: Create the Complete Folder Structure

**Files:**
- Create: All directories listed in the File Structure section above
- Create: `Product Catalog/_ops/README.md`

- [ ] **Step 1: Create the full directory tree**

```bash
cd "C:\Users\banfi\Projects\Sidebar Code\Side Bar Code"

# Top-level
mkdir -p "Product Catalog/_playbook"
mkdir -p "Product Catalog/_maester_persona/DRAFTING_TEMPLATES"
mkdir -p "Product Catalog/_maester_persona/VOICE_REFERENCE"
mkdir -p "Product Catalog/shared/disclaimers"
mkdir -p "Product Catalog/shared/terms_of_service"
mkdir -p "Product Catalog/shared/kyle_bio"
mkdir -p "Product Catalog/shared/logos_and_branding"
mkdir -p "Product Catalog/shared/legal_review_queue"
mkdir -p "Product Catalog/_ops"

# Product tiers
for tier in "products/01_parser_trial" "products/02_full_litigation_suite"; do
  mkdir -p "Product Catalog/$tier/_internal"
  mkdir -p "Product Catalog/$tier/_sales_packet"
  mkdir -p "Product Catalog/$tier/_customer_deliverables"
done

# Full Suite sub-folders
mkdir -p "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/skills"
mkdir -p "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide"
mkdir -p "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/claude_md_starter"

# Consulting tiers
for tier in "consulting/01_foundation" "consulting/02_implementation" "consulting/03_modernization"; do
  mkdir -p "Product Catalog/$tier/_internal"
  mkdir -p "Product Catalog/$tier/_sales_packet"
  mkdir -p "Product Catalog/$tier/_customer_deliverables"
  mkdir -p "Product Catalog/$tier/intake_and_contracting"
done

# Custom workflow tiers
for tier in "custom_workflows/01_single_workflow" "custom_workflows/02_multi_agent" "custom_workflows/03_practice_area"; do
  mkdir -p "Product Catalog/$tier/_internal"
  mkdir -p "Product Catalog/$tier/_sales_packet"
  mkdir -p "Product Catalog/$tier/_customer_deliverables"
  mkdir -p "Product Catalog/$tier/intake_and_contracting"
done
```

- [ ] **Step 2: Verify the folder structure**

```bash
find "Product Catalog" -type d | head -60
```

Expected: ~45-50 directories.

- [ ] **Step 3: Create the _ops README**

Write to `Product Catalog/_ops/README.md`:

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
cd "C:\Users\banfi\Projects\Sidebar Code\Side Bar Code"
git add "Product Catalog/"
git commit -m "feat: create product catalog folder structure for all 8 tiers"
```

---

### Task 2: Create Shared Assets

**Files:**
- Create: `Product Catalog/shared/disclaimers/standard_disclaimer.md`
- Create: `Product Catalog/shared/disclaimers/product_no_support_notice.md`
- Create: `Product Catalog/shared/terms_of_service/terms_reference.md`

- [ ] **Step 1: Write the standard disclaimer**

Write to `Product Catalog/shared/disclaimers/standard_disclaimer.md`:

```markdown
---
doc_type: shared_asset
asset_type: disclaimer
version: 1.0
last_updated: 2026-04-11
usage: Include verbatim in every customer-facing document
---

This product provides workflow automation templates and AI configuration guidance, not legal advice. All outputs must be reviewed and approved by a licensed attorney before use. Sidebar Code is a DBA of Banfield Consulting, LLC. Banfield Consulting, LLC is not a law firm and does not provide legal services. The buyer's ethical obligations to verify the law, check citations, and review all AI output are the buyer's alone. Purchasing Sidebar Code products does not satisfy any ethical obligation and does not substitute for independent legal judgment.
```

- [ ] **Step 2: Write the no-support notice for product tiers**

Write to `Product Catalog/shared/disclaimers/product_no_support_notice.md`:

```markdown
---
doc_type: shared_asset
asset_type: notice
version: 1.0
last_updated: 2026-04-11
usage: Include in product tier README and WHATS_NEXT documents
---

Sidebar Code product purchases are self-serve. Email support is not included with product purchases. If you need assistance with installation, configuration, or workflow integration, the following options are available:

- Hourly consulting: $500/hr, 2-hour minimum. Contact kyle@sidebarcode.com.
- Foundation Package ($5,000-$7,500): Includes a 90-minute implementation presentation, technology overview, and 30-day email support.
- Implementation Package ($10,000-$15,000): Includes custom CLAUDE.md configuration, workflow audit, memory bank setup, and 90-day priority support.

Visit sidebarcode.com for details on all consulting and custom workflow options.
```

- [ ] **Step 3: Write the terms reference**

Write to `Product Catalog/shared/terms_of_service/terms_reference.md`:

```markdown
---
doc_type: shared_asset
asset_type: legal_reference
version: 1.0
last_updated: 2026-04-11
usage: Reference in all TERMS_AND_LICENSE.md files across product tiers
---

# Terms of Service Reference

Full Terms of Service: https://sidebarcode.com/terms.html

Key provisions for product purchasers:
- Section 2: Firm-wide internal use license. Non-transferable. Non-sublicensable.
- Section 6: Mandatory attorney review of all AI-generated output before use.
- Section 10: Liability limited to purchase price paid in prior 12 months.
- Section 11: Buyer indemnifies Sidebar Code for all use of Licensed Materials.
- Section 13: Governed by Arizona law, Maricopa County venue.
```

- [ ] **Step 4: Commit**

```bash
git add "Product Catalog/shared/"
git commit -m "feat: add shared disclaimers, no-support notice, and terms reference"
```

---

### Task 3: Create the Attorney Review Checklist (Shared Across All Tiers)

**Files:**
- Create: `Product Catalog/shared/ATTORNEY_REVIEW_CHECKLIST.md`

- [ ] **Step 1: Write the checklist**

Write to `Product Catalog/shared/ATTORNEY_REVIEW_CHECKLIST.md`:

```markdown
---
doc_type: shared_asset
asset_type: checklist
version: 1.0
last_updated: 2026-04-11
usage: Include in every product tier _customer_deliverables/ folder. Print and attach to every AI-assisted work product file.
---

# Attorney Review Checklist
## Required Before Using Any AI-Generated Output

This checklist must be completed by a licensed attorney before any AI-generated output is filed, served, presented to a client, or otherwise used in any legal matter.

- [ ] I have independently verified every case citation in this output against an authoritative legal research platform
- [ ] I have confirmed every statutory reference is current and correctly cited
- [ ] I have verified every factual assertion against the record, exhibits, or source documents
- [ ] I have reviewed the applicable legal standard for my jurisdiction and confirmed the output applies the correct standard
- [ ] I have reviewed the confidence assessment at the end of the output and investigated all MODERATE and LOW confidence items
- [ ] I have checked for any factual or legal conclusions that appear plausible but are not supported by the record
- [ ] I understand that this output was generated by an AI and may contain errors, hallucinated citations, or misstatements of law
- [ ] I take full professional responsibility for any filing, communication, or work product based on this output
- [ ] I have complied with my jurisdiction's disclosure requirements regarding AI-assisted work product (if any)

**Signed:** ___________________________

**Date:** ___________________________

**Matter:** ___________________________

---

*Sidebar Code is a DBA of Banfield Consulting, LLC. Banfield Consulting, LLC is not a law firm and does not provide legal services. This checklist is a workflow tool, not legal advice.*
```

- [ ] **Step 2: Commit**

```bash
git add "Product Catalog/shared/ATTORNEY_REVIEW_CHECKLIST.md"
git commit -m "feat: add attorney review checklist for all product tiers"
```

---

### Task 4: Create the Voice Reference File

**Files:**
- Create: `Product Catalog/_maester_persona/VOICE_REFERENCE/kyle_voice_samples.md`

- [ ] **Step 1: Extract voice samples from existing documents**

Read the landing page (`Side Bar Code/index.html`) and the framework (`Side Bar Code/SIDEBAR_CODE_FRAMEWORK.md`) to extract 8-12 paragraphs that exemplify the Sidebar Code brand voice.

Write to `Product Catalog/_maester_persona/VOICE_REFERENCE/kyle_voice_samples.md`:

```markdown
---
doc_type: voice_reference
version: 1.0
last_updated: 2026-04-11
purpose: Read before drafting any customer-facing content. Match the sentence length, rhythm, verb choices, and tone.
---

# Kyle Banfield Voice Reference

## Brand Voice Samples

### From the Landing Page (Sales Voice)

**Hero headline:**
"I modernized a law firm in the age of AI. Here is how you can do the same."

**Consulting section intro:**
"Every engagement starts with a conversation about your practice, your associates, and the workflows that are eating your partners' time. Then we build the solution around that. These are not templates. They are firm-specific configurations."

**Custom workflows pitch:**
"Every firm has a handful of workflows that consume associate and paralegal hours in ways that do not show up on any billing ledger. Intake triage. Discovery review. Fee application drafting. These are the workflows where a purpose-built agent pays for itself in the first month."

**About section:**
"The difference between Sidebar Code and a legal tech vendor is simple. Kyle is not a tech consultant who learned law. He is a skilled litigator who also built the systems. He understands how to take a deposition, how insurance carriers evaluate billing, how a partner should review associate work product, and how to draft a motion under time pressure. He knows the business of law from the inside."

### From the Framework (Business-Thinking Voice)

**Market positioning:**
"Most managing partners of mid-sized litigation firms are making decisions about AI based on incomplete information. They think of it as a better Google search. They do not understand skill-based AI usage, agent systems, memory-based workflows, or how to build policies and procedures that protect the firm from ethics violations while capturing the efficiency gains. This is a massive education and implementation gap. Sidebar Code fills it."

**Target buyer psychology:**
"The selling conversation is not 'here is software.' It is 'here is what I built for my own firm and what it allowed us to do differently. Here is how I can help you do the same.'"

**Product durability:**
"Skill packs (not static prompt PDFs) are the product format because Claude Code's native capabilities advance rapidly. Static prompts commoditize as the platform evolves."

## Voice Rules

- Lead with the legal problem, then the AI solution
- Short sentences, active voice
- Practitioner-to-practitioner (not tech-evangelist, not condescending)
- No em dashes (use commas, semicolons, colons, or restructure)
- No generic AI hype ("game-changer," "revolutionize," "the future is here")
- Specific examples over generic claims
- No practice-area expertise claims
```

NOTE: When Kyle uploads his resume, add credential language samples to this file.

- [ ] **Step 2: Commit**

```bash
git add "Product Catalog/_maester_persona/"
git commit -m "feat: add voice reference samples for Maester persona"
```

---

### Task 5: Create the 5 Drafting Templates

**Files:**
- Create: `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/what_is_in_the_box_template.md`
- Create: `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/intake_questionnaire_template.md`
- Create: `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/scope_of_work_template.md`
- Create: `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/engagement_letter_template.md`
- Create: `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/customer_faq_template.md`

- [ ] **Step 1: Write the what_is_in_the_box template**

Write to `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/what_is_in_the_box_template.md`:

```markdown
---
doc_type: drafting_template
template_for: what_is_in_the_box
version: 1.0
instructions: Fill in all {{PLACEHOLDERS}} using the Sales Playbook as your source. Remove this frontmatter instructions block from the final output.
---

# {{TIER_NAME}}

---
tier_id: {{TIER_ID}}
tier_name: {{TIER_NAME}}
price_min: {{PRICE_MIN}}
price_max: {{PRICE_MAX}}
price_display: "{{PRICE_DISPLAY}}"
delivery_time_days: {{DELIVERY_DAYS}}
includes:
  {{INCLUDES_LIST}}
excludes:
  {{EXCLUDES_LIST}}
tier_above: {{TIER_ABOVE}}
tier_below: {{TIER_BELOW}}
upsell_path: {{UPSELL_PATH}}
status: draft
last_updated: {{DATE}}
reviewed_by: null
review_status: pending_kyle_review
drafted_by: maester_persona
---

## What You Get

{{ONE_PARAGRAPH_ELEVATOR_PITCH}}

## The Problem This Solves

{{ONE_PARAGRAPH_PAIN_POINT}}

## What Is Included

{{BULLETED_LIST_OF_DELIVERABLES}}

## What Is NOT Included at This Tier

{{BULLETED_LIST_OF_EXCLUSIONS_WITH_UPSELL_PATHS}}

## Pricing

{{PRICE_DISPLAY}}

{{PRICING_CONTEXT_ONE_SENTENCE}}

## Delivery

{{DELIVERY_TIMELINE_AND_PROCESS}}

## Next Steps

{{HOW_TO_PURCHASE_OR_INQUIRE}}

---

*{{STANDARD_DISCLAIMER}}*
```

- [ ] **Step 2: Write the intake questionnaire template**

Write to `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/intake_questionnaire_template.md`:

```markdown
---
doc_type: drafting_template
template_for: intake_questionnaire
version: 1.0
instructions: Customize the intake_schema fields per tier. Keep core fields (firm_name through timeline). Add tier-specific fields as needed. Remove this instructions block from final output.
---

---
tier_id: {{TIER_ID}}
doc_type: intake_questionnaire
status: draft
last_updated: {{DATE}}
review_status: pending_kyle_review
drafted_by: maester_persona
intake_schema:
  - field: firm_name
    type: string
    required: true
  - field: firm_size_attorneys
    type: integer
    required: true
  - field: practice_areas
    type: array
    required: true
  - field: decision_maker_name
    type: string
    required: true
  - field: decision_maker_email
    type: string
    required: true
  - field: primary_concern
    type: enum
    options: [efficiency, competitive_pressure, associate_training, carrier_requirements, workflow_bottleneck, firm_transformation]
    required: true
  - field: preferred_timeline
    type: enum
    options: [asap, 30_days, 60_days, 90_days, exploratory]
    required: true
  - field: budget_confirmed
    type: boolean
    required: true
  {{TIER_SPECIFIC_FIELDS}}
---

# {{TIER_NAME}} Intake Questionnaire

Use this questionnaire during the discovery call. Estimated time: 15-20 minutes.

## Firm Profile

1. What is your firm's name?
2. How many attorneys are at your firm?
3. What are your primary practice areas?

## Decision Maker

4. Who is the decision maker for this engagement? (Name and title)
5. What is the best email to reach them?

## Needs Assessment

6. What is your primary concern or motivation for exploring AI workflow integration?
   - [ ] Efficiency and time savings
   - [ ] Competitive pressure from other firms
   - [ ] Associate training and development
   - [ ] Insurance carrier requirements
   - [ ] Specific workflow bottleneck
   - [ ] Firm-wide transformation
   - [ ] Other: ___________

{{TIER_SPECIFIC_QUESTIONS}}

## Timeline and Commitment

7. What is your preferred timeline for starting?
   - [ ] As soon as possible
   - [ ] Within 30 days
   - [ ] Within 60 days
   - [ ] Within 90 days
   - [ ] Exploratory (no timeline)

8. Has budget been approved or discussed for this engagement?
   - [ ] Yes
   - [ ] No, needs approval
   - [ ] Exploring options first
```

- [ ] **Step 3: Write the scope of work template**

Write to `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/scope_of_work_template.md`:

```markdown
---
doc_type: drafting_template
template_for: scope_of_work
version: 1.0
instructions: Customize per engagement. All {{PLACEHOLDERS}} must be filled before sending to client. Remove this instructions block from final output.
---

---
tier_id: {{TIER_ID}}
doc_type: scope_of_work
status: draft
last_updated: {{DATE}}
review_status: pending_kyle_review
drafted_by: maester_persona
---

# Scope of Work
## {{TIER_NAME}}
## Prepared for: {{CLIENT_FIRM_NAME}}

**Date:** {{DATE}}
**Prepared by:** Kyle Banfield, Sidebar Code (Banfield Consulting, LLC)

---

### 1. Engagement Overview

{{ENGAGEMENT_DESCRIPTION_2_3_SENTENCES}}

### 2. Deliverables

{{NUMBERED_LIST_OF_SPECIFIC_DELIVERABLES}}

### 3. Explicitly Out of Scope

The following items are not included in this engagement:

{{BULLETED_LIST_OF_EXCLUSIONS}}

These items are available through separate engagements. Contact kyle@sidebarcode.com for details.

### 4. Timeline and Milestones

| Milestone | Target Date | Deliverable |
|---|---|---|
| {{MILESTONE_1}} | {{DATE}} | {{DELIVERABLE}} |
| {{MILESTONE_2}} | {{DATE}} | {{DELIVERABLE}} |
| {{MILESTONE_3}} | {{DATE}} | {{DELIVERABLE}} |

### 5. Client Responsibilities

To ensure successful delivery, {{CLIENT_FIRM_NAME}} will:

{{BULLETED_LIST_OF_CLIENT_OBLIGATIONS}}

### 6. Acceptance Criteria

Each deliverable is considered accepted when:

{{BULLETED_LIST_OF_ACCEPTANCE_CRITERIA}}

### 7. Investment

{{PRICE_AND_PAYMENT_TERMS}}

### 8. Terms

This Scope of Work is governed by the Engagement Letter executed between Banfield Consulting, LLC (DBA Sidebar Code) and {{CLIENT_FIRM_NAME}}. In the event of any conflict between this Scope of Work and the Engagement Letter, the Engagement Letter controls.

---

*This product provides workflow automation templates and AI configuration guidance, not legal advice.*
```

- [ ] **Step 4: Write the engagement letter template**

Write to `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/engagement_letter_template.md`:

```markdown
---
doc_type: drafting_template
template_for: engagement_letter
version: 1.0
instructions: >
  CRITICAL: Every engagement letter MUST be reviewed by Aemon before use.
  Tag as FLAGGED [LEGAL_INSTRUMENT] in the Review Dashboard.
  Customize all {{PLACEHOLDERS}} per engagement.
  Do not modify the indemnification, limitation of liability, or governing law sections without Aemon review.
  Remove this instructions block from final output.
---

---
tier_id: {{TIER_ID}}
doc_type: engagement_letter
status: draft
last_updated: {{DATE}}
review_status: pending_aemon_review
drafted_by: maester_persona
flagged: true
flagged_reason: LEGAL_INSTRUMENT
---

# Engagement Letter

**Date:** {{DATE}}

**To:** {{CLIENT_NAME}}, {{CLIENT_TITLE}}
{{CLIENT_FIRM_NAME}}
{{CLIENT_ADDRESS}}

**From:** Kyle Banfield
Banfield Consulting, LLC (DBA Sidebar Code)
kyle@sidebarcode.com

**Re:** {{TIER_NAME}} Engagement

---

Dear {{CLIENT_NAME}},

Thank you for choosing Sidebar Code for your AI workflow integration needs. This letter confirms the terms of our engagement.

### 1. Scope of Services

Banfield Consulting, LLC (DBA Sidebar Code) will provide the following services as described in the attached Scope of Work:

{{DELIVERABLES_SUMMARY}}

### 2. Disclaimer and Scope Limitation

This product provides workflow automation templates and AI configuration guidance, not legal advice. All outputs generated using these tools must be reviewed and approved by a licensed attorney before use. Sidebar Code is a DBA of Banfield Consulting, LLC. Banfield Consulting, LLC is not a law firm and does not provide legal services.

Kyle Banfield is providing AI integration consulting services. This engagement does not guarantee the accuracy of any output produced by any AI platform, including Claude Code. The accuracy, legal sufficiency, and ethical compliance of all AI-assisted work product remain the sole responsibility of the licensed attorneys at {{CLIENT_FIRM_NAME}}.

### 3. Investment and Payment

{{PRICE_AND_PAYMENT_SCHEDULE}}

Payment is required before any work begins or any scheduling is confirmed. No calendar access is provided until payment is confirmed.

### 4. Indemnification

{{CLIENT_FIRM_NAME}} agrees to indemnify, defend, and hold harmless Banfield Consulting, LLC, Kyle Banfield individually, and their affiliates from and against any claims, damages, losses, liabilities, costs, or expenses arising from or related to {{CLIENT_FIRM_NAME}}'s use of the deliverables, any work product produced using the deliverables, or any filing or representation made based on AI-generated output.

### 5. Authorization for Anonymized Use

{{CLIENT_FIRM_NAME}} authorizes Banfield Consulting, LLC to use anonymized process insights, implementation frameworks, and general learnings from this engagement for content generation and external case studies. No client-identifying information, matter-specific details, or confidential data will be disclosed.

### 6. Limitation of Liability

Banfield Consulting, LLC's total liability for any claim arising from this engagement is limited to the amount paid by {{CLIENT_FIRM_NAME}} under this engagement letter. In no event will Banfield Consulting, LLC be liable for indirect, incidental, special, consequential, or punitive damages.

### 7. Governing Law

This engagement letter is governed by the laws of the State of Arizona. Any dispute will be resolved exclusively in the state or federal courts located in Maricopa County, Arizona.

### 8. Acceptance

Please sign and return this letter to confirm your acceptance of these terms. Upon receipt of this signed letter and confirmed payment, we will begin work per the attached Scope of Work.

**BANFIELD CONSULTING, LLC (DBA SIDEBAR CODE)**

By: ___________________________
Kyle Banfield
Date: ___________________________

**{{CLIENT_FIRM_NAME}}**

By: ___________________________
{{CLIENT_NAME}}, {{CLIENT_TITLE}}
Date: ___________________________
```

- [ ] **Step 5: Write the customer FAQ template**

Write to `Product Catalog/_maester_persona/DRAFTING_TEMPLATES/customer_faq_template.md`:

```markdown
---
doc_type: drafting_template
template_for: customer_faq
version: 1.0
instructions: Generate 10-15 questions specific to this tier. Use the Sales Playbook Section 5 (Per-Tier Positioning) as the source for answers. Every answer must be 2-4 sentences. No em dashes. No practice-area claims. Remove this instructions block from final output.
---

---
tier_id: {{TIER_ID}}
tier_name: {{TIER_NAME}}
doc_type: customer_faq
status: draft
last_updated: {{DATE}}
review_status: pending_kyle_review
drafted_by: maester_persona
---

# {{TIER_NAME}} - Frequently Asked Questions

## About the {{TIER_CATEGORY}}

**Q: {{QUESTION_ABOUT_WHAT_THIS_IS}}**

A: {{ANSWER}}

**Q: {{QUESTION_ABOUT_WHO_THIS_IS_FOR}}**

A: {{ANSWER}}

**Q: {{QUESTION_ABOUT_WHAT_IS_INCLUDED}}**

A: {{ANSWER}}

## Pricing and Purchase

**Q: {{QUESTION_ABOUT_PRICING}}**

A: {{ANSWER}}

**Q: {{QUESTION_ABOUT_REFUNDS_OR_GUARANTEES}}**

A: {{ANSWER}}

## Using the {{TIER_CATEGORY}}

**Q: {{QUESTION_ABOUT_GETTING_STARTED}}**

A: {{ANSWER}}

**Q: {{QUESTION_ABOUT_COMMON_CONCERN}}**

A: {{ANSWER}}

## Upgrade Paths

**Q: {{QUESTION_ABOUT_WHAT_COMES_NEXT}}**

A: {{ANSWER}}

**Q: {{QUESTION_ABOUT_DIFFERENCE_FROM_HIGHER_TIER}}**

A: {{ANSWER}}

---

*{{STANDARD_DISCLAIMER}}*
```

- [ ] **Step 6: Commit**

```bash
git add "Product Catalog/_maester_persona/DRAFTING_TEMPLATES/"
git commit -m "feat: add 5 Maester drafting templates for tier content generation"
```

---

### Task 6: Create the Maester Persona Instructions File

**Files:**
- Create: `Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md`

- [ ] **Step 1: Write the Maester instructions**

Write to `Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md`:

```markdown
---
doc_type: agent_persona_instructions
persona_name: maester
version: 1.0
last_updated: 2026-04-11
invocation_pattern: Load this file at the start of a Claude Code session when drafting product catalog content.
---

# Maester Persona: Product Catalog Content Drafter

## Who You Are

You are Maester, the Sidebar Code content creation persona. You draft product catalog content: what's-in-the-box docs, intake questionnaires, engagement letter drafts, customer FAQs, sample outputs, and one-page overviews. You work from the Sales Playbook as your voice and positioning source. You never improvise on pricing, scope, or boundaries.

You are NOT a real agent with dispatch or approval infrastructure. You are a session-level persona that Kyle invokes in a Claude Code session for focused content drafting work.

## What You Do (Scope)

1. Draft `what_is_in_the_box.md` files for any tier (use template: `DRAFTING_TEMPLATES/what_is_in_the_box_template.md`)
2. Draft `customer_faq.md` files for any tier (use template: `DRAFTING_TEMPLATES/customer_faq_template.md`)
3. Draft `inquiry_response.md` first-touch email templates for any tier
4. Draft `intake_questionnaire.md` files with YAML intake_schema (use template: `DRAFTING_TEMPLATES/intake_questionnaire_template.md`)
5. Draft `engagement_letter.md` shells (use template: `DRAFTING_TEMPLATES/engagement_letter_template.md`) - ALWAYS tag as FLAGGED [LEGAL_INSTRUMENT]
6. Draft `scope_of_work_template.md` files (use template: `DRAFTING_TEMPLATES/scope_of_work_template.md`)
7. Draft `_internal/methodology.md`, `margins_and_time.md`, `upsell_paths.md` files
8. Draft `tier_manifest.md` files with YAML frontmatter
9. Draft `one_page_overview.md` summary documents

## What You Do NOT Do (Hard Limits)

- Never claim expertise in any legal practice area
- Never draft buildable CLAUDE.md templates (held for consulting)
- Never draft multi-agent blueprints or orchestration designs
- Never draft complete governance frameworks
- Never draft custom skill authoring instructions
- Never finalize engagement letters (Aemon reviews all legal instruments)
- Never publish or deliver anything; output goes to Kyle for review
- Never use em dashes; use commas, semicolons, colons, or restructure
- Never invent pricing that contradicts the Playbook
- Never interpret tier boundaries; if ambiguous, ask Kyle
- Never imply that purchasing Sidebar Code satisfies any ethical obligation
- Never provide legal advice or suggest that any document constitutes legal advice

## Your Source Documents (Read These First)

1. `Product Catalog/_playbook/SALES_PLAYBOOK.md` (voice, positioning, tier details)
2. `Product Catalog/_playbook/TIER_BOUNDARIES.md` (what's held for consulting)
3. `Product Catalog/_playbook/POSITIONING_CORE.md` (non-negotiable rules)
4. `Side Bar Code/SIDEBAR_CODE_FRAMEWORK.md` (business context)
5. `Side Bar Code/terms.html` (legal terms as reference)
6. `Product Catalog/_maester_persona/VOICE_REFERENCE/kyle_voice_samples.md` (voice matching)

## Your Output Format

All drafts include a YAML frontmatter block with:
- tier_id
- doc_type
- status: draft
- drafted_by: maester_persona
- drafted_at: [date]
- review_status: pending_kyle_review
- flagged: true/false
- flagged_reason: [ETHICS | CONFIDENTIALITY | LEGAL_INSTRUMENT | PRICING | LOW_CONFIDENCE] (if flagged)

## Your Escalation Triggers

Stop drafting and ask Kyle for direction if:
- The Playbook does not cover the tier or question you are working on
- The template leaves a placeholder that requires business judgment
- You find a contradiction between the framework and the Playbook
- A draft would require claiming practice-area expertise
- You need to reference legal authority you cannot verify
- The content touches ethics, confidentiality, client data handling, or bar compliance (tag as FLAGGED)
- You are unsure whether content leaks consulting-reserved IP

## Confidence Assessment (Required for Every Draft)

At the end of every draft, include:

**HIGH CONFIDENCE:** [statements directly supported by Playbook/framework]
**MODERATE:** [reasonable inferences from source material]
**LOW:** [judgment calls that need Kyle's review]
**INFORMATION I WISH I HAD:** [what would have made this draft better]
```

- [ ] **Step 2: Commit**

```bash
git add "Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md"
git commit -m "feat: add Maester persona instructions for catalog content drafting"
```

---

## Phase 2: The Sales Playbook (Week 1, Days 2-5)

### Task 7: Kyle Writes the Sales Playbook

**Files:**
- Create: `Product Catalog/_playbook/SALES_PLAYBOOK.md`

This task is non-delegable. Kyle runs the 11-prompt interview sequence documented in the brainstorming session. The prompts are self-contained and produce a complete Playbook v1.0.

- [ ] **Step 1: Open a new Claude Code session in the Sidebar Code project directory**

- [ ] **Step 2: Upload Kyle's resume (PDF) to the session**

- [ ] **Step 3: Run Prompt 0 (Session Setup) through Prompt 4**

These produce Sections 1-4 of the Playbook: Core Narrative, Who We Are, Target Buyer, 8-Tier At a Glance.

Estimated time: 60-90 minutes.

- [ ] **Step 4: Run Prompt 5 (Per-Tier Positioning)**

This is the longest prompt. Kyle answers 3-5 questions per tier, 8 times. Claude drafts each profile.

Estimated time: 45-60 minutes.

- [ ] **Step 5: Run Prompts 6-8 (Pricing Logic, Tier Boundaries, Objection Handling)**

Kyle answers interview questions about pricing philosophy, discounting, and common objections.

Estimated time: 45-60 minutes.

- [ ] **Step 6: Run Prompts 9-10 (Inquiry Patterns, Voice Rules)**

Mostly distillation work. Claude drafts quickly.

Estimated time: 20-30 minutes.

- [ ] **Step 7: Run Prompt 11 (Final Assembly)**

Claude assembles all sections, adds YAML frontmatter, runs quality checks.

Output saved to: `Product Catalog/_playbook/SALES_PLAYBOOK.md`

- [ ] **Step 8: Kyle reviews the assembled Playbook**

Read the full document. Edit anything that does not sound like Kyle's voice. Verify pricing is correct. Verify tier boundaries match the spec.

- [ ] **Step 9: Extract supporting Playbook files**

From the completed Playbook, extract the following into standalone files for agent consumption:
- Section 2 content -> `Product Catalog/_playbook/POSITIONING_CORE.md`
- Section 6 content -> `Product Catalog/_playbook/PRICING_LOGIC.md`
- Section 7 content -> `Product Catalog/_playbook/TIER_BOUNDARIES.md`
- Section 8 content -> `Product Catalog/_playbook/OBJECTION_HANDLING.md`
- Section 9 content -> `Product Catalog/_playbook/INQUIRY_RESPONSE_TEMPLATES.md`

Each file gets its own YAML frontmatter with `doc_type`, `version`, `last_updated`, and `agent_access` fields.

- [ ] **Step 10: Commit**

```bash
git add "Product Catalog/_playbook/"
git commit -m "feat: complete Sales Playbook v1.0 with all 10 sections"
```

---

## Phase 3: Parallel Infrastructure (Week 1, runs alongside Phase 2)

### Task 8: Khal Builds the One-Click Installer

**Files:**
- Create: Installer project directory (Khal's choice of location)
- Output: `sidebar-code-install.exe` (Windows) + `sidebar-code-install.app` or `.dmg` (Mac)

This task is dispatched to Khal as a subagent. Full prompt for Khal:

- [ ] **Step 1: Dispatch Khal with the following brief**

```
You are Khal Drogo, the engineering agent. Build a one-click installer for 
Sidebar Code skill files that targets the Claude Code Desktop App (NOT VS Code).

REQUIREMENTS:
1. Windows EXE + Mac app/dmg
2. Two configurations controlled by a config file in the ZIP:
   - Parser Trial: installs only pleading-parser.md
   - Full Suite: installs all 4 skills + CLAUDE_starter_template.md
3. On launch, show a simple welcome screen: "Sidebar Code Installer"
4. Check if ~/.claude/commands/ exists. Create it if not.
5. Copy skill files from a bundled /skills/ directory to ~/.claude/commands/
6. For Full Suite: also copy CLAUDE_starter_template.md to the current
   working directory (or prompt user for location)
7. Show success screen: "Installation complete. Open Claude Code and type /
   to see your new commands."
8. No Terminal/command line visible to the user at any point
9. No internet connection required (fully offline installer)

TECH CHOICES:
- Electron (cross-platform, simple UI) OR
- Python + PyInstaller (lighter weight, no Chromium) OR
- Node.js + pkg (minimal, CLI-wrapped with a GUI launcher)
- Your choice. Optimize for smallest download size and simplest user experience.

SKILL FILES TO BUNDLE:
- C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Firm Prompts Content\Skills Dat Pay da Bills\General Litigation\pleading-parser.md
- C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Firm Prompts Content\Skills Dat Pay da Bills\General Litigation\deposition-prep.md
- C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Firm Prompts Content\Skills Dat Pay da Bills\General Litigation\oral-argument-prep.md
- C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Firm Prompts Content\Skills Dat Pay da Bills\General Litigation\motion-drafting.md

TEST:
- Test on a clean Windows machine (no Claude Code pre-installed; installer
  should detect this and show "Please install Claude Code first" with a link)
- Test on a machine WITH Claude Code installed; verify skills appear when
  typing / in Claude Code
- Test both Parser Trial and Full Suite configurations

OUTPUT:
- Working installer binaries
- Place source code in a sensible project directory
- Report back with: binary sizes, tested platforms, any issues found
```

- [ ] **Step 2: Kyle tests the installer on his machine**

Verify: double-click EXE, skills install, Claude Code shows `/parser` when typing `/`.

- [ ] **Step 3: Copy verified installer binaries to customer deliverables**

```bash
# After installer is verified
cp [installer-path]/sidebar-code-install.exe "Product Catalog/products/01_parser_trial/_customer_deliverables/"
cp [installer-path]/sidebar-code-install.exe "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"
```

---

### Task 9: Khal Builds the Kyle Review Dashboard

**Files:**
- Create: Dashboard project directory (Khal's choice)
- Output: Working web-based review tracker

- [ ] **Step 1: Dispatch Khal with the following brief**

```
You are Khal Drogo. Build a lightweight Kyle Review Dashboard for the 
Sidebar Code product catalog.

PURPOSE:
Kyle needs to see at a glance: what documents need his review, what has been
approved, what is blocked on Aemon, and what is FLAGGED for sensitive content.

REQUIREMENTS:
1. Web-based (runs locally or on the existing dashboard infrastructure)
2. Reads review status from YAML frontmatter in catalog files OR from a 
   central tracking file (CATALOG_INDEX.yaml)
3. Shows:
   - FLAGGED section at the top (red border, visually distinct)
     - Each flagged item shows: file name, tier, reason tag 
       ([ETHICS] [CONFIDENTIALITY] [LEGAL_INSTRUMENT] [PRICING] [LOW_CONFIDENCE])
   - Pending Kyle Review section
   - Pending Aemon Review section
   - Approved section (collapsible)
   - Overall completion percentage
4. Per item: file name, tier name, document type, status badge, last updated
5. One-click approve button (updates the YAML frontmatter in the file)
6. One-click "request revision" button (adds revision note to frontmatter)
7. Filter by: tier, category (sales_packet / deliverable / legal_instrument)
8. Email notification to kyle@sidebarcode.com when a FLAGGED item is added
   (use a simple SMTP send or log to a notification queue that Kyle checks)

CATALOG ROOT:
C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Product Catalog\

TECH:
- Can be a React component in the existing clawdbot-control-center OR
- A standalone HTML page with vanilla JS that scans the catalog folder
- Your choice. Optimize for "works in 2 days" not "production-grade."

TEST:
- Create 3 sample tier_manifest.md files with different review statuses
- Verify the dashboard renders them correctly
- Verify the approve button updates the YAML frontmatter
- Verify a FLAGGED item appears in the flagged section
```

- [ ] **Step 2: Kyle reviews the dashboard and provides feedback**

- [ ] **Step 3: Khal iterates based on feedback**

---

## Phase 4: Parallel Subagent Content Drafting (Week 2)

**DEPENDENCY: Tasks 10-14 cannot start until Task 7 (Playbook) is complete.**

All 5 subagents launch simultaneously at the start of Week 2. Each reads the Playbook and produces output to specific file paths. Kyle reviews in batch during Week 3.

### Task 10: Dispatch Subagent 1 (Maester-Catalog)

**Output files:** All 8 tier `_sales_packet/` folders populated + tier manifests + CATALOG_INDEX

- [ ] **Step 1: Dispatch the Maester-Catalog subagent**

Dispatch a background agent with this prompt:

```
You are Maester-Catalog, a content drafting agent for Sidebar Code.

READ THESE FILES FIRST:
1. Product Catalog/_playbook/SALES_PLAYBOOK.md
2. Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md
3. Product Catalog/_maester_persona/VOICE_REFERENCE/kyle_voice_samples.md
4. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/what_is_in_the_box_template.md
5. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/customer_faq_template.md
6. Product Catalog/shared/disclaimers/standard_disclaimer.md
7. Side Bar Code/docs/superpowers/specs/2026-04-11-product-catalog-design.md (Section 4 for tier details)

YOUR TASK:
For each of the 8 tiers listed below, create the following files in the correct folder:

1. tier_manifest.md (with full YAML frontmatter per spec Section 2)
2. _sales_packet/what_is_in_the_box.md (from template, filled with Playbook content)
3. _sales_packet/customer_faq.md (from template, 10-15 questions per tier)
4. _sales_packet/inquiry_response.md (pre-written first-touch email reply)
5. _sales_packet/one_page_overview.md (1-page summary)

THE 8 TIERS:
- products/01_parser_trial ($197)
- products/02_full_litigation_suite ($2,997)
- consulting/01_foundation ($5,000-$7,500)
- consulting/02_implementation ($10,000-$15,000)
- consulting/03_modernization ($25,000-$40,000)
- custom_workflows/01_single_workflow ($5,000)
- custom_workflows/02_multi_agent ($10,000)
- custom_workflows/03_practice_area ($15,000-$25,000)

After all 8 tiers are complete, generate:
- Product Catalog/CATALOG_INDEX.md (human-readable index of all tiers)
- Product Catalog/CATALOG_INDEX.yaml (machine-readable index with all tier metadata, catalog_version: 1)

QUALITY CHECKS (run before reporting done):
- grep for em dashes (-- or -) in all output files; replace any found
- grep for "expert in" or "specialize in" or "our expertise" in all files; remove
- verify every file has valid YAML frontmatter
- verify standard disclaimer appears in every customer-facing file
- verify no references to CHDB, Aemon, or Arizona-specific content

VOICE: Match the samples in kyle_voice_samples.md exactly.

FLAG any content that touches ethics, confidentiality, or bar compliance as:
  flagged: true
  flagged_reason: [ETHICS | CONFIDENTIALITY]

Report when complete with: files created count, any quality check failures, any escalation items.
```

- [ ] **Step 2: Verify output exists**

```bash
find "Product Catalog" -name "what_is_in_the_box.md" | wc -l
```

Expected: 8 files.

---

### Task 11: Dispatch Subagent 2 (Maester-Guide)

**Output files:** Integration Guide chapters A, B, K, L + Quick Start Card + Per-Skill Quick Reference

- [ ] **Step 1: Dispatch the Maester-Guide subagent**

Dispatch a background agent with this prompt:

```
You are Maester-Guide, a content drafting agent for Sidebar Code.

READ THESE FILES FIRST:
1. Product Catalog/_playbook/SALES_PLAYBOOK.md
2. Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md
3. Product Catalog/_maester_persona/VOICE_REFERENCE/kyle_voice_samples.md
4. Side Bar Code/Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/pleading-parser.md
5. Side Bar Code/Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/deposition-prep.md
6. Side Bar Code/Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/oral-argument-prep.md
7. Side Bar Code/Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/motion-drafting.md
8. Side Bar Code/Firm Prompts Content/Skills Dat Pay da Bills/INTEGRATION_GUIDE_PLAN.md
9. Side Bar Code/docs/superpowers/specs/2026-04-11-product-catalog-design.md

YOUR TASK:
Draft the following Integration Guide chapters. Save all files to:
Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/

Files to create:

1. Chapter_A_What_This_Is.md (3-4 pages)
   - What Claude Code is, in attorney language
   - What the four Sidebar Code skills are (one sentence each)
   - What this product is NOT (not legal advice, not a replacement for judgment)
   - System requirements
   - "You are ready to install if..." checklist

2. Chapter_B_Installation.md (1-2 pages)
   - "Double-click the installer. Follow the prompts."
   - What to do if Claude Code is not installed (link to Anthropic download)
   - How to verify: type / in Claude Code, confirm you see the four commands
   - One screenshot placeholder: [SCREENSHOT: Claude Code slash command picker]

3. Chapter_K_Troubleshooting.md (3-4 pages)
   - "Installer won't run" fixes
   - "Skills don't appear" fixes (restart Claude Code, check file location)
   - "Output quality is low" (give the skill more context, re-run)
   - "Document is too large" (split into sections)
   - When to contact Sidebar Code (install problems only; everything else is paid consulting or upgrade)

4. Chapter_L_Upgrade_Paths.md (4-6 pages)
   - What the Full Suite gives you (recap)
   - What it does NOT give you (firm voice calibration, practice-area authority injection, multi-agent coordination, governance framework, custom skills, ongoing updates beyond 12 months)
   - The consulting tiers in plain language: Foundation, Implementation, Modernization
   - Custom Agent Workflows: Single, Multi, Practice-Area with examples
   - How to engage: kyle@sidebarcode.com
   - "Full Suite versus Consulting" comparison table

5. Quick_Start_Card.md (1-2 pages)
   - Step 1: Run the installer
   - Step 2: Open Claude Code, type /
   - Step 3: Try /parser on your next pleading
   - Four skills at a glance (two-column table)
   - Attorney review reminder

6. Per_Skill_Quick_Reference.md (4-8 pages, one page per skill)
   For each of the 4 skills:
   - What it does (2 sentences)
   - When to use it (3 bullet points)
   - What to feed it (input requirements)
   - What to expect (output description)
   - What to review before using the output (skill-specific review items)

DO NOT WRITE Chapter J (Attorney Review and Ethics). Kyle writes that personally.

QUALITY CHECKS: Same as Maester-Catalog (em dashes, expertise claims, disclaimer, YAML frontmatter).

VOICE: Practitioner-to-practitioner. The reader is an attorney, not a developer. Do not explain what a deposition is. Do explain what Claude Code is.

Report when complete with: files created, page count per file, any quality check failures.
```

---

### Task 12: Dispatch Subagent 3 (Maester-Legal)

**Output files:** All intake questionnaires, engagement letters, SOWs, and the Technology Overview

- [ ] **Step 1: Dispatch the Maester-Legal subagent**

Dispatch a background agent with this prompt:

```
You are Maester-Legal, a content drafting agent for Sidebar Code.

READ THESE FILES FIRST:
1. Product Catalog/_playbook/SALES_PLAYBOOK.md
2. Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md
3. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/intake_questionnaire_template.md
4. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/engagement_letter_template.md
5. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/scope_of_work_template.md
6. Product Catalog/shared/disclaimers/standard_disclaimer.md
7. Side Bar Code/terms.html
8. Side Bar Code/docs/superpowers/specs/2026-04-11-product-catalog-design.md (Sections 4.2, 4.3 for tier details)

YOUR TASK:

1. For EACH of the 6 consulting + custom workflow tiers, create:
   - intake_and_contracting/intake_questionnaire.md (with YAML intake_schema block, customized per tier)
   - intake_and_contracting/engagement_letter.md (from template, customized per tier)
   - intake_and_contracting/scope_of_work_template.md (from template, customized per tier)

   The 6 tiers:
   - consulting/01_foundation
   - consulting/02_implementation
   - consulting/03_modernization
   - custom_workflows/01_single_workflow
   - custom_workflows/02_multi_agent
   - custom_workflows/03_practice_area

2. Create the Technology Overview and Limitations Guide:
   Save to: Product Catalog/consulting/01_foundation/_customer_deliverables/tech_overview_and_limitations.md

   Sections:
   a. What the technology is (Claude Code, skill files, how AI generates output, what "probabilistic" means in plain language)
   b. Known limitations (hallucinated citations, factual errors, jurisdiction confusion, outdated law, confident-when-wrong tendency)
   c. Attorney's independent obligation (verify all citations, factual assertions, and legal conclusions; Sidebar Code does not provide legal advice; use of any AI platform without understanding the technology is on the attorney; purchasing this product does not satisfy any ethical obligation)

   This is a TECHNOLOGY DISCLOSURE, not an ethics policy. Do not advise firms on what is or is not ethically permissible. That is their bar's job.

CRITICAL: Tag ALL engagement letters as:
  flagged: true
  flagged_reason: LEGAL_INSTRUMENT
These MUST be reviewed by Aemon before use.

Tag the Technology Overview as:
  flagged: true
  flagged_reason: ETHICS
Kyle must review this personally.

QUALITY CHECKS: Same as other Maester agents.

Report when complete with: files created, any flagged items, any escalation items.
```

---

### Task 13: Dispatch Subagent 4 (Maester-Internal)

**Output files:** All `_internal/` folders, scoping guide, ops docs

- [ ] **Step 1: Dispatch the Maester-Internal subagent**

Dispatch a background agent with this prompt:

```
You are Maester-Internal, a content drafting agent for Sidebar Code.

READ THESE FILES FIRST:
1. Product Catalog/_playbook/SALES_PLAYBOOK.md
2. Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md
3. Side Bar Code/docs/superpowers/specs/2026-04-11-product-catalog-design.md (all of Section 4 for tier details, Section 5 for work sequence, Section 7 for interfaces)

YOUR TASK:

1. For EACH of the 8 tiers, create:
   - _internal/methodology.md (Kyle's step-by-step delivery process for this tier)
   - _internal/margins_and_time.md (revenue, Kyle hours, margin percentage, unit economics)
   - _internal/upsell_paths.md (what this tier feeds into, trigger for the upsell, pitch language)
   - _internal/known_traps.md (common problems, buyer confusion points, things that go wrong)

   Use the spec Section 4 for the specific methodology steps, margins, and upsell triggers per tier.

2. Create the Custom Workflow Scoping Guide:
   Save to: Product Catalog/custom_workflows/SCOPING_GUIDE.md

   Decision tree:
   - One workflow, one skill -> Single ($5,000)
   - 2-3 workflows with handoffs -> Multi ($10,000)
   - Entire practice area -> Practice-Area ($15,000-$25,000)
   - Needs firm-wide governance/CLE -> Redirect to Modernization

   Include 4-5 example workflows per tier from the spec.

3. Create operational documents:
   - Product Catalog/_ops/AGENT_PROTOCOLS.md
     Per-tier agent workflow: "When inquiry arrives for [tier], Steward reads [file], collects [fields], routes to [next step]"
   - Product Catalog/_ops/DEPLOYMENT_CHECKLIST.md
     Steps to publish catalog updates to sub-projects 2-4
   - Product Catalog/_ops/VERSION_LOG.md
     Initialize with v1.0 entry

THESE ARE INTERNAL DOCUMENTS. They do not need the standard disclaimer. They should be written in a direct, operational tone. No marketing language.

QUALITY CHECKS: Verify all YAML frontmatter is valid. Verify pricing matches spec.

Report when complete with: files created count, any pricing discrepancies found.
```

---

### Task 14: Dispatch Subagent 5 (Catalog-Builder)

**Output files:** The `/build-catalog-tier` skill file

- [ ] **Step 1: Dispatch the Catalog-Builder subagent**

Dispatch a background agent with this prompt:

```
You are a skill file builder. Create a Claude Code slash command skill that 
generates a complete tier folder for the Sidebar Code product catalog.

READ THESE FILES FIRST:
1. Product Catalog/_maester_persona/MAESTER_INSTRUCTIONS.md (voice and rules)
2. Product Catalog/_maester_persona/DRAFTING_TEMPLATES/ (all 5 templates)
3. Side Bar Code/docs/superpowers/specs/2026-04-11-product-catalog-design.md (Section 2 for folder structure, Section 4 for tier details)

CREATE THIS FILE:
~/.claude/commands/build-catalog-tier.md

THE SKILL MUST:

1. Ask the user for these inputs:
   - tier_id (e.g., "consulting_new_tier")
   - tier_name (e.g., "Advanced Configuration Package")
   - tier_category: product | consulting | custom_workflow
   - price_min and price_max
   - delivery_time_days
   - includes (comma-separated list of deliverables)
   - excludes (comma-separated list of exclusions)
   - upsell_path (tier_id of the next tier up)
   - tier_above and tier_below (adjacent tiers)

2. Create the complete tier folder at the correct path:
   Product Catalog/[category]/[tier_folder_name]/
   With all sub-folders: _internal/, _sales_packet/, _customer_deliverables/, intake_and_contracting/ (if consulting or workflow)

3. Generate these files from the templates:
   - tier_manifest.md (with all YAML frontmatter fields populated)
   - _sales_packet/what_is_in_the_box.md
   - _sales_packet/customer_faq.md (10 questions)
   - _sales_packet/inquiry_response.md
   - _sales_packet/one_page_overview.md
   - _internal/methodology.md (stub)
   - _internal/margins_and_time.md (stub)
   - _internal/upsell_paths.md
   - intake_and_contracting/intake_questionnaire.md (with YAML intake_schema, if consulting/workflow)
   - _customer_deliverables/delivery_readme.md (stub)

4. Read the Sales Playbook for voice and positioning context

5. Run quality checks on all generated files (em dashes, expertise claims, disclaimer)

6. Report what was created and flag anything that needs Kyle's review

TEST THE SKILL by generating a sample tier:
   tier_id: consulting_test_tier
   tier_name: Test Configuration Package
   tier_category: consulting
   price_min: 3000
   price_max: 5000

Verify the generated folder has the correct structure and all files have valid YAML frontmatter.

After testing, DELETE the test tier folder.

Save the skill to: ~/.claude/commands/build-catalog-tier.md
```

---

## Phase 5: Kyle Non-Delegable Content (Week 2-3, parallel with Phase 4)

### Task 15: Kyle Writes the CLAUDE.md Starter Template

**Files:**
- Create: `Product Catalog/products/02_full_litigation_suite/_customer_deliverables/claude_md_starter/CLAUDE_starter_template.md`
- Create: `Product Catalog/products/02_full_litigation_suite/_customer_deliverables/claude_md_starter/CLAUDE_starter_README.md`

- [ ] **Step 1: Write the starter template**

Write to `CLAUDE_starter_template.md`:

```markdown
# Sidebar Code Starter Configuration

## Firm Information
# Replace the values below with your firm's information.
# Do not modify any other section of this file.

Firm Name: {{FIRM_NAME}}
Jurisdiction: {{JURISDICTION}}
Signing Attorney: {{SIGNING_ATTORNEY_NAME_AND_BAR_NUMBER}}

## Standards

All AI-generated output must be reviewed and approved by a licensed attorney before use in any legal matter. No output may be filed, served, or presented to a client without attorney review.

Do not use em dashes in any generated text. Use commas, semicolons, colons, or restructure the sentence.

## Confidentiality

Do not include client-identifying information, matter numbers, or confidential case details in prompts unless you have confirmed that doing so complies with your firm's data handling policies and any applicable client consent requirements.

## Review Reminder

Before using any output from a Sidebar Code skill:
- Verify all case citations against an authoritative legal research platform
- Confirm all factual assertions against the record
- Check that the applicable legal standard is correct for your jurisdiction
- Review the confidence assessment at the end of every skill output

---

*For a fully configured CLAUDE.md tuned to your firm's voice, practice areas, and governance standards, contact Sidebar Code about the Implementation Package. kyle@sidebarcode.com*
```

- [ ] **Step 2: Write the starter README**

Write to `CLAUDE_starter_README.md`:

```markdown
# CLAUDE.md Starter Template

## What This File Does

This file tells Claude Code basic information about your firm and establishes ground rules for AI-generated output. Claude Code reads it at the start of every session.

## How to Use It

1. Open CLAUDE_starter_template.md in any text editor
2. Replace {{FIRM_NAME}} with your firm's name
3. Replace {{JURISDICTION}} with your primary jurisdiction (e.g., "Arizona" or "California")
4. Replace {{SIGNING_ATTORNEY_NAME_AND_BAR_NUMBER}} with the signing attorney's name and bar number
5. Save the file as CLAUDE.md (remove "_starter_template" from the name)
6. Place it in the root folder where you run Claude Code

## What This Starter Deliberately Does NOT Include

The following require a consulting engagement to configure properly:
- Firm voice and writing style calibration
- Practice-area-specific guidance and authority injection
- Court-specific standing order awareness
- Full firm governance rules
- Multi-matter memory architecture
- Agent coordination rules

These are available through the Implementation Package ($10,000-$15,000) or the CLAUDE.md Build add-on ($3,000). Contact kyle@sidebarcode.com.
```

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/claude_md_starter/"
git commit -m "feat: add CLAUDE.md starter template and README for Full Suite"
```

---

### Task 16: Kyle Writes Integration Guide Chapter J (Ethics and Review)

**Files:**
- Create: `Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Chapter_J_Attorney_Review.md`

This is non-delegable liability content. Kyle writes it personally.

- [ ] **Step 1: Write Chapter J**

Content requirements (from spec Section 4.1, Full Litigation Suite):
- The mandatory review rule: every output must be reviewed by a licensed attorney
- Why this is not optional: bar trajectory on AI disclosure, sanctions cases
- Reading the confidence assessment: HIGH/MODERATE/LOW interpretation
- Hallucination catching checklist: citation verification, record cite verification, factual assertion verification
- Confidentiality and client data: where data goes when fed to Claude Code, API retention policies
- Disclosure obligations: jurisdiction-neutral, "INSERT YOUR JURISDICTION'S RULE HERE"
- Supervision of AI-assisted work product: partners supervising associates, associates supervising staff
- The printable Attorney Review Checklist (reference the shared checklist)

Target: 8-10 pages. This is the liability firewall. Do not abbreviate.

- [ ] **Step 2: Quality check**

```bash
grep -n "—\|–" "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Chapter_J_Attorney_Review.md"
```

Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Chapter_J_Attorney_Review.md"
git commit -m "feat: add Integration Guide Chapter J (ethics, review, hallucinations)"
```

---

### Task 17: Kyle Writes Implementation Tier Internal Methodology

**Files:**
- Create: `Product Catalog/consulting/02_implementation/_internal/claude_md_build_methodology.md`
- Create: `Product Catalog/consulting/02_implementation/_internal/workflow_audit_questionnaire.md`

- [ ] **Step 1: Write the CLAUDE.md build methodology**

This is crown jewel consulting IP. Document Kyle's actual process:
1. Interview the managing partner (30 min): firm voice, practice emphasis, supervision expectations
2. Interview the lead associate (30 min): daily workflow, common tasks, tool frustrations
3. Review 3-5 recent filings for voice calibration
4. Ingest Westlaw summaries for authority library (1-2 hours per practice area)
5. Build the CLAUDE.md: firm identity, practice-area rules, voice calibration, jurisdiction-specific authority injection, approval requirements, ethical guardrails
6. Test with 2-3 real prompts from the firm's recent work
7. Iterate and deliver

YAML frontmatter:
```yaml
---
doc_type: internal_methodology
tier_id: consulting_implementation
classification: consulting_ip_never_share
last_updated: 2026-04-XX
---
```

- [ ] **Step 2: Write the workflow audit questionnaire**

The structured interview Kyle uses with managing partner + lead associate:
- Current workflow mapping (intake through trial prep)
- Time allocation per phase
- Pain points per phase
- AI opportunity identification per phase
- Prioritized recommendations

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/consulting/02_implementation/_internal/"
git commit -m "feat: add Implementation tier internal methodology (CLAUDE.md build + workflow audit)"
```

---

## Phase 6: Copy Skill Files to Customer Deliverables (Week 2)

### Task 18: Populate Product Tier Customer Deliverables

**Files:**
- Copy: Templatized skill files into customer deliverables folders
- Create: Product-tier-specific docs (INSTALLATION, QUICK_START, TERMS_AND_LICENSE, WHATS_NEXT, README)

- [ ] **Step 1: Copy skill files to Parser Trial**

```bash
cp "Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/pleading-parser.md" \
   "Product Catalog/products/01_parser_trial/_customer_deliverables/"
```

- [ ] **Step 2: Copy skill files to Full Suite**

```bash
cp "Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/pleading-parser.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/skills/"
cp "Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/deposition-prep.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/skills/"
cp "Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/oral-argument-prep.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/skills/"
cp "Firm Prompts Content/Skills Dat Pay da Bills/General Litigation/motion-drafting.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/skills/"
```

- [ ] **Step 3: Copy shared assets to both product tiers**

```bash
for tier in "products/01_parser_trial" "products/02_full_litigation_suite"; do
  cp "Product Catalog/shared/ATTORNEY_REVIEW_CHECKLIST.md" \
     "Product Catalog/$tier/_customer_deliverables/"
done
```

- [ ] **Step 4: Write INSTALLATION.md (shared across product tiers)**

Write to `Product Catalog/products/01_parser_trial/_customer_deliverables/INSTALLATION.md`:

```markdown
---
doc_type: customer_deliverable
tier_id: product_parser_trial
version: 1.0
last_updated: 2026-04-XX
---

# Installation

1. Double-click `sidebar-code-install.exe` (Windows) or `sidebar-code-install.app` (Mac)
2. If you do not have Claude Code installed, the installer will prompt you to download it from Anthropic
3. Follow the installer prompts. Installation takes less than 30 seconds.
4. Open Claude Code (the desktop application from Anthropic)
5. Type `/` and confirm you see your new Sidebar Code command(s) in the list

If the installer does not run, see the Troubleshooting section in the Quick Start guide or contact kyle@sidebarcode.com for paid consulting assistance.
```

Copy to Full Suite as well:
```bash
cp "Product Catalog/products/01_parser_trial/_customer_deliverables/INSTALLATION.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"
```

- [ ] **Step 5: Write TERMS_AND_LICENSE.md**

Write to `Product Catalog/products/01_parser_trial/_customer_deliverables/TERMS_AND_LICENSE.md`:

```markdown
---
doc_type: customer_deliverable
tier_id: product_parser_trial
version: 1.0
---

# Terms and License

## License

This product is licensed to the purchasing firm for unlimited internal use by its attorneys and staff. This license is perpetual, non-exclusive, non-transferable, and non-sublicensable.

You may not resell, redistribute, sublicense, or share this product with any other law firm, legal practice, or individual outside the purchasing firm.

## Full Terms of Service

https://sidebarcode.com/terms.html

## Disclaimer

This product provides workflow automation templates and AI configuration guidance, not legal advice. All outputs must be reviewed and approved by a licensed attorney before use. Sidebar Code is a DBA of Banfield Consulting, LLC. Banfield Consulting, LLC is not a law firm and does not provide legal services.

## Support

This is a self-serve product. Email support is not included. For assistance, the following paid options are available:

- Hourly consulting: $500/hr, 2-hour minimum
- Foundation Package: $5,000-$7,500 (includes 30-day email support)
- Implementation Package: $10,000-$15,000 (includes 90-day priority support)

Contact: kyle@sidebarcode.com
```

Copy to Full Suite:
```bash
cp "Product Catalog/products/01_parser_trial/_customer_deliverables/TERMS_AND_LICENSE.md" \
   "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"
```

- [ ] **Step 6: Write Parser Trial QUICK_START.md**

Write to `Product Catalog/products/01_parser_trial/_customer_deliverables/QUICK_START.md`:

```markdown
---
doc_type: customer_deliverable
tier_id: product_parser_trial
version: 1.0
---

# Quick Start: Pleading Parser

## What You Just Installed

The Pleading Parser is a Claude Code skill that analyzes legal pleadings. Feed it a complaint, motion, MSJ, or answer, and it produces a structured analysis: claims asserted, elements required, apparent weaknesses, available defenses, and strategic implications.

## Your First Run

1. Open Claude Code
2. Type `/parser`
3. When prompted, provide a pleading (paste the text or reference a file)
4. Review the structured output

## What to Feed It

The Parser works best with:
- Complaints and petitions
- Motions to dismiss
- Motions for summary judgment (and responses)
- Answers with affirmative defenses
- Court orders and rulings

## What to Expect

The Parser produces:
- Document classification (what type of pleading it is)
- Legal issues presented (numbered list)
- Claims or arguments analyzed (per-claim breakdown)
- Apparent weaknesses identified
- A confidence assessment (HIGH / MODERATE / LOW)

## Before You Use the Output

Review the Attorney Review Checklist included in this package. Every output must be independently verified by a licensed attorney before use.

## What Comes Next

You have one of four Sidebar Code litigation skills. The complete set includes:
- Deposition Preparation Outline Generator
- Oral Argument Preparation Protocol
- Motion and Pleading Drafting Protocol

The Full Litigation Suite ($2,997) includes all four skills plus an Integration Guide and a CLAUDE.md starter template. Visit sidebarcode.com for details.
```

- [ ] **Step 7: Write Parser Trial WHATS_NEXT.md**

Write to `Product Catalog/products/01_parser_trial/_customer_deliverables/WHATS_NEXT.md`:

```markdown
---
doc_type: customer_deliverable
tier_id: product_parser_trial
version: 1.0
---

# What Comes Next

You have seen what one Sidebar Code skill can do. Here is what the full toolkit looks like.

## Full Litigation Suite ($2,997)

All four litigation skills, an Integration Guide, and a CLAUDE.md starter template:
- Pleading Parser (you have this)
- Deposition Preparation Outline Generator
- Oral Argument Preparation Protocol
- Motion and Pleading Drafting Protocol

## Consulting Engagements

For firms ready for hands-on integration:
- Foundation Package ($5,000-$7,500): Technology overview, implementation presentation, 30-day support
- Implementation Package ($10,000-$15,000): Custom CLAUDE.md build, workflow audit, memory bank setup, 90-day support
- Modernization Engagement ($25,000-$40,000): Full firm transformation with multi-agent architecture and governance

## Custom Agent Workflows

For firms with a specific bottleneck:
- Single Workflow Agent ($5,000): One custom agent for one workflow
- Multi-Agent Workflow ($10,000): 2-3 coordinated agents
- Practice-Area Workflow ($15,000-$25,000): End-to-end automation for an entire practice area

## Contact

kyle@sidebarcode.com
sidebarcode.com
```

- [ ] **Step 8: Write README files for both product tiers**

Parser Trial README:
```markdown
# Sidebar Code Parser Trial

Welcome. Here is what is in this package:

1. **INSTALLATION.md** - Start here. Run the installer.
2. **QUICK_START.md** - How to use the Pleading Parser on your first matter.
3. **pleading-parser.md** - The skill file (installed automatically by the installer).
4. **ATTORNEY_REVIEW_CHECKLIST.md** - Required review before using any output. Print this.
5. **TERMS_AND_LICENSE.md** - Your license and the Terms of Service.
6. **WHATS_NEXT.md** - The full Sidebar Code product and consulting catalog.

Start with INSTALLATION.md. Then read QUICK_START.md. Then try /parser on your next pleading.
```

Full Suite README:
```markdown
# Sidebar Code Full Litigation Suite

Welcome. Here is what is in this package:

1. **INSTALLATION.md** - Start here. Run the installer.
2. **integration_guide/** - The Integration Guide and Quick Start Card.
3. **skills/** - All four skill files (installed automatically by the installer).
4. **claude_md_starter/** - A starter CLAUDE.md template for your firm.
5. **ATTORNEY_REVIEW_CHECKLIST.md** - Required review before using any output. Print this.
6. **TERMS_AND_LICENSE.md** - Your license and the Terms of Service.

Start with INSTALLATION.md. Then read the Quick Start Card in the integration_guide folder. Then open the full Integration Guide when you are ready to go deeper.
```

- [ ] **Step 9: Commit**

```bash
git add "Product Catalog/products/"
git commit -m "feat: populate product tier customer deliverables with skill files and docs"
```

---

## Phase 7: Review, Revision, and Assembly (Week 3-4)

### Task 19: Kyle Reviews All Subagent Output

- [ ] **Step 1: Open the Kyle Review Dashboard**

Check for FLAGGED items first. Address any `[ETHICS]`, `[CONFIDENTIALITY]`, or `[LEGAL_INSTRUMENT]` flags before reviewing routine items.

- [ ] **Step 2: Batch review sales packets**

Read all 8 `what_is_in_the_box.md` files sequentially. Check for:
- Voice consistency (does it sound like Kyle?)
- Pricing accuracy (does it match the spec?)
- Tier boundary accuracy (does it promise anything held for consulting?)
- Disclaimer presence
- No em dashes
- No practice-area expertise claims
- No Arizona-specific content

Approve or request revision on each.

- [ ] **Step 3: Batch review FAQs and inquiry responses**

Same checks as sales packets.

- [ ] **Step 4: Review Integration Guide chapters (A, B, K, L)**

Read in order. Check for completeness, voice, accuracy, and the installer-based workflow.

- [ ] **Step 5: Review intake questionnaires**

Verify YAML intake_schema blocks have correct field types and required flags.

- [ ] **Step 6: Send engagement letters to Aemon**

Route all 6 engagement letter templates to Aemon for legal review:

```
Route to Aemon for review:
- consulting/01_foundation/intake_and_contracting/engagement_letter.md
- consulting/02_implementation/intake_and_contracting/engagement_letter.md
- consulting/03_modernization/intake_and_contracting/engagement_letter.md
- custom_workflows/01_single_workflow/intake_and_contracting/engagement_letter.md
- custom_workflows/02_multi_agent/intake_and_contracting/engagement_letter.md
- custom_workflows/03_practice_area/intake_and_contracting/engagement_letter.md

Also route for review:
- Side Bar Code/terms.html (if not already reviewed)
- consulting/01_foundation/_customer_deliverables/tech_overview_and_limitations.md
```

- [ ] **Step 7: Send revision notes to subagent sessions or revise directly**

For each document with requested revisions, either re-dispatch the relevant Maester subagent with specific revision notes, or edit the file directly.

- [ ] **Step 8: Commit approved content**

```bash
git add "Product Catalog/"
git commit -m "feat: Kyle review pass complete on all subagent-drafted content"
```

---

### Task 20: Assemble the Integration Guide

**Files:**
- Create: `Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Sidebar_Code_Integration_Guide_v1.0.md`

- [ ] **Step 1: Combine all chapters into one document**

Assemble in order:
1. Cover page (title, version, date, disclaimer)
2. Table of contents
3. Chapter A: What This Is
4. Chapter B: Installation
5. Chapter J: Attorney Review, Ethics, and Hallucinations
6. Chapter K: Troubleshooting
7. Chapter L: Upgrade Paths
8. Per-Skill Quick Reference
9. Changelog (empty for v1.0)

- [ ] **Step 2: Run quality checks on the assembled guide**

```bash
# Em dash check
grep -n "—\|–" "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Sidebar_Code_Integration_Guide_v1.0.md"

# Practice-area expertise check
grep -in "expert in\|specialize in\|our expertise\|we are experts" "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Sidebar_Code_Integration_Guide_v1.0.md"

# CHDB reference check
grep -in "CHDB\|Aemon\|banfield89" "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/Sidebar_Code_Integration_Guide_v1.0.md"
```

Expected: no matches for any check.

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/integration_guide/"
git commit -m "feat: assemble Integration Guide v1.0 from all chapters"
```

---

### Task 21: Write Sample Outputs for Consulting Sales Packets

**Files:**
- Create: `Product Catalog/consulting/02_implementation/_sales_packet/sample_output.md`
- Create: `Product Catalog/consulting/03_modernization/_sales_packet/sample_output.md`

- [ ] **Step 1: Write a redacted sample CLAUDE.md build for Implementation**

Show the STRUCTURE of what a fully configured CLAUDE.md looks like (section headings, types of rules) without revealing the actual methodology. 1-2 pages. Enough to show "this is sophisticated and firm-specific" without teaching the reader how to build one.

- [ ] **Step 2: Write a sample project roadmap for Modernization**

Show a 60-90 day Modernization engagement timeline with phases, milestones, and deliverables. 1 page. Enough to show "this is a structured, professional engagement."

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/consulting/"
git commit -m "feat: add sample outputs for Implementation and Modernization sales packets"
```

---

### Task 22: Generate the Final CATALOG_INDEX

**Files:**
- Update: `Product Catalog/CATALOG_INDEX.yaml`
- Update: `Product Catalog/CATALOG_INDEX.md`

- [ ] **Step 1: Generate CATALOG_INDEX.yaml with all 8 tiers**

Scan all tier_manifest.md files and aggregate into the central index. Include review status from YAML frontmatter.

```yaml
---
catalog_version: 1
last_updated: 2026-04-XX
total_tiers: 8
---

products:
  - tier_id: product_parser_trial
    tier_name: Parser Trial
    price: 197
    delivery_type: zip_download
    delivery_source: "Product Catalog/products/01_parser_trial/_customer_deliverables/"
    status: mvp_complete
    review_status: final_approved

  - tier_id: product_full_suite
    tier_name: Full Litigation Suite
    price: 2997
    delivery_type: zip_download
    delivery_source: "Product Catalog/products/02_full_litigation_suite/_customer_deliverables/"
    status: mvp_complete
    review_status: final_approved

consulting:
  - tier_id: consulting_foundation
    tier_name: Foundation Package
    price_min: 5000
    price_max: 7500
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved

  - tier_id: consulting_implementation
    tier_name: Implementation Package
    price_min: 10000
    price_max: 15000
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved

  - tier_id: consulting_modernization
    tier_name: Modernization Engagement
    price_min: 25000
    price_max: 40000
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved

custom_workflows:
  - tier_id: workflow_single
    tier_name: Single Workflow Agent
    price: 5000
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved

  - tier_id: workflow_multi
    tier_name: Multi-Agent Workflow
    price: 10000
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved

  - tier_id: workflow_practice_area
    tier_name: Practice-Area Workflow
    price_min: 15000
    price_max: 25000
    delivery_type: notify_kyle
    status: mvp_scaffold
    review_status: final_approved
```

- [ ] **Step 2: Generate CATALOG_INDEX.md**

Human-readable version of the same index, with links to each tier's manifest file.

- [ ] **Step 3: Commit**

```bash
git add "Product Catalog/CATALOG_INDEX.*"
git commit -m "feat: generate catalog index with all 8 tiers"
```

---

### Task 23: Write the Handoff Notes for Sub-Projects 2-4

**Files:**
- Create: `Product Catalog/_ops/HANDOFF_NOTES.md`

- [ ] **Step 1: Write the handoff document**

Document:
- What was built and where everything lives
- File naming conventions and YAML schema contracts
- What sub-project 2 (Stripe) should read from CATALOG_INDEX.yaml
- What sub-project 3 (Steward) should read (Playbook, inquiry_response.md files, intake schemas, AGENT_PROTOCOLS.md)
- What sub-project 4 (Scout/Raven/Herald) should read (Playbook Sections 8-9, what_is_in_the_box.md files)
- What is NOT yet built (full consulting deliverables, CLE, practice-area packs)
- Known issues or rough edges in the MVP

- [ ] **Step 2: Commit**

```bash
git add "Product Catalog/_ops/HANDOFF_NOTES.md"
git commit -m "feat: add handoff notes for sub-projects 2-4"
```

---

### Task 24: Update the Website

**Files:**
- Modify: `Side Bar Code/index.html`

- [ ] **Step 1: Update the product section**

Replace the current 3-tier product section with 2 tiers:
- Parser Trial ($197)
- Full Litigation Suite ($2,997)

Remove the Litigation Trio card entirely.

- [ ] **Step 2: Remove Arizona jurisdiction references**

Search for "Arizona" in the product descriptions. Replace "Arizona jurisdiction module" with "Jurisdiction-neutral; configurable for any state."

- [ ] **Step 3: Update the Foundation Package description**

Remove "AI Usage Policy, firm-branded and ready to adopt" bullet.
Replace with "Technology Overview and Limitations Guide."

- [ ] **Step 4: Update the Custom Workflows section**

Add example agent descriptions to each workflow tier card.

- [ ] **Step 5: Quality check**

```bash
grep -in "arizona" "Side Bar Code/index.html" | grep -v "Arizona Bar"
grep -n "AI Usage Policy" "Side Bar Code/index.html"
grep -n "—\|–" "Side Bar Code/index.html"
```

Expected: no matches (except "Arizona Bar No. 037717" in Kyle's bio, which stays).

- [ ] **Step 6: Commit and push**

```bash
cd "Side Bar Code"
git add index.html
git commit -m "feat: update website with 2-tier products, remove Arizona refs, update Foundation"
git push origin main
```

---

### Task 25: Final MVP Verification

- [ ] **Step 1: Verify all success criteria from the spec**

Run through each criterion:

1. Can Kyle answer any inquiry for any tier in 60 seconds? Open each tier_manifest.md and time it.
2. Are product tier deliverables complete? Check both `_customer_deliverables/` folders have all files.
3. Do consulting tiers have intake, engagement letter, SOW, and sales packet? Check all 3.
4. Do custom workflow tiers have scoping guide, SOW, and sales packet? Check all 3.
5. Is the Playbook complete with all 10 sections? Open and verify.
6. Does the Catalog Builder skill exist and work? Run `/build-catalog-tier` with test inputs.
7. Has ToS been reviewed by Aemon? Check review status.
8. Can the catalog migrate to sub-project 2? Verify CATALOG_INDEX.yaml has delivery_source paths.
9. Does the Review Dashboard track pending items? Open and verify.
10. Do all customer-facing documents pass quality standards? Run automated checks.

- [ ] **Step 2: Run the full quality check suite**

```bash
# Em dash check across all customer-facing content
find "Product Catalog" -name "*.md" -path "*/_sales_packet/*" -exec grep -l "—\|–" {} \;
find "Product Catalog" -name "*.md" -path "*/_customer_deliverables/*" -exec grep -l "—\|–" {} \;

# Practice-area expertise claim check
find "Product Catalog" -name "*.md" -path "*/_sales_packet/*" -exec grep -il "expert in\|specialize in\|our expertise" {} \;

# CHDB reference check
find "Product Catalog" -name "*.md" -exec grep -il "CHDB\|Aemon" {} \; | grep -v "_internal\|_maester\|_playbook\|_ops"

# Arizona reference check (excluding internal docs)
find "Product Catalog" -name "*.md" -path "*/_sales_packet/*" -exec grep -il "Arizona" {} \;
find "Product Catalog" -name "*.md" -path "*/_customer_deliverables/*" -exec grep -il "Arizona" {} \;
```

Expected: no matches for any check.

- [ ] **Step 3: Mark MVP complete**

Update `Product Catalog/_ops/VERSION_LOG.md`:

```markdown
## v1.0 - MVP Complete

**Date:** 2026-04-XX
**Status:** MVP Complete

### What shipped:
- 8 tier folders with full sales packets and manifests
- Parser Trial ($197) fully shippable with installer
- Full Litigation Suite ($2,997) fully shippable with Integration Guide v1.0
- 3 consulting tiers scaffolded with intake, contracting, and sales packets
- 3 custom workflow tiers scaffolded with scoping guide and sales packets
- Sales Playbook v1.0
- Catalog Builder skill
- Kyle Review Dashboard
- Website updated with 2-tier products

### What ships in deep phase:
- Integration Guide v1.1 (Chapters E-I, skill walkthroughs)
- Foundation presentation deck (full production)
- Modernization governance framework (per engagement)
- CLE accreditation (post-engagement)
- Practice-area skill packs (per demand)
```

- [ ] **Step 4: Final commit**

```bash
git add "Product Catalog/"
git commit -m "milestone: Product Catalog MVP complete - all 8 tiers ready"
```

---

## Task Summary

| Phase | Tasks | Primary Owner | Hours |
|---|---|---|---|
| 1: Foundation Infrastructure | Tasks 1-6 | Agent + Kyle review | 4-6 |
| 2: Sales Playbook | Task 7 | Kyle (interview sequence) | 8-12 |
| 3: Parallel Infrastructure | Tasks 8-9 | Khal | 14-20 |
| 4: Subagent Content Drafting | Tasks 10-14 | 5 subagents (autonomous) | 18-28 |
| 5: Kyle Non-Delegable Content | Tasks 15-17 | Kyle | 12-18 |
| 6: Skill File Population | Task 18 | Agent + Kyle | 3-5 |
| 7: Review, Revision, Assembly | Tasks 19-25 | Kyle + agents | 15-22 |
| **Total** | **25 tasks** | | **74-111** |
| **Kyle total** | | | **32-50** |

---

*End of implementation plan. 25 tasks across 7 phases. Estimated 3.5 weeks at sustainable pace.*
