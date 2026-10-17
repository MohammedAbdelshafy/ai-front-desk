# Mia Clinical Platform — Master Build Plan
**Date:** 2026-10-10  
**Status:** Research-derived architecture and execution plan. This document is a plan, not a claim that the described production capabilities are shipped.

> **Strategy update — October 17, 2026:** The product's core offer is now Dr. Mia Clinical Quality & Prescribing Copilot; smart intake supports that workflow, and front-desk/retention/lead-generation functions are optional upsells. Earlier commercial sequencing in this plan is superseded by [Dr. Mia Clinical Copilot MVP Spec](DR_MIA_CLINICAL_COPILOT_MVP_SPEC.md). The architecture, source-governance, privacy, clinical-review, and validation constraints remain applicable. The current workbench is a local synthetic-data prototype with zero approved medication evidence cards.

## Executive decision

Build **one reusable Mia experience and agent runtime**, then attach **versioned, evidence-backed specialty packs** to it. Start commercial validation with the dental pre-visit workflow because that is the clearest wedge already identified. Architect for every clinic niche and market, but do not try to clinically validate every specialty before the first paid pilot.

The initial product is not “a chatbot for every doctor.” It is:

1. A patient completes a medical/dental history before arriving.
2. A clinic-approved workflow captures medications (including current/recent antibiotics), allergies and reactions, chronic conditions, prior procedures, relevant symptoms and other specialty-specific history.
3. The dentist receives a structured, readable brief with missing or stale information clearly identified.
4. The clinician reviews and confirms the record.
5. Mia guides the patient or staff through the workflow, explains what is happening, and shows real progress.
6. Retention, appointment requests, staff handoff, and later evidence-linked clinician decision support expand around that core.

A claimed 10–15 minute saving is a hypothesis to measure in a pilot, not a guaranteed promise.

## Product principles

- **Mia is the universal experience, not a universal permission set.** Every application inherits a consistent character-led conversation, visible task stage, execution transparency, and handoff experience. Each app gets its own character configuration, voice, visual identity, permitted tools, instructions, and safety rules.
- **Clinical data is not the character's memory.** The UI/agent layer must not own the clinical record. Patient records, consent, access control, retention, and audit are maintained by a separate clinical-data layer.
- **One source of truth.** A question, clinical guideline, clinic rule, patient answer, consent, or approval has a version and provenance.
- **Evidence before eloquence.** Clinical outputs must distinguish patient-reported facts, clinician observations, derived summaries, and uncertain interpretations.
- **No autonomous prescribing.** Later clinical decision support may show evidence, medication safety checks, and clinician-facing options, but must never silently issue a prescription or replace a licensed professional's decision.
- **Build only what advances the pilot.** Reuse mature components; do not deploy an agent swarm, voice/video pipeline, or multiple EHR integrations just because they are available.
- **No false outcomes.** Do not invent appointment confirmations, time savings, recovered revenue, clinical accuracy, customer results, or compliance status.

## Current verified starting point

### First-party assets
- **[ai-front-desk](https://github.com/MohammedAbdelshafy/ai-front-desk):** Python domain logic, generic WhatsApp/n8n reference workflow, webhook harness, and a dental-specific pure logic module. The current README describes a reference build, not a managed clinical product. The dental PR [#3](https://github.com/MohammedAbdelshafy/ai-front-desk/pull/3) is still open and draft; it is not merged. Its CI passed 20 tests in the earlier verification run.
- **[Mia AI site](https://github.com/MohammedAbdelshafy/mia-ai-site):** existing Mia character assets, welcome experience, agent directory, and mission-stage visual ideas. The site is a standalone static experience, not yet a reusable application SDK. Reuse its assets and interaction learnings, but avoid breaking the current marketing site during product development.
- **Dental AI Hatchable prototype:** demo only. It does not yet provide production patient-data persistence, live messaging/booking, or clinical decision support. Keep synthetic data in demos.
- **[MVP build spec](DENTAL_AI_MVP_BUILD_SPEC.md)** and [research note](DENTAL_AI_GITHUB_RESEARCH.md) already record initial scope and implementation constraints.
- GitHub issues [#1](https://github.com/MohammedAbdelshafy/ai-front-desk/issues/1) and [#2](https://github.com/MohammedAbdelshafy/ai-front-desk/issues/2) already track the technical MVP and GTM pilot work. Preserve them instead of creating competing backlogs.

No clinic was contacted and no outreach was sent as part of this plan.

## Architecture recommendation

Use five clearly separated layers.

### 1. Mia Experience Runtime
A portable React/TypeScript UI package should eventually provide:
- Character presentation and app-specific theme/persona configuration.
- Conversation panel and accessible text-first fallback.
- Task stage with honest states: idle, listening, planning, working, waiting for input, awaiting approval, handing off, completed, and failed.
- Evidence of actions actually performed, progress events, cancellation, and recoverable errors.
- Voice/animation adapters added separately from core chat.
- Responsive/mobile-first UI, reduced-motion support, keyboard navigation, captions/transcripts, and clear AI identity.

Reuse the existing Mia artwork and “mission theatre” as visual references. Start with the existing character image/approved animation plus real task-stage events. Do not require a generated real-time talking head for the first clinical pilot.

Each product should supply a typed character manifest: character ID, name, greeting, visual asset, supported languages, tone, allowed actions/tools, domain pack IDs, handoff rules, and safety boundaries. Changing an avatar must not change permissions.

### 2. Mia Agent Runtime
Start with one orchestrator and explicit deterministic workflow states, not a swarm of autonomous agents. It should:
- Parse the user's goal and select an allowed workflow.
- Retrieve only authorized, tenant-scoped data.
- Call tools through typed adapters with explicit input/output schemas.
- Emit a trace/event after each real step.
- Verify results against expected conditions.
- Request approval before consequential external actions.
- Escalate to a human and stop autonomous actions after handoff.
- Support provider/model adapters so models can be changed without rewriting the application.

Keep domain decisions in testable Python/TypeScript functions rather than burying logic in prompts. Never treat model-generated text as verified state.

### 3. Clinical data and interoperability layer
Evaluate **Medplum** as the leading FHIR-based clinical data repository candidate before implementing a bespoke patient-data store. Its repository describes FHIR APIs, identity/access controls, an SDK, and React components. The hosted API documentation indicates FHIR R4/US Core support, so confirm the exact FHIR version, hosting model, terms, BAA availability, data residency, backup/restore, and tenant-isolation evidence before selecting it.

Use FHIR-compatible concepts for at minimum:
- Patient and Encounter
- Questionnaire and QuestionnaireResponse
- MedicationStatement for patient-reported medication use
- AllergyIntolerance for reported allergies/reactions
- Condition for condition history where appropriate
- Observation for relevant measured values
- Consent, Provenance/AuditEvent or equivalent auditable records as required by the implementation.

Use **FHIR R4-compatible representations for the first US interoperability spike** unless a target system explicitly requires another supported version. Do not invent a private questionnaire format that becomes impossible to map later. Preserve the original response as well as any normalized summary; never overwrite patient answers with an AI inference.

If Medplum's contract, hosting, or operational fit fails review, use a healthcare-suitable hosted database with server-enforced tenant isolation and an explicit FHIR mapping layer. Do not build a home-grown EHR.

### 4. Clinical knowledge and source registry
Maintain a separate curated library, not one giant prompt and not unreviewed web scraping. The registry should manage:
- Questions and reusable modules.
- Specialty and visit templates.
- Clinical practice guidelines and medicine references.
- Clinical reasoning/teaching frameworks.
- Market/jurisdiction rules and approved language variants.
- Source URL, source type, publication/version/effective date, jurisdiction, evidence type/strength, usage rights/licence, reviewer, review date, hash, supersession date, and enabled/retired state.
- Evaluation cases and known failure modes linked to each knowledge pack.

Keep educational reasoning methods separate from clinical recommendations. Universities are potential sources for open teaching materials and methods; current diagnosis/treatment guidance must be backed by applicable professional guidelines, official medicine references, regulators, and qualified clinical review. Do not copy restricted textbooks or course material into the corpus without permission. Do not imply university endorsement.

### 5. Channel and integration adapters
Start with the current WhatsApp Cloud API/reference workflow only if the first clinic confirms that channel. The core service, not n8n, must be the source of truth for state and idempotency. Use n8n for low-risk orchestration/notifications only after its current commercial-use terms are checked.

Every provider adapter must validate webhook signatures, deduplicate provider event IDs, use a durable idempotent outbox with bounded retries/dead-letter handling, and expose delivery failures to staff. Appointment requests are requests until the trusted booking system or staff confirms them.

Consider Chatwoot only if its shared inbox saves build time; its core and enterprise directory have different licensing terms. Consider the Open Dental API or a vendor such as NexHealth only after a pilot clinic confirms the exact PMS, permissions, terms, support and required agreements. Consider LiveKit Agents for realtime voice/telephony later; Pipecat is a credible Python-oriented alternative. Confirm model/add-on licences, hosting, contracts, voice recording/consent, latency, transfer, and cost before selecting a voice stack.

## Specialty-pack system

Make each specialty a versioned configuration and evidence package, not a separately forked AI product.

Each pack should define:
- Specialty ID, patient population, appointment types and target market.
- Questionnaire modules and conditional branching.
- Required/optional questions and "not known/not applicable/prefer not to answer" response behavior.
- Specialty-specific intake summary schema.
- Human handoff and emergency escalation rules approved for the market.
- Curated guideline/medicine source registry.
- Allowed clinical-support use cases and forbidden outputs.
- Clinician reviewers, approval status, version, review date and expiry/revalidation rules.
- An automated evaluation set, including under-specified cases, contraindications, contradictory answers and adversarial inputs.

Initial sequence:
1. **Dentistry:** general medical history, current/recent medicines and antibiotics, drug/latex allergies and reactions, relevant chronic conditions, surgical/anesthesia history, the reason for the visit, dental history, review/sign-off, and missing answers. Follow the ADA's current dental health-history guidance and require clinic approval.
2. **Primary care:** medication reconciliation, chronic conditions, symptoms, medical/surgical and family history, and clinic-specific review.
3. **Next specialties by customer evidence:** e.g. dermatology, cardiology, pediatrics, women's health, etc. Choose each pack only when a qualified reviewer and customer workflow are available.
4. Expand to the full specialty catalogue without claiming every pack is clinically validated on day one.

### Academic selection method
For every specialty, assemble a documented academic reference panel of up to three suitable institutions, based on relevant specialty departments, research, teaching materials available for lawful use, and published clinical-education frameworks. This is not a universal top-three ranking and should not be picked from overall university rankings alone.

For each proposed institution/material, record what it contributes: e.g. evidence-based medicine, problem/case-based learning, clinical reasoning, specialty training or patient safety. Never equate university prestige with a current treatment recommendation. Never scrape or embed closed courseware, textbooks, lecture recordings, or proprietary protocols without rights. The clinically authoritative layer remains applicable guidelines and approved drug information.

## Evidence-linked medication decision support: core product direction, not cleared for live prescribing

**Strategy update — October 17, 2026:** This is the core product direction, not a later optional module. However, the current prototype is only an evidence-retrieval foundation and has zero approved medication evidence cards. Do not sell or deploy it as a live prescribing capability. The first proof should be a narrow, supervised validation/shadow-mode workflow with qualified dentists, approved sources, and synthetic cases. Obtain clinical governance and regulatory review of the proposed intended use in each target market before any real-patient workflow.

A future clinician-facing panel can:
- Restate clinician-entered assessment and relevant patient facts, clearly distinguishing facts from AI summaries.
- Surface relevant, current, applicable guidelines and authorized drug-reference data.
- Flag missing information, allergy conflicts, documented medication interactions, dose-relevant factors, and guideline-defined cautions.
- Explain why a source is relevant and present alternatives or uncertainty.
- Require the clinician to independently validate and document the decision.

It must not autonomously diagnose, prescribe, sign, transmit orders, or recommend a medicine when key patient factors are missing. A disclaimer or a “suggestion only” label does not by itself determine regulatory status. FDA's **January 2026 Clinical Decision Support Software guidance** is current US input for assessing the actual functionality and intended use; obtain counsel before building or marketing treatment recommendations. Use WHO medication-safety guidance and applicable local medicines guidance to create safety requirements, not as a substitute for clinical approval.

## Research references and adoption decisions

| Project / standard | Recommended use | Decision / caution |
|---|---|---|
| [Mia AI site](https://github.com/MohammedAbdelshafy/mia-ai-site) | Existing character assets, welcome/onboarding and mission theatre | Reuse designs; extract a portable package without destabilizing the live site. |
| [ai-front-desk](https://github.com/MohammedAbdelshafy/ai-front-desk) | Existing pure domain logic, test harness and initial WhatsApp reference | Keep as current dental pilot code base. Harden first; do not treat current demo as production. |
| [Medplum](https://github.com/medplum/medplum) | FHIR clinical data repository candidate | Leading candidate for a time-boxed technical/contract spike. Verify exact support, BAA, hosting and isolation. Apache-2.0 core noted in its repository; check dependency-specific terms too. |
| [Hiberius WhatsApp Receptionist](https://github.com/Hiberius/whatsapp-receptionist) | Architectural reference for tenant configuration, outbox, retry, idempotency, staff handoff and retention | Its July 2026 project status says database-level RLS isolation was not yet proven and the cross-tenant admin panel was unwired. Borrow test ideas, do not blindly fork/adopt. |
| [Chatwoot](https://github.com/chatwoot/chatwoot) | Optional operator inbox | Core is MIT; enterprise directory has separate terms. Verify healthcare data-flow, hosting and contract fit. |
| [LiveKit Agents](https://github.com/livekit/agents) | Later realtime voice and telephony | Apache-2.0 framework; model/add-on licences differ. Defer until text workflow proves value. |
| [Pipecat](https://github.com/pipecat-ai/pipecat) | Alternative realtime Python voice/multimodal stack | BSD-2-Clause per repository metadata; verify adapter and model licences. |
| [HL7 FHIR Questionnaire](https://hl7.org/fhir/R4/questionnaire.html), [QuestionnaireResponse](https://hl7.org/fhir/R4/questionnaireresponse.html), [MedicationStatement](https://hl7.org/fhir/R4/medicationstatement.html) | Interoperable questionnaire and clinical records | Use for data mapping and future PMS/EHR integrations. |
| [ADA medical/dental history](https://www.ada.org/resources/practice/practice-management/medical-dental-health-history) | Dental questionnaire content review | Dentist remains responsible for reviewing a current, complete history; use clinic-approved wording. |
| [FDA CDS software guidance, Jan 2026](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software) | US regulatory scoping for future medication support | Read the full current guidance with qualified counsel; no simple disclaimer shortcut. |
| [HHS Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html), [WHO Medication Without Harm](https://www.who.int/initiatives/medication-without-harm), [NICE medicines optimisation](https://www.nice.org.uk/guidance/ng5/chapter/Recommendations) | Security baseline and medication-safety design inputs | Applicability, obligations and local implementation must be assessed per deployment. |

## Execution roadmap

### Phase 0 — Pilot discovery and boundaries
- Confirm one clinic type, one location and one high-friction workflow.
- Interview a small set of dentists/clinic staff; capture current form completion, admin time, dentist review time, messaging channels, scheduling/PMS, and handoff process.
- Ask a qualified dentist to approve the first questionnaire and review brief.
- Select the actual jurisdiction, clinic data flow, channels and vendors.
- Keep the first product focused on pre-visit intake and staff handoff, not medication decision support.

**Gate:** one clinic confirms the problem and agrees to test a paid or clearly scoped pilot; its baseline and success metrics are documented.

### Phase 1 — Dental pre-visit workflow
- Build mobile-first patient link with expiring, non-guessable access token and appropriate identity verification.
- Capture medication names, dose/frequency as reported, current/recent antibiotics, allergies/reactions, long-term conditions, past procedures, relevant history and visit concerns using a dentist-approved questionnaire.
- Support a pre-visit reminder and a waiting-room QR/fallback completion path.
- Build the dentist brief that highlights patient-reported facts, omissions, conflicts and history needing reconfirmation.
- Let staff correct or clarify information with provenance; preserve the original submitted answers.
- Record dentist review/sign-off, form version and timestamps.

**Gate:** clinicians confirm the brief is usable; no AI interpretation is silently represented as patient fact.

### Phase 2 — Secure, auditable production foundation
- Decide between Medplum and an alternative only after security, data-processing and contract spike.
- Enforce tenant isolation at database/server level and test with at least two seeded clinics.
- Role-based access, least privilege, encryption, secret handling, audit events, data minimization, retention/deletion, backup/restore, incident response and access review.
- Protect health data from general LLM analytics/logs; send minimum necessary context only to approved processors with appropriate contracts/settings.
- Verify webhook signatures, idempotency, durable outbox, retry handling and human handoff state.
- Keep live channel writes off until the clinic signs off on configuration and its privacy/compliance review is complete.

**Gate:** security review and negative tests pass; no production PHI in demo or preview environments.

### Phase 3 — Reusable Mia shell
- Extract the character/chat/task-stage pattern into a small TypeScript/React package with typed events and adapters.
- Connect UI progress to actual backend events, not decorative animations.
- Separate persona presentation from permissions and data access.
- Test accessibility, mobile layout, cancellation, retry, error, offline and human handoff states.
- Use the same package in one clinical UI and one non-clinical Mia app before generalizing it to the entire product portfolio.

**Gate:** one UI implementation is reused in two apps without forking its core behavior.

### Phase 4 — Pilot proof and revenue
Track baseline and post-launch:
- Questionnaire completion before arrival.
- Staff time spent collecting/re-entering history.
- Dentist time spent gathering routine background information.
- Missing or stale responses.
- Number and time-to-resolution of staff handoffs.
- Patient/staff experience and real workflow failures.

Compare measured results with baseline and describe sample size/limitations. Do not claim 10–15 minutes saved until measured and replicated.

### Phase 5 — Retention and clinic integrations
- Add clinic-approved recalls, confirmations, follow-up, missed-appointment recovery and patient communications with appropriate consent and policy.
- Add one PMS integration selected by the first real clinic (Open Dental, NexHealth or another system as appropriate).
- Maintain request-versus-confirmed-booking semantics.
- Use an operator inbox only if clinic workflows show the current queue is inadequate.

### Phase 6 — Curated multi-specialty knowledge registry
- Implement a reviewed, versioned pack format and provenance registry.
- Create the academic reference panel and source map for each specialty.
- Build synthetic cases, test suites and domain-specific acceptance gates before any pack is enabled.
- Expand by customer demand and clinical reviewer availability. Do not bulk-ingest copyrighted academic content.
- Add localization and market rules as independent overlays rather than forking the underlying application.

### Phase 7 — Clinical decision support
Only after clinical governance, regulatory assessment, evidence licensing, and validated evaluation:
- Start with source retrieval, completeness checks, interactions/cautions and clinician-facing guideline navigation.
- Validate on specialist-authored case sets and prospective shadow-mode cases before visible recommendations.
- Require source citations, display data freshness and uncertainty, audit every recommendation, and preserve clinician authority.
- No autonomous prescribing, order transmission or treatment action.

### Phase 8 — Voice and high-fidelity characters
Once the text workflow is proven:
- Evaluate LiveKit Agents versus Pipecat on call transfer, latency, interruption handling, language support, hosting, cost, licences and observability.
- Add a character/voice provider adapter so avatar services can be changed without rewriting the agent.
- First ship voice as an optional accessible interface, with transcript and human handoff.
- Do not transmit identifiable clinical details to avatar/voice vendors until privacy, retention, training-use settings, data region and required agreements are reviewed.

## Required quality gates

### Product and workflow
- Every patient submission can be viewed and corrected only by authorized users.
- Every questionnaire links to the exact template version used.
- An incomplete or contradictory answer is visible, not filled in by guesswork.
- The patient may ask for staff at any time, and the bot stays handed off until an authorized staff reset.
- Staff can see work waiting for action; no silent drops.
- No appointment is labelled confirmed without system/staff confirmation.
- Mia reports errors and external-action outcomes truthfully.

### Security and operations
- Cross-tenant reads/writes fail in real database tests, not just mocked unit tests.
- Invalid/duplicate webhook events cause no duplicate reply or record.
- Failed messages enter a visible retry/dead-letter path.
- Secrets and full patient message bodies are not emitted to general logs.
- Access, edits, reviews, consent, exports and deletions are auditable.
- Backups and restore, incident response and retention/deletion are tested.
- Live sends/calls/booking are per-clinic feature-flagged and default off in test/preview.

### Clinical knowledge and decision support
- Every active question and clinical claim has provenance, scope, version and review status.
- Clinical packs have qualified reviewers, a documented scope and revalidation schedule.
- Evaluation tests missing facts, conflicting answers, allergy/interaction conflicts, population constraints, outdated references, prompt injection and unsupported questions.
- Critical miss rate and false alert rate are monitored; no public clinical accuracy claim without a valid study.
- Any medication-support feature receives separate product-intended-use and regulatory review before implementation or marketing.

## First implementation order

1. Close the product boundary: dental pre-visit intake first; no live medication advice in the paid MVP.
2. Get clinician approval for the dental questionnaire and dentist brief.
3. Spike Medplum versus a healthcare-suitable FHIR-mapped backend and document contract/security findings.
4. Implement persistent intake and dentist-review states behind synthetic-data tests.
5. Harden tenant isolation, audit and deletion, webhook idempotency and the outbox.
6. Embed a first Mia shell using existing assets and real stage events.
7. Run a pilot and measure actual time and completion outcomes.
8. Add retention/PMS integration only where the pilot requires it.
9. Build other specialty packs using the registry.
10. Assess evidence-linked clinical decision support and voice as separate later milestones.

## Current operating constraints

- Do not send dental outreach automatically; the 40-clinic target list must be revalidated at point of contact and drafts remain unsent pending explicit approval.
- No use of real patient information in current demos, static sites or unsecured previews.
- Keep the single-clinic source-of-truth and tenant boundaries explicit; do not let a general Mia memory store become a shared clinical database.
- Preserve the current dental PR and issues rather than assuming unmerged work is already shipped.
- Do not represent the project as HIPAA compliant, clinically validated, or capable of live booking until the actual deployment has been reviewed and tested.

## Decision summary

**Build the reusable Mia shell and safe task/runtime patterns once; build a FHIR-aligned clinical record layer with strict boundaries; validate dental pre-visit intake and dentist-ready summaries first; then add retention, integrations, reviewed specialty packs, and finally governed clinical decision support/voice.**

This is the shortest credible path that respects the long-term multi-app vision without turning the first release into an untestable “AI doctor for every specialty.”
