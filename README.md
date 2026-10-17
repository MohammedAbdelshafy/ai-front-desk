# Dr. Mia — AI Front Desk & Dental Clinic Copilot

Dr. Mia is the dental-practice product direction built on this AI Front Desk repository: a friendly, character-led assistant designed to help clinics respond to patient inquiries, capture appointment requests that arrive after hours, prepare patient histories before visits, and make follow-up more consistent.

**Core product promise:** fewer patient inquiries falling through the cracks, better-prepared consultations, and clearer handoffs between patients and clinic staff. The aim is to reduce repetitive administration, while measuring real outcomes in a clinic pilot rather than promising unverified savings or revenue.

> **Status:** This repository contains reference workflows and a local clinical demo, not a live managed service. Phone answering, live outbound messages, production scheduling, public review campaigns, and medication decision support are not currently shipped. The clinical demo uses synthetic data only.

## Dr. Mia product direction

The proposed product is organized into modules so a practice can start with patient access and expand only when the workflow is proven.

- **AI Front Desk — planned:** work toward after-hours and overflow inquiry capture, including a future phone/voice integration. The assistant should collect a caller's reason for contacting the clinic, preferred callback details, and appointment preferences, answer only clinic-approved administrative questions, and route requests to staff. A request must never be described as a confirmed appointment unless a trusted scheduling workflow confirms it.
- **Smart Patient Intake — prototype:** a pre-visit dental history workflow and dentist-facing history dashboard. The questionnaire is still a draft and requires review by a qualified dentist before clinical use.
- **Appointment messaging — planned:** send booking confirmations and reminders from verified scheduling events, including a one-hour reminder when enabled by the clinic, plus appropriate post-visit follow-up.
- **Patient feedback — planned:** gather feedback about waiting time, communication, comfort, and the overall experience; summarize patterns for the practice to improve. Public review invitations should be neutral and must not be gated on private feedback scores.
- **Optional Growth / Lead Engine — proposed add-on:** help practices capture and track new-patient campaign inquiries, route callbacks, and run approved follow-up. Marketing outreach needs its own appropriate permission and opt-out. Clinical records must not be repurposed as a marketing list.
- **Clinician-facing medication support — future concept, not in the MVP:** potentially provide dentists with evidence-linked medication information and patient-specific safety checks for clinician review. It must not independently diagnose, prescribe, or send medication orders, and requires qualified clinical governance and jurisdiction-specific review before real-world use.

See [Dr. Mia product positioning and copy](docs/DR_MIA_PRODUCT_POSITIONING.md) for the fuller feature descriptions and honest launch messaging.

## What's in this repository today

- `ai_front_desk/logic.py`: generic qualification state machine as pure, importable Python.
- `ai_front_desk/webhook.py`: local development/test harness for the Meta webhook contract. `DRY_RUN=1` by default.
- `ai_front_desk/n8n_workflow.json`: reference WhatsApp Cloud API workflow.
- `ai_front_desk/dental_logic.py`: early dental administrative intake logic, approved FAQ handling, and human handoff.
- `ai_front_desk/clinical/question_bank.py`: versioned conditional question bank and FHIR R4 Questionnaire export.
- `ai_front_desk/clinical/dental_intake_v1.json`: dental health-history form, currently a draft awaiting qualified dentist review.
- `ai_front_desk/clinical/intake.py`: validation, missing-answer and contradiction checks, FHIR QuestionnaireResponse export.
- `ai_front_desk/clinical/store.py`: local SQLite development store with clinic scoping and an audit log.
- `ai_front_desk/clinical/dashboard.py`: dentist-facing history brief with patient-reported answers, system-check flags, and a deterministic structured rollup. It is not AI-generated clinical interpretation.
- `ai_front_desk/clinical/mia_shell.py`: Dental Mia character manifest and task-stage model.
- `ai_front_desk/clinical/server.py`: local demo server with patient intake, dentist dashboard, record review, corrections, audit history, and FHIR export endpoints.
- `docs/DENTAL_AI_MVP_BUILD_SPEC.md`, `docs/DENTAL_AI_GITHUB_RESEARCH.md`, `docs/DENTAL_AI_PRODUCTION_REFERENCE.md`: scope, research, and production architecture notes.
- `docs/MIA_CLINICAL_PLATFORM_BUILD_PLAN.md`: multi-app Mia runtime and multi-specialty clinical platform plan.
- `docs/DR_MIA_PRODUCT_POSITIONING.md`: product narrative, module descriptions, proposed add-on, and honest claims boundary.
- `docs/adr/001-clinical-data-store.md`: development storage decision and production prerequisites.

## Run the Mia Clinical demo

Requires Python 3.9 or newer. From the repository root:

```bash
python -m pip install -e .
python -m ai_front_desk.clinical.server
```

Open **http://127.0.0.1:8766**. Pick a fictional demo clinic, submit a fictional history, and then inspect the dentist dashboard. The server deliberately binds to loopback only.

The demo database is stored at `~/.mia-clinical-demo/clinical-demo.sqlite3` by default. Set `CLINICAL_DB` to override the local path. This is a development prototype, not an EHR.

**Do not enter real patient data.** The questionnaire is marked draft and must be reviewed and approved by a qualified dentist before clinical use. The prototype has no production authentication, does not send messages or book appointments, and does not provide medication recommendations or autonomous clinical decisions. The Mia help conversation uses fixed local responses and is explicitly not a connected live AI model.

## Test

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest -q
```

The GitHub Actions workflow runs the test suite on relevant branches and pull requests. Check the actual workflow status before claiming a build is green.

## Original WhatsApp reference flow

```bash
VERIFY_TOKEN=mysecret PORT=8765 ai-front-desk-webhook
# in another shell:
curl "http://127.0.0.1:8765/webhook?hub.mode=subscribe&hub.verify_token=mysecret&hub.challenge=ping"
```

Before enabling live messaging, the actual configuration needs provider signature verification, idempotency, tenant-scoped persistence, durable outbound retries, staff handoff, retention/deletion controls, and privacy/security review. Clinic-approved messages and explicit consent are required. An appointment request is not a confirmed booking unless a trusted scheduling workflow confirms it.

## Safety and claims

This repository is a reference build, not a managed service. Do not claim that it is HIPAA-compliant, clinically validated, or safe for production patient data. The dental questionnaire remains a draft pending qualified dentist review. It only captures and organizes information; it does not diagnose, prescribe, recommend medicines, or replace a clinician.

## License

MIT — Mohammed Abdelshafy.
