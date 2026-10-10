# Dental AI — production architecture reference addendum
**Reviewed:** 2026-10-10

## Highest-signal new repository
### Hiberius / WhatsApp Receptionist
Repository: https://github.com/Hiberius/whatsapp-receptionist  
README: https://github.com/Hiberius/whatsapp-receptionist/blob/main/README.md

Its README describes a self-hostable MIT Next.js/React/TypeScript WhatsApp receptionist with calendar-based appointment booking, staff escalation, tenant-specific clinic/business settings, a durable outbox, retry/backoff and dead-letter handling, webhook idempotency, double-booking prevention via a database constraint, tenant RLS, and data access/deletion workflows. It advertises a large test suite (544 unit tests + 56 E2E in the README at the time checked). These are upstream project claims, not independently executed by this product team. The README also admits important gaps in tenant-isolation proof and cross-tenant admin tooling, a useful reminder not to trust badge counts as production assurance.

**How to use this reference:** borrow the architecture and acceptance-test ideas, not the entire codebase by default. Review current code, dependencies, licences, release status, security reports, and test commands before adopting. The current product's simpler Python/n8n base may still be faster for one pilot. If faster feature coverage becomes more important than reusing our base, run a structured comparison against this codebase before choosing a migration.

## Other current references
- Official Meta WhatsApp Business Platform / Cloud API: use it as the supported messaging path, validate webhook signatures and provider message ids, and observe messaging policy/templates and opt-in requirements.
- Open Dental API specification: https://www.opendental.com/site/apispecification.html. Its docs say API developers should have a Business Associate Agreement with clients. Treat this as an integration option, not a shortcut around privacy/legal review.
- NexHealth API: https://docs.nexhealth.com/docs/whats-possible-with-the-nexhealth-api. The API documentation describes access to data from 15+ practice-management systems and use cases including appointment scheduling, communications, reminders, recall, and forms. Validate vendor access, supported systems, contract terms, cost and BAA before designing against it.
- Chatwoot WhatsApp business integration: https://www.chatwoot.com/features/whatsapp-for-business. It describes official WhatsApp Business API integration, team assignment, private notes and an agent inbox. Potential staff inbox adapter; not a required component if our pilot needs only a simple queue.
- Weave AI dental clinic page: https://www.getweave.com/ai-dental-clinic/. Shows that AI reception is already a competitive category. Differentiate with practical implementation and transparent measured outcomes, not generic AI branding.
- LiveKit Agents: https://github.com/livekit/agents. Candidate future framework for real-time voice agents. Keep out of first release until phone consent, transfer, latency, interruption handling, telephony costs and legal review are covered.

## Updated architecture choice
1. Keep `ai-front-desk` as the current pilot base and maintain the pure dental domain module separately from the generic services flow.
2. Implement persistent tenant-scoped sessions, validated webhook events, message-id idempotency, durable outbox and explicit staff queue before any live clinic channel.
3. Start with text/WhatsApp patient inquiry + request capture + staff follow-up. Booking is a request, not a confirmation, until a trusted PMS or staff workflow confirms it.
4. Use clinic-approved FAQs; fail closed on unknown information, clinical questions, unknown insurance policies, unavailable prices or scheduling availability.
5. Add a small operator UI and measurable pilot metrics. Do not deploy a vector database, multi-agent framework, voice stack, or multi-PMS integration until the first customer requirement justifies it.
6. Consider Chatwoot for staff operations if building an inbox materially slows the pilot; consider NexHealth/Open Dental only after an actual clinic names its PMS.
7. Keep all outbound sends and calls off by default in test and preview environments; use synthetic demo data only.

## Test cases inspired by mature implementations
- Webhook signature failure rejects request without processing.
- Duplicate provider message id produces one effective conversation transition and one outbound send.
- Outbox retries back off and dead-letter after a bounded number of failures.
- Human handoff is a durable state: the bot cannot resume autonomous handling until an authorized staff action resets it.
- Appointment availability cannot double-book under concurrent requests.
- Every database read/write is tenant-scoped; test cross-tenant denial, not just helper functions.
- Patient request and consent events are auditable without default retention of full message bodies.
- Retention/deletion jobs match the written data policy.
- Human staff can reply and stop automation for that thread.
- Metrics are derived from recorded events and cannot be seeded from simulated results.

## Product and commercial decision
Do not migrate wholesale to a more elaborate upstream platform before validating a paying clinic. Use the upstream repository as a design benchmark and revisit adoption if the first live pilot makes persistent booking, tenant management, or the operator inbox the dominant bottleneck.
