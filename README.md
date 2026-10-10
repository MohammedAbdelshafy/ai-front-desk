# Mia Dental OS

**The prescribing safety copilot for young dentists.** Mia Dental OS is an AI front-desk platform for dental clinics. Its entry module, the **Mia Dental Prescribing Copilot**, is a prescribing safety *reference aid*: it walks the dentist through a guided 7-step check — indication, patient factors, allergies, current medications, conditions — and returns a cited safety review (clear / caution / do-not-use / cannot-verify) before the dentist makes their own call.

Mia is the employee you hire for your clinic's departments — an AI operator that shows its work. She never prescribes, never signs orders, never diagnoses, and the dentist always decides.

> **Honest status (read first):** Mia Dental OS is a **working demo using synthetic data only**. It is **not publicly deployed yet**, it is **not live with any clinic**, and the prescribing reference data is **awaiting qualified dentist review**. Everything here is **founding-pilot / prelaunch**. There are no customers, no clinical validation claims, and no real patient data anywhere in this repository.

## Pricing

- **$99/month**, with a **7-day free trial**.
- Billing today is **manual via Neteller**: send $99 to **abdelshafyclapps@gmail.com**, then message us and the founder activates your account by hand. No automatic checkout yet.

## Try the demo

The prescribing copilot runs locally (standard-library Python only, no dependencies to install):

```bash
python -m ai_front_desk.clinical.prescribe.server
```

Open **http://127.0.0.1:8767**. Run the guided wizard, try a penicillin-allergy scenario, and watch the safety review flag it with citations.

A public hosted demo is coming after the founder's hosting setup — no public URL yet.

## What's inside (prescribing module)

- `ai_front_desk/clinical/prescribe/server.py`: the Mia Dental OS web app — landing page, signup/signin, 7-step wizard, safety review, trial/subscription state, dentist review workflow, legal pages.
- `ai_front_desk/clinical/prescribe/reference_data.py`: the cited reference library (DailyMed/FDA labels, ADA and WHO guidance). **Draft — requires qualified dentist review before any clinical use.**
- `ai_front_desk/clinical/prescribe/wizard.py`: the guided intake flow with missing-information flags (missing info never renders as "safe").
- `ai_front_desk/clinical/prescribe/accounts.py`, `billing.py`, `trial.py`: per-account isolation, manual Neteller billing, 7-day trial lifecycle.
- `docs/review/`: the dentist review packet (generated from the reference data) — ready to send to a reviewing dentist.
- `docs/legal/`: draft privacy, terms, security, and clinical-limitation documents (require qualified legal review before production use).

> The prescribing module is in active development on branch `build/dental-mia-prescribe-2026-10-11` (draft PR #6, not yet merged into `main`).

---

## Also in this repo: AI Front Desk (reference build)

A WhatsApp support-agent reference build using **WhatsApp Business Cloud API + n8n + OpenAI**. WhatsApp intake → qualification → human escalation → follow-up. No vendor lock-in.

This repository also contains the **Mia Clinical Platform demo**: dental pre-visit intake plus a dentist-facing history dashboard, with reusable foundations for future specialties. The clinical demo uses synthetic data only and is not suitable for real patient records.

### What's inside

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

### Run the Mia Clinical demo

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

This repository is a reference build, not a managed service. Do not claim that it is HIPAA-compliant, clinically validated, or safe for production patient data. The dental questionnaire and the prescribing reference data remain drafts pending qualified dentist review. They only capture and organize information; they do not diagnose, prescribe, recommend medicines, or replace a clinician.

## License

MIT — Mohammed Abdelshafy.
