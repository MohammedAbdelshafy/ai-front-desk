# Dr. Mia Clinic OS

Dr. Mia Clinic OS is a clinic-operations product built around better-prepared visits, consistent patient follow-up, patient growth, and an owner-friendly daily quality view. The clinic-facing name and workflows are intended to be configurable by specialty; this repository currently contains a **dental intake demonstration**, not a production multi-specialty service.

> **Current status: synthetic-data prototype.** The local demo is not a deployed clinical service, EHR, or production patient-data system. It does not send live messages, place calls, book appointments, or provide medication recommendations. Do not enter real patient information.

The repository slug and Python package remain `ai-front-desk` for compatibility. The approved product display name is **Dr. Mia Clinic OS**.

## What the demo contains

- Versioned conditional dental history questionnaire, currently marked draft pending licensed dentist review.
- Validation for required answers, missing information, and contradictory responses.
- Clinician-facing history brief that distinguishes patient-reported answers from system checks and deterministic rollups.
- Correction overlays that preserve original answers and add an audit record.
- FHIR R4 `Questionnaire` and `QuestionnaireResponse` representations for interoperability experiments.
- Clinic-scoped local SQLite storage for submissions, reviews, corrections and audit events.
- Count-only operational event ledger with idempotency and clinic scoping.
- Daily count scorecard and synthetic demo events, explicitly labelled in the UI.
- Versioned workflow skills describing Foundation-style intake, missed-opportunity follow-up, reminders, no-show recovery, growth, daily/weekly scorecards, recall, and future clinician decision support.
- A local demo site with clear readiness labels for every workflow.

## Run the local demo

Requires Python 3.10+.

```bash
python -m pip install -e .
python -m pip install pytest
python -m ai_front_desk.clinical.server
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766). The server refuses non-loopback binding by design. It seeds two fictional demo clinics, synthetic patient-history submissions, and clearly labelled sample operational counts. The local SQLite file defaults to `~/.mia-clinical-demo/clinical-demo.sqlite3`; set `CLINICAL_DB` to override it.

### Demo routes

| Route | What it shows |
|---|---|
| `/` | Demo entry and clinic selection |
| `/intake?clinic=demo-smile-arts` | Synthetic patient-history form |
| `/dashboard?clinic=demo-smile-arts` | History queue plus daily count scorecard |
| `/record?clinic=demo-smile-arts&sub=<submission_id>` | Clinician brief, flags, review, corrections and audit trail |
| `/workflows` | Versioned workflow skills and their readiness state |
| `/api/scorecard?clinic=demo-smile-arts` | Daily scorecard JSON, data mode and limitations |
| `/api/workflow-skills` | Machine-readable workflow catalog |
| `/api/questions` | Question bank snapshot |
| `/api/fhir/questionnaire` | FHIR Questionnaire draft |
| `/api/fhir/questionnaire-response?clinic=demo-smile-arts&sub=<submission_id>` | FHIR QuestionnaireResponse for a synthetic submission |

Replace `demo-smile-arts` with `demo-lakeside` where needed.

## Capability readiness

| Capability | State | Honest limit |
|---|---|---|
| Pre-visit history | Demo only | Question bank is draft; qualified dentist review is pending |
| Missing/contradictory answer checks | Prototype implemented | Structural checks, not diagnosis or clinical interpretation |
| Clinician history brief | Prototype implemented | Clinician reviews original patient-reported answers |
| Daily operations scorecard | Limited implementation | Count-only; no attribution, ROI, or conversion rates inferred |
| Missed-call follow-up | Design only | No live telephony provider connected |
| Reminders and outbound messages | Design only | No production delivery, consent or opt-out configuration |
| No-show recovery | Design only | No trusted practice-management/attendance integration |
| Patient-growth marketing | Design only | No live campaigns or measured acquisition outcomes |
| Weekly quality scorecard | Design only | Requires agreed measures and reliable clinic events |
| Clinician prescribing assistant | Clinical review required | No enabled treatment pathways or autonomous medication advice |

The synthetic scorecard demonstrates a reporting shape only. It deliberately does not calculate recovered revenue, appointment conversion, time saved, or clinical outcomes from unrelated count totals.

## First paid offer

The established entry offer is the **$1,500 Quality-Audit Pilot**. Until production gates pass, scope it as a workflow review and implementation plan: current-state mapping, an agreed baseline using authorized aggregate/de-identified data, an intake/follow-up gap analysis, a sample report, and a prioritized action plan. Do not imply that this fee includes live patient-data processing or production deployment unless the signed scope and verified delivery explicitly say so.

Monthly package prices remain unset. Do not invent them in software copy.

## Before any clinic uses real patient information

Required release gates include:

1. Named clinic owner, written scope, and clinic-approved workflow.
2. Questionnaire reviewed and signed off by an appropriate licensed clinician.
3. Production identity and authentication, clinic tenant isolation, least privilege, and access tests.
4. Appropriate healthcare privacy/security and contractual review, including any required business-associate agreement.
5. Secure deployment, backup/restore, logging minimization, retention/deletion, incident response, and audit review.
6. Verified integrations with explicit consent, opt-out, idempotency, bounded retries, staff handoff and delivery-failure states.
7. Trusted scheduling confirmation. An appointment request must not be described as a booking until an authoritative scheduling source confirms it.
8. Clinic acceptance testing and a recorded baseline before reporting outcomes.

Never expose the local server to the public internet. Keep real-patient data out of the demo.

## Tests

```bash
python -m pip install -e .
python -m pytest -q
```

GitHub Actions runs the same suite on relevant branches and pull requests. Check the live run for the actual commit before stating that tests pass.

## Original WhatsApp reference flow

```bash
VERIFY_TOKEN=mysecret PORT=8765 ai-front-desk-webhook
# in another shell:
curl "http://127.0.0.1:8765/webhook?hub.mode=subscribe&hub.verify_token=mysecret&hub.challenge=ping"
```

Before enabling live messaging, the actual configuration needs provider signature verification, idempotency, tenant-scoped persistence, durable outbound retries, staff handoff, retention/deletion controls, and privacy/security review. Clinic-approved messages and applicable consent are required. An appointment request is not a confirmed booking unless a trusted scheduling workflow confirms it.

## Safety and product boundaries

- Administrative intake is separate from clinician decision support.
- A workflow-skill definition does not activate a live capability.
- Never claim live bookings, live messaging, a live model, production authentication, compliance certification, clinical validation, or outcomes unless independently verified.
- Keep live calls, texts, bookings and real-patient data disabled until their release gates pass.
- Monthly prices are unset; the $1,500 audit is a paid workflow-audit offer, not an assertion that production software is deployed.

## License

MIT — Mohammed Abdelshafy.
