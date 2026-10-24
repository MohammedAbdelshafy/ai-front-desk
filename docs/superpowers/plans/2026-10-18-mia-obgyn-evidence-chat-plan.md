# Mia OB-GYN Evidence Retrieval and Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or an equivalent task-by-task workflow. Complete tests before implementation code. This plan follows the web prototype plan and does not enable real clinical advice.

**Goal:** Provide fast, jurisdiction-aware, source-cited OB-GYN reference retrieval and a useful chatbox interface that explains what evidence was found and what remains unknown, without presenting an unapproved medication decision as a recommendation.

**Architecture:** Import the existing OB-GYN reference directory into the Next.js app through a deterministic sync/validation script. Add a local lexical index, source filters, a typed evidence-responder contract, and a chat UI. Phase one makes no external model or live patient-data call and has no approved medication pathways.

**Tech Stack:** TypeScript, JSON catalog, deterministic tokenization/ranking, Vitest, React Testing Library and Playwright.

**Spec:** `docs/superpowers/specs/2026-10-18-mia-clinical-os-design.md`

**Dependencies:** `docs/superpowers/plans/2026-10-18-mia-obgyn-web-prototype-plan.md`

## Global Constraints

- Source scope is OB-GYN only and this app instance is Egypt-first.
- Use the existing `ai_front_desk/clinical/obgyn_reference_centers.json` as the canonical source directory; do not import dental catalogs.
- Directory search is discovery, not evidence grading. It does not itself establish an approved protocol or the correct medicine.
- Every result must preserve source ID/title/publisher where available, jurisdiction, canonical HTTPS URL, topics, status, date/version and license/rights notes.
- Egypt/UK/US/Global filters must not quietly mix jurisdictions. A non-Egypt source may be shown as background only when explicitly tagged as a global reference and clearly labelled.
- No patient-identifying information is sent to any external provider. In fact, no external AI provider is called in phase one.
- The chat cannot prescribe, select a “correct” medication, calculate/validate a dose or claim safety based on a failed/empty lookup.
- Any future clinical card remains disabled until rights-reviewed and approved by an appropriate specialty clinician/pharmacist for the stated jurisdiction.

## Review Focus

1. Typo, synonym or mixed-language queries still return relevant source links where available without implying certainty.
2. Egypt search results never present US-only regulator/source material as Egyptian authority.
3. Empty, stale, failed or conflicting evidence yields an explicit limitation/abstention.
4. Every displayed source comes from the source catalog and has a valid HTTPS canonical URL.
5. The chat must not echo raw HTML or patient-specific details from a prompt into rendered HTML.

---

### Task 1: Synchronize and validate the OB-GYN source directory

**Files:**
- Create: `apps/mia-obgyn/scripts/sync-obgyn-catalog.mjs`
- Create: `apps/mia-obgyn/src/data/obgyn-reference-centers.json` (generated from the canonical Python source)
- Create: `apps/mia-obgyn/src/lib/evidence/catalog.ts`
- Test: `apps/mia-obgyn/src/lib/evidence/catalog.test.ts`

**Interfaces:**
- `loadObgynCatalog(): ObgynCatalog`
- `validateObgynCatalog(catalog): CatalogValidationResult`
- Sync script reads only `../../ai_front_desk/clinical/obgyn_reference_centers.json` relative to the app root and copies it into the app's data directory.

- [ ] **Step 1: Write failing tests** for unique IDs, HTTPS URLs, required title/id/topic/jurisdiction fields, OB-GYN-only specialty marker and source parity with the canonical Python catalog.
- [ ] **Step 2: Run** `npm test -- --run src/lib/evidence/catalog.test.ts`; expected FAIL.
- [ ] **Step 3: Implement** deterministic sync/validation; wire `predev`, `prebuild` and `pretest` scripts so local and Vercel builds sync the catalog and fail on malformed data.
- [ ] **Step 4: Run** catalog test and `npm run build`; expected PASS.
- [ ] **Step 5: Commit** `feat: sync OB-GYN reference catalog into web app`.

### Task 2: Implement fast, jurisdiction-aware source retrieval

**Files:**
- Create: `apps/mia-obgyn/src/lib/evidence/search.ts`
- Test: `apps/mia-obgyn/src/lib/evidence/search.test.ts`

**Interfaces:**
- `searchObgynSources(query: string, filters: { jurisdiction: "EG" | "GLOBAL" | "US" | "UK"; careStage?: string; limit?: number }): EvidenceSource[]`
- Search normalization uses safe length caps, Unicode normalization, stemming-light token matching and existing topic/source metadata.
- The result order is relevance order only; do not label it “quality”, “safest” or “recommended”.

- [ ] **Step 1: Write failing tests** for postpartum haemorrhage, pre-eclampsia, pregnancy/lactation medication, contraception and general gynaecology queries; test Egypt jurisdiction isolation, empty query and max limits.
- [ ] **Step 2: Run** focused search tests; expected FAIL.
- [ ] **Step 3: Implement** deterministic search with an explainable match reason and stable tie-break, filtering to the selected jurisdiction and permitted global-reference tags.
- [ ] **Step 4: Run** tests, including existing Python catalog tests when available; expected PASS.
- [ ] **Step 5: Commit** `feat: add fast OB-GYN reference search`.

### Task 3: Implement the safe chat response contract

**Files:**
- Create: `apps/mia-obgyn/src/lib/evidence/answer.ts`
- Create: `apps/mia-obgyn/src/lib/evidence/safety-checks.ts`
- Test: `apps/mia-obgyn/src/lib/evidence/answer.test.ts`
- Test: `apps/mia-obgyn/src/lib/evidence/safety-checks.test.ts`

**Interfaces:**
- `buildReferenceAnswer(input: { question: string; jurisdiction: Jurisdiction; careStage?: string; context?: SelectedSyntheticContext }): EvidenceAnswer`
- `EvidenceAnswer` contains: concise response, evidence-found status, source records, why each source matched, key limitations, clinician-verification checklist and explicit state when no approved pathway exists.
- `approvedMedicationPathwayFor(input): ApprovedMedicationPathway | null` returns `null` for every query in phase one; the type supports later reviewed cards but no fallback may invent one.

- [ ] **Step 1: Write failing tests** for no-results abstention, unapproved medication query, unknown allergy status, pregnancy/lactation context gaps, source failures and visible provenance.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** a deterministic evidence summary using matching sources, with separate “what this source may help answer”, “what Mia cannot conclude”, and “what the clinician needs to verify” sections.
- [ ] **Step 4: Run** focused tests and coverage for the response builder; expected PASS.
- [ ] **Step 5: Commit** `feat: add cited reference answer contracts`.

### Task 4: Implement the Mia chat UI and evidence cards

**Files:**
- Create: `apps/mia-obgyn/src/app/mia/page.tsx`
- Create: `apps/mia-obgyn/src/components/mia-chat.tsx`
- Create: `apps/mia-obgyn/src/components/evidence-card.tsx`
- Create: `apps/mia-obgyn/src/components/chat-composer.tsx`
- Modify: appointment detail action from the web prototype plan.
- Test: chat and evidence-card component tests.

**Interfaces:**
- Prompts may contain selected synthetic context only. The UI displays exactly what context is attached and offers “remove context”.
- Quick starts include: “Find current guidance”, “Medication in pregnancy/lactation”, “Hypertension in pregnancy references”, “Postpartum bleeding guidance” and “Contraception eligibility guidance”.
- Form submit is local deterministic retrieval. No API route is wired to a language model.

- [ ] **Step 1: Write failing tests** for question submission, citations, quick prompts, attached-context display, remove-context behavior and no-approved-pathway messaging.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** chat bubbles, source/result panels, source match reasons, limitations, jurisdiction filter, loading/error/empty states and keyboard-accessible composer.
- [ ] **Step 4: Run** tests/build and the browser journey; expected PASS.
- [ ] **Step 5: Commit** `feat: build Mia evidence chat interface`.

### Task 5: Add evidence library view and provenance display

**Files:**
- Create: `apps/mia-obgyn/src/app/evidence/page.tsx`
- Create: `apps/mia-obgyn/src/components/source-detail.tsx`
- Test: evidence view tests.

- [ ] **Step 1: Write failing tests** for filter by jurisdiction/source type/topic, license labels, date/version display and safe external-link attributes.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** searchable source registry and detail drawer/page, with states “directory only”, “rights review required”, “clinical review draft”, “approved” and “needs re-review”. Existing sources must not be upgraded automatically.
- [ ] **Step 4: Run** tests/build; expected PASS.
- [ ] **Step 5: Commit** `feat: add OB-GYN evidence library browser`.

### Task 6: End-to-end safety verification

**Files:**
- Create/modify: `apps/mia-obgyn/e2e/mia-evidence-chat.spec.ts`
- Modify: `.github/workflows/mia-obgyn-web.yml`

- [ ] **Step 1: Write failing browser tests** showing that an Egypt-mode medication query shows source links plus “no approved pathway” and that a missing source returns an abstention state.
- [ ] **Step 2: Run** browser tests; expected FAIL until wired.
- [ ] **Step 3: Implement** the CI step and retain synthetic fixtures only.
- [ ] **Step 4: Run** `npm ci && npm test && npm run build` and browser tests; expected zero failures. Run the full existing Python suite too.
- [ ] **Step 5: Commit** `test: verify safe OB-GYN evidence chat`.

## Deferred until separate approval and external review

- Authenticated production retrieval, patient-record database, embeddings/vector store, external LLM/gateway, live drug label API, drug-interaction service, dose support, e-prescribing and any medication recommendation.
- For a later model-backed implementation, re-read current Vercel AI SDK/Gateway docs, evaluate provider retention/training/region/contracts, define redacted input policy and spend caps, build a clinical gold set, test answer grounding/abstention/citation correctness, and complete clinical/regulatory review before exposure to real patient data.
