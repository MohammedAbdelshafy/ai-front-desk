# AI Front Desk

A fully-owned WhatsApp support agent build: **WhatsApp Business Cloud API + n8n + OpenAI**.
WhatsApp intake → qualification → human escalation → follow-up. No vendor lock-in.

## What's inside

- `ai_front_desk/logic.py` — the generic qualification state machine as pure, importable Python. No network calls — reusable in n8n Code nodes, your server, and tests.
- `ai_front_desk/webhook.py` — local dev/test harness emulating the Meta webhook contract. `DRY_RUN=1` by default, so it doesn't send real replies.
- `ai_front_desk/n8n_workflow.json` — reference workflow for WhatsApp Cloud API webhook → extraction → assistant → Graph API reply.
- `ai_front_desk/dental_logic.py` — early dental-specific administrative intake state machine, clinic-approved FAQ handling, explicit follow-up permission, and staff handoff. Pure logic only, no external side effects.
- `tests/test_dental_logic.py` — focused guardrail tests for the dental prototype.
- `docs/DENTAL_AI_MVP_BUILD_SPEC.md` — product scope and deployment acceptance checklist.
- `docs/DENTAL_AI_GITHUB_RESEARCH.md` and `docs/DENTAL_AI_PRODUCTION_REFERENCE.md` — repository/product research and architecture references.

## Dental MVP status

The dental module is an early prototype, **not production clinic software**. It is not wired into the WhatsApp webhook and it does not persist conversations, send patient messages, book appointments, or provide clinical decision support. A user asking for an appointment is creating a request, not a confirmed booking.

Before a clinic pilot: connect persistent tenant-scoped storage, webhook signature verification, inbound message idempotency, a durable outbound queue, visible staff handoff, retention/deletion controls, and clinic-approved configuration. Complete the actual deployment's privacy/security and telecom review. Use synthetic data for demos; keep live message sending disabled until the clinic explicitly approves the configuration.

## Install

```bash
pip install ai-front-desk
```

## Local test

```bash
VERIFY_TOKEN=mysecret PORT=8765 ai-front-desk-webhook
# then in another shell:
curl "http://127.0.0.1:8765/webhook?hub.mode=subscribe&hub.verify_token=mysecret&hub.challenge=ping"
pytest
```

## Local dental intake demo

This prototype includes a local, end-to-end fictional patient intake and dentist-review workflow.

Install the project, then run the demo command:

    python -m pip install -e .
    ai-front-desk-demo

Open http://127.0.0.1:8765 in your browser. The server is deliberately restricted to
127.0.0.1 and stores its synthetic demo database at
~/.ai-front-desk/dental-demo.sqlite3 by default. Set DENTAL_DEMO_DB to choose a different
local path. Use fictional records only. The demo has no production authentication,
no messaging or booking integration, and no clinical decision-support or prescribing.

The dashboard includes a preloaded set of fictional records, a patient questionnaire,
a dentist-facing history summary, review outcomes, and a local audit trail. This is a
development prototype, not an EHR and not suitable for actual patient information.

## Going live — Meta app setup checklist

1. Create an app at developers.facebook.com → add the WhatsApp product.
2. In WhatsApp API Setup, note the test phone number, Phone Number ID, and temporary access token.
3. Configure the webhook callback URL and verify token, and subscribe to the messages field.
4. Configure secrets only in the host's secret store. Never commit access tokens.
5. Complete Meta business verification and messaging limit steps before production traffic.
6. For a dental deployment, finish the tenant persistence, idempotency, approved FAQ, staff handoff and privacy/security gates documented above before enabling any real messages.

## Scope and claims

This repository is a reference build, not a managed service. No guaranteed response quality, lead volume, patient recovery, or revenue. Generic FAQ examples are not clinic facts. Do not make HIPAA or other compliance claims without verifying the actual deployment and contracts.

## License

MIT — Mohammed Abdelshafy.
