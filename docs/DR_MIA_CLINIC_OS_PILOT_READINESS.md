# Dr. Mia Clinic OS — Pilot Readiness Record

**Review date:** 2026-10-28  
**Product display name:** Dr. Mia Clinic OS  
**Current demonstration specialty:** Dentistry  
**Current status:** Synthetic-data prototype; demo readiness is distinct from production-pilot readiness.  
**Entry offer:** $1,500 Quality-Audit Pilot. Monthly package prices remain intentionally unset.

## What this build can demonstrate

- A fictional patient completes a versioned pre-visit dental history questionnaire.
- The intake validator identifies missing required answers and structural contradictions.
- The clinician view separates patient-reported answers, system-check flags, deterministic rollups, and staff corrections.
- Reviews and corrections are recorded in a local audit trail.
- The local demo seeds fictional patient records and a visibly synthetic daily operations scorecard.
- A count-only operational event ledger deduplicates events and scopes queries by clinic.
- A workflow registry explains each planned outcome, inputs, outputs, guardrails and current readiness state.

## Readiness matrix

| Area | State | Evidence / limitation |
|---|---|---|
| Pre-visit questionnaire | Demo only | Question bank remains draft |
| Intake validation | Prototype | Structural validation only; not clinical reasoning |
| Clinician history brief | Prototype | Qualified clinician reviews original patient-reported answers |
| Local records and audit | Development only | Local SQLite; the demo selector is not production authentication |
| Daily scorecard | Limited implementation | Count-only events; no inferred ROI or conversion |
| Missed-call recovery | Not live | Workflow definition only; no live telephony provider |
| Reminders and messaging | Not live | No production messaging, consent or delivery path |
| No-show recovery | Not live | No trusted practice-management/attendance connection |
| Patient growth | Not live | No live campaign connection or measured patient-acquisition results |
| Weekly quality scorecard | Not live | Metrics and thresholds need clinic agreement |
| Prescribing assistant | Clinical review required | No approved pathways or autonomous prescribing |

## Incomplete data: do not fabricate completion

The dental question bank currently has `review_status = draft` and blank reviewer/date fields. Do not fill these with invented credentials or dates. The correct resolution is for a named, qualified dentist to review the exact version, record their decision/date, and document requested changes.

All seeded patients and operational events remain synthetic. Synthetic counts are not evidence of clinic performance, demand, missed-call rates, patient outcomes or recovered revenue.

## Accepted scope for the $1,500 audit

The Quality-Audit Pilot can be sold as a bounded professional service while live software remains gated:

1. Confirm owner/manager, specialty, locations, existing workflow and practice-management vendor.
2. Map patient history from booking through staff preparation and clinical review.
3. Establish a baseline using clinic-approved aggregate/de-identified data and agreed time observations. Do not upload PHI into this demo.
4. Review missed-inquiry, reminder, no-show and follow-up processes against clinic policy and authorized data.
5. Deliver a prioritized gap register, process map, measurable scorecard definition and proposed rollout.
6. Offer a separate implementation/retainer scope only for capabilities that are operationally ready and contractually included.

## Gates before real patient records, live messaging or booking

- [ ] Written clinic scope, owner and named implementation approver.
- [ ] Qualified clinician approves questionnaire and clinical/escalation wording.
- [ ] Production identity, access controls, tenant isolation and security tests.
- [ ] Appropriate privacy/security assessment and contracts, including a BAA if applicable.
- [ ] Approved hosting, secrets management, logging minimization, backups, retention/deletion and incident response.
- [ ] Provider signature validation, idempotency, durable outbox, bounded retries/dead letters and staff handoff.
- [ ] Communication consent, opt-out, operating hours and clinic-approved templates.
- [ ] Trusted scheduling integration and booking-confirmation semantics.
- [ ] Integration tests, end-to-end smoke test, clinic acceptance and rollback plan.
- [ ] Baseline and metric definitions recorded before outcome claims.

## Local demo acceptance checklist

- [ ] Run `python -m pytest -q` and inspect Actions for the exact commit.
- [ ] Start only on `127.0.0.1`; verify public binding is refused.
- [ ] Open home and choose a fictional clinic.
- [ ] Show the synthetic patient queue and visibly synthetic scorecard.
- [ ] Open a history brief and demonstrate flags, source labels, correction/review and audit trail.
- [ ] Open `/workflows` to show readiness labels.
- [ ] Confirm no outbound calls, messages, reminders or bookings are triggered.
- [ ] Tell the clinic this is a prototype preview; synthetic counts are not its results.

## Definition of a successful audit

Success means the clinic has a useful current-state process map, an agreed baseline definition, a prioritized action plan, and a decision about whether a production implementation is appropriate. It does **not** require representing this prototype as already connected to the clinic.
