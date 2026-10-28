---
type: repository
status: active
owner_repo: MohammedAbdelshafy/ai-front-desk
product_name: Dr. Mia Clinic OS
source_of_truth: https://github.com/MohammedAbdelshafy/ai-front-desk
reviewed: 2026-10-28
---

# Dr. Mia Clinic OS — Project Context

One job: help clinics deliver better-prepared visits, consistent patient follow-up, patient growth and owner visibility without pretending a prototype is a live clinic service.

## Inputs
- Product and run limitations: [README](README.md)
- Pilot readiness: [pilot readiness record](docs/DR_MIA_CLINIC_OS_PILOT_READINESS.md)
- Demo steps: [demo runbook](docs/DR_MIA_CLINIC_OS_DEMO_RUNBOOK.md)
- Workflow readiness: [outcome workflow catalog](docs/DR_MIA_CLINIC_OS_WORKFLOW_SKILLS.md)
- Implementation: [ai_front_desk](ai_front_desk/)
- Tests: [tests](tests/)

## Current state
- Pre-visit dental history, structural validation, source-labelled history brief, reviews/corrections and local audit trail exist as a synthetic-data prototype.
- Daily operations scorecard is count-only and explicitly labels synthetic demo events.
- Missed-call recovery, live reminders, no-show recovery, patient growth and weekly scorecard workflows are described, but not live integrations.
- The dental questionnaire remains draft pending qualified dentist review.
- Prescribing/clinical decision support remains separate and blocked pending specialist, medication-safety, regulatory and privacy review.

## Operating rules
1. Collect only information needed for the approved task.
2. Validate inputs and flag missing/conflicting answers.
3. Route clinical judgment and patient concerns to qualified clinic staff.
4. Keep external sends, calls, bookings and integrations disabled until the clinic-level gates pass.
5. Keep demo patient records and event counts synthetic.
6. Distinguish recorded facts, inferred summaries, synthetic examples and unknowns.
7. Do not claim production authentication, compliance certification, clinical validation, or outcomes without independent evidence.
8. Never send clinic outreach without approval of the exact recipient batch and exact message.

## Commercial entry
The established entry offer is the $1,500 Quality-Audit Pilot. It can deliver workflow mapping, baseline definitions, a gap register and an action plan. Any implementation scope must be explicitly bounded to verified delivery capacity. Monthly tier pricing remains unset.

## Check
Run the documented tests and inspect the GitHub Actions result for the exact commit. Review the readiness record before any customer demo or proposal. Keep the repository slug and Python package unchanged.
