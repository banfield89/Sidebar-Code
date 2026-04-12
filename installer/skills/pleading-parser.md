---
name: pleading-parser
description: Analyze a legal pleading (complaint, motion, MSJ, answer, court order) and produce a structured issue-spotter report for general civil litigation.
license: Sidebar Code / Banfield Consulting, LLC — Firm-wide internal use only. See Terms of Service at sidebarcode.com/terms.html
version: 1.0
jurisdiction: General (jurisdiction-specific citations must be added by the licensing firm)
---

# Pleading Parser and Issue Spotter

A structured litigation analysis skill. This workflow parses uploaded pleadings and court documents to extract legal issues, claims, defenses, and factual arguments. It automatically detects the document type and applies the appropriate analysis mode, then produces a confidence-assessed report the handling attorney can work from.

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

Jurisdiction-specific case citations must be added for standards of review and substantive law. Federal Rule 56, Rule 12(b)(6), and Rule 60(b) references are included as they are substantially similar across jurisdictions, but verify local variation.

---

## Step 1: Document Classification

Before any analysis, identify the document type by scanning the caption, title block, and opening paragraphs. Classify into one of the following modes:

| Document Type | Analysis Mode |
|---|---|
| Complaint / Petition | COMPLAINT MODE |
| Motion to Dismiss | MTD MODE |
| Motion for Summary Judgment | MSJ MODE |
| Response / Opposition to MSJ | MSJ RESPONSE MODE |
| Combined MSJ + Response (both uploaded) | FULL MSJ ANALYSIS MODE |
| Motion (other) | MOTION MODE |
| Answer / Affirmative Defenses | ANSWER MODE |
| Order / Ruling | ORDER MODE |
| Unknown / Mixed | GENERAL MODE |

Output the classification at the top of every analysis:

```
DOCUMENT TYPE: [type]
ANALYSIS MODE: [mode]
CASE: [case name and cause number if present]
COURT: [court name and judge if present]
PARTIES: [plaintiff(s) vs. defendant(s)]
DOCUMENT DATE: [date filed or dated if present]
```

## Step 2: Select Analysis Mode

Read the appropriate section below based on the classified mode.

### COMPLAINT MODE

**A. Claims Asserted**

List every cause of action pled, in the order presented. For each:

- **Claim Name:** [e.g., Breach of Contract, Breach of Fiduciary Duty, Negligence]
- **Count Number:** [as labeled in the complaint, if any]
- **Statutory or Common Law Basis:** [cite the applicable statute or common law doctrine]
- **Elements Required:** [list the elements plaintiff must prove]
- **Factual Allegations Supporting This Claim:** [summarize the specific paragraphs relied on]
- **Apparent Weaknesses:** [identify missing elements, vague allegations, or pleading deficiencies]

**B. Parties and Standing**

- Identify each plaintiff and defendant
- Note any standing issues (capacity to sue, derivative standing, representative capacity)
- Flag whether the named plaintiff is the real party in interest

**C. Relief Requested**

List all categories of relief sought: injunctive, monetary, declaratory, attorneys' fees, costs. Flag any relief that appears unsupported by the claims pled.

**D. Available Defenses**

For each claim identified, list the most viable defenses:

- Affirmative defenses (statute of limitations, laches, waiver, estoppel, release, accord and satisfaction)
- Motion to dismiss grounds (failure to state a claim, lack of standing, improper venue, lack of personal/subject matter jurisdiction)
- Substantive defenses specific to the cause of action (e.g., contractual defenses, privilege, consent, assumption of risk)

**E. Issue Spotter Summary**

Produce a concise numbered list of the top legal issues presented by this complaint, ranked by significance to the litigation outcome.

### MSJ MODE

**A. Motion Summary**

- **Movant:** [who is moving]
- **Relief Sought:** [full or partial summary judgment; which claims or defenses]
- **Governing Standard Cited:** [Rule 56 standard as stated in the motion]

**B. Legal Issues Presented**

List every discrete legal question the motion asks the court to resolve. For each:

- **Issue:** [one-sentence statement of the legal question]
- **Movant's Position:** [summary of the argument]
- **Key Cases or Statutes Cited:** [list citations used to support this issue]
- **Strength Assessment:** [Strong / Moderate / Weak, with brief rationale]

**C. Statement of Facts Analysis**

This is the most critical section for MSJ work. For every material fact asserted in the Statement of Facts (or Separate Statement of Facts if filed):

- **Fact Number / Paragraph:** [reference]
- **Assertion:** [the factual claim as stated]
- **Support Cited:** [exhibit, affidavit, deposition, bates number cited]
- **Support Quality:** [Adequate / Thin / Missing / Disputed]
- **Notes:** [flag hearsay issues, foundation problems, best evidence issues, or contradictions with other record evidence]

After completing the fact-by-fact review, produce:

**Critical Facts Summary:** Identify the 5 to 10 most outcome-determinative facts in the motion and assess whether each is adequately supported in the record.

**D. Gap Analysis: Unsupported Assertions**

Produce a dedicated gap analysis table:

| Fact / Assertion | Where Asserted | Support Cited | Gap Identified |
|---|---|---|---|
| [assertion] | [paragraph] | [citation or "none"] | [description of the evidentiary gap] |

Flag any legal conclusion that is stated as a factual assertion without citation. Flag any factual assertion where the cited exhibit does not actually appear to support the stated fact. Flag any element of a legal standard that is assumed rather than argued.

**E. Missing Citations**

List any legal proposition in the argument section that is:

- Asserted without any case or statute citation
- Supported only by the movant's own brief from prior proceedings
- Cited to unpublished or out-of-jurisdiction authority without explanation

**F. Anticipated Opposition Arguments**

For each legal issue identified, identify the most likely counterargument available to the non-moving party and assess whether the motion adequately pre-answers it.

### FULL MSJ ANALYSIS MODE

Use this mode when both the motion and the opposition response have been uploaded. Perform the complete MSJ MODE analysis above for the motion, then add the following:

**G. Response Analysis**

- **Respondent's Framing:** How does the opposition restate the legal issues?
- **Disputed Facts:** Which facts from the Statement of Facts are genuinely disputed in the response? For each disputed fact, assess whether the dispute is: (1) supported by admissible evidence, (2) merely argumentative, or (3) a legal conclusion dressed as a factual dispute.
- **New Arguments in Response:** Identify any arguments raised in the response that were not addressed in the motion.
- **Evidentiary Objections:** Note any evidentiary challenges raised by either party.

**H. Comparative Fact Matrix**

Produce a side-by-side comparison of the most critical contested facts:

| Issue | Movant's Version | Respondent's Version | Record Support (Movant) | Record Support (Respondent) | Assessment |
|---|---|---|---|---|---|
| [issue] | [movant fact] | [respondent fact] | [citation] | [citation] | [who has the better of the record on this point] |

**I. Reply Brief Priorities**

If the skill is assisting in drafting a reply, identify in priority order:

1. Facts the opposition disputed that are actually undisputed in the record
2. Legal arguments in the response that misstate the governing standard
3. Evidentiary objections that should be addressed
4. New arguments requiring a response
5. The single most important point the reply must win to prevail

### MOTION MODE (General Motions)

**A. Relief Requested**

State precisely what the motion is asking the court to do.

**B. Legal Issues Presented**

List and analyze as in MSJ MODE Section B above.

**C. Issue Spotter Summary**

Identify the top legal issues, any procedural defects, and the strongest available response arguments.

### ANSWER MODE

**A. Admitted and Denied Allegations**

Identify any allegations that are admitted, and flag any allegation denied "for lack of information" that appears to be within the defendant's knowledge.

**B. Affirmative Defenses**

List all affirmative defenses pled. For each:

- Is it facially sufficient under applicable pleading standards?
- Is it supported by any factual allegation?
- Is it potentially subject to a motion to strike?

**C. Counterclaims or Cross-Claims**

Identify and analyze as in COMPLAINT MODE if present.

## Step 3: Confidence Assessment (Mandatory)

Before delivering output, categorize every substantive claim in your analysis:

**HIGH CONFIDENCE** (directly supported by record):
- [Statement] — Source: [page/exhibit/cite]

**MODERATE CONFIDENCE** (reasonable inference, not directly stated):
- [Inference] — Based on: [what I read] — Gap: [what would confirm this]

**LOW CONFIDENCE** (educated guess or assumption):
- [Assumption] — I assumed this because: [reason] — What I need: [specific fact/doc]

**INFORMATION I WISH I HAD:**
- [Specific document, fact, or context that would materially improve this analysis]

Rules: If a fact is missing and the analysis must work around it, state the assumption and flag it. Do NOT silently fill the gap with a guess.

## Step 4: Output Format

Always deliver the analysis in the following structure. Use headers exactly as shown.

```
====================================================
PLEADING ANALYSIS REPORT
====================================================

CLASSIFICATION
--------------
[Document type, mode, case, court, parties, date]

LEGAL ISSUES PRESENTED
-----------------------
[Numbered list]

CLAIMS ASSERTED [if complaint or relevant]
------------------------------------------
[Per-claim analysis]

DEFENSES AVAILABLE [if complaint or relevant]
----------------------------------------------
[Per-claim defenses]

STATEMENT OF FACTS ANALYSIS [MSJ only]
----------------------------------------
[Per-fact review and critical facts summary]

GAP ANALYSIS [MSJ only]
------------------------
[Gap analysis table]

MISSING CITATIONS [MSJ only]
------------------------------
[List]

COMPARATIVE FACT MATRIX [Full MSJ Analysis only]
-------------------------------------------------
[Table]

CRITICAL ISSUES SUMMARY
------------------------
[Top 5 to 10 issues ranked by importance to the outcome, with one-paragraph
assessment of each]

CONFIDENCE ASSESSMENT
----------------------
[High / Moderate / Low / Information I wish I had]

RECOMMENDED NEXT STEPS
-----------------------
[Action items for the attorney]
====================================================
```
