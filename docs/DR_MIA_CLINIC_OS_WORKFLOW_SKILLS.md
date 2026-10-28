# Dr. Mia Clinic OS — Outcome Workflow Skills

Skills are versioned delivery contracts. **A definition is not a live capability.** Read each JSON file's `readiness_status` before including a feature in a proposal.

| Workflow | Customer outcome | Current state |
|---|---|---|
| Pre-Visit History | Better-prepared visits and a structured clinician review brief | Demo only; qualified clinician review required before real use |
| Missed Opportunity Recovery | Track missed calls/inquiries through follow-up and disposition | Design only |
| Appointment Reminders | Keep patients informed and route confirmation/reschedule requests | Design only |
| No-Show Recovery | Make missed appointments visible and organize respectful rescheduling | Design only |
| Patient Growth | Track new inquiries from campaign through booking and attendance | Design only |
| Daily Operations Scorecard | Show daily counts with source/data-mode labels | Limited implementation; count-only |
| Weekly Quality Scorecard | Review intake completeness, event coverage, attendance and follow-up work | Design only |
| Recall and Reactivation | Organize clinic-approved recall work and approved contact | Design only |
| Clinician Prescribing Assistant / Professor | Future clinician-controlled, source-cited medication reference review | Clinical review required; no pathways enabled |

## Required contract for every skill

Each workflow definition includes a stable identifier/version, intended outcome, required inputs, expected outputs, guardrails, activation requirements and an explicit readiness label.

No workflow is live until its integrations, approvals, access controls, monitoring and failure handling are complete. Sales scope must match what has been verified.

## Upsell sequence

1. **Foundation entry:** pre-visit history, completeness checks and staff review after a clinic-approved questionnaire.
2. **Recovery add-ons:** missed-call follow-up, reminders and no-show recovery after communications and scheduling prerequisites pass.
3. **Growth add-ons:** acquisition, recall/reactivation and reviews with agreed tracking, permissions and attribution.
4. **Command:** daily/weekly reporting after event sources and scorecard definitions are agreed with the clinic.
5. **Future clinical workbench:** only after specialist and medication-safety review, current jurisdiction-specific sources, evaluation and regulatory/privacy gates.

Monthly recurring tier prices have not been set. The $1,500 Quality-Audit Pilot is the established entry price; keep its scope separate from live production implementation.
