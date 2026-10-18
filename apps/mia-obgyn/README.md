# MIA OB-GYN UI — implementation contract

- app root: `apps/mia-obgyn/`
- specialties: obstetrics & gynaecology only
- language: English + Arabic UI, proper RTL layout; clinical text is never auto-translated
- data: clearly synthetic, demo-only, no real PHI, no outbound calls or external model
- primary routes: `/dashboard`, `/patients`, `/patients/[id]`, `/appointments`, `/appointments/[id]`, `/questionnaires`, `/intake-demo/[id]`, `/mia`, `/evidence`, `/governance`
- chat: local deterministic source retrieval with citations, limitations, selected synthetic context shown visibly
- future pattern: one separate app/deployment/data resources per clinic-specialty; no cross-app shared patient database
- deploy target: create `mia-obgyn-prototype` on Vercel, root directory `apps/mia-obgyn`; do not reuse `mbm-dialer-app`

## Build tasks

1. Bootstrap pinned Next.js/TypeScript, tests, lockfile, CSS tokens and CI.
2. Define synthetic OB-GYN patient, allergy, medication-history, appointment, questionnaire and evidence types/fixtures.
3. Add mobile-first app shell, avatar, English/Arabic switch, dashboard and reduced-motion support.
4. Add patient directory/detail and dated source/verification metadata.
5. Add appointment views and patient-context isolation.
6. Add doctor-configurable questionnaire templates, branching, versioned responses and a demo patient intake.
7. Add safe local evidence directory sync/search and citation cards.
8. Add chat page and appointment-integrated context selection. No external LLM in this phase.
9. Add governance document status/index and draft templates.
10. Run unit tests, build and browser smoke tests. Deploy a protected synthetic preview after the code is ready.

## Acceptance gate

A user can go dashboard → synthetic patient → appointment → questionnaire → Mia chat, and see the exact selected context and its sources. Invalid IDs resolve to a safe not-found state. No real patient identifiers, live external calls, diagnosis or unsupported medication recommendations appear.
