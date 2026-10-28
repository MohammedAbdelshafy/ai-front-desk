# Dr. Mia Clinic OS — Repeatable Demo Runbook

## Safety status

This is a **local synthetic-data demo**. Never use real patient names, contact information, dates of birth, health histories, screenshots, or exports. The local server must stay on loopback. No live calls, texts, reminders, bookings, or clinical recommendations are performed.

## Start

```bash
python -m pip install -e .
python -m pip install pytest
python -m ai_front_desk.clinical.server
```

Open `http://127.0.0.1:8766`.

The SQLite file defaults to `~/.mia-clinical-demo/clinical-demo.sqlite3`. For a clean demonstration, set `CLINICAL_DB` to a unique temporary local path before starting. The demo seeds two fictional clinics, fictional patient-history submissions and sample operational counts.

## Demo sequence (8–10 minutes)

1. **Set context (30 seconds).** Dr. Mia Clinic OS is being developed around better-prepared visits, consistent follow-up, patient growth and owner visibility. The current runnable workflow is the patient-history demo.
2. **Show the intake (2 minutes).** Open `/intake?clinic=demo-smile-arts`. Submit only fictional answers with a label such as `Demo Patient Jordan`.
3. **Show the brief (2 minutes).** Open `/dashboard?clinic=demo-smile-arts`, select a sample patient, and review the history brief. Distinguish patient-reported answers, structural flags, corrections and clinician review.
4. **Show owner visibility (1 minute).** Point out the daily scorecard. Its status must say synthetic sample data. Counts are not conversion rates or revenue.
5. **Show workflow readiness (1 minute).** Open `/workflows`; explain demo-only, limited implementation, planned/not live and clinical-review-required statuses.
6. **Show the data contract (1 minute).** Open `/api/scorecard?clinic=demo-smile-arts` and `/api/workflow-skills`. Explain the reporting window, data mode and limitations.
7. **Close with the audit offer (1 minute).** The established $1,500 Quality-Audit Pilot maps the clinic's actual process and baseline, then delivers a prioritized action plan. Do not promise a live integration, measured savings or patient growth from this demo.

## Expected sample entities

- Demo clinics: `demo-smile-arts` and `demo-lakeside`.
- Synthetic submissions: `Demo Patient Casey` and `Demo Patient Riley`.
- Operational events have source `demo_synthetic`; the daily seed is idempotent per date, clinic, and event type.
- Workflow catalog includes nine versioned definitions with explicit readiness status.

## Before every demo

```bash
python -m pytest -q
```

Inspect the latest GitHub Actions result for the exact commit. A passing test suite is not a production security audit or clinical validation.

## Troubleshooting

- **Port busy:** start on a different loopback port; never bind the demo to a public interface.
- **Old sample records:** local SQLite persists. Set `CLINICAL_DB` to a new temporary file before restarting.
- **Scorecard says no events:** check the selected clinic and that demo initialization ran.
- **Questionnaire approval:** the current form is still draft. Do not describe it as clinically approved; request qualified dentist review before any real-patient workflow.
