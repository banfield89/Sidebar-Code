# Sidebar Code SP2 — Incident Runbook

**Audience:** Kyle, at 9pm on a Saturday, after a buyer just emailed saying something is broken.

This runbook covers the most likely failure modes for the Stripe + Delivery
service. Each scenario has four sections: **Symptoms**, **Diagnosis**, **Fix**,
**Prevention**. Read them in order. Don't try to be clever — the steps are
written this way because the obvious shortcut is usually wrong under stress.

If you're paged for something not in this runbook, do these three things first:

1. Check `https://sidebarcode-api.onrender.com/health` — should return `{"status":"ok",...}`. If it doesn't, jump to **Scenario 1**.
2. Check the daily digest inbox for any failures already alerted overnight.
3. Open https://dashboard.render.com → `sidebarcode-api` → **Logs** tab — search the last hour for `ERROR` or `Traceback`.

Most incidents will resolve to one of the scenarios below within 5 minutes of these checks.

---

## Scenario 1 — Webhook service is down

### Symptoms
- `https://sidebarcode-api.onrender.com/health` does not return JSON, or returns a 5xx, or times out
- Buyers report nothing happened after they paid
- Stripe dashboard shows recent `checkout.session.completed` events with status `Failed` or `Pending`
- New purchases are not appearing in the SQL `purchases` table
- No new lines in Render logs in the last few minutes

### Diagnosis
1. Open https://dashboard.render.com → `sidebarcode-api` → check the top status indicator. Is it green (Live), yellow (Deploying), or red (Failed)?
2. If green but `/health` still doesn't respond, Render's edge might be the issue — check https://status.render.com.
3. If red, look at the **Events** tab for the most recent deploy. A failed deploy means the code change broke the build.
4. If yellow, a deploy is in progress — wait 2-3 minutes and retest.

### Fix
- **Failed deploy:** click into the failed deploy → read the build log → identify the failing line. Most common: a syntax error or missing import in a recent commit. **Fastest fix:** click **Rollback** on a known-good prior deploy. Then fix the bad commit and push when you have time.
- **Live but unresponsive:** click **Manual Deploy → Clear build cache & deploy**. This restarts the service from scratch, which fixes most "it just stopped responding" cases.
- **Render edge issue:** wait it out. Stripe will retry every webhook for up to 3 days, so as long as your service comes back within 72 hours, no purchases are lost.

### Prevention
- Don't push at night
- CI catches obvious breakage but not all of it — manual smoke test `/health` after every deploy
- Watch the Render Events feed for at least 60 seconds after pushing

---

## Scenario 2 — Stripe webhook retries are visible in the dashboard

### Symptoms
- https://dashboard.stripe.com/test/webhooks → click endpoint → "Recent deliveries" or "Event deliveries" shows entries with status `Failed` (red)
- The Failed entries say things like `500 Internal Server Error` or `400 Bad Request` from your endpoint
- Stripe shows "Next retry in N minutes/hours"
- Affected buyer hasn't received their delivery email yet

### Diagnosis
1. Click into one of the failed delivery rows. Stripe shows the response body your service returned.
2. The response body usually identifies the failure:
   - `"webhook secret not configured"` → `STRIPE_WEBHOOK_SECRET` env var missing in Render
   - `"invalid signature"` → secret in Render does not match the secret Stripe uses
   - `"handler error"` → exception inside `handle_checkout_completed` or `handle_refund` — go to Render logs to find the traceback
3. Cross-reference with Render logs (search for the timestamp of the failed delivery)

### Fix
- **`webhook secret not configured`:** Render → `sidebarcode-api` → **Environment** → add `STRIPE_WEBHOOK_SECRET` with the `whsec_...` value from Stripe's webhook endpoint detail page. Save → Render auto-redeploys → click **Resend** in the Stripe dashboard on each failed delivery.
- **`invalid signature`:** the secret in Render and the secret Stripe is using are different. Either you rotated the Stripe secret without updating Render, or you're using the wrong secret (live vs test). Re-copy from the Stripe dashboard, paste in Render.
- **`handler error`:** find the traceback in Render logs and fix the underlying bug. **Do NOT manually mark events as processed** — let Stripe retry once you ship a fix.

### Prevention
- After Stripe rotates a webhook secret, immediately update Render and confirm with a test event
- Aemon should review every webhook handler change before merge — they touch money flow

---

## Scenario 3 — R2 upload is failing

### Symptoms
- Buyers complete checkout but never receive a download email
- Render logs show `build_and_deliver_zip FAILED` with a `BotoCoreError` or `ClientError` or `RuntimeError: R2 credentials missing`
- `delivery_failures` table has new rows with R2-related errors
- `delivery_failure_alert` emails arriving in your inbox

### Diagnosis
1. Render logs → search `R2` → look for the specific exception
2. Common error messages:
   - `R2 credentials missing` → one of `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` is missing in Render env
   - `Access Denied` → token revoked or scoped to wrong buckets
   - `NoSuchBucket` → bucket name typo or bucket was deleted
   - `Forbidden` → token expired or wrong region
3. Test R2 directly via Cloudflare dashboard: https://dash.cloudflare.com → R2 → click your bucket → confirm objects can be created via the UI

### Fix
- **Missing env vars:** add to Render → `sidebarcode-api` → Environment. Re-trigger a failed delivery via the admin dashboard's **Resend** button.
- **Token revoked or expired:** in Cloudflare → R2 → API tokens → create a new Object Read & Write token scoped to all three buckets → update Render env.
- **Wrong bucket name:** confirm `R2_BUCKET` in Render matches an actual bucket name (e.g., `sidebarcode-staging`, not `sidebarcode_staging`).

### Prevention
- Pin Cloudflare token TTL to 1 year and rotate calendar-style, not after expiration
- Lifecycle rule on staging/prod buckets prevents accidental data growth
- Token is scoped to specific buckets so a leak can't access unrelated data

---

## Scenario 4 — Postmark delivery is failing

### Symptoms
- Buyers paid but emails never arrived
- Render logs show `postmark` errors or `ClientError: 401`
- Postmark Activity log shows messages with status `Bounced`, `Failed`, or `Spam complaint`
- `delivery_failure_alert` emails arrive but the original buyer email never did

### Diagnosis
1. Open Postmark → server → **Activity** tab → look at the most recent messages
2. Click into a failed message to see the bounce reason
3. Common failure modes:
   - **`401 Unauthorized`** → token in Render is wrong type (Account vs Server) or revoked. See Postmark docs on token types.
   - **`Hard bounce`** → recipient address doesn't exist. Check the buyer's email in the purchases table — did Stripe Checkout collect the right email?
   - **`Spam complaint`** → recipient marked your email as spam. Reach out manually if it's a legitimate buyer.
   - **`Sender signature unverified`** → `kyle@sidebarcode.com` is no longer verified in Postmark sender signatures.

### Fix
- **Wrong token:** Postmark → Servers → Sidebar Code → API Tokens → copy the **Server** token (not Account). Update Render env. Re-trigger via admin dashboard Resend.
- **Bounce:** if the email address is genuinely wrong, contact the buyer through Stripe (their phone number is in the purchase row) and re-send to a corrected address via the admin dashboard.
- **Sender signature unverified:** Postmark → Sender Signatures → re-verify `kyle@sidebarcode.com` (re-send the verification email and click the link).

### Prevention
- Always grab the **Server** token from inside the server, never the Account token
- Renew sender signature verification annually
- Set up a Postmark webhook for bounces (advanced — Phase 2 enhancement)

---

## Scenario 5 — SQLite database is locked

### Symptoms
- Random 500 errors with `sqlite3.OperationalError: database is locked` in Render logs
- Some webhooks succeed, others fail with this error
- Symptoms come in bursts, not steady-state

### Diagnosis
1. SQLite locks happen when two writers compete for the same file. WAL mode mitigates but doesn't eliminate this.
2. Most likely cause: a long-running query is holding a read lock while a write tries to commit
3. Less likely: file system permission issue on `/var/data/sidebarcode.db`
4. Check Render logs for the specific operation that hit the lock

### Fix
- **One-time burst:** restart the service. Render → `sidebarcode-api` → click the **Manual Deploy → Restart** option (NOT Deploy — Restart is a smaller hammer).
- **Persistent locking:** the long-term fix is migrating to Postgres (Render Postgres add-on, ~$7/month). At current volumes you should not need this. If you do, that's a sign of growth.
- **File permission issue:** SSH into Render via the **Shell** tab, run `ls -la /var/data/`. Should show `sidebarcode.db` owned by the service user.

### Prevention
- Keep query patterns short — every helper in `api/crm.py` does single-row inserts/updates
- WAL mode is enabled at schema init
- Monitor row counts: when `purchases` exceeds ~50,000 rows, plan the Postgres migration

---

## Scenario 6 — Buyer reports they never received the email

### Symptoms
- Customer emails support saying "I bought X but didn't get my download/receipt"
- Their purchase IS in the SQL table (so payment + webhook worked)
- But they say no email arrived in their inbox

### Diagnosis
1. Open the admin dashboard: https://sidebarcode-api.onrender.com/admin/sales
2. Find the purchase. Note the status:
   - `delivered` → email was sent. Either it's in their spam folder or Postmark bounced it.
   - `awaiting_delivery` → delivery never completed. Look in `delivery_failures` table for the reason.
   - `failed` → delivery failed and was logged. See Scenario 3 or 4.
3. Open Postmark Activity → search the buyer's email → check delivery status
4. Check the `purchases.buyer_email` column. Did Stripe collect the right address?

### Fix
- **Status `delivered` and Postmark says delivered:** the email is in their spam folder. Reply to the buyer, ask them to check spam, and forward the original from your sent folder.
- **Status `delivered` and Postmark says bounced:** their email address is wrong. Reply to the buyer asking for a corrected address, then click **Resend** in the admin dashboard after updating the email manually via the Render Shell + sqlite3 if needed.
- **Status `awaiting_delivery` or `failed`:** click **Resend** in the admin dashboard to re-trigger the build_and_deliver_zip pipeline. Watch Render logs to confirm it succeeds this time.

### Prevention
- Don't allow optional email at Stripe Checkout (already enforced — it's required)
- Daily digest counts failed deliveries so you spot persistent issues before customers complain

---

## Scenario 7 — Dispute opened (chargeback)

### Symptoms
- Stripe sends a `charge.dispute.created` event
- You receive a Stripe email titled "New dispute"
- The customer has filed a chargeback through their bank

### Diagnosis
1. Click the Stripe link in their alert email → see the dispute reason
2. Common reasons:
   - **Fraudulent** — buyer claims they didn't make the purchase
   - **Product not received** — buyer says they paid but got nothing
   - **Subscription canceled** — N/A for SP2 (one-time charges only)
   - **Duplicate** — buyer claims they were charged twice
3. Cross-reference with the SP2 admin dashboard: find the purchase, check delivery status, check whether they downloaded the file (look at `download_attempts` column)

### Fix
- **Decide whether to fight or accept.** Fighting takes work. Accepting costs you the money plus a $15 dispute fee. Decide based on:
  - Was delivery actually completed? Check `purchases.status` and `download_attempts > 0`.
  - Was the buyer's email and address legitimate?
  - Is this a real attempt at fraud or a misunderstanding?
- **To accept:** in Stripe → dispute → **Refund the customer** (note: this is different from accepting the dispute — accepting doesn't refund automatically). Sidebar Code's webhook will fire `charge.refunded` and clean up the R2 object automatically.
- **To fight:** in Stripe → dispute → **Submit evidence**. Upload:
  - The original Postmark email log showing delivery to their address
  - The download_attempts count from the SQL table (proves they accessed the file)
  - Their accepted ToS + Tech Overview hash from the purchase row
  - Their billing IP and country from the purchase row

### Prevention
- ToS acceptance is recorded with timestamp + version hash + buyer IP for every purchase — this is your evidence trail
- Postmark Activity log retains delivery records for 45 days
- Stripe Radar catches obvious fraud attempts before they hit your service
- The `purchases` table never gets purged — 7-year retention for tax/audit/dispute defense

---

## Scenario 8 — Daily digest stopped arriving

### Symptoms
- It's morning and you don't have a digest email in your inbox
- You usually get one even on quiet days, so silence is meaningful
- Could mean the cron didn't fire, or fired and crashed, or fired and Postmark failed

### Diagnosis
1. Render dashboard → look for the `sidebarcode-daily-digest` cron job in the services list
2. Click into it → **Events** tab → look at the most recent run
3. If there's no recent run at all, the cron schedule is wrong or the cron was paused
4. If the run shows `Failed`, click into the run and read the log
5. Most common: `POSTMARK_API_TOKEN` not propagated from the web service to the cron service

### Fix
- **Cron didn't fire:** in the cron service Settings, confirm the schedule is `0 15 * * *` (15:00 UTC = 08:00 Phoenix, no DST). If it's anything else, edit it. Then **Manual Deploy** to apply the schedule change.
- **Cron crashed on Postmark:** check if `POSTMARK_API_TOKEN` is set in the cron service's Environment tab. The render.yaml uses `fromService` to inherit from the web service, but if the web service env var was added/changed manually, it may not have propagated.
- **Manual run:** in the cron service, click **Trigger Run** to fire it immediately. Confirms the script works without waiting 24 hours.

### Prevention
- Daily digest is the only signal that the entire pipeline is alive. If it stops, **everything is suspect** until you confirm otherwise.
- Set a calendar reminder to check the digest arrived for the first 30 days post-launch
- After 30 days of clean operation, make digest absence a paging event

---

## Quick reference — services and dashboards

| What | URL |
|---|---|
| Health check | https://sidebarcode-api.onrender.com/health |
| Admin dashboard | https://sidebarcode-api.onrender.com/admin/sales |
| Render | https://dashboard.render.com |
| Stripe (test mode) | https://dashboard.stripe.com/test/payments |
| Stripe webhooks (test) | https://dashboard.stripe.com/test/webhooks |
| Postmark | https://account.postmarkapp.com |
| Cloudflare R2 | https://dash.cloudflare.com → R2 |
| GitHub repo | https://github.com/banfield89/Sidebar-Code |
| Postmark Activity | https://account.postmarkapp.com → server → Activity |

## Quick reference — env vars that must be set in Render

If the service is misbehaving, confirm all of these are present in Render's Environment tab on the `sidebarcode-api` service:

- `STRIPE_SECRET_KEY` (test mode: `sk_test_...`)
- `STRIPE_WEBHOOK_SECRET` (`whsec_...`)
- `STRIPE_PUBLISHABLE_KEY` (`pk_test_...`)
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET` (`sidebarcode-staging` or `sidebarcode-prod`)
- `POSTMARK_API_TOKEN` (Server token, NOT Account token)
- `KYLE_ALERT_EMAIL`
- `ADMIN_USER`
- `ADMIN_PASSWORD`
- `SIDEBARCODE_ENV` (`staging` or `prod`)
- `SQLITE_PATH` (`/var/data/sidebarcode.db`)

Missing any one of these will cause specific failure modes documented above.

---

*End of runbook. Last updated: 2026-04-13. Update this file every time you hit a new failure mode in production.*
