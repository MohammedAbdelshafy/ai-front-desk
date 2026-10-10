# AI Front Desk

A fully-owned WhatsApp support agent build: **WhatsApp Business Cloud API + n8n + OpenAI**.
WhatsApp intake → qualification → human escalation → follow-up. No vendor lock-in.

Plus the **Mia Clinical Platform**: dental pre-visit intake + dentist-facing
patient-history dashboard, with reusable foundations (MiaShell character
component, versioned question bank, FHIR-compatible records) for future
specialties. Synthetic data only — not HIPAA-compliant, not for real patients.

## Mia Clinical Platform (demo)

- `ai_front_desk/clinical/question_bank.py` — versioned, conditional question
  bank with validation and FHIR R4 `Questionnaire` export.
- `ai_front_desk/clinical/dental_intake_v1.json` — dental pre-visit questionnaire
  v1.0.0 (identity, visit, medications incl. antibiotics, allergies, conditions,
  surgical history). **Status: draft — dentist review pending before any
  clinical use.**
- `ai_front_desk/clinical/intake.py` — intake processing: validation, omission
  and contradiction detection, FHIR `QuestionnaireResponse` export.
- `ai_front_desk/clinical/store.py` — SQLite dev store with tenant isolation
  and append-only audit log. See `docs/adr/001-clinical-data-store.md`.
- `ai_front_desk/clinical/dashboard.py` — dentist brief: patient-reported facts,
  labeled AI rollup, flags, corrections overlay (originals preserved).
- `ai_front_desk/clinical/mia_shell.py` — reusable MiaShell character manifest
  + honest task-stage tracker (Dental Mia included).
- `ai_front_desk/clinical/server.py` — stdlib demo server: mobile patient
  intake form, dentist dashboard, record brief, review/correction actions.

Run the demo:

```bash
python -m ai_front_desk.clinical.server
# open http://127.0.0.1:8766 — pick a demo clinic, complete an intake,
# then open the dentist dashboard. Synthetic data only.
```

Hard rules: no real patient data, no live messaging/booking, no medication
decision support in v1 (collect + present history only), every finding labeled
by source (patient_reported / system_check / ai_summary / clinician_entered).

## What's inside (WhatsApp reference)

- `ai_front_desk/logic.py` — the qualification state machine as pure, importable
  Python: greet → name → service → urgency → done, with FAQ answers and
  escalation triggers. No network calls — reuse it anywhere (n8n Code node,
  your own server, tests).
- `ai_front_desk/webhook.py` — local dev/test server (stdlib only) emulating the
  Meta webhook contract: GET verify (hub.mode/hub.verify_token/hub.challenge)
  and POST message callbacks. `DRY_RUN=1` (default) writes the would-be Graph
  reply payload instead of sending anything.
- `ai_front_desk/n8n_workflow.json` — the **production** workflow. Import into
  n8n: Webhook (Meta callbacks) → IF (verify challenge vs message event) →
  Set (extract sender/text) → OpenAI node (front-desk brain) →
  HTTP Request (POST reply to Graph API) → Respond 200.

## Install

```bash
pip install ai-front-desk
```

## Local test

```bash
VERIFY_TOKEN=mysecret PORT=8765 ai-front-desk-webhook
# then in another shell:
curl "http://127.0.0.1:8765/webhook?hub.mode=subscribe&hub.verify_token=mysecret&hub.challenge=ping"
```

Run the test suite: `pytest` (unit tests) — the webhook contract e2e spins up the
real server on localhost.

## Going live — Meta app setup checklist

1. Create an app at developers.facebook.com → add the **WhatsApp** product.
2. In WhatsApp → API Setup: note the **test phone number** and generate a
   **temporary access token** (later: a permanent system-user token).
3. Note the **Phone Number ID** from the same page.
4. Configure the webhook: callback URL = your public n8n webhook URL,
   verify token = your `VERIFY_TOKEN`, subscribe to the **messages** field.
5. On the n8n host set env vars: `VERIFY_TOKEN`, `WHATSAPP_TOKEN`,
   `PHONE_NUMBER_ID`. Add the OpenAI credential to the Front Desk Brain node
   and the HTTP Header Auth credential to the Reply node.
6. For production traffic beyond the test number, complete Meta's business
   verification and request messaging limits upgrades in the app dashboard.

## What it does not do

This is a reference build, not a managed service. You bring your own Meta app,
phone number, n8n host, and OpenAI key. No guaranteed response quality, lead
volume, or revenue — the state machine is deterministic and test-covered; the
AI reply quality depends on your own OpenAI configuration.

## License

MIT — Mohammed Abdelshafy.
