# Mia Dental OS — Public Deployment Guide

**Status: DRAFT v0.1 — 2026-10-11.** Deploy the demo publicly with `render.yaml`
(one-click Blueprint). Fly.io config is included as a later alternative.

## What the founder taps (3 steps)

1. **Create a Render account** at https://render.com (sign up with GitHub).
2. **New → Blueprint** → connect the `ai-front-desk` repo → select the
   `build/dental-mia-prescribe-2026-10-11` branch → **Apply**.
3. **Wait for the deploy**, then open the URL Render gives you
   (looks like `https://mia-dental-os.onrender.com`).

That's it. The Blueprint builds the Dockerfile, attaches the 1 GB persistent
disk at `/data`, and sets every env var. No secrets to paste — billing is
manual Neteller, so there are no API keys.

> **Pricing note:** Render's persistent disk needs a paid instance (Starter,
> ~$7/mo). The free tier has *ephemeral* storage — accounts and patient data
> would be wiped on every restart. Don't use free for anything a dentist touches.

## Environment variables (set by render.yaml — verify in the dashboard)

| Variable | Value | Why |
|---|---|---|
| `PORT` | injected by Render | the server reads `$PORT` first |
| `PRESCRIBE_HOST` | `0.0.0.0` | bind inside the container |
| `PRESCRIBE_DB` | `/data/prescribe.sqlite3` | accounts DB on the persistent disk |
| `PRESCRIBE_STATE_DIR` | `/data` | trial/clinical state on the persistent disk |
| `PRESCRIBE_SECURE_COOKIES` | `1` | `Secure` flag on session cookies (HTTPS) |

## How to verify the live deployment

1. Open the URL → landing page loads with Mia's intro and the 7-day trial offer.
2. **Sign up** a test dentist account → you land on `/welcome` with the trial pill.
3. **Run the wizard**: load the sample patient → run the sample check → confirm
   the RED flag on the penicillin allergy (the "aha" moment).
4. **Check the legal pages**: `/legal`, `/privacy`, `/terms`, `/security` all 200.
5. **Test the billing loop**: let the trial expire (or backdate it) → subscribe
   page shows the Neteller instructions → "I've paid" → `list-pending` in the
   admin CLI → activate.
6. Confirm response headers include `Content-Security-Policy` and
   `X-Frame-Options: DENY` (devtools → Network).

## After deploy — founder runbook

- **Activating a paying dentist:** SSH is not needed. Run the admin CLI against
  the same database. Easiest: `render ssh` (paid plans) then
  `python -m ai_front_desk.clinical.prescribe.admin list-pending` /
  `activate <email>`. The DB lives at `/data/prescribe.sqlite3` — set
  `PRESCRIBE_DB=/data/prescribe.sqlite3` in that shell.
- **Backups:** Render disk snapshots are manual — take one before any upgrade.
  (Automated daily snapshots are a later step.)
- **Logs:** Render dashboard → service → Logs. Auth/billing events are also in
  the app's audit trail (`prescribe_audit` table).

## Honest limits (read before a real dentist uses this)

- **Demo-grade auth.** PBKDF2 hashing, secure sessions, rate limits — but no
  email verification, no password reset, no 2FA, no independent security audit.
- **SQLite, single instance.** One container, one disk. No replication, no
  failover. Fine for the first pilot; not a scale story.
- **Not HIPAA-compliant.** No BAA. Do not put real patient PHI on the public
  demo until the security checklist (`docs/security/DEPLOYMENT_CHECKLIST.md`)
  is fully worked through.
- **Reference data v2 requires dentist review.** Labeled as such in the app.
- **Manual billing.** Neteller transfers + human activation. No chargebacks
  handling, no dunning, no invoices — that comes with a real provider.

## Local Docker test (when docker is available)

```bash
docker build -t mia-dental-os .
docker run --rm -p 8767:8767 \
  -e PORT=8767 \
  -v mia-data:/data \
  mia-dental-os
# → http://localhost:8767
```
