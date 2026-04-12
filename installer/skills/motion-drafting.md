---
name: motion-drafting
description: Draft a legal motion, response, reply, or other pleading for general civil litigation — produces a formatted, CRAC-structured document with caption, memorandum of points and authorities, and signature block.
license: Sidebar Code / Banfield Consulting, LLC — Firm-wide internal use only. See Terms of Service at sidebarcode.com/terms.html
version: 1.0
jurisdiction: General (jurisdiction-specific citations must be added by the licensing firm)
---

# Motion Drafting Protocol

A structured motion-drafting workflow for general civil litigation. This skill ingests the handling attorney's instructions, the opposing filing, the record, and any prior analysis, then produces a formatted, CRAC-structured draft motion (or response, reply, or pleading) suitable for filing after attorney review.

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

Jurisdiction-specific case citations must be added for standards of review and substantive law. Federal Rule 56, Rule 12(b)(6), and Rule 60(b) references are substantially similar across most jurisdictions but verify local variation.

---

## Input Sources (weighted by availability)

- Priority 1: Attorney instructions — the filing type requested, case context, strategy notes, facts to emphasize, tone directives, arguments to include or exclude
- Priority 2: Attached documents — opposing filing, exhibits, prior orders, contracts, declarations, pleadings
- Priority 3: Prior pleading-parser output — if the parser has already been run on the opposing document
- Priority 4: The firm's authorities database — the firm's preferred case citations for common standards (summary judgment, dismissal, sanctions, etc.)
- Priority 5: Inference — fills gaps using legal training, flagged in the Confidence Assessment

The attorney may provide a one-liner ("draft our response to the attached MSJ") or a detailed set of instructions with strategy, attached documents, and specific arguments. Use everything available. Flag what was not provided.

## Step 1: Intake

Read everything provided:
- Identify the filing type requested, case name and number, strategic instructions, specific arguments to include or exclude, and any tone directives
- Read ALL attachments completely — every page of every document
- If a prior pleading-parser run is referenced, load that analysis
- If the case has existing files or prior filings, load the case history
- Identify the legal issues and pull the applicable authorities from the firm's authorities database

## Step 2: Filing-Type Detection

Auto-detect from the instructions and attachments:

| Trigger language | Filing type |
|---|---|
| "respond to MSJ," "opposition to MSJ," "response to summary judgment" | Response to MSJ |
| "draft MSJ," "summary judgment," "MSJ on [claim]" | Motion for Summary Judgment |
| "draft MTD," "motion to dismiss," "12(b)(6)" | Motion to Dismiss |
| "draft reply," "reply in support" | Reply ISO Motion |
| "draft sanctions," "motion for sanctions" | Motion for Sanctions |
| "draft fee app," "attorneys' fees," "fee application" | Application for Fees and Costs |
| "motion to strike" | Motion to Strike |
| "respond to motion," "opposition to" | Response to Motion |
| "Rule 60," "relief from judgment" | Rule 60(b) Motion |

If ambiguous: draft what seems most likely AND flag in the Confidence Assessment: "I interpreted this request as [type] because [reason]. If you meant [other type], let me know."

## Step 3: Argument Map

For each argument, build an internal working map:
- a. The legal conclusion (topic sentence that will open the subsection)
- b. The controlling authority (case name, citation, parenthetical template)
- c. The record facts supporting it (with exhibit, SOF, deposition, or declaration cites)
- d. The anticipated counter-argument from opposing counsel
- e. The rebuttal strategy (CRAC, 5-step adverse-authority neutralization, case-comparison paragraph)
- f. Confidence level — binding authority and record support, or inferred?

Also identify:
- Arguments the attorney specifically requested → include
- Arguments the attorney specifically excluded → omit
- Arguments the skill would add beyond the attorney's instructions → include but flag as "Suggested addition — not specifically requested, included because [reason]"

## Step 4: Draft the Motion

### CAPTION

Use a caption template with these placeholders. The firm's clerical team should fill in values specific to each case:

```
                  IN THE {{COURT}}

{{PLAINTIFF NAME}},                          )  Case No. [Number]
                                             )
                    Plaintiff,               )  [DOCUMENT TITLE IN ALL CAPS]
                                             )
          vs.                                )  (Assigned to the Honorable
                                             )   [Judge Name])
{{DEFENDANT NAME}},                          )
                                             )  [Oral Argument Requested / Not Requested]
                    Defendant.               )
_____________________________________________)
```

Firm block (upper left, above caption):

```
{{FIRM_NAME}}
{{FIRM_ADDRESS}}
{{FIRM_CITY_STATE_ZIP}}
{{FIRM_PHONE}}
{{FIRM_EMAIL}}

[Attorney Name], Esq. (Bar No. [Number])
Attorneys for [Party]
```

Use a short-name parenthetical at first mention of each party, e.g., "[Full Party Name] ('[Short Name]')."

### INTRODUCTION

Use this formula (proven general litigation introductory structure):

"[Party designation], [Full Party Name] (the '[Short Name]') hereby [action verb: requests / submits / files] [document name and relief sought in one sentence]. [One to two sentences of case posture or thesis.] This [Motion/Response/Reply] is supported by the following Memorandum of Points and Authorities[, Separate Statement of Facts ('SOF'),] and all of the pleadings and matters of record filed with the Court, all of which are incorporated herein by reference."

### MEMORANDUM OF POINTS AND AUTHORITIES

Insert a centered, ALL CAPS banner after the introduction:

```
                    MEMORANDUM OF POINTS AND AUTHORITIES
```

### BACKGROUND / PROCEDURAL HISTORY

- Narrative facts with parallel record cites on every factual proposition
- For MSJs: SOF ¶__ pg.__ cites
- For MTDs: Complaint at ¶__ cites
- For other motions: cite exhibits, declarations (e.g., "[Name] Decl. at ¶__"), and prior rulings (e.g., "Minute Entry filed [date]")
- Organized chronologically or thematically as the case requires

### LEGAL ARGUMENT

Heading hierarchy:
- Roman numeral, ALL CAPS for major sections: `II. LEGAL ARGUMENT`
- Capital letter, Title Case (bold) for subsections: `A. Summary Judgment Standard`
- Lowercase letter for sub-subsections: `a. Procedural History`

**Standard of review subsection FIRST.** The first subsection of the argument section must set out the governing legal standard. Insert jurisdiction-specific standard of review authority here. The firm's authorities database should supply the preferred citations for each standard:

- MSJ: [Insert the firm's preferred summary judgment standard citations.] Federal Rule 56 and *Anderson v. Liberty Lobby, Inc.*, 477 U.S. 242 (1986) apply in federal court. State practice typically parallels the federal standard but verify jurisdiction-specific controlling authority.
- MTD: [Insert the firm's preferred Rule 12(b)(6) / failure to state a claim citations.]
- Sanctions: [Insert the firm's preferred sanctions standard citations and the applicable statute or rule.]
- Rule 60(b) Motion: [Insert the firm's preferred Rule 60(b) citations.]

Each substantive argument subsection follows **CRAC**:
1. **C**onclusion: Topic sentence = legal conclusion
2. **R**ule statement with full citation + block quote or parenthetical
3. **A**pplication paragraph opening with "Here," — connect record facts to rule elements
4. Case-comparison paragraph: "In [Case]... Here,..."
5. Restated **C**onclusion at paragraph end

Per subsection:
- 2-4 authorities stacked: binding first, then persuasive
- Statutory reinforcement after the case stack
- Opponent's arguments restated fairly in 1 sentence, then destroyed
- Adverse authority neutralized using the 5-step playbook:
  1. **Acknowledge** the case
  2. **Narrow** its holding to its facts
  3. **Distinguish** the facts from those at bar
  4. **Cite a better case** (more directly on point)
  5. **Flip it** — use the reasoning of the adverse case against the party citing it

### CONCLUSION

Prayer formula:

"For the reasons set forth herein[, and in (prior briefing),] [Party] respectfully requests that this Court [specific relief]. [Party] further requests its attorneys' fees and costs [phrase] pursuant to [authority], and such other and further relief as the Court deems just and proper."

### SIGNATURE BLOCK

```
RESPECTFULLY SUBMITTED this [ordinal] day of [Month], [Year].

                              {{FIRM_NAME}}

                              By: {{ATTORNEY_SIGNATURE_BLOCK}}
                                  [Attorney Name], Esq.
                                  Attorneys for [Party]
```

### CERTIFICATE OF SERVICE

Add a Certificate of Service at the end consistent with the local rules of the applicable court. A template should be maintained by the firm.

---

## Writing Rules (Enforced Throughout)

- **Active voice in every sentence.** No passive constructions.
- **No hedging.** "Arguably," "it seems," "tends to suggest" are prohibited.
- **Medium-long sentences** (25-45 words). Compound structures with "and," "but," "however."
- **Topic sentence of every paragraph states a legal conclusion.**
- **Case names italicized throughout.**
- **Citation format:** use the firm's preferred citation style consistently. Spacing around § and ¶ should match firm style. Pincite required on every case cite. Use "(Emphasis added)." where emphasis is added to a quotation. Record cites required on every factual proposition.
- **No em dashes.** Use commas, parentheses, or semicolons instead.
- **Every factual proposition has a record cite.** (SOF ¶, Complaint ¶, Exhibit, Decl. ¶)
- **Every legal proposition has a case or statute cite with pincite.**

### Recommended Active Verbs

- **Damaging verbs (for opposing arguments):** contends, ignores, confuses, overlooks, mischaracterizes, misstates, conflates, misreads
- **Neutral verbs (for courts and authorities):** held, stated, noted, reasoned, explained, observed, concluded
- **Affirmative verbs (for your client):** maintains, submits, argues, establishes, demonstrates, shows

### Dismissive Adjectives for Opposing Arguments

Use sparingly and only where the record supports the characterization: groundless, baseless, meritless, inexplicable, unsupported, conclusory, perfunctory.

---

## Step 5: Self-Audit (14-Point Checklist)

Before delivering, verify:

- [ ] 1. Active voice every sentence — no passive constructions
- [ ] 2. Every factual proposition has a record cite (SOF ¶, Complaint ¶, Exhibit, Decl. ¶)
- [ ] 3. Every legal proposition has a case or statute cite with pincite
- [ ] 4. Topic sentence of each paragraph is a legal conclusion
- [ ] 5. CRAC structure in every argument subsection
- [ ] 6. 2-4 authorities per subsection, binding cited first
- [ ] 7. Case-comparison paragraph included where analogous authority exists
- [ ] 8. Opponent's arguments restated fairly, then rebutted
- [ ] 9. Standard of review is the first subsection of the legal argument
- [ ] 10. Caption matches firm template with all placeholders filled
- [ ] 11. Prayer formula matches structure
- [ ] 12. Citation format consistent with firm style guide (§ spacing, ¶ spacing, italics, pincites)
- [ ] 13. No hedging language anywhere
- [ ] 14. Case names italicized throughout; no em dashes

## Step 6: Confidence Assessment

**HIGH CONFIDENCE** (directly supported by record + binding authority):
- [Argument/fact] — Source: [cite]

**MODERATE CONFIDENCE** (reasonable inference; authority is analogous but not directly on point):
- [Argument/fact] — Based on: [what I read] — Gap: [what would confirm this]

**LOW CONFIDENCE** (assumption; gap in the record; authority is thin or out-of-jurisdiction):
- [Argument/fact] — I assumed this because: [reason] — What I need: [specific fact/doc]

**INFORMATION I WISH I HAD:**
- [Specific document, deposition, declaration, or exhibit that would materially strengthen the draft]

Rules: If a fact is missing and the draft must work around it, state the assumption and flag it. Do NOT silently fill the gap with a guess.

## Step 7: Deliver

Produce a delivery summary alongside the draft:

```
I. WHAT WAS DRAFTED
   - Filing type: [Response to MSJ / MTD / etc.]
   - Page count: [X] pages
   - Arguments made: [numbered list]
   - Arguments considered but not included: [list + why]

II. KEY DECISIONS MADE
   - [Decision] — because [reason]

III. CONFIDENCE ASSESSMENT
   [High / Moderate / Low / Information I wish I had]

IV. OPEN QUESTIONS
   - [Question]
```

Deliver the draft as a formatted Word document (.docx) or PDF.

**Iterative revision:** If the handling attorney sends follow-up changes, incorporate them, deliver the revised draft with a brief diff summary, and label it "REVISED DRAFT — [Filing Type] — [2-5 word diff summary]."

## Standing Rules

- **Active voice in every sentence.** No passive constructions.
- **Case names italicized** throughout.
- **Lettering and bullets for sub-points.** Primary sections use Roman numerals. Subsections use capital letters. Sub-subsections use lowercase letters or bullet points.
- **No hedging.** Every sentence earns its place.
- **Every factual proposition has a record cite.** No naked facts.
- **Every legal proposition has a case cite with pincite.** No naked legal claims.
- **Attorney instructions override defaults.** If the attorney says "don't make that argument," the skill omits it even if it would be strong — but flags the disagreement in the Confidence Assessment.
