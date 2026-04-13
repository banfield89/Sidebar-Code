# SP2 Decisions Parking Lot

**Purpose:** Questions the day-session agent hit that need Kyle's evening input. The agent uses the documented default and keeps working. Kyle reviews here in the evening and marks each item.

**Format per entry:**
- `[Session #]` `[Status: PENDING | CONFIRMED | CHANGE_TO]`
- **File:** path
- **Question:** ...
- **Agent default:** ...
- **Kyle response:** (filled in evening)
- **Logged:** YYYY-MM-DD

---

## Pending decisions

*(Day-session agents append here as they encounter questions. Kyle edits in the evening.)*

### Session 2 — FastAPI skeleton + CI

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py
- **Question:** Basic auth credentials for /admin/dashboard. Playbook parks this.
- **Agent default:** Read from `ADMIN_USER` and `ADMIN_PASSWORD` env vars. Fails closed with 503 "admin dashboard not configured" if either is unset. Constant-time comparison via `secrets.compare_digest`. Matches parked default in the playbook.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py, .github/workflows/ci.yml, stripe-delivery/render.yaml
- **Question:** Python runtime version. Playbook parks 3.12.
- **Agent default:** Python 3.12 everywhere (CI, Render, local dev target). Matches Render default. Production code is written against 3.12 stdlib; agent's local pytest runs on 3.14 which is a superset — tests pass on both.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py /health endpoint
- **Question:** How to resolve the git SHA at runtime so /health can return it?
- **Agent default:** Check `GIT_COMMIT` env var first (Render will be configured to inject this), fall back to `RENDER_GIT_COMMIT`, fall back to `git rev-parse --short HEAD` for local dev, return "unknown" if all three fail. Render may need a `GIT_COMMIT=$RENDER_GIT_COMMIT` env var mapping added in the service settings — flagging for Session 2 deploy step.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/api/main.py /health endpoint
- **Question:** Source of the `env` field in /health response (staging vs prod vs development).
- **Agent default:** Read from `SIDEBARCODE_ENV` env var. Default value "development" when unset. Render staging service should set `SIDEBARCODE_ENV=staging`; prod sets `=prod`. Flagging so Kyle adds this env var during the Render blueprint apply step.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]`
- **File:** stripe-delivery/.github/workflows/ci.yml
- **Question:** gitleaks install method (playbook listed it in requirements.txt but it's a Go binary, not pip).
- **Agent default:** Installed via `gitleaks/gitleaks-action@v2` GitHub Action in CI. No local pip install. Resolves the Session 1 parking lot entry about this.
- **Logged:** 2026-04-13

---

`[S2]` `[Status: PENDING]` — **Deploy phase NOT YET RUN.**
- Session 2 was split into (a) autonomous coding phase and (b) Kyle-gated deploy phase per Option A in-session. Coding phase is complete and committed. Deploy phase requires Kyle to: (1) run Render Blueprint apply on `stripe-delivery/render.yaml`, (2) paste 6 env vars into the new service (STRIPE_SECRET_KEY, POSTMARK_API_TOKEN, R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, plus ADMIN_USER/ADMIN_PASSWORD/SIDEBARCODE_ENV/GIT_COMMIT), (3) optionally create staging.sidebarcode.com CNAME or accept onrender.com subdomain, (4) smoke test /health returns 200. Exit criteria (staging /health green, CI green) cannot be declared met until these steps complete.
- **Logged:** 2026-04-13

---

### Session 1 — repo scaffolding

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml
- **Question:** Single Render service for checkout + webhook, or split into two services?
- **Agent default:** Single service (`sidebarcode-api`). Simpler to deploy, one webhook endpoint to register, less secret duplication. Splitting is a later optimization if webhook volume starves checkout latency.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml, stripe-delivery/README.md
- **Question:** Confirm domain `sidebarcode.com` is in Kyle's control for DNS SPF/DKIM (needed for Postmark sender verification in Session 1 external tasks).
- **Agent default:** Assume yes. Session 7 emails fail closed if Postmark domain is not verified by then.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/requirements.txt
- **Question:** Playbook lists `gitleaks (dev)` as a requirements.txt entry, but gitleaks is a Go binary, not a pip package. How to install?
- **Agent default:** Added a comment in requirements.txt noting the discrepancy. Plan: install via `zricethezav/gitleaks-action` in the GitHub Actions workflow built in Session 2. No local pip install. If Kyle wants a local pre-commit hook, pre-commit framework can pull the binary.
- **Logged:** 2026-04-13

---

`[S1]` `[Status: PENDING]`
- **File:** stripe-delivery/render.yaml
- **Question:** Render Python runtime version pin. Session 2 playbook parks Python 3.12 as the default; Session 1 render.yaml needs a concrete version to deploy.
- **Agent default:** `PYTHON_VERSION=3.12` set in render.yaml envVars (matches Session 2 parked default). Overridable in Render UI.
- **Logged:** 2026-04-13

---

### Session 1 — exit criteria that could not be completed

`[S1]` `[Status: PENDING]` — **External accounts not created in session.**
- Kyle owns creating Stripe, Cloudflare R2, Postmark, and Render accounts per the playbook "External account tasks" list. Agent scope explicitly excludes API calls to these services in Session 1. The "Kyle has created external accounts (checked off manually)" exit criterion is pending Kyle's evening work before Session 2 can deploy to staging.
- **Logged:** 2026-04-13

---

### Pre-session locks (Spec Appendix B — answer BEFORE starting Session 1)

These are the open questions from the spec that, if left unanswered, force the agent into defaults that are hard to reverse mid-build. Lock them in an evening session before Session 1 starts.

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q1
- **Question:** Final pricing for all 6 consulting/workflow tiers (Foundation, Implementation, Modernization, Single Workflow, Multi Workflow, Practice Area).
- **Agent default:** Placeholder amounts in mock catalog only. Day sessions do NOT touch live prices. Kyle must set real prices before the post-SP1 swap-in session.
- **Why it matters:** Stripe Prices are immutable. Changing a price after provisioning means archiving and recreating. Cheap to fix, but annoying if done repeatedly.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q2
- **Question:** Preferred scheduling tool for consulting handoff: Calendly, Cal.com, or other?
- **Agent default:** Cal.com with URL `https://cal.com/kylebanfield/foundation` (spec example). Template merge var `{{ scheduling_link }}` is tier-specific via catalog.
- **Why it matters:** Session 7 wires the scheduling link into the consulting receipt email. Changing tools later is a find/replace, but locking now avoids placeholder-in-production risk.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q3
- **Question:** Transactional email provider: Postmark or Resend?
- **Agent default:** Postmark (spec default; superior deliverability for transactional; template system is mature).
- **Why it matters:** Session 1 creates the account. Swapping providers after Session 7 means rewriting `send_email` calls and re-creating 4 templates. Not catastrophic but wasted time.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q4
- **Question:** Admin dashboard auth: basic auth (MVP) or simple login form?
- **Agent default:** Basic auth with `ADMIN_USER` / `ADMIN_PASSWORD` env vars, fail closed if unset.
- **Why it matters:** Session 8 builds the dashboard. Upgrading to a login form later is a 1-hour change. Basic auth is fine for single-user MVP.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q5
- **Question:** Parser Trial → Full Suite upsell coupon in the download email? If yes, amount and TTL?
- **Agent default:** NO coupon at MVP. Session 7 sends a clean download email without upsell. Add later if conversion data supports it.
- **Why it matters:** Adding a coupon means creating a Stripe Coupon + Promotion Code + wiring the merge var into the template. ~1 hour of work. Skipping at MVP is fine.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q6
- **Question:** Refund policy: 7-day no-questions-asked, or case-by-case?
- **Agent default:** Case-by-case, documented in ToS as "refunds at Sidebar Code's discretion within 30 days of purchase." No automated refund button.
- **Why it matters:** Affects ToS copy and Aemon review. A "no-questions 7-day" policy is cleaner legally but means more refund losses on impulse buys.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q7
- **Question:** Failed-delivery retry strategy: auto-retry N times before alerting, or alert on first failure?
- **Agent default:** Alert Kyle on FIRST failure. Stripe's built-in webhook retry handles reprocessing. The alert is for visibility, not intervention required.
- **Why it matters:** Lower threshold = more noise but faster response. Session 7 wires this.
- **Kyle response:**
- **Logged:** 2026-04-13

---

`[PRE]` `[Status: PENDING]`
- **File:** specs/2026-04-13-stripe-delivery-design.md Appendix B Q8
- **Question:** Consulting tiers: pay in full at Checkout, or deposit + balance due?
- **Agent default:** Pay in full at Checkout. Simpler for MVP. Deposit model requires invoicing infrastructure.
- **Why it matters:** Changing to deposit model means adding Stripe Invoicing integration later. Real but not Session-1 blocking.
- **Kyle response:**
- **Logged:** 2026-04-13

---

---

## Kyle manual verification queue

*(Day-session agents drop links and test outputs here for Kyle to eyeball in the evening.)*

---

## Confirmed / resolved

*(Move entries here after Kyle marks them CONFIRMED or CHANGE_TO. Keep a running history so the next session can check prior decisions.)*
