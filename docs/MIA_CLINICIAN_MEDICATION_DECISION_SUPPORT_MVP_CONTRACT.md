# Mia Dental OS — Clinician Medication Decision-Support: MVP Contract

**Status:** Proposed implementation and clinical-governance contract. This is not evidence of clinical approval or production readiness.

## Product objective
Help a licensed dentist review evidence-supported medication options for a clinician-entered assessment, with concise explanations and traceable sources. Mia is decision support; the treating clinician remains responsible for diagnosis and treatment. The system must not independently prescribe, create or transmit orders, or present a draft pathway as approved.

## User-facing output for each eligible option
1. **Why it may be considered:** source-grounded rationale for the defined clinical question and population.
2. **Evidence:** guideline/label/source title, publisher, edition/version, exact section, jurisdiction, effective date, link, and last clinical review date.
3. **Patient-context checks:** allergies and prior reactions, current medicines/supplements, relevant conditions, pregnancy/lactation where applicable, age/population limits, and missing/contradictory data.
4. **Warnings and boundaries:** contraindications, relevant interaction-screening result, serious warnings, monitoring/counselling details, uncertainties and excluded populations.
5. **Alternatives and non-pharmacologic/supportive steps:** only when explicitly supported by reviewed guidance and appropriate to the clinical scenario.
6. **Why Mia is abstaining:** missing context, no approved pathway, unclear medication/product identity, jurisdiction mismatch, stale source, failed provider, conflicting evidence, or a clinical scenario outside scope.
7. **Clinician action:** review, edit, reject or document a decision. No medicine is preselected; nothing is sent to a pharmacy or patient.

## Required architecture
- Keep the clinical-guideline adapter separate from drug-label retrieval and from medication terminology/interaction screening. These are different evidence functions.
- The existing approved medication pathway registry remains empty until a pathway has been separately approved by the appropriate dental clinician and medication-safety reviewer. Draft cards cannot be promoted by keyword match or model confidence.
- Model use may summarize/restructure already approved evidence and clinician-entered synthetic or properly authorized data. It may not invent a source, infer approval, fill missing clinical context, or turn a source mention into a patient-specific order.
- Keep source/version/provenance with every displayed clinical statement. Show source quotations only within applicable licenses/rights and display limits.
- Use role-based access, tenant isolation, audit logs, retention/deletion controls and appropriate privacy/vendor agreements before any real-patient data is accepted.
- Single-writer invariant: exactly one authoritative write path for medication review state. Model tools must be read-only by default; all clinical sign-off and any state-changing operation go through the authoritative server/store with authorization and audit logging. No direct model-to-database writes.
- Provider timeout, ambiguous medicine mapping, missing strength/route where necessary, stale data, unsupported jurisdiction, empty evidence set, contradictory history, or low confidence must fail closed and clearly state “not checked” or “clinician review required.” Never convert a failure into a clean safety status.
- No patient data is sent to an external model or third-party provider until privacy, jurisdiction, vendor terms, and clinic authorizations are reviewed.

## Data-source strategy
- Clinical guidance: source-specific dental guidance (e.g. ADA/CDC/AAPD/AAE as applicable) with rights and current-version checks.
- Drug label: exact product/label matching from a suitable source such as DailyMed in the US, with jurisdiction displayed.
- Medication identity: use a supported terminology service to resolve ingredient/product IDs; free-text name similarity alone is not sufficient for a production interaction check.
- Interactions: evaluate a properly licensed/current interaction data provider (e.g. DrugBank Clinical API or Medi-Span) and validate its scope. Do not build new DDI screening on the discontinued RxNav DDI API.
- Open Medicine: use its published algorithms when directly relevant; record algorithm ID, author, version/date and limitations. Search availability does not prove the returned algorithm fits dentistry or the patient's jurisdiction. The initial searches made for this task did not find a matching dental algorithm.
- ClinicalTrials.gov, PubMed and trial registry records are research discovery sources, not direct evidence that a medicine should be prescribed to an individual.

## Evaluation gates before any supervised pilot
1. Qualified dentist and appropriate medication-safety reviewer approve each individual evidence card and its source rights/jurisdiction.
2. Dentist-authored synthetic evaluation set includes contraindications, allergies, current medicines, unknown/contradictory history, pregnancy/lactation where relevant, population boundaries, no-match, stale sources, ambiguous products, source outages and misleading prompts.
3. Pass criteria defined in advance, including zero tolerance for invented citations, unapproved-pathway display, silent provider failure, autonomous prescribing, and bypass of clinician sign-off.
4. Measure citation correctness, source applicability, critical-risk recall, false-alert burden, abstention behavior, traceability, and review time. Mean scores cannot compensate for a critical safety failure.
5. Typecheck, build, tests, access-control review, tenant-isolation/security test, retention/deletion, backup/restore and rollback procedures pass.
6. Begin only in supervised shadow mode with synthetic data until privacy, contracts, regulation and clinical governance authorize the exact next scope.

## Acceptance criteria for implementation PR
- Zero approved pathway entries remain until signed approval is provided.
- The interface can display an approved pathway only when source, reviewer, jurisdiction, review date and review-due gates all pass.
- Each candidate output visibly separates: clinician-entered assessment, source text/summary, system checks, missing data and human decision.
- Every failure path has a deterministic abstention state.
- No prescription generation/transmission route exists.
- All writes are mediated by the authoritative server/store and audited.
- Unit/integration tests cover approval, expiration, jurisdiction, ambiguous medicine identity, missing/contradictory context, provider outage, replay/duplicate prevention, audit records and the empty-catalog state.

## Commercial framing
Position the first product as **clinical evidence review and medication-safety workflow support for dental clinicians**, not an autonomous prescriber. Do not claim reduced medication errors, improved outcomes, universal drug-interaction coverage, regulatory clearance or clinical validation until supported by appropriate evidence and review.
