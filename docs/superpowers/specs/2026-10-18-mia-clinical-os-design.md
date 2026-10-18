# Dr. Mia Clinical OS: Full Workflow Design

- **Status:** Approved for planning; refined scope accepted 2026-10-18
- **Date:** 2026-10-18
- **Repository:** `MohammedAbdelshafy/ai-front-desk`
- **Branch:** `feat/mia-clinical-os`
- **Scope:** Synthetic-data-first web prototype and a gated path to clinical readiness

## 1. Purpose and product intent

Build a polished, responsive Egypt-first **OB-GYN-only** clinical web application. This app must contain only obstetrics/gynaecology content and workflows: no dental navigation, dental patient examples, dental evidence, or cross-specialty retrieval. Every clinic/specialty gets its own app deployment and, before real use, its own data resources by default. The first prototype models one fictional OB-GYN clinic. A doctor should find a patient, inspect appointment-relevant history, send or complete a pre-visit questionnaire in a demo flow, review answers, and consult Mia through an evidence-retrieval chat.

The app must make a reliable distinction between:
1. **A product UI prototype** using fictional records and simulated workflows.
2. **A validated clinical decision-support function** whose intended use, source rights, clinical content, privacy, security and regulatory status have been reviewed and approved.

The first release is the former. It must not accept or encourage use of identifiable or real patient health data.

## 2. Goals and non-goals

### Goals for the first demonstrable release

- Futuristic but legible UI: dark navy foundation, cyan/teal accents, subtle motion, glass-like panels, clear typography, strong contrast, responsive desktop/tablet/mobile layouts, reduced-motion support, and customizable Mia avatar.
- Doctor dashboard with day/next appointments, incomplete intake counts, recent synthetic patients, review queue and clearly labelled demo status.
- Patient directory and detail page with demographics, contact data, allergies/reactions, current and prior medicines, medical/surgical/obstetric history, encounter timeline, questionnaire submissions, clinician notes, investigation/document placeholders, and data provenance/last-confirmed labels.
- Appointment detail view with status, reason for visit, relevant patient history, questionnaire responses, clinician notes, review checklist, and link to the patient profile.
- Doctor-controlled, versioned questionnaire templates; patient-facing secure-link journey is visual/demo only in phase one. Support conditional questions, required/optional fields, skip reasons, patient correction, save/resume in demo mode, submission timestamp, and review status.
- OB-GYN intake template and general intake template. OB-GYN fields may include LMP, gestational age, gravidity/parity, relevant prior complications, medicines, allergies, symptoms/timeline, breastfeeding status, and clinician-configurable follow-up prompts. Fields must be conditionally relevant and clearly mark unknown/not applicable/prefer not to say where appropriate.
- Mia medication-reference chat located inside an appointment and also accessible as a general evidence search. It uses synthetic chart context only, shows which data were considered, returns reference links and source metadata, and says when the available evidence is incomplete.
- Knowledge-center browser with topic search, source type, jurisdiction, publication/update dates, license/rights status, approval status, and source link.
- Shared avatar presets and local portrait upload, keeping the existing local-first behavior.
- Draft governance and compliance document templates, version control, owner, review status and checklist of required external review.
- Automated tests for flows, access boundaries in the architecture contracts, citation provenance, and safety/abstention behavior.

### Explicit non-goals for phase one

- Real patient data, production authentication, real SMS/email notifications, real patient-facing portal deployment, EHR/PACS/LIS integration, claims/billing, e-prescribing, autonomous triage, autonomous diagnosis, autonomous prescribing, dose calculation, or clinical actions that execute without clinician approval.
- Describing the prototype as clinically validated, legally compliant, certified, or ready for real patient care.
- Bulk copying/downloading restricted or non-commercially licensed guidelines/books into a commercial system.
- Treating model output, keyword matching, or an empty lookup result as validated evidence or proof of safety.

## 3. Main journeys and UX requirements

### A. Doctor dashboard
- Left navigation: Overview, Patients, Appointments, Questionnaires, Mia Chat, Evidence Library, Safety & Governance, Settings.
- Top bar: specialty, synthetic/demo indicator, global patient search, avatar/profile controls.
- Dashboard cards are actionable, not decorative. Every number is explicitly seed/demo data in phase one.
- No patient identifiers in URLs; prototype routes use opaque demo IDs.
- Use accessible focus states, semantic landmarks, keyboard navigation, labels, useful empty/loading/error states and mobile-friendly tables/cards.

### B. Patient record
Sections: Overview; History & Conditions; Allergies; Medicines; Obstetric/Gynaecology History (specialty-gated); Encounters; Questionnaires; Documents (synthetic placeholders in phase one); Audit/Provenance.
- Record each item’s source (patient-reported, clinician-entered, imported, or synthetic demo), created/updated time and confirmation status.
- Display allergy reaction and severity as separate fields; never flatten “unknown” into “no known allergies.”
- Medicine records capture name/ingredient where known, product/strength/form, route, schedule if recorded, start/stop status and verification date. Phase one does not recommend or calculate a regimen.
- The page should show a concise, dated summary while preserving the full detail.

### C. Appointment
- Appointment links to one patient, one clinician/owner, location/service, time, status, reason and specialty-specific context.
- Timeline combines questionnaire submission, notes, recorded observations and follow-up events.
- Keep patient-reported facts separate from clinician-confirmed observations and model-generated summaries.
- Any generated summary must preserve source links to the originating fields; clinician edits remain attributable.

### D. Questionnaire authoring and completion
- Doctors can select templates, choose required fields, configure conditional branches, preview mobile layout and publish a version.
- Every submitted response points to the exact template version and respondent; revisions are append-only or versioned, not silent overwrites.
- Display missing answers, inconsistent values and explicit “unknown” separately. Red-flag text can inform a doctor to follow the clinic’s emergency pathway, but is not a validated triage score.
- Patient confirmation, consent/notice and identity verification must be separate concepts in production. A checkbox cannot be treated as a universal legal basis for all processing.
- Secure token-based links, rate limits, expiry, identity validation and consent/notice evidence are **not** implemented in phase one; do not expose a real patient link.

### E. Mia medication/evidence chat
- Entry points: active appointment (“Ask Mia about this case”) and general evidence search.
- The doctor must see whether synthetic patient context is attached, the exact data categories supplied to the assistant, and a way to remove irrelevant context.
- Chat request envelope: question, specialty, jurisdiction, selected synthetic context fields, and eligible retrieved evidence IDs. Never send a full chart by default.
- Retrieval order: local source index and approved evidence cards first; source-directory search second; optional language-model synthesis only when a configured provider is approved for the intended data class. Phase-one default is deterministic, source-first retrieval with clearly marked prototype summaries. No real clinical answer should be simulated as if verified.
- Proposed response structure: concise evidence summary; why it may apply; reasons it might not apply; required missing facts; contraindication/interaction/pregnancy/lactation checks and limitations; suggested clinician verification steps; urgent escalation notice when applicable; inline citations to sources/version/date; source disagreement or stale-source flag.
- A recommendation cannot be presented as “the correct medicine” unless a specific, versioned and locally approved clinical pathway authorizes that presentation. Phase one contains no such production-approved pathways.
- No evidence found, failed API call, ambiguous drug identity, stale source, or unresolved source conflict must produce an explicit limitation/abstention, not a confident guess.
- Clinical answer cards remain drafts until a qualified specialty clinician and pharmacist (as appropriate) review the content, applicability, jurisdiction, dose/route/formulation if any, exclusions, monitoring, alternatives, provenance and expiry/review date.

## 4. Clinical knowledge and rights architecture

Use four separately managed layers:
1. **Source directory:** title, publisher, canonical URL, jurisdiction, specialty/topic tags, version/date, access status, license/terms, update check and responsible owner.
2. **Licensed educational library:** foundational pharmacology/books used for education only where exact record/chapter rights permit. Do not turn general textbook passages into prescribing instructions automatically.
3. **Clinical reference retrieval:** link-first discovery of current guidelines, medicine labels, medicine-in-pregnancy/lactation references and official national regulatory information.
4. **Approved evidence cards/pathways:** structured and versioned clinical content, with recommendation basis, evidence level/strength where the source supports it, included/excluded populations, required patient factors, contraindications, monitoring, alternatives, local approval and re-review deadline.

Rights handling is per-source and per-record, not per-domain. Keep non-commercial sources link-only in the commercial prototype unless written permission or a lawyer-approved rights basis permits adaptation/reuse. In particular, current WHO publications may use CC BY-NC-SA terms, which are not a blanket commercial-reuse permission.

Initial source families already present in the repository include WHO maternal-health/PPH/labour guidance, ACOG, RCOG, CDC contraceptive guidance, LactMed, MotherToBaby, UKTIS/BUMPS, DailyMed/openFDA, Egyptian Drug Authority (EDA) references, Egyptian Ministry of Health and Population (MOHP) maternity-service references, PubMed/PMC and SMFM. The exact current version, applicability and source rights must be checked before an item becomes an approved evidence card.

### Citation and freshness requirements
- Every evidence-backed assistant statement must link to the supporting source and identify source title, issuing body, publication/update date when available, jurisdiction, and retrieved/checked date.
- Distinguish primary guideline, product label, systematic review, educational text and secondary patient-information page.
- Surface source conflicts rather than arbitrarily averaging them.
- Track review state: discovered → rights-reviewed → clinical-review draft → approved for named jurisdiction/use → retired/needs review.
- Automated source monitoring may alert to changes but must never auto-approve a content update.
- Source-index ranking improves relevance only; it is not an evidence-quality score.

## 5. Privacy, security and legal-document pack

The repository should provide **draft templates for review, not purported legal certifications**. A local privacy lawyer, clinical governance owner and security reviewer must adapt/sign off materials before production.

Required policy/document templates:
- Product intended-use and prohibited-use statement; jurisdiction and actor map.
- Data inventory, purpose/retention map, data-flow diagram and data classification.
- Patient privacy notice; staff privacy notice; patient intake notice; appropriate consent/authorization forms and evidence records where legally required.
- Data protection impact/risk assessment and cross-border transfer/hosting assessment.
- Controller/processor and subprocessor inventory; data-processing addendum and model/hosting provider due-diligence checklist.
- Retention/deletion schedule, records access/correction/export process, rights-request and complaint workflow.
- Security threat model; access-control matrix; MFA/session policy; encryption/key management; secrets management; backup/restore; incident and breach-response plan; audit policy; vulnerability and penetration-testing plan.
- Business continuity/disaster recovery plan and operational support/escalation policy.
- Clinical hazard log/risk file, FMEA-style review, clinical validation protocol/report template, usability evaluation, human-factors review, model/retrieval evaluation set governance, release approval/change control, incident reporting, post-release monitoring and rollback procedure.
- Source-license register and content permission log; clinical evidence card template and reviewer sign-off record.
- Staff training and acceptable-use policy; algorithm/model transparency and limitations statement.
- Regulatory classification memorandum for each launch jurisdiction (including whether the intended functionality may qualify as software as a medical device/clinical decision support) and a launch-gate checklist.

### Non-negotiable security rules
- Separate each clinic/specialty deployment's app configuration, database, storage, auth configuration, secrets and backups. No shared patient database across clinic apps by default. When later supporting shared infrastructure, enforce tenant scoping and authorization server-side for every request and object.
- Deny by default; verify role, tenant, record and action on every request. Never trust a client-provided clinic ID as proof of access.
- Use least-privilege roles and MFA for staff where supported. Protect service secrets; never send privileged backend keys to the browser.
- Audit sensitive read/write, export, deletion, consent changes, clinical approval, and evidence-card releases. Audit logs must not indiscriminately duplicate entire clinical records or secrets.
- No patient record, chat content or upload may be used for model training by default.
- Do not send patient context to an external AI provider until the provider’s contractual terms, retention/training settings, processing locations, subprocessors and legal basis have been reviewed.
- Production-grade clinical data is prohibited in the first release.

## 6. Proposed technical architecture

### Recommended direction
- **Web UI:** a new TypeScript/Next.js App Router application under `apps/mia-obgyn/`, with accessible reusable components, responsive design tokens and a clear UI/application/data boundary. This app is OB-GYN-only. Preserve existing Python workbenches in their current paths, but do not embed the dental workbench or its content in this app.
- **Phase-one demo data:** fictional seed records and deterministic browser/mock repository. Prominently label the app “Prototype • Synthetic data only.” No external model call and no backend PHI storage in this phase. Avoid suggesting that browser-local state is secure clinical storage.
- **Application contracts:** define typed interfaces for PatientRepository, AppointmentRepository, QuestionnaireRepository, EvidenceRetriever, ChatResponder and AuditRecorder. The prototype uses seed/mock adapters; a future production adapter must satisfy the same contracts and security tests.
- **Future hosted identity/data:** evaluate a dedicated, isolated backend such as Supabase Auth/Postgres/Storage with RLS only after the team selects organization, region and legal data-hosting posture. Do not reuse existing unrelated Supabase projects (current projects have unrelated names and regions) or create a new paid project during the design/spec stage.
- **Deployment:** create a dedicated Vercel Git project for `apps/mia-obgyn/` (proposed project slug `mia-obgyn-prototype`) on the existing `money-beastx` team. Do not repurpose the unrelated `mbm-dialer-app` project. The current workspace shows no linked project for this repository. Preview deployments must remain protected where possible and contain synthetic data only. Each later clinic/specialty instance gets its own project and separate storage/database configuration.
- **AI gateway/provider:** provider-neutral interface; no provider call in synthetic phase one. Before implementation, inspect current AI Gateway model/catalog, SDK version and data-retention terms; configure a hard spend cap. A future RAG answer must be grounded in retrieved evidence, expose citations, and abstain on conflicts/missing facts.
- **Retrieval:** parse only rights-cleared content into chunks carrying source ID, section/page where available, version/date, license, jurisdiction, approval state and content hash. In phase one a small local lexical index is enough; a vector database is not required until evaluation demonstrates need.
- **Interoperability:** design the domain model to permit future FHIR mapping, but do not claim certified interoperability or connect an EHR in phase one.
- **Avatar:** retain preset/photo upload and export/import; in phase one photos remain client-side only. Production cross-device profiles require authenticated storage, retention and deletion controls.

### Data model concepts
Clinic configuration (fixed to one app instance in phase one); User/Role; Clinician; Patient; Allergy/Reaction; MedicationStatement; MedicalHistoryItem; ObstetricHistory; Appointment; Encounter; QuestionnaireTemplate; QuestionnaireVersion; QuestionnaireResponse; ClinicalNote; Observation; AttachmentMetadata; Consent/NoticeRecord; EvidenceSource; EvidenceChunk; ClinicalEvidenceCard; ChatSession; ChatMessageMetadata; Citation; AuditEvent; SafetyIncident. Do not add shared multi-tenant patient tables to the first prototype.

The full sensitive medical content schema, FHIR mapping and retention values require review; this spec must not be treated as a final production database schema.

## 7. Regulatory and clinical safety reference set

Use official, current sources and re-check them before the relevant implementation or launch gate:
- Egypt Personal Data Protection Law No. 151/2020 and Executive Regulations under Decision No. 816/2025; use Personal Data Protection Center materials as an official starting point, with local legal advice: https://pdpc.gov.eg/assets/pdf-data/Guidelines/DPO.pdf
- Egyptian Drug Authority medical-device regulatory resources, including its SaMD/UDI materials; obtain a written classification assessment for the product’s actual intended purpose: https://www.edaegypt.gov.eg/media/goxpgwu3/8_regulatory-guideline-on-requirements-for-unique-device.pdf
- FDA Clinical Decision Support Software final guidance, issued January 29, 2026; only directly applicable in relevant US scope, but useful for product classification analysis: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- HHS HIPAA Security Rule risk analysis guidance for US covered entities/business associates where HIPAA applies: https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html
- EU GDPR Article 9 for health data in EU scope: https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/eng
- WHO Recommendations on Maternal Health, second edition (2025): https://www.who.int/publications/i/item/9789240080591
- WHO consolidated PPH guideline (2025), available under CC BY-NC-SA 3.0 IGO; treat commercial adaptation as permission-gated: https://www.who.int/publications/i/item/9789240115637
- WHO PPH implementation guide (2026): https://www.who.int/publications/i/item/9789240116115

These sources inform the requirements; citing them does not establish compliance or clinical approval.

## 8. Acceptance criteria

The first phase is acceptable when:

1. A doctor can navigate dashboard → synthetic patient → appointment → pre-visit questionnaire → submitted answers → Mia chat → cited source details without broken links.
2. Switching patient or appointment visibly changes the synthetic context attached to chat and its provenance.
3. The questionnaire flow supports required/optional answers, branching, unknown/not-applicable, versioned submission and review status.
4. The UI is responsive and keyboard accessible, supports reduced-motion settings, and works without the avatar feature being enabled.
5. All views clearly show synthetic/demo status; input screens warn users not to enter real patient information.
6. The chat makes no external model call, does not make unsupported medication recommendations, links relevant references, and displays an explicit “insufficient evidence / needs clinician review” state when no approved pathway exists.
7. The app has no production-patient data store, external sharing, notifications or e-prescribing integration in phase one.
8. Source rights/status/version are visible and draft evidence cards cannot appear as approved.
9. Automated tests cover cross-patient context isolation in the UI/domain layer, safe output for unknown allergies/medications, citation provenance, stale/failed lookup handling, questionnaire branching and HTML/form input safety.
10. The governance workspace contains the document templates listed in section 5, each stamped “Draft for professional review.”
11. No claim of regulatory compliance, clinical validation, readiness for live patients or production security is presented.
12. A protected preview or local run can be demonstrated with the included synthetic dataset once implementation and deployment configuration are approved.

## 9. Alternatives considered

### Option A: extend the existing Python standard-library server
Fastest for isolated tests but poor fit for a large, polished multi-page product, shared components, modern form handling and clear separation between frontend/backend. Retain it as a reference/test harness rather than growing it into the whole OS.

### Option B: modern frontend plus mock adapters first (recommended)
A new Next.js/TypeScript UI with typed repository/retrieval interfaces and synthetic fixture data. It delivers the complete navigable experience without prematurely moving sensitive records into a cloud service. It creates stable contracts for a later production data service.

### Option C: immediately build the live hosted system
Could deliver persistence/auth earlier, but requires choosing a region/organization, data-processing terms, access architecture, legal assessment, regulatory posture and budget now. Existing connected cloud projects are not clearly intended for Mia. This option is premature for clinical records and is not selected for phase one.

## 10. Decisions and gates

- **Approved in principle:** full doctor/patient workflow, pre-visit questionnaires, appointment/history pages, medication evidence chat, shared knowledge library, futuristic UI and avatar personalization.
- **Selected for first release:** Option B, with synthetic data and no external model call by default, in a dedicated `apps/mia-obgyn/` Next.js app and a new Vercel project. Existing unrelated projects are left untouched.
- **Not yet approved:** create/connect a Supabase project; select hosting region for real health data; enable a live AI provider; collect real patient information; launch public patient links; deploy e-prescribing or EHR integrations.
- **Required before production:** review and approve this spec and implementation plan; clinician/pharmacist approval of named clinical pathways; local legal and regulatory review; threat model and security verification; contractual approval of every hosting/AI subprocessor; clinical validation; formal production release sign-off.

## Sources and research checked on 2026-10-18

- WHO Maternal Health 2nd edition: https://www.who.int/publications/i/item/9789240080591
- WHO PPH consolidated guideline / rights page: https://www.who.int/publications/i/item/9789240115637
- WHO PPH implementation guide: https://www.who.int/publications/i/item/9789240116115
- FDA Clinical Decision Support Software final guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- HHS HIPAA risk-analysis guidance: https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html
- EU GDPR consolidated regulation: https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- Egypt Personal Data Protection Center material referencing Law 151/2020 and Decision 816/2025: https://pdpc.gov.eg/assets/pdf-data/Guidelines/DPO.pdf
- EDA SaMD/UDI regulatory document: https://www.edaegypt.gov.eg/media/goxpgwu3/8_regulatory-guideline-on-requirements-for-unique-device.pdf
