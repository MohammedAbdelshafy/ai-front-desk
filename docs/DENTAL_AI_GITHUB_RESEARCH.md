# Dental AI — repository and product research
**Reviewed:** 2026-10-10  
This list is a component evaluation, not a recommendation to install all projects. Recheck maintenance, licences, hosting and healthcare contracts before adoption.

## Best-fitting components
### Existing first-party base
- `MohammedAbdelshafy/ai-front-desk`: https://github.com/MohammedAbdelshafy/ai-front-desk
  - Current branch `main`; initial release commit dated 2026-10-06.
  - Python deterministic qualification logic, Meta webhook test harness with DRY_RUN default, n8n Cloud API workflow and tests.
  - README documents it as a reference build, not a managed service. It uses a generic services-business vocabulary and in-memory sessions; clinic FAQ hours are hard-coded examples. That must not ship as clinic truth.
  - Decision: extend this repo for the sellable wedge. Avoid duplicate app scaffolding.
### Open-source components worth evaluating
- Chatwoot: https://github.com/chatwoot/chatwoot
  - Open-source omnichannel staff inbox, with web chat and WhatsApp and other channels. MIT license is stated by the project.
  - Use only if a shared staff inbox saves implementation time. It is not the core clinic workflow engine.
- Evolution API: https://github.com/evolution-foundation/evolution-api
  - WhatsApp/multichannel REST API, supports WhatsApp Cloud API and a Baileys-based pathway, plus integrations.
  - Prefer official Meta WhatsApp Cloud API for production where possible; Baileys/WhatsApp-Web-dependent routes may have policy, reliability, and account-risk trade-offs. Review Evolution licence and additional conditions before redistribution.
- n8n: https://github.com/n8n-io/n8n
  - Best orchestration layer for webhook → validation → AI → messaging and notifications. Check the current Sustainable Use License and commercial/embedding limitations before packaging or reselling n8n itself.
- Dify: https://github.com/langgenius/dify
  - Agent/workflow, RAG, model management and observability platform. Good for fast experimentation; adds deployment footprint and another system to secure, so defer unless it clearly accelerates clinic-specific knowledge workflows.
- LiveKit Agents: https://github.com/livekit/agents
  - Active realtime voice AI framework, telephony integration and built-in agent tests. Future voice channel option; do not make it a prerequisite for the first text/WhatsApp pilot.
- Existing workflow example: https://github.com/YonaidisSoto/Whatsapp-Automation
  - n8n + Evolution API + OpenAI example adapted from a dental clinic receptionist to a hotel reservation flow. Useful for patterns only, not a validated product or production reference.
### Official interoperability options
- Open Dental API: https://www.opendental.com/site/apispecification.html
  - Official REST API covers resources including appointments, supports GET/POST/PUT/DELETE; developer must have a Business Associate Agreement with clients as stated by vendor. Integrate only after clinic-specific access and API permissions are agreed.
- NexHealth Synchronizer: https://docs.nexhealth.com/docs/whats-possible-with-nexhealth
  - Commercial integration option across multiple dental/medical practice-management systems, with APIs for scheduling, messaging, recalls, forms and more. Evaluate pricing, access and BAA terms directly.
- Chatwoot GitHub: https://github.com/chatwoot/chatwoot
- Meta WhatsApp Business Platform: use official Cloud API, approved templates and Meta policy-aligned opt-in/messaging rules.

## Competitive products and lessons
- Weave AI Receptionist: https://www.getweave.com/ai-receptionist/
  - Markets phone/text reception, FAQs, staff handoff, and scheduling for qualified practice-management systems. Generic receptionist capability is already competitive; differentiate on hands-on implementation, clear measurement, clinic-specific configuration, multi-location rollout, plus discoverability services.
- NexHealth: https://www.nexhealth.com/
  - Strong scheduling, messaging, recall, forms, payments and interoperability positioning; marketed as trusted by 20,000+ practices at time of review. Avoid building a replacement PMS or broad synchronization layer before demand.
- ADA HPI AI adoption research surfaced a July 2026 snapshot: 43.3% of responding US dentists reported AI use in at least one practice task; 26.4% said they planned future adoption; insurance verification and reception/check-in appeared as named use cases. Use the original ADA report to verify exact survey denominator and wording before external marketing.
- Existing internal report: `Dental_AI_Case_Study_Report.pdf` describes conversational recommendation workflows, structured FAQ, semantic categorization, treatment pages, local intent mapping, and AI-search discoverability. It is a strategic visibility report, not evidence of clinical validation, live product deployment, guaranteed rankings, or patient outcomes.

## Product design rules
1. Solve patient access + request capture + human handoff first.
2. Store no more patient data than needed; separate tenants, audit access, define retention/deletion.
3. AI cannot invent clinic hours, prices, insurance acceptance, availability, policies, clinical claims or completed bookings.
4. The clinic approves knowledge and patient communication language.
5. Medical/emergency or treatment advice goes to clinic-defined human escalation; no autonomous diagnosis or treatment recommendations in first release.
6. Keep data-plane side effects behind explicit feature flags and audit logs.
7. HIPAA obligations depend on the actual data flow and role. HHS explicitly lists some third-party healthcare chatbot vendors handling PHI as business associates; execute appropriate BAAs and risk analysis where applicable. Do not market as HIPAA compliant merely because an underlying vendor advertises security.
8. Before any AI-initiated voice call, complete telecom legal review. HIPAA and TCPA are separate concerns.
9. Establish Week-0 baseline for each clinic; all conversion and ROI claims must be calculated from real, attributable events.

## Excluded for the first release
- Autonomous clinical diagnosis/treatment recommendations, dental image analysis, insurance adjudication, autonomous PMS writes, patient payment processing, voice outbound calls, bulk recall campaigns, and multi-clinic rollout automation.
- No autonomous sends or external messages activated by this documentation commit.
