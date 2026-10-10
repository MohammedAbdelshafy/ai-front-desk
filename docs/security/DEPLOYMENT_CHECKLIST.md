# Mia Dental OS — Deployment Security Checklist

**Status: DRAFT v0.1 — 2026-10-11.** Review before any real patient data touches this system.

The app ships defense-in-depth headers, hardened cookies, rate limits, input caps,
and audit logging out of the box (see "What the app already does"). Everything below
is what the *operator* must do around it — headers alone don't make a deployment secure.

## What the app already does (inner)

- Security headers on every response: `Content-Security-Policy` (no JavaScript at all),
  `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
  `Permissions-Policy`.
- Session cookies: `HttpOnly`, `SameSite=Lax`; `Secure` flag when `PRESCRIBE_SECURE_COOKIES=1`.
- Passwords: PBKDF2-HMAC-SHA256, 200k iterations, per-user salt. Never logged, never stored plaintext.
- Sessions: 24h sliding expiry + 7-day absolute cap. Sign-out invalidates server-side.
- Rate limits: sign-in 10 fails/10min lockout per email; signup 5/hour per IP (in-memory).
- Input caps: every form field hard-capped (4k chars), max 200 fields per request, body size capped.
- Tenant isolation: all patient/check/wizard/audit data scoped per account; cross-account → 403 + audited.
- Auth/billing events audited: signup, signin, signin failures, signout, payment-pending, access denials.
- Generic auth errors (no email-existence oracle). No tracebacks leak to clients.

## What the operator must do (outer)

### 1. TLS everywhere
- Run behind a TLS-terminating reverse proxy (Caddy or nginx). Never expose the Python
  server directly to the internet.
- Set `PRESCRIBE_SECURE_COOKIES=1` so session cookies get the `Secure` flag.
- Redirect HTTP → HTTPS at the proxy.

### 2. Network
- Bind the app to `127.0.0.1` (default). The proxy is the only thing that talks to it.
- Firewall: only 80/443 inbound. No SSH password auth (keys only).

### 3. Host & files
- Run as a dedicated non-root user.
- Data dir (`~/.mia-prescribe/` or `$PRESCRIBE_STATE_DIR`): mode `0700`; SQLite files `0600`
  (the app sets this itself — verify after first run).
- Back up the SQLite DBs daily; test a restore. Encrypt backups at rest.

### 4. Secrets & config
- No secrets in code, git, or chat. Configuration only via environment variables.
- `NETELLER_EMAIL` in `billing.py` is a payment *destination* (public), not a secret.

### 5. Updates & monitoring
- Keep the host OS and Python patched.
- Watch disk space (SQLite grows with audit logs); rotate/archive the audit table periodically.
- Review `prescribe_audit` for `access_denied` / `signin_failed` spikes — they signal probing.

### 6. Before real patient data
- [ ] Qualified dentist review of reference data (currently v2, labeled "requires review").
- [ ] Legal review of Privacy Policy / Terms / Security Policy (currently DRAFT).
- [ ] BAA signed with the clinic if US PHI is involved. **Do not accept real PHI without one.**
- [ ] Email verification + password reset flow (currently missing — documented gap).
- [ ] Independent security review / pentest.
- [ ] Incident response contact and runbook defined.

## Quick reference — environment variables

| Variable | Purpose | Default |
|---|---|---|
| `PRESCRIBE_DB` | accounts database path | `~/.mia-prescribe/accounts.sqlite3` |
| `PRESCRIBE_STATE_DIR` | trial/clinical state dir | `~/.mia-prescribe/` |
| `PRESCRIBE_PORT` | listen port | `8767` |
| `PRESCRIBE_SECURE_COOKIES` | `1` = Secure cookie flag (set behind TLS) | unset |
