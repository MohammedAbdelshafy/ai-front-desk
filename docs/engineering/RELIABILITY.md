# Mia Dental OS — Reliability Engineering Standard

**Status:** living standard, v1.0 — 2026-10-11. Every future change to
`ai_front_desk/clinical/prescribe/` is held to these four rules.

The founder's non-negotiables: **the app can't lag, can't make mistakes,
can't lose info, can't get hacked.** This document codifies what each means,
how the code enforces it, how to verify it, and the checklist for new features.

---

## 1. CAN'T LAG (performance)

**What it means:** every page renders in under 300ms on local hardware; one
slow request never blocks others.

**How the code enforces it:**
- `server.py`: `ThreadingHTTPServer` (aliased as `HTTPServer`) — each request
  gets its own thread. A slow client or a long check never head-of-line-blocks
  the next dentist.
- `store.py`: `LockedConnection` serializes every statement through one
  re-entrant lock. The stores share a single SQLite connection each, and
  `check_same_thread=False` does NOT make concurrent use safe — without this,
  simultaneous requests corrupt reads/writes (`InterfaceError`).
- `store.py` / `accounts.py`: SQLite `PRAGMA journal_mode=WAL` (readers never
  block writers), `synchronous=NORMAL` (safe with WAL — only a full OS crash,
  not a process kill, can lose the un-checkpointed tail), `busy_timeout=5000`
  (transient write contention waits instead of erroring), `foreign_keys=ON`.
- Indexes on every hot path: `prescribe_patients(clinic_id)`,
  `prescribe_checks(clinic_id)`, `prescribe_checks(patient_id)`,
  `prescribe_audit(clinic_id, created_at)`, `prescribe_sessions(account_id)`.
- `MAX_BODY` (64 KiB) is enforced **before** parsing — oversized bodies get an
  immediate 413 instead of being read and truncated.

**How to verify:**
```bash
/tmp/pv/bin/python -m pytest tests/test_prescribe_reliability.py -q
```
The benchmark test walks signup → wizard (all 7 steps) → check and asserts
every page < 300ms. Recent numbers (local VM, 2026-10-11): see test output —
all pages render in single-digit to tens of milliseconds.

---

## 2. CAN'T MAKE MISTAKES (correctness)

**What it means:** the server never trusts the client about workflow state.
Steps happen in order, required answers are required, and doing the same
action twice never creates duplicates.

**How the code enforces it:**
- `wizard.py`: every wizard tracks `steps_done`. `step_is_unlocked()` gates
  both GET (redirects to the first incomplete step) and POST (409 if a step is
  submitted out of order). `can_finish()` requires all five POST steps plus a
  non-empty indication before the check is created.
- Idempotent finish: `WizardSessions.claim_finish()` atomically reserves the
  finish under the wizard lock. A double-submit (double-click, retry, or two
  concurrent requests) returns the *existing* check — never a duplicate.
  If check creation fails mid-way, the claim is released so the dentist can
  retry instead of being stuck.
- `accounts.py`: billing state transitions are validated — e.g.
  `mark_payment_pending()` raises `ValueError` if the account is already
  subscribed (subscribed → pending is impossible).
- Unknown/missing clinical data is never presented as verified-safe:
  missing answers become info-severity flags, and the verdict stays
  `CANNOT_VERIFY` rather than flipping green.

**How to verify:**
```bash
/tmp/pv/bin/python -m pytest tests/test_prescribe_reliability.py -q -k "wizard or finish or transition or double"
```
Covers: skipped-step POSTs rejected, out-of-order GETs redirected, double
finish returns one check, concurrent finishes create exactly one check,
subscribed→pending rejected.

---

## 3. CAN'T LOSE INFO (durability)

**What it means:** once the app says "done", the data survives a `kill -9`.
Every mutation commits before the response is sent.

**How the code enforces it:**
- Every mutating store method (`add_patient`, `record_check`,
  `set_review_state`, `create_account`, `mark_*`, session writes) calls
  `commit()` before returning — the HTTP handler only responds afterwards.
- `/api/invite` (file-based) flushes + `os.fsync()`s before replying.
- WAL + `synchronous=NORMAL`: committed transactions survive process death.
  (Only a kernel/OS crash could lose the un-checkpointed tail — accepted and
  documented; the backup cadence covers it.)
- Backup: `python -m ai_front_desk.clinical.prescribe.admin backup <dest>`
  uses the SQLite backup API — a consistent hot copy, safe while serving
  traffic, verified on write (checks the tables exist in the backup).

**Restore (one paragraph):** stop the app server, copy the backup file over
the live database path (`$PRESCRIBE_DB`, default
`~/.mia-prescribe/prescribe-demo.sqlite3`), delete any `-wal`/`-shm` files
next to it if present, restart the server, and sign in to confirm your
patients and check history are intact.

**How to verify:**
```bash
/tmp/pv/bin/python -m pytest tests/test_prescribe_reliability.py -q -k "crash or backup or commit"
```
The crash test starts a real server subprocess, writes a patient + check over
HTTP, `kill -9`s the server mid-flow, restarts, and asserts the data is
intact. The backup test round-trips backup → restore → data verified.

---

## 4. CAN'T GET HACKED (security)

**What it means:** standard web attacks don't work — CSRF, session fixation,
version disclosure, oversized-body smuggling, and error-message leakage are
all closed.

**How the code enforces it:**
- **CSRF:** every session carries a random per-session `csrf_token`
  (`accounts.py`, generated at `create_session`). `_csrf_field(ctx)` injects
  it into every authenticated state-changing form (central helper). Every
  non-exempt POST validates it with `secrets.compare_digest`; missing/invalid
  → 403 + audited. Exempt: `/api/signup`, `/api/signin` (no session exists
  yet — rate-limited instead), `/api/invite` (public lead capture, no session).
  Signout is POST + CSRF (GET `/signout` no longer changes state).
- **No version disclosure:** `Handler.version_string()` returns `""` — the
  `Server` header reveals nothing about the product or Python version.
- **413 before parse:** bodies over `MAX_BODY` are rejected before reading a
  single byte (no truncation, no keep-alive smuggling).
- **No tracebacks to clients:** `do_GET`/`do_POST` are wrapped; any unhandled
  exception is logged server-side and the client gets a generic 500
  (JSON for `/api/*`, plain page otherwise).
- **Session fixation impossible:** `create_session()` mints a fresh
  `secrets.token_urlsafe(32)` bearer token on *every* signin — the pre-login
  token (if any) is never reused. Verified by test.
- **Defense in depth (already present):** CSP with `script-src 'none'`,
  `X-Frame-Options: DENY`, `HttpOnly; SameSite=Lax` cookies (+ `Secure` flag
  via `PRESCRIBE_SECURE_COOKIES=1`), PBKDF2-HMAC-SHA256 passwords (200k
  iterations), per-account tenant isolation, signup/signin throttles, input
  caps, auth-event audit trail.

**How to verify:**
```bash
/tmp/pv/bin/python -m pytest tests/test_prescribe_reliability.py tests/test_prescribe_security.py -q
```
Covers: POST without CSRF → 403, wrong CSRF → 403, valid → works, Server
header empty, oversized body → 413, forced exception → generic 500 with no
traceback, fresh token on every signin.

---

## New-feature checklist

Before any PR merges, answer all four:

1. **Does it lag?** — New queries need indexes on their WHERE clauses. New
   pages must stay < 300ms in the benchmark. No unbounded result sets
   (paginate or cap).
2. **Can it mistake?** — Never trust client-supplied workflow state.
   Multi-step flows: server-side step tracking like the wizard. Any
   create-on-POST: make it idempotent (claim pattern) or reject duplicates.
   State transitions: validate in the store method, not the handler.
3. **Can it lose?** — Every mutation commits before the response. File
   writes get flush + fsync. Ask: "if I `kill -9` right after this line,
   is the user's data safe?"
4. **Can it be hacked?** — New POST route: does it need CSRF? (If it changes
   state and has a session: yes.) New inputs: capped lengths, validated
   values, escaped output (`esc()`). New errors: generic to the client,
   detailed only in server logs. New headers/cookies: check the security
   header list still applies.

Then: add regression tests, run the full suite green, and update this
document if the change introduces a new pattern.
