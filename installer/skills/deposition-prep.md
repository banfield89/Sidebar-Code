---
name: deposition-prep
description: Prepare a fact-witness or expert deposition outline from case documents, disclosure statement, and exhibits, with exhibit-anchored examination questions and impeachment notes.
license: Sidebar Code / Banfield Consulting, LLC — Firm-wide internal use only. See Terms of Service at sidebarcode.com/terms.html
version: 1.0
jurisdiction: General (jurisdiction-specific citations must be added by the licensing firm)
---

# Deposition Preparation Outline Generator

A comprehensive deposition preparation workflow. The skill ingests all available case documents — with the disclosure statement as the foundation — analyzes what the deposition needs to accomplish relative to the legal theories, then produces a numbered examination outline anchored to exhibits and tied to case goals. Use this skill any time an attorney needs to prepare for a fact witness, party, corporate representative, or expert deposition.

## How to Customize This Skill for Your Firm

Before using this skill, replace the following placeholders with your firm's information:
- `{{FIRM_NAME}}` — Your law firm's legal name
- `{{FIRM_ADDRESS}}` — Street address
- `{{FIRM_CITY_STATE_ZIP}}` — City, state, and zip
- `{{FIRM_PHONE}}` — Main phone number
- `{{FIRM_EMAIL}}` — Primary firm email
- `{{ATTORNEY_SIGNATURE_BLOCK}}` — Signing attorney's name, bar number, and title
- `{{JURISDICTION_RULES_OF_CIVIL_PROCEDURE}}` — Your jurisdiction's rules (e.g., "Federal Rules of Civil Procedure" or "[State] Rules of Civil Procedure")
- `{{STATE_STATUTES}}` — Applicable state statutes for substantive claims
- `{{COURT}}` — Court name for caption

Jurisdiction-specific case citations must be added for standards of review and substantive law. Rule 30(b)(6) corporate representative procedure is substantially similar across federal and most state jurisdictions, but verify local variation.

---

# PART ONE — WORKFLOW

The output document has these sections in order:

1. What Are We Trying to Accomplish (strategic framework)
2. Deposition Goals (specific admissions needed)
3. Exhibits (table of all documents to be used)
4. Examination Outline (exhibit-anchored, numbered questions with follow-ups)

The outline uses standard legal paragraph numbering: Roman numerals for major topic areas, then numbered questions (1, 2, 3) with lettered follow-ups (a, b, c). Exhibit references appear at the START of a question cluster, anchoring the questions to the document being examined. Impeachment notes appear inline where strategically relevant.

---

## Step 1: Document Intake and Classification

Inventory every document provided. Classify each document:

```
DOCUMENT INTAKE
-------------------------------------------------
WITNESS:       [Name]
ROLE:          [Corporate Rep / Party / Fact Witness / Manager / Vendor / Expert / Other]
DEPO TYPE:     [30(b)(6) Corporate | Hostile Fact | Neutral Fact | Party Deposition | Expert]
CASE:          [Case name and cause number]
DEPO DATE:     [Date if known]
NOTICED BY:    [Noticing party]
OUR ROLE:      [Plaintiff | Defendant | Petitioner | Respondent]
-------------------------------------------------
DOCUMENTS REVIEWED:
  [#]  [Title]                    [Type]              [Date]
-------------------------------------------------
```

**Document types to classify:**
- DISCLOSURE: Disclosure statement, initial disclosures, supplemental disclosures
- PLEADING: Complaint, answer, counterclaim, motions
- DISCOVERY: Interrogatory responses, RFA responses, RFP responses/objections
- CORRESPONDENCE: Letters between counsel, demand letters, notices
- EVIDENCE: Contracts, deeds, emails, financial records, photographs
- DECLARATION: Sworn declarations, affidavits by any party or witness
- TRANSCRIPT: Prior deposition transcripts
- EXPERT: Expert reports, opinions, disclosures
- GOVERNING: Contracts, operating agreements, bylaws, policies, governing documents
- MEDICAL: Medical records, bills, diagnostic reports
- FINANCIAL: Tax returns, ledgers, invoices, payment records

**Deposition type auto-detection:**
- If documents include a Rule 30(b)(6) notice → 30(b)(6) Corporate mode
- If the witness is an adverse party → Party Deposition mode (offensive)
- If the witness is adverse or adverse-aligned non-party → Hostile Fact mode
- If the witness is non-party with no stake → Neutral Fact mode
- If the witness is a retained expert → Expert mode
- If uncertain, confirm the mode with the handling attorney before proceeding

---

## Step 2: Disclosure Statement Analysis

**This step is mandatory. If no disclosure statement (or its jurisdictional equivalent — initial disclosures, case management statement, or pretrial order) is provided, request it before proceeding. The disclosure statement is the foundation for the entire outline.**

Read the disclosure statement (both sides if available) and extract:

```
CASE FRAMEWORK
=================================================

CLAIMS ALLEGED:
  1. [Claim name] -- [Elements that must be proved]
  2. [Claim name] -- [Elements that must be proved]

DEFENSES RAISED:
  1. [Defense name] -- [Elements that must be proved]
  2. [Defense name] -- [Elements that must be proved]

PLAINTIFF'S FACTUAL CONTENTIONS:
  - [Key factual assertion and supporting evidence cited]

DEFENDANT'S FACTUAL CONTENTIONS:
  - [Key factual assertion and supporting evidence cited]

KEY DISPUTED FACTS:
  - [Fact in dispute] -- Plaintiff says X, Defendant says Y

UNDISPUTED FACTS:
  - [Fact both sides agree on]

LEGAL THEORIES:
  - [Legal theory] -- requires proving [elements]
```

**For each claim and defense, identify:**
- What elements must be proved and by whom
- What evidence each side has cited in support
- Where the gaps are (elements not yet supported by evidence)
- What this witness can address (directly or as impeachment)

---

## Step 3: Document-to-Issue Mapping

For each document in the intake inventory, map it to the case framework:

```
DOCUMENT MAP
=================================================
[Document title] (Bates/Exhibit reference)
  SUPPORTS: Claim 2, Element 3 (proves notice was given)
  UNDERMINES: Defense 1 (contradicts claim of no knowledge)
  IMPEACHES: Witness's interrogatory answer #4
  KEY PASSAGES: Page 3, Para 2 ("[relevant quoted text]")
```

Identify:
- Documents that contradict each other
- Documents that contradict known or expected witness testimony
- Documents the witness authored, signed, received, or should know about
- Documents referenced in discovery responses that were not produced
- Gaps: issues in the case framework with no supporting documents

---

## Step 4: Witness Profile

Extract from available documents:

**Identity and Background**
- Full name and any name variations in the record
- Current and prior addresses during the relevant period
- Employer, title, and tenure in the relevant role
- Relationship to the parties and to the subject matter

**Role in the Events at Issue**
Map every key event, decision, communication, or document to this witness:

```
Event / Document                  Witness Involvement        Case Framework Link
----------------------------      ----------------------     -------------------
[Document or event]               [What witness did]         [Supports Claim 2]
```

**Prior Statements in the Record**
List every prior sworn or written statement by this witness: declarations, interrogatory responses signed by the witness, letters or emails authored by the witness, statements attributed to the witness in other depositions, admissions in pleadings. Each one is a potential impeachment opportunity and is flagged at the question where it applies.

**Witness-to-Framework Mapping**
For each claim and defense from Step 2:
- TIER 1: This witness is essential to this issue (firsthand knowledge, decision-maker)
- TIER 2: This witness can corroborate or undermine (secondary knowledge)
- TIER 3: This witness is peripheral (limited or no direct knowledge)

---

## Step 5: Build "What Are We Trying to Accomplish"

This section appears at the top of the final outline document. It is the strategic framework that explains WHY each topic area is being covered and what outcome the deposition is designed to achieve.

Write this section in direct, plain language addressed to the handling attorney. Structure:

```
WHAT ARE WE TRYING TO ACCOMPLISH
=================================================

STRATEGIC OBJECTIVE:
[One paragraph: what is the overall purpose of this deposition relative to the
case? What legal theory does it serve? What motion does it support? What trial
narrative does it build?]

CASE POSTURE:
[One paragraph: where does the case stand? What has been established? What
remains disputed? How does this deposition fit in the litigation timeline?]

KEY ISSUES FOR THIS WITNESS:

  1. [Issue/Topic Name]
     WHY IT MATTERS: [Connect to specific claim/defense and element from the
     disclosure statement. Explain what admission or testimony is needed and how
     it advances the position.]
     DOCUMENTS: [List the exhibits that support this topic]
     RISK: [What could go wrong -- what harmful testimony might the witness give?
     How do we contain it?]

  2. [Issue/Topic Name]
     WHY IT MATTERS: [Same structure]
     DOCUMENTS: [Exhibits]
     RISK: [Containment strategy]

  [Continue for each major topic area]

ADMISSIONS NEEDED:
  1. [Specific factual admission tied to a claim/defense element]
  2. [Specific factual admission]
  3. [Specific factual admission]

TRAPS TO SET:
  [If applicable: sequences that commit the witness to a position before
  confronting with contradictory evidence. Describe the setup without revealing
  the technique in the outline itself -- the questions do the work.]
```

---

## Step 6: Deposition Goals

Numbered list of specific admissions or testimony needed, each tied back to the case framework. These are the measurable outcomes of the deposition.

```
DEPOSITION GOALS
=================================================

  1. [Specific admission needed]
     SERVES: [Claim/Defense and element]
     KEY DOCUMENT: [Exhibit that supports or forces this admission]

  2. [Specific admission needed]
     SERVES: [Claim/Defense and element]
     KEY DOCUMENT: [Exhibit]
```

Goals should be specific and testable. "Establish that the witness knew about the restriction" is too vague. "Establish that the witness reviewed the written agreement containing the restriction before signing it" is specific and tied to the notice element of the claim.

---

## Step 7: Exhibit Identification

Compile every document this witness will be examined about. These populate the Exhibits section of the final document.

For each exhibit:
- Assign a number (use existing designation if already assigned; otherwise assign sequentially)
- Document title (official title or clean descriptive name)
- Bates range, recording information, or other identifying reference
- One-line description connecting the document to the case framework

---

## Step 8: Build the Examination Outline

### Format

The outline uses this structure:

```
I.   MAJOR TOPIC AREA

     (BATES RANGE or EXHIBIT #) Document Title

     1.  Question text as it would be spoken at the deposition.
         a.  Follow-up question flowing from the main question.
         b.  Follow-up question.
         c.  Follow-up if witness says X. (Note: if witness denies, go to 2)
         [IMPEACH: Declaration Para. 12 states the opposite]

     2.  Next question.
         a.  Follow-up.
```

**Rules:**
- Exhibit references anchor a question cluster: bold, at the START, before the questions that use that document
- Numbered questions (1, 2, 3) are the primary examination questions
- Lettered follow-ups (a, b, c) flow naturally from the main question
- Impeachment notes appear inline in brackets where strategically placed
- Attorney notes appear in parentheses where a reminder is needed: (if witness denies, move to document confrontation)
- Questions are written in natural spoken language as they would be asked
- Multiple related questions can appear under a single number when they form a natural chain on the same narrow point
- Each major section (Roman numeral) should connect back to a deposition goal

### Section Sequence

**I. Opening Admonitions and Ground Rules** — Use the Universal Opening Protocol in Part Two, Section A, verbatim. For 30(b)(6) depositions, add the corporate representative foundation module from Part Two, Section D, immediately after ground rules.

**II. Background and Personal History** — Use the Background Question Bank in Part Two, Section B. Tailor to the witness: extend employment history if the witness's authority or role is at issue; add professional licensing questions if a license is relevant; add bias and financial interest questions if the witness has a personal stake in the outcome.

**III. Role and Responsibilities** — Use the applicable role-specific questions from Part Two, Section D, based on the deposition type and witness role. Tailor to the specific responsibilities and involvement identified in Step 4.

**IV through [N]: Issue-by-Issue Examination** — One Roman numeral section per topic area from "What Are We Trying to Accomplish." Each section:

- Connects to a specific deposition goal
- Opens with exhibit-anchored questions when a document drives the topic
- Uses the open-to-closed sequence from Part Three (Technique): broad narrative question first, then funneling questions, then pinning questions, then locking the testimony
- Document examination follows the foundation-first rule: establish recognition and relationship to the document before substantive questions
- Impeachment setups: commit the witness to a position BEFORE confronting with the contradictory document. Place the impeachment note at the confrontation question, not at the setup
- Closes each section with: "Is there anything about [topic] you have not yet told me?"

**[Second to Last]: Additional Witnesses and Documents** — Use the closing protocol in Part Two, Section C.

**[Last]: Closing** — Use the closing protocol in Part Two, Section C. Include defense lockdown questions tailored to the specific claims/defenses from the disclosure statement analysis.

---

## Step 9: Generate the Final Document

Deliver as a formatted Word document (.docx) or PDF. Two versions are recommended:

1. Attorney version — includes attorney notes and impeachment flags in gray or red italic
2. Clean version — no attorney notes (suitable for sharing with co-counsel or for the record)

---

# PART TWO — STANDARD QUESTION BANKS

## Section A: Universal Opening Protocol

These questions are read at the start of every fact witness deposition, verbatim or substantially as written. They exist to protect the record.

### A.1 Oath and Understanding

- You understand that you have taken an oath to tell the truth today?
- You understand that oath has the same force and effect as if you were testifying in a courtroom before a judge and jury?
- Is there any reason why you cannot testify truthfully and completely today?

### A.2 Deposition Experience

- Have you ever had your deposition taken before?
  - IF YES: How many times? In what type of cases? Approximately when was the most recent deposition you gave?
  - IF NO: [Proceed to explain the process briefly before continuing]

### A.3 Ground Rules

- If you do not understand a question, please tell me and I will rephrase it. Will you agree to do that?
- If you answer a question, I will assume you understood it. Is that fair?
- If you do not know the answer, please say "I don't know." Is that agreeable?
- If you do not remember, please say "I don't remember" rather than guessing. Can you agree to that?
- Please give spoken answers. The court reporter can only record spoken words. Can you do that?
- If at any point you want to clarify or add to an answer, please feel free to do so. Do you understand?
- Your attorney may object to some questions. Unless your attorney instructs you not to answer, please answer after the objection. Do you understand?

### A.4 Physical and Mental Condition

- Are you taking any medication or substance today that could affect your memory or ability to testify accurately?
- Are you suffering from any illness, injury, or physical or mental condition that could affect your memory or testimony today?
- Is there any reason you are not at your best today?

### A.5 Document Review Before the Deposition

- Did you review any documents in preparation for your deposition today?
  - IF YES: What documents? Did your attorney provide them? Did you review any documents not provided by your attorney? Did reviewing them refresh your memory?
  - IF NO: Did you speak with your attorney about this deposition before today?

### A.6 Communications With Other Witnesses

- Have you spoken with anyone other than your attorney about your testimony today?
  - IF YES: Who? When? What did you discuss? Did that person tell you what to say? Did that person suggest any answers?

### A.7 Documents Brought to the Deposition

- Did you bring any documents with you today?
  - IF YES: What documents? [Request to inspect any documents brought]

---

## Section B: Background and Personal History

### B.1 Identity

- Please state your full legal name for the record.
- Have you ever been known by any other name? IF YES: What name, and during what period?
- What is your current home address?
- How long have you lived at that address?
- What were your prior addresses for the last [10] years? [For each: how long?]
- What is your date of birth?

### B.2 Education

- What is the highest level of education you have completed?
- Where did you attend school? What did you study?
- Do you hold any professional licenses, certifications, or designations?
  - IF YES: What licenses? Issued by what entity? Are they current? Have any been suspended, revoked, or disciplined?

### B.3 Employment History

- Where are you currently employed? What is your job title?
- How long have you been in that position? What are your primary responsibilities?
- Who is your direct supervisor?
- Before your current employer, where did you work? [Trace for at least 10 years or to the relevant period]
  - For each prior employer: title, responsibilities, reason for leaving

### B.4 Prior Litigation

- Have you ever been a party to a lawsuit before this one?
  - IF YES: How many times? What type of cases? Plaintiff or defendant? How resolved?
- Have you ever given testimony in a legal proceeding other than today?
- Have you ever been convicted of a crime? [Follow applicable rules on admissibility of prior convictions for impeachment]
- Are there any pending criminal charges against you?

---

## Section C: Closing and Cleanup Protocol

### C.1 Completeness by Topic

For each major topic covered:
- Is there anything else you want to tell me about [topic] that we have not already discussed?
- Is there anything about [topic] that you think is important for me to know that I have not asked you about?

### C.2 Other Witnesses

- Are you aware of any other person who has knowledge of the events we have discussed today?
  - IF YES: Who? What knowledge? How do you know?

### C.3 Additional Documents

- Are you aware of any documents, recordings, photographs, or other materials related to the issues in this case that have not been produced in this litigation?
  - IF YES: What documents? Where are they? Who has custody?
- Have you or anyone on your behalf destroyed, deleted, or discarded any documents related to this case?
  - IF YES: What documents? When? Why? Who authorized the destruction?

### C.4 Prior Legal History (Final Check)

- Other than this case, are you currently involved in any other legal proceeding?
- Has there ever been a judgment entered against you?
- Is there any aspect of your background, education, employment, or personal history that you believe is relevant to this case that we have not discussed?

### C.5 Anticipated Defenses Lockdown

Customize based on the defenses anticipated in the specific matter. Examples:

- Is it your testimony that [party] acted in good faith in all dealings with [opposing party]?
- Is it your testimony that all required notices were given before [action at issue]?
- Is it your testimony that [party] has treated similarly situated persons the same way?

### C.6 Finalization

- Have you answered all my questions truthfully and to the best of your ability?
- Is there any question you now believe you answered incorrectly? IF YES: Which one, and what is the correct answer?
- Is there anything you want to add to or change about any prior answers?
- Do you understand you will have the opportunity to review the transcript and make corrections before it is finalized?
- Do you understand that substantive changes may entitle me to re-depose you about those changes?
- Is there anything else you want to say for the record before we conclude?

---

## Section D: Role-Specific and Mode-Specific Examination Modules

Load the applicable module(s) based on witness type and deposition mode. Multiple modules can be combined.

### MODULE CORP-A: Corporate Representative Foundation (Rule 30(b)(6))

Use at the beginning of any Rule 30(b)(6) deposition, after opening admonitions.

**CORP-1: Designation and Preparation**

1. Are you the designated Rule 30(b)(6) witness for [entity]?
   a. What topics were you designated to testify about today?
   b. You understand all of your answers are binding on [entity] as its corporate representative?

2. What documents did you review in preparation for today?
   a. Who provided those documents? Did you review anything not provided by counsel?

3. Who did you speak with in preparing to testify today?
   a. Did you consult with anyone to educate yourself on any topic?

4. Is there anyone else within [entity] who has knowledge of the claims at issue?

**CORP-2: Corporate Structure**

1. Describe the ownership and management structure of [entity].
   a. Identify all members, managers, directors, and officers with decision-making authority.
   b. (For each) What is their role? What decisions can they make?

2. Describe the formation, purpose, and business activities of [entity].
   a. When was [entity] formed? What is its principal business?

3. (If applicable) What is the relationship between [entity] and any affiliated or parent entity?

### MODULE DEC-A: Decision-Maker / Authority Examination

For board members, managers, officers, or any witness whose authority is at issue.

**DEC-1: Authority and Decision-Making**

1. What authority do you have to act unilaterally on behalf of [entity]?
   a. What decisions require a formal vote or approval?
   b. Were any decisions at issue in this case made without required approval?

2. Does [entity] maintain written policies governing the decision at issue?
   a. Where are they kept? Did [entity] follow them? If not, who authorized the departure?

**DEC-2: Good Faith / Business Judgment**

1. Before taking the action at issue, what information did you review?
   a. Did you consult counsel? Did you consult any outside professional?

2. Was there any internal opposition to the action?
   a. Who opposed? What were the objections? How were they addressed?

3. Did any decision-maker have a personal financial interest in the outcome?
   a. Any personal relationship with a party that could have influenced the decision?

### MODULE REC-A: Records Custodian Foundation

1. What is your role with respect to the records at issue?
2. What records are in your custody? How are they maintained?
3. Are those records kept in the ordinary course of business?
4. Who is responsible for creating them?
5. Are they created at or near the time of the events they record?
6. Are they accurate and complete to the best of your knowledge?
7. Are there any records that should exist but that you have been unable to locate? IF YES: What records? When did you first notice they were missing?

### MODULE PARTY-A: Party Deposition (Offensive — Plaintiff or Defendant)

**P-1: Knowledge of Governing Documents or Contracts**

1. You signed [the contract/agreement/document] at issue?
   a. You reviewed it before signing?
   b. You understood its terms and obligations?
   c. You understood the consequences of [breach/noncompliance]?

**P-2: Conduct at Issue**

1. Describe, in your own words, what happened.
2. Who was present? Who else has knowledge?
3. What contemporaneous documents exist?
4. Did you document your version of events at the time?

**P-3: Damages**

1. What damages do you claim?
2. For each category: what is the basis? What documentation supports it?
3. Have you taken any steps to mitigate?

### MODULE PI-A: Incident Narrative (Personal Injury / Premises Liability)

**PI-1: Pre-Incident Conditions**

1. On the day of the incident, what footwear were you wearing?
2. Had you consumed any alcohol or medication prior?
3. Had you been to this location before? How many times?

**PI-2: The Incident**

1. Please describe from the moment you began [activity] to the moment of the incident, exactly what happened.
2. What were you carrying? Which hand? Did you have free hands to use [railing / grab bar]?
3. What were the lighting conditions? Did you observe any condition before the incident?
4. Where were you when the incident occurred?
5. Was anyone else present? What did they see?

**PI-3: Immediate Aftermath**

1. What did you do immediately after?
2. What did you say to anyone present? Exactly what did you say?
3. How was staff or any responsible party notified?
4. Did you mention the alleged cause at the time? IF NO: Why not?
5. Did anyone say you [tripped over your own feet / acted inattentively]? How would you respond?

**PI-4: Post-Incident**

1. Any phone calls with anyone at the location afterwards? When? What was discussed?
2. Do you have photographs from the date of the incident? Did you return to the scene?

### MODULE PI-B: Medical History by Body Region

For each body region the plaintiff alleges was injured, repeat this sequence.

1. You referenced [body region] pain. Describe the pain.
   a. Have you had [body region] pain before the incident? When did it first start?
   b. Do you believe you had some pain as a result of any prior activity/injury?
2. Describe the pain following the incident. Pain scale immediately after?
3. List every provider you have seen for [body region] pain.
   a. Treatment? Improvement? Currently receiving treatment?
4. Issues with range of motion? Returned to pre-incident levels?

**Injections and Procedures**
1. Any injections? When? How many? Relief? Still receiving?
2. Any surgeries for these injuries? Any planned?

**Pre-Existing Conditions**
1. Any major prior injuries? When? What treatment?
2. Any prior activities or occupations that caused similar injuries?
3. Any major surgeries in your medical history?

**Emotional Distress**
1. Are you alleging mental or emotional distress?
   a. When did it start? Seen a provider? Under mental health care? Prior diagnoses?

### MODULE PI-C: Damages (Personal Injury)

**Lost Earnings**
1. Currently employed? Where? Daily responsibilities? Hours?
2. Working at the time of the incident? Where?
3. Days of work missed? Lost earnings? Reduced earning capacity?
4. Basis for lost/decreased earning capacity? Documents to support it?
5. Compensation structure? Paid sick days? Paid when absent?
6. Fired from any job in the last 10 years? Why?

**Medical Billing**
1. Health insurance? What company? What has it covered? Any denied claims?
2. Records of what insurance paid? Turned over to counsel?

**Quality of Life**
1. Impact on activities of daily living? What can you no longer do?
2. Improvement with treatment?
3. Any other life changes as a result of the incident?

**Other Damages**
1. Other damages claimed? Basis? Documentation?

### MODULE PI-D: Credibility Testing

**Decision to Sue**
1. When did you decide to engage counsel and file suit?
   a. What led to that decision? Any conversations beforehand?

**Prior Litigation**
1. Prior lawsuits? How many? What type? Plaintiff or defendant? Resolution?

**Contemporaneous Statements**
1. Who did you speak with about the incident other than counsel? When? What did you say?
2. Any social media posts about the incident? Photos of injuries?

### MODULE DR-A: Discovery Response Confrontation

Use when the witness has signed interrogatory responses, RFA responses, or is the person most knowledgeable about document production.

**DR-1: Interrogatory Answer Confrontation**
1. You signed your responses to our interrogatories under oath, correct?
   a. Reviewed before signing? Understood your obligation to answer fully?
2. (Show specific interrogatory) Your answer to Interrogatory [#] states [quote].
   a. Is that still your answer? (If expanded) Why was it not in your sworn response? You understand the duty to supplement?

**DR-2: RFA Confrontation**
1. (Show RFA response) You denied Request for Admission [#], which asked [quote].
   a. Identify every document you relied on to deny that request.
   b. (If no documents) So you denied under oath without documentary support?
   c. You did not consult any expert or authority before denying, correct?

**DR-3: RFP Objection Confrontation**
1. You objected to Request for Production [#] on grounds of [stated objection].
   a. You maintain those records for business purposes, correct?
   b. You have not produced any of these records, correct?
   c. You did not attempt to redact and produce, correct?
   d. What specifically is private about records directly at issue in this lawsuit?

### MODULE CONTRACT-A: Contract / Commercial Dispute Witness

**C-1: Formation**
1. Who negotiated the contract on behalf of [party]?
2. What were the discussions leading to the agreement?
3. Were prior drafts exchanged? Who made the final edits?
4. Is the final written agreement the complete agreement, or were there any side agreements?

**C-2: Performance**
1. What were your obligations under the contract?
2. Were they performed? Documentation of performance?
3. Did [counterparty] perform its obligations?
4. Were any performance disputes raised contemporaneously?

**C-3: Breach**
1. When did you first believe [counterparty] was in breach?
2. Did you provide written notice? When?
3. What was the response?
4. Did you provide an opportunity to cure if required?

### MODULE VENDOR-A: Vendor / Contractor Examination

1. Type of work your company performs? Licensed? Licenses held?
2. How long in business? Prior work for [party]?
3. How were you hired for this job? Who specifically authorized it?
4. Written contract? Who signed for [party]? Scope of work? Changes documented?
5. Total contract price? Work completed to specifications? Any deficiencies?
6. Asked to return to correct? Corrections made and accepted?
7. In your professional opinion, workmanlike performance?
8. Paid in full? Disputed invoices?

### MODULE EXPERT-A: Expert Witness Examination

**EX-1: Qualifications**
1. Educational background? Degrees? Institutions? Licenses? Certifications?
2. How many times retained as an expert? Trial testimony? Ever excluded? On what grounds?
3. What percentage of expert work for plaintiffs versus defendants?

**EX-2: Engagement and Compensation**
1. Who retained you? When? Hourly rate? Paid to date?
2. What were you asked to do? Asked to reach a particular conclusion? Limitations on analysis?

**EX-3: Methodology and Basis**
1. Methodology used? Generally accepted in your field? Peer reviewed? Known error rate?
2. Materials reviewed? Who provided them? Any materials requested but not provided?
3. Assumptions made? If any turned out incorrect, would opinion change? Basis for each key assumption?

**EX-4: Opinions and Limitations**
1. What are your opinions? For each: factual basis? Scientific or professional basis?
2. Issues you were not asked to opine on? Issues you do not feel qualified to opine on?
3. Publications addressing the subject matter? Consistent with current opinion? If inconsistent, explain?

### MODULE OBSERVER-A: Neighbor / Third-Party Observer

**O-1: Observations**
1. Personally observed the condition or events at issue? When first observed? How frequently? What specifically?
2. From what vantage point? Able to clearly see? Anyone else observe it? Documentation (photos, notes)?

**O-2: Complaints Filed**
1. Did you file a complaint? When? How many times? Form (in person, writing, phone)? Response?

**O-3: Relationship and Bias**
1. Personal dispute with any party? Any unrelated disagreement?
2. Financial interest in outcome? Asked to testify a particular way? Promised anything?

---

# PART THREE — DEPOSITION TECHNIQUE

## Question Design Principles

### The Open-to-Closed Sequence

Every examination section should follow this arc:
1. **Open**: "Tell me everything you remember about [event]." Let the witness talk. Do not interrupt. Take notes on what is said and what is not said.
2. **Funnel**: Use what the witness volunteered to narrow the topic. "You mentioned [X]. Tell me more about that."
3. **Pin**: Close off escape routes with specific closed questions. "So you are telling me that [specific fact], correct?"
4. **Lock**: Obtain the final commitment. "And that is your testimony today, under oath, that [specific fact], correct?"

The most common mistake is skipping the open phase and going directly to closed questions. When an attorney asks closed questions first, they teach the witness which answers matter and give the witness a roadmap to avoid the truth.

### One Fact Per Question

Never ask compound questions. "Did you send the notice and was it by certified mail?" is two questions. Ask one. The witness can answer "yes" without specifying which part they are affirming; a compound question is objectionable and opposing counsel will use the objection to coach the witness; in the transcript, it is unclear what the "yes" referred to.

### The Power of Silence

After the witness answers, wait. Do not move to the next question immediately. Silence makes witnesses uncomfortable and they will often volunteer additional information to fill it.

### Never Argue With the Witness

A deposition is not the trial. The goal is to get testimony into the record, not to win an argument with the witness. If the witness gives a harmful answer, do not challenge it on the spot. Ask a series of narrowing questions that create internal inconsistencies in the transcript.

### Telegraph Nothing

Do not signal which answers are important. Ask important questions the same way you ask unimportant ones. The most productive deposition questions look routine until the transcript is read later.

---

## Handling Specific Witness Behaviors

### The Evasive Witness

Symptoms: Long narrative answers to simple questions; volunteers context rather than answering directly; answers a different question than the one asked.

Techniques:
- "I appreciate that, but my question was [repeat]. Can you answer that specific question?"
- "You have told me [what the witness volunteered]. That is helpful. But let me ask my question again: [question]."
- Use time and place anchoring: "On [date], at [location], you [action], correct?"

### The Coached Witness

Symptoms: Same phrasing repeatedly; pauses significantly before each answer; frequent "to the best of my recollection"; frequent conferences with counsel through objections.

Techniques:
- Explore substance of attorney-client conferences during the deposition: "Your attorney just whispered something. Other than legal advice, did your attorney tell you how to answer my question?"
- When the witness uses a rehearsed phrase, push for specificity.
- Loop back to the same topic from a different angle to check consistency.

### The Hostile Witness

Symptoms: Short combative answers; volunteers arguments and legal positions; disputes the premise of questions.

Techniques:
- Maintain a calm methodical tone. The witness's hostility on the record benefits you.
- Do not take the bait. Move on after a combative answer and return later.
- Use leading questions freely.
- "You can disagree with the premise of my question after you answer it. Please answer the question first."

### The Overly Helpful Witness (Opposing Party's Witness)

Symptoms: Volunteers favorable information; fills in details not requested; corrects perceived misimpressions before they are established.

Techniques:
- Do not follow up on volunteered harmful information. Move on.
- Come back from a different angle to contain the damage.
- Close off the narrative quickly with specific closed questions.

### The Witness Who Claims Not to Remember

Techniques:
- "Is it that you don't remember, or that you don't know?"
- "Is there anything that would refresh your recollection?"
- Show the document: "Does Exhibit [#] refresh your recollection?"
- Context cues: "You were the [role] at the time. In the regular course of your duties, would you have [taken the action in question]?"
- For implausible memory gaps: "You are telling me that you do not remember signing a document with your signature dated [recent date]?"

---

## Impeachment Technique

### The Classic Three-Step

1. **Obtain the current testimony**: Get the witness fully committed. "And your testimony today is that you never received that letter, correct?"

2. **Credit the prior statement**: "You gave a declaration in this case on [date]? You signed it under penalty of perjury? You reviewed it before signing to make sure it was accurate? Your memory at that time was fresher than it is today?"

3. **Confront with the inconsistency**: Show the document; read the specific language; ask whether the prior statement accurately reflects what happened. "Your declaration states, and I am reading from Paragraph 12: [read the prior statement]. That is inconsistent with what you just told me, isn't it?"

### After the Impeachment

Let the witness respond. Options:
- Admit: "You are right, I misspoke." This is a win.
- Explain: The explanation may be implausible.
- Double down: Creates a direct conflict with the prior sworn statement for the jury.

Do not argue with any of these responses. The transcript does the work.

---

## Document Examination Technique

### Never Show a Document Without a Plan

Before placing an exhibit in front of a witness, know:
- Exactly what the witness needs to say about it
- What the worst possible response is and how it will be contained
- Whether to use it early (for foundation) or late (for impeachment)

### The Foundation-First Rule

Before asking any substantive question about a document:
1. Establish that the witness recognizes it
2. Establish when they first saw it
3. Establish their relationship to it (author, recipient, custodian, or aware of it)
4. Establish whether it accurately reflects what it purports to reflect

Only after the foundation is established ask the substantive questions.

### Using Documents to Box In the Witness

If the witness gives testimony that contradicts a document:
- Do not immediately show the document
- Continue with more questions to develop and lock in the contradictory testimony
- When the testimony is fully committed, show the document and confront

The more committed the witness is to the contradictory position before seeing the document, the more powerful the confrontation.

---

## Strategic Pacing

### Time Management

- Must-Get Goals (Tier 1): 50% of allocated time
- Should-Get Goals (Tier 2): 30% of allocated time
- Nice-to-Have Goals (Tier 3): 20% of allocated time
- Reserve 15 minutes at the end for cleanup regardless

### When to Go Long on a Topic

- Witness is giving inconsistent answers and the inconsistency is building
- Document examination is generating more than expected
- Witness appears nervous or uncomfortable and more time in the discomfort zone is productive

### When to Cut a Topic Short

- The witness is clearly prepared and is giving nothing useful
- The topic is generating more harmful testimony than helpful testimony
- You already have what you came for and further questions risk rehabilitation

### The End-of-Deposition Opportunity

Witnesses and their counsel often relax at the end. The witness may be tired and their guard down. Consider saving one or two important questions for the very end when the witness is least vigilant.
