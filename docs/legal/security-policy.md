# Security Policy — Mia Dental OS

> **DRAFT v0.1 — 2026-10-11 — requires qualified legal review before production use or real patient data.**
> This is a starting draft, not legal advice. It has not been reviewed by an attorney.

**Operator:** MBM (Mohammed Abdelshafy), contact: abdelshafyclapps@gmail.com

## 1. Honest status

Mia Dental OS is currently **demo-grade software**. It has **not** been independently security-audited, is **not** HIPAA-compliant, and we do not offer a Business Associate Agreement (BAA) at this stage. Do not enter real patient data until compliant hosting is confirmed in writing. This document describes what the software actually does today — not aspirational controls.

## 2. Architecture summary

- Single-server Python application (standard library only — no third-party runtime dependencies).
- Data stored in a local SQLite database on the deployment server.
- No advertising trackers or third-party analytics on clinical pages.

## 3. Authentication

- Passwords are hashed with **PBKDF2-HMAC-SHA256, 200,000 iterations**, with a unique per-user random salt. Plaintext passwords are never stored or logged. Minimum 10 characters at sign-up.
- Sessions use 256-bit random tokens (`secrets.token_urlsafe(32)`); only the SHA-256 hash of the token is stored server-side. Sessions expire after 24 hours with sliding refresh.
- Session cookie: `HttpOnly`, `SameSite=Lax`.
- Sign-in rate limiting: 10 failed attempts per email per 10 minutes triggers a 10-minute lockout (HTTP 429). Error messages are generic to avoid leaking whether an email is registered.
- **Not yet implemented:** email verification, password reset flow, two-factor authentication. These are required before production use with real patient data.

## 4. Authorization and isolation

- Every patient record, check, wizard session, and audit entry is scoped to the owning account. Cross-account access returns HTTP 403 and the denied attempt is written to the audit log.
- Demo ("Explore demo") data lives in a separate namespace and never mixes with account data.

## 5. Audit logging

Every prescribing check, review conclusion, sign-in, trial event, and access-denied event is recorded with actor, timestamp, and details. The audit log is append-oriented and visible to the account owner.

## 6. Data handling

- Minimum-necessary principle: the copilot collects only the fields the dentist provides for the prescribing workflow.
- No clinical data in general analytics or marketing systems. Clinical data is never sold.
- Backups: currently the deployment server's database file. Formal backup, encryption-at-rest, and recovery procedures are **not yet in place** — required before production.

## 7. Incident response (outline)

1. **Detect:** server error logs and failed-auth monitoring; users report issues to abdelshafyclapps@gmail.com.
2. **Contain:** revoke affected sessions, disable compromised accounts.
3. **Assess:** determine what data was accessed.
4. **Notify:** affected account owners will be notified without unreasonable delay; regulatory notifications as required by applicable law.
5. **Remediate:** fix the root cause, rotate secrets, document the incident.

A formal tested incident-response plan is a pre-production requirement.

## 8. Responsible disclosure

If you find a security issue, email abdelshafyclapps@gmail.com with details. Please do not access other users' data or disrupt the service while investigating. We will acknowledge within 5 business days.

## 9. Pre-production security checklist (open items)

- [ ] Independent security review / penetration test
- [ ] Email verification + password reset + 2FA
- [ ] Encryption at rest and in transit (TLS) on production hosting
- [ ] Formal backup, retention, and disaster-recovery procedures
- [ ] HIPAA compliance program + BAA execution (if handling PHI)
- [ ] Tested incident-response plan
