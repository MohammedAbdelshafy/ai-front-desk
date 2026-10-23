# AI Front Desk

A WhatsApp support-agent reference build using **WhatsApp Business Cloud API + n8n + OpenAI**. WhatsApp intake → qualification → human escalation → follow-up. No vendor lock-in.

This repository now also contains the **Mia Clinical Platform demo**: dental pre-visit intake plus a dentist-facing history dashboard, with reusable foundations for future specialties. The clinical demo uses synthetic data only and is not suitable for real patient records.

## What's inside

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

## Mia medication review (experimental scaffold)

A local, synthetic-only clinician review screen is available at
`/medication-review?clinic=demo-smile-arts` when the local server is running.
It provides the same rule-engine interface for **dentistry** and **gynecology**.
The API currently uses an intentionally empty, draft catalogue, so it will not
return medication options. The initial scope is source-backed clinician
education and safety checks, not autonomous diagnosis or prescribing.

Do not enter real patient data. Nothing is persisted by the medication-review
endpoint, and it does not create, sign, or transmit prescriptions. A missing
candidate is not a recommendation to withhold treatment. Each medication
entry and its rules require qualified specialty-clinician and medication-safety
review before the entry can be enabled. The code, empty catalogue contract,
specialty-pack activation gates and known production blockers are documented in
[`docs/MIA_MEDICATION_SUPPORT_V1.md`](docs/MIA_MEDICATION_SUPPORT_V1.md).

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
