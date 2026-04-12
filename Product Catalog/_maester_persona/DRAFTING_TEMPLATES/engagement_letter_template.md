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
