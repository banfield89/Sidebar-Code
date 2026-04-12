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
