# Mia OB-GYN Governance and Readiness Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or an equivalent task-by-task workflow. These are editable templates for professional review, not legal opinions or compliance certificates.

**Goal:** Create a useful launch-readiness workspace and a coherent pack of privacy, security, clinical-governance, source-rights and regulatory-review documents specific to the OB-GYN-only synthetic prototype.

**Architecture:** Keep full documents in version-controlled `docs/clinical-governance/` and expose only a concise status/index view inside the synthetic web app. Each document is stamped “DRAFT — PROFESSIONAL REVIEW REQUIRED”, has an owner role, review status, scope/jurisdiction and a list of decisions requiring human sign-off. Do not claim any document establishes compliance on its own.

**Tech Stack:** Markdown, JSON manifest, TypeScript governance index UI, Python/Node-based validation tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-18-mia-clinical-os-design.md`

**Dependencies:** `docs/superpowers/plans/2026-10-18-mia-obgyn-web-prototype-plan.md`

## Global Constraints

- Documents are templates for a product team, not legal advice. Use explicit TODO/checklist fields rather than fabricated decisions, sign-offs, retention periods, vendor terms or compliance claims.
- Scope starts in Egypt and the OB-GYN specialty. Label US/EU rules as conditional reference frameworks, only relevant when jurisdiction/party scope requires them.
- No real health information in examples, fixtures, screenshots or tests.
- Never claim that Vercel, Supabase, an AI provider or this repository is automatically HIPAA-, GDPR- or Egypt-law-compliant.
- Store no secrets, real vendor tokens, real clinical pathways, identifiable patient data or security-sensitive credentials in docs.
- Keep document metadata, readiness states and app UI consistent.
- Each live-use gate needs an accountable owner and evidence of completion; a blank checkbox is not an approval.

## Review Focus

1. Draft templates must not make unsupported claims such as “Mia is compliant”, “data is fully secure”, or “clinically validated”.
2. Egypt applicability and any cross-border transfer must be specifically reviewed, not inferred from an EU/US policy template.
3. AI/model/provider processing must be absent in phase one and marked not approved in the readiness inventory.
4. Privacy notice, consent/authorization, legal basis and retention are separate concepts; do not use one checkbox as a universal substitute.
5. Source availability and a source license are different: source access does not automatically permit commercial reproduction or adaptation.

---

### Task 1: Create the governance document registry and readiness status model

**Files:**
- Create: `docs/clinical-governance/README.md`
- Create: `docs/clinical-governance/document-registry.json`
- Create: `apps/mia-obgyn/src/lib/governance/documents.ts`
- Create: `apps/mia-obgyn/src/app/governance/page.tsx`
- Test: `apps/mia-obgyn/src/lib/governance/documents.test.ts`

**Interfaces:**
- Document metadata: `id`, `title`, `purpose`, `ownerRole`, `status`, `jurisdictions`, `reviewersNeeded`, `path`, `lastUpdated`, `blocksLiveUse`.
- Status values: `draft`, `review_required`, `review_in_progress`, `approved_for_named_scope`, `expired_or_needs_review`, `not_applicable_pending_justification`.
- No document may default to an approved status.

- [ ] **Step 1: Write failing tests** for unique IDs, required metadata, known status enum, an unapproved default and a registry warning when a required live-use document is missing.
- [ ] **Step 2: Run** `npm test -- --run src/lib/governance/documents.test.ts`; expected FAIL.
- [ ] **Step 3: Implement** the registry, status helper and governance view with filters by owner/status and visible “not production-ready” notice.
- [ ] **Step 4: Run** focused tests and build; expected PASS.
- [ ] **Step 5: Commit** `feat: add Mia governance readiness index`.

### Task 2: Draft privacy, data-flow and legal-review templates

**Files:**
- Create:
  - `docs/clinical-governance/01-intended-use-and-data-classes.md`
  - `docs/clinical-governance/02-data-inventory-and-data-flow.md`
  - `docs/clinical-governance/03-patient-and-staff-privacy-notice-template.md`
  - `docs/clinical-governance/04-consent-authorization-and-notice-records.md`
  - `docs/clinical-governance/05-dpia-and-cross-border-transfer-assessment.md`
  - `docs/clinical-governance/06-vendor-and-subprocessor-review.md`
  - `docs/clinical-governance/07-retention-deletion-and-data-rights.md`
- Test: `tests/test_clinical_governance_docs.py`

- [ ] **Step 1: Write failing tests** requiring the seven paths, draft banner, jurisdiction/scope fields, accountable review roles and no fabricated retention duration/processor contract.
- [ ] **Step 2: Run** `python -m pytest tests/test_clinical_governance_docs.py -q`; expected FAIL.
- [ ] **Step 3: Implement** editable templates with purpose/processing inventory, proposed data-flow placeholders, categories of health data, patient/staff roles, hosting and model provider decision points, transfer risk, retention schedule fields, rights request process and sign-off blocks.
- [ ] **Step 4: Run** the focused Python test; expected PASS.
- [ ] **Step 5: Commit** `docs: add privacy and data governance templates`.

### Task 3: Draft security, response and continuity templates

**Files:**
- Create:
  - `docs/clinical-governance/08-security-threat-model-and-controls.md`
  - `docs/clinical-governance/09-access-control-and-audit-policy.md`
  - `docs/clinical-governance/10-incident-and-breach-response.md`
  - `docs/clinical-governance/11-backup-recovery-and-continuity.md`
  - `docs/clinical-governance/12-secure-development-and-release-checklist.md`
- Test: `tests/test_clinical_governance_docs.py`

- [ ] **Step 1: Add failing tests** requiring deny-by-default access, MFA/least privilege considerations, audit/read-write/export policies, incident roles/contact placeholders, recovery objectives to be approved rather than invented, and release/rollback gates.
- [ ] **Step 2: Run** focused Python tests; expected FAIL.
- [ ] **Step 3: Implement** threat-model tables for patient misbinding, broken object-level authorization, leaked secrets, model prompt leakage, data export, lost device and malicious uploads. Write security controls and test evidence fields without claiming the controls are currently deployed.
- [ ] **Step 4: Run** tests; expected PASS.
- [ ] **Step 5: Commit** `docs: add security and incident readiness templates`.

### Task 4: Draft clinical risk, validation and source-rights templates

**Files:**
- Create:
  - `docs/clinical-governance/13-clinical-risk-and-hazard-log.md`
  - `docs/clinical-governance/14-clinical-validation-and-human-factors-plan.md`
  - `docs/clinical-governance/15-evidence-source-rights-register.md`
  - `docs/clinical-governance/16-clinical-evidence-card-template.md`
  - `docs/clinical-governance/17-regulatory-classification-memo.md`
  - `docs/clinical-governance/18-staff-training-and-acceptable-use.md`
  - `docs/clinical-governance/19-production-release-gates.md`
- Test: `tests/test_clinical_governance_docs.py`

- [ ] **Step 1: Add failing tests** requiring hazards for missed emergencies, wrong patient/context, stale/wrong-jurisdiction sources, hallucinated answer, omitted contraindication, missing allergy and misleading empty lookups; clinical reviewer/pharmacist sign-off fields; source license/review date; and explicit regulator/legal sign-off.
- [ ] **Step 2: Run** focused Python tests; expected FAIL.
- [ ] **Step 3: Implement** risk register, clinical test-set methodology, citation-grounding and abstention evaluation, human-factors review, source terms/attribution register, evidence-card approval record, jurisdictional classification checklist and training policy. All records stay draft until actual review.
- [ ] **Step 4: Run** tests; expected PASS.
- [ ] **Step 5: Commit** `docs: add clinical validation and regulatory templates`.

### Task 5: Connect registry to app and preserve readiness gates

**Files:**
- Modify: `apps/mia-obgyn/src/lib/governance/documents.ts`
- Modify: `apps/mia-obgyn/src/app/governance/page.tsx`
- Modify: `apps/mia-obgyn/src/data/governance-docs.json` (or the selected validated registry format)
- Test: governance registry/page tests and `tests/test_clinical_governance_docs.py`.

- [ ] **Step 1: Write failing tests** that verify every required document appears with its current status and all live-use-blocking documents prevent the UI from showing “ready”.
- [ ] **Step 2: Run** tests; expected FAIL where the registry is incomplete.
- [ ] **Step 3: Implement** governance dashboard with counts by status, owners/reviewers, direct repository-linked document paths and an immutable phase-one banner stating no real patient data/model calls are permitted.
- [ ] **Step 4: Run** all governance/UI checks; expected PASS.
- [ ] **Step 5: Commit** `feat: surface clinical readiness gates in app`.

## Verification and rollout

- Run the full existing Python suite via the repository CI plus `npm ci`, unit tests, `npm run build` and browser smoke tests from the web plan.
- Inspect all generated Markdown for unsupported legal/clinical assertions, placeholders that hide key decisions, and contradictory statuses.
- Preview deployment is for the synthetic prototype only. Governance pages must not imply documents are signed or approvals exist merely because templates are present.
- Before any real-data release, obtain written local legal and regulatory review, clinician/pharmacist clinical governance sign-off, completed security risk assessment and threat-model evidence, vendor contract approval, and formal release authorization.
