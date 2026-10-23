# Dental AI Clinic Assistant — MVP Build Specification
**Date:** 2026-10-10
**Status:** Build spec only. Do not represent unimplemented capabilities as shipped.

> **Strategy update — October 17, 2026:** This document recorded an earlier front-desk-first pilot recommendation. It is now superseded for product priority and go-to-market by [Dr. Mia Clinical Copilot MVP Spec](DR_MIA_CLINICAL_COPILOT_MVP_SPEC.md): clinical quality and evidence-linked prescribing support are the core product, while AI Front Desk and Growth / Lead Engine are optional add-ons. The implementation and safety constraints below remain reference material for those optional workflows.

## Decision
Extend `ai-front-desk`; do not start a parallel dental repository. The existing code already has a WhatsApp Cloud API + n8n + OpenAI reference flow, a Python qualification state machine, a Meta webhook harness, and automated tests. It is a generic reference implementation, not yet a dental product or managed service.

## Commercial wedge
Sell a single-site paid pilot that combines:
1. Patient-access assistant for approved clinic FAQs and service inquiries.
2. Missed-call / unanswered-message follow-up workflow, only after clinic-approved telecom and consent configuration.
3. Structured appointment request capture and staff handoff. Treat requests as requests until connected scheduling confirms the booking.
4. Simple operator dashboard / daily report with real events and auditable outcomes.

No autonomous diagnosis, treatment recommendations, insurance adjudication, emergency triage decisions, or write access to a dental PMS in MVP.

## Target customer
US dental practices, starting with DFW because an existing evidence-based DFW campaign exists. Prioritize an owner-controlled 1–3 location practice or an operationally accessible multi-site group. Use the 40-clinic fresh verified list as the initial sales universe; the list itself is external to this repo and must be revalidated at send/dial time. The 14-record frozen DFW campaign is a separate historical snapshot, not necessarily disjoint from the 40.

## MVP user journeys
### Patient
- Ask clinic-specific questions (hours, location, published services, insurance plans only when explicitly verified by the clinic, new-patient process).
- Request an appointment, preferred time window, service category, and callback method.
- Receive clear acknowledgement and next step. No message claims appointment is booked unless a trusted PMS/API confirms it.
- Ask for a person at any point. Agent hands off and stops autonomous handling.
- Urgent symptoms/clinical questions receive clinic-approved safety wording and human referral; no diagnosis or automated decision.

### Staff
- See a human-readable conversation summary, requested service, desired time window, callback preference, urgency marker, and handoff reason.
- Accept, resolve, or correct a request.
- See pending callbacks and communication status.
- Review a pilot dashboard with baseline vs measured period. No invented loss/recovery estimates.

### Clinic configuration
- Clinic name, addresses, published hours, approved services, booking URL/phone, accepted insurance text if clinic-verified, approved policies, language settings, escalation destination and after-hours instructions.
- Version and timestamp each approved content update.
- Separate tenant and credentials for every clinic. No cross-tenant retrieval.

## Build boundaries
- Keep pure state/intent rules separate from channel adapters.
- Persist message deduplication by provider message ID; webhook retries must not send duplicate replies.
- Replace in-memory sessions with tenant-scoped persistence before production.
- Verify webhook signature per provider contract; validate event shape, ignore status-only / outbound echo events, and return quickly.
- Use idempotency keys and an outbox for external sends.
- Strict schema for AI output; fallback to deterministic FAQ or human handoff on parse/quality failure.
- Do not log full patient message bodies by default. Redact secrets and minimize any stored identifiers.
- Tenant ID comes from authenticated routing/configuration, never from arbitrary user-supplied input.
- Feature flags default off for live outbound actions.
- Retain DRY_RUN default. Never enable real sends, calls, SMS or scheduling without explicit clinic-level configuration and approved credentials.
- Metrics are event-derived only; maintain a human-auditable source-of-truth event log.

## Recommended stack
- Existing Python package and n8n workflow as the quick initial delivery path.
- Meta WhatsApp Cloud API for WhatsApp channel; n8n is orchestration, not the patient database.
- Postgres for tenant configuration, conversations metadata, appointment requests, handoff tasks, event log, and metrics.
- A thin staff UI, only after confirming the first pilot needs it; initial version can use a secured shared queue.
- Optional Chatwoot for staff inbox only if it materially reduces delivery time. Check data-flow, hosting, licence and HIPAA/BAA implications before handling ePHI.
- Optional LiveKit Agents later for voice; do not introduce voice until the channel, telephony consent, recording, retention, escalation and cost controls are tested.
- Open Dental or an integrator such as NexHealth only after validating the target clinic's PMS, API terms and integration access. Start with request capture + staff confirmation, not silent appointment writes.

## Required tests
1. Meta webhook verification success/failure.
2. Malformed JSON and unexpected events safely rejected/acknowledged.
3. Duplicate message id does not duplicate external reply or request.
4. Tenant isolation across conversations and knowledge retrieval.
5. Unknown answer does not hallucinate policy, price, accepted insurance or availability.
6. Human request always escalates.
7. Clinical/emergency content follows preapproved routing text, makes no diagnosis.
8. Appointment request is never presented as confirmed booking without provider confirmation.
9. Outbound delivery fails safely and creates a visible staff task.
10. Data minimization, deletion/retention behavior and secrets never appear in logs.
11. DRY_RUN is default and external send requires an explicit per-tenant production flag.
12. Regression tests for original reference flow remain green.

## Pilot acceptance criteria
- One clinic approves all assistant content and escalation rules.
- Privacy/security and vendor contract review completed for the actual configuration.
- Staff can take over any conversation and see unhandled work.
- Every inbound message is either answered, queued for staff, or explicitly rejected; no silent drops.
- Duplicate webhook deliveries do not duplicate patient messages.
- One-week baseline and pilot metrics are recorded from real events.
- No public claim of recovered revenue or compliance status unless independently supported.
- Clinic owner signs off before production activation.

## Sales experiment
Offer a 30-day single-workflow pilot. Price tests:
- $500–$750 pilot fee, proposed not proven.
- Upsell only after validation; historical concept was $1,850/month + $1,500 setup.
Do not price before estimating telephony, messaging, model, onboarding and support cost.

Primary CTA: 10-minute workflow review. Ask for current inbound volume, unanswered call handling, callbacks, booking system, staff handoff, and Week-0 baseline. Outcome is either qualified pilot, nurture, or disqualified. Never assume missed calls exist from company size or multi-location structure alone.

## Execution order
1. Add dental config and pure domain logic with tests.
2. Harden webhook parser, signature validation, event dedupe and safe replies.
3. Add tenant-scoped persistence and audited event records.
4. Add staff handoff queue and appointment request records.
5. Add clinic FAQ/knowledge import with approvals/versioning.
6. Add real-channel integration under per-tenant feature flag and DRY_RUN tests.
7. Create demo tenant with fabricated, visibly synthetic demo data only.
8. Use first customer requirements before adding PMS integration, voice, recall campaigns or wider clinical features.
