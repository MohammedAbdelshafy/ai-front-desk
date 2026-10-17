# Dr. Mia — Clinical Quality & Prescribing Copilot MVP

**Status:** Product and engineering specification, October 17, 2026. The current local prototype is an evidence-retrieval foundation and completeness checklist, not a prescribing system.

## Product decision

Dr. Mia's core offer is **clinical quality and evidence-linked medication review for dental clinicians**, with particular value for junior dentists and supervising dentists. Smart patient intake supplies context. The AI Front Desk, retention/feedback automation, and Growth / Lead Engine are optional expansions, not the main product identity.

This replaces the earlier front-desk-first commercial recommendation recorded in `DENTAL_AI_MVP_BUILD_SPEC.md`. That older spec remains useful for future front-desk implementation constraints.

## User and workflow

### Primary users
- **Junior dentist:** wants clear, source-grounded clinical information and visibility into relevant patient-context checks.
- **Supervising dentist / clinical owner:** wants junior clinicians to follow approved references and clinic protocols, and wants a clear review trail.
- **Practice owner:** wants a consistent, teachable workflow without pretending an AI system is the licensed decision-maker.

### Intended future workflow
1. Clinician enters a working assessment and symptoms, and summarizes relevant patient context such as allergies/reactions, current medicines/supplements, and medical history.
2. Mia checks whether required context has actually been entered and reviewed. A checked box must not override a blank allergy or medication field.
3. Mia retrieves evidence cards only if each card and its source are approved, current, licensed for the intended use, and matched to the selected jurisdiction.
4. Each card links to the exact source/version/section and states the scope and limitations. The screen differentiates what a source says from what the clinician entered and what the system infers.
5. Missing data, no-match, stale source, unknown medicine identity, and unavailable provider each show a visible review/fallback state.
6. The treating dentist reviews the information; a supervising dentist is involved according to the clinic's policy. Mia does not issue, sign, or transmit prescriptions.

## What exists today

- Evidence registry and source/card data models.
- Candidate source links for ADA/CDC dental guidance, DailyMed label information, RxNorm terminology, and FDA clinical-decision-support guidance.
- Strict source eligibility checks (approval state, rights status, jurisdiction, reviewer metadata, and review due date).
- Exact-phrase evidence-card retrieval with source provenance.
- Baseline allergy/current-medication review prompts and a deterministic completeness checklist.
- A local workbench at `http://127.0.0.1:8767` that accepts synthetic cases and stores no submissions. By default it makes no external calls; its optional public lookup sends only a standalone medicine name to NLM RxNorm/openFDA for metadata and never sends case context.
- Automated tests covering the no-evidence path, source expiry/approval/rights/jurisdiction checks, form escaping, and local HTTP behavior.

**There are zero approved medication evidence cards.** The source links are candidates, not clinical approval. The workbench correctly returns “No verified evidence found” until evidence has been reviewed and approved.

## Explicit non-goals for the current prototype

The current prototype does not diagnose, recommend a particular medicine for a real patient, calculate doses, perform comprehensive drug-interaction screening, interpret a patient's full chart, issue medication orders, connect to an EHR/PMS, or persist patient cases. It is not deployed for clinical use and has no production authentication. A disclaimer does not substitute for adequate validation or applicable regulatory analysis.

## Evidence and provider strategy

Keep the software source-agnostic and split three jobs:
- **Dental clinical guidelines:** use source-specific cards from the ADA and other appropriate professional sources for the exact patient population and clinical question.
- **Drug labeling:** retrieve the right product and label version from a suitable source such as DailyMed, then show the label provenance.
- **Medication identity and drug-interaction screening:** evaluate a supported terminology service and a properly licensed provider such as DrugBank Clinical API or Medi-Span. Do not depend on the retired RxNav Drug-Drug Interaction API.

Before any vendor integration, establish permitted clinical use, license terms, caching/display limits, version/update commitments, uptime, data-processing terms, and total per-clinic operating cost. Do not send real patient data to a provider until the clinic's privacy/security and contract requirements have been reviewed.

See [Clinical Information Centers](CLINICAL_INFORMATION_CENTERS.md), the machine-readable catalog at `ai_front_desk/clinical/clinical_information_centers.json`, the [Clinical Source Register](CLINICAL_SOURCE_REGISTER.md), and [Clinical Data Provider Options](CLINICAL_DATA_PROVIDER_OPTIONS.md). The directory now lists ADA, CDC, AAPD, AAE, NLM/FDA, EDA Egypt, WHO, and a licensed DDI provider candidate. Only RxNorm/openFDA name-only metadata lookup is currently implemented; the other entries are source links or integration candidates, not live recommendation sources.

## Build sequence

### Gate 1 — Workbench foundation (in progress)
- Validate the domain model, review prompts, and fail-closed behavior.
- Keep registry empty of approved cards until qualified clinical approval.
- Run automated tests in CI.
- Expose the prototype only on loopback with synthetic data.

### Gate 2 — Source approval workflow
- Define source owner, rights, scope, jurisdiction, review date/due date, reviewer, supersession and retirement.
- Let reviewers create and approve a specific evidence card without silently approving the entire source.
- Audit all changes and preserve the source/version with every card.
- Ensure stale, retired, or rights-uncleared cards stop appearing.

### Gate 3 — Licensed drug-data adapter
- Choose the provider after a technical/commercial comparison and lawful-use review.
- Normalize medicine identity using supported product/ingredient identifiers, not unverified name matching.
- Define explicit states for ambiguous, unavailable, stale, unsupported, or incomplete results.
- Keep interaction-check output separate from clinical-guideline evidence.

### Gate 4 — Dentist-authored offline evaluation
Use synthetic cases designed and reviewed by qualified dentists. Include incomplete and contradictory history, allergies, current medicines, formulation/strength ambiguity, relevant contraindication and interaction scenarios, false-alert cases, source updates, and no-match cases.

Measure:
- Whether every displayed clinical statement has a correct, applicable source.
- Whether critical safety context is detected or explicitly marked unknown.
- False-positive burden and review time.
- Correct handling of stale sources, API failures, and no-match cases.
- Whether the interface clearly communicates uncertainty and prevents users treating a source mention as a prescription.

A qualified clinical owner must predefine acceptance thresholds. Do not tune the test set to hide errors or use a high average score to excuse a critical missed safety issue.

### Gate 5 — Supervised shadow-mode pilot
Only after evidence and vendor gates pass, consider a narrowly scoped pilot where outputs are reviewed by dentists and are **not used as the sole or deciding basis for live treatment**. Start with a small set of common dental medication questions, record discrepancies and feedback, and require clinical sign-off before each scope expansion. Whether any real patient data can be used requires prior privacy, security, contractual, and regulatory review.

## Commercial offer

Core offer: **Dr. Mia Clinical Quality & Prescribing Copilot** for dental practices. Sell the value of evidence traceability, context review, learning support, and consistent protocols; do not claim fewer medication errors or better clinical outcomes before appropriately designed evaluations support those claims.

Optional modules:
1. Smart Patient Intake.
2. Patient retention, appointment communications, feedback, and recall.
3. AI Front Desk / missed-inquiry capture.
4. Growth / Lead Engine.

The first commercial proof point should be a qualified clinical partner willing to co-design and review a narrow workflow. Another language model is not a substitute for a qualified dental reviewer or licensed drug data.
