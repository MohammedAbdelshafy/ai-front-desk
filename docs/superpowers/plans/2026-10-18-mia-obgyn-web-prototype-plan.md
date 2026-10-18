# Mia OB-GYN Web Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or an equivalent task-by-task workflow. Every task uses red-green-refactor and must pass its own checks before moving on.

**Goal:** Build an interactive, responsive, OB-GYN-only web prototype covering the doctor dashboard, synthetic patient records, appointments, pre-visit questionnaires and entry points into Mia's evidence chat.

**Architecture:** A self-contained Next.js App Router app lives in `apps/mia-obgyn/`. Phase one uses typed mock repositories and fictional fixtures only. It has no clinical database, real patient portal, external AI calls or other-specialty content. The deployment template is one app instance per clinic/specialty.

**Tech Stack:** TypeScript, Next.js App Router, React, CSS design tokens, Lucide icons, Vitest/React Testing Library and Playwright for smoke-level browser journeys. Pin compatible stable direct dependency versions and commit `package-lock.json` after checking current documentation.

**Spec:** `docs/superpowers/specs/2026-10-18-mia-clinical-os-design.md`

## Global Constraints

- Initial app name/scope: **Mia OB-GYN**; only obstetrics and gynaecology content.
- Every fixture and visible record is synthetic. Label all screens “Prototype · Synthetic data only”.
- Never ask the user to enter real patient data into this prototype. No real patient links, database, external AI calls, outbound communication, e-prescribing or clinical action execution.
- Do not repurpose Vercel project `mbm-dialer-app`; later create the dedicated `mia-obgyn-prototype` project with root directory `apps/mia-obgyn`.
- Future clinic/specialty deployments are isolated instances with separate secrets, auth, database, storage and backups by default. Do not implement shared multi-clinic records in this phase.
- Medication answers are source retrieval and review prompts only; there are no approved prescribing pathways. Do not imply clinical approval.
- Maintain keyboard accessibility, semantic controls, visible focus, high contrast, responsive layouts and `prefers-reduced-motion`.
- Keep existing Python apps and workflows intact.

## Review Focus

1. Unknown allergies must remain distinct from “no known allergies”.
2. Switching patient/appointment must never retain another synthetic patient's chat context.
3. Query-string IDs, invalid IDs and form values must not create arbitrary record access or HTML injection.
4. Empty/conditional questionnaire values must not be mistaken for a negative clinical finding.
5. Mobile layout, keyboard navigation and reduced-motion must remain usable without avatar/photo support.

---

### Task 1: Bootstrap a self-contained Next.js app and test harness

**Files:**
- Create: `apps/mia-obgyn/package.json`, `package-lock.json`, `tsconfig.json`, `next.config.ts`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`, `vitest.config.ts`
- Create: `apps/mia-obgyn/src/test/setup.ts`
- Test: `apps/mia-obgyn/src/app/page.test.tsx`
- Create: `.github/workflows/mia-obgyn-web.yml`

**Interfaces:**
- The app is independently installable from its own directory via `npm ci`.
- The default route renders the app shell and synthetic-data banner.

- [ ] **Step 1: Write failing tests** for the homepage title, global synthetic-data banner and no-dental-navigation rule.
- [ ] **Step 2: Run** `cd apps/mia-obgyn && npm test -- --run src/app/page.test.tsx`; expected FAIL because the app/test harness is not implemented.
- [ ] **Step 3: Implement** the minimum pinned Next.js/React, TypeScript, Vitest, RTL, Lucide and Playwright setup. Ensure package lock is created and version-pinned.
- [ ] **Step 4: Run** `npm ci && npm test -- --run src/app/page.test.tsx && npm run build`; expected PASS/exit 0.
- [ ] **Step 5: Commit** `feat: scaffold Mia OB-GYN web prototype`.

### Task 2: Define OB-GYN domain types and synthetic demo repositories

**Files:**
- Create: `apps/mia-obgyn/src/lib/domain/types.ts`
- Create: `apps/mia-obgyn/src/lib/demo/fixtures.ts`
- Create: `apps/mia-obgyn/src/lib/demo/repositories.ts`
- Test: `apps/mia-obgyn/src/lib/demo/repositories.test.ts`

**Interfaces:**
- `getPatients(): Patient[]`
- `getPatientById(id: string): Patient | null`
- `getAppointments(): Appointment[]`
- `getAppointmentById(id: string): Appointment | null`
- Types: `Patient`, `AllergyRecord`, `MedicationStatement`, `ObstetricHistory`, `Appointment`, `QuestionnaireTemplate`, `QuestionnaireResponse`, `EvidenceSource`.

- [ ] **Step 1: Write failing tests** for known fixture retrieval, invalid IDs, fictional-only data markers and unknown-vs-negative allergy status.
- [ ] **Step 2: Run** `npm test -- --run src/lib/demo/repositories.test.ts`; expected FAIL.
- [ ] **Step 3: Implement** type-safe deterministic repositories and 6–8 fictional OB-GYN patients with clearly fake identifiers, example appointments, allergy/reaction status, medicine statements and obstetric/gynaecology histories.
- [ ] **Step 4: Run** the focused test and full unit suite; expected PASS.
- [ ] **Step 5: Commit** `feat: add synthetic OB-GYN demo domain`.

### Task 3: Build the futuristic application shell and doctor dashboard

**Files:**
- Create: `apps/mia-obgyn/src/components/app-shell.tsx`
- Create: `apps/mia-obgyn/src/components/side-nav.tsx`
- Create: `apps/mia-obgyn/src/components/top-bar.tsx`
- Create: `apps/mia-obgyn/src/components/mia-avatar.tsx`
- Create: `apps/mia-obgyn/src/app/dashboard/page.tsx`
- Modify: `apps/mia-obgyn/src/app/globals.css`
- Test: shell/dashboard component tests.

**Interfaces:**
- Navigation routes: `/dashboard`, `/patients`, `/appointments/[id]`, `/questionnaires`, `/mia`, `/evidence`, `/governance`.
- Shell owns accessible nav, status badge, page content, avatar-customization trigger and mobile nav.

- [ ] **Step 1: Write failing tests** for navigation destinations, synthetic-only badge, reduced-motion fallback and mobile menu keyboard behavior.
- [ ] **Step 2: Run** focused shell tests; expected FAIL.
- [ ] **Step 3: Implement** deep-navy/cyan visual system, subtle gradients/glass cards, ambient decorative motion, a responsive layout and actionable dashboard cards for appointments, pending questionnaires and review tasks.
- [ ] **Step 4: Run** focused tests and build; expected PASS.
- [ ] **Step 5: Commit** `feat: add Mia OB-GYN command center UI`.

### Task 4: Implement patient directory and patient detail

**Files:**
- Create: `apps/mia-obgyn/src/app/patients/page.tsx`
- Create: `apps/mia-obgyn/src/app/patients/[id]/page.tsx`
- Create: `apps/mia-obgyn/src/components/patient-summary.tsx`
- Create: `apps/mia-obgyn/src/components/history-timeline.tsx`
- Test: patient directory/profile tests.

**Interfaces:**
- Search is limited to synthetic name/demo ID and client-side fixture data.
- Profile sections: overview, allergies/reactions, medicine history, medical/surgical/obstetric history, encounters, questionnaires and synthetic document placeholders.

- [ ] **Step 1: Write failing tests** for searching, opening a patient, missing record, provenance badges and display of unknown allergies without changing them to “none”.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** responsive list/cards and patient pages. Show source/confirmation labels and last-reviewed/updated dates. Use only obviously fictional contact details (e.g., reserved `.invalid` email domains).
- [ ] **Step 4: Run** focused tests and build; expected PASS.
- [ ] **Step 5: Commit** `feat: add OB-GYN patient records UI`.

### Task 5: Implement appointment detail and context isolation

**Files:**
- Create: `apps/mia-obgyn/src/app/appointments/page.tsx`
- Create: `apps/mia-obgyn/src/app/appointments/[id]/page.tsx`
- Create: `apps/mia-obgyn/src/lib/demo/appointment-context.ts`
- Test: appointment and context tests.

**Interfaces:**
- `buildAppointmentContext(appointmentId: string): AppointmentContext | null`
- Context includes only fields linked to that specific appointment/patient and explicitly selected by the clinician.

- [ ] **Step 1: Write failing tests** that prove appointment ID resolution, invalid-ID empty state and that switching appointment A → B removes A's patient details from the active context.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** appointment list/detail with time/status/reason, history summary, questionnaire results, clinician-note placeholder, review checklist and “Ask Mia about this synthetic case” action.
- [ ] **Step 4: Run** focused tests; expected PASS.
- [ ] **Step 5: Commit** `feat: add appointment workspace`.

### Task 6: Build doctor-configurable questionnaire templates and patient intake demo

**Files:**
- Create: `apps/mia-obgyn/src/app/questionnaires/page.tsx`
- Create: `apps/mia-obgyn/src/app/questionnaires/[id]/page.tsx`
- Create: `apps/mia-obgyn/src/app/intake-demo/[id]/page.tsx`
- Create: `apps/mia-obgyn/src/lib/questionnaires/engine.ts`
- Test: questionnaire engine and route tests.

**Interfaces:**
- `shouldShowQuestion(question, answers): boolean`
- `validateQuestionnaire(template, answers): ValidationResult`
- `createDemoSubmission(templateVersion, answers): QuestionnaireResponse`
- Support required/optional answers, branching, yes/no/choice/text/date fields, unknown/not-applicable/prefer-not-to-answer, draft/published versions, completion/review status.

- [ ] **Step 1: Write failing tests** for conditional follow-up, required-answer validation, unknown/not-applicable semantics, template-version pinning and safe invalid inputs.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** doctor template gallery/editor preview and patient-facing mobile intake demo; responses remain in in-memory/browser demo state and are not transmitted or described as secure storage.
- [ ] **Step 4: Run** focused tests and build; expected PASS.
- [ ] **Step 5: Commit** `feat: add configurable pre-visit questionnaires`.

### Task 7: Add avatar personalization without a server upload

**Files:**
- Create or adapt: `apps/mia-obgyn/src/components/avatar-customizer.tsx`
- Create or adapt: `apps/mia-obgyn/src/lib/avatar/profile.ts`
- Test: avatar upload/profile tests.

- [ ] **Step 1: Write failing tests** for preset changes, unsupported extension/MIME, oversize images and local-only profile behavior.
- [ ] **Step 2: Run** focused tests; expected FAIL.
- [ ] **Step 3: Implement** built-in clinician presets and optional local image preview with file-type/size limits. No network upload or cross-user profile synchronization.
- [ ] **Step 4: Run** focused tests; expected PASS.
- [ ] **Step 5: Commit** `feat: add local Mia avatar customization`.

### Task 8: Browser smoke tests, CI, and review build

**Files:**
- Create: `apps/mia-obgyn/e2e/doctor-journey.spec.ts`
- Modify: `.github/workflows/mia-obgyn-web.yml`

- [ ] **Step 1: Write failing Playwright test** for dashboard → patient → appointment → questionnaire → Mia chat, asserting synthetic banner and OB-GYN-only navigation.
- [ ] **Step 2: Run** the smoke test; expected FAIL until the journey is wired.
- [ ] **Step 3: Implement** CI that runs npm ci, unit tests, build and the browser smoke test with synthetic fixtures only.
- [ ] **Step 4: Run** `npm ci && npm test && npm run build` and the browser test; expected zero failures.
- [ ] **Step 5: Commit** `test: verify Mia OB-GYN demo journey`.

## Rollout gate

Do not connect patient storage, external AI, live patient links or e-prescribing. After the new app is present in the target branch, create a separate Vercel project named `mia-obgyn-prototype` rooted at `apps/mia-obgyn`, build a protected synthetic-data preview, verify the deployment, and leave the unrelated dialer project untouched. A future per-clinic release must provision separate auth, secrets, storage, database and backups and pass the privacy/security/legal/clinical gates in the spec.
